#!/usr/bin/env python3
"""
Build leakage-safe Step 14 ML labels from a walkforward summary.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List

from latest_refs import publish_latest_ref, rel_payload_path
from ml_overlay_utils import (
    build_leakage_safe_label_rows,
    build_walkforward_splits,
    read_json_obj,
    resolve_user_data,
    utc_now_iso,
    walkforward_summary_path,
    write_json_atomic,
)


def _default_run_id(walkforward_run_id: str) -> str:
    stem = str(walkforward_run_id or "").strip() or "walkforward"
    return f"ml_labels_{stem}"


def _write_rows_csv(path: Path, rows: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: List[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(str(key))
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user-data", default="user_data")
    ap.add_argument("--walkforward-run-id", default="", help="Run id under user_data/walkforward.")
    ap.add_argument("--summary-path", default="", help="Optional explicit summary.json path.")
    ap.add_argument("--run-id", default="", help="Output run-id under user_data/ml_overlay/labels.")
    ap.add_argument("--horizon-windows", type=int, default=1)
    ap.add_argument("--min-train-samples", type=int, default=8)
    ap.add_argument("--purge-windows", type=int, default=1)
    ap.add_argument("--embargo-windows", type=int, default=1)
    ap.add_argument("--range-pnl-threshold", type=float, default=0.0)
    ap.add_argument("--breakout-stop-rate-threshold", type=float, default=1.0)
    ap.add_argument("--breakout-pnl-threshold", type=float, default=-0.2)
    return ap


def main() -> int:
    args = build_parser().parse_args()
    root_dir = Path(__file__).resolve().parents[1]
    user_data = resolve_user_data(root_dir, str(args.user_data))
    if not user_data.is_dir():
        raise FileNotFoundError(f"user_data directory not found: {user_data}")

    summary_path = Path(str(args.summary_path)).resolve() if str(args.summary_path).strip() else None
    run_id = str(args.walkforward_run_id or "").strip()
    if summary_path is None:
        if not run_id:
            raise ValueError("Provide --walkforward-run-id or --summary-path")
        summary_path = walkforward_summary_path(user_data, run_id)

    if not summary_path.exists():
        raise FileNotFoundError(f"Walkforward summary not found: {summary_path}")

    summary = read_json_obj(summary_path)
    effective_wf_run_id = run_id or str(summary.get("run_id") or summary_path.parent.name)
    out_run_id = str(args.run_id).strip() or _default_run_id(effective_wf_run_id)
    out_dir = user_data / "ml_overlay" / "labels" / out_run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = build_leakage_safe_label_rows(
        summary,
        horizon_windows=max(1, int(args.horizon_windows)),
        range_pnl_threshold=float(args.range_pnl_threshold),
        breakout_stop_rate_threshold=float(args.breakout_stop_rate_threshold),
        breakout_pnl_threshold=float(args.breakout_pnl_threshold),
    )
    splits = build_walkforward_splits(
        rows,
        min_train_samples=max(1, int(args.min_train_samples)),
        purge_windows=max(0, int(args.purge_windows)),
        embargo_windows=max(0, int(args.embargo_windows)),
    )

    labels_csv = out_dir / "labels.csv"
    _write_rows_csv(labels_csv, rows)

    valid_rows = [r for r in rows if int(r.get("label_valid", 0)) == 1]
    leak_violations = [
        r
        for r in rows
        if int(r.get("leakage_safe", 0)) != 1
        or int(r.get("label_start_window_index", 0)) <= int(r.get("feature_cutoff_window_index", 0))
    ]
    label_summary = {
        "created_utc": utc_now_iso(),
        "run_type": "ml_labels",
        "run_id": out_run_id,
        "walkforward_run_id": effective_wf_run_id,
        "summary_path": str(summary_path),
        "horizon_windows": int(max(1, int(args.horizon_windows))),
        "purge_windows": int(max(0, int(args.purge_windows))),
        "embargo_windows": int(max(0, int(args.embargo_windows))),
        "min_train_samples": int(max(1, int(args.min_train_samples))),
        "range_pnl_threshold": float(args.range_pnl_threshold),
        "breakout_stop_rate_threshold": float(args.breakout_stop_rate_threshold),
        "breakout_pnl_threshold": float(args.breakout_pnl_threshold),
        "rows_total": int(len(rows)),
        "rows_valid": int(len(valid_rows)),
        "split_count": int(len(splits)),
        "leakage_checks": {
            "feature_uses_future": False,
            "label_starts_after_feature_cutoff": bool(len(leak_violations) == 0),
            "violations": int(len(leak_violations)),
        },
        "target_balance": {
            "range_continuation_positive": int(
                sum(1 for r in valid_rows if int(r.get("y_range_continuation", 0)) == 1)
            ),
            "breakout_risk_positive": int(
                sum(1 for r in valid_rows if int(r.get("y_breakout_risk", 0)) == 1)
            ),
        },
        "artifacts": {
            "labels_csv": str(labels_csv),
            "splits_file": str(out_dir / "splits.json"),
        },
    }

    splits_payload = {
        "created_utc": utc_now_iso(),
        "run_type": "ml_labels_splits",
        "run_id": out_run_id,
        "walkforward_run_id": effective_wf_run_id,
        "split_count": int(len(splits)),
        "splits": splits,
    }
    write_json_atomic(out_dir / "splits.json", splits_payload)
    write_json_atomic(out_dir / "summary.json", label_summary)

    latest_payload = {
        "run_type": "ml_labels",
        "run_id": out_run_id,
        "walkforward_run_id": effective_wf_run_id,
        "out_dir": rel_payload_path(user_data, out_dir),
        "summary_path": rel_payload_path(user_data, out_dir / "summary.json"),
        "labels_path": rel_payload_path(user_data, labels_csv),
        "rows_total": int(len(rows)),
        "rows_valid": int(len(valid_rows)),
        "split_count": int(len(splits)),
        "leakage_violations": int(len(leak_violations)),
    }
    ref = publish_latest_ref(user_data, "ml_labels", latest_payload)

    print(f"[ml-labels] wrote {out_dir / 'summary.json'}")
    print(f"[ml-labels] latest_ref wrote {ref}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
