from __future__ import annotations

from collections import deque
from typing import Dict, List, Optional

import numpy as np


def _safe_float(x: object) -> Optional[float]:
    try:
        if x is None:
            return None
        if isinstance(x, (float, int, np.floating, np.integer)):
            if np.isnan(x):
                return None
            return float(x)
        xf = float(x)
        if np.isnan(xf):
            return None
        return xf
    except Exception:
        return None


class MetaDriftGuard:
    """Per-pair drift detector using smoothed z-score + CUSUM/Page-Hinkley style accumulators."""

    def __init__(self, window: int, smoothing_alpha: float) -> None:
        self._window = max(int(window), 8)
        self._alpha = float(np.clip(smoothing_alpha, 0.01, 1.0))
        self._state_by_pair: Dict[str, Dict[str, object]] = {}

    def reset_pair(self, pair: str) -> None:
        self._state_by_pair.pop(pair, None)

    def _pair_state(self, pair: str) -> Dict[str, object]:
        state = self._state_by_pair.get(pair)
        if state is None:
            state = {
                "bars_seen": 0,
                "channels": {},
            }
            self._state_by_pair[pair] = state
        return state

    def observe(
        self,
        pair: str,
        channels: Dict[str, Optional[float]],
        *,
        min_samples: int,
        eps: float,
        z_soft: float,
        z_hard: float,
        cusum_k_sigma: float,
        cusum_soft: float,
        cusum_hard: float,
        ph_delta_sigma: float,
        ph_soft: float,
        ph_hard: float,
        soft_min_channels: int,
        hard_min_channels: int,
    ) -> Dict[str, object]:
        pair_state = self._pair_state(pair)
        pair_state["bars_seen"] = int(pair_state.get("bars_seen", 0) + 1)
        channels_state = pair_state.setdefault("channels", {})

        channel_details: Dict[str, Dict[str, object]] = {}
        ready_channels: List[str] = []
        soft_channels: List[str] = []
        hard_channels: List[str] = []

        for name, raw in channels.items():
            value = _safe_float(raw)
            state = channels_state.get(name)
            if not isinstance(state, dict):
                state = {
                    "ema": None,
                    "history": deque(maxlen=self._window),
                    "cusum_pos": 0.0,
                    "cusum_neg": 0.0,
                    "ph_pos": 0.0,
                    "ph_neg": 0.0,
                }
                channels_state[name] = state

            if value is None or not np.isfinite(value):
                channel_details[name] = {
                    "available": False,
                    "value": None,
                    "smoothed": None,
                    "baseline_mean": None,
                    "baseline_std": None,
                    "z_score": None,
                    "cusum_score": None,
                    "page_hinkley_score": None,
                    "soft": False,
                    "hard": False,
                }
                continue

            prev_ema = _safe_float(state.get("ema"))
            ema = float(value) if prev_ema is None else float((self._alpha * value) + ((1.0 - self._alpha) * prev_ema))
            history = state.get("history")
            if not isinstance(history, deque) or history.maxlen != self._window:
                history = deque(history if isinstance(history, (list, tuple, deque)) else [], maxlen=self._window)
                state["history"] = history

            baseline_ready = len(history) >= max(int(min_samples), 1)
            baseline_mean = None
            baseline_std = None
            z_score = None
            cusum_score = None
            page_hinkley_score = None
            soft_hit = False
            hard_hit = False

            if baseline_ready:
                hist_arr = np.asarray(list(history), dtype=float)
                if hist_arr.size > 0:
                    baseline_mean = float(np.mean(hist_arr))
                    baseline_std = float(max(np.std(hist_arr, ddof=1), max(float(eps), 1e-12)))
                    delta = float(ema - baseline_mean)
                    z_score = float(abs(delta) / baseline_std)

                    cusum_pos = float(max(float(state.get("cusum_pos", 0.0)) + delta - (float(cusum_k_sigma) * baseline_std), 0.0))
                    cusum_neg = float(max(float(state.get("cusum_neg", 0.0)) - delta - (float(cusum_k_sigma) * baseline_std), 0.0))
                    state["cusum_pos"] = cusum_pos
                    state["cusum_neg"] = cusum_neg
                    cusum_score = float(max(cusum_pos, cusum_neg) / baseline_std)

                    ph_pos = float(max(float(state.get("ph_pos", 0.0)) + delta - (float(ph_delta_sigma) * baseline_std), 0.0))
                    ph_neg = float(max(float(state.get("ph_neg", 0.0)) - delta - (float(ph_delta_sigma) * baseline_std), 0.0))
                    state["ph_pos"] = ph_pos
                    state["ph_neg"] = ph_neg
                    page_hinkley_score = float(max(ph_pos, ph_neg) / baseline_std)

                    soft_hit = bool(
                        z_score >= float(z_soft)
                        or cusum_score >= float(cusum_soft)
                        or page_hinkley_score >= float(ph_soft)
                    )
                    hard_hit = bool(
                        z_score >= float(z_hard)
                        or cusum_score >= float(cusum_hard)
                        or page_hinkley_score >= float(ph_hard)
                    )
                    ready_channels.append(str(name))
            else:
                state["cusum_pos"] = 0.0
                state["cusum_neg"] = 0.0
                state["ph_pos"] = 0.0
                state["ph_neg"] = 0.0

            state["ema"] = float(ema)
            history.append(float(ema))

            if soft_hit:
                soft_channels.append(str(name))
            if hard_hit:
                hard_channels.append(str(name))

            channel_details[name] = {
                "available": True,
                "value": float(value),
                "smoothed": float(ema),
                "baseline_mean": baseline_mean,
                "baseline_std": baseline_std,
                "z_score": z_score,
                "cusum_score": cusum_score,
                "page_hinkley_score": page_hinkley_score,
                "soft": bool(soft_hit),
                "hard": bool(hard_hit),
            }

        soft_unique = list(dict.fromkeys(soft_channels))
        hard_unique = list(dict.fromkeys(hard_channels))
        severity = "none"
        if len(hard_unique) >= max(int(hard_min_channels), 1):
            severity = "hard"
        elif len(soft_unique) >= max(int(soft_min_channels), 1):
            severity = "soft"
        drift_channels = hard_unique if severity == "hard" else soft_unique if severity == "soft" else []

        return {
            "bars_seen": int(pair_state.get("bars_seen", 0)),
            "min_samples": int(max(int(min_samples), 1)),
            "ready_channels": ready_channels,
            "channels": channel_details,
            "soft_channels": soft_unique,
            "hard_channels": hard_unique,
            "soft_count": int(len(soft_unique)),
            "hard_count": int(len(hard_unique)),
            "severity": str(severity),
            "drift_detected": bool(severity in {"soft", "hard"}),
            "drift_channels": drift_channels,
        }

