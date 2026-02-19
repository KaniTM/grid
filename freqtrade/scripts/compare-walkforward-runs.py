#!/usr/bin/env python3
"""
Compare two walkforward summaries and emit an AB compare JSON artifact.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple

from latest_refs import publish_latest_ref, rel_payload_path
from run_state import RunStateTracker
from long_run_monitor import LongRunMonitor, MonitorConfig


def _read_json(path: Path) -> Dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected object JSON: {path}")
    return payload


def _infer_days(summary: Dict) -> Tuple[str, str]:
    timerange = str((summary.get("args", {}) or {}).get("timerange") or "")
    if "-" in timerange:
        a, b = timerange.split("-", 1)
        return a.strip(), b.strip()
    return "", ""


def _section(run_id: str, summary: Dict) -> Dict:
    agg = summary.get("aggregate", {}) or {}
    start_day, end_day = _infer_days(summary)
    return {
        "run_id": run_id,
        "created_utc": str(summary.get("created_utc") or ""),
        "start_day": start_day,
        "end_day": end_day,
        "windows_total": int(agg.get("windows_total", 0) or 0),
        "windows_ok": int(agg.get("windows_ok", 0) or 0),
        "windows_failed": int(agg.get("windows_failed", 0) or 0),
        "sum_pnl_quote": float(agg.get("sum_pnl_quote", 0.0) or 0.0),
        "avg_pnl_pct": float(agg.get("avg_pnl_pct", 0.0) or 0.0),
        "median_pnl_pct": float(agg.get("median_pnl_pct", 0.0) or 0.0),
        "win_rate": float(agg.get("win_rate", 0.0) or 0.0),
        "profit_factor": float(agg.get("profit_factor", 0.0) or 0.0),
        "max_loss_pct": float(agg.get("max_loss_pct", 0.0) or 0.0),
        "max_gain_pct": float(agg.get("max_gain_pct", 0.0) or 0.0),
        "top_start_blocker": str(agg.get("top_start_blocker") or ""),
        "top_start_counterfactual_combo": str(agg.get("top_start_counterfactual_combo") or ""),
        "top_stop_reason": str(agg.get("top_stop_reason") or ""),
    }


def _default_out_path(user_data: Path, sec_a: Dict, sec_b: Dict, label: str) -> Path:
    start = str(sec_a.get("start_day") or "") or str(sec_b.get("start_day") or "")
    end = str(sec_a.get("end_day") or "") or str(sec_b.get("end_day") or "")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = f"_{label.strip()}" if str(label).strip() else ""
    name = f"wf_AB_compare_{start}_{end}{suffix}_{stamp}.json"
    return user_data / "walkforward" / name


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user-data", default="user_data")
    ap.add_argument("--run-a", required=True, help="Walkforward run-id for A.")
    ap.add_argument("--run-b", required=True, help="Walkforward run-id for B.")
    ap.add_argument("--out", default="", help="Optional output json path.")
    ap.add_argument("--label", default="", help="Optional label added to default filename.")
    ap.add_argument(
        "--enable-liveness",
        action="store_true",
        help="Emit liveness/state-output lines and state event markers.",
    )
    ap.add_argument(
        "--stall-threshold-sec",
        type=int,
        default=0,
        help="Raise when no new liveness progress occurs for this many seconds (if liveness enabled).",
    )
    return ap


def main() -> int:
    args = build_parser().parse_args()
    root_dir = Path(__file__).resolve().parents[1]
    user_data = Path(args.user_data)
    if not user_data.is_absolute():
        user_data = (root_dir / user_data).resolve()
    if not user_data.is_dir():
        raise FileNotFoundError(f"user_data directory not found: {user_data}")

    run_a = str(args.run_a).strip()
    run_b = str(args.run_b).strip()
    if not run_a or not run_b:
        raise ValueError("--run-a and --run-b are required")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    state_dir = user_data / "run_state" / "ab_compare" / stamp
    run_state = (
        RunStateTracker(state_dir / "state.json", state_dir / "events.jsonl") if args.enable_liveness else None
    )
    monitor = LongRunMonitor(
        MonitorConfig(
            run_id=f"ab_compare_{stamp}",
            run_type="ab_compare",
            total_steps=2,
            enabled=args.enable_liveness,
            state_dir=state_dir if args.enable_liveness else None,
            stall_threshold_sec=args.stall_threshold_sec,
        ),
        run_state=run_state,
    )
    monitor.start(message=f"{run_a} vs {run_b}", total_steps=2)

    a_summary_path = user_data / "walkforward" / run_a / "summary.json"
    b_summary_path = user_data / "walkforward" / run_b / "summary.json"
    if not a_summary_path.exists():
        raise FileNotFoundError(f"Missing summary for A: {a_summary_path}")
    if not b_summary_path.exists():
        raise FileNotFoundError(f"Missing summary for B: {b_summary_path}")

    a_summary = _read_json(a_summary_path)
    b_summary = _read_json(b_summary_path)
    monitor.progress(done=1, stage="LOAD_SUMMARIES", message=f"{run_a} vs {run_b}")
    sec_a = _section(run_a, a_summary)
    sec_b = _section(run_b, b_summary)

    delta_keys = (
        "windows_total",
        "windows_ok",
        "windows_failed",
        "sum_pnl_quote",
        "avg_pnl_pct",
        "median_pnl_pct",
        "win_rate",
        "profit_factor",
        "max_loss_pct",
        "max_gain_pct",
    )
    delta = {k: (float(sec_b[k]) - float(sec_a[k])) for k in delta_keys}

    payload = {
        "A": sec_a,
        "B": sec_b,
        "delta_B_minus_A": delta,
    }

    out_path = Path(str(args.out).strip()) if str(args.out).strip() else _default_out_path(
        user_data, sec_a, sec_b, str(args.label)
    )
    if not out_path.is_absolute():
        out_path = (root_dir / out_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    monitor.progress(done=2, stage="WRITE_ARTIFACT", message=str(out_path))

    latest_payload = {
        "run_type": "ab_compare",
        "A_run_id": run_a,
        "B_run_id": run_b,
        "out_path": rel_payload_path(user_data, out_path),
        "delta_B_minus_A": delta,
    }
    ref = publish_latest_ref(user_data, "ab_compare", latest_payload)

    print(f"[ab-compare] wrote {out_path}")
    print(f"[ab-compare] latest_ref wrote {ref}")
    monitor.complete("RUN_COMPLETE", message=f"out={out_path}", return_code=0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
