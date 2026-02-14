#!/usr/bin/env python3
"""
Integrity checks for compact walkforward outputs and AB compare artifacts.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def parse_day_timerange(timerange: str) -> Tuple[datetime, datetime]:
    if "-" not in str(timerange):
        raise ValueError(f"Invalid timerange: {timerange!r}")
    a, b = str(timerange).split("-", 1)
    start = datetime.strptime(a, "%Y%m%d").replace(tzinfo=timezone.utc)
    end = datetime.strptime(b, "%Y%m%d").replace(tzinfo=timezone.utc)
    if end <= start:
        raise ValueError(f"Invalid timerange order: {timerange!r}")
    return start, end


def fmt_day(dt: datetime) -> str:
    return dt.strftime("%Y%m%d")


def iter_windows(
    start: datetime, end: datetime, window_days: int, step_days: int, min_window_days: int
) -> List[Tuple[int, str]]:
    out: List[Tuple[int, str]] = []
    idx = 1
    cur = start
    while cur < end:
        w_end = min(cur + timedelta(days=int(window_days)), end)
        if (w_end - cur).days < int(min_window_days):
            break
        out.append((idx, f"{fmt_day(cur)}-{fmt_day(w_end)}"))
        cur = cur + timedelta(days=int(step_days))
        idx += 1
    return out


def _is_bad_num(v: object) -> bool:
    return isinstance(v, float) and (math.isnan(v) or math.isinf(v))


def _read_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return payload


def _check_state_markers(run_dir: Path) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    state_file = run_dir / "_state" / "state.json"
    events_file = run_dir / "_state" / "events.jsonl"
    if not state_file.exists():
        errors.append(f"missing state file: {state_file}")
        return errors, warnings
    try:
        state = _read_json(state_file)
    except Exception as exc:
        errors.append(f"cannot parse state file {state_file}: {exc}")
        return errors, warnings
    status = str(state.get("status") or "")
    word = str(state.get("step_word") or "")
    if status != "completed":
        errors.append(f"state.status is not completed: {status!r}")
    if word != "RUN_COMPLETE":
        errors.append(f"state.step_word is not RUN_COMPLETE: {word!r}")
    if not events_file.exists():
        warnings.append(f"missing events file: {events_file}")
        return errors, warnings
    run_complete_found = False
    try:
        with events_file.open("r", encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if not s:
                    continue
                try:
                    rec = json.loads(s)
                except Exception:
                    continue
                if str(rec.get("word") or "") == "RUN_COMPLETE":
                    run_complete_found = True
                    break
    except Exception as exc:
        warnings.append(f"cannot read events file {events_file}: {exc}")
    if not run_complete_found:
        warnings.append(f"RUN_COMPLETE not found in {events_file}")
    return errors, warnings


def verify_walkforward_summary(path: Path, require_state_complete: bool) -> Tuple[Dict, List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    data = _read_json(path)
    run_dir = path.parent
    run_id = str(data.get("run_id") or run_dir.name)
    args = data.get("args") or {}
    agg = data.get("aggregate") or {}
    windows = data.get("windows") or []

    if not isinstance(args, dict):
        errors.append("args missing or invalid")
        args = {}
    if not isinstance(agg, dict):
        errors.append("aggregate missing or invalid")
        agg = {}
    if not isinstance(windows, list):
        errors.append("windows missing or invalid")
        windows = []

    # Summary/window cardinality checks
    if int(agg.get("windows_total") or 0) != int(len(windows)):
        errors.append(
            f"aggregate.windows_total mismatch: agg={agg.get('windows_total')} actual={len(windows)}"
        )

    # Expected window sequence from args
    timerange = str(args.get("timerange") or "")
    if timerange:
        try:
            wexp = iter_windows(
                *parse_day_timerange(timerange),
                window_days=int(args.get("window_days") or 0),
                step_days=int(args.get("step_days") or 0),
                min_window_days=int(args.get("min_window_days") or 0),
            )
            if len(wexp) != len(windows):
                errors.append(f"window count mismatch vs args-derived sequence: expected={len(wexp)} actual={len(windows)}")
            for i, row in enumerate(windows):
                if i >= len(wexp):
                    break
                exp_idx, exp_timerange = wexp[i]
                got_idx = int(row.get("index") or 0)
                got_timerange = str(row.get("timerange") or "")
                if got_idx != exp_idx:
                    errors.append(f"window index mismatch at pos={i}: expected={exp_idx} got={got_idx}")
                if got_timerange != exp_timerange:
                    errors.append(
                        f"window timerange mismatch at index={got_idx}: expected={exp_timerange} got={got_timerange}"
                    )
                start_day = str(row.get("start_day") or "")
                end_day = str(row.get("end_day") or "")
                exp_start, exp_end = exp_timerange.split("-", 1)
                if start_day != exp_start or end_day != exp_end:
                    errors.append(
                        f"window start/end mismatch index={got_idx}: expected={exp_start}-{exp_end} got={start_day}-{end_day}"
                    )
        except Exception as exc:
            errors.append(f"cannot derive expected windows from args.timerange: {exc}")
    else:
        warnings.append("args.timerange missing; skipped expected-window sequence check")

    # Status and numeric sanity checks
    ok_count = 0
    failed_count = 0
    bad_num_count = 0
    for row in windows:
        status = str(row.get("status") or "").lower()
        if status == "ok":
            ok_count += 1
        else:
            failed_count += 1
        for k in (
            "pnl_quote",
            "pnl_pct",
            "initial_equity",
            "end_equity",
            "end_quote",
            "end_base",
        ):
            if _is_bad_num(row.get(k)):
                bad_num_count += 1
                errors.append(f"bad numeric value at window={row.get('index')} field={k}: {row.get(k)!r}")
    if int(agg.get("windows_ok") or 0) != int(ok_count):
        errors.append(f"aggregate.windows_ok mismatch: agg={agg.get('windows_ok')} actual={ok_count}")
    if int(agg.get("windows_failed") or 0) != int(failed_count):
        errors.append(f"aggregate.windows_failed mismatch: agg={agg.get('windows_failed')} actual={failed_count}")
    # windows.csv row count check
    windows_csv = run_dir / "windows.csv"
    if windows_csv.exists():
        try:
            with windows_csv.open("r", encoding="utf-8", newline="") as f:
                n_rows = sum(1 for _ in csv.DictReader(f))
            if n_rows != len(windows):
                errors.append(f"windows.csv row count mismatch: csv={n_rows} summary={len(windows)}")
        except Exception as exc:
            errors.append(f"cannot read windows.csv: {exc}")
    else:
        warnings.append(f"windows.csv missing: {windows_csv}")

    if require_state_complete:
        state_errors, state_warnings = _check_state_markers(run_dir)
        errors.extend(state_errors)
        warnings.extend(state_warnings)

    info = {
        "run_id": run_id,
        "summary_path": str(path),
        "windows_total": len(windows),
        "windows_ok": ok_count,
        "windows_failed": failed_count,
        "timerange": timerange,
    }
    return info, errors, warnings


def verify_ab_compare(path: Path) -> Tuple[Dict, List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    payload = _read_json(path)
    for key in ("A", "B", "delta_B_minus_A"):
        if key not in payload or not isinstance(payload.get(key), dict):
            errors.append(f"missing section: {key}")
    for section_name in ("A", "B", "delta_B_minus_A"):
        section = payload.get(section_name, {})
        if not isinstance(section, dict):
            continue
        for k, v in section.items():
            if _is_bad_num(v):
                errors.append(f"bad numeric value in {section_name}.{k}: {v!r}")
    info = {
        "path": str(path),
        "A_run_id": str((payload.get("A") or {}).get("run_id") or ""),
        "B_run_id": str((payload.get("B") or {}).get("run_id") or ""),
    }
    if not info["A_run_id"] or not info["B_run_id"]:
        warnings.append("AB compare file is missing A.run_id or B.run_id")
    return info, errors, warnings


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user-data", default="user_data")
    ap.add_argument("--walkforward-run-id", action="append", default=[])
    ap.add_argument("--walkforward-summary", action="append", default=[])
    ap.add_argument("--ab-compare", action="append", default=[])
    ap.add_argument("--require-state-complete", action="store_true", default=True)
    ap.add_argument("--no-require-state-complete", action="store_false", dest="require_state_complete")
    return ap


def main() -> int:
    args = build_parser().parse_args()
    root_dir = Path(__file__).resolve().parents[1]
    user_data = Path(args.user_data)
    if not user_data.is_absolute():
        user_data = (root_dir / user_data).resolve()

    summary_paths: List[Path] = []
    for rid in args.walkforward_run_id:
        rid_s = str(rid).strip()
        if not rid_s:
            continue
        summary_paths.append((user_data / "walkforward" / rid_s / "summary.json").resolve())
    for item in args.walkforward_summary:
        p = Path(str(item))
        if not p.is_absolute():
            p = (root_dir / p).resolve()
        summary_paths.append(p)

    ab_paths: List[Path] = []
    for item in args.ab_compare:
        p = Path(str(item))
        if not p.is_absolute():
            p = (root_dir / p).resolve()
        ab_paths.append(p)

    if not summary_paths and not ab_paths:
        raise ValueError("Provide at least one --walkforward-run-id/--walkforward-summary or --ab-compare")

    all_errors: List[str] = []
    all_warnings: List[str] = []

    for summary in summary_paths:
        if not summary.exists():
            msg = f"missing walkforward summary: {summary}"
            print(f"[verify] error {msg}", flush=True)
            all_errors.append(msg)
            continue
        info, errors, warnings = verify_walkforward_summary(summary, bool(args.require_state_complete))
        print(
            f"[verify] walkforward run_id={info['run_id']} windows={info['windows_ok']}/{info['windows_total']} "
            f"failed={info['windows_failed']} timerange={info['timerange']}",
            flush=True,
        )
        for w in warnings:
            print(f"[verify] warning run_id={info['run_id']} {w}", flush=True)
        for e in errors:
            print(f"[verify] error run_id={info['run_id']} {e}", flush=True)
        all_warnings.extend([f"{info['run_id']}: {w}" for w in warnings])
        all_errors.extend([f"{info['run_id']}: {e}" for e in errors])

    for ab in ab_paths:
        if not ab.exists():
            msg = f"missing AB compare file: {ab}"
            print(f"[verify] error {msg}", flush=True)
            all_errors.append(msg)
            continue
        info, errors, warnings = verify_ab_compare(ab)
        print(
            f"[verify] ab_compare path={info['path']} A={info['A_run_id'] or 'n/a'} B={info['B_run_id'] or 'n/a'}",
            flush=True,
        )
        for w in warnings:
            print(f"[verify] warning ab_compare {w}", flush=True)
        for e in errors:
            print(f"[verify] error ab_compare {e}", flush=True)
        all_warnings.extend([f"ab_compare: {w}" for w in warnings])
        all_errors.extend([f"ab_compare: {e}" for e in errors])

    print(
        f"[verify] done errors={len(all_errors)} warnings={len(all_warnings)}",
        flush=True,
    )
    return 1 if all_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
