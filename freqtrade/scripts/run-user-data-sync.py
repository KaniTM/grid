#!/usr/bin/env python3
"""
Incremental OHLCV sync helper with progress and heartbeat logs.

Modes:
- append: extend existing local data forward in time (default)
- prepend: backfill earlier history using --prepend
- full: explicit timerange sync
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from latest_refs import publish_latest_ref, rel_payload_path
from run_state import RunStateTracker


def q(text: str) -> str:
    return shlex.quote(text)


def pair_fs(pair: str) -> str:
    return str(pair).replace("/", "_").replace(":", "_")


def day_now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def add_days(day: str, delta: int) -> str:
    dt = datetime.strptime(day, "%Y%m%d")
    return (dt + timedelta(days=int(delta))).strftime("%Y%m%d")


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


def _format_pct(done: int, total: int) -> str:
    if int(total) <= 0:
        return "0.00%"
    return f"{(100.0 * float(done) / float(total)):.2f}%"


def _probe_file(path: Optional[Path]) -> Dict[str, object]:
    if path is None:
        return {}
    out: Dict[str, object] = {"path": str(path)}
    if path.exists():
        try:
            st = path.stat()
            out["bytes"] = int(st.st_size)
            out["mtime"] = int(st.st_mtime)
        except Exception:
            out["bytes"] = -1
            out["mtime"] = -1
    else:
        out["bytes"] = 0
        out["mtime"] = 0
    return out


def run_compose_inner(
    root_dir: Path,
    service: str,
    inner_cmd: str,
    heartbeat_sec: int = 60,
    progress_label: str = "",
    progress_probe: Optional[Callable[[], Dict[str, object]]] = None,
    stalled_heartbeats_max: int = 0,
    dry_run: bool = False,
) -> None:
    cmd = ["docker", "compose", "run", "--rm", "--entrypoint", "bash", service, "-lc", inner_cmd]
    print(f"[data-sync] $ {' '.join(shlex.quote(x) for x in cmd)}", flush=True)
    if dry_run:
        return
    hb = int(heartbeat_sec)
    if hb <= 0:
        subprocess.run(cmd, cwd=str(root_dir), check=True)
        return
    proc = subprocess.Popen(cmd, cwd=str(root_dir))
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
                f"[data-sync] heartbeat stage={label} elapsed_sec={elapsed} {usage_txt} "
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


def run_compose_capture(root_dir: Path, service: str, inner_cmd: str) -> Tuple[int, str, str]:
    cmd = ["docker", "compose", "run", "--rm", "--entrypoint", "bash", service, "-lc", inner_cmd]
    cp = subprocess.run(cmd, cwd=str(root_dir), capture_output=True, text=True)
    return int(cp.returncode), str(cp.stdout), str(cp.stderr)


def container_to_host_path(container_path: str, user_data_dir: Path) -> Optional[Path]:
    prefix = "/freqtrade/user_data/"
    if not str(container_path).startswith(prefix):
        return None
    rel = str(container_path)[len(prefix) :]
    return (user_data_dir / rel).resolve()


def get_coverage(root_dir: Path, service: str, container_file: str) -> Dict[str, object]:
    inner = (
        "python - <<'PY'\n"
        "import json\n"
        "import os\n"
        "import pandas as pd\n"
        f"p = {container_file!r}\n"
        "out = {'path': p, 'exists': os.path.exists(p)}\n"
        "if out['exists']:\n"
        "    try:\n"
        "        df = pd.read_feather(p, columns=['date'])\n"
        "    except Exception:\n"
        "        df = pd.read_feather(p)\n"
        "    out['rows'] = int(len(df))\n"
        "    if 'date' in df.columns and len(df) > 0:\n"
        "        ts = pd.to_datetime(df['date'], utc=True, errors='coerce').dropna()\n"
        "        if len(ts) > 0:\n"
        "            out['min_day'] = ts.min().strftime('%Y%m%d')\n"
        "            out['max_day'] = ts.max().strftime('%Y%m%d')\n"
        "print(json.dumps(out, sort_keys=True))\n"
        "PY"
    )
    rc, stdout, stderr = run_compose_capture(root_dir, service, inner)
    text = (stdout or "") + "\n" + (stderr or "")
    payload: Dict[str, object] = {"path": container_file, "exists": False}
    for line in reversed(text.splitlines()):
        s = line.strip()
        if not s.startswith("{") or not s.endswith("}"):
            continue
        try:
            parsed = json.loads(s)
            if isinstance(parsed, dict):
                payload = parsed
                break
        except Exception:
            continue
    payload["rc"] = int(rc)
    return payload


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", nargs="+", default=["ETH/USDT"])
    ap.add_argument("--timeframes", nargs="+", default=["15m", "1h", "4h"])
    ap.add_argument("--mode", choices=["append", "prepend", "full"], default="append")
    ap.add_argument("--timerange", default=None, help="Required for --mode full (YYYYMMDD-YYYYMMDD)")
    ap.add_argument("--start-day", default=None, help="Required for --mode prepend")
    ap.add_argument("--end-day", default=None, help="Optional target end day (YYYYMMDD), default=today UTC")
    ap.add_argument("--bootstrap-start", default="20200101", help="Start day when no existing file exists")
    ap.add_argument("--overlap-days", type=int, default=2, help="Overlap days when deriving incremental timeranges")
    ap.add_argument("--exchange", default="binance")
    ap.add_argument("--config-path", default="/freqtrade/user_data/config.json")
    ap.add_argument("--data-dir", default="/freqtrade/user_data/data/binance")
    ap.add_argument("--data-format-ohlcv", default="feather", choices=["json", "jsongz", "feather", "parquet"])
    ap.add_argument("--service", default="freqtrade")
    ap.add_argument("--run-id", default=None, help="Run-state id under user_data/run_state/data_sync/")
    ap.add_argument("--trading-mode", default="spot", choices=["spot", "margin", "futures"])
    ap.add_argument("--no-parallel-download", action="store_true")
    ap.add_argument("--heartbeat-sec", type=int, default=30)
    ap.add_argument(
        "--stalled-heartbeats-max",
        type=int,
        default=0,
        help="If >0, abort when probe output is unchanged for this many heartbeats.",
    )
    ap.add_argument("--fail-on-task-error", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--disable-run-state",
        action="store_true",
        help="Disable run-state marker files (state.json + events.jsonl).",
    )
    return ap


def main() -> int:
    args = build_parser().parse_args()

    if args.mode == "full" and not args.timerange:
        raise ValueError("--timerange is required for --mode full")
    if args.mode == "prepend" and not args.start_day:
        raise ValueError("--start-day is required for --mode prepend")

    root_dir = Path(__file__).resolve().parents[1]
    user_data_dir = root_dir / "user_data"
    if not user_data_dir.is_dir():
        raise FileNotFoundError(f"user_data directory not found: {user_data_dir}")

    tasks: List[Tuple[str, str]] = []
    for p in args.pairs:
        for tf in args.timeframes:
            tasks.append((str(p), str(tf)))
    total = len(tasks)
    print(f"[data-sync] tasks_total={total} mode={args.mode}", flush=True)
    run_id = str(args.run_id or datetime.now(timezone.utc).strftime("data_sync_%Y%m%dT%H%M%SZ"))
    run_state: Optional[RunStateTracker] = None
    if not args.disable_run_state:
        run_state_dir = user_data_dir / "run_state" / "data_sync" / run_id
        run_state = RunStateTracker(run_state_dir / "state.json", run_state_dir / "events.jsonl")
        run_state.update(
            run_type="data_sync",
            run_id=run_id,
            status="running",
            step_word="RUN_START",
            mode=str(args.mode),
            tasks_total=int(total),
            tasks_completed=0,
            tasks_failed=0,
            pct_complete=_format_pct(0, total),
            dry_run=int(bool(args.dry_run)),
        )
        run_state.event("RUN_START", run_id=run_id, mode=str(args.mode), tasks_total=int(total))

    failures: List[str] = []
    completed = 0
    task_records: List[Dict[str, object]] = []
    for i, (pair, timeframe) in enumerate(tasks, start=1):
        pct = _format_pct(i - 1, total)
        task_status = "running"
        terminal_state_written = False
        if run_state is not None:
            run_state.event(
                "TASK_START",
                task_index=int(i),
                tasks_total=int(total),
                pair=str(pair),
                timeframe=str(timeframe),
            )
        pair_file = pair_fs(pair)
        file_name = f"{pair_file}-{timeframe}.{args.data_format_ohlcv}"
        container_file = f"{args.data_dir.rstrip('/')}/{file_name}"
        host_file = container_to_host_path(container_file, user_data_dir)

        before = get_coverage(root_dir, args.service, container_file)
        before_min = str(before.get("min_day") or "")
        before_max = str(before.get("max_day") or "")
        before_rows = int(before.get("rows") or 0)
        end_day = str(args.end_day or day_now_utc())

        skip_reason = ""
        prepend_flag = False
        timerange = str(args.timerange or "")
        if args.mode == "append":
            if before_max:
                if before_max >= end_day:
                    skip_reason = f"already_up_to_date max_day={before_max} target_end={end_day}"
                start_day = add_days(before_max, -abs(int(args.overlap_days)))
            else:
                start_day = str(args.bootstrap_start)
            timerange = f"{start_day}-{end_day}"
        elif args.mode == "prepend":
            prepend_flag = True
            target_start = str(args.start_day)
            if before_min:
                if before_min <= target_start:
                    skip_reason = f"already_backfilled min_day={before_min} target_start={target_start}"
                prepend_end = add_days(before_min, abs(int(args.overlap_days)))
            else:
                prepend_end = end_day
            timerange = f"{target_start}-{prepend_end}"

        if skip_reason:
            completed += 1
            task_status = "skip"
            task_records.append(
                {
                    "pair": str(pair),
                    "timeframe": str(timeframe),
                    "status": "skip",
                    "reason": str(skip_reason),
                    "timerange": str(timerange),
                    "prepend": bool(prepend_flag),
                    "data_path": rel_payload_path(user_data_dir, host_file),
                    "before_rows": int(before_rows),
                    "before_min_day": before_min or "",
                    "before_max_day": before_max or "",
                }
            )
            print(
                f"[data-sync] task {i}/{total} pct={_format_pct(i, total)} pair={pair} tf={timeframe} "
                f"status=skip reason={skip_reason}",
                flush=True,
            )
            if run_state is not None:
                run_state.event(
                    "TASK_SKIP",
                    task_index=int(i),
                    pair=str(pair),
                    timeframe=str(timeframe),
                    reason=str(skip_reason),
                )
                run_state.update(
                    status="running",
                    step_word="TASK_DONE",
                    tasks_completed=int(completed),
                    tasks_failed=int(len(failures)),
                    pct_complete=_format_pct(completed, total),
                    last_task=f"{pair}|{timeframe}",
                    last_task_status="skip",
                )
            continue

        print(
            f"[data-sync] task {i}/{total} pct={pct} pair={pair} tf={timeframe} "
            f"timerange={timerange} prepend={int(prepend_flag)} before_rows={before_rows} "
            f"before_min={before_min or 'n/a'} before_max={before_max or 'n/a'}",
            flush=True,
        )

        dl_cmd = (
            f"freqtrade download-data "
            f"--config {q(args.config_path)} "
            f"--exchange {q(args.exchange)} "
            f"--pairs {q(pair)} "
            f"--timeframes {q(timeframe)} "
            f"--timerange {q(timerange)} "
            f"--data-format-ohlcv {q(args.data_format_ohlcv)} "
            f"--trading-mode {q(args.trading_mode)}"
        )
        if prepend_flag:
            dl_cmd = f"{dl_cmd} --prepend"
        if args.no_parallel_download:
            dl_cmd = f"{dl_cmd} --no-parallel-download"

        try:
            run_compose_inner(
                root_dir,
                args.service,
                dl_cmd,
                heartbeat_sec=int(args.heartbeat_sec),
                progress_label=f"download_{pair_file}_{timeframe}",
                progress_probe=(lambda hf=host_file: _probe_file(hf)),
                stalled_heartbeats_max=int(args.stalled_heartbeats_max),
                dry_run=args.dry_run,
            )
            after = get_coverage(root_dir, args.service, container_file)
            after_min = str(after.get("min_day") or "")
            after_max = str(after.get("max_day") or "")
            after_rows = int(after.get("rows") or 0)
            print(
                f"[data-sync] task {i}/{total} pct={_format_pct(i, total)} pair={pair} tf={timeframe} "
                f"status=ok rows_delta={after_rows - before_rows} after_rows={after_rows} "
                f"after_min={after_min or 'n/a'} after_max={after_max or 'n/a'}",
                flush=True,
            )
            task_status = "ok"
            task_records.append(
                {
                    "pair": str(pair),
                    "timeframe": str(timeframe),
                    "status": "ok",
                    "timerange": str(timerange),
                    "prepend": bool(prepend_flag),
                    "data_path": rel_payload_path(user_data_dir, host_file),
                    "before_rows": int(before_rows),
                    "after_rows": int(after_rows),
                    "rows_delta": int(after_rows - before_rows),
                    "before_min_day": before_min or "",
                    "before_max_day": before_max or "",
                    "after_min_day": after_min or "",
                    "after_max_day": after_max or "",
                }
            )
            if run_state is not None:
                run_state.event(
                    "TASK_DONE",
                    task_index=int(i),
                    pair=str(pair),
                    timeframe=str(timeframe),
                    status="ok",
                    before_rows=int(before_rows),
                    after_rows=int(after_rows),
                    rows_delta=int(after_rows - before_rows),
                    after_min=after_min or "",
                    after_max=after_max or "",
                )
        except KeyboardInterrupt:
            task_status = "interrupted"
            if run_state is not None:
                run_state.event(
                    "INTERRUPTED",
                    task_index=int(i),
                    pair=str(pair),
                    timeframe=str(timeframe),
                    tasks_completed=int(completed),
                )
                run_state.update(
                    status="interrupted",
                    step_word="INTERRUPTED",
                    tasks_completed=int(completed),
                    tasks_failed=int(len(failures)),
                    pct_complete=_format_pct(completed, total),
                    last_task=f"{pair}|{timeframe}",
                    last_task_status="interrupted",
                )
            terminal_state_written = True
            raise
        except Exception as exc:
            msg = f"pair={pair} tf={timeframe} error={exc}"
            failures.append(msg)
            task_status = "error"
            task_records.append(
                {
                    "pair": str(pair),
                    "timeframe": str(timeframe),
                    "status": "error",
                    "error": str(exc),
                    "timerange": str(timerange),
                    "prepend": bool(prepend_flag),
                    "data_path": rel_payload_path(user_data_dir, host_file),
                    "before_rows": int(before_rows),
                    "before_min_day": before_min or "",
                    "before_max_day": before_max or "",
                }
            )
            print(f"[data-sync] task {i}/{total} pct={_format_pct(i, total)} status=error {msg}", flush=True)
            if run_state is not None:
                run_state.event(
                    "TASK_ERROR",
                    task_index=int(i),
                    pair=str(pair),
                    timeframe=str(timeframe),
                    error=str(exc),
                )
            if args.fail_on_task_error:
                if run_state is not None:
                    run_state.update(
                        status="failed",
                        step_word="RUN_FAILED",
                        tasks_completed=int(completed),
                        tasks_failed=int(len(failures)),
                        pct_complete=_format_pct(completed, total),
                        last_task=f"{pair}|{timeframe}",
                        last_task_status="error",
                    )
                    run_state.event(
                        "RUN_FAILED",
                        run_id=run_id,
                        reason="fail_on_task_error",
                        task_index=int(i),
                    )
                    terminal_state_written = True
                raise
        finally:
            completed += 1
            if run_state is not None and (not terminal_state_written):
                run_state.update(
                    status="running",
                    step_word=("TASK_ERROR" if task_status == "error" else "TASK_DONE"),
                    tasks_completed=int(completed),
                    tasks_failed=int(len(failures)),
                    pct_complete=_format_pct(completed, total),
                    last_task=f"{pair}|{timeframe}",
                    last_task_status=str(task_status),
                )

    print(
        f"[data-sync] done completed={completed}/{total} pct={_format_pct(completed, total)} failures={len(failures)}",
        flush=True,
    )
    for item in failures:
        print(f"[data-sync] failure {item}", flush=True)
    rc = 0
    final_word = "RUN_COMPLETE"
    final_status = "completed"
    if failures:
        final_word = "RUN_COMPLETE_WITH_ERRORS"
        final_status = "completed_with_errors"
        if args.fail_on_task_error:
            rc = 1
            final_word = "RUN_FAILED"
            final_status = "failed"
    if run_state is not None:
        run_state.update(
            status=final_status,
            step_word=final_word,
            tasks_completed=int(completed),
            tasks_failed=int(len(failures)),
            pct_complete=_format_pct(completed, total),
            return_code=int(rc),
        )
        run_state.event(
            final_word,
            run_id=run_id,
            return_code=int(rc),
            tasks_total=int(total),
            tasks_completed=int(completed),
            tasks_failed=int(len(failures)),
        )
    latest_payload = {
        "run_type": "data_sync",
        "run_id": str(run_id),
        "status": str(final_status),
        "step_word": str(final_word),
        "return_code": int(rc),
        "mode": str(args.mode),
        "exchange": str(args.exchange),
        "pairs": [str(x) for x in args.pairs],
        "timeframes": [str(x) for x in args.timeframes],
        "tasks_total": int(total),
        "tasks_completed": int(completed),
        "tasks_failed": int(len(failures)),
        "tasks": task_records,
        "run_state_dir": rel_payload_path(
            user_data_dir,
            (user_data_dir / "run_state" / "data_sync" / run_id),
        ),
    }
    latest_ref = publish_latest_ref(user_data_dir, "data_sync", latest_payload)
    print(f"[data-sync] latest_ref wrote {latest_ref}", flush=True)
    return int(rc)


if __name__ == "__main__":
    raise SystemExit(main())
