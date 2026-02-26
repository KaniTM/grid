from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Iterable, List

import pandas as pd
from pandas import DataFrame

from core.enums import BlockReason


def assess_data_quality(
    dataframe: DataFrame,
    *,
    expected_candle_seconds: float,
    gap_multiplier: float,
    max_stale_minutes: float,
    zero_volume_streak_bars: int,
    required_columns: Iterable[str] = ("bb_mid_1h", "bb_mid_4h"),
) -> Dict[str, object]:
    reasons: List[BlockReason] = []
    details: Dict[str, object] = {}
    ok = True

    ts = pd.to_datetime(dataframe["date"], utc=True, errors="coerce")
    details["last_timestamp"] = ts.iloc[-1].isoformat() if len(ts) and pd.notna(ts.iloc[-1]) else None

    def add_reason(reason: BlockReason) -> None:
        if reason not in reasons:
            reasons.append(reason)

    if ts.isnull().any():
        ok = False
        add_reason(BlockReason.BLOCK_DATA_MISALIGN)
    if ts.duplicated().any():
        ok = False
        add_reason(BlockReason.BLOCK_DATA_MISALIGN)
    if not ts.is_monotonic_increasing:
        ok = False
        add_reason(BlockReason.BLOCK_DATA_MISALIGN)

    if len(ts) >= 2:
        diffs = ts.diff().dt.total_seconds().iloc[1:]
        threshold = float(expected_candle_seconds) * float(gap_multiplier)
        if (diffs > threshold).any():
            ok = False
            add_reason(BlockReason.BLOCK_DATA_GAP)
            details["gap_detected_secs"] = float(max(diffs))

    if len(ts) >= 1 and pd.notna(ts.iloc[-1]):
        now_ts = datetime.now(timezone.utc)
        stale_secs = (now_ts - ts.iloc[-1]).total_seconds()
        details["stale_secs"] = float(stale_secs)
        if stale_secs >= float(max_stale_minutes) * 60.0:
            ok = False
            add_reason(BlockReason.BLOCK_DATA_GAP)

    zero_check = int(max(0, zero_volume_streak_bars))
    if zero_check > 0 and len(dataframe) >= zero_check:
        tail_vol = pd.to_numeric(dataframe["volume"].iloc[-zero_check:], errors="coerce").fillna(0.0)
        if tail_vol.eq(0.0).all():
            ok = False
            add_reason(BlockReason.BLOCK_ZERO_VOL_ANOMALY)

    last = dataframe.iloc[-1]
    for column in required_columns:
        value = last.get(column)
        if value is None or pd.isna(value):
            ok = False
            add_reason(BlockReason.BLOCK_DATA_MISALIGN)
            break

    return {
        "ok": bool(ok),
        "reasons": reasons,
        "details": details,
    }

