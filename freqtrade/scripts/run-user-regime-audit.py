#!/usr/bin/env python3
"""
Run long-history regime audit inside docker and write calibration report.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, Optional

from latest_refs import publish_latest_ref, rel_payload_path
from run_state import RunStateTracker

REPO_ROOT = Path(__file__).resolve().parents[2]
FREQTRADE_ROOT = REPO_ROOT / "freqtrade"
DEFAULT_COMPOSE_FILE = REPO_ROOT / "docker-compose.grid.yml"
DEFAULT_USER_DATA = FREQTRADE_ROOT / "user_data"


def q(text: str) -> str:
    return shlex.quote(text)


def to_container_user_data_path(local_path: Path, user_data_dir: Path) -> str:
    rel = local_path.resolve().relative_to(user_data_dir.resolve())
    return f"/freqtrade/user_data/{rel.as_posix()}"


def _proc_usage(pid: int) -> Dict[str, object]:
    stat_path = Path(f"/proc/{int(pid)}/stat")
    if not stat_path.exists():
        return {}
    try:
        raw = stat_path.read_text(encoding="utf-8")
        rparen = raw.rfind(")")
        if rparen < 0:
            return {}
        rest = raw[rparen + 2 :].split()
        utime = float(rest[11])
        stime = float(rest[12])
        rss_pages = int(rest[21])
        clk = float(os.sysconf("SC_CLK_TCK"))
        page_size = float(os.sysconf("SC_PAGE_SIZE"))
        cpu_sec = (utime + stime) / clk
        rss_mb = (rss_pages * page_size) / (1024.0 * 1024.0)
        return {"cpu_sec": round(cpu_sec, 3), "rss_mb": round(rss_mb, 1)}
    except Exception:
        return {}


def _probe_outputs(paths: Dict[str, Path]) -> Dict[str, object]:
    out: Dict[str, object] = {}
    for key, path in paths.items():
        if path.exists():
            try:
                out[f"{key}_bytes"] = int(path.stat().st_size)
            except Exception:
                out[f"{key}_bytes"] = -1
        else:
            out[f"{key}_bytes"] = 0
    return out


def _resolve_repo_path(value: str) -> Path:
    text = str(value or "").strip()
    if not text:
        return Path(text)
    candidate = Path(text)
    if candidate.is_absolute():
        return candidate.resolve()
    return (REPO_ROOT / candidate).resolve()


def _compose_env() -> Dict[str, str]:
    env = dict(os.environ)
    try:
        env.setdefault("GRID_UID", str(os.getuid()))
        env.setdefault("GRID_GID", str(os.getgid()))
    except Exception:
        pass
    return env


def run_compose_inner(
    project_dir: Path,
    compose_file: Path,
    service: str,
    inner_cmd: str,
    heartbeat_sec: int = 60,
    progress_label: str = "",
    progress_probe: Optional[Callable[[], Dict[str, object]]] = None,
    stalled_heartbeats_max: int = 0,
    dry_run: bool = False,
) -> None:
    cmd = [
        "docker",
        "compose",
        "-f",
        str(compose_file),
        "run",
        "--rm",
        "--entrypoint",
        "bash",
        service,
        "-lc",
        inner_cmd,
    ]
    print(f"[regime-audit] $ {' '.join(shlex.quote(x) for x in cmd)}", flush=True)
    if dry_run:
        return
    hb = int(heartbeat_sec)
    if hb <= 0:
        subprocess.run(cmd, cwd=str(project_dir), env=_compose_env(), check=True)
        return
    proc = subprocess.Popen(cmd, cwd=str(project_dir), env=_compose_env())
    started = time.time()
    label = str(progress_label).strip() or "compose"
    last_probe: Dict[str, object] = {}
    stale_heartbeats = 0
    stale_max = int(max(0, int(stalled_heartbeats_max)))
    while True:
        try:
            rc = proc.wait(timeout=hb)
            if rc != 0:
                raise subprocess.CalledProcessError(rc, cmd)
            return
        except subprocess.TimeoutExpired:
            elapsed = int(max(0.0, time.time() - started))
            usage = _proc_usage(int(proc.pid))
            probe: Dict[str, object] = {}
            if progress_probe is not None:
                try:
                    probe = progress_probe() or {}
                except Exception as exc:
                    probe = {"probe_error": str(exc)}
            changed = int(probe != last_probe)
            last_probe = dict(probe)
            if changed:
                stale_heartbeats = 0
            else:
                stale_heartbeats += 1
            usage_txt = " ".join(f"{k}={v}" for k, v in usage.items())
            probe_txt = json.dumps(probe, sort_keys=True) if probe else "{}"
            print(
                f"[regime-audit] heartbeat stage={label} elapsed_sec={elapsed} {usage_txt} "
                f"progress_changed={changed} stale_heartbeats={stale_heartbeats} probe={probe_txt} still_running=1",
                flush=True,
            )
            if stale_max > 0 and stale_heartbeats >= stale_max:
                try:
                    proc.terminate()
                except Exception:
                    pass
                raise TimeoutError(
                    f"Stalled: no observable probe progress for {stale_heartbeats} heartbeats at stage={label}."
                )
        except KeyboardInterrupt:
            try:
                proc.terminate()
            except Exception:
                pass
            raise


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user-data", default=str(DEFAULT_USER_DATA), help="Local user_data directory path.")
    ap.add_argument("--pair", default="ETH/USDT")
    ap.add_argument("--timeframe", default="15m")
    ap.add_argument("--data-dir", default="/freqtrade/user_data/data/binance")
    ap.add_argument("--timerange", default=None, help="YYYYMMDD-YYYYMMDD")
    ap.add_argument("--bbwp-lookback", type=int, default=252)
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--out-dir", default=None, help="Local directory under user_data for outputs")
    ap.add_argument("--service", default="freqtrade")
    ap.add_argument(
        "--compose-file",
        default=str(DEFAULT_COMPOSE_FILE),
        help="docker compose file path (defaults to repo-level docker-compose.grid.yml)",
    )
    ap.add_argument(
        "--project-dir",
        default=str(REPO_ROOT),
        help="docker compose project directory (defaults to repo root).",
    )
    ap.add_argument("--emit-features-csv", action="store_true")
    ap.add_argument("--emit-verbose", action="store_true", help="Emit per-candle verbose and transition event artifacts")
    ap.add_argument(
        "--heartbeat-sec",
        type=int,
        default=60,
        help="Print periodic heartbeat while compose command is running (0 disables).",
    )
    ap.add_argument(
        "--stalled-heartbeats-max",
        type=int,
        default=0,
        help="If >0, abort when probe output is unchanged for this many heartbeats.",
    )
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--disable-run-state",
        action="store_true",
        help="Disable _state marker files (state.json + events.jsonl).",
    )
    return ap


def main() -> int:
    args = build_parser().parse_args()

    project_dir = _resolve_repo_path(args.project_dir)
    compose_file = _resolve_repo_path(args.compose_file)
    if not project_dir.is_dir():
        raise FileNotFoundError(f"Compose project directory missing (--project-dir): {project_dir}")
    if not compose_file.is_file():
        raise FileNotFoundError(f"Compose file missing (--compose-file): {compose_file}")
    user_data_dir = _resolve_repo_path(args.user_data)
    if not user_data_dir.is_dir():
        raise FileNotFoundError(f"user_data directory not found: {user_data_dir}")

    run_id = args.run_id or datetime.now(timezone.utc).strftime("regime_audit_%Y%m%dT%H%M%SZ")
    if args.out_dir:
        out_dir = Path(args.out_dir)
        if not out_dir.is_absolute():
            out_dir = (user_data_dir / out_dir).resolve()
    else:
        out_dir = (user_data_dir / "regime_audit" / run_id).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    run_state: Optional[RunStateTracker] = None
    if not args.disable_run_state:
        run_state = RunStateTracker(out_dir / "_state" / "state.json", out_dir / "_state" / "events.jsonl")
        run_state.update(
            run_type="regime_audit",
            run_id=str(run_id),
            out_dir=str(out_dir),
            status="running",
            step_word="RUN_START",
            pair=str(args.pair),
            timeframe=str(args.timeframe),
            timerange=str(args.timerange or ""),
            dry_run=int(bool(args.dry_run)),
        )
        run_state.event(
            "RUN_START",
            run_id=str(run_id),
            pair=str(args.pair),
            timeframe=str(args.timeframe),
            timerange=str(args.timerange or ""),
        )

    report_local = out_dir / "report.json"
    report_container = to_container_user_data_path(report_local, user_data_dir)
    features_local: Optional[Path] = None
    features_container: Optional[str] = None
    verbose_local: Optional[Path] = None
    verbose_container: Optional[str] = None
    transitions_csv_local: Optional[Path] = None
    transitions_csv_container: Optional[str] = None
    transitions_json_local: Optional[Path] = None
    transitions_json_container: Optional[str] = None
    if args.emit_features_csv:
        features_local = out_dir / "features.csv"
        features_container = to_container_user_data_path(features_local, user_data_dir)
    if args.emit_verbose:
        verbose_local = out_dir / "per_candle_verbose.csv"
        verbose_container = to_container_user_data_path(verbose_local, user_data_dir)
        transitions_csv_local = out_dir / "transition_events.csv"
        transitions_csv_container = to_container_user_data_path(transitions_csv_local, user_data_dir)
        transitions_json_local = out_dir / "transition_events.json"
        transitions_json_container = to_container_user_data_path(transitions_json_local, user_data_dir)

    inner = (
        f"python /freqtrade/user_data/scripts/regime_audit_v1.py "
        f"--pair {q(args.pair)} "
        f"--timeframe {q(args.timeframe)} "
        f"--data-dir {q(args.data_dir)} "
        f"--bbwp-lookback {int(args.bbwp_lookback)} "
        f"--out {q(report_container)}"
    )
    if args.timerange:
        inner = f"{inner} --timerange {q(args.timerange)}"
    if features_container:
        inner = f"{inner} --emit-features-csv {q(features_container)}"
    if verbose_container:
        inner = f"{inner} --emit-verbose-csv {q(verbose_container)}"
    if transitions_csv_container:
        inner = f"{inner} --emit-transitions-csv {q(transitions_csv_container)}"
    if transitions_json_container:
        inner = f"{inner} --emit-transitions-json {q(transitions_json_container)}"

    progress_paths: Dict[str, Path] = {"report": report_local}
    if features_local:
        progress_paths["features"] = features_local
    if verbose_local:
        progress_paths["verbose"] = verbose_local
    if transitions_csv_local:
        progress_paths["transitions_csv"] = transitions_csv_local
    if transitions_json_local:
        progress_paths["transitions_json"] = transitions_json_local

    print("[regime-audit] stage 1/1 running audit", flush=True)
    if run_state is not None:
        run_state.event("AUDIT_START", run_id=str(run_id))
    try:
        run_compose_inner(
            project_dir,
            compose_file,
            args.service,
            inner,
            heartbeat_sec=int(args.heartbeat_sec),
            progress_label="regime_audit",
            progress_probe=lambda: _probe_outputs(progress_paths),
            stalled_heartbeats_max=int(args.stalled_heartbeats_max),
            dry_run=args.dry_run,
        )
    except KeyboardInterrupt:
        if run_state is not None:
            run_state.update(status="interrupted", step_word="INTERRUPTED")
            run_state.event("INTERRUPTED", run_id=str(run_id))
        raise
    except Exception as exc:
        if run_state is not None:
            run_state.update(status="failed", step_word="RUN_FAILED", error=str(exc))
            run_state.event("RUN_FAILED", run_id=str(run_id), error=str(exc))
        raise
    if run_state is not None:
        run_state.event("AUDIT_DONE", run_id=str(run_id))
    if args.dry_run:
        if run_state is not None:
            run_state.update(status="completed", step_word="RUN_COMPLETE", return_code=0)
            run_state.event("RUN_COMPLETE", run_id=str(run_id), return_code=0, dry_run=1)
        return 0

    with report_local.open("r", encoding="utf-8") as f:
        report = json.load(f)

    meta = report.get("meta", {}) or {}
    rec = report.get("recommended_thresholds", {}) or {}
    labels = report.get("labels", {}) or {}
    print(
        "[regime-audit] coverage:",
        {
            "pair": meta.get("pair"),
            "rows_raw": meta.get("rows_raw"),
            "rows_valid_features": meta.get("rows_valid_features"),
            "start_utc": meta.get("start_utc"),
            "end_utc": meta.get("end_utc"),
        },
        flush=True,
    )
    print("[regime-audit] label_counts:", labels, flush=True)
    print("[regime-audit] recommended_thresholds:", json.dumps(rec, indent=2), flush=True)

    mode_overrides: Dict[str, Dict[str, object]] = {}
    for mode_name in ("intraday", "swing"):
        src = rec.get(mode_name, {}) if isinstance(rec, dict) else {}
        if not isinstance(src, dict):
            continue
        ov: Dict[str, object] = {}
        if src.get("adx_enter_max") is not None:
            ov["adx_enter_max"] = float(src["adx_enter_max"])
        if src.get("adx_exit_max") is not None:
            ov["adx_exit_min"] = float(src["adx_exit_max"])
            ov["adx_exit_max"] = float(src["adx_exit_max"])
        if src.get("bbw_1h_pct_max") is not None:
            ov["bbw_1h_pct_max"] = float(src["bbw_1h_pct_max"])
        if src.get("ema_dist_max_frac") is not None:
            ov["ema_dist_max_frac"] = float(src["ema_dist_max_frac"])
        if src.get("vol_spike_mult") is not None:
            ov["vol_spike_mult"] = float(src["vol_spike_mult"])
        if src.get("bbwp_s_max") is not None:
            ov["bbwp_s_max"] = float(src["bbwp_s_max"])
            ov["bbwp_s_enter_high"] = float(src["bbwp_s_max"])
        if src.get("bbwp_m_max") is not None:
            ov["bbwp_m_max"] = float(src["bbwp_m_max"])
            ov["bbwp_m_enter_high"] = float(src["bbwp_m_max"])
        if src.get("bbwp_l_max") is not None:
            ov["bbwp_l_max"] = float(src["bbwp_l_max"])
            ov["bbwp_l_enter_high"] = float(src["bbwp_l_max"])
        if src.get("os_dev_rvol_max") is not None:
            ov["os_dev_rvol_max"] = float(src["os_dev_rvol_max"])
        if src.get("os_dev_persist_bars") is not None:
            ov["os_dev_persist_bars"] = int(src["os_dev_persist_bars"])
        ov["router_eligible"] = True
        mode_overrides[mode_name] = ov

    overrides_local = out_dir / "mode_threshold_overrides.json"
    with overrides_local.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "source_report": str(report_local),
                "recommended_thresholds": rec,
                "intraday": mode_overrides.get("intraday", {}),
                "swing": mode_overrides.get("swing", {}),
            },
            f,
            indent=2,
            sort_keys=True,
        )
    if run_state is not None:
        run_state.event("OVERRIDES_WRITTEN", path=str(overrides_local))

    print(f"[regime-audit] wrote {report_local}", flush=True)
    print(f"[regime-audit] wrote {overrides_local}", flush=True)
    if features_local:
        print(f"[regime-audit] wrote {features_local}", flush=True)
    if verbose_local:
        print(f"[regime-audit] wrote {verbose_local}", flush=True)
    if transitions_csv_local:
        print(f"[regime-audit] wrote {transitions_csv_local}", flush=True)
    if transitions_json_local:
        print(f"[regime-audit] wrote {transitions_json_local}", flush=True)
    if run_state is not None:
        run_state.update(
            status="completed",
            step_word="RUN_COMPLETE",
            report_path=str(report_local),
            overrides_path=str(overrides_local),
            return_code=0,
        )
        run_state.event("RUN_COMPLETE", run_id=str(run_id), return_code=0)
    latest_payload = {
        "run_type": "regime_audit",
        "run_id": str(run_id),
        "status": "completed",
        "step_word": "RUN_COMPLETE",
        "pair": str(args.pair),
        "timeframe": str(args.timeframe),
        "timerange": str(args.timerange or ""),
        "out_dir": rel_payload_path(user_data_dir, out_dir),
        "report_path": rel_payload_path(user_data_dir, report_local),
        "overrides_path": rel_payload_path(user_data_dir, overrides_local),
        "features_path": rel_payload_path(user_data_dir, features_local),
        "verbose_path": rel_payload_path(user_data_dir, verbose_local),
        "transitions_csv_path": rel_payload_path(user_data_dir, transitions_csv_local),
        "transitions_json_path": rel_payload_path(user_data_dir, transitions_json_local),
        "label_counts": labels,
        "recommended_thresholds": rec,
    }
    latest_ref = publish_latest_ref(user_data_dir, "regime_audit", latest_payload)
    print(f"[regime-audit] latest_ref wrote {latest_ref}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
