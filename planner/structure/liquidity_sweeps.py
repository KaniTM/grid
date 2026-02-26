from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from pandas import DataFrame


@dataclass(frozen=True)
class LiquiditySweepConfig:
    enabled: bool = True
    pivot_len: int = 5
    max_age_bars: int = 200
    break_buffer_mode: str = "step"  # step | atr | pct | abs
    break_buffer_value: float = 0.2
    retest_window_bars: int = 12
    retest_buffer_mode: str = "step"  # step | atr | pct | abs
    retest_buffer_value: float = 0.2
    stop_if_through_box_edge: bool = True
    retest_validation_mode: str = "Wick"  # Wick | Open
    min_level_separation_steps: float = 1.0


def _atr(df: DataFrame, length: int) -> pd.Series:
    high = pd.to_numeric(df["high"], errors="coerce")
    low = pd.to_numeric(df["low"], errors="coerce")
    close = pd.to_numeric(df["close"], errors="coerce")
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            (high - low).abs(),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    window = max(int(length), 1)
    return tr.rolling(window, min_periods=window).mean()


def _buffer_value(
    *,
    mode: str,
    value: float,
    step_price: float,
    atr_value: float,
    price: float,
) -> float:
    mode_norm = str(mode or "step").strip().lower()
    base = float(max(value, 0.0))
    if mode_norm == "step":
        return float(max(base * max(step_price, 0.0), 0.0))
    if mode_norm == "atr":
        return float(max(base * max(atr_value, 0.0), 0.0))
    if mode_norm == "pct":
        return float(max(base * max(price, 0.0), 0.0))
    if mode_norm == "abs":
        return float(max(base, 0.0))
    return float(max(base * max(step_price, 0.0), 0.0))


def _confirmed_pivot_indices(highs: np.ndarray, lows: np.ndarray, pivot_len: int) -> Tuple[List[int], List[int]]:
    p = max(int(pivot_len), 1)
    n = len(highs)
    high_idx: List[int] = []
    low_idx: List[int] = []
    if n < ((2 * p) + 1):
        return high_idx, low_idx

    for i in range(p, n - p):
        hi = highs[i]
        lo = lows[i]
        if not (np.isfinite(hi) and np.isfinite(lo)):
            continue
        hi_window = highs[i - p : i + p + 1]
        lo_window = lows[i - p : i + p + 1]
        if np.isfinite(hi_window).all():
            hi_max = float(np.max(hi_window))
            if float(hi) == hi_max and int(np.sum(np.isclose(hi_window, hi_max, rtol=0.0, atol=1e-12))) == 1:
                high_idx.append(i)
        if np.isfinite(lo_window).all():
            lo_min = float(np.min(lo_window))
            if float(lo) == lo_min and int(np.sum(np.isclose(lo_window, lo_min, rtol=0.0, atol=1e-12))) == 1:
                low_idx.append(i)
    return high_idx, low_idx


def analyze_liquidity_sweeps(
    dataframe: DataFrame,
    *,
    cfg: LiquiditySweepConfig,
    step_price: float,
    box_low: Optional[float],
    box_high: Optional[float],
    event_hold_bars: int = 1,
) -> Dict[str, object]:
    out: Dict[str, object] = {
        "enabled": bool(cfg.enabled),
        "pivot_len": int(cfg.pivot_len),
        "swing_high": None,
        "swing_low": None,
        "swing_high_index": None,
        "swing_low_index": None,
        "sweep_high": False,
        "sweep_low": False,
        "break_retest_high": False,
        "break_retest_low": False,
        "break_level_high": None,
        "break_level_low": None,
        "tp_nudge": None,
        "stop_triggered": False,
        "block_start": False,
        "through_box_edge": False,
        "retest_validation_mode": str(cfg.retest_validation_mode),
        "events_recent": [],
    }

    required_cols = {"open", "high", "low", "close"}
    if not bool(cfg.enabled) or dataframe is None or len(dataframe) < 3 or not required_cols.issubset(dataframe.columns):
        return out

    work = dataframe.copy()
    opens = pd.to_numeric(work["open"], errors="coerce").to_numpy(dtype=float)
    highs = pd.to_numeric(work["high"], errors="coerce").to_numpy(dtype=float)
    lows = pd.to_numeric(work["low"], errors="coerce").to_numpy(dtype=float)
    closes = pd.to_numeric(work["close"], errors="coerce").to_numpy(dtype=float)
    n = len(work)

    if "atr_15m" in work.columns:
        atr_series = pd.to_numeric(work["atr_15m"], errors="coerce")
    else:
        atr_series = _atr(work, length=14)
    atr_vals = atr_series.to_numpy(dtype=float)

    pivot_len = max(int(cfg.pivot_len), 1)
    max_age = max(int(cfg.max_age_bars), 1)
    retest_window = max(int(cfg.retest_window_bars), 1)
    hold = max(int(event_hold_bars), 1)

    pivot_high_idx, pivot_low_idx = _confirmed_pivot_indices(highs, lows, pivot_len)
    ph_ptr = 0
    pl_ptr = 0

    current_high_idx: Optional[int] = None
    current_low_idx: Optional[int] = None
    current_high_level: Optional[float] = None
    current_low_level: Optional[float] = None

    min_sep_steps = float(max(cfg.min_level_separation_steps, 0.0))

    sweep_high_flags = np.zeros(n, dtype=bool)
    sweep_low_flags = np.zeros(n, dtype=bool)
    break_retest_high_flags = np.zeros(n, dtype=bool)
    break_retest_low_flags = np.zeros(n, dtype=bool)
    through_box_flags = np.zeros(n, dtype=bool)
    break_level_high: List[Optional[float]] = [None] * n
    break_level_low: List[Optional[float]] = [None] * n

    up_break_state: Optional[Dict[str, float]] = None
    dn_break_state: Optional[Dict[str, float]] = None
    mode = str(cfg.retest_validation_mode or "Wick").strip().lower()

    for t in range(n):
        close_t = closes[t]
        high_t = highs[t]
        low_t = lows[t]
        open_t = opens[t]
        atr_t = atr_vals[t] if np.isfinite(atr_vals[t]) else 0.0
        if not (np.isfinite(close_t) and np.isfinite(high_t) and np.isfinite(low_t) and np.isfinite(open_t)):
            continue

        while ph_ptr < len(pivot_high_idx) and (pivot_high_idx[ph_ptr] + pivot_len) <= t:
            idx = pivot_high_idx[ph_ptr]
            level = float(highs[idx])
            update_ok = True
            if current_high_level is not None and step_price > 0 and min_sep_steps > 0:
                if abs(level - current_high_level) < (min_sep_steps * step_price):
                    update_ok = False
            if update_ok:
                current_high_idx = int(idx)
                current_high_level = float(level)
            ph_ptr += 1

        while pl_ptr < len(pivot_low_idx) and (pivot_low_idx[pl_ptr] + pivot_len) <= t:
            idx = pivot_low_idx[pl_ptr]
            level = float(lows[idx])
            update_ok = True
            if current_low_level is not None and step_price > 0 and min_sep_steps > 0:
                if abs(level - current_low_level) < (min_sep_steps * step_price):
                    update_ok = False
            if update_ok:
                current_low_idx = int(idx)
                current_low_level = float(level)
            pl_ptr += 1

        if current_high_idx is not None and (t - current_high_idx) > max_age:
            current_high_idx = None
            current_high_level = None
        if current_low_idx is not None and (t - current_low_idx) > max_age:
            current_low_idx = None
            current_low_level = None

        break_buffer = _buffer_value(
            mode=cfg.break_buffer_mode,
            value=float(cfg.break_buffer_value),
            step_price=float(step_price),
            atr_value=float(atr_t),
            price=float(close_t),
        )
        retest_buffer = _buffer_value(
            mode=cfg.retest_buffer_mode,
            value=float(cfg.retest_buffer_value),
            step_price=float(step_price),
            atr_value=float(atr_t),
            price=float(close_t),
        )

        if current_high_level is not None:
            if high_t > (current_high_level + break_buffer) and close_t < current_high_level:
                sweep_high_flags[t] = True
            if close_t > (current_high_level + break_buffer):
                up_break_state = {
                    "level": float(current_high_level),
                    "break_index": float(t),
                }

        if current_low_level is not None:
            if low_t < (current_low_level - break_buffer) and close_t > current_low_level:
                sweep_low_flags[t] = True
            if close_t < (current_low_level - break_buffer):
                dn_break_state = {
                    "level": float(current_low_level),
                    "break_index": float(t),
                }

        if up_break_state is not None:
            b_idx = int(up_break_state.get("break_index", -1))
            b_level = float(up_break_state.get("level", np.nan))
            if t <= b_idx:
                pass
            elif (t - b_idx) > retest_window:
                up_break_state = None
            else:
                if mode == "open":
                    touched = bool(open_t <= (b_level + retest_buffer))
                else:
                    touched = bool(low_t <= (b_level + retest_buffer))
                invalidated = bool(touched and close_t < b_level)
                if invalidated:
                    break_retest_high_flags[t] = True
                    break_level_high[t] = float(b_level)
                    through = False
                    if box_high is not None:
                        through = bool(b_level >= (float(box_high) - max(retest_buffer, 0.0)))
                    through_box_flags[t] = bool(through_box_flags[t] or through)
                    up_break_state = None

        if dn_break_state is not None:
            b_idx = int(dn_break_state.get("break_index", -1))
            b_level = float(dn_break_state.get("level", np.nan))
            if t <= b_idx:
                pass
            elif (t - b_idx) > retest_window:
                dn_break_state = None
            else:
                if mode == "open":
                    touched = bool(open_t >= (b_level - retest_buffer))
                else:
                    touched = bool(high_t >= (b_level - retest_buffer))
                invalidated = bool(touched and close_t > b_level)
                if invalidated:
                    break_retest_low_flags[t] = True
                    break_level_low[t] = float(b_level)
                    through = False
                    if box_low is not None:
                        through = bool(b_level <= (float(box_low) + max(retest_buffer, 0.0)))
                    through_box_flags[t] = bool(through_box_flags[t] or through)
                    dn_break_state = None

    recent_slice = slice(max(n - hold, 0), n)
    recent_br_high = bool(np.any(break_retest_high_flags[recent_slice]))
    recent_br_low = bool(np.any(break_retest_low_flags[recent_slice]))
    recent_through = bool(np.any(through_box_flags[recent_slice]))

    current_sweep_high = bool(sweep_high_flags[-1])
    current_sweep_low = bool(sweep_low_flags[-1])
    current_break_retest_high = bool(break_retest_high_flags[-1])
    current_break_retest_low = bool(break_retest_low_flags[-1])

    stop_triggered = bool(
        cfg.stop_if_through_box_edge
        and recent_through
        and (recent_br_high or recent_br_low)
    )

    tp_nudge = None
    if current_sweep_high and current_high_level is not None and current_high_level > closes[-1]:
        tp_nudge = float(current_high_level)

    events_recent: List[str] = []
    if current_sweep_high:
        events_recent.append("EVENT_SWEEP_WICK_HIGH")
    if current_sweep_low:
        events_recent.append("EVENT_SWEEP_WICK_LOW")
    if recent_br_high:
        events_recent.append("EVENT_SWEEP_BREAK_RETEST_HIGH")
    if recent_br_low:
        events_recent.append("EVENT_SWEEP_BREAK_RETEST_LOW")

    out.update(
        {
            "swing_high": float(current_high_level) if current_high_level is not None else None,
            "swing_low": float(current_low_level) if current_low_level is not None else None,
            "swing_high_index": int(current_high_idx) if current_high_idx is not None else None,
            "swing_low_index": int(current_low_idx) if current_low_idx is not None else None,
            "sweep_high": bool(current_sweep_high),
            "sweep_low": bool(current_sweep_low),
            "break_retest_high": bool(current_break_retest_high),
            "break_retest_low": bool(current_break_retest_low),
            "break_retest_high_recent": bool(recent_br_high),
            "break_retest_low_recent": bool(recent_br_low),
            "break_level_high": next((float(x) for x in reversed(break_level_high) if x is not None), None),
            "break_level_low": next((float(x) for x in reversed(break_level_low) if x is not None), None),
            "tp_nudge": float(tp_nudge) if tp_nudge is not None else None,
            "through_box_edge": bool(recent_through),
            "stop_triggered": bool(stop_triggered),
            "block_start": bool(stop_triggered),
            "events_recent": events_recent,
        }
    )
    return out
