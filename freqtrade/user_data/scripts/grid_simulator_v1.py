import argparse
import json
import os
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Deque, List, Dict, Optional, Tuple

import numpy as np
import pandas as pd
from sim.chaos_profiles import load_chaos_profile, validate_chaos_profile

SOURCE_PATH = Path(__file__).resolve()
MODULE_NAME = "grid_simulator_v1"


def log_event(level: str, message: str, plan: Optional[Dict] = None, **meta: object) -> None:
    payload: Dict[str, object] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": str(level).upper(),
        "module": MODULE_NAME,
        "source_path": str(SOURCE_PATH),
        "message": message,
    }
    if plan is not None:
        payload["plan_context"] = _plan_context(plan)
    payload.update(meta)
    print(json.dumps(payload, sort_keys=True))


def _log_plan_marker(
    label: str, plan: Optional[Dict], level: str = "debug", **meta: object
) -> None:
    log_event(level, label, plan=plan, **meta)


# -----------------------------
# Plan helpers
# -----------------------------
def _plan_context(plan: Optional[Dict]) -> Dict[str, object]:
    if not plan:
        return {}
    out: Dict[str, object] = {}
    path = plan.get("_plan_path") or plan.get("plan_path") or plan.get("path")
    if path:
        out["plan_path"] = str(path)
    ts = plan.get("ts") or plan.get("candle_time_utc")
    if ts:
        out["plan_ts"] = str(ts)
    try:
        out["plan_keys"] = sorted(plan.keys())
    except Exception:
        pass
    return out


# -----------------------------
# Helpers: load OHLCV from freqtrade data directory
# -----------------------------
def find_ohlcv_file(data_dir: str, pair: str, timeframe: str) -> str:
    """
    Locate OHLCV file for pair/timeframe under user_data/data/<exchange>/...
    Supports: .feather, .parquet, .json, .json.gz, .csv, .csv.gz
    """
    pair_fs = pair.replace("/", "_").replace(":", "_")
    candidates = []
    for root, _, files in os.walk(data_dir):
        for fn in files:
            low = fn.lower()
            if pair_fs.lower() in low and f"-{timeframe}".lower() in low:
                candidates.append(os.path.join(root, fn))
    if not candidates:
        log_event(
            "error",
            "missing_ohlcv",
            data_dir=data_dir,
            pair=pair,
            timeframe=timeframe,
        )
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
        log_event("error", "unsupported_ohlcv_format", path=path)
        raise ValueError(f"Unsupported file format: {path}")

    # Normalize column names
    cols = {c.lower(): c for c in df.columns}
    date_col = cols.get("date") or cols.get("timestamp") or cols.get("datetime")
    if not date_col:
        log_event("error", "missing_date_column", path=path, columns=df.columns.tolist())
        raise ValueError(f"Could not find date/timestamp column in {path}. Columns: {df.columns.tolist()}")

    df = df.rename(columns={date_col: "date"})
    for c in ["open", "high", "low", "close", "volume"]:
        # case-insensitive rename
        if c not in df.columns:
            real = cols.get(c)
            if real:
                df = df.rename(columns={real: c})
        else:
            # ensure exact
            for real in list(df.columns):
                if real.lower() == c and real != c:
                    df = df.rename(columns={real: c})

    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    df = df[["date", "open", "high", "low", "close", "volume"]].copy()
    return df


def filter_timerange(df: pd.DataFrame, timerange: Optional[str]) -> pd.DataFrame:
    """
    timerange like: 20260101-20260201 (inclusive start, exclusive end)
    """
    if not timerange:
        return df
    if "-" not in timerange:
        log_event("error", "invalid_timerange", value=timerange)
        raise ValueError("timerange must look like YYYYMMDD-YYYYMMDD")
    a, b = timerange.split("-", 1)
    start = pd.to_datetime(a, format="%Y%m%d", utc=True)
    end = pd.to_datetime(b, format="%Y%m%d", utc=True)
    return df[(df["date"] >= start) & (df["date"] < end)].reset_index(drop=True)


def parse_start_at(start_at: Optional[str], plan: Dict) -> Optional[pd.Timestamp]:
    """
    start_at:
      - None -> no filtering
      - "plan" -> use plan["candle_time_utc"] (preferred) or plan["candle_ts"]
      - "YYYYMMDD" or "YYYYMMDDHHMM"
      - ISO timestamp (e.g. 2026-02-09T17:21:00Z)
    """
    if not start_at:
        return None

    s = start_at.strip().lower()
    if s == "plan":
        for key in ("candle_time_utc", "candle_ts", "ts"):
            value = plan.get(key)
            if value is None:
                continue
            try:
                resolved = pd.to_datetime(value, utc=True)
                _log_plan_marker(
                    "parse_start_at_plan",
                    plan,
                    level="debug",
                    requested="plan",
                    resolved=str(resolved),
                    plan_key=key,
                )
                return resolved
            except Exception:
                continue
        _log_plan_marker(
            "parse_start_at_plan",
            plan,
            level="warning",
            requested="plan",
            resolved=None,
        )
        return None

    # numeric formats
    if s.isdigit():
        if len(s) == 8:
            resolved = pd.to_datetime(s, format="%Y%m%d", utc=True)
            _log_plan_marker(
                "parse_start_at_numeric",
                plan,
                level="debug",
                requested=start_at,
                resolved=str(resolved),
                format="YYYYMMDD",
            )
            return resolved
        if len(s) == 12:
            resolved = pd.to_datetime(s, format="%Y%m%d%H%M", utc=True)
            _log_plan_marker(
                "parse_start_at_numeric",
                plan,
                level="debug",
                requested=start_at,
                resolved=str(resolved),
                format="YYYYMMDDHHMM",
            )
            return resolved

    # ISO-ish
    try:
        resolved = pd.to_datetime(start_at, utc=True)
        _log_plan_marker(
            "parse_start_at_iso",
            plan,
            level="debug",
            requested=start_at,
            resolved=str(resolved),
        )
        return resolved
    except Exception:
        _log_plan_marker(
            "parse_start_at_error",
            plan,
            level="error",
            requested=start_at,
        )
        raise ValueError("Unsupported --start-at. Use 'plan', YYYYMMDD, YYYYMMDDHHMM, or ISO timestamp.")


# -----------------------------
# Grid Simulator
# -----------------------------
@dataclass
class OrderSim:
    side: str          # "buy" or "sell"
    price: float
    qty_base: float
    level_index: int   # rung index
    status: str = "open"


@dataclass
class FillSim:
    ts_utc: str
    side: str
    price: float
    qty_base: float
    fee_quote: float
    reason: str


def _round_to_tick(price: float, tick_size: Optional[float]) -> float:
    if tick_size is None or tick_size <= 0:
        return float(price)
    return float(np.round(float(price) / float(tick_size)) * float(tick_size))


def build_levels(
    box_low: float,
    box_high: float,
    n_levels: int,
    tick_size: Optional[float] = None,
) -> np.ndarray:
    if n_levels <= 0:
        return np.array([])
    levels = np.linspace(box_low, box_high, n_levels + 1)
    if tick_size is not None and tick_size > 0:
        levels = np.array([_round_to_tick(float(px), tick_size) for px in levels], dtype=float)
        levels = np.sort(levels)
        # Keep deterministic level count after rounding.
        if len(levels) != (n_levels + 1):
            levels = np.linspace(float(levels[0]), float(levels[-1]), n_levels + 1)
            levels = np.array([_round_to_tick(float(px), tick_size) for px in levels], dtype=float)
    return levels


def _normalize_fill_mode(touch_fill: bool, mode_hint: Optional[str]) -> str:
    mode = str(mode_hint or "").strip().lower()
    if mode == "touch":
        return "Touch"
    if mode == "reverse":
        return "Reverse"
    return "Touch" if bool(touch_fill) else "Reverse"


def _fill_trigger(side: str, o: float, h: float, l: float, c: float, price: float, mode: str) -> bool:
    m = str(mode or "Touch")
    if m == "Reverse":
        if side == "buy":
            return bool(o > price and c < price)
        return bool(o < price and c > price)
    if side == "buy":
        return bool(l <= price)
    return bool(h >= price)


def _touched_index_bounds(
    levels: np.ndarray,
    *,
    side: str,
    o: float,
    h: float,
    l: float,
    c: float,
    mode: str,
) -> Optional[Tuple[int, int]]:
    if len(levels) == 0:
        return None
    m = str(mode or "Touch")
    if m == "Reverse":
        if side == "buy":
            if not (o > c):
                return None
            lo, hi = c, o
        else:
            if not (o < c):
                return None
            lo, hi = o, c
        left = int(np.searchsorted(levels, lo, side="right"))
        right = int(np.searchsorted(levels, hi, side="left")) - 1
    else:
        if side == "buy":
            left = int(np.searchsorted(levels, l, side="left"))
            right = len(levels) - 1
        else:
            left = 0
            right = int(np.searchsorted(levels, h, side="right")) - 1
    if right < left:
        return None
    left = max(left, 0)
    right = min(right, len(levels) - 1)
    if right < left:
        return None
    return left, right


class FillCooldownGuard:
    def __init__(self, cooldown_bars: int, no_repeat_lsi_guard: bool = True) -> None:
        self.cooldown_bars = max(int(cooldown_bars), 0)
        self.no_repeat_lsi_guard = bool(no_repeat_lsi_guard)
        self._last_fill_by_key: Dict[Tuple[str, int], int] = {}

    def configure(
        self,
        *,
        cooldown_bars: Optional[int] = None,
        no_repeat_lsi_guard: Optional[bool] = None,
    ) -> None:
        if cooldown_bars is not None:
            self.cooldown_bars = max(int(cooldown_bars), 0)
        if no_repeat_lsi_guard is not None:
            self.no_repeat_lsi_guard = bool(no_repeat_lsi_guard)

    def allow(self, side: str, level_index: int, bar_index: int) -> bool:
        if not self.no_repeat_lsi_guard:
            return True
        last = self._last_fill_by_key.get((str(side), int(level_index)))
        if last is None:
            return True
        return bool((int(bar_index) - int(last)) > self.cooldown_bars)

    def mark(self, side: str, level_index: int, bar_index: int) -> None:
        if not self.no_repeat_lsi_guard:
            return
        self._last_fill_by_key[(str(side), int(level_index))] = int(bar_index)


def _safe_float(x, default=None):
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _safe_int(x, default=None):
    try:
        if x is None:
            return default
        return int(x)
    except Exception:
        return default


def _clamp_probability(x: object, default: float = 0.0) -> float:
    value = _safe_float(x, default=default)
    if value is None:
        return float(default)
    return float(min(max(value, 0.0), 1.0))


@dataclass
class ChaosRuntimeConfig:
    profile_id: str
    name: str
    enabled: bool
    seed: int
    latency_mean_ms: float
    latency_jitter_ms: float
    latency_fill_window_ms: float
    spread_base_bps: float
    spread_burst_bps: float
    spread_burst_probability: float
    partial_fill_probability: float
    partial_fill_min_ratio: float
    partial_fill_max_ratio: float
    reject_burst_probability: float
    reject_burst_min_bars: int
    reject_burst_max_bars: int
    delayed_candle_probability: float
    missing_candle_probability: float
    data_gap_probability: float


def _build_chaos_runtime_config(profile: Optional[Dict]) -> Optional[ChaosRuntimeConfig]:
    if not profile:
        return None
    payload = dict(profile)
    errors = validate_chaos_profile(payload)
    if errors:
        raise ValueError(f"Invalid chaos profile: {errors[0]}")

    enabled = bool(payload.get("enabled", True))
    if not enabled:
        return None

    latency_cfg = payload.get("latency_ms", {}) or {}
    latency_mean = _safe_float(latency_cfg.get("mean"), default=None)
    if latency_mean is None:
        latency_mean = _safe_float(latency_cfg.get("p50"), default=0.0)
    latency_p95 = _safe_float(latency_cfg.get("p95"), default=None)
    latency_jitter = _safe_float(latency_cfg.get("jitter"), default=None)
    if latency_jitter is None:
        if latency_p95 is None or latency_mean is None:
            latency_jitter = 0.0
        else:
            latency_jitter = max(float(latency_p95) - float(latency_mean), 0.0)
    latency_fill_window_ms = _safe_float(latency_cfg.get("fill_window_ms"), default=500.0)
    if latency_fill_window_ms is None or latency_fill_window_ms <= 0:
        latency_fill_window_ms = 500.0

    spread_cfg = payload.get("spread_shock_bps", {}) or {}
    spread_base_bps = _safe_float(
        spread_cfg.get("base"),
        default=_safe_float(spread_cfg.get("base_p50"), default=0.0),
    )
    spread_burst_bps = _safe_float(
        spread_cfg.get("burst"),
        default=_safe_float(spread_cfg.get("burst_p95"), default=0.0),
    )
    spread_burst_probability = _clamp_probability(spread_cfg.get("burst_probability"), default=0.0)

    partial_fill_min_ratio = _safe_float(payload.get("partial_fill_min_ratio"), default=0.3)
    partial_fill_max_ratio = _safe_float(payload.get("partial_fill_max_ratio"), default=0.8)
    if partial_fill_min_ratio is None:
        partial_fill_min_ratio = 0.3
    if partial_fill_max_ratio is None:
        partial_fill_max_ratio = 0.8
    partial_fill_min_ratio = float(min(max(partial_fill_min_ratio, 0.0), 1.0))
    partial_fill_max_ratio = float(min(max(partial_fill_max_ratio, 0.0), 1.0))
    if partial_fill_max_ratio < partial_fill_min_ratio:
        partial_fill_max_ratio = partial_fill_min_ratio

    reject_burst_cfg = payload.get("reject_burst_bars", {}) or {}
    reject_burst_min_bars = _safe_int(reject_burst_cfg.get("min"), default=1) or 1
    reject_burst_max_bars = _safe_int(reject_burst_cfg.get("max"), default=3) or 3
    reject_burst_min_bars = max(int(reject_burst_min_bars), 1)
    reject_burst_max_bars = max(int(reject_burst_max_bars), reject_burst_min_bars)

    return ChaosRuntimeConfig(
        profile_id=str(payload.get("profile_id") or "chaos-profile"),
        name=str(payload.get("name") or "chaos"),
        enabled=True,
        seed=_safe_int(payload.get("seed"), default=42) or 42,
        latency_mean_ms=float(max(latency_mean or 0.0, 0.0)),
        latency_jitter_ms=float(max(latency_jitter or 0.0, 0.0)),
        latency_fill_window_ms=float(latency_fill_window_ms),
        spread_base_bps=float(max(spread_base_bps or 0.0, 0.0)),
        spread_burst_bps=float(max(spread_burst_bps or 0.0, 0.0)),
        spread_burst_probability=spread_burst_probability,
        partial_fill_probability=_clamp_probability(payload.get("partial_fill_probability"), default=0.0),
        partial_fill_min_ratio=partial_fill_min_ratio,
        partial_fill_max_ratio=partial_fill_max_ratio,
        reject_burst_probability=_clamp_probability(payload.get("reject_burst_probability"), default=0.0),
        reject_burst_min_bars=reject_burst_min_bars,
        reject_burst_max_bars=reject_burst_max_bars,
        delayed_candle_probability=_clamp_probability(payload.get("delayed_candle_probability"), default=0.0),
        missing_candle_probability=_clamp_probability(payload.get("missing_candle_probability"), default=0.0),
        data_gap_probability=_clamp_probability(payload.get("data_gap_probability"), default=0.0),
    )


def _uniform_int_inclusive(rng: np.random.Generator, low: int, high: int) -> int:
    if high <= low:
        return int(low)
    return int(rng.integers(low, high + 1))


def extract_rung_weights(plan: Dict, n_levels: int) -> Optional[List[float]]:
    try:
        g = plan.get("grid", {}) or {}
        rb = g.get("rung_density_bias", {}) or {}
        ws = rb.get("weights_by_level_index")
        if ws is None:
            log_event(
                "warning",
                "missing_rung_weights",
                plan_ts=str(plan.get("ts") or plan.get("candle_time_utc") or ""),
                n_levels=n_levels,
            )
            return None
        vals = [max(float(x), 0.0) for x in ws]
        if len(vals) != n_levels + 1:
            log_event(
                "warning",
                "rung_weight_length_mismatch",
                plan_ts=str(plan.get("ts") or plan.get("candle_time_utc") or ""),
                expected=n_levels + 1,
                actual=len(vals),
            )
            return None
        if not any(v > 0 for v in vals):
            log_event(
                "warning",
                "rung_weights_all_zero",
                plan_ts=str(plan.get("ts") or plan.get("candle_time_utc") or ""),
                n_levels=n_levels,
                **_plan_context(plan),
            )
            return None
        return vals
    except Exception as exc:
        log_event(
            "error",
            "rung_weight_parse_failed",
            plan_ts=str(plan.get("ts") or plan.get("candle_time_utc") or ""),
            error=str(exc),
            **_plan_context(plan),
        )
        return None


def normalized_side_weights(indices: List[int], rung_weights: Optional[List[float]]) -> List[float]:
    if not indices:
        return []
    if rung_weights is None:
        return [1.0 / len(indices)] * len(indices)
    vals = [max(float(rung_weights[i]), 0.0) if 0 <= i < len(rung_weights) else 0.0 for i in indices]
    s = float(sum(vals))
    if s <= 0:
        log_event(
            "warning",
            "normalized_weights_zero_sum",
            indices=indices,
            rung_weights=list(rung_weights or []),
        )
        return [1.0 / len(indices)] * len(indices)
    return [float(v / s) for v in vals]


def plan_signature(plan: Dict) -> Tuple:
    try:
        r = plan["range"]
        g = plan["grid"]
        return (
            round(float(r["low"]), 12),
            round(float(r["high"]), 12),
            int(g["n_levels"]),
            round(float(g["step_price"]), 12),
        )
    except Exception as exc:
        log_event(
            "error",
            "plan_signature_failed",
            error=str(exc),
            **_plan_context(plan),
        )
        raise


def soft_adjust_ok(prev_plan: Dict, new_plan: Dict) -> bool:
    try:
        prev_low = float(prev_plan["range"]["low"])
        prev_high = float(prev_plan["range"]["high"])
        new_low = float(new_plan["range"]["low"])
        new_high = float(new_plan["range"]["high"])
        step = float(new_plan["grid"]["step_price"])
        frac = float(new_plan.get("update_policy", {}).get("soft_adjust_max_step_frac", 0.5))
        tol = frac * step
        return abs(new_low - prev_low) <= tol and abs(new_high - prev_high) <= tol
    except Exception as exc:
        prev_ctx = _plan_context(prev_plan)
        new_ctx = _plan_context(new_plan)
        log_event(
            "warning",
            "soft_adjust_exception",
            error=str(exc),
            prev_plan_path=prev_ctx.get("plan_path"),
            plan_path=new_ctx.get("plan_path"),
        )
        return False


def action_signature(action: str, sig: Tuple, stop_reason: Optional[str] = None) -> Tuple:
    a = str(action or "HOLD").upper()
    if a == "STOP":
        return (a, sig, str(stop_reason or "PLAN_STOP"))
    return (a, sig)


def extract_exit_levels(plan: Dict) -> Tuple[Optional[float], Optional[float]]:
    tp = None
    sl = None
    try:
        ex = plan.get("exit", {}) or {}
        tp = _safe_float(ex.get("tp_price"), default=None)
        sl = _safe_float(ex.get("sl_price"), default=None)
    except Exception as exc:
        tp = None
        sl = None
        log_event(
            "warning",
            "extract_exit_levels_failed",
            error=str(exc),
            **_plan_context(plan),
        )

    if tp is None or sl is None:
        try:
            rk = plan.get("risk", {}) or {}
            if tp is None:
                tp = _safe_float(rk.get("tp_price"), default=None)
            if sl is None:
                sl = _safe_float(rk.get("sl_price"), default=None)
        except Exception:
            pass

    return tp, sl


def plan_effective_time(plan: Dict) -> Optional[pd.Timestamp]:
    ct = plan.get("candle_time_utc")
    if ct:
        try:
            return pd.to_datetime(ct, utc=True)
        except Exception:
            pass

    cts = plan.get("candle_ts")
    if cts is not None:
        try:
            return pd.to_datetime(int(cts), unit="s", utc=True)
        except Exception:
            pass

    pts = plan.get("ts")
    if pts:
        try:
            return pd.to_datetime(pts, utc=True)
        except Exception:
            pass

    return None


def load_plan_sequence(plan_path: str, plans_dir: Optional[str] = None) -> List[Dict]:
    """
    Load and sort archived plan snapshots for replay.
    Includes the provided plan file and all grid_plan.*.json files in the same directory.
    """
    base_dir = plans_dir or os.path.dirname(plan_path)
    if not base_dir:
        base_dir = "."

    paths = {plan_path}
    try:
        for fn in os.listdir(base_dir):
            if not fn.startswith("grid_plan.") or not fn.endswith(".json"):
                continue
            paths.add(os.path.join(base_dir, fn))
    except Exception:
        pass

    loaded: List[Tuple[pd.Timestamp, float, str, Dict]] = []
    for p in sorted(paths):
        if not os.path.isfile(p):
            continue
        try:
            with open(p, "r", encoding="utf-8") as f:
                plan = json.load(f)
        except Exception:
            continue
        if "range" not in plan or "grid" not in plan:
            log_event(
                "warning",
                "plan_missing_range_or_grid",
                plan_path=str(p),
            )
            continue
        pt = plan_effective_time(plan)
        if pt is None:
            continue
        try:
            mt = float(os.path.getmtime(p))
        except Exception:
            mt = 0.0
        loaded.append((pt, mt, p, plan))

    if not loaded:
        raise FileNotFoundError(f"No valid plan snapshots found near: {plan_path}")

    # Sort by effective time, then mtime/path; keep last snapshot per timestamp.
    loaded.sort(key=lambda x: (x[0], x[1], x[2]))
    dedup: Dict[int, Tuple[pd.Timestamp, float, str, Dict]] = {}
    for item in loaded:
        ts_key = int(item[0].value)
        dedup[ts_key] = item

    out: List[Dict] = []
    for ts_key in sorted(dedup.keys()):
        pt, mt, p, plan = dedup[ts_key]
        cp = dict(plan)
        cp["_plan_time"] = pt
        cp["_plan_path"] = p
        out.append(cp)
    return out


def _uniq_reasons(vals: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for v in vals:
        k = str(v).strip()
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(k)
    return out


def _increment_reason(counter: Dict[str, int], reason: Optional[str], inc: int = 1) -> None:
    if reason is None:
        return
    key = str(reason).strip()
    if not key:
        return
    counter[key] = int(counter.get(key, 0)) + int(max(inc, 0))


def _increment_reasons(counter: Dict[str, int], reasons: List[str]) -> None:
    for r in reasons:
        _increment_reason(counter, r, 1)


def _sorted_reason_counts(counter: Dict[str, int]) -> Dict[str, int]:
    return {k: int(v) for k, v in sorted(counter.items(), key=lambda kv: (-int(kv[1]), str(kv[0])))}


def _normalize_router_mode(value: object, default: str = "unknown") -> str:
    mode = str(value or "").strip().lower()
    if mode in ("intraday", "swing", "pause", "neutral_choppy"):
        return mode
    return str(default or "unknown")


def extract_start_block_reasons(plan: Dict) -> List[str]:
    diag = plan.get("diagnostics", {}) or {}
    runtime = plan.get("runtime_state", {}) or {}
    signals = plan.get("signals", {}) or {}

    reasons: List[str] = []
    for src in (diag.get("start_block_reasons"), runtime.get("start_block_reasons")):
        if isinstance(src, list):
            reasons.extend([str(x) for x in src if str(x).strip()])
    if reasons:
        return _uniq_reasons(reasons)

    rr = signals.get("rule_range_fail_reasons")
    if isinstance(rr, list):
        reasons.extend([f"gate_fail:{x}" for x in rr if str(x).strip()])
    if diag.get("price_in_box") is False:
        reasons.append("price_outside_box")
    if diag.get("rsi_ok") is False:
        reasons.append("rsi_out_of_range")
    if runtime.get("reclaim_active") is True:
        reasons.append("reclaim_active")
    if runtime.get("cooldown_active") is True:
        reasons.append("cooldown_active")
    if diag.get("stop_rule_triggered") is True:
        reasons.append("stop_rule_active")
    if diag.get("stop_rule_triggered_raw") is True and diag.get("stop_rule_triggered") is False:
        reasons.append("stop_rule_suppressed_by_min_runtime")
    return _uniq_reasons(reasons)


def extract_start_counterfactual(
    plan: Dict,
    action: Optional[str] = None,
    start_block_reasons: Optional[List[str]] = None,
) -> Dict[str, object]:
    """
    For HOLD candles, compute the minimal set of blockers that would need to
    clear for START to be possible on that candle.
    """
    diag = plan.get("diagnostics", {}) or {}
    runtime = plan.get("runtime_state", {}) or {}
    signals = plan.get("signals", {}) or {}

    act = str(action if action is not None else plan.get("action", "HOLD")).upper()
    reasons = _uniq_reasons([str(x) for x in (start_block_reasons or extract_start_block_reasons(plan))])

    gate_reasons = [
        r
        for r in reasons
        if r == "gate_ratio_below_required" or r.startswith("gate_fail:") or r.startswith("core_gate_fail:")
    ]

    start_gate_ok_raw = diag.get("start_gate_ok")
    if isinstance(start_gate_ok_raw, bool):
        start_gate_ok = bool(start_gate_ok_raw)
    else:
        start_gate_ok = len(gate_reasons) == 0

    if (not start_gate_ok) and (not gate_reasons):
        rr = signals.get("rule_range_fail_reasons")
        if isinstance(rr, list):
            gate_reasons = [f"gate_fail:{str(x)}" for x in rr if str(x).strip()]
        if not gate_reasons:
            gate_reasons = ["start_gate_not_ok"]

    price_in_box_raw = diag.get("price_in_box")
    price_in_box = bool(price_in_box_raw) if isinstance(price_in_box_raw, bool) else ("price_outside_box" not in reasons)

    rsi_ok_raw = diag.get("rsi_ok")
    rsi_ok = bool(rsi_ok_raw) if isinstance(rsi_ok_raw, bool) else ("rsi_out_of_range" not in reasons)

    start_signal_raw = runtime.get("start_signal", diag.get("start_signal"))
    start_signal = bool(start_signal_raw) if isinstance(start_signal_raw, bool) else False

    start_blocked_raw = runtime.get("start_blocked", diag.get("start_blocked"))
    start_blocked = bool(start_blocked_raw) if isinstance(start_blocked_raw, bool) else False

    reclaim_active_raw = runtime.get("reclaim_active")
    reclaim_active = bool(reclaim_active_raw) if isinstance(reclaim_active_raw, bool) else ("reclaim_active" in reasons)

    cooldown_active_raw = runtime.get("cooldown_active")
    cooldown_active = bool(cooldown_active_raw) if isinstance(cooldown_active_raw, bool) else ("cooldown_active" in reasons)

    required: List[str] = []
    if not start_gate_ok:
        required.extend(gate_reasons)
    if not price_in_box:
        required.append("price_outside_box")
    if not rsi_ok:
        required.append("rsi_out_of_range")
    if start_signal and start_blocked:
        if reclaim_active:
            required.append("reclaim_active")
        if cooldown_active:
            required.append("cooldown_active")
        if (not reclaim_active) and (not cooldown_active):
            required.append("start_blocked")

    required = _uniq_reasons(required)
    combo_key = "+".join(required) if required else None
    single = required[0] if len(required) == 1 else None

    return {
        "action": act,
        "required_blockers": required,
        "required_count": int(len(required)),
        "single_blocker": single,
        "combo_key": combo_key,
    }


def extract_stop_reason_flags(plan: Dict, applied_only: bool = True) -> List[str]:
    diag = plan.get("diagnostics", {}) or {}
    runtime = plan.get("runtime_state", {}) or {}

    key = "stop_reason_flags_applied_active" if applied_only else "stop_reason_flags_raw_active"
    reasons: List[str] = []
    for src in (diag.get(key), runtime.get(key)):
        if isinstance(src, list):
            reasons.extend([str(x) for x in src if str(x).strip()])

    if reasons:
        return _uniq_reasons(reasons)

    stop_reasons = (plan.get("risk", {}) or {}).get("stop_reasons", {}) or {}
    for k, v in stop_reasons.items():
        if isinstance(v, bool) and v:
            reasons.append(str(k))
    return _uniq_reasons(reasons)


def build_desired_ladder(
    levels: np.ndarray,
    ref_price: float,
    quote_total: float,
    base_total: float,
    maker_fee_pct: float,
    grid_budget_pct: float,
    max_orders_per_side: int = 40,
    rung_weights: Optional[List[float]] = None,
) -> List[OrderSim]:
    buys: List[Tuple[int, float]] = []
    sells: List[Tuple[int, float]] = []

    for i, px in enumerate(levels):
        px = float(px)
        if px <= 0:
            continue
        if px <= ref_price:
            buys.append((i, px))
        elif base_total > 0:
            sells.append((i, px))

    if len(buys) > max_orders_per_side:
        buys = buys[-max_orders_per_side:]
    if len(sells) > max_orders_per_side:
        sells = sells[:max_orders_per_side]

    out: List[OrderSim] = []
    fee = maker_fee_pct / 100.0
    quote_budget = max(float(quote_total) * float(grid_budget_pct), 0.0)

    if buys and quote_budget > 0:
        side_w = normalized_side_weights([i for i, _ in buys], rung_weights)
        for (i, px), w in zip(buys, side_w):
            quote_per = quote_budget * float(w)
            cost = quote_per / (1.0 + fee) if (1.0 + fee) > 0 else quote_per
            qty = cost / px
            if qty > 0:
                out.append(OrderSim("buy", px, qty, i))

    if sells and base_total > 0:
        side_w = normalized_side_weights([i for i, _ in sells], rung_weights)
        for (i, px), w in zip(sells, side_w):
            qty = float(base_total) * float(w)
            if qty > 0:
                out.append(OrderSim("sell", px, qty, i))

    return out


def simulate_grid(
    df: pd.DataFrame,
    box_low: float,
    box_high: float,
    n_levels: int,
    start_quote: float,
    start_base: float,
    maker_fee_pct: float,
    stop_out_steps: int = 1,
    touch_fill: bool = True,
    fill_confirmation_mode: Optional[str] = None,
    fill_cooldown_bars: int = 1,
    fill_no_repeat_lsi_guard: bool = True,
    tick_size: Optional[float] = None,
    tp_price: Optional[float] = None,
    sl_price: Optional[float] = None,
    rung_weights: Optional[List[float]] = None,
) -> Dict:
    """
    Neutral-ish grid simulation (v1):
    - Builds fixed levels in [box_low, box_high].
    - Places initial BUY ladder below the first candle close (quote-only unless start_base > 0).
    - If start_base > 0, it can place initial SELL ladder above price too (more market-maker-ish).
    - Fills use OHLC touch:
        buy fills if low <= price
        sell fills if high >= price
      (or reverse/cross mode if touch_fill=False)
    - On buy fill -> place sell one rung above (same qty)
    - On sell fill -> place buy one rung below (same qty)
    - Stop-out if TP/SL level is crossed (if provided), otherwise fallback to
      box break by stop_out_steps * step.
    """
    if df.empty:
        raise ValueError("OHLCV dataframe is empty (timerange/filter may have removed all rows).")

    fill_mode = _normalize_fill_mode(touch_fill, fill_confirmation_mode)
    levels = build_levels(box_low, box_high, n_levels, tick_size=tick_size)
    if len(levels) < 2:
        raise ValueError("Not enough levels. n_levels must be >= 1.")

    step = float(levels[1] - levels[0])
    fee = maker_fee_pct / 100.0

    quote = float(start_quote)
    base = float(start_base)

    open_orders: List[OrderSim] = []
    fills: List[FillSim] = []
    fill_guard = FillCooldownGuard(fill_cooldown_bars, fill_no_repeat_lsi_guard)

    curve = []

    first_close = float(df.iloc[0]["close"])
    initial_equity = quote + base * first_close

    # -----------------------------
    # Initial ladder
    # -----------------------------
    buy_idxs = [i for i, p in enumerate(levels) if p <= first_close]
    if not buy_idxs:
        buy_idxs = [0]

    sell_idxs = []
    if base > 0:
        sell_idxs = [i for i, p in enumerate(levels) if p >= first_close]
        if not sell_idxs:
            sell_idxs = [n_levels]

    if buy_idxs:
        side_w = normalized_side_weights(buy_idxs, rung_weights)
        for i, w in zip(buy_idxs, side_w):
            px = float(levels[i])
            if px <= 0:
                continue
            quote_per_order = quote * float(w)
            qty = quote_per_order / px
            if qty <= 0:
                continue
            open_orders.append(OrderSim(side="buy", price=px, qty_base=qty, level_index=i))

    if sell_idxs and base > 0:
        side_w = normalized_side_weights(sell_idxs, rung_weights)
        for i, w in zip(sell_idxs, side_w):
            px = float(levels[i])
            if px <= 0:
                continue
            qty = base * float(w)
            if qty <= 0:
                continue
            open_orders.append(OrderSim(side="sell", price=px, qty_base=qty, level_index=i))

    # -----------------------------
    # Simulation loop
    # -----------------------------
    for bar_index, (_, row) in enumerate(df.iterrows()):
        ts = row["date"].isoformat()
        o = float(row["open"])
        h = float(row["high"])
        l = float(row["low"])
        c = float(row["close"])

        # Stop-out check on close (prefer explicit TP/SL from plan when provided).
        stop_reason = None
        if tp_price is not None and c >= tp_price:
            stop_reason = "STOP_OUT_TP"
        elif sl_price is not None and c <= sl_price:
            stop_reason = "STOP_OUT_SL"
        elif c > box_high + stop_out_steps * step or c < box_low - stop_out_steps * step:
            stop_reason = "STOP_OUT_BOX_BREAK"

        if stop_reason is not None:
            if base > 0:
                proceeds = base * c
                fee_quote = proceeds * fee
                quote += proceeds - fee_quote
                fills.append(FillSim(ts, "sell", c, base, fee_quote, stop_reason))
                base = 0.0

            for od in open_orders:
                od.status = "canceled"
            open_orders = []

            curve.append({
                "ts": ts,
                "close": c,
                "quote": quote,
                "base": base,
                "equity": quote + base * c,
                "open_orders": 0,
                "stop": True,
            })
            break

        newly_filled: List[OrderSim] = []
        remaining: List[OrderSim] = []
        buy_bounds = _touched_index_bounds(
            levels,
            side="buy",
            o=o,
            h=h,
            l=l,
            c=c,
            mode=fill_mode,
        )
        sell_bounds = _touched_index_bounds(
            levels,
            side="sell",
            o=o,
            h=h,
            l=l,
            c=c,
            mode=fill_mode,
        )

        for od in open_orders:
            if od.status != "open":
                continue
            if od.level_index < 0 or od.level_index > n_levels:
                remaining.append(od)
                continue

            if od.side == "buy":
                if buy_bounds is None or not (buy_bounds[0] <= od.level_index <= buy_bounds[1]):
                    remaining.append(od)
                    continue
                fill = _fill_trigger("buy", o, h, l, c, od.price, fill_mode)
                if fill:
                    if not fill_guard.allow("buy", od.level_index, bar_index):
                        remaining.append(od)
                        continue
                    cost = od.qty_base * od.price
                    fee_quote = cost * fee
                    if quote >= cost + fee_quote:
                        quote -= (cost + fee_quote)
                        base += od.qty_base
                        od.status = "filled"
                        fills.append(FillSim(ts, "buy", od.price, od.qty_base, fee_quote, "FILL"))
                        fill_guard.mark("buy", od.level_index, bar_index)
                        newly_filled.append(od)
                    else:
                        remaining.append(od)
                else:
                    remaining.append(od)

            else:  # sell
                if sell_bounds is None or not (sell_bounds[0] <= od.level_index <= sell_bounds[1]):
                    remaining.append(od)
                    continue
                fill = _fill_trigger("sell", o, h, l, c, od.price, fill_mode)
                if fill:
                    if not fill_guard.allow("sell", od.level_index, bar_index):
                        remaining.append(od)
                        continue
                    proceeds = od.qty_base * od.price
                    fee_quote = proceeds * fee
                    if base >= od.qty_base:
                        base -= od.qty_base
                        quote += (proceeds - fee_quote)
                        od.status = "filled"
                        fills.append(FillSim(ts, "sell", od.price, od.qty_base, fee_quote, "FILL"))
                        fill_guard.mark("sell", od.level_index, bar_index)
                        newly_filled.append(od)
                    else:
                        remaining.append(od)
                else:
                    remaining.append(od)

        open_orders = remaining

        for od in newly_filled:
            i = od.level_index
            if od.side == "buy":
                if i + 1 <= n_levels:
                    sell_px = float(levels[i + 1])
                    open_orders.append(OrderSim("sell", sell_px, od.qty_base, i + 1))
            else:
                if i - 1 >= 0 and i - 1 <= n_levels:
                    buy_px = float(levels[i - 1])
                    open_orders.append(OrderSim("buy", buy_px, od.qty_base, i - 1))

        curve.append({
            "ts": ts,
            "close": c,
            "quote": quote,
            "base": base,
            "equity": quote + base * c,
            "open_orders": len(open_orders),
            "stop": False,
        })

    last_close = float(df.iloc[-1]["close"])
    equity = quote + base * last_close

    return {
        "summary": {
            "start_quote": start_quote,
            "start_base": start_base,
            "end_quote": quote,
            "end_base": base,
            "first_close": float(first_close),
            "last_close": last_close,
            "equity": equity,
            "initial_equity": float(initial_equity),
            "pnl_quote": float(equity - initial_equity),
            "pnl_pct": float((equity / initial_equity - 1.0) * 100.0) if initial_equity > 0 else 0.0,
            "box_low": box_low,
            "box_high": box_high,
            "n_levels": n_levels,
            "step": step,
            "maker_fee_pct": maker_fee_pct,
            "stop_out_steps": stop_out_steps,
            "touch_fill": touch_fill,
            "fill_confirmation_mode": fill_mode,
            "fill_cooldown_bars": int(fill_cooldown_bars),
            "fill_no_repeat_lsi_guard": bool(fill_no_repeat_lsi_guard),
            "tick_size": tick_size,
            "tp_price": tp_price,
            "sl_price": sl_price,
        },
        "fills": [asdict(x) for x in fills],
        "open_orders": [asdict(x) for x in open_orders],
        "curve": curve,
    }


def simulate_grid_replay(
    df: pd.DataFrame,
    plans: List[Dict],
    start_quote: float,
    start_base: float,
    maker_fee_pct: float,
    stop_out_steps: int = 1,
    touch_fill: bool = True,
    fill_confirmation_mode: Optional[str] = None,
    fill_cooldown_bars: int = 1,
    fill_no_repeat_lsi_guard: bool = True,
    tick_size: Optional[float] = None,
    max_orders_per_side: int = 40,
    close_on_stop: bool = False,
    chaos_profile: Optional[Dict] = None,
    include_deterministic_delta: bool = True,
) -> Dict:
    """
    Replay simulation across time-varying plan snapshots.
    Semantics match executor v1:
    - START seeds/rebuilds ladder (or soft-adjusts prices).
    - HOLD manages existing ladder only; never seeds from empty.
    - STOP cancels all open orders (optional flatten with close_on_stop).
    """
    if df.empty:
        raise ValueError("OHLCV dataframe is empty (timerange/filter may have removed all rows).")
    if not plans:
        raise ValueError("No plans provided for replay simulation.")

    fee = maker_fee_pct / 100.0
    quote = float(start_quote)
    base = float(start_base)

    open_orders: List[OrderSim] = []
    fills: List[FillSim] = []
    curve: List[Dict] = []
    events: List[Dict] = []

    first_close = float(df.iloc[0]["close"])
    initial_equity = quote + base * first_close

    plan_idx = -1
    active_plan: Optional[Dict] = None
    prev_plan: Optional[Dict] = None

    raw_action_counts: Dict[str, int] = {"START": 0, "HOLD": 0, "STOP": 0, "NO_PLAN": 0}
    effective_action_counts: Dict[str, int] = {"START": 0, "HOLD": 0, "STOP": 0, "NO_PLAN": 0}
    action_suppression_counts: Dict[str, int] = {}
    stop_count = 0
    seed_count = 0
    rebuild_count = 0
    soft_adjust_count = 0
    plan_switch_count = 0
    close_on_stop_count = 0
    start_blocker_counts: Dict[str, int] = {}
    start_counterfactual_single_counts: Dict[str, int] = {}
    start_counterfactual_combo_counts: Dict[str, int] = {}
    hold_reason_counts: Dict[str, int] = {}
    stop_reason_counts: Dict[str, int] = {}
    stop_event_reason_counts: Dict[str, int] = {}
    mode_plan_counts: Dict[str, int] = {}
    mode_desired_counts: Dict[str, int] = {}
    raw_action_mode_counts: Dict[str, int] = {}
    effective_action_mode_counts: Dict[str, int] = {}
    fill_mode_counts: Dict[str, int] = {}
    fill_mode_side_counts: Dict[str, int] = {}
    last_effective_action_signature: Optional[Tuple] = None
    fill_guard = FillCooldownGuard(fill_cooldown_bars, fill_no_repeat_lsi_guard)
    active_fill_mode = _normalize_fill_mode(touch_fill, fill_confirmation_mode)
    chaos_cfg = _build_chaos_runtime_config(chaos_profile)
    chaos_rng = np.random.default_rng(chaos_cfg.seed) if chaos_cfg is not None else None
    chaos_counters: Dict[str, int] = {
        "bars_total": int(len(df)),
        "bars_with_latency_block": 0,
        "bars_with_spread_shock": 0,
        "partial_fill_events": 0,
        "bars_with_reject_burst": 0,
        "rejected_fill_attempts": 0,
        "delayed_candles": 0,
        "missing_candles": 0,
        "data_gap_candles": 0,
        "dropped_candles_total": 0,
    }
    reject_burst_remaining = 0
    fill_candle_queue: Deque[Tuple[int, Dict[str, float]]] = deque()
    if chaos_cfg is not None:
        events.append(
            {
                "ts": str(pd.Timestamp(df.iloc[0]["date"]).isoformat()),
                "type": "CHAOS_PROFILE_APPLIED",
                "profile_id": chaos_cfg.profile_id,
                "profile_name": chaos_cfg.name,
                "seed": int(chaos_cfg.seed),
            }
        )

    for bar_index, (_, row) in enumerate(df.iterrows()):
        dt = pd.Timestamp(row["date"])
        ts = dt.isoformat()
        o = float(row["open"])
        h = float(row["high"])
        l = float(row["low"])
        c = float(row["close"])
        chaos_spread_shock_bps = 0.0
        chaos_latency_ms = 0.0
        chaos_latency_block = False
        chaos_reject_active = False
        chaos_data_gap = False
        chaos_missing_candle = False
        chaos_delayed_candle = False

        if chaos_cfg is not None and chaos_rng is not None:
            if reject_burst_remaining <= 0 and chaos_rng.random() < chaos_cfg.reject_burst_probability:
                reject_burst_remaining = _uniform_int_inclusive(
                    chaos_rng,
                    chaos_cfg.reject_burst_min_bars,
                    chaos_cfg.reject_burst_max_bars,
                )
            chaos_reject_active = reject_burst_remaining > 0
            if chaos_reject_active:
                chaos_counters["bars_with_reject_burst"] += 1

            chaos_data_gap = bool(chaos_rng.random() < chaos_cfg.data_gap_probability)
            if chaos_data_gap:
                chaos_counters["data_gap_candles"] += 1
                chaos_counters["dropped_candles_total"] += 1
            else:
                chaos_missing_candle = bool(chaos_rng.random() < chaos_cfg.missing_candle_probability)
                if chaos_missing_candle:
                    chaos_counters["missing_candles"] += 1
                    chaos_counters["dropped_candles_total"] += 1
                else:
                    chaos_delayed_candle = bool(chaos_rng.random() < chaos_cfg.delayed_candle_probability)
                    if chaos_delayed_candle:
                        chaos_counters["delayed_candles"] += 1

                    release_index = bar_index + (1 if chaos_delayed_candle else 0)
                    fill_candle_queue.append(
                        (
                            int(release_index),
                            {
                                "open": o,
                                "high": h,
                                "low": l,
                                "close": c,
                            },
                        )
                    )

            spread_burst = bool(chaos_rng.random() < chaos_cfg.spread_burst_probability)
            chaos_spread_shock_bps = float(chaos_cfg.spread_base_bps)
            if spread_burst:
                chaos_spread_shock_bps += float(chaos_cfg.spread_burst_bps)
            if chaos_spread_shock_bps > 0.0:
                chaos_counters["bars_with_spread_shock"] += 1

            chaos_latency_ms = max(
                0.0,
                float(chaos_rng.normal(chaos_cfg.latency_mean_ms, chaos_cfg.latency_jitter_ms)),
            )
            latency_probability = min(
                max(chaos_latency_ms / max(chaos_cfg.latency_fill_window_ms, 1.0), 0.0),
                1.0,
            )
            chaos_latency_block = bool(chaos_rng.random() < latency_probability)
            if chaos_latency_block:
                chaos_counters["bars_with_latency_block"] += 1

        switched = False
        while (plan_idx + 1) < len(plans):
            nxt = plans[plan_idx + 1]
            ptime = nxt.get("_plan_time")
            if ptime is None or ptime > dt:
                break
            plan_idx += 1
            active_plan = nxt
            switched = True

        if switched and active_plan is not None:
            plan_switch_count += 1
            events.append(
                {
                    "ts": ts,
                    "type": "PLAN_SWITCH",
                    "plan_index": int(plan_idx),
                    "plan_time_utc": str(active_plan.get("_plan_time")),
                    "plan_path": active_plan.get("_plan_path"),
                    "action": str(active_plan.get("action", "HOLD")).upper(),
                }
            )

        if chaos_cfg is not None:
            if chaos_data_gap:
                events.append({"ts": ts, "type": "CHAOS_DATA_GAP", "profile_id": chaos_cfg.profile_id})
            elif chaos_missing_candle:
                events.append({"ts": ts, "type": "CHAOS_MISSING_CANDLE", "profile_id": chaos_cfg.profile_id})
            elif chaos_delayed_candle:
                events.append({"ts": ts, "type": "CHAOS_DELAYED_CANDLE", "profile_id": chaos_cfg.profile_id})
            if chaos_latency_block:
                events.append(
                    {
                        "ts": ts,
                        "type": "CHAOS_LATENCY_BLOCK",
                        "profile_id": chaos_cfg.profile_id,
                        "latency_ms": float(chaos_latency_ms),
                    }
                )
            if chaos_reject_active:
                events.append({"ts": ts, "type": "CHAOS_REJECT_BURST", "profile_id": chaos_cfg.profile_id})

        if active_plan is None:
            raw_action_counts["NO_PLAN"] += 1
            effective_action_counts["NO_PLAN"] += 1
            _increment_reason(raw_action_mode_counts, "NO_PLAN|no_plan", 1)
            _increment_reason(effective_action_mode_counts, "NO_PLAN|no_plan", 1)
            curve.append(
                {
                    "ts": ts,
                    "close": c,
                    "quote": quote,
                    "base": base,
                    "equity": quote + base * c,
                    "open_orders": len([x for x in open_orders if x.status == "open"]),
                    "stop": False,
                    "action": "NO_PLAN",
                    "raw_action": "NO_PLAN",
                    "effective_action": "NO_PLAN",
                    "action_suppression_reason": None,
                    "plan_index": None,
                    "plan_time_utc": None,
                    "start_counterfactual_required_count": 0,
                    "start_counterfactual_single": None,
                    "start_counterfactual_combo": None,
                    "start_counterfactual_required": "",
                    "chaos_profile_id": chaos_cfg.profile_id if chaos_cfg is not None else None,
                    "chaos_latency_block": bool(chaos_latency_block),
                    "chaos_spread_shock_bps": float(chaos_spread_shock_bps),
                    "chaos_reject_burst_active": bool(chaos_reject_active),
                    "chaos_delayed_candle": bool(chaos_delayed_candle),
                    "chaos_missing_candle": bool(chaos_missing_candle),
                    "chaos_data_gap": bool(chaos_data_gap),
                    "chaos_fill_queue_len": int(len(fill_candle_queue)),
                }
            )
            if chaos_reject_active and reject_burst_remaining > 0:
                reject_burst_remaining -= 1
            continue

        active_mode = _normalize_router_mode(active_plan.get("mode"), default="unknown")
        desired_mode = _normalize_router_mode(
            ((active_plan.get("regime_router") or {}).get("desired_mode")),
            default="unknown",
        )
        runtime_state = active_plan.get("runtime_state") or {}
        mode_at_entry = runtime_state.get("mode_at_entry") or runtime_state.get("mode") or active_mode
        mode_at_exit = runtime_state.get("mode_at_exit") or mode_at_entry
        _increment_reason(mode_plan_counts, active_mode, 1)
        _increment_reason(mode_desired_counts, desired_mode, 1)

        if "range" not in active_plan or "grid" not in active_plan:
            raise KeyError("Plan schema mismatch during replay: expected keys ['range','grid'].")

        box_low = float(active_plan["range"]["low"])
        box_high = float(active_plan["range"]["high"])
        n_levels = int(active_plan["grid"]["n_levels"])
        grid_cfg = active_plan.get("grid", {}) or {}
        fd_cfg = grid_cfg.get("fill_detection", {}) or {}
        active_fill_mode = _normalize_fill_mode(
            touch_fill,
            fd_cfg.get("fill_confirmation_mode", fill_confirmation_mode),
        )
        fill_guard.configure(
            cooldown_bars=int(fd_cfg.get("cooldown_bars", fill_cooldown_bars) or fill_cooldown_bars),
            no_repeat_lsi_guard=bool(fd_cfg.get("no_repeat_lsi_guard", fill_no_repeat_lsi_guard)),
        )
        tick_size_eff = _safe_float(grid_cfg.get("tick_size"), default=tick_size)
        levels = build_levels(box_low, box_high, n_levels, tick_size=tick_size_eff)
        if len(levels) < 2:
            raise ValueError("Not enough levels in replay plan (n_levels must be >= 1).")
        step = float(levels[1] - levels[0])

        ref_price = _safe_float((active_plan.get("price_ref", {}) or {}).get("close"), default=None)
        if ref_price is None:
            ref_price = c

        tp_price, sl_price = extract_exit_levels(active_plan)
        raw_action = str(active_plan.get("action", "HOLD")).upper()
        if raw_action not in ("START", "HOLD", "STOP"):
            raw_action = "HOLD"

        stop_reason: Optional[str] = None
        if raw_action != "STOP":
            if tp_price is not None and c >= tp_price:
                raw_action = "STOP"
                stop_reason = "STOP_OUT_TP"
            elif sl_price is not None and c <= sl_price:
                raw_action = "STOP"
                stop_reason = "STOP_OUT_SL"
            elif tp_price is None and sl_price is None:
                if c > box_high + stop_out_steps * step or c < box_low - stop_out_steps * step:
                    raw_action = "STOP"
                    stop_reason = "STOP_OUT_BOX_BREAK"

        plan_sig = plan_signature(active_plan)
        rebuild = False
        soft_adjust = False
        if prev_plan is None:
            rebuild = True
        else:
            sig_prev = plan_signature(prev_plan)
            sig_new = plan_sig
            if sig_prev != sig_new:
                if soft_adjust_ok(prev_plan, active_plan):
                    soft_adjust = True
                else:
                    rebuild = True

        has_active_orders = any(o.status in ("open", "partial") for o in open_orders)
        effective_action = raw_action
        suppression_reason: Optional[str] = None

        if raw_action == "START" and has_active_orders and (not rebuild) and (not soft_adjust):
            # START is seed-only; unchanged live ladders are managed under HOLD semantics.
            effective_action = "HOLD"
            suppression_reason = "duplicate_start_manage_existing"
        elif raw_action == "STOP":
            has_flatten_work = close_on_stop and base > 0.0
            stop_sig = action_signature("STOP", plan_sig, stop_reason or "PLAN_STOP")
            if (not has_active_orders) and (not has_flatten_work):
                if last_effective_action_signature == stop_sig:
                    # Duplicate STOP on already-cleared state: suppress churn.
                    effective_action = "HOLD"
                    suppression_reason = "duplicate_stop_already_cleared"

        raw_action_counts[raw_action] += 1
        effective_action_counts[effective_action] += 1
        _increment_reason(raw_action_mode_counts, f"{raw_action}|{active_mode}", 1)
        _increment_reason(effective_action_mode_counts, f"{effective_action}|{active_mode}", 1)
        if suppression_reason is not None:
            _increment_reason(action_suppression_counts, suppression_reason, 1)
            events.append(
                {
                    "ts": ts,
                    "type": "ACTION_SUPPRESS",
                    "raw_action": raw_action,
                    "effective_action": effective_action,
                    "reason": suppression_reason,
                    "plan_index": int(plan_idx),
                    "plan_time_utc": str(active_plan.get("_plan_time")),
                }
            )

        plan_start_block_reasons = extract_start_block_reasons(active_plan)
        start_counterfactual = extract_start_counterfactual(
            active_plan,
            action=raw_action,
            start_block_reasons=plan_start_block_reasons,
        )
        cf_required = [str(x) for x in (start_counterfactual.get("required_blockers", []) or [])]
        cf_required_count = int(start_counterfactual.get("required_count", 0) or 0)
        cf_single = start_counterfactual.get("single_blocker")
        cf_combo = start_counterfactual.get("combo_key")
        cf_required_text = "|".join(cf_required)
        if raw_action != "START":
            _increment_reasons(start_blocker_counts, plan_start_block_reasons)
        if effective_action == "HOLD":
            _increment_reasons(hold_reason_counts, plan_start_block_reasons)
            _increment_reason(hold_reason_counts, suppression_reason, 1)
            if cf_required:
                _increment_reason(start_counterfactual_combo_counts, cf_combo, 1)
                if len(cf_required) == 1:
                    _increment_reason(start_counterfactual_single_counts, cf_single, 1)
        plan_stop_reason_flags = extract_stop_reason_flags(active_plan, applied_only=True)
        if raw_action == "STOP":
            if not plan_stop_reason_flags:
                plan_stop_reason_flags = extract_stop_reason_flags(active_plan, applied_only=False)
            _increment_reasons(stop_reason_counts, plan_stop_reason_flags)

        if effective_action == "STOP":
            stop_count += 1
            if stop_reason is None:
                stop_reason = "PLAN_STOP"
            _increment_reason(stop_event_reason_counts, stop_reason, 1)
            if not plan_stop_reason_flags:
                _increment_reason(stop_reason_counts, f"event:{stop_reason}", 1)

            for od in open_orders:
                od.status = "canceled"
            open_orders = []

            if close_on_stop and base > 0:
                proceeds = base * c
                fee_quote = proceeds * fee
                quote += proceeds - fee_quote
                fills.append(FillSim(ts, "sell", c, base, fee_quote, stop_reason))
                _increment_reason(fill_mode_counts, active_mode, 1)
                _increment_reason(fill_mode_side_counts, f"sell|{active_mode}", 1)
                base = 0.0
                close_on_stop_count += 1

            events.append(
                {
                    "ts": ts,
                    "type": "STOP",
                    "reason": stop_reason,
                    "reason_flags": [str(x) for x in plan_stop_reason_flags],
                    "start_block_reasons": [str(x) for x in plan_start_block_reasons],
                    "plan_index": int(plan_idx),
                    "plan_time_utc": str(active_plan.get("_plan_time")),
                    "mode_at_entry": mode_at_entry,
                    "mode_at_exit": mode_at_exit,
                }
            )

            curve.append(
                {
                    "ts": ts,
                    "close": c,
                    "quote": quote,
                    "base": base,
                    "equity": quote + base * c,
                    "open_orders": 0,
                    "stop": True,
                    "action": effective_action,
                    "raw_action": raw_action,
                    "effective_action": effective_action,
                    "action_suppression_reason": suppression_reason,
                    "plan_index": int(plan_idx),
                    "plan_time_utc": str(active_plan.get("_plan_time")),
                    "start_counterfactual_required_count": cf_required_count,
                    "start_counterfactual_single": cf_single,
                    "start_counterfactual_combo": cf_combo,
                    "start_counterfactual_required": cf_required_text,
                    "mode_at_entry": mode_at_entry,
                    "mode_at_exit": mode_at_exit,
                    "stop_reason": stop_reason,
                    "chaos_profile_id": chaos_cfg.profile_id if chaos_cfg is not None else None,
                    "chaos_latency_block": bool(chaos_latency_block),
                    "chaos_spread_shock_bps": float(chaos_spread_shock_bps),
                    "chaos_reject_burst_active": bool(chaos_reject_active),
                    "chaos_delayed_candle": bool(chaos_delayed_candle),
                    "chaos_missing_candle": bool(chaos_missing_candle),
                    "chaos_data_gap": bool(chaos_data_gap),
                    "chaos_fill_queue_len": int(len(fill_candle_queue)),
                }
            )

            prev_plan = active_plan
            last_effective_action_signature = action_signature(
                "STOP", plan_sig, stop_reason or "PLAN_STOP"
            )
            if chaos_reject_active and reject_burst_remaining > 0:
                reject_burst_remaining -= 1
            continue

        if effective_action == "HOLD":
            if has_active_orders and soft_adjust:
                for od in open_orders:
                    if od.status not in ("open", "partial"):
                        continue
                    if od.level_index < 0 or od.level_index > n_levels:
                        continue
                    od.price = float(levels[od.level_index])
                soft_adjust_count += 1
                events.append(
                    {
                        "ts": ts,
                        "type": "SOFT_ADJUST",
                        "action": "HOLD",
                        "plan_index": int(plan_idx),
                    }
                )

        else:
            need_seed = (not has_active_orders) or rebuild or (prev_plan is None)
            if need_seed:
                if has_active_orders:
                    for od in open_orders:
                        od.status = "canceled"
                    open_orders = []
                    rebuild_count += 1
                events.append(
                    {
                        "ts": ts,
                        "type": "REBUILD",
                        "plan_index": int(plan_idx),
                        "mode_at_entry": mode_at_entry,
                    }
                )

                desired = build_desired_ladder(
                    levels=levels,
                    ref_price=float(ref_price),
                    quote_total=quote,
                    base_total=base,
                    maker_fee_pct=maker_fee_pct,
                    grid_budget_pct=float((active_plan.get("capital_policy", {}) or {}).get("grid_budget_pct", 1.0)),
                    max_orders_per_side=max_orders_per_side,
                    rung_weights=extract_rung_weights(active_plan, n_levels),
                )
                open_orders = desired
                seed_count += 1
                events.append(
                    {
                        "ts": ts,
                        "type": "SEED",
                        "orders": len(desired),
                        "plan_index": int(plan_idx),
                        "mode_at_entry": mode_at_entry,
                    }
                )
            elif soft_adjust:
                for od in open_orders:
                    if od.status not in ("open", "partial"):
                        continue
                    if od.level_index < 0 or od.level_index > n_levels:
                        continue
                    od.price = float(levels[od.level_index])
                soft_adjust_count += 1
                events.append(
                    {
                        "ts": ts,
                        "type": "SOFT_ADJUST",
                        "action": "START",
                        "plan_index": int(plan_idx),
                    }
                )

        fill_candle: Optional[Dict[str, float]]
        if chaos_cfg is None:
            fill_candle = {
                "open": o,
                "high": h,
                "low": l,
                "close": c,
            }
        else:
            fill_candle = None
            if (not chaos_latency_block) and fill_candle_queue and fill_candle_queue[0][0] <= bar_index:
                _, fill_candle = fill_candle_queue.popleft()

        newly_filled: List[Tuple[str, int, float]] = []
        remaining: List[OrderSim] = []
        if fill_candle is not None:
            fo = float(fill_candle["open"])
            fh = float(fill_candle["high"])
            fl = float(fill_candle["low"])
            fc = float(fill_candle["close"])
            buy_bounds = _touched_index_bounds(
                levels,
                side="buy",
                o=fo,
                h=fh,
                l=fl,
                c=fc,
                mode=active_fill_mode,
            )
            sell_bounds = _touched_index_bounds(
                levels,
                side="sell",
                o=fo,
                h=fh,
                l=fl,
                c=fc,
                mode=active_fill_mode,
            )
            spread_shock_pct = float(max(chaos_spread_shock_bps, 0.0)) * 1e-4

            for od in open_orders:
                if od.status not in ("open", "partial"):
                    continue
                if od.level_index < 0 or od.level_index > n_levels:
                    remaining.append(od)
                    continue

                if od.side == "buy":
                    if buy_bounds is None or not (buy_bounds[0] <= od.level_index <= buy_bounds[1]):
                        remaining.append(od)
                        continue
                    trigger_price = float(od.price * (1.0 - spread_shock_pct))
                    fill = _fill_trigger("buy", fo, fh, fl, fc, trigger_price, active_fill_mode)
                    if fill:
                        if chaos_reject_active:
                            chaos_counters["rejected_fill_attempts"] += 1
                            remaining.append(od)
                            continue
                        if not fill_guard.allow("buy", od.level_index, bar_index):
                            remaining.append(od)
                            continue
                        fill_ratio = 1.0
                        if chaos_cfg is not None and chaos_rng is not None:
                            if chaos_rng.random() < chaos_cfg.partial_fill_probability:
                                fill_ratio = float(
                                    chaos_rng.uniform(
                                        chaos_cfg.partial_fill_min_ratio,
                                        chaos_cfg.partial_fill_max_ratio,
                                    )
                                )
                        fill_qty = float(min(max(od.qty_base * fill_ratio, 0.0), od.qty_base))
                        if fill_qty <= 0.0:
                            remaining.append(od)
                            continue
                        cost = fill_qty * od.price
                        fee_quote = cost * fee
                        if quote >= cost + fee_quote:
                            quote -= (cost + fee_quote)
                            base += fill_qty
                            is_partial = fill_qty < od.qty_base
                            if is_partial:
                                od.qty_base = float(max(od.qty_base - fill_qty, 0.0))
                                od.status = "partial"
                                remaining.append(od)
                                chaos_counters["partial_fill_events"] += 1
                            else:
                                od.status = "filled"
                            fills.append(
                                FillSim(
                                    ts,
                                    "buy",
                                    od.price,
                                    fill_qty,
                                    fee_quote,
                                    "PARTIAL_FILL" if is_partial else "FILL",
                                )
                            )
                            fill_guard.mark("buy", od.level_index, bar_index)
                            _increment_reason(fill_mode_counts, active_mode, 1)
                            _increment_reason(fill_mode_side_counts, f"buy|{active_mode}", 1)
                            newly_filled.append(("buy", od.level_index, fill_qty))
                        else:
                            remaining.append(od)
                    else:
                        remaining.append(od)

                else:
                    if sell_bounds is None or not (sell_bounds[0] <= od.level_index <= sell_bounds[1]):
                        remaining.append(od)
                        continue
                    trigger_price = float(od.price * (1.0 + spread_shock_pct))
                    fill = _fill_trigger("sell", fo, fh, fl, fc, trigger_price, active_fill_mode)
                    if fill:
                        if chaos_reject_active:
                            chaos_counters["rejected_fill_attempts"] += 1
                            remaining.append(od)
                            continue
                        if not fill_guard.allow("sell", od.level_index, bar_index):
                            remaining.append(od)
                            continue
                        fill_ratio = 1.0
                        if chaos_cfg is not None and chaos_rng is not None:
                            if chaos_rng.random() < chaos_cfg.partial_fill_probability:
                                fill_ratio = float(
                                    chaos_rng.uniform(
                                        chaos_cfg.partial_fill_min_ratio,
                                        chaos_cfg.partial_fill_max_ratio,
                                    )
                                )
                        fill_qty = float(min(max(od.qty_base * fill_ratio, 0.0), od.qty_base))
                        if fill_qty <= 0.0:
                            remaining.append(od)
                            continue
                        proceeds = fill_qty * od.price
                        fee_quote = proceeds * fee
                        if base >= fill_qty:
                            base -= fill_qty
                            quote += (proceeds - fee_quote)
                            is_partial = fill_qty < od.qty_base
                            if is_partial:
                                od.qty_base = float(max(od.qty_base - fill_qty, 0.0))
                                od.status = "partial"
                                remaining.append(od)
                                chaos_counters["partial_fill_events"] += 1
                            else:
                                od.status = "filled"
                            fills.append(
                                FillSim(
                                    ts,
                                    "sell",
                                    od.price,
                                    fill_qty,
                                    fee_quote,
                                    "PARTIAL_FILL" if is_partial else "FILL",
                                )
                            )
                            fill_guard.mark("sell", od.level_index, bar_index)
                            _increment_reason(fill_mode_counts, active_mode, 1)
                            _increment_reason(fill_mode_side_counts, f"sell|{active_mode}", 1)
                            newly_filled.append(("sell", od.level_index, fill_qty))
                        else:
                            remaining.append(od)
                    else:
                        remaining.append(od)
        else:
            remaining.extend(open_orders)

        open_orders = remaining

        for side, level_index, fill_qty in newly_filled:
            if side == "buy":
                if level_index + 1 <= n_levels:
                    sell_px = float(levels[level_index + 1])
                    open_orders.append(OrderSim("sell", sell_px, fill_qty, level_index + 1))
            else:
                if level_index - 1 >= 0 and level_index - 1 <= n_levels:
                    buy_px = float(levels[level_index - 1])
                    open_orders.append(OrderSim("buy", buy_px, fill_qty, level_index - 1))

        curve.append(
            {
                "ts": ts,
                "close": c,
                "quote": quote,
                "base": base,
                "equity": quote + base * c,
                "open_orders": len(open_orders),
                "stop": False,
                "action": effective_action,
                "raw_action": raw_action,
                "effective_action": effective_action,
                "action_suppression_reason": suppression_reason,
                "plan_index": int(plan_idx),
                "plan_time_utc": str(active_plan.get("_plan_time")),
                "start_counterfactual_required_count": cf_required_count,
                "start_counterfactual_single": cf_single,
                "start_counterfactual_combo": cf_combo,
                "start_counterfactual_required": cf_required_text,
                "chaos_profile_id": chaos_cfg.profile_id if chaos_cfg is not None else None,
                "chaos_latency_block": bool(chaos_latency_block),
                "chaos_spread_shock_bps": float(chaos_spread_shock_bps),
                "chaos_reject_burst_active": bool(chaos_reject_active),
                "chaos_delayed_candle": bool(chaos_delayed_candle),
                "chaos_missing_candle": bool(chaos_missing_candle),
                "chaos_data_gap": bool(chaos_data_gap),
                "chaos_fill_queue_len": int(len(fill_candle_queue)),
            }
        )

        prev_plan = active_plan
        last_effective_action_signature = action_signature(effective_action, plan_sig)
        if chaos_reject_active and reject_burst_remaining > 0:
            reject_burst_remaining -= 1

    last_close = float(df.iloc[-1]["close"])
    equity = quote + base * last_close

    plan_times = [str(p.get("_plan_time")) for p in plans]
    plan_paths = [str(p.get("_plan_path")) for p in plans]
    stop_reason_counts_sorted = _sorted_reason_counts(stop_reason_counts)
    stop_event_reason_counts_sorted = _sorted_reason_counts(stop_event_reason_counts)
    combined_stop_reason_counts = dict(stop_reason_counts_sorted)
    for k, v in stop_event_reason_counts_sorted.items():
        ek = f"event:{k}"
        combined_stop_reason_counts[ek] = int(combined_stop_reason_counts.get(ek, 0)) + int(v)
    combined_stop_reason_counts = _sorted_reason_counts(combined_stop_reason_counts)

    chaos_counters_out = {k: int(v) for k, v in sorted(chaos_counters.items())}
    chaos_counters_out["pending_fill_candles"] = int(len(fill_candle_queue))
    summary = {
        "mode": "replay",
        "start_quote": start_quote,
        "start_base": start_base,
        "end_quote": quote,
        "end_base": base,
        "first_close": float(first_close),
        "last_close": last_close,
        "equity": equity,
        "initial_equity": float(initial_equity),
        "pnl_quote": float(equity - initial_equity),
        "pnl_pct": float((equity / initial_equity - 1.0) * 100.0) if initial_equity > 0 else 0.0,
        "maker_fee_pct": maker_fee_pct,
        "stop_out_steps": stop_out_steps,
        "touch_fill": touch_fill,
        "fill_confirmation_mode": active_fill_mode,
        "fill_cooldown_bars": int(fill_guard.cooldown_bars),
        "fill_no_repeat_lsi_guard": bool(fill_guard.no_repeat_lsi_guard),
        "close_on_stop": bool(close_on_stop),
        "plans_total": int(len(plans)),
        "plans_switched": int(plan_switch_count),
        "actions": effective_action_counts,
        "raw_actions": raw_action_counts,
        "effective_actions": effective_action_counts,
        "mode_plan_counts": _sorted_reason_counts(mode_plan_counts),
        "mode_desired_counts": _sorted_reason_counts(mode_desired_counts),
        "raw_action_mode_counts": _sorted_reason_counts(raw_action_mode_counts),
        "effective_action_mode_counts": _sorted_reason_counts(effective_action_mode_counts),
        "fill_mode_counts": _sorted_reason_counts(fill_mode_counts),
        "fill_mode_side_counts": _sorted_reason_counts(fill_mode_side_counts),
        "action_suppression_counts": _sorted_reason_counts(action_suppression_counts),
        "action_suppressed_total": int(sum(action_suppression_counts.values())),
        "stop_events": int(stop_count),
        "seed_events": int(seed_count),
        "rebuild_events": int(rebuild_count),
        "soft_adjust_events": int(soft_adjust_count),
        "close_on_stop_events": int(close_on_stop_count),
        "start_blocker_counts": _sorted_reason_counts(start_blocker_counts),
        "start_counterfactual_single_counts": _sorted_reason_counts(start_counterfactual_single_counts),
        "start_counterfactual_combo_counts": _sorted_reason_counts(start_counterfactual_combo_counts),
        "hold_reason_counts": _sorted_reason_counts(hold_reason_counts),
        "stop_reason_counts": stop_reason_counts_sorted,
        "stop_event_reason_counts": stop_event_reason_counts_sorted,
        "stop_reason_counts_combined": combined_stop_reason_counts,
        "chaos_profile_enabled": bool(chaos_cfg is not None),
        "chaos_profile_id": chaos_cfg.profile_id if chaos_cfg is not None else None,
        "chaos_profile_name": chaos_cfg.name if chaos_cfg is not None else None,
        "chaos_seed": int(chaos_cfg.seed) if chaos_cfg is not None else None,
        "chaos_counters": chaos_counters_out if chaos_cfg is not None else {},
    }

    if chaos_cfg is not None and include_deterministic_delta:
        try:
            baseline_res = simulate_grid_replay(
                df=df,
                plans=plans,
                start_quote=start_quote,
                start_base=start_base,
                maker_fee_pct=maker_fee_pct,
                stop_out_steps=stop_out_steps,
                touch_fill=touch_fill,
                fill_confirmation_mode=fill_confirmation_mode,
                fill_cooldown_bars=fill_cooldown_bars,
                fill_no_repeat_lsi_guard=fill_no_repeat_lsi_guard,
                tick_size=tick_size,
                max_orders_per_side=max_orders_per_side,
                close_on_stop=close_on_stop,
                chaos_profile=None,
                include_deterministic_delta=False,
            )
            baseline_summary = baseline_res.get("summary", {}) or {}
            summary["deterministic_baseline"] = {
                "pnl_pct": float(baseline_summary.get("pnl_pct", 0.0)),
                "pnl_quote": float(baseline_summary.get("pnl_quote", 0.0)),
                "fills_total": int(len(baseline_res.get("fills", []) or [])),
                "stop_events": int(baseline_summary.get("stop_events", 0)),
                "action_suppressed_total": int(baseline_summary.get("action_suppressed_total", 0)),
            }
            summary["deterministic_vs_chaos_delta"] = {
                "pnl_pct_delta": float(summary["pnl_pct"]) - float(baseline_summary.get("pnl_pct", 0.0)),
                "pnl_quote_delta": float(summary["pnl_quote"]) - float(baseline_summary.get("pnl_quote", 0.0)),
                "fills_total_delta": int(len(fills)) - int(len(baseline_res.get("fills", []) or [])),
                "stop_events_delta": int(summary["stop_events"]) - int(baseline_summary.get("stop_events", 0)),
                "action_suppressed_total_delta": int(summary["action_suppressed_total"])
                - int(baseline_summary.get("action_suppressed_total", 0)),
            }
        except Exception as exc:
            summary["deterministic_baseline_error"] = str(exc)

    return {
        "summary": summary,
        "fills": [asdict(x) for x in fills],
        "open_orders": [asdict(x) for x in open_orders],
        "curve": curve,
        "events": events,
        "plan_times_utc": plan_times,
        "plan_paths": plan_paths,
    }


def load_plan(plan_path: str) -> Dict:
    with open(plan_path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", required=True, help="e.g. ETH/USDT")
    ap.add_argument("--timeframe", required=True, help="e.g. 15m or 1h (must match the OHLCV file you downloaded)")
    ap.add_argument("--data-dir", default="/freqtrade/user_data/data", help="freqtrade data directory")
    ap.add_argument("--plan", required=True, help="plan json path (grid_plan.latest.json)")
    ap.add_argument("--replay-plans", action="store_true", help="Replay archived plan snapshots over candle time")
    ap.add_argument("--plans-dir", default=None, help="Directory with archived grid_plan.*.json files (optional)")
    ap.add_argument(
        "--chaos-profile",
        default=None,
        help="Optional chaos profile JSON for replay perturbations (validated against schemas/chaos_profile.schema.json)",
    )
    ap.add_argument("--timerange", default=None, help="YYYYMMDD-YYYYMMDD (optional)")
    ap.add_argument("--start-at", default=None, help="Start time: 'plan' or YYYYMMDD or YYYYMMDDHHMM or ISO timestamp")
    ap.add_argument("--start-quote", type=float, default=1000.0)
    ap.add_argument("--start-base", type=float, default=0.0)
    ap.add_argument("--fee-pct", type=float, default=0.10)
    ap.add_argument("--stop-out-steps", type=int, default=1)
    ap.add_argument("--max-orders-per-side", type=int, default=40, help="Initial ladder cap per side in replay mode")
    ap.add_argument("--close-on-stop", action="store_true", help="Flatten base inventory when STOP occurs")
    ap.add_argument("--touch-fill", action="store_true", help="OHLC touch-fill model (default)")
    ap.add_argument("--reverse-fill", action="store_true", help="reverse/cross-fill model (more strict)")
    ap.add_argument("--out", default="/freqtrade/user_data/grid_sim_v1.result.json")
    args = ap.parse_args()

    touch_fill = True
    if args.reverse_fill:
        touch_fill = False
    if args.touch_fill:
        touch_fill = True

    plan = load_plan(args.plan)
    plan_sequence: Optional[List[Dict]] = None
    chaos_profile: Optional[Dict] = None

    if "range" not in plan or "grid" not in plan:
        raise KeyError(
            "Plan schema mismatch: expected keys ['range','grid'] from GridBrainV1.\n"
            "Make sure --plan points to grid_plans/<exchange>/<pair>/grid_plan.latest.json"
        )

    # Warn if plan says exec TF != your OHLCV TF
    plan_exec_tf = (plan.get("timeframes") or {}).get("exec")
    if plan_exec_tf and plan_exec_tf != args.timeframe:
        print(
            f"[WARN] Plan exec timeframe is '{plan_exec_tf}' but you are simulating on '{args.timeframe}'.\n"
            f"       This can be OK for rough testing, but fills/stop behavior will differ.\n",
            flush=True,
        )

    if args.replay_plans:
        plan_sequence = load_plan_sequence(args.plan, args.plans_dir)
        if not plan_sequence:
            raise ValueError("Replay mode requested but no valid plan snapshots were loaded.")

    if args.chaos_profile:
        chaos_profile = load_chaos_profile(args.chaos_profile)

    box_low = float(plan["range"]["low"])
    box_high = float(plan["range"]["high"])
    n_levels = int(plan["grid"]["n_levels"])
    rung_weights = extract_rung_weights(plan, n_levels)
    fill_cfg = (plan.get("grid", {}) or {}).get("fill_detection", {}) or {}
    fill_mode_hint = fill_cfg.get("fill_confirmation_mode")
    fill_cooldown_bars = int(fill_cfg.get("cooldown_bars", 1) or 1)
    fill_no_repeat_lsi_guard = bool(fill_cfg.get("no_repeat_lsi_guard", True))
    tick_size = _safe_float((plan.get("grid", {}) or {}).get("tick_size"), default=None)
    tp_price = None
    sl_price = None
    try:
        ex = plan.get("exit", {}) or {}
        if ex.get("tp_price") is not None:
            tp_price = float(ex.get("tp_price"))
        if ex.get("sl_price") is not None:
            sl_price = float(ex.get("sl_price"))
    except Exception:
        tp_price = None
        sl_price = None

    if tp_price is None or sl_price is None:
        try:
            rk = plan.get("risk", {}) or {}
            if tp_price is None and rk.get("tp_price") is not None:
                tp_price = float(rk.get("tp_price"))
            if sl_price is None and rk.get("sl_price") is not None:
                sl_price = float(rk.get("sl_price"))
        except Exception:
            pass

    ohlcv_path = find_ohlcv_file(args.data_dir, args.pair, args.timeframe)
    df = load_ohlcv(ohlcv_path)
    df = filter_timerange(df, args.timerange)

    start_plan = plan
    if args.replay_plans and plan_sequence:
        if args.start_at is None:
            start_at_ts = plan_sequence[0]["_plan_time"]
        else:
            if args.start_at.strip().lower() == "plan":
                start_plan = plan_sequence[0]
            start_at_ts = parse_start_at(args.start_at, start_plan)
    else:
        start_at_ts = parse_start_at(args.start_at, start_plan)

    if start_at_ts is not None:
        df = df[df["date"] >= start_at_ts].reset_index(drop=True)

    if args.replay_plans:
        if not plan_sequence:
            raise ValueError("Replay mode requested but no plan sequence is available.")
        res = simulate_grid_replay(
            df=df,
            plans=plan_sequence,
            start_quote=args.start_quote,
            start_base=args.start_base,
            maker_fee_pct=args.fee_pct,
            stop_out_steps=args.stop_out_steps,
            touch_fill=touch_fill,
            fill_confirmation_mode=fill_mode_hint,
            fill_cooldown_bars=fill_cooldown_bars,
            fill_no_repeat_lsi_guard=fill_no_repeat_lsi_guard,
            tick_size=tick_size,
            max_orders_per_side=args.max_orders_per_side,
            close_on_stop=args.close_on_stop,
            chaos_profile=chaos_profile,
        )
    else:
        if chaos_profile is not None:
            print("[WARN] --chaos-profile is ignored unless --replay-plans is enabled.", flush=True)
        res = simulate_grid(
            df=df,
            box_low=box_low,
            box_high=box_high,
            n_levels=n_levels,
            start_quote=args.start_quote,
            start_base=args.start_base,
            maker_fee_pct=args.fee_pct,
            stop_out_steps=args.stop_out_steps,
            touch_fill=touch_fill,
            fill_confirmation_mode=fill_mode_hint,
            fill_cooldown_bars=fill_cooldown_bars,
            fill_no_repeat_lsi_guard=fill_no_repeat_lsi_guard,
            tick_size=tick_size,
            tp_price=tp_price,
            sl_price=sl_price,
            rung_weights=rung_weights,
        )

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)

    fills = pd.DataFrame(res["fills"])
    csv_out = args.out.replace(".json", ".fills.csv")
    fills.to_csv(csv_out, index=False)

    curve = pd.DataFrame(res["curve"])
    curve_out = args.out.replace(".json", ".curve.csv")
    curve.to_csv(curve_out, index=False)

    if "events" in res:
        events = pd.DataFrame(res["events"])
        events_out = args.out.replace(".json", ".events.csv")
        events.to_csv(events_out, index=False)
        print(f"Wrote events: {events_out}", flush=True)

    print(f"Loaded OHLCV: {ohlcv_path}", flush=True)
    print(f"Wrote result: {args.out}", flush=True)
    print(f"Wrote fills:  {csv_out}", flush=True)
    print(f"Wrote curve:  {curve_out}", flush=True)
    print("Summary:", res["summary"], flush=True)


if __name__ == "__main__":
    main()
