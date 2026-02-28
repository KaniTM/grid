from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, Optional, Sequence


def load_capacity_hint_state(
    pair: str,
    *,
    capacity_hint_path: str,
    capacity_hint_hard_block: bool,
) -> Dict[str, object]:
    out = {
        "available": False,
        "allow_start": True,
        "reason": None,
        "preferred_rung_cap": None,
        "max_concurrent_rebuilds": None,
        "advisory_only": bool(not capacity_hint_hard_block),
    }
    path = str(capacity_hint_path or "").strip()
    if not path:
        return out
    p = Path(path).expanduser()
    if not p.is_file():
        return out

    try:
        with p.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        raw: Optional[dict]
        raw = payload.get(pair) if isinstance(payload, dict) and pair in payload else payload
        if not isinstance(raw, dict):
            return out
        out["available"] = True
        out["allow_start"] = bool(raw.get("allow_start", True))
        out["reason"] = raw.get("reason")
        out["preferred_rung_cap"] = raw.get("preferred_rung_cap")
        out["max_concurrent_rebuilds"] = raw.get("max_concurrent_rebuilds")
        out["advisory_only"] = bool(raw.get("advisory_only", not capacity_hint_hard_block))
        return out
    except Exception:
        return out


def _as_float(value: object, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _as_int(value: object, default: Optional[int] = None) -> Optional[int]:
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


def compute_dynamic_capacity_state(
    *,
    max_orders_per_side: int,
    n_levels: int,
    quote_total: float,
    grid_budget_pct: float,
    preferred_rung_cap: Optional[int],
    runtime_spread_pct: Optional[float],
    runtime_depth_thinning_score: Optional[float],
    top_book_notional: Optional[float],
    runtime_capacity_ok: bool,
    runtime_reasons: Sequence[str],
    spread_wide_threshold: float,
    depth_thin_threshold: float,
    spread_cap_multiplier: float,
    depth_cap_multiplier: float,
    min_rung_cap: int,
    top_book_safety_fraction: float,
    delay_replenish_on_thin: bool,
) -> Dict[str, object]:
    base_cap = max(min(int(max_orders_per_side), int(n_levels) + 1), 0)
    min_cap = max(int(min_rung_cap), 1)
    if preferred_rung_cap is not None and int(preferred_rung_cap) > 0:
        base_cap = min(base_cap, int(preferred_rung_cap))
    effective_min_cap = int(max(min(min_cap, max(base_cap, 0)), 0))
    reasons = [str(x) for x in runtime_reasons if str(x).strip()]
    spread_pct = _as_float(runtime_spread_pct, default=None)
    depth_thinning = _as_float(runtime_depth_thinning_score, default=None)
    top_notional = _as_float(top_book_notional, default=None)
    applied_cap = int(max(base_cap, 0))

    # Hard-zero configuration must stay blocked, regardless of runtime multipliers.
    if applied_cap <= 0:
        if "BLOCK_CAPACITY_THIN" not in reasons:
            reasons.append("BLOCK_CAPACITY_THIN")
        return {
            "capacity_ok": False,
            "max_safe_active_rungs": 0,
            "max_safe_rung_notional": None,
            "reasons": reasons,
            "delay_replenishment": bool(delay_replenish_on_thin),
            "preferred_rung_cap": _as_int(preferred_rung_cap, default=None),
            "base_rung_cap": int(base_cap),
            "applied_rung_cap": 0,
            "rung_cap_applied": False,
            "spread_pct": spread_pct,
            "depth_thinning_score": depth_thinning,
            "top_book_notional": top_notional,
        }

    if spread_pct is not None and spread_pct > float(max(spread_wide_threshold, 0.0)):
        reduced = int(math.floor(float(applied_cap) * float(max(spread_cap_multiplier, 0.0))))
        reduced = min(applied_cap, reduced)
        applied_cap = max(effective_min_cap, reduced)
        if "SPREAD_WIDE" not in reasons:
            reasons.append("SPREAD_WIDE")

    if depth_thinning is not None and depth_thinning > float(max(depth_thin_threshold, 0.0)):
        reduced = int(math.floor(float(applied_cap) * float(max(depth_cap_multiplier, 0.0))))
        reduced = min(applied_cap, reduced)
        applied_cap = max(effective_min_cap, reduced)
        if "DEPTH_THIN_AT_TOP" not in reasons:
            reasons.append("DEPTH_THIN_AT_TOP")

    max_safe_rung_notional = None
    if top_notional is not None and top_notional > 0:
        max_safe_rung_notional = float(top_notional * max(float(top_book_safety_fraction), 0.0))
        quote_budget = max(float(quote_total) * float(grid_budget_pct), 0.0)
        if max_safe_rung_notional > 0 and quote_budget > 0:
            notional_cap = int(math.floor(quote_budget / max_safe_rung_notional))
            notional_cap = max(effective_min_cap, notional_cap)
            if notional_cap < applied_cap:
                applied_cap = int(notional_cap)
                if "TOP_BOOK_NOTIONAL_LIMIT" not in reasons:
                    reasons.append("TOP_BOOK_NOTIONAL_LIMIT")

    if not bool(runtime_capacity_ok):
        if "BLOCK_CAPACITY_THIN" not in reasons:
            reasons.append("BLOCK_CAPACITY_THIN")

    capacity_ok = bool(runtime_capacity_ok) and bool(applied_cap >= effective_min_cap)
    delay_replenishment = bool(delay_replenish_on_thin and ("DEPTH_THIN_AT_TOP" in reasons or not capacity_ok))

    return {
        "capacity_ok": bool(capacity_ok),
        "max_safe_active_rungs": int(applied_cap),
        "max_safe_rung_notional": max_safe_rung_notional,
        "reasons": reasons,
        "delay_replenishment": bool(delay_replenishment),
        "preferred_rung_cap": _as_int(preferred_rung_cap, default=None),
        "base_rung_cap": int(base_cap),
        "applied_rung_cap": int(applied_cap),
        "rung_cap_applied": bool(applied_cap < base_cap),
        "spread_pct": spread_pct,
        "depth_thinning_score": depth_thinning,
        "top_book_notional": top_notional,
    }
