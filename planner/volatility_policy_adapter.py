from __future__ import annotations

from typing import Dict, Optional, Tuple

import numpy as np


VOL_BUCKETS = ("calm", "normal", "elevated", "unstable")


def _clip(value: float, lo: float, hi: float) -> float:
    return float(min(max(float(value), float(lo)), float(hi)))


def _safe_float(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    try:
        val = float(value)
    except Exception:
        return None
    if not np.isfinite(val):
        return None
    return float(val)


def _atr_bucket(atr_pct_15m: Optional[float], atr_pct_1h: Optional[float]) -> str:
    a15 = _safe_float(atr_pct_15m)
    a1h = _safe_float(atr_pct_1h)
    if a15 is None and a1h is None:
        return "normal"
    a15 = float(max(a15 or 0.0, 0.0))
    a1h = float(max(a1h or 0.0, 0.0))
    if a15 <= 0.006 and a1h <= 0.010:
        return "calm"
    if a15 <= 0.012 and a1h <= 0.020:
        return "normal"
    if a15 <= 0.020 and a1h <= 0.035:
        return "elevated"
    return "unstable"


def _bbwp_bucket(
    bbwp_s: Optional[float],
    bbwp_m: Optional[float],
    bbwp_l: Optional[float],
) -> str:
    s = _safe_float(bbwp_s)
    m = _safe_float(bbwp_m)
    l = _safe_float(bbwp_l)
    values = [float(max(x, 0.0)) for x in (s, m, l) if x is not None]
    if not values:
        return "normal"
    hi = float(max(values))
    if hi <= 35.0:
        return "calm"
    if hi <= 70.0:
        return "normal"
    if hi <= 90.0:
        return "elevated"
    return "unstable"


def compute_volatility_policy_view(
    *,
    active_mode: str,
    adapter_enabled: bool,
    adapter_strength: float,
    atr_pct_15m: Optional[float],
    atr_pct_1h: Optional[float],
    atr_mode_pct: Optional[float],
    atr_mode_max: float,
    bbwp_s: Optional[float],
    bbwp_m: Optional[float],
    bbwp_l: Optional[float],
    squeeze_on_1h: Optional[bool],
    hvp_state: Optional[str],
    base_n_min: int,
    base_n_max: int,
    base_box_width_min_pct: float,
    base_box_width_max_pct: float,
    base_min_step_buffer_bps: float,
    base_cooldown_minutes: float,
    base_min_runtime_minutes: float,
) -> Dict[str, object]:
    strength = _clip(adapter_strength, 0.0, 2.0)
    atr_bucket = _atr_bucket(atr_pct_15m, atr_pct_1h)
    bbwp_bucket = _bbwp_bucket(bbwp_s, bbwp_m, bbwp_l)
    hvp_norm = str(hvp_state or "").strip().lower()

    severity_rank = {name: idx for idx, name in enumerate(VOL_BUCKETS)}
    bucket_idx = max(severity_rank.get(atr_bucket, 1), severity_rank.get(bbwp_bucket, 1))
    if hvp_norm in {"expanding", "high", "rising"}:
        bucket_idx = max(bucket_idx, severity_rank["elevated"])
    if squeeze_on_1h is True and bucket_idx > 0:
        bucket_idx -= 1
    if squeeze_on_1h is False and bbwp_bucket in {"elevated", "unstable"} and bucket_idx < 3:
        bucket_idx += 1
    bucket = VOL_BUCKETS[int(np.clip(bucket_idx, 0, len(VOL_BUCKETS) - 1))]

    profiles = {
        "calm": {
            "n_shift": 1,
            "width_min_mult": 0.95,
            "width_max_mult": 0.95,
            "step_buffer_bps_add": 0.0,
            "cooldown_mult": 0.90,
            "min_runtime_mult": 0.95,
            "start_gate_ratio_delta": 0.00,
            "build_strictness": {
                "enforce_squeeze_gate": False,
                "vol_bucket_block_start": False,
            },
        },
        "normal": {
            "n_shift": 0,
            "width_min_mult": 1.00,
            "width_max_mult": 1.00,
            "step_buffer_bps_add": 0.0,
            "cooldown_mult": 1.00,
            "min_runtime_mult": 1.00,
            "start_gate_ratio_delta": 0.00,
            "build_strictness": {
                "enforce_squeeze_gate": False,
                "vol_bucket_block_start": False,
            },
        },
        "elevated": {
            "n_shift": -1,
            "width_min_mult": 1.05,
            "width_max_mult": 1.10,
            "step_buffer_bps_add": 6.0,
            "cooldown_mult": 1.20,
            "min_runtime_mult": 1.10,
            "start_gate_ratio_delta": 0.02,
            "build_strictness": {
                "enforce_squeeze_gate": True,
                "vol_bucket_block_start": False,
            },
        },
        "unstable": {
            "n_shift": -2,
            "width_min_mult": 1.10,
            "width_max_mult": 1.20,
            "step_buffer_bps_add": 12.0,
            "cooldown_mult": 1.50,
            "min_runtime_mult": 1.25,
            "start_gate_ratio_delta": 0.05,
            "build_strictness": {
                "enforce_squeeze_gate": True,
                "vol_bucket_block_start": True,
            },
        },
    }
    profile = profiles[bucket]
    scale = float(strength if adapter_enabled else 0.0)

    n_low_base = max(int(base_n_min), 1)
    n_high_base = max(int(base_n_max), n_low_base)
    n_shift = int(np.round(float(profile["n_shift"]) * scale))
    if n_shift > 0:
        n_low = n_low_base + n_shift
    else:
        n_low = n_low_base
    n_high = max(n_low, n_high_base + n_shift)

    atr_ratio = None
    atr_adjust = 0
    atr_mode_pct_safe = _safe_float(atr_mode_pct)
    if atr_mode_pct_safe is not None and float(atr_mode_max) > 0.0:
        atr_ratio = float(max(atr_mode_pct_safe, 0.0) / float(atr_mode_max))
        atr_adjust = int(np.floor(max(atr_ratio - 1.0, 0.0) * scale * 2.0))
        if atr_adjust > 0:
            n_high = max(n_low, n_high - atr_adjust)

    width_min_mult = 1.0 + (float(profile["width_min_mult"]) - 1.0) * scale
    width_max_mult = 1.0 + (float(profile["width_max_mult"]) - 1.0) * scale
    box_width_min_pct = _clip(float(base_box_width_min_pct) * width_min_mult, 0.01, 0.20)
    box_width_max_pct = _clip(float(base_box_width_max_pct) * width_max_mult, 0.01, 0.30)
    if box_width_max_pct < box_width_min_pct:
        box_width_max_pct = box_width_min_pct

    min_step_buffer_bps = _clip(
        float(base_min_step_buffer_bps) + (float(profile["step_buffer_bps_add"]) * scale),
        0.0,
        100.0,
    )
    cooldown_minutes = _clip(
        float(base_cooldown_minutes)
        * (1.0 + (float(profile["cooldown_mult"]) - 1.0) * scale),
        1.0,
        24.0 * 60.0,
    )
    min_runtime_minutes = _clip(
        float(base_min_runtime_minutes)
        * (1.0 + (float(profile["min_runtime_mult"]) - 1.0) * scale),
        1.0,
        48.0 * 60.0,
    )
    start_gate_ratio_delta = _clip(float(profile["start_gate_ratio_delta"]) * scale, 0.0, 0.25)

    build_strictness_base = dict(profile["build_strictness"])
    build_strictness = {
        "enforce_squeeze_gate": bool(build_strictness_base.get("enforce_squeeze_gate", False) and adapter_enabled),
        "vol_bucket_block_start": bool(build_strictness_base.get("vol_bucket_block_start", False) and adapter_enabled),
    }

    base = {
        "n_min": int(n_low_base),
        "n_max": int(n_high_base),
        "box_width_min_pct": float(base_box_width_min_pct),
        "box_width_max_pct": float(base_box_width_max_pct),
        "min_step_buffer_bps": float(base_min_step_buffer_bps),
        "cooldown_minutes": float(base_cooldown_minutes),
        "min_runtime_minutes": float(base_min_runtime_minutes),
    }
    adapted = {
        "n_min": int(n_low),
        "n_max": int(n_high),
        "box_width_min_pct": float(box_width_min_pct),
        "box_width_max_pct": float(box_width_max_pct),
        "min_step_buffer_bps": float(min_step_buffer_bps),
        "cooldown_minutes": float(cooldown_minutes),
        "min_runtime_minutes": float(min_runtime_minutes),
        "start_gate_ratio_delta": float(start_gate_ratio_delta),
        "build_strictness": build_strictness,
    }
    return {
        "mode": str(active_mode),
        "adapter_enabled": bool(adapter_enabled),
        "adapter_strength": float(strength),
        "vol_bucket": str(bucket),
        "bucket_components": {
            "atr_bucket": str(atr_bucket),
            "bbwp_bucket": str(bbwp_bucket),
            "hvp_state": str(hvp_norm or "none"),
            "squeeze_on_1h": bool(squeeze_on_1h) if squeeze_on_1h is not None else None,
        },
        "inputs": {
            "atr_pct_15m": atr_pct_15m,
            "atr_pct_1h": atr_pct_1h,
            "atr_mode_pct": atr_mode_pct_safe,
            "atr_mode_max": float(atr_mode_max),
            "bbwp_s": bbwp_s,
            "bbwp_m": bbwp_m,
            "bbwp_l": bbwp_l,
        },
        "base": base,
        "adapted": adapted,
        "n_level_diag": {
            "volatility_ratio": atr_ratio,
            "adjustment": int(atr_adjust),
            "bucket_n_shift": int(n_shift),
        },
    }


def compute_n_level_bounds(
    *,
    n_min: int,
    n_max: int,
    active_mode: str,
    adapter_enabled: bool,
    atr_mode_pct: Optional[float],
    atr_mode_max: float,
    adapter_strength: float,
) -> Tuple[int, int, Dict[str, object]]:
    n_low = max(int(n_min), 1)
    n_high = max(int(n_max), n_low)
    diag = {
        "mode": str(active_mode),
        "adapter_enabled": bool(adapter_enabled),
        "volatility_ratio": None,
        "adjustment": 0,
    }
    if not adapter_enabled:
        return n_low, n_high, diag
    if atr_mode_pct is None or atr_mode_max <= 0:
        return n_low, n_high, diag

    ratio = float(max(float(atr_mode_pct), 0.0) / float(atr_mode_max))
    adjustment = int(np.floor(max(ratio - 1.0, 0.0) * float(adapter_strength) * 2.0))
    if adjustment > 0:
        n_high = max(n_low, n_high - adjustment)
    diag["volatility_ratio"] = float(ratio)
    diag["adjustment"] = int(adjustment)
    return n_low, n_high, diag
