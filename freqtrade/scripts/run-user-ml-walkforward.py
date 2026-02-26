#!/usr/bin/env python3
"""
Step 14 walk-forward ML evaluation for confidence overlay.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from latest_refs import publish_latest_ref, rel_payload_path
from ml_overlay_utils import (
    binary_metrics,
    build_leakage_safe_label_rows,
    build_walkforward_splits,
    read_json_obj,
    resolve_user_data,
    to_float,
    to_int,
    utc_now_iso,
    walkforward_summary_path,
    write_json_atomic,
)

FEATURE_COLUMNS: Sequence[str] = (
    "feature_pnl_pct",
    "feature_pnl_quote",
    "feature_stop_events",
    "feature_action_start",
    "feature_seed_events",
    "feature_rebuild_events",
    "feature_soft_adjust_events",
    "feature_fills",
    "feature_stop_per_start",
    "feature_churn_per_action",
    "feature_stop_per_fill",
)


def _default_run_id(label_source: str) -> str:
    return f"ml_wf_eval_{label_source}"


def _read_rows_csv(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def _write_rows_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: List[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fields:
                fields.append(str(key))
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _coerce_rows(raw_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for r in raw_rows:
        row = dict(r)
        for key in (
            "sample_index",
            "source_window_index",
            "feature_cutoff_window_index",
            "label_start_window_index",
            "label_end_window_index",
            "label_valid",
            "leakage_safe",
            "feature_stop_events",
            "feature_action_start",
            "feature_seed_events",
            "feature_rebuild_events",
            "feature_soft_adjust_events",
            "feature_fills",
            "future_failed_windows",
            "y_range_continuation",
            "y_breakout_risk",
        ):
            if key in row:
                row[key] = to_int(row.get(key), 0)
        for key in (
            "feature_pnl_pct",
            "feature_pnl_quote",
            "feature_stop_per_start",
            "feature_churn_per_action",
            "feature_stop_per_fill",
            "future_avg_pnl_pct",
            "future_avg_stop_per_start",
        ):
            if key in row:
                row[key] = to_float(row.get(key), 0.0)
        out.append(row)
    out.sort(key=lambda x: to_int(x.get("source_window_index"), 0))
    return out


def _fit_predict_binary(
    train_x: np.ndarray,
    train_y: np.ndarray,
    test_x: np.ndarray,
) -> Tuple[float, str]:
    if train_x.shape[0] <= 0:
        return 0.5, "no_train_rows"

    uniq = np.unique(train_y)
    if uniq.size < 2:
        return float(np.clip(np.mean(train_y), 0.0, 1.0)), "single_class_train"

    model = Pipeline(
        steps=[
            ("scale", StandardScaler()),
            (
                "logreg",
                LogisticRegression(
                    max_iter=500,
                    random_state=42,
                    class_weight="balanced",
                    solver="lbfgs",
                ),
            ),
        ]
    )
    model.fit(train_x, train_y)
    prob = model.predict_proba(test_x)[0, 1]
    return float(np.clip(prob, 0.0, 1.0)), "model"


def _check(name: str, passed: bool, observed: Any, threshold: Any, op: str, *, skipped: bool = False) -> Dict[str, Any]:
    return {
        "name": str(name),
        "passed": bool(passed),
        "observed": observed,
        "threshold": threshold,
        "operator": str(op),
        "skipped": bool(skipped),
    }


def _resolve_labels(
    user_data: Path,
    *,
    labels_csv: str,
    labels_run_id: str,
    walkforward_run_id: str,
    summary_path: str,
    horizon_windows: int,
    range_pnl_threshold: float,
    breakout_stop_rate_threshold: float,
    breakout_pnl_threshold: float,
) -> Tuple[List[Dict[str, Any]], str, str]:
    if str(labels_csv).strip():
        path = Path(str(labels_csv)).resolve()
        if not path.exists():
            raise FileNotFoundError(f"labels csv not found: {path}")
        return _coerce_rows(_read_rows_csv(path)), "labels_csv", str(path)

    if str(labels_run_id).strip():
        path = user_data / "ml_overlay" / "labels" / str(labels_run_id).strip() / "labels.csv"
        if not path.exists():
            raise FileNotFoundError(f"labels run not found: {path}")
        return _coerce_rows(_read_rows_csv(path)), "labels_run", str(path)

    wf_run_id = str(walkforward_run_id).strip()
    wf_summary_path = Path(str(summary_path)).resolve() if str(summary_path).strip() else None
    if wf_summary_path is None:
        if not wf_run_id:
            raise ValueError(
                "Provide --labels-csv, --labels-run-id, or walkforward source via --walkforward-run-id/--summary-path."
            )
        wf_summary_path = walkforward_summary_path(user_data, wf_run_id)
    if not wf_summary_path.exists():
        raise FileNotFoundError(f"walkforward summary not found: {wf_summary_path}")

    summary = read_json_obj(wf_summary_path)
    rows = build_leakage_safe_label_rows(
        summary,
        horizon_windows=max(1, int(horizon_windows)),
        range_pnl_threshold=float(range_pnl_threshold),
        breakout_stop_rate_threshold=float(breakout_stop_rate_threshold),
        breakout_pnl_threshold=float(breakout_pnl_threshold),
    )
    return _coerce_rows(rows), "walkforward_summary", str(wf_summary_path)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user-data", default="user_data")
    ap.add_argument("--labels-csv", default="")
    ap.add_argument("--labels-run-id", default="")
    ap.add_argument("--walkforward-run-id", default="")
    ap.add_argument("--summary-path", default="")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--horizon-windows", type=int, default=1)
    ap.add_argument("--min-train-samples", type=int, default=8)
    ap.add_argument("--purge-windows", type=int, default=1)
    ap.add_argument("--embargo-windows", type=int, default=1)
    ap.add_argument("--range-pnl-threshold", type=float, default=0.0)
    ap.add_argument("--breakout-stop-rate-threshold", type=float, default=1.0)
    ap.add_argument("--breakout-pnl-threshold", type=float, default=-0.2)
    ap.add_argument("--confidence-min", type=float, default=0.60)
    ap.add_argument("--min-range-auc", type=float, default=0.52)
    ap.add_argument("--min-breakout-auc", type=float, default=0.52)
    ap.add_argument("--max-range-brier", type=float, default=0.30)
    ap.add_argument("--max-breakout-brier", type=float, default=0.30)
    ap.add_argument("--max-range-ece", type=float, default=0.20)
    ap.add_argument("--max-breakout-ece", type=float, default=0.20)
    ap.add_argument("--min-coverage", type=float, default=0.10)
    return ap


def main() -> int:
    args = build_parser().parse_args()
    root_dir = Path(__file__).resolve().parents[1]
    user_data = resolve_user_data(root_dir, str(args.user_data))
    if not user_data.is_dir():
        raise FileNotFoundError(f"user_data directory not found: {user_data}")

    rows, source_type, source_path = _resolve_labels(
        user_data,
        labels_csv=str(args.labels_csv),
        labels_run_id=str(args.labels_run_id),
        walkforward_run_id=str(args.walkforward_run_id),
        summary_path=str(args.summary_path),
        horizon_windows=max(1, int(args.horizon_windows)),
        range_pnl_threshold=float(args.range_pnl_threshold),
        breakout_stop_rate_threshold=float(args.breakout_stop_rate_threshold),
        breakout_pnl_threshold=float(args.breakout_pnl_threshold),
    )
    if not rows:
        raise ValueError("No label rows available for ML evaluation.")

    label_source = str(args.labels_run_id).strip() or Path(source_path).stem
    out_run_id = str(args.run_id).strip() or _default_run_id(label_source.replace(".", "_"))
    out_dir = user_data / "ml_overlay" / "walkforward" / out_run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    splits = build_walkforward_splits(
        rows,
        min_train_samples=max(1, int(args.min_train_samples)),
        purge_windows=max(0, int(args.purge_windows)),
        embargo_windows=max(0, int(args.embargo_windows)),
    )
    row_by_window = {to_int(r.get("source_window_index"), 0): r for r in rows}

    pred_rows: List[Dict[str, Any]] = []
    range_y_true: List[int] = []
    range_y_prob: List[float] = []
    breakout_y_true: List[int] = []
    breakout_y_prob: List[float] = []

    for split in splits:
        test_idx = to_int(split.get("test_source_window_index"), 0)
        train_idx = [to_int(x, 0) for x in split.get("train_source_window_indices", [])]
        test_row = row_by_window.get(test_idx)
        if not isinstance(test_row, dict):
            continue
        if to_int(test_row.get("label_valid"), 0) != 1:
            continue

        train_rows = [
            row_by_window[i]
            for i in train_idx
            if i in row_by_window and to_int(row_by_window[i].get("label_valid"), 0) == 1
        ]
        if len(train_rows) < max(1, int(args.min_train_samples)):
            continue

        x_train = np.asarray(
            [
                [to_float(r.get(col), 0.0) for col in FEATURE_COLUMNS]
                for r in train_rows
            ],
            dtype=float,
        )
        x_test = np.asarray([[to_float(test_row.get(col), 0.0) for col in FEATURE_COLUMNS]], dtype=float)

        y_train_range = np.asarray([to_int(r.get("y_range_continuation"), 0) for r in train_rows], dtype=float)
        y_train_breakout = np.asarray([to_int(r.get("y_breakout_risk"), 0) for r in train_rows], dtype=float)

        p_range, mode_range = _fit_predict_binary(x_train, y_train_range, x_test)
        p_breakout, mode_breakout = _fit_predict_binary(x_train, y_train_breakout, x_test)

        y_true_range = to_int(test_row.get("y_range_continuation"), 0)
        y_true_breakout = to_int(test_row.get("y_breakout_risk"), 0)
        range_y_true.append(int(y_true_range))
        range_y_prob.append(float(p_range))
        breakout_y_true.append(int(y_true_breakout))
        breakout_y_prob.append(float(p_breakout))

        pred_rows.append(
            {
                "test_source_window_index": int(test_idx),
                "train_size": int(len(train_rows)),
                "p_range_continuation": float(p_range),
                "p_breakout_risk": float(p_breakout),
                "y_range_continuation": int(y_true_range),
                "y_breakout_risk": int(y_true_breakout),
                "predict_mode_range": str(mode_range),
                "predict_mode_breakout": str(mode_breakout),
            }
        )

    range_metrics = binary_metrics(range_y_true, range_y_prob, confidence_min=float(args.confidence_min))
    breakout_metrics = binary_metrics(
        breakout_y_true,
        breakout_y_prob,
        confidence_min=float(args.confidence_min),
    )

    checks: List[Dict[str, Any]] = []
    checks.append(
        _check(
            "min_range_auc",
            (range_metrics.get("auc") is not None)
            and float(range_metrics.get("auc") or 0.0) >= float(args.min_range_auc),
            range_metrics.get("auc"),
            float(args.min_range_auc),
            ">=",
            skipped=(range_metrics.get("auc") is None),
        )
    )
    checks.append(
        _check(
            "min_breakout_auc",
            (breakout_metrics.get("auc") is not None)
            and float(breakout_metrics.get("auc") or 0.0) >= float(args.min_breakout_auc),
            breakout_metrics.get("auc"),
            float(args.min_breakout_auc),
            ">=",
            skipped=(breakout_metrics.get("auc") is None),
        )
    )
    checks.append(
        _check(
            "max_range_brier",
            (range_metrics.get("brier") is not None)
            and float(range_metrics.get("brier") or 0.0) <= float(args.max_range_brier),
            range_metrics.get("brier"),
            float(args.max_range_brier),
            "<=",
        )
    )
    checks.append(
        _check(
            "max_breakout_brier",
            (breakout_metrics.get("brier") is not None)
            and float(breakout_metrics.get("brier") or 0.0) <= float(args.max_breakout_brier),
            breakout_metrics.get("brier"),
            float(args.max_breakout_brier),
            "<=",
        )
    )
    checks.append(
        _check(
            "max_range_ece",
            (range_metrics.get("ece") is not None)
            and float(range_metrics.get("ece") or 0.0) <= float(args.max_range_ece),
            range_metrics.get("ece"),
            float(args.max_range_ece),
            "<=",
        )
    )
    checks.append(
        _check(
            "max_breakout_ece",
            (breakout_metrics.get("ece") is not None)
            and float(breakout_metrics.get("ece") or 0.0) <= float(args.max_breakout_ece),
            breakout_metrics.get("ece"),
            float(args.max_breakout_ece),
            "<=",
        )
    )
    checks.append(
        _check(
            "min_range_coverage",
            float(range_metrics.get("coverage") or 0.0) >= float(args.min_coverage),
            float(range_metrics.get("coverage") or 0.0),
            float(args.min_coverage),
            ">=",
        )
    )
    checks.append(
        _check(
            "min_breakout_coverage",
            float(breakout_metrics.get("coverage") or 0.0) >= float(args.min_coverage),
            float(breakout_metrics.get("coverage") or 0.0),
            float(args.min_coverage),
            ">=",
        )
    )

    gates_passed = bool(all(bool(c.get("passed")) or bool(c.get("skipped")) for c in checks))
    predictions_csv = out_dir / "predictions.csv"
    _write_rows_csv(predictions_csv, pred_rows)

    summary_payload = {
        "created_utc": utc_now_iso(),
        "run_type": "ml_overlay_walkforward_eval",
        "run_id": out_run_id,
        "label_source_type": source_type,
        "label_source_path": source_path,
        "features": list(FEATURE_COLUMNS),
        "horizon_windows": int(max(1, int(args.horizon_windows))),
        "purge_windows": int(max(0, int(args.purge_windows))),
        "embargo_windows": int(max(0, int(args.embargo_windows))),
        "min_train_samples": int(max(1, int(args.min_train_samples))),
        "splits_total": int(len(splits)),
        "predictions_total": int(len(pred_rows)),
        "targets": {
            "range_continuation": range_metrics,
            "breakout_risk": breakout_metrics,
        },
        "gates": {
            "passed": bool(gates_passed),
            "checks": checks,
            "confidence_min": float(args.confidence_min),
        },
        "artifacts": {
            "predictions_csv": str(predictions_csv),
            "summary_json": str(out_dir / "summary.json"),
        },
    }
    write_json_atomic(out_dir / "summary.json", summary_payload)

    latest_payload = {
        "run_type": "ml_overlay_walkforward_eval",
        "run_id": out_run_id,
        "out_dir": rel_payload_path(user_data, out_dir),
        "summary_path": rel_payload_path(user_data, out_dir / "summary.json"),
        "predictions_path": rel_payload_path(user_data, predictions_csv),
        "gates_passed": bool(gates_passed),
        "predictions_total": int(len(pred_rows)),
    }
    ref = publish_latest_ref(user_data, "ml_overlay_eval", latest_payload)

    print(f"[ml-wf-eval] wrote {out_dir / 'summary.json'}")
    print(f"[ml-wf-eval] latest_ref wrote {ref}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
