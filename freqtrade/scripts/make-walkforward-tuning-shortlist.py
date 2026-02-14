#!/usr/bin/env python3
"""
Build a pragmatic tuning shortlist from two walkforward runs (A baseline vs B candidate).
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from latest_refs import publish_latest_ref, rel_payload_path


def _read_json(path: Path) -> Dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected object JSON: {path}")
    return payload


def _parse_count_map(value: object) -> Dict[str, int]:
    raw = value
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return {}
        try:
            raw = json.loads(text)
        except Exception:
            return {}
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, int] = {}
    for k, v in raw.items():
        key = str(k).strip()
        if not key:
            continue
        try:
            n = int(v)
        except Exception:
            continue
        if n <= 0:
            continue
        out[key] = n
    return out


def _agg_counts(summary: Dict, field: str) -> Dict[str, int]:
    out: Dict[str, int] = {}
    windows = summary.get("windows", [])
    if not isinstance(windows, list):
        return out
    for row in windows:
        if not isinstance(row, dict):
            continue
        if str(row.get("status", "")).lower() != "ok":
            continue
        counts = _parse_count_map(row.get(field))
        for k, n in counts.items():
            out[k] = int(out.get(k, 0)) + int(n)
    return out


def _top_items(counts: Dict[str, int], n: int) -> List[Tuple[str, int]]:
    items = sorted(counts.items(), key=lambda kv: (-int(kv[1]), str(kv[0])))
    return items[: max(0, int(n))]


def _pct(part: int, whole: int) -> float:
    if int(whole) <= 0:
        return 0.0
    return 100.0 * float(part) / float(whole)


def _reason_suggestion(reason: str) -> List[str]:
    r = str(reason)
    if r == "gate_fail:mode_active_ok":
        return [
            "Test faster router switching: `regime_router_switch_persist_bars` 4 -> 3.",
            "Test lower switch margin: `regime_router_switch_margin` 1.0 -> 0.5.",
            "A/B keep `router_eligible=true` in both modes while tuning entry gates.",
        ]
    if r == "gate_fail:bbwp_gate_ok":
        return [
            "Raise BBWP caps in overrides: `bbwp_s_max`, `bbwp_m_max`, `bbwp_l_max` by +3 then +5 points.",
            "Re-test with unchanged stop logic first to isolate entry-gate impact.",
        ]
    if r == "gate_fail:fvg_gate_ok":
        return [
            "Relax FVG veto aggressiveness in `GridBrainV1` (fvg gate constants) by one notch.",
            "Measure STOP churn impact before and after to ensure no adverse breakouts.",
        ]
    if r == "gate_fail:adx_ok":
        return [
            "Raise mode ADX entry cap by +2 (intraday and swing) and re-run.",
            "Keep ADX exit unchanged for first pass to isolate entry sensitivity.",
        ]
    if r == "gate_fail:ema_dist_ok":
        return [
            "Loosen EMA distance cap by ~10-15% (`ema_dist_max_frac`) per mode.",
            "Pair with unchanged BBWP caps in one pass, then combine in second pass.",
        ]
    if r == "gate_fail:atr_ok":
        return [
            "Increase ATR% cap slightly (+0.002 intraday, +0.003 swing) and compare.",
            "Watch drawdown tail and stop frequency for risk regression.",
        ]
    if r == "gate_fail:os_dev_build_ok":
        return [
            "Reduce `os_dev_persist_bars` one step (24 -> 18 intraday, 12 -> 9 swing).",
            "Keep `os_dev_rvol_max` fixed in pass-1; tune only if needed in pass-2.",
        ]
    if r == "gate_fail:vol_ok":
        return [
            "Raise `vol_spike_mult` +0.10 and +0.20 ladders by mode.",
            "Validate against slippage/spread guardrails before promotion.",
        ]
    if r == "event:PLAN_STOP":
        return [
            "Decompose STOP events by underlying stop flags in the same windows.",
            "Tune the dominant stop rule only after entry-gate changes stabilize.",
        ]
    if r == "bbwp_expansion_stop":
        return [
            "Add 1-step hysteresis to BBWP expansion stop trigger.",
            "Test +2/+4 BBWP stop margin ladders to reduce premature exits.",
        ]
    if r in ("adx_hysteresis_stop", "adx_di_down_risk_stop"):
        return [
            "Raise ADX exit threshold by +2 and require one extra confirming bar.",
            "Re-check win-rate vs max loss tradeoff after change.",
        ]
    return ["Run a one-variable-at-a-time pass to measure this reason’s isolated effect."]


def _make_shortlist(
    a_blockers: Dict[str, int],
    b_blockers: Dict[str, int],
    b_stops: Dict[str, int],
    max_items: int,
) -> List[Dict]:
    candidates: List[Tuple[float, str, int, int]] = []
    for reason, b_count in b_blockers.items():
        if not str(reason).startswith("gate_fail:"):
            continue
        a_count = int(a_blockers.get(reason, 0))
        delta = int(b_count) - int(a_count)
        score = float(b_count) + max(0, delta)
        candidates.append((score, reason, int(b_count), int(a_count)))
    # Add dominant stop reasons too.
    for reason, b_count in b_stops.items():
        if reason == "event:PLAN_STOP":
            continue
        score = float(b_count) * 0.8
        candidates.append((score, reason, int(b_count), 0))

    candidates.sort(key=lambda x: (-x[0], x[1]))
    out: List[Dict] = []
    for idx, (_, reason, b_count, a_count) in enumerate(candidates[: max_items], start=1):
        out.append(
            {
                "rank": int(idx),
                "reason": str(reason),
                "B_count": int(b_count),
                "A_count": int(a_count),
                "delta_B_minus_A": int(b_count - a_count),
                "suggested_experiments": _reason_suggestion(str(reason)),
            }
        )
    return out


def _write_markdown(path: Path, payload: Dict) -> None:
    lines: List[str] = []
    lines.append("# Walkforward Tuning Shortlist")
    lines.append("")
    lines.append(f"- Generated: `{payload.get('generated_utc')}`")
    lines.append(f"- Run A: `{payload.get('run_a')}`")
    lines.append(f"- Run B: `{payload.get('run_b')}`")
    lines.append(f"- Delta B-A (`sum_pnl_quote`): `{payload.get('delta_sum_pnl_quote')}`")
    lines.append("")
    lines.append("## Top Blockers (B)")
    lines.append("")
    for item in payload.get("top_start_blockers_B", []):
        lines.append(
            f"- `{item['reason']}`: `{item['count']}` ({item['share_pct']:.2f}%)"
        )
    lines.append("")
    lines.append("## Top Stops (B)")
    lines.append("")
    for item in payload.get("top_stop_reasons_B", []):
        lines.append(
            f"- `{item['reason']}`: `{item['count']}` ({item['share_pct']:.2f}%)"
        )
    lines.append("")
    lines.append("## Shortlist")
    lines.append("")
    for item in payload.get("shortlist", []):
        lines.append(
            f"- **#{item['rank']} {item['reason']}** (B={item['B_count']}, "
            f"A={item['A_count']}, Δ={item['delta_B_minus_A']})"
        )
        for exp in item.get("suggested_experiments", []):
            lines.append(f"  - {exp}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user-data", default="user_data")
    ap.add_argument("--run-a", required=True)
    ap.add_argument("--run-b", required=True)
    ap.add_argument("--top-n", type=int, default=5, help="How many shortlist items to emit.")
    ap.add_argument("--out-prefix", default="wf_tuning_shortlist", help="Output file prefix.")
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

    sum_a = _read_json(user_data / "walkforward" / run_a / "summary.json")
    sum_b = _read_json(user_data / "walkforward" / run_b / "summary.json")
    agg_a = sum_a.get("aggregate", {}) or {}
    agg_b = sum_b.get("aggregate", {}) or {}

    a_blockers = _agg_counts(sum_a, "start_blocker_counts")
    b_blockers = _agg_counts(sum_b, "start_blocker_counts")
    b_stops = _agg_counts(sum_b, "stop_reason_counts_combined")
    b_cf_combo = _agg_counts(sum_b, "start_counterfactual_combo_counts")

    top_b_blockers = _top_items(b_blockers, 8)
    top_b_stops = _top_items(b_stops, 8)
    top_b_cf_combo = _top_items(b_cf_combo, 8)
    total_b_blockers = int(sum(b_blockers.values()))
    total_b_stops = int(sum(b_stops.values()))

    shortlist = _make_shortlist(a_blockers, b_blockers, b_stops, int(args.top_n))
    ts = datetime.now(timezone.utc)
    stamp = ts.strftime("%Y%m%dT%H%M%SZ")
    prefix = str(args.out_prefix).strip() or "wf_tuning_shortlist"
    out_json = user_data / "walkforward" / f"{prefix}_{stamp}.json"
    out_md = user_data / "walkforward" / f"{prefix}_{stamp}.md"

    payload = {
        "generated_utc": ts.isoformat(),
        "run_a": run_a,
        "run_b": run_b,
        "windows_ok_A": int(agg_a.get("windows_ok", 0) or 0),
        "windows_ok_B": int(agg_b.get("windows_ok", 0) or 0),
        "sum_pnl_quote_A": float(agg_a.get("sum_pnl_quote", 0.0) or 0.0),
        "sum_pnl_quote_B": float(agg_b.get("sum_pnl_quote", 0.0) or 0.0),
        "delta_sum_pnl_quote": float(agg_b.get("sum_pnl_quote", 0.0) or 0.0)
        - float(agg_a.get("sum_pnl_quote", 0.0) or 0.0),
        "top_start_blockers_B": [
            {"reason": k, "count": int(v), "share_pct": _pct(int(v), total_b_blockers)}
            for k, v in top_b_blockers
        ],
        "top_start_counterfactual_combos_B": [
            {"reason": k, "count": int(v)} for k, v in top_b_cf_combo
        ],
        "top_stop_reasons_B": [
            {"reason": k, "count": int(v), "share_pct": _pct(int(v), total_b_stops)}
            for k, v in top_b_stops
        ],
        "shortlist": shortlist,
    }

    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _write_markdown(out_md, payload)

    ref_payload = {
        "run_type": "tuning_shortlist",
        "run_a": run_a,
        "run_b": run_b,
        "json_path": rel_payload_path(user_data, out_json),
        "markdown_path": rel_payload_path(user_data, out_md),
        "delta_sum_pnl_quote": float(payload["delta_sum_pnl_quote"]),
    }
    ref = publish_latest_ref(user_data, "tuning_shortlist", ref_payload)

    print(f"[shortlist] wrote {out_json}")
    print(f"[shortlist] wrote {out_md}")
    print(f"[shortlist] latest_ref wrote {ref}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
