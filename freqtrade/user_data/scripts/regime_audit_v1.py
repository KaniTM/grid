#!/usr/bin/env python3
"""
Long-history feature/label audit for regime calibration.

Outputs:
- Feature distributions by inferred range/trend labels.
- Recommended intraday/swing gate thresholds.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Dict, List, Optional

import numpy as np
import pandas as pd


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
    df["rvol_15m"] = df["volume"] / df["volume"].rolling(20, min_periods=20).mean()
    df["bb_width_15m"] = bb_width(df["close"], window=20, stds=2.0)
    df["bbwp_15m_pct"] = rolling_percentile_last(df["bb_width_15m"], bbwp_lookback)

    df_1h = resample_ohlcv(df_15m, "1h")
    df_1h["ema50_1h"] = df_1h["close"].ewm(span=50, adjust=False).mean()
    df_1h["ema100_1h"] = df_1h["close"].ewm(span=100, adjust=False).mean()
    df_1h["ema_dist_frac_1h"] = (df_1h["ema50_1h"] - df_1h["ema100_1h"]).abs() / df_1h["close"].replace(0.0, np.nan)
    df_1h["vol_ratio_1h"] = df_1h["volume"] / df_1h["volume"].rolling(20, min_periods=20).mean()
    df_1h["bb_width_1h"] = bb_width(df_1h["close"], window=20, stds=2.0)
    df_1h["bbwp_1h_pct"] = rolling_percentile_last(df_1h["bb_width_1h"], bbwp_lookback)

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
    return {
        "rows_total": int(len(df)),
        "range_label": int((df[f"{prefix}_range_label"] == 1).sum()),
        "trend_label": int((df[f"{prefix}_trend_label"] == 1).sum()),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", required=True, help="e.g. ETH/USDT")
    ap.add_argument("--timeframe", default="15m", help="base timeframe file to load (usually 15m)")
    ap.add_argument("--data-dir", default="/freqtrade/user_data/data/binance", help="OHLCV directory")
    ap.add_argument("--timerange", default=None, help="YYYYMMDD-YYYYMMDD (optional)")
    ap.add_argument("--bbwp-lookback", type=int, default=252)
    ap.add_argument("--out", required=True, help="output json path")
    ap.add_argument("--emit-features-csv", default=None, help="optional feature dump csv path")
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
        "ema_dist_frac_1h",
        "bb_width_1h_pct",
        "bbwp_15m_pct",
        "bbwp_1h_pct",
        "bbwp_4h_pct",
        "vol_ratio_1h",
        "rvol_15m",
    ]
    valid = feat.dropna(subset=feature_cols).copy()
    if len(valid) == 0:
        raise ValueError("No valid rows after feature construction.")

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
    }

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)

    if args.emit_features_csv:
        keep = [
            "date",
            "close",
            "adx_4h",
            "ema_dist_frac_1h",
            "bb_width_1h_pct",
            "bbwp_15m_pct",
            "bbwp_1h_pct",
            "bbwp_4h_pct",
            "vol_ratio_1h",
            "rvol_15m",
            "intraday_range_label",
            "intraday_trend_label",
            "swing_range_label",
            "swing_trend_label",
        ]
        os.makedirs(os.path.dirname(args.emit_features_csv), exist_ok=True)
        valid[keep].to_csv(args.emit_features_csv, index=False)

    print(f"Wrote regime audit report: {args.out}", flush=True)
    if args.emit_features_csv:
        print(f"Wrote feature dump: {args.emit_features_csv}", flush=True)
    print("Recommended thresholds:", json.dumps(report["recommended_thresholds"], indent=2), flush=True)


if __name__ == "__main__":
    main()

