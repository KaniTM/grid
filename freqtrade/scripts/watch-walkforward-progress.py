#!/usr/bin/env python3
"""
Watch one or more walkforward run state files and print changes.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--user-data",
        default="/home/kani/grid-ml-system/freqtrade/user_data",
        help="Path to user_data directory.",
    )
    ap.add_argument("--run-id", action="append", required=True, help="Walkforward run-id (repeatable).")
    ap.add_argument("--interval-sec", type=int, default=10, help="Poll interval in seconds.")
    ap.add_argument("--once", action="store_true", help="Print a single snapshot and exit.")
    ap.add_argument(
        "--exit-when-all-terminal",
        action="store_true",
        help="Exit when all runs are completed/failed/interrupted.",
    )
    return ap


def _read_state(state_path: Path) -> Dict:
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _sig(d: Dict) -> Tuple:
    return (
        str(d.get("status") or ""),
        int(d.get("windows_completed") or 0),
        int(d.get("windows_total") or 0),
        str(d.get("pct_complete") or ""),
        int(d.get("windows_failed") or 0),
        str(d.get("step_word") or ""),
        str(d.get("last_window_timerange") or ""),
        str(d.get("error") or ""),
    )


def _terminal(status: str) -> bool:
    return status in {"completed", "failed", "interrupted"}


def main() -> int:
    args = build_parser().parse_args()
    user_data = Path(args.user_data).resolve()
    interval = max(1, int(args.interval_sec))
    run_ids = [str(r).strip() for r in args.run_id if str(r).strip()]
    if not run_ids:
        raise ValueError("Provide at least one --run-id.")

    last: Dict[str, Tuple] = {}
    while True:
        all_terminal = True
        for run_id in run_ids:
            state_path = user_data / "walkforward" / run_id / "_state" / "state.json"
            if not state_path.exists():
                sig = ("missing", 0, 0, "", 0, "", "", "")
                if last.get(run_id) != sig:
                    print(f"{_now_utc()} run={run_id} state=missing path={state_path}", flush=True)
                    last[run_id] = sig
                all_terminal = False
                continue

            d = _read_state(state_path)
            sig = _sig(d)
            if last.get(run_id) != sig:
                status, done, total, pct, failed, step, tr, err = sig
                print(
                    f"{_now_utc()} run={run_id} status={status} done={done}/{total} "
                    f"pct={pct} failed={failed} step={step} last={tr} error={err}",
                    flush=True,
                )
                last[run_id] = sig
            if not _terminal(str(d.get("status") or "")):
                all_terminal = False

        if args.once:
            return 0
        if args.exit_when_all_terminal and all_terminal:
            return 0
        time.sleep(interval)


if __name__ == "__main__":
    raise SystemExit(main())
