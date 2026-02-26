from __future__ import annotations

from typing import Dict, Optional, Tuple

import numpy as np


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

