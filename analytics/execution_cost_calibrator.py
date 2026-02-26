from __future__ import annotations

from collections import deque
from typing import Dict, Optional

import numpy as np


class EmpiricalCostCalibrator:
    """
    Lightweight rolling empirical cost estimator.
    """

    def __init__(self, window: int) -> None:
        self._window = max(int(window), 1)
        self._samples_by_pair: Dict[str, deque] = {}
        self._bars_seen_by_pair: Dict[str, int] = {}
        self._last_update_bar_by_pair: Dict[str, int] = {}

    def _samples(self, pair: str) -> deque:
        samples = self._samples_by_pair.get(pair)
        if samples is None or samples.maxlen != self._window:
            samples = deque(maxlen=self._window)
            self._samples_by_pair[pair] = samples
        return samples

    def observe(
        self,
        pair: str,
        *,
        spread_pct: Optional[float],
        adverse_selection_pct: Optional[float],
        retry_reject_rate: Optional[float],
        missed_fill_rate: Optional[float],
        retry_penalty_pct: float,
        missed_fill_penalty_pct: float,
        recommended_floor_pct: Optional[float] = None,
        sample_source: Optional[str] = None,
        market_state_bucket: Optional[str] = None,
    ) -> Dict[str, Optional[float]]:
        bar_idx = int(self._bars_seen_by_pair.get(pair, 0) + 1)
        self._bars_seen_by_pair[pair] = bar_idx

        spread = float(max(spread_pct or 0.0, 0.0))
        adverse = float(max(adverse_selection_pct or 0.0, 0.0))
        retry_rate = float(np.clip(retry_reject_rate or 0.0, 0.0, 1.0))
        missed_rate = float(np.clip(missed_fill_rate or 0.0, 0.0, 1.0))
        retry_penalty = float(max(retry_penalty_pct, 0.0) * retry_rate)
        missed_penalty = float(max(missed_fill_penalty_pct, 0.0) * missed_rate)
        recommended = (
            float(max(recommended_floor_pct, 0.0))
            if recommended_floor_pct is not None
            else None
        )
        source = str(sample_source or "proxy").strip().lower().replace(" ", "_")
        if not source:
            source = "proxy"
        bucket = str(market_state_bucket).strip() if market_state_bucket is not None else None
        if bucket == "":
            bucket = None

        sample = {
            "spread_pct": float(spread),
            "adverse_selection_pct": float(adverse),
            "retry_reject_rate": float(retry_rate),
            "missed_fill_rate": float(missed_rate),
            "retry_penalty_pct": float(retry_penalty),
            "missed_fill_penalty_pct": float(missed_penalty),
            "total_pct": float(spread + adverse + retry_penalty + missed_penalty),
            "recommended_floor_pct": recommended,
            "sample_source": str(source),
            "market_state_bucket": bucket,
            "bar_idx": int(bar_idx),
        }
        self._samples(pair).append(sample)
        self._last_update_bar_by_pair[pair] = bar_idx
        return sample

    def snapshot(
        self,
        pair: str,
        *,
        percentile: float,
        min_samples: int,
        stale_bars: int,
    ) -> Dict[str, object]:
        samples = list(self._samples(pair))
        sample_count = int(len(samples))
        p = float(np.clip(percentile, 0.0, 100.0))
        bars_seen = int(self._bars_seen_by_pair.get(pair, 0))
        last_update = self._last_update_bar_by_pair.get(pair)
        bars_since_update = (
            int(max(bars_seen - int(last_update), 0))
            if last_update is not None
            else None
        )

        out: Dict[str, object] = {
            "sample_count": int(sample_count),
            "bars_seen": int(bars_seen),
            "bars_since_update": int(bars_since_update) if bars_since_update is not None else None,
            "stale": True,
            "samples_by_source": {},
            "live_sample_count": 0,
            "has_live_samples": False,
            "spread_pct_percentile": None,
            "adverse_selection_pct_percentile": None,
            "retry_reject_rate_percentile": None,
            "missed_fill_rate_percentile": None,
            "retry_penalty_pct_percentile": None,
            "missed_fill_penalty_pct_percentile": None,
            "total_cost_pct_percentile": None,
            "recommended_floor_pct_percentile": None,
            "total_cost_pct_p75": None,
            "total_cost_pct_p90": None,
            "recommended_floor_pct_p75": None,
            "recommended_floor_pct_p90": None,
            "empirical_floor_p75_pct": None,
            "empirical_floor_p90_pct": None,
            "empirical_floor_pct": None,
        }

        if sample_count == 0:
            return out

        source_counts: Dict[str, int] = {}
        for item in samples:
            source = str(item.get("sample_source") or "proxy").strip().lower() or "proxy"
            source_counts[source] = int(source_counts.get(source, 0) + 1)

        live_sample_count = int(
            source_counts.get("artifact_empirical", 0)
            + source_counts.get("lifecycle", 0)
            + source_counts.get("live", 0)
        )

        def pct(name: str, percentile_val: float) -> Optional[float]:
            vals = [
                float(item[name])
                for item in samples
                if item.get(name) is not None and np.isfinite(float(item[name]))
            ]
            if not vals:
                return None
            p_val = float(np.clip(percentile_val, 0.0, 100.0))
            return float(np.percentile(np.asarray(vals, dtype=float), p_val))

        spread_pct_p = pct("spread_pct", p)
        adverse_pct_p = pct("adverse_selection_pct", p)
        retry_rate_p = pct("retry_reject_rate", p)
        missed_rate_p = pct("missed_fill_rate", p)
        retry_penalty_p = pct("retry_penalty_pct", p)
        missed_penalty_p = pct("missed_fill_penalty_pct", p)
        total_cost_p = pct("total_pct", p)
        recommended_p = pct("recommended_floor_pct", p)
        total_cost_p75 = pct("total_pct", 75.0)
        total_cost_p90 = pct("total_pct", 90.0)
        recommended_p75 = pct("recommended_floor_pct", 75.0)
        recommended_p90 = pct("recommended_floor_pct", 90.0)

        empirical_floor_candidates = [x for x in [total_cost_p, recommended_p] if x is not None]
        empirical_floor = float(max(empirical_floor_candidates)) if empirical_floor_candidates else None
        empirical_floor_p75_candidates = [x for x in [total_cost_p75, recommended_p75] if x is not None]
        empirical_floor_p75 = (
            float(max(empirical_floor_p75_candidates)) if empirical_floor_p75_candidates else None
        )
        empirical_floor_p90_candidates = [x for x in [total_cost_p90, recommended_p90] if x is not None]
        empirical_floor_p90 = (
            float(max(empirical_floor_p90_candidates)) if empirical_floor_p90_candidates else None
        )

        stale = bool(
            sample_count < max(int(min_samples), 1)
            or (bars_since_update is not None and bars_since_update > max(int(stale_bars), 0))
        )

        out.update(
            {
                "stale": bool(stale),
                "samples_by_source": dict(source_counts),
                "live_sample_count": int(live_sample_count),
                "has_live_samples": bool(live_sample_count > 0),
                "spread_pct_percentile": spread_pct_p,
                "adverse_selection_pct_percentile": adverse_pct_p,
                "retry_reject_rate_percentile": retry_rate_p,
                "missed_fill_rate_percentile": missed_rate_p,
                "retry_penalty_pct_percentile": retry_penalty_p,
                "missed_fill_penalty_pct_percentile": missed_penalty_p,
                "total_cost_pct_percentile": total_cost_p,
                "recommended_floor_pct_percentile": recommended_p,
                "total_cost_pct_p75": total_cost_p75,
                "total_cost_pct_p90": total_cost_p90,
                "recommended_floor_pct_p75": recommended_p75,
                "recommended_floor_pct_p90": recommended_p90,
                "empirical_floor_p75_pct": empirical_floor_p75,
                "empirical_floor_p90_pct": empirical_floor_p90,
                "empirical_floor_pct": empirical_floor,
            }
        )
        return out
