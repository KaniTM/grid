#!/usr/bin/env python3
"""
Backfill latest_refs from already-existing artifacts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Optional, Tuple

from latest_refs import publish_latest_ref, rel_payload_path


def _read_json(path: Path) -> Dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {}
    return payload


def _latest_walkforward_run(user_data: Path) -> Optional[Path]:
    wf = user_data / "walkforward"
    if not wf.is_dir():
        return None
    best: Tuple[float, Optional[Path]] = (0.0, None)
    for d in wf.iterdir():
        if not d.is_dir():
            continue
        summary = d / "summary.json"
        windows = d / "windows.csv"
        if not summary.exists() or not windows.exists():
            continue
        ts = float(summary.stat().st_mtime)
        if ts > best[0]:
            best = (ts, d)
    return best[1]


def _latest_regime_run(user_data: Path) -> Optional[Path]:
    ra = user_data / "regime_audit"
    if not ra.is_dir():
        return None
    best: Tuple[float, Optional[Path]] = (0.0, None)
    for d in ra.iterdir():
        if not d.is_dir():
            continue
        report = d / "report.json"
        overrides = d / "mode_threshold_overrides.json"
        if not report.exists() or not overrides.exists():
            continue
        ts = float(report.stat().st_mtime)
        if ts > best[0]:
            best = (ts, d)
    return best[1]


def _latest_data_sync_run(user_data: Path) -> Optional[Path]:
    rs = user_data / "run_state" / "data_sync"
    if not rs.is_dir():
        return None
    best: Tuple[float, Optional[Path]] = (0.0, None)
    for d in rs.iterdir():
        if not d.is_dir():
            continue
        state = d / "state.json"
        if not state.exists():
            continue
        ts = float(state.stat().st_mtime)
        if ts > best[0]:
            best = (ts, d)
    return best[1]


def _latest_file(parent: Path, pattern: str) -> Optional[Path]:
    files = sorted(parent.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user-data", default="user_data")
    return ap


def main() -> int:
    args = build_parser().parse_args()
    root_dir = Path(__file__).resolve().parents[1]
    user_data = Path(args.user_data)
    if not user_data.is_absolute():
        user_data = (root_dir / user_data).resolve()
    if not user_data.is_dir():
        raise FileNotFoundError(f"user_data directory not found: {user_data}")

    wrote = 0

    wf_run = _latest_walkforward_run(user_data)
    if wf_run is not None:
        summary = _read_json(wf_run / "summary.json")
        agg = summary.get("aggregate", {}) if isinstance(summary.get("aggregate"), dict) else {}
        run_id = str(summary.get("run_id") or wf_run.name)
        payload = {
            "run_type": "walkforward",
            "run_id": run_id,
            "out_dir": rel_payload_path(user_data, wf_run),
            "summary_path": rel_payload_path(user_data, wf_run / "summary.json"),
            "windows_path": rel_payload_path(user_data, wf_run / "windows.csv"),
            "aggregate": {
                "windows_total": int(agg.get("windows_total", 0) or 0),
                "windows_ok": int(agg.get("windows_ok", 0) or 0),
                "windows_failed": int(agg.get("windows_failed", 0) or 0),
                "sum_pnl_quote": float(agg.get("sum_pnl_quote", 0.0) or 0.0),
                "avg_pnl_pct": float(agg.get("avg_pnl_pct", 0.0) or 0.0),
                "win_rate": float(agg.get("win_rate", 0.0) or 0.0),
            },
        }
        ref = publish_latest_ref(user_data, "walkforward", payload)
        print(f"[refresh-latest] walkforward -> {ref}")
        wrote += 1

    rg_run = _latest_regime_run(user_data)
    if rg_run is not None:
        report = _read_json(rg_run / "report.json")
        run_id = str(rg_run.name)
        payload = {
            "run_type": "regime_audit",
            "run_id": run_id,
            "out_dir": rel_payload_path(user_data, rg_run),
            "report_path": rel_payload_path(user_data, rg_run / "report.json"),
            "overrides_path": rel_payload_path(user_data, rg_run / "mode_threshold_overrides.json"),
            "pair": str(((report.get("meta") or {}).get("pair") or "")),
            "timeframe": str(((report.get("meta") or {}).get("timeframe") or "")),
        }
        ref = publish_latest_ref(user_data, "regime_audit", payload)
        print(f"[refresh-latest] regime_audit -> {ref}")
        wrote += 1

    ds_run = _latest_data_sync_run(user_data)
    if ds_run is not None:
        state = _read_json(ds_run / "state.json")
        payload = {
            "run_type": "data_sync",
            "run_id": str(state.get("run_id") or ds_run.name),
            "status": str(state.get("status") or ""),
            "step_word": str(state.get("step_word") or ""),
            "return_code": int(state.get("return_code", 0) or 0),
            "tasks_total": int(state.get("tasks_total", 0) or 0),
            "tasks_completed": int(state.get("tasks_completed", 0) or 0),
            "tasks_failed": int(state.get("tasks_failed", 0) or 0),
            "run_state_dir": rel_payload_path(user_data, ds_run),
        }
        ref = publish_latest_ref(user_data, "data_sync", payload)
        print(f"[refresh-latest] data_sync -> {ref}")
        wrote += 1

    wf_dir = user_data / "walkforward"
    ab_file = _latest_file(wf_dir, "*AB_compare*.json") or _latest_file(wf_dir, "wf_AB_compare_*.json")
    if ab_file is not None:
        payload = _read_json(ab_file)
        a_run = str(((payload.get("A") or {}).get("run_id") or ""))
        b_run = str(((payload.get("B") or {}).get("run_id") or ""))
        ref = publish_latest_ref(
            user_data,
            "ab_compare",
            {
                "run_type": "ab_compare",
                "A_run_id": a_run,
                "B_run_id": b_run,
                "out_path": rel_payload_path(user_data, ab_file),
                "delta_B_minus_A": payload.get("delta_B_minus_A", {}),
            },
        )
        print(f"[refresh-latest] ab_compare -> {ref}")
        wrote += 1

    shortlist_file = _latest_file(wf_dir, "*tuning_shortlist*.json")
    if shortlist_file is not None:
        pl = _read_json(shortlist_file)
        ref = publish_latest_ref(
            user_data,
            "tuning_shortlist",
            {
                "run_type": "tuning_shortlist",
                "run_a": str(pl.get("run_a") or ""),
                "run_b": str(pl.get("run_b") or ""),
                "json_path": rel_payload_path(user_data, shortlist_file),
                "markdown_path": rel_payload_path(user_data, shortlist_file.with_suffix(".md")),
                "delta_sum_pnl_quote": float(pl.get("delta_sum_pnl_quote", 0.0) or 0.0),
            },
        )
        print(f"[refresh-latest] tuning_shortlist -> {ref}")
        wrote += 1

    print(f"[refresh-latest] wrote_refs={wrote}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
