#!/usr/bin/env python3
"""
Run long-history regime audit inside docker and write calibration report.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional


def q(text: str) -> str:
    return shlex.quote(text)


def to_container_user_data_path(local_path: Path, user_data_dir: Path) -> str:
    rel = local_path.resolve().relative_to(user_data_dir.resolve())
    return f"/freqtrade/user_data/{rel.as_posix()}"


def run_compose_inner(root_dir: Path, service: str, inner_cmd: str, dry_run: bool = False) -> None:
    cmd = ["docker", "compose", "run", "--rm", "--entrypoint", "bash", service, "-lc", inner_cmd]
    print(f"[regime-audit] $ {' '.join(shlex.quote(x) for x in cmd)}", flush=True)
    if dry_run:
        return
    subprocess.run(cmd, cwd=str(root_dir), check=True)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", default="ETH/USDT")
    ap.add_argument("--timeframe", default="15m")
    ap.add_argument("--data-dir", default="/freqtrade/user_data/data/binance")
    ap.add_argument("--timerange", default=None, help="YYYYMMDD-YYYYMMDD")
    ap.add_argument("--bbwp-lookback", type=int, default=252)
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--out-dir", default=None, help="Local directory under user_data for outputs")
    ap.add_argument("--service", default="freqtrade")
    ap.add_argument("--emit-features-csv", action="store_true")
    ap.add_argument("--emit-verbose", action="store_true", help="Emit per-candle verbose and transition event artifacts")
    ap.add_argument("--dry-run", action="store_true")
    return ap


def main() -> int:
    args = build_parser().parse_args()

    root_dir = Path(__file__).resolve().parents[1]
    user_data_dir = root_dir / "user_data"
    if not user_data_dir.is_dir():
        raise FileNotFoundError(f"user_data directory not found: {user_data_dir}")

    run_id = args.run_id or datetime.now(timezone.utc).strftime("regime_audit_%Y%m%dT%H%M%SZ")
    if args.out_dir:
        out_dir = Path(args.out_dir)
        if not out_dir.is_absolute():
            out_dir = (root_dir / out_dir).resolve()
    else:
        out_dir = (user_data_dir / "regime_audit" / run_id).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

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

    run_compose_inner(root_dir, args.service, inner, dry_run=args.dry_run)
    if args.dry_run:
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
