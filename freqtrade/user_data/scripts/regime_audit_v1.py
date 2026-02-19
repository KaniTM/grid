#!/usr/bin/env python3
"""
Long-history feature/label audit for regime calibration.

Outputs:
- Feature distributions by inferred range/trend labels.
- Recommended intraday/swing gate thresholds.
"""

# ruff: noqa

from __future__ import annotations


import argparse
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from freqtrade.exchange import timeframe_to_minutes


CAL_WINDOW_DAYS_DEFAULT = 180
ER_LOOKBACK = 20
CHOP_LOOKBACK = 20
ATR_PERIOD = 20
ADX_PERIOD = 14
CONTAINMENT_LOOKBACK_BARS = 96  # 24h window on 15m candles
SCORE_ENTER_QUANTILE = 0.70
SCORE_EXIT_QUANTILE = 0.55
SCORE_PERSISTENCE_DEFAULT = 4
FEATURE_HORIZON_MAP = {
    "er_15m": "15m",
    "chop_15m": "15m",
    "atr_pct_15m": "15m",
    "adx_4h": "4h",
}


def find_ohlcv_file(data_dir: str, pair: str, timeframe: str) -> str:
    pair_fs = pair.replace("/", "_").replace(":", "_")
    candidates: List[str] = []
    for root, _, files in os.walk(data_dir):
        for fn in files:
            low = fn.lower()
            if pair_fs.lower() in low and f"-{timeframe}".lower() in low:
                candidates.append(os.path.join(root, fn))
    if not candidates:
        raise FileNotFoundError(f"No OHLCV file found for {pair} {timeframe} under {data_dir}")
    pref = [".feather", ".parquet", ".json.gz", ".json", ".csv.gz", ".csv"]
    candidates.sort(key=lambda p: next((i for i, ext in enumerate(pref) if p.lower().endswith(ext)), 999))
    return candidates[0]


def load_ohlcv(path: str) -> pd.DataFrame:
    low = path.lower()
    if low.endswith(".feather"):
        df = pd.read_feather(path)
    elif low.endswith(".parquet"):
        df = pd.read_parquet(path)
    elif low.endswith(".json.gz"):
        df = pd.read_json(path, compression="gzip")
    elif low.endswith(".json"):
        df = pd.read_json(path)
    elif low.endswith(".csv.gz"):
        df = pd.read_csv(path, compression="gzip")
    elif low.endswith(".csv"):
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file format: {path}")

    cols = {c.lower(): c for c in df.columns}
    date_col = cols.get("date") or cols.get("timestamp") or cols.get("datetime")
    if not date_col:
        raise ValueError(f"No date/timestamp column found in {path}")
    df = df.rename(columns={date_col: "date"})
    for c in ["open", "high", "low", "close", "volume"]:
        if c not in df.columns:
            real = cols.get(c)
            if real:
                df = df.rename(columns={real: c})
    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return df[["date", "open", "high", "low", "close", "volume"]].copy()


def filter_timerange(df: pd.DataFrame, timerange: Optional[str]) -> pd.DataFrame:
    if not timerange:
        return df
    if "-" not in timerange:
        raise ValueError("timerange must be YYYYMMDD-YYYYMMDD")
    a, b = timerange.split("-", 1)
    start = pd.to_datetime(a, format="%Y%m%d", utc=True)
    end = pd.to_datetime(b, format="%Y%m%d", utc=True)
    return df[(df["date"] >= start) & (df["date"] < end)].reset_index(drop=True)


def bb_width(close: pd.Series, window: int = 20, stds: float = 2.0) -> pd.Series:
    mid = close.rolling(window, min_periods=window).mean()
    sd = close.rolling(window, min_periods=window).std(ddof=0)
    upper = mid + (stds * sd)
    lower = mid - (stds * sd)
    return (upper - lower) / mid.replace(0.0, np.nan)


def atr_series(high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
    hl = high - low
    hc = (high - close.shift(1)).abs()
    lc = (low - close.shift(1)).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.rolling(period, min_periods=period).mean()


def efficiency_ratio_series(series: pd.Series, period: int) -> pd.Series:
    out = pd.Series(np.nan, index=series.index)
    values = pd.to_numeric(series, errors="coerce").astype(float)
    if len(values) < (period + 1):
        return out
    for i in range(period, len(values)):
        window = values.iloc[i - period : i + 1]
        if window.isna().any():
            continue
        change = abs(window.iloc[-1] - window.iloc[0])
        volatility = window.diff().abs().sum()
        if volatility <= 0:
            continue
        out.iloc[i] = change / volatility
    return out


def choppiness_index_series(high: pd.Series, low: pd.Series, atr: pd.Series, period: int) -> pd.Series:
    out = pd.Series(np.nan, index=high.index)
    highs = pd.to_numeric(high, errors="coerce").astype(float)
    lows = pd.to_numeric(low, errors="coerce").astype(float)
    atr_vals = pd.to_numeric(atr, errors="coerce").astype(float)
    if len(highs) < period or len(lows) < period or len(atr_vals) < period:
        return out
    for i in range(period - 1, len(highs)):
        hwin = highs.iloc[i - period + 1 : i + 1]
        lwin = lows.iloc[i - period + 1 : i + 1]
        atr_win = atr_vals.iloc[i - period + 1 : i + 1]
        if hwin.isna().any() or lwin.isna().any() or atr_win.isna().any():
            continue
        total_atr = float(atr_win.sum())
        range_high = float(hwin.max())
        range_low = float(lwin.min())
        price_range = range_high - range_low
        if total_atr <= 0 or price_range <= 0:
            continue
        try:
            ratio = total_atr / price_range
            score = 100.0 * math.log10(ratio) / math.log10(period)
        except Exception:
            continue
        out.iloc[i] = score
    return out


def adx_wilder(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()

    plus_dm_s = pd.Series(plus_dm, index=high.index).ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    minus_dm_s = pd.Series(minus_dm, index=high.index).ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()

    plus_di = 100.0 * plus_dm_s / atr.replace(0.0, np.nan)
    minus_di = 100.0 * minus_dm_s / atr.replace(0.0, np.nan)
    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0.0, np.nan)
    return dx.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def rolling_percentile_last(series: pd.Series, lookback: int) -> pd.Series:
    vals = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)
    out = np.full(vals.shape[0], np.nan, dtype=float)
    n = len(vals)
    if lookback <= 1 or n < 2:
        return pd.Series(out, index=series.index)
    for i in range(n):
        cur = vals[i]
        if not np.isfinite(cur):
            continue
        start = max(0, i - lookback + 1)
        window = vals[start : i + 1]
        window = window[np.isfinite(window)]
        if len(window) < 2:
            continue
        out[i] = float((np.sum(window <= cur) / len(window)) * 100.0)
    return pd.Series(out, index=series.index)


def future_roll_max(series: pd.Series, horizon: int) -> pd.Series:
    rev = series.iloc[::-1].rolling(horizon, min_periods=horizon).max().iloc[::-1]
    return rev.shift(-1)


def future_roll_min(series: pd.Series, horizon: int) -> pd.Series:
    rev = series.iloc[::-1].rolling(horizon, min_periods=horizon).min().iloc[::-1]
    return rev.shift(-1)


def resample_ohlcv(df: pd.DataFrame, tf: str) -> pd.DataFrame:
    out = (
        df.set_index("date")
        .resample(tf)
        .agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
            }
        )
        .dropna()
        .reset_index()
    )
    return out


def build_feature_frame(df_15m: pd.DataFrame, bbwp_lookback: int) -> pd.DataFrame:
    df = df_15m.copy()
    df["atr_15m"] = atr_series(df["high"], df["low"], df["close"], ATR_PERIOD)
    df["atr_pct_15m"] = df["atr_15m"] / df["close"].replace({0.0: np.nan})
    df["rvol_15m"] = df["volume"] / df["volume"].rolling(20, min_periods=20).mean()
    df["bb_width_15m"] = bb_width(df["close"], window=20, stds=2.0)
    df["bbwp_15m_pct"] = rolling_percentile_last(df["bb_width_15m"], bbwp_lookback)

    df["high_24h"] = df["high"].rolling(CONTAINMENT_LOOKBACK_BARS, min_periods=1).max()
    df["low_24h"] = df["low"].rolling(CONTAINMENT_LOOKBACK_BARS, min_periods=1).min()
    df["close_in_24h_box"] = df["close"].between(df["low_24h"], df["high_24h"])
    df["containment_pct"] = df["close_in_24h_box"].rolling(CONTAINMENT_LOOKBACK_BARS, min_periods=1).mean()

    df_1h = resample_ohlcv(df_15m, "1h")
    df_1h["ema50_1h"] = df_1h["close"].ewm(span=50, adjust=False).mean()
    df_1h["ema100_1h"] = df_1h["close"].ewm(span=100, adjust=False).mean()
    df_1h["ema_dist_frac_1h"] = (df_1h["ema50_1h"] - df_1h["ema100_1h"]).abs() / df_1h["close"].replace(0.0, np.nan)
    df_1h["vol_ratio_1h"] = df_1h["volume"] / df_1h["volume"].rolling(20, min_periods=20).mean()
    df_1h["bb_width_1h"] = bb_width(df_1h["close"], window=20, stds=2.0)
    df_1h["bbwp_1h_pct"] = rolling_percentile_last(df_1h["bb_width_1h"], bbwp_lookback)
    df_1h["adx_1h"] = adx_wilder(df_1h["high"], df_1h["low"], df_1h["close"], period=ADX_PERIOD)

    df_4h = resample_ohlcv(df_15m, "4h")
    df_4h["adx_4h"] = adx_wilder(df_4h["high"], df_4h["low"], df_4h["close"], period=14)
    df_4h["bb_width_4h"] = bb_width(df_4h["close"], window=20, stds=2.0)
    df_4h["bbwp_4h_pct"] = rolling_percentile_last(df_4h["bb_width_4h"], bbwp_lookback)

    feat = df[
        [
            "date",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "rvol_15m",
            "bb_width_15m",
            "bbwp_15m_pct",
            "atr_15m",
            "atr_pct_15m",
            "containment_pct",
        ]
    ].copy()
    feat = pd.merge_asof(
        feat.sort_values("date"),
        df_1h[
            [
                "date",
                "ema_dist_frac_1h",
                "vol_ratio_1h",
                "bb_width_1h",
                "bbwp_1h_pct",
                "adx_1h",
            ]
        ].sort_values("date"),
        on="date",
        direction="backward",
    )
    feat = pd.merge_asof(
        feat.sort_values("date"),
        df_4h[["date", "adx_4h", "bb_width_4h", "bbwp_4h_pct"]].sort_values("date"),
        on="date",
        direction="backward",
    )
    feat["bb_width_1h_pct"] = feat["bbwp_1h_pct"]
    feat["er_15m"] = efficiency_ratio_series(df["close"], ER_LOOKBACK)
    feat["chop_15m"] = choppiness_index_series(df["high"], df["low"], df["atr_15m"], CHOP_LOOKBACK)
    return feat


def add_labels(
    feat: pd.DataFrame,
    prefix: str,
    horizon_bars: int,
    range_ret_max: float,
    range_span_min: float,
    range_span_max: float,
    range_eff_max: float,
    trend_ret_min: float,
    trend_eff_min: float,
) -> pd.DataFrame:
    out = feat.copy()
    close = out["close"]
    f_close = close.shift(-horizon_bars)
    f_hi = future_roll_max(out["high"], horizon_bars)
    f_lo = future_roll_min(out["low"], horizon_bars)
    f_abs_ret = (f_close / close - 1.0).abs()
    f_span = (f_hi - f_lo) / close.replace(0.0, np.nan)
    f_eff = (f_close - close).abs() / (f_hi - f_lo).replace(0.0, np.nan)

    range_label = (
        (f_abs_ret <= range_ret_max)
        & (f_span >= range_span_min)
        & (f_span <= range_span_max)
        & (f_eff <= range_eff_max)
    )
    trend_label = (f_abs_ret >= trend_ret_min) & (f_eff >= trend_eff_min)
    range_label = range_label & (~trend_label)

    out[f"{prefix}_fwd_abs_ret"] = f_abs_ret
    out[f"{prefix}_fwd_span"] = f_span
    out[f"{prefix}_fwd_eff"] = f_eff
    out[f"{prefix}_range_label"] = range_label.astype(int)
    out[f"{prefix}_trend_label"] = trend_label.astype(int)
    return out


def qval(series: pd.Series, q: float, fallback: float) -> float:
    vals = pd.to_numeric(series, errors="coerce").dropna()
    if len(vals) == 0:
        return float(fallback)
    return float(vals.quantile(q))


def assign_non_trend_mask(
    adx_pct: pd.Series,
    enter_pct: float = 55.0,
    exit_pct: float = 65.0,
    veto_pct: float = 70.0,
) -> pd.Series:
    series = pd.to_numeric(adx_pct, errors="coerce")
    mask = np.zeros(len(series), dtype=bool)
    current = False
    for pos, val in enumerate(series):
        if not np.isfinite(val):
            current = False
        elif val >= veto_pct:
            current = False
        elif current:
            current = val < exit_pct
        else:
            current = val <= enter_pct
        mask[pos] = current
    return pd.Series(mask, index=series.index)


def percentile_stats(series: pd.Series) -> Dict[str, Optional[float]]:
    vals = pd.to_numeric(series, errors="coerce").dropna()
    if len(vals) == 0:
        return {}
    return {
        "p10": float(vals.quantile(0.10)),
        "p50": float(vals.quantile(0.50)),
        "p90": float(vals.quantile(0.90)),
    }


def normalize_series(series: pd.Series, stats: Dict[str, Optional[float]]) -> pd.Series:
    if not stats:
        return pd.Series(np.nan, index=series.index)
    p10 = stats.get("p10")
    p90 = stats.get("p90")
    if p10 is None or p90 is None or p90 <= p10:
        return pd.Series(np.nan, index=series.index)
    vals = pd.to_numeric(series, errors="coerce")
    norm = (vals - float(p10)) / float(p90 - p10)
    return norm.clip(0.0, 1.0)


def feature_quantiles(df: pd.DataFrame, mask: pd.Series, features: List[str]) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    sub = df.loc[mask, features]
    for col in features:
        vals = pd.to_numeric(sub[col], errors="coerce").dropna()
        if len(vals) == 0:
            out[col] = {}
            continue
        out[col] = {
            "q10": float(vals.quantile(0.10)),
            "q25": float(vals.quantile(0.25)),
            "q50": float(vals.quantile(0.50)),
            "q75": float(vals.quantile(0.75)),
            "q90": float(vals.quantile(0.90)),
        }
    return out


def recommend_mode_thresholds(df: pd.DataFrame, prefix: str, defaults: Dict[str, float]) -> Dict[str, float]:
    mask = df[f"{prefix}_range_label"] == 1
    sub = df.loc[mask]
    adx_enter = qval(sub["adx_4h"], 0.75, defaults["adx_enter_max"])
    adx_exit = max(adx_enter + 3.0, qval(sub["adx_4h"], 0.90, defaults["adx_exit_max"]))
    return {
        "adx_enter_max": round(adx_enter, 4),
        "adx_exit_max": round(adx_exit, 4),
        "bbw_1h_pct_max": round(qval(sub["bb_width_1h_pct"], 0.80, defaults["bbw_1h_pct_max"]), 4),
        "ema_dist_max_frac": round(qval(sub["ema_dist_frac_1h"], 0.75, defaults["ema_dist_max_frac"]), 6),
        "vol_spike_mult": round(qval(sub["vol_ratio_1h"], 0.90, defaults["vol_spike_mult"]), 4),
        "bbwp_s_max": round(qval(sub["bbwp_15m_pct"], 0.75, defaults["bbwp_s_max"]), 4),
        "bbwp_m_max": round(qval(sub["bbwp_1h_pct"], 0.75, defaults["bbwp_m_max"]), 4),
        "bbwp_l_max": round(qval(sub["bbwp_4h_pct"], 0.75, defaults["bbwp_l_max"]), 4),
        "os_dev_rvol_max": round(qval(sub["rvol_15m"], 0.80, defaults["os_dev_rvol_max"]), 4),
        "os_dev_persist_bars": int(defaults["os_dev_persist_bars"]),
    }


def label_counts(df: pd.DataFrame, prefix: str) -> Dict[str, int]:
    def label_sum(col_name: str) -> int:
        if col_name not in df:
            return 0
        return int((df[col_name] == 1).sum())

    return {
        "rows_total": int(len(df)),
        "range_label": label_sum(f"{prefix}_range_label"),
        "trend_label": label_sum(f"{prefix}_trend_label"),
        "non_trend_range_label": label_sum(f"{prefix}_non_trend_range_label"),
        "neutral_choppy_label": label_sum(f"{prefix}_neutral_choppy_label"),
    }


def add_verbose_states(feat: pd.DataFrame, prefixes: List[str]) -> pd.DataFrame:
    out = feat.copy()
    for prefix in prefixes:
        f_abs = f"{prefix}_fwd_abs_ret"
        f_span = f"{prefix}_fwd_span"
        f_eff = f"{prefix}_fwd_eff"
        range_col = f"{prefix}_range_label"
        trend_col = f"{prefix}_trend_label"
        non_trend_range_col = f"{prefix}_non_trend_range_label"
        neutral_choppy_col = f"{prefix}_neutral_choppy_label"

        valid_col = f"{prefix}_label_valid"
        state_col = f"{prefix}_state"
        transition_col = f"{prefix}_transition"
        run_len_col = f"{prefix}_state_run_len"

        out[valid_col] = (
            pd.to_numeric(out[f_abs], errors="coerce").notna()
            & pd.to_numeric(out[f_span], errors="coerce").notna()
            & pd.to_numeric(out[f_eff], errors="coerce").notna()
        )

        if non_trend_range_col in out:
            non_trend_range_vals = out[non_trend_range_col].astype(bool)
        else:
            non_trend_range_vals = pd.Series(False, index=out.index)
        if neutral_choppy_col in out:
            neutral_choppy_vals = out[neutral_choppy_col].astype(bool)
        else:
            neutral_choppy_vals = pd.Series(False, index=out.index)

        state = np.where(
            ~out[valid_col],
            "unlabeled",
            np.where(
                out[trend_col] == 1,
                "trend",
                np.where(
                    neutral_choppy_vals,
                    "neutral_choppy",
                    np.where(
                        non_trend_range_vals,
                        "non_trend_range",
                        np.where(out[range_col] == 1, "range", "neutral"),
                    ),
                ),
            ),
        )
        out[state_col] = state

        state_change = out[state_col] != out[state_col].shift(1)
        valid_now = out[valid_col].astype(bool)
        valid_prev = out[valid_col].shift(1)
        valid_prev = valid_prev.where(valid_prev.notna(), False).astype(bool)
        valid_change = valid_now & valid_prev
        out[transition_col] = (state_change & valid_change).astype(int)

        group_id = state_change.cumsum()
        out[run_len_col] = out.groupby(group_id).cumcount() + 1
    return out


def extract_transition_events(
    df: pd.DataFrame,
    prefix: str,
    feature_cols: List[str],
) -> List[Dict[str, object]]:
    state_col = f"{prefix}_state"
    valid_col = f"{prefix}_label_valid"
    run_len_col = f"{prefix}_state_run_len"
    prev_state = df[state_col].shift(1)
    prev_run_len = pd.to_numeric(df[run_len_col].shift(1), errors="coerce")
    valid_now = df[valid_col].astype(bool)
    valid_prev = df[valid_col].shift(1)
    valid_prev = valid_prev.where(valid_prev.notna(), False).astype(bool)
    changed = valid_now & valid_prev & (df[state_col] != prev_state)

    events: List[Dict[str, object]] = []
    for idx in df.index[changed]:
        row = df.loc[idx]
        from_state = str(prev_state.loc[idx])
        to_state = str(row[state_col])
        ev: Dict[str, object] = {
            "date": pd.to_datetime(row["date"], utc=True),
            "mode": str(prefix),
            "from_state": from_state,
            "to_state": to_state,
            "from_to": f"{from_state}->{to_state}",
            "prev_state_run_len_bars": int(prev_run_len.loc[idx]) if pd.notna(prev_run_len.loc[idx]) else None,
            "to_state_run_len_bars": int(row[run_len_col]) if pd.notna(row[run_len_col]) else None,
            f"{prefix}_fwd_abs_ret": float(row[f"{prefix}_fwd_abs_ret"]) if pd.notna(row[f"{prefix}_fwd_abs_ret"]) else None,
            f"{prefix}_fwd_span": float(row[f"{prefix}_fwd_span"]) if pd.notna(row[f"{prefix}_fwd_span"]) else None,
            f"{prefix}_fwd_eff": float(row[f"{prefix}_fwd_eff"]) if pd.notna(row[f"{prefix}_fwd_eff"]) else None,
            f"{prefix}_range_label": int(row[f"{prefix}_range_label"]) if pd.notna(row[f"{prefix}_range_label"]) else None,
            f"{prefix}_trend_label": int(row[f"{prefix}_trend_label"]) if pd.notna(row[f"{prefix}_trend_label"]) else None,
            f"{prefix}_non_trend_range_label": int(row[f"{prefix}_non_trend_range_label"]) if f"{prefix}_non_trend_range_label" in row and pd.notna(row[f"{prefix}_non_trend_range_label"]) else None,
            f"{prefix}_neutral_choppy_label": int(row[f"{prefix}_neutral_choppy_label"]) if f"{prefix}_neutral_choppy_label" in row and pd.notna(row[f"{prefix}_neutral_choppy_label"]) else None,
        }
        for col in feature_cols:
            val = row[col] if col in row else None
            if val is None or pd.isna(val):
                ev[col] = None
            else:
                ev[col] = float(val)
        events.append(ev)
    return events


def transition_counts(events: List[Dict[str, object]]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for ev in events:
        key = str(ev.get("from_to") or "").strip()
        if not key:
            continue
        out[key] = int(out.get(key, 0)) + 1
    return {k: int(v) for k, v in sorted(out.items(), key=lambda kv: (-int(kv[1]), str(kv[0])))}


def median_state_run_length(df: pd.DataFrame, prefix: str, state: str) -> Optional[int]:
    state_col = f"{prefix}_state"
    run_len_col = f"{prefix}_state_run_len"
    if state_col not in df or run_len_col not in df:
        return None
    mask = df[state_col] == state
    values = pd.to_numeric(df.loc[mask, run_len_col], errors="coerce")
    if values.empty:
        return None
    median_val = float(np.nanmedian(values))
    if math.isnan(median_val):
        return None
    return int(round(median_val))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", required=True, help="e.g. ETH/USDT")
    ap.add_argument("--timeframe", default="15m", help="base timeframe file to load (usually 15m)")
    ap.add_argument("--data-dir", default="/freqtrade/user_data/data/binance", help="OHLCV directory")
    ap.add_argument("--timerange", default=None, help="YYYYMMDD-YYYYMMDD (optional)")
    ap.add_argument("--bbwp-lookback", type=int, default=252)
    ap.add_argument("--out", required=True, help="output json path")
    ap.add_argument(
        "--cal-window-days",
        type=float,
        default=CAL_WINDOW_DAYS_DEFAULT,
        help="rolling window (in days) used to compute ER/CHOP/ADX/ATR percentiles",
    )
    ap.add_argument("--artifact-root", default="/freqtrade/user_data/artifacts", help="base folder for artifacts")
    ap.add_argument("--artifact-run-id", default=None, help="run id under artifact root (auto-generated when omitted)")
    ap.add_argument(
        "--score-enter-quantile",
        type=float,
        default=SCORE_ENTER_QUANTILE,
        help="quantile used for recommended enter score",
    )
    ap.add_argument(
        "--score-exit-quantile",
        type=float,
        default=SCORE_EXIT_QUANTILE,
        help="quantile used for recommended exit score",
    )
    ap.add_argument(
        "--score-persistence-bars",
        type=int,
        default=SCORE_PERSISTENCE_DEFAULT,
        help="persistence (in 15m bars) for score hysteresis",
    )
    ap.add_argument("--emit-features-csv", default=None, help="optional feature dump csv path")
    ap.add_argument("--emit-verbose-csv", default=None, help="optional per-candle verbose audit csv path")
    ap.add_argument("--emit-transitions-csv", default=None, help="optional transition events csv path")
    ap.add_argument("--emit-transitions-json", default=None, help="optional transition events json path")
    args = ap.parse_args()

    ohlcv_path = find_ohlcv_file(args.data_dir, args.pair, args.timeframe)
    df = load_ohlcv(ohlcv_path)
    df = filter_timerange(df, args.timerange)
    if len(df) < 500:
        raise ValueError("Not enough rows after timerange filter. Need at least 500 rows.")

    feat = build_feature_frame(df, bbwp_lookback=int(args.bbwp_lookback))
    feat = add_labels(
        feat,
        prefix="intraday",
        horizon_bars=16,
        range_ret_max=0.008,
        range_span_min=0.006,
        range_span_max=0.045,
        range_eff_max=0.40,
        trend_ret_min=0.015,
        trend_eff_min=0.60,
    )
    feat = add_labels(
        feat,
        prefix="swing",
        horizon_bars=96,
        range_ret_max=0.015,
        range_span_min=0.010,
        range_span_max=0.080,
        range_eff_max=0.45,
        trend_ret_min=0.030,
        trend_eff_min=0.65,
    )

    feature_cols = [
        "adx_4h",
        "adx_1h",
        "ema_dist_frac_1h",
        "bb_width_1h_pct",
        "bbwp_15m_pct",
        "bbwp_1h_pct",
        "bbwp_4h_pct",
        "vol_ratio_1h",
        "rvol_15m",
        "er_15m",
        "chop_15m",
        "atr_pct_15m",
        "containment_pct",
    ]
    valid = feat.dropna(subset=feature_cols).copy()
    if len(valid) == 0:
        raise ValueError("No valid rows after feature construction.")

    tf_minutes = max(1, timeframe_to_minutes(args.timeframe))
    bars_per_day = max(1, int(round((24 * 60) / tf_minutes)))
    cal_window_bars = max(1, int(round(args.cal_window_days * bars_per_day)))
    window = valid.tail(cal_window_bars)

    valid["er_pct_15m"] = rolling_percentile_last(valid["er_15m"], cal_window_bars)
    valid["chop_pct_15m"] = rolling_percentile_last(valid["chop_15m"], cal_window_bars)
    valid["adx_pct_4h"] = rolling_percentile_last(valid["adx_4h"], cal_window_bars)
    valid["adx_pct_1h"] = rolling_percentile_last(valid["adx_1h"], cal_window_bars)
    valid["atr_pct_pct"] = rolling_percentile_last(valid["atr_pct_15m"], cal_window_bars)

    valid["intraday_non_trend_mask"] = assign_non_trend_mask(valid["adx_pct_1h"])
    valid["swing_non_trend_mask"] = assign_non_trend_mask(valid["adx_pct_4h"])


    # Neutral/choppy detection inside the non-trend regime.
    chop_condition = (
        (valid["chop_15m"] >= 61.8)
        | (valid["chop_pct_15m"] >= 70.0)
    )
    er_condition = valid["er_pct_15m"] <= 40.0
    containment_condition = valid["containment_pct"] >= 0.65
    # Default "neutral/choppy" contract: high chop, low ER, and sustained containment.
    neutral_choppy_base = chop_condition & er_condition & containment_condition
    neutral_choppy_base = neutral_choppy_base.fillna(False).astype(bool)

    valid["intraday_neutral_choppy_label"] = neutral_choppy_base & valid["intraday_non_trend_mask"]
    valid["swing_neutral_choppy_label"] = neutral_choppy_base & valid["swing_non_trend_mask"]

    valid["intraday_non_trend_range_label"] = (
        valid["intraday_range_label"].astype(bool)
        & valid["intraday_non_trend_mask"]
        & (~valid["intraday_neutral_choppy_label"])
    )
    valid["swing_non_trend_range_label"] = (
        valid["swing_range_label"].astype(bool)
        & valid["swing_non_trend_mask"]
        & (~valid["swing_neutral_choppy_label"])
    )

    er_stats = percentile_stats(window["er_15m"])
    chop_stats = percentile_stats(window["chop_15m"])
    atr_stats = percentile_stats(window["atr_pct_15m"])
    adx_stats = percentile_stats(window["adx_4h"])

    er_norm = normalize_series(valid["er_15m"], er_stats)
    chop_norm = normalize_series(valid["chop_15m"], chop_stats)
    atr_norm = normalize_series(valid["atr_pct_15m"], atr_stats)
    adx_norm = normalize_series(valid["adx_4h"], adx_stats)

    bbwp_stats = percentile_stats(window["bbwp_15m_pct"])
    valid["volatility_allowed"] = (
        (valid["bbwp_15m_pct"] >= 20.0)
        & (valid["bbwp_15m_pct"] <= 60.0)
    )
    valid["volatility_veto"] = valid["bbwp_15m_pct"] >= 85.0
    atr_non_dead = valid["atr_pct_pct"] >= 15.0
    valid["dead_vol_veto"] = (valid["bbwp_15m_pct"] <= 10.0) & (~atr_non_dead)
    valid["volatility_ready"] = (
        valid["volatility_allowed"]
        & (~valid["volatility_veto"])
        & (~valid["dead_vol_veto"])
    )

    volatility_component = valid["volatility_ready"].astype(float).fillna(0.0)

    score_series = (
        0.30 * (1.0 - er_norm)
        + 0.30 * chop_norm
        + 0.25 * (1.0 - adx_norm)
        + 0.10 * atr_norm
        + 0.05 * volatility_component
    )
    valid["chop_score"] = score_series

    score_enter = qval(score_series, args.score_enter_quantile, SCORE_ENTER_QUANTILE)
    score_exit = qval(score_series, args.score_exit_quantile, SCORE_EXIT_QUANTILE)
    score_stats = percentile_stats(score_series.dropna())

    artifact_run_id = str(args.artifact_run_id or "").strip()
    if not artifact_run_id:
        artifact_run_id = datetime.now(timezone.utc).strftime("regime_bands_%Y%m%dT%H%M%SZ")
    artifact_root = Path(args.artifact_root or "/freqtrade/user_data/artifacts").resolve()
    artifact_dir = artifact_root / "regime_bands" / artifact_run_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / "neutral_bands.json"

    feature_entries = [
        {
            "pair": args.pair,
            "horizon": "15m",
            "features": {
                "er_15m": er_stats,
                "chop_15m": chop_stats,
                "atr_pct_15m": atr_stats,
            },
            "enter_score": score_enter,
            "exit_score": score_exit,
            "persistence_bars": int(args.score_persistence_bars),
        },
        {
            "pair": args.pair,
            "horizon": "4h",
            "features": {
                "adx_4h": adx_stats,
            },
            "enter_score": score_enter,
            "exit_score": score_exit,
            "persistence_bars": int(args.score_persistence_bars),
        },
    ]

    verbose = add_verbose_states(valid, prefixes=["intraday", "swing"])

    persistence_recs: Dict[str, Dict[str, Optional[int]]] = {}
    for prefix in ("intraday", "swing"):
        persistence_recs[prefix] = {
            "non_trend_range_bars": median_state_run_length(verbose, prefix, "non_trend_range"),
            "neutral_choppy_bars": median_state_run_length(verbose, prefix, "neutral_choppy"),
        }

    # Open decision defaults (entry/exit/veto percentiles) for the new neutral/choppy gating.
    hysteresis_bands = {
        "intraday": {
            "adx": {
                "enter_pct": 55,
                "enter_value": qval(window["adx_1h"], 0.55, intraday_defaults["adx_enter_max"]),
                "exit_pct": 65,
                "exit_value": qval(window["adx_1h"], 0.65, intraday_defaults["adx_exit_max"]),
                "veto_pct": 70,
                "veto_value": qval(window["adx_1h"], 0.70, intraday_defaults["adx_exit_max"]),
            },
            "bbwp": {
                "entry_min_pct": 20,
                "entry_min_value": qval(window["bbwp_15m_pct"], 0.20, 30.0),
                "exit_max_pct": 60,
                "exit_max_value": qval(window["bbwp_15m_pct"], 0.60, 60.0),
                "veto_pct": 85,
                "veto_value": qval(window["bbwp_15m_pct"], 0.85, 85.0),
                "dead_vol_pct": 10,
                "dead_vol_value": qval(window["bbwp_15m_pct"], 0.10, 10.0),
                "dead_vol_atr_pct": 15.0,
            },
            "atr_pct": {
                "non_dead_pct": 15,
                "non_dead_value": qval(window["atr_pct_15m"], 0.15, 0.0015),
            },
        },
        "swing": {
            "adx": {
                "enter_pct": 55,
                "enter_value": qval(window["adx_4h"], 0.55, swing_defaults["adx_enter_max"]),
                "exit_pct": 65,
                "exit_value": qval(window["adx_4h"], 0.65, swing_defaults["adx_exit_max"]),
                "veto_pct": 70,
                "veto_value": qval(window["adx_4h"], 0.70, swing_defaults["adx_exit_max"]),
            },
            "bbwp": {
                "entry_min_pct": 20,
                "entry_min_value": qval(window["bbwp_15m_pct"], 0.20, 30.0),
                "exit_max_pct": 60,
                "exit_max_value": qval(window["bbwp_15m_pct"], 0.60, 60.0),
                "veto_pct": 85,
                "veto_value": qval(window["bbwp_15m_pct"], 0.85, 85.0),
                "dead_vol_pct": 10,
                "dead_vol_value": qval(window["bbwp_15m_pct"], 0.10, 10.0),
                "dead_vol_atr_pct": 15.0,
            },
            "atr_pct": {
                "non_dead_pct": 15,
                "non_dead_value": qval(window["atr_pct_15m"], 0.15, 0.0015),
            },
        },
    }

    verbose = add_verbose_states(valid, prefixes=["intraday", "swing"])

    intraday_defaults = {
        "adx_enter_max": 22.0,
        "adx_exit_max": 26.0,
        "bbw_1h_pct_max": 55.0,
        "ema_dist_max_frac": 0.010,
        "vol_spike_mult": 2.5,
        "bbwp_s_max": 45.0,
        "bbwp_m_max": 60.0,
        "bbwp_l_max": 70.0,
        "os_dev_rvol_max": 1.4,
        "os_dev_persist_bars": 24,
    }
    swing_defaults = {
        "adx_enter_max": 26.0,
        "adx_exit_max": 30.0,
        "bbw_1h_pct_max": 70.0,
        "ema_dist_max_frac": 0.015,
        "vol_spike_mult": 3.5,
        "bbwp_s_max": 60.0,
        "bbwp_m_max": 75.0,
        "bbwp_l_max": 85.0,
        "os_dev_rvol_max": 1.8,
        "os_dev_persist_bars": 12,
    }

    intraday_range_mask = valid["intraday_range_label"] == 1
    intraday_trend_mask = valid["intraday_trend_label"] == 1
    swing_range_mask = valid["swing_range_label"] == 1
    swing_trend_mask = valid["swing_trend_label"] == 1
    intraday_events = extract_transition_events(verbose, "intraday", feature_cols)
    swing_events = extract_transition_events(verbose, "swing", feature_cols)
    all_events = sorted(
        [*intraday_events, *swing_events],
        key=lambda x: pd.Timestamp(x["date"]).value if x.get("date") is not None else 0,
    )

    report = {
        "meta": {
            "pair": args.pair,
            "timeframe": args.timeframe,
            "data_dir": args.data_dir,
            "source_path": ohlcv_path,
            "timerange": args.timerange,
            "rows_raw": int(len(df)),
            "rows_valid_features": int(len(valid)),
            "start_utc": str(df["date"].min()),
            "end_utc": str(df["date"].max()),
        },
        "label_config": {
            "intraday": {
                "horizon_bars": 16,
                "range_ret_max": 0.008,
                "range_span_min": 0.006,
                "range_span_max": 0.045,
                "range_eff_max": 0.40,
                "trend_ret_min": 0.015,
                "trend_eff_min": 0.60,
            },
            "swing": {
                "horizon_bars": 96,
                "range_ret_max": 0.015,
                "range_span_min": 0.010,
                "range_span_max": 0.080,
                "range_eff_max": 0.45,
                "trend_ret_min": 0.030,
                "trend_eff_min": 0.65,
            },
        },
        "labels": {
            "intraday": label_counts(valid, "intraday"),
            "swing": label_counts(valid, "swing"),
        },
        "state_counts": {
            "intraday": {
                "range": int((verbose["intraday_state"] == "range").sum()),
                "trend": int((verbose["intraday_state"] == "trend").sum()),
                "neutral": int((verbose["intraday_state"] == "neutral").sum()),
                "non_trend_range": int((verbose["intraday_state"] == "non_trend_range").sum()),
                "neutral_choppy": int((verbose["intraday_state"] == "neutral_choppy").sum()),
                "unlabeled": int((verbose["intraday_state"] == "unlabeled").sum()),
            },
            "swing": {
                "range": int((verbose["swing_state"] == "range").sum()),
                "trend": int((verbose["swing_state"] == "trend").sum()),
                "neutral": int((verbose["swing_state"] == "neutral").sum()),
                "non_trend_range": int((verbose["swing_state"] == "non_trend_range").sum()),
                "neutral_choppy": int((verbose["swing_state"] == "neutral_choppy").sum()),
                "unlabeled": int((verbose["swing_state"] == "unlabeled").sum()),
            },
        },
        "hysteresis_bands": hysteresis_bands,
        "persistence_recommendations": persistence_recs,
        "transition_counts": {
            "intraday": transition_counts(intraday_events),
            "swing": transition_counts(swing_events),
            "total_events": int(len(all_events)),
        },
        "feature_quantiles": {
            "intraday_range": feature_quantiles(valid, intraday_range_mask, feature_cols),
            "intraday_trend": feature_quantiles(valid, intraday_trend_mask, feature_cols),
            "swing_range": feature_quantiles(valid, swing_range_mask, feature_cols),
            "swing_trend": feature_quantiles(valid, swing_trend_mask, feature_cols),
        },
        "recommended_thresholds": {
            "intraday": recommend_mode_thresholds(valid, "intraday", intraday_defaults),
            "swing": recommend_mode_thresholds(valid, "swing", swing_defaults),
        },
        "regime_bands": {
            "artifact_path": str(artifact_path),
            "artifact_run_id": artifact_run_id,
            "cal_window_days": float(args.cal_window_days),
            "cal_window_bars": int(cal_window_bars),
            "enter_score": float(score_enter),
            "exit_score": float(score_exit),
            "persistence_bars": int(args.score_persistence_bars),
        },
        "chop_score": {
            "p10": score_stats.get("p10"),
            "p50": score_stats.get("p50"),
            "p90": score_stats.get("p90"),
            "enter_quantile": float(args.score_enter_quantile),
            "exit_quantile": float(args.score_exit_quantile),
        },
    }

    artifact_payload: Dict[str, Any] = {
        "meta": {
            "pair": args.pair,
            "timeframe": args.timeframe,
            "run_id": artifact_run_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "cal_window_days": float(args.cal_window_days),
            "cal_window_bars": int(cal_window_bars),
            "feature_horizons": FEATURE_HORIZON_MAP,
        },
        "entries": feature_entries,
        "hysteresis_bands": hysteresis_bands,
        "persistence_recommendations": persistence_recs,
    }
    with artifact_path.open("w", encoding="utf-8") as f:
        json.dump(artifact_payload, f, indent=2, sort_keys=True)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)

    if args.emit_features_csv:
        keep = [
            "date",
            "close",
            "adx_4h",
            "adx_1h",
            "adx_pct_4h",
            "adx_pct_1h",
            "ema_dist_frac_1h",
            "bb_width_1h_pct",
            "bbwp_15m_pct",
            "bbwp_1h_pct",
            "bbwp_4h_pct",
            "vol_ratio_1h",
            "rvol_15m",
            "containment_pct",
            "volatility_allowed",
            "volatility_veto",
            "dead_vol_veto",
            "volatility_ready",
            "er_15m",
            "er_pct_15m",
            "chop_15m",
            "chop_pct_15m",
            "atr_pct_15m",
            "intraday_range_label",
            "intraday_trend_label",
            "intraday_non_trend_range_label",
            "intraday_neutral_choppy_label",
            "intraday_fwd_abs_ret",
            "intraday_fwd_span",
            "intraday_fwd_eff",
            "intraday_state",
            "intraday_transition",
            "swing_range_label",
            "swing_trend_label",
            "swing_non_trend_range_label",
            "swing_neutral_choppy_label",
            "swing_fwd_abs_ret",
            "swing_fwd_span",
            "swing_fwd_eff",
            "swing_state",
            "swing_transition",
            "chop_score",
        ]
        os.makedirs(os.path.dirname(args.emit_features_csv), exist_ok=True)
        verbose[keep].to_csv(args.emit_features_csv, index=False)

    if args.emit_verbose_csv:
        os.makedirs(os.path.dirname(args.emit_verbose_csv), exist_ok=True)
        verbose.to_csv(args.emit_verbose_csv, index=False)

    if args.emit_transitions_csv:
        os.makedirs(os.path.dirname(args.emit_transitions_csv), exist_ok=True)
        pd.DataFrame(all_events).to_csv(args.emit_transitions_csv, index=False)

    if args.emit_transitions_json:
        os.makedirs(os.path.dirname(args.emit_transitions_json), exist_ok=True)
        payload: List[Dict[str, object]] = []
        for ev in all_events:
            item = dict(ev)
            if isinstance(item.get("date"), pd.Timestamp):
                item["date"] = item["date"].isoformat()
            payload.append(item)
        with open(args.emit_transitions_json, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)

    print(f"Wrote regime audit report: {args.out}", flush=True)
    if args.emit_features_csv:
        print(f"Wrote feature dump: {args.emit_features_csv}", flush=True)
    if args.emit_verbose_csv:
        print(f"Wrote verbose per-candle dump: {args.emit_verbose_csv}", flush=True)
    if args.emit_transitions_csv:
        print(f"Wrote transition events csv: {args.emit_transitions_csv}", flush=True)
    if args.emit_transitions_json:
        print(f"Wrote transition events json: {args.emit_transitions_json}", flush=True)
        print("Recommended thresholds:", json.dumps(report["recommended_thresholds"], indent=2), flush=True)
    print(f"Wrote regime bands artifact: {artifact_path}", flush=True)


if __name__ == "__main__":
    main()
