from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal, Optional, Tuple

import numpy as np
import pandas as pd
from pandas import DataFrame


OrderBlockSide = Literal["bull", "bear"]


@dataclass(frozen=True)
class OrderBlock:
    side: OrderBlockSide
    tf: str
    created_ts: int
    top: float
    bottom: float
    mid: float
    mitigated: bool
    last_mitigated_ts: Optional[int]


@dataclass(frozen=True)
class OrderBlockConfig:
    enabled: bool = True
    tf: str = "1h"
    use_wick_zone: bool = True
    impulse_lookahead: int = 3
    impulse_atr_len: int = 14
    impulse_atr_mult: float = 1.0
    fresh_bars: int = 20
    max_age_bars: int = 400
    mitigation_mode: str = "wick"  # wick | close


@dataclass(frozen=True)
class OrderBlockSnapshot:
    bull: Optional[OrderBlock]
    bear: Optional[OrderBlock]
    bull_age_bars: Optional[int]
    bear_age_bars: Optional[int]
    bull_fresh: bool
    bear_fresh: bool
    bull_valid: bool
    bear_valid: bool

    def as_dict(self) -> Dict[str, object]:
        def to_dict(block: Optional[OrderBlock]) -> Optional[Dict[str, object]]:
            if block is None:
                return None
            return {
                "side": block.side,
                "tf": block.tf,
                "created_ts": int(block.created_ts),
                "top": float(block.top),
                "bottom": float(block.bottom),
                "mid": float(block.mid),
                "mitigated": bool(block.mitigated),
                "last_mitigated_ts": (
                    int(block.last_mitigated_ts)
                    if block.last_mitigated_ts is not None
                    else None
                ),
            }

        return {
            "bull": to_dict(self.bull),
            "bear": to_dict(self.bear),
            "bull_age_bars": self.bull_age_bars,
            "bear_age_bars": self.bear_age_bars,
            "bull_fresh": bool(self.bull_fresh),
            "bear_fresh": bool(self.bear_fresh),
            "bull_valid": bool(self.bull_valid),
            "bear_valid": bool(self.bear_valid),
        }


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            (high - low).abs(),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    lookback = max(int(length), 1)
    return tr.rolling(lookback, min_periods=lookback).mean()


def _row_ts_seconds(row_ts: object) -> Optional[int]:
    if row_ts is None:
        return None
    try:
        ts = pd.Timestamp(row_ts)
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")
        else:
            ts = ts.tz_convert("UTC")
        return int(ts.value // 10**9)
    except Exception:
        return None


def _extract_ts_series(df: DataFrame) -> pd.Series:
    if "date" in df.columns:
        return pd.to_datetime(df["date"], utc=True, errors="coerce")
    return pd.to_datetime(df.index, utc=True, errors="coerce")


def _zone_bounds(
    open_val: float,
    high_val: float,
    low_val: float,
    close_val: float,
    use_wick_zone: bool,
) -> Tuple[float, float]:
    if use_wick_zone:
        return float(high_val), float(low_val)
    body_top = max(float(open_val), float(close_val))
    body_bottom = min(float(open_val), float(close_val))
    return body_top, body_bottom


def _is_impulse_match(
    side: OrderBlockSide,
    *,
    base_high: float,
    base_low: float,
    atr_value: float,
    future_closes: np.ndarray,
    atr_mult: float,
) -> bool:
    if side == "bull":
        threshold = float(base_high + (atr_mult * atr_value))
        return bool(np.any(future_closes > threshold))
    threshold = float(base_low - (atr_mult * atr_value))
    return bool(np.any(future_closes < threshold))


def _detect_latest_block_for_side(
    df: DataFrame,
    *,
    side: OrderBlockSide,
    cfg: OrderBlockConfig,
    atr: pd.Series,
) -> Tuple[Optional[OrderBlock], Optional[int]]:
    n = len(df)
    lookahead = max(int(cfg.impulse_lookahead), 1)
    if n <= lookahead:
        return None, None

    opens = pd.to_numeric(df["open"], errors="coerce").to_numpy(dtype=float)
    highs = pd.to_numeric(df["high"], errors="coerce").to_numpy(dtype=float)
    lows = pd.to_numeric(df["low"], errors="coerce").to_numpy(dtype=float)
    closes = pd.to_numeric(df["close"], errors="coerce").to_numpy(dtype=float)
    atr_vals = pd.to_numeric(atr, errors="coerce").to_numpy(dtype=float)
    ts_series = _extract_ts_series(df)

    latest_idx: Optional[int] = None
    for idx in range(0, n - lookahead):
        o = opens[idx]
        h = highs[idx]
        l = lows[idx]
        c = closes[idx]
        atr_value = atr_vals[idx]
        if not (np.isfinite(o) and np.isfinite(h) and np.isfinite(l) and np.isfinite(c) and np.isfinite(atr_value)):
            continue
        if side == "bull" and not (c < o):
            continue
        if side == "bear" and not (c > o):
            continue

        future = closes[idx + 1 : idx + lookahead + 1]
        if future.size == 0 or not np.isfinite(future).any():
            continue
        future = future[np.isfinite(future)]
        if future.size == 0:
            continue

        if _is_impulse_match(
            side,
            base_high=float(h),
            base_low=float(l),
            atr_value=float(atr_value),
            future_closes=future,
            atr_mult=float(max(cfg.impulse_atr_mult, 0.0)),
        ):
            latest_idx = idx

    if latest_idx is None:
        return None, None

    o = float(opens[latest_idx])
    h = float(highs[latest_idx])
    l = float(lows[latest_idx])
    c = float(closes[latest_idx])
    top, bottom = _zone_bounds(o, h, l, c, bool(cfg.use_wick_zone))
    if not (np.isfinite(top) and np.isfinite(bottom)) or top <= bottom:
        return None, None

    created_ts = _row_ts_seconds(ts_series.iloc[latest_idx])
    if created_ts is None:
        return None, None

    mitigation_mode = str(cfg.mitigation_mode or "wick").strip().lower()
    post = df.iloc[latest_idx + 1 :]
    mitigated = False
    last_mitigated_ts: Optional[int] = None
    if not post.empty:
        post_high = pd.to_numeric(post["high"], errors="coerce")
        post_low = pd.to_numeric(post["low"], errors="coerce")
        post_close = pd.to_numeric(post["close"], errors="coerce")
        post_ts = _extract_ts_series(post)

        if mitigation_mode == "close":
            mask = (post_close >= bottom) & (post_close <= top)
        else:
            mask = (post_low <= top) & (post_high >= bottom)

        touched_idx = np.flatnonzero(mask.to_numpy(dtype=bool))
        if touched_idx.size > 0:
            mitigated = True
            ts_val = _row_ts_seconds(post_ts.iloc[int(touched_idx[-1])])
            if ts_val is not None:
                last_mitigated_ts = int(ts_val)

    block = OrderBlock(
        side=side,
        tf=str(cfg.tf or "1h"),
        created_ts=int(created_ts),
        top=float(top),
        bottom=float(bottom),
        mid=float((top + bottom) / 2.0),
        mitigated=bool(mitigated),
        last_mitigated_ts=last_mitigated_ts,
    )
    return block, int(latest_idx)


def _age_gated_block(
    block: Optional[OrderBlock],
    idx: Optional[int],
    *,
    bars_total: int,
    cfg: OrderBlockConfig,
) -> Tuple[Optional[OrderBlock], Optional[int], bool, bool]:
    if block is None or idx is None or bars_total <= 0:
        return None, None, False, False
    age_bars = int(max((bars_total - 1) - int(idx), 0))
    max_age = max(int(cfg.max_age_bars), 1)
    if age_bars > max_age:
        return None, age_bars, False, False
    fresh = bool(age_bars <= max(int(cfg.fresh_bars), 0))
    valid = bool(block.top > block.bottom)
    return block, age_bars, fresh, valid


def build_order_block_snapshot(df_1h: DataFrame, cfg: OrderBlockConfig) -> OrderBlockSnapshot:
    if not bool(cfg.enabled):
        return OrderBlockSnapshot(
            bull=None,
            bear=None,
            bull_age_bars=None,
            bear_age_bars=None,
            bull_fresh=False,
            bear_fresh=False,
            bull_valid=False,
            bear_valid=False,
        )

    required_cols = {"open", "high", "low", "close"}
    if df_1h is None or df_1h.empty or not required_cols.issubset(df_1h.columns):
        return OrderBlockSnapshot(
            bull=None,
            bear=None,
            bull_age_bars=None,
            bear_age_bars=None,
            bull_fresh=False,
            bear_fresh=False,
            bull_valid=False,
            bear_valid=False,
        )

    high = pd.to_numeric(df_1h["high"], errors="coerce")
    low = pd.to_numeric(df_1h["low"], errors="coerce")
    close = pd.to_numeric(df_1h["close"], errors="coerce")
    atr = _atr(high, low, close, max(int(cfg.impulse_atr_len), 1))

    bull_raw, bull_idx = _detect_latest_block_for_side(df_1h, side="bull", cfg=cfg, atr=atr)
    bear_raw, bear_idx = _detect_latest_block_for_side(df_1h, side="bear", cfg=cfg, atr=atr)

    bull, bull_age, bull_fresh, bull_valid = _age_gated_block(
        bull_raw,
        bull_idx,
        bars_total=len(df_1h),
        cfg=cfg,
    )
    bear, bear_age, bear_fresh, bear_valid = _age_gated_block(
        bear_raw,
        bear_idx,
        bars_total=len(df_1h),
        cfg=cfg,
    )

    return OrderBlockSnapshot(
        bull=bull,
        bear=bear,
        bull_age_bars=bull_age,
        bear_age_bars=bear_age,
        bull_fresh=bool(bull_fresh),
        bear_fresh=bool(bear_fresh),
        bull_valid=bool(bull_valid),
        bear_valid=bool(bear_valid),
    )
