#!/usr/bin/env python3
"""
Utilities shared by Step 14 ML overlay scripts.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.metrics import brier_score_loss, roc_auc_score


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return float(default)
        return float(value)
    except Exception:
        return float(default)


def to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return int(default)
        return int(value)
    except Exception:
        return int(default)


def read_json_obj(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected object JSON: {path}")
    return payload


def write_json_atomic(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def resolve_user_data(root_dir: Path, user_data_arg: str) -> Path:
    user_data = Path(str(user_data_arg))
    if not user_data.is_absolute():
        user_data = (root_dir / user_data).resolve()
    return user_data


def walkforward_summary_path(user_data_dir: Path, run_id: str) -> Path:
    return user_data_dir / "walkforward" / str(run_id).strip() / "summary.json"


def _window_stop_per_start(window: Dict[str, Any]) -> float:
    stop_events = to_float(window.get("stop_events"), 0.0)
    action_start = max(to_float(window.get("action_start"), 0.0), 1.0)
    return float(stop_events / action_start)


def build_leakage_safe_label_rows(
    summary: Dict[str, Any],
    *,
    horizon_windows: int,
    range_pnl_threshold: float,
    breakout_stop_rate_threshold: float,
    breakout_pnl_threshold: float,
) -> List[Dict[str, Any]]:
    windows_raw = summary.get("windows", [])
    if not isinstance(windows_raw, list):
        return []

    ordered = [w for w in windows_raw if isinstance(w, dict)]
    ordered.sort(key=lambda w: to_int(w.get("index"), 0))
    out: List[Dict[str, Any]] = []
    horizon = max(1, int(horizon_windows))

    for pos, w in enumerate(ordered):
        status = str(w.get("status") or "").lower()
        if status != "ok":
            continue

        source_idx = to_int(w.get("index"), 0)
        future = ordered[pos + 1 : pos + 1 + horizon]
        label_valid = len(future) == horizon
        future_ok = [x for x in future if str(x.get("status") or "").lower() == "ok"]
        failed_count = int(len(future) - len(future_ok))

        future_avg_pnl = None
        future_avg_stop_rate = None
        if future_ok:
            future_avg_pnl = float(
                np.mean([to_float(x.get("pnl_pct"), 0.0) for x in future_ok], dtype=float)
            )
            future_avg_stop_rate = float(np.mean([_window_stop_per_start(x) for x in future_ok], dtype=float))

        y_range_continuation = None
        y_breakout_risk = None
        if label_valid:
            y_range_continuation = int(
                failed_count == 0
                and future_avg_pnl is not None
                and float(future_avg_pnl) >= float(range_pnl_threshold)
            )
            y_breakout_risk = int(
                failed_count > 0
                or (
                    future_avg_stop_rate is not None
                    and float(future_avg_stop_rate) >= float(breakout_stop_rate_threshold)
                )
                or (
                    future_avg_pnl is not None
                    and float(future_avg_pnl) <= float(breakout_pnl_threshold)
                )
            )

        source_stop = to_float(w.get("stop_events"), 0.0)
        source_action_start = max(to_float(w.get("action_start"), 0.0), 1.0)
        source_seed = to_float(w.get("seed_events"), 0.0)
        source_rebuild = to_float(w.get("rebuild_events"), 0.0)
        source_fills = max(to_float(w.get("fills"), 0.0), 1.0)
        source_soft_adjust = to_float(w.get("soft_adjust_events"), 0.0)
        source_churn = source_seed + source_rebuild + source_stop

        label_start_idx = source_idx + 1
        label_end_idx = source_idx + horizon if label_valid else None
        leakage_safe = bool(label_start_idx > source_idx)

        out.append(
            {
                "sample_index": int(len(out) + 1),
                "source_window_index": int(source_idx),
                "source_timerange": str(w.get("timerange") or ""),
                "source_status": str(w.get("status") or ""),
                "feature_cutoff_window_index": int(source_idx),
                "label_start_window_index": int(label_start_idx),
                "label_end_window_index": int(label_end_idx) if label_end_idx is not None else None,
                "label_valid": int(1 if label_valid else 0),
                "leakage_safe": int(1 if leakage_safe else 0),
                "feature_pnl_pct": to_float(w.get("pnl_pct"), 0.0),
                "feature_pnl_quote": to_float(w.get("pnl_quote"), 0.0),
                "feature_stop_events": int(source_stop),
                "feature_action_start": int(source_action_start),
                "feature_seed_events": int(source_seed),
                "feature_rebuild_events": int(source_rebuild),
                "feature_soft_adjust_events": int(source_soft_adjust),
                "feature_fills": int(source_fills),
                "feature_stop_per_start": float(source_stop / source_action_start),
                "feature_churn_per_action": float(source_churn / source_action_start),
                "feature_stop_per_fill": float(source_stop / source_fills),
                "future_failed_windows": int(failed_count),
                "future_avg_pnl_pct": future_avg_pnl,
                "future_avg_stop_per_start": future_avg_stop_rate,
                "y_range_continuation": y_range_continuation,
                "y_breakout_risk": y_breakout_risk,
            }
        )
    return out


def build_walkforward_splits(
    rows: List[Dict[str, Any]],
    *,
    min_train_samples: int,
    purge_windows: int,
    embargo_windows: int,
) -> List[Dict[str, Any]]:
    ordered = list(rows)
    ordered.sort(key=lambda r: to_int(r.get("source_window_index"), 0))
    min_train = max(1, int(min_train_samples))
    purge = max(0, int(purge_windows))
    embargo = max(0, int(embargo_windows))

    splits: List[Dict[str, Any]] = []
    for test_row in ordered:
        if int(test_row.get("label_valid", 0)) != 1:
            continue
        test_idx = to_int(test_row.get("source_window_index"), 0)
        train_idx: List[int] = []
        for row in ordered:
            if int(row.get("label_valid", 0)) != 1:
                continue
            row_idx = to_int(row.get("source_window_index"), 0)
            if row_idx >= test_idx:
                continue
            if row_idx > (test_idx - 1 - purge):
                continue
            row_label_end = to_int(row.get("label_end_window_index"), row_idx)
            if row_label_end > (test_idx - 1 - embargo):
                continue
            train_idx.append(int(row_idx))
        if len(train_idx) < min_train:
            continue
        splits.append(
            {
                "test_source_window_index": int(test_idx),
                "train_source_window_indices": sorted(set(train_idx)),
                "train_size": int(len(set(train_idx))),
            }
        )
    return splits


def expected_calibration_error(y_true: np.ndarray, y_prob: np.ndarray, bins: int = 10) -> float:
    if y_true.size == 0:
        return 0.0
    bins = max(2, int(bins))
    edges = np.linspace(0.0, 1.0, bins + 1)
    total = float(y_true.size)
    ece = 0.0
    for i in range(bins):
        lo = edges[i]
        hi = edges[i + 1]
        if i == bins - 1:
            mask = (y_prob >= lo) & (y_prob <= hi)
        else:
            mask = (y_prob >= lo) & (y_prob < hi)
        count = int(np.sum(mask))
        if count <= 0:
            continue
        conf = float(np.mean(y_prob[mask]))
        acc = float(np.mean(y_true[mask]))
        ece += (count / total) * abs(acc - conf)
    return float(ece)


def binary_metrics(y_true: List[int], y_prob: List[float], *, confidence_min: float) -> Dict[str, Any]:
    if not y_true:
        return {
            "n_eval": 0,
            "positive_rate": 0.0,
            "auc": None,
            "brier": None,
            "ece": None,
            "coverage": 0.0,
            "accuracy": None,
        }

    y = np.asarray(y_true, dtype=float)
    p = np.asarray(y_prob, dtype=float)
    pred = (p >= 0.5).astype(float)
    confidence = np.maximum(p, 1.0 - p)

    auc = None
    if np.unique(y).size > 1:
        auc = float(roc_auc_score(y, p))

    brier = float(brier_score_loss(y, p))
    ece = float(expected_calibration_error(y, p, bins=10))
    coverage = float(np.mean(confidence >= float(confidence_min)))
    accuracy = float(np.mean(pred == y))

    return {
        "n_eval": int(y.size),
        "positive_rate": float(np.mean(y)),
        "auc": auc,
        "brier": brier,
        "ece": ece,
        "coverage": coverage,
        "accuracy": accuracy,
    }
