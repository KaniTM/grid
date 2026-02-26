#!/usr/bin/env python3
"""
Compare deterministic-only vs deterministic+ML walkforward runs.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional

from latest_refs import publish_latest_ref, rel_payload_path
from ml_overlay_utils import (
    read_json_obj,
    resolve_user_data,
    to_float,
    to_int,
    utc_now_iso,
    walkforward_summary_path,
    write_json_atomic,
)


def _collect_wf_metrics(summary: Dict[str, Any], run_id: str) -> Dict[str, Any]:
    agg = summary.get("aggregate", {}) if isinstance(summary.get("aggregate"), dict) else {}
    windows = summary.get("windows", []) if isinstance(summary.get("windows"), list) else []
    ok_rows = [w for w in windows if isinstance(w, dict) and str(w.get("status", "")).lower() == "ok"]

    sum_seed = int(sum(to_int(w.get("seed_events"), 0) for w in ok_rows))
    sum_rebuild = int(sum(to_int(w.get("rebuild_events"), 0) for w in ok_rows))
    sum_stop = int(sum(to_int(w.get("stop_events"), 0) for w in ok_rows))
    sum_action_start = int(sum(to_int(w.get("action_start"), 0) for w in ok_rows))
    windows_ok = int(agg.get("windows_ok", len(ok_rows)) or len(ok_rows))
    windows_failed = int(agg.get("windows_failed", 0) or 0)

    churn_total = int(sum_seed + sum_rebuild + sum_stop)
    churn_events_per_window = float(churn_total / max(1, windows_ok))
    false_start_rate = float(sum_stop / max(1, sum_action_start))
    stop_events_per_window = float(sum_stop / max(1, windows_ok))

    return {
        "run_id": str(run_id),
        "windows_total": int(agg.get("windows_total", len(windows)) or len(windows)),
        "windows_ok": int(windows_ok),
        "windows_failed": int(windows_failed),
        "sum_pnl_quote": float(to_float(agg.get("sum_pnl_quote"), 0.0)),
        "avg_pnl_pct": float(to_float(agg.get("avg_pnl_pct"), 0.0)),
        "median_pnl_pct": float(to_float(agg.get("median_pnl_pct"), 0.0)),
        "win_rate": float(to_float(agg.get("win_rate"), 0.0)),
        "profit_factor": float(to_float(agg.get("profit_factor"), 0.0)),
        "churn_events_per_window": float(churn_events_per_window),
        "false_start_rate": float(false_start_rate),
        "stop_events_per_window": float(stop_events_per_window),
    }


def _check(name: str, passed: bool, observed: Any, threshold: Any, op: str, *, skipped: bool = False) -> Dict[str, Any]:
    return {
        "name": str(name),
        "passed": bool(passed),
        "observed": observed,
        "threshold": threshold,
        "operator": str(op),
        "skipped": bool(skipped),
    }


def _load_ml_eval_summary(
    user_data: Path,
    *,
    run_id: str,
    summary_path: str,
) -> Optional[Dict[str, Any]]:
    if str(summary_path).strip():
        path = Path(str(summary_path)).resolve()
        if not path.exists():
            raise FileNotFoundError(f"ML eval summary not found: {path}")
        return read_json_obj(path)
    if str(run_id).strip():
        path = user_data / "ml_overlay" / "walkforward" / str(run_id).strip() / "summary.json"
        if not path.exists():
            raise FileNotFoundError(f"ML eval run summary not found: {path}")
        return read_json_obj(path)
    return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user-data", default="user_data")
    ap.add_argument("--run-det", required=True, help="Deterministic-only walkforward run id (baseline A).")
    ap.add_argument("--run-ml", required=True, help="ML-overlay walkforward run id (candidate B).")
    ap.add_argument("--run-id", default="", help="Output run id under user_data/ml_overlay/compare.")
    ap.add_argument("--label", default="", help="Optional label for traceability.")
    ap.add_argument("--ml-eval-run-id", default="", help="Optional ml_overlay_walkforward_eval run id.")
    ap.add_argument("--ml-eval-summary", default="", help="Optional explicit path to ml eval summary.")
    ap.add_argument("--require-ml-eval-pass", action="store_true")
    ap.add_argument("--min-avg-pnl-delta", type=float, default=0.0)
    ap.add_argument("--min-sum-pnl-delta", type=float, default=0.0)
    ap.add_argument("--max-failed-window-delta", type=int, default=0)
    ap.add_argument("--max-churn-degradation-pct", type=float, default=20.0)
    ap.add_argument("--max-false-start-degradation-pct", type=float, default=25.0)
    ap.add_argument("--max-stop-events-multiplier", type=float, default=1.25)
    return ap


def main() -> int:
    args = build_parser().parse_args()
    root_dir = Path(__file__).resolve().parents[1]
    user_data = resolve_user_data(root_dir, str(args.user_data))
    if not user_data.is_dir():
        raise FileNotFoundError(f"user_data directory not found: {user_data}")

    det_run_id = str(args.run_det).strip()
    ml_run_id = str(args.run_ml).strip()
    det_summary = walkforward_summary_path(user_data, det_run_id)
    ml_summary = walkforward_summary_path(user_data, ml_run_id)
    if not det_summary.exists():
        raise FileNotFoundError(f"deterministic summary not found: {det_summary}")
    if not ml_summary.exists():
        raise FileNotFoundError(f"ml summary not found: {ml_summary}")

    det_metrics = _collect_wf_metrics(read_json_obj(det_summary), det_run_id)
    ml_metrics = _collect_wf_metrics(read_json_obj(ml_summary), ml_run_id)

    ml_eval = _load_ml_eval_summary(
        user_data,
        run_id=str(args.ml_eval_run_id),
        summary_path=str(args.ml_eval_summary),
    )

    run_id = str(args.run_id).strip() or f"ml_overlay_compare_{det_run_id}_vs_{ml_run_id}"
    out_dir = user_data / "ml_overlay" / "compare" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    delta = {
        "windows_ok": int(ml_metrics["windows_ok"] - det_metrics["windows_ok"]),
        "windows_failed": int(ml_metrics["windows_failed"] - det_metrics["windows_failed"]),
        "sum_pnl_quote": float(ml_metrics["sum_pnl_quote"] - det_metrics["sum_pnl_quote"]),
        "avg_pnl_pct": float(ml_metrics["avg_pnl_pct"] - det_metrics["avg_pnl_pct"]),
        "win_rate": float(ml_metrics["win_rate"] - det_metrics["win_rate"]),
        "profit_factor": float(ml_metrics["profit_factor"] - det_metrics["profit_factor"]),
        "churn_events_per_window": float(
            ml_metrics["churn_events_per_window"] - det_metrics["churn_events_per_window"]
        ),
        "false_start_rate": float(ml_metrics["false_start_rate"] - det_metrics["false_start_rate"]),
        "stop_events_per_window": float(
            ml_metrics["stop_events_per_window"] - det_metrics["stop_events_per_window"]
        ),
    }

    checks: List[Dict[str, Any]] = []
    checks.append(
        _check(
            "max_failed_window_delta",
            int(delta["windows_failed"]) <= int(args.max_failed_window_delta),
            int(delta["windows_failed"]),
            int(args.max_failed_window_delta),
            "<=",
        )
    )
    checks.append(
        _check(
            "min_avg_pnl_delta",
            float(delta["avg_pnl_pct"]) >= float(args.min_avg_pnl_delta),
            float(delta["avg_pnl_pct"]),
            float(args.min_avg_pnl_delta),
            ">=",
        )
    )
    checks.append(
        _check(
            "min_sum_pnl_delta",
            float(delta["sum_pnl_quote"]) >= float(args.min_sum_pnl_delta),
            float(delta["sum_pnl_quote"]),
            float(args.min_sum_pnl_delta),
            ">=",
        )
    )

    det_churn = float(det_metrics["churn_events_per_window"])
    max_churn = (
        det_churn * (1.0 + float(args.max_churn_degradation_pct) / 100.0)
        if det_churn > 0.0
        else 0.0
    )
    checks.append(
        _check(
            "max_churn_degradation_pct",
            float(ml_metrics["churn_events_per_window"]) <= float(max_churn),
            float(ml_metrics["churn_events_per_window"]),
            float(max_churn),
            "<=",
        )
    )

    det_false = float(det_metrics["false_start_rate"])
    max_false = (
        det_false * (1.0 + float(args.max_false_start_degradation_pct) / 100.0)
        if det_false > 0.0
        else 0.0
    )
    checks.append(
        _check(
            "max_false_start_degradation_pct",
            float(ml_metrics["false_start_rate"]) <= float(max_false),
            float(ml_metrics["false_start_rate"]),
            float(max_false),
            "<=",
        )
    )

    det_stop = float(det_metrics["stop_events_per_window"])
    if det_stop <= 0.0:
        stop_mult = 1.0 if float(ml_metrics["stop_events_per_window"]) <= 0.0 else float("inf")
    else:
        stop_mult = float(ml_metrics["stop_events_per_window"] / det_stop)
    checks.append(
        _check(
            "max_stop_events_multiplier",
            float(stop_mult) <= float(args.max_stop_events_multiplier),
            float(stop_mult),
            float(args.max_stop_events_multiplier),
            "<=",
        )
    )

    if bool(args.require_ml_eval_pass):
        eval_pass = bool((ml_eval or {}).get("gates", {}).get("passed", False))
        checks.append(
            _check(
                "require_ml_eval_pass",
                bool(eval_pass),
                bool(eval_pass),
                True,
                "==",
            )
        )
    else:
        checks.append(
            _check(
                "require_ml_eval_pass",
                True,
                None if ml_eval is None else bool(ml_eval.get("gates", {}).get("passed", False)),
                None,
                "==",
                skipped=True,
            )
        )

    gates_passed = bool(all(bool(c.get("passed")) for c in checks))
    summary_payload = {
        "created_utc": utc_now_iso(),
        "run_type": "ml_overlay_compare",
        "run_id": run_id,
        "label": str(args.label),
        "deterministic_run_id": det_run_id,
        "ml_overlay_run_id": ml_run_id,
        "deterministic_metrics": det_metrics,
        "ml_overlay_metrics": ml_metrics,
        "delta_ml_minus_det": delta,
        "ml_eval_ref": {
            "run_id": str(args.ml_eval_run_id).strip(),
            "summary_path": str(args.ml_eval_summary).strip(),
            "loaded": bool(ml_eval is not None),
            "gates_passed": bool((ml_eval or {}).get("gates", {}).get("passed", False)),
        },
        "gates": {
            "passed": bool(gates_passed),
            "checks": checks,
        },
    }

    summary_path = out_dir / "summary.json"
    write_json_atomic(summary_path, summary_payload)
    latest_payload = {
        "run_type": "ml_overlay_compare",
        "run_id": run_id,
        "out_dir": rel_payload_path(user_data, out_dir),
        "summary_path": rel_payload_path(user_data, summary_path),
        "deterministic_run_id": det_run_id,
        "ml_overlay_run_id": ml_run_id,
        "gates_passed": bool(gates_passed),
    }
    ref = publish_latest_ref(user_data, "ml_overlay_compare", latest_payload)

    print(f"[ml-overlay-compare] wrote {summary_path}")
    print(f"[ml-overlay-compare] latest_ref wrote {ref}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
