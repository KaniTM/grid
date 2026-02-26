from __future__ import annotations

import math
from typing import Dict, List, Tuple

import numpy as np


def evaluate_start_stability(
    gate_checks: List[Tuple[str, bool]],
    min_score: float,
    k_fraction: float,
) -> Dict[str, float]:
    total = max(int(len(gate_checks)), 1)
    passed = int(sum(1 for _, ok in gate_checks if ok))
    score = float(passed / total)
    frac = float(np.clip(k_fraction, 0.0, 1.0))
    k_required = int(math.ceil(total * frac))
    min_required = float(np.clip(min_score, 0.0, 1.0))
    ok = bool(score >= min_required and passed >= k_required)
    return {
        "score": score,
        "passed": passed,
        "total": total,
        "k_required": k_required,
        "min_score": min_required,
        "ok": ok,
    }

