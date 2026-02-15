# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these imports ---
import json
import os
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple, List

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy, informative
import talib.abstract as ta
from technical import qtpylib


class GridBrainV1(IStrategy):
    """
    GridBrainV1 (Brain-only) — outputs a GridPlan JSON every 15m candle.
    - Does NOT trade.
    - Uses deterministic v1 rules (no ML yet, but fields are present).
    - Writes plan files under:
        user_data/grid_plans/<exchange>/<pair>/grid_plan.latest.json
        user_data/grid_plans/<exchange>/<pair>/grid_plan.<timestamp>.json
      - Optional override for automation: GRID_PLANS_ROOT_REL

    Architecture:
      - Freqtrade/Strategy = Brain (signals + range + sizing + stop triggers)
      - Separate Executor places/maintains ladder orders on any CEX via CCXT
      - Separate Simulator replays candles/ticks and simulates fills accurately
    """

    INTERFACE_VERSION = 3

    # ===== MTF PLAN ALIGNMENT =====
    # 15m: box + execution triggers
    # 1h : volatility / MA distance / vol gates
    # 4h : regime ADX
    timeframe = "15m"
    can_short: bool = False

    minimal_roi = {"0": 0.0}
    stoploss = -0.99
    trailing_stop = False

    process_only_new_candles = True

    # Need enough candles for 7d lookback on 15m:
    # 7 * 24 * 4 = 672  (plus buffer)
    startup_candle_count: int = 800

    # ========= v1 locked defaults =========
    # Box builder (15m)
    box_lookback_24h_bars = 96     # 24h on 15m
    box_lookback_48h_bars = 192    # 48h on 15m
    box_lookback_18h_bars = 72
    box_lookback_12h_bars = 48
    extremes_7d_bars = 7 * 24 * 4  # 672

    atr_period_15m = 20
    atr_pad_mult = 0.35

    rsi_period_15m = 14
    rsi_min = 40
    rsi_max = 60

    # Regime gate (4h ADX)
    adx_period = 14
    adx_4h_max = 22

    # 1h gates
    ema_fast = 50
    ema_slow = 100
    ema_dist_max_frac = 0.012  # 1.2%

    bb_window = 20
    bb_stds = 2.0
    bbw_pct_lookback_1h = 252
    bbw_1h_pct_max = 50.0

    vol_sma_window = 20
    vol_spike_mult = 1.5  # 1h volume <= 1.5 * SMA20
    rvol_window_15m = 20

    # VRVP (fixed-window volume profile)
    vrvp_lookback_bars = 96
    vrvp_bins = 48
    vrvp_value_area_pct = 0.70
    vrvp_poc_outside_box_max_frac = 0.005
    vrvp_max_box_shift_frac = 0.005
    vrvp_reject_if_still_outside = True

    # BBWP + squeeze gates
    bbwp_enabled = True
    bbwp_lookback_s = 252  # 15m
    bbwp_lookback_m = 252  # 1h
    bbwp_lookback_l = 252  # 4h
    bbwp_s_max = 35.0
    bbwp_m_max = 50.0
    bbwp_l_max = 60.0
    bbwp_veto_pct = 90.0
    bbwp_cooloff_trigger_pct = 98.0
    bbwp_cooloff_release_s = 50.0
    bbwp_cooloff_release_m = 60.0
    squeeze_enabled = True
    squeeze_require_on_1h = False
    kc_atr_mult = 1.5

    # os_dev regime state
    os_dev_enabled = True
    os_dev_n_strike = 2
    os_dev_range_band = 0.75
    os_dev_persist_bars = 24
    os_dev_rvol_max = 1.2
    os_dev_history_bars = 960

    # Micro-VAP + HVN/LVN
    micro_vap_enabled = True
    micro_vap_lookback_bars = 96
    micro_vap_bins = 64
    micro_hvn_quantile = 0.80
    micro_lvn_quantile = 0.20
    micro_extrema_count = 6
    micro_lvn_corridor_steps = 1.0
    micro_void_slope_threshold = 0.55

    # FVG stack (Defensive + IMFVG + Session FVG)
    fvg_enabled = True
    fvg_lookback_bars = 192
    fvg_min_gap_atr = 0.05
    fvg_straddle_veto_steps = 0.75
    fvg_position_avg_count = 8

    imfvg_enabled = True
    imfvg_mitigated_relax = True

    defensive_fvg_enabled = True
    defensive_fvg_min_gap_atr = 0.20
    defensive_fvg_body_frac = 0.55
    defensive_fvg_fresh_bars = 16

    session_fvg_enabled = True
    session_fvg_inside_gate = True
    session_fvg_pause_bars = 0

    # MRVD (multi-range volume distribution: day/week/month)
    mrvd_enabled = True
    mrvd_bins = 64
    mrvd_value_area_pct = 0.70
    mrvd_day_lookback_bars = 96         # 1 day on 15m
    mrvd_week_lookback_bars = 7 * 96    # 1 week on 15m
    mrvd_month_lookback_bars = 30 * 96  # 30 days on 15m (falls back to available bars)
    mrvd_required_overlap_count = 2     # >= 2/3 periods
    mrvd_va_overlap_min_frac = 0.10
    mrvd_near_poc_steps = 1.0
    mrvd_drift_guard_enabled = True
    mrvd_drift_guard_steps = 0.75

    # CVD (divergence + BOS nudges)
    cvd_enabled = True
    cvd_lookback_bars = 192
    cvd_pivot_left = 3
    cvd_pivot_right = 3
    cvd_divergence_max_age_bars = 64
    cvd_near_value_steps = 1.0
    cvd_bos_lookback = 20
    cvd_bos_freeze_bars = 4
    cvd_rung_bias_strength = 0.35

    # FreqAI confidence overlay (soft nudges; deterministic loop remains primary)
    freqai_overlay_enabled = True
    freqai_overlay_strict_predict = False
    freqai_overlay_confidence_min = 0.55
    freqai_overlay_breakout_scale = 0.02
    freqai_overlay_breakout_quick_tp_thresh = 0.70
    freqai_overlay_rung_edge_cut_max = 0.45

    # Rung density bias (executor/simulator consume these weights)
    rung_weight_hvn_boost = 1.0
    rung_weight_lvn_penalty = 0.40
    rung_weight_min = 0.20
    rung_weight_max = 3.00

    # Grid sizing (cost-aware)
    # Net target per step (>=0.40%), gross = net + fee + spread
    target_net_step_pct = 0.0040
    est_fee_pct = 0.0020     # default 0.20% (tweak per exchange/VIP)
    est_spread_pct = 0.0005  # default 0.05% majors
    n_min = 6
    n_max = 12

    # Width constraints for the box
    min_width_pct = 0.035  # 3.5%
    max_width_pct = 0.060  # 6.0%

    # Stop rules (15m)
    stop_confirm_bars = 2
    fast_stop_step_multiple = 1.0  # 1 * step beyond edge
    range_shift_stop_pct = 0.007   # 0.7% mid shift vs previous plan
    tp_step_multiple = 0.75
    sl_step_multiple = 1.0
    reclaim_hours = 4.0
    cooldown_minutes = 90
    min_runtime_hours = 3.0

    # Gate tuning profile (START gating debug/tune helper)
    gate_profile = "strict"  # strict | balanced | aggressive
    start_min_gate_pass_ratio = 1.0  # keep 1.0 for strict all-gates behavior

    # Regime router (intraday / swing / pause).
    regime_router_enabled = True
    regime_router_default_mode = "intraday"  # intraday | swing | pause
    regime_router_force_mode = ""  # empty for auto, else intraday | swing | pause
    regime_router_switch_persist_bars = 4
    regime_router_switch_cooldown_bars = 6
    regime_router_switch_margin = 1.0
    regime_router_allow_pause = True
    regime_threshold_profile = "manual"  # manual | research_v1

    # Intraday (scalper-ish) mode thresholds.
    intraday_adx_enter_max = 22.0
    intraday_adx_exit_min = 30.0
    intraday_adx_rising_bars = 3
    intraday_bbw_1h_pct_max = 30.0
    intraday_ema_dist_max_frac = 0.005
    intraday_vol_spike_mult = 1.2
    intraday_bbwp_s_enter_low = 15.0
    intraday_bbwp_s_enter_high = 45.0
    intraday_bbwp_m_enter_low = 10.0
    intraday_bbwp_m_enter_high = 55.0
    intraday_bbwp_l_enter_low = 10.0
    intraday_bbwp_l_enter_high = 65.0
    intraday_bbwp_stop_high = 90.0
    intraday_atr_pct_max = 0.015
    intraday_os_dev_persist_bars = 24
    intraday_os_dev_rvol_max = 1.2

    # Swing range mode thresholds.
    swing_adx_enter_max = 28.0
    swing_adx_exit_min = 35.0
    swing_adx_rising_bars = 2
    swing_bbw_1h_pct_max = 40.0
    swing_ema_dist_max_frac = 0.010
    swing_vol_spike_mult = 1.8
    swing_bbwp_s_enter_low = 10.0
    swing_bbwp_s_enter_high = 65.0
    swing_bbwp_m_enter_low = 10.0
    swing_bbwp_m_enter_high = 65.0
    swing_bbwp_l_enter_low = 10.0
    swing_bbwp_l_enter_high = 75.0
    swing_bbwp_stop_high = 93.0
    swing_atr_pct_max = 0.030
    swing_os_dev_persist_bars = 12
    swing_os_dev_rvol_max = 1.8

    # Backtest/walk-forward: write full per-candle plan history for true replay.
    emit_per_candle_history_backtest = True

    # Update policy
    soft_adjust_max_step_frac = 0.5  # if edges move < 0.5*step => soft adjust allowed

    # Capital policy (quote-only for now)
    grid_budget_pct = 0.70
    reserve_pct = 0.30

    plans_root_rel = "grid_plans"

    # -------- internal state (best-effort, per process) --------
    _last_written_ts_by_pair: Dict[str, int] = {}
    _last_plan_hash_by_pair: Dict[str, str] = {}
    _last_mid_by_pair: Dict[str, float] = {}
    _reclaim_until_ts_by_pair: Dict[str, int] = {}
    _cooldown_until_ts_by_pair: Dict[str, int] = {}
    _active_since_ts_by_pair: Dict[str, int] = {}
    _running_by_pair: Dict[str, bool] = {}
    _bbwp_cooloff_by_pair: Dict[str, bool] = {}
    _os_dev_state_by_pair: Dict[str, int] = {}
    _os_dev_candidate_by_pair: Dict[str, int] = {}
    _os_dev_candidate_count_by_pair: Dict[str, int] = {}
    _os_dev_zero_persist_by_pair: Dict[str, int] = {}
    _mrvd_day_poc_prev_by_pair: Dict[str, float] = {}
    _cvd_freeze_bars_left_by_pair: Dict[str, int] = {}
    _last_adx_by_pair: Dict[str, float] = {}
    _adx_rising_count_by_pair: Dict[str, int] = {}
    _mode_by_pair: Dict[str, str] = {}
    _mode_candidate_by_pair: Dict[str, str] = {}
    _mode_candidate_count_by_pair: Dict[str, int] = {}
    _mode_cooldown_until_ts_by_pair: Dict[str, int] = {}
    _running_mode_by_pair: Dict[str, str] = {}
    _history_emit_in_progress_by_pair: Dict[str, bool] = {}
    _history_emit_end_ts_by_pair: Dict[str, int] = {}
    _external_mode_thresholds_path_cache: Optional[str] = None
    _external_mode_thresholds_mtime_cache: float = -1.0
    _external_mode_thresholds_cache: Dict[str, Dict[str, float]] = {}

    # ========== Informative pairs ==========
    def informative_pairs(self):
        if not self.dp:
            return []
        wl = self.dp.current_whitelist()
        out = []
        for p in wl:
            out.append((p, "1h"))
            out.append((p, "4h"))
        return out

    @informative("4h")
    def populate_indicators_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["adx_4h"] = ta.ADX(dataframe, timeperiod=self.adx_period)
        dataframe["plus_di_4h"] = ta.PLUS_DI(dataframe, timeperiod=self.adx_period)
        dataframe["minus_di_4h"] = ta.MINUS_DI(dataframe, timeperiod=self.adx_period)
        dataframe["atr_4h"] = ta.ATR(dataframe, timeperiod=self.bb_window)

        tp = qtpylib.typical_price(dataframe)
        bb = qtpylib.bollinger_bands(tp, window=self.bb_window, stds=self.bb_stds)
        dataframe["bb_mid_4h"] = bb["mid"]
        dataframe["bb_upper_4h"] = bb["upper"]
        dataframe["bb_lower_4h"] = bb["lower"]
        dataframe["bb_width_4h"] = (dataframe["bb_upper_4h"] - dataframe["bb_lower_4h"]) / dataframe["bb_mid_4h"]
        return dataframe

    @informative("1h")
    def populate_indicators_1h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        tp = qtpylib.typical_price(dataframe)
        bb = qtpylib.bollinger_bands(tp, window=self.bb_window, stds=self.bb_stds)
        dataframe["bb_mid_1h"] = bb["mid"]
        dataframe["bb_upper_1h"] = bb["upper"]
        dataframe["bb_lower_1h"] = bb["lower"]
        dataframe["bb_width_1h"] = (dataframe["bb_upper_1h"] - dataframe["bb_lower_1h"]) / dataframe["bb_mid_1h"]

        dataframe["ema50_1h"] = ta.EMA(dataframe, timeperiod=self.ema_fast)
        dataframe["ema100_1h"] = ta.EMA(dataframe, timeperiod=self.ema_slow)

        dataframe["vol_sma20_1h"] = dataframe["volume"].rolling(self.vol_sma_window).mean()

        dataframe["kc_mid_1h"] = ta.EMA(dataframe, timeperiod=self.bb_window)
        dataframe["atr_1h"] = ta.ATR(dataframe, timeperiod=self.bb_window)
        dataframe["kc_upper_1h"] = dataframe["kc_mid_1h"] + (self.kc_atr_mult * dataframe["atr_1h"])
        dataframe["kc_lower_1h"] = dataframe["kc_mid_1h"] - (self.kc_atr_mult * dataframe["atr_1h"])
        dataframe["squeeze_on_1h"] = (
            (dataframe["bb_upper_1h"] < dataframe["kc_upper_1h"])
            & (dataframe["bb_lower_1h"] > dataframe["kc_lower_1h"])
        ).astype(int)
        return dataframe

    # ========== Helpers ==========
    @staticmethod
    def _safe_float(x) -> Optional[float]:
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

    @staticmethod
    def _adx_exit_hysteresis_trigger(
        adx_value: Optional[float],
        rising_count: int,
        exit_min: float,
        rising_bars_required: int,
    ) -> bool:
        adx = GridBrainV1._safe_float(adx_value)
        if adx is None:
            return False
        rb = int(max(int(rising_bars_required), 1))
        return bool(adx >= float(exit_min) and int(rising_count) >= rb)

    @staticmethod
    def _adx_di_down_risk_trigger(
        adx_value: Optional[float],
        plus_di_value: Optional[float],
        minus_di_value: Optional[float],
        rising_count: int,
        exit_min: float,
        rising_bars_required: int,
        early_margin: float = 2.0,
    ) -> bool:
        adx = GridBrainV1._safe_float(adx_value)
        plus_di = GridBrainV1._safe_float(plus_di_value)
        minus_di = GridBrainV1._safe_float(minus_di_value)
        if adx is None or plus_di is None or minus_di is None:
            return False
        if not bool(minus_di > plus_di):
            return False
        rb = int(max(int(rising_bars_required), 1))
        threshold = max(float(exit_min) - abs(float(early_margin)), 0.0)
        return bool(adx >= threshold and int(rising_count) >= rb)

    def _gate_profile_values(self) -> Dict[str, float]:
        profile = str(getattr(self, "gate_profile", "strict")).strip().lower()
        if profile not in ("strict", "balanced", "aggressive"):
            profile = "strict"

        cfg = {
            "profile": profile,
            "adx_4h_max": float(self.adx_4h_max),
            "bbw_1h_pct_max": float(self.bbw_1h_pct_max),
            "ema_dist_max_frac": float(self.ema_dist_max_frac),
            "vol_spike_mult": float(self.vol_spike_mult),
            "bbwp_s_max": float(self.bbwp_s_max),
            "bbwp_m_max": float(self.bbwp_m_max),
            "bbwp_l_max": float(self.bbwp_l_max),
            "bbwp_veto_pct": float(self.bbwp_veto_pct),
            "bbwp_cooloff_trigger_pct": float(self.bbwp_cooloff_trigger_pct),
            "bbwp_cooloff_release_s": float(self.bbwp_cooloff_release_s),
            "bbwp_cooloff_release_m": float(self.bbwp_cooloff_release_m),
            "os_dev_persist_bars": int(self.os_dev_persist_bars),
            "os_dev_rvol_max": float(self.os_dev_rvol_max),
            "start_min_gate_pass_ratio": float(np.clip(self.start_min_gate_pass_ratio, 0.0, 1.0)),
        }

        if profile == "balanced":
            cfg["adx_4h_max"] = max(cfg["adx_4h_max"], 25.0)
            cfg["bbw_1h_pct_max"] = max(cfg["bbw_1h_pct_max"], 60.0)
            cfg["ema_dist_max_frac"] = max(cfg["ema_dist_max_frac"], 0.009)
            cfg["vol_spike_mult"] = max(cfg["vol_spike_mult"], 3.0)
            cfg["bbwp_s_max"] = max(cfg["bbwp_s_max"], 45.0)
            cfg["bbwp_m_max"] = max(cfg["bbwp_m_max"], 60.0)
            cfg["bbwp_l_max"] = max(cfg["bbwp_l_max"], 70.0)
            cfg["os_dev_persist_bars"] = min(cfg["os_dev_persist_bars"], 24)
            cfg["os_dev_rvol_max"] = max(cfg["os_dev_rvol_max"], 1.5)
        elif profile == "aggressive":
            cfg["adx_4h_max"] = max(cfg["adx_4h_max"], 30.0)
            cfg["bbw_1h_pct_max"] = max(cfg["bbw_1h_pct_max"], 70.0)
            cfg["ema_dist_max_frac"] = max(cfg["ema_dist_max_frac"], 0.015)
            cfg["vol_spike_mult"] = max(cfg["vol_spike_mult"], 4.0)
            cfg["bbwp_s_max"] = max(cfg["bbwp_s_max"], 60.0)
            cfg["bbwp_m_max"] = max(cfg["bbwp_m_max"], 75.0)
            cfg["bbwp_l_max"] = max(cfg["bbwp_l_max"], 85.0)
            cfg["os_dev_persist_bars"] = min(cfg["os_dev_persist_bars"], 12)
            cfg["os_dev_rvol_max"] = max(cfg["os_dev_rvol_max"], 1.8)

        return cfg

    @staticmethod
    def _normalize_mode_name(mode: Optional[str]) -> str:
        m = str(mode or "").strip().lower()
        if m == "swing":
            return "swing"
        if m == "pause":
            return "pause"
        return "intraday"

    def _active_threshold_profile(self) -> str:
        env_profile = str(os.getenv("GRID_REGIME_THRESHOLD_PROFILE", "") or "").strip().lower()
        if env_profile in ("manual", "research_v1"):
            return env_profile
        return str(getattr(self, "regime_threshold_profile", "manual") or "manual").strip().lower()

    def _external_mode_threshold_overrides(self) -> Dict[str, Dict[str, float]]:
        path = str(os.getenv("GRID_MODE_THRESHOLDS_PATH", "") or "").strip()
        if not path:
            self._external_mode_thresholds_path_cache = None
            self._external_mode_thresholds_mtime_cache = -1.0
            self._external_mode_thresholds_cache = {}
            return {}

        try:
            mtime = float(os.path.getmtime(path))
        except Exception:
            mtime = -1.0

        if (
            self._external_mode_thresholds_path_cache == path
            and self._external_mode_thresholds_mtime_cache == mtime
        ):
            return dict(self._external_mode_thresholds_cache)

        raw: Dict = {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f) or {}
        except Exception:
            raw = {}

        payload = raw.get("recommended_thresholds", raw)
        out: Dict[str, Dict[str, float]] = {}

        for mode in ("intraday", "swing"):
            src = payload.get(mode, {}) if isinstance(payload, dict) else {}
            if not isinstance(src, dict):
                continue

            normalized: Dict[str, float] = {}
            for key_raw, val_raw in src.items():
                key = str(key_raw).strip()
                if not key:
                    continue
                if key in ("atr_source",):
                    normalized[key] = str(val_raw).strip().lower()
                    continue
                if key in ("router_eligible",):
                    normalized[key] = bool(val_raw)
                    continue
                fv = self._safe_float(val_raw)
                if fv is None:
                    continue
                normalized[key] = float(fv)

            # Optional shorthand compatibility from audit report schema.
            if "bbwp_s_max" in normalized and "bbwp_s_enter_high" not in normalized:
                normalized["bbwp_s_enter_high"] = float(normalized["bbwp_s_max"])
            if "bbwp_m_max" in normalized and "bbwp_m_enter_high" not in normalized:
                normalized["bbwp_m_enter_high"] = float(normalized["bbwp_m_max"])
            if "bbwp_l_max" in normalized and "bbwp_l_enter_high" not in normalized:
                normalized["bbwp_l_enter_high"] = float(normalized["bbwp_l_max"])
            if "adx_exit_max" in normalized and "adx_exit_min" not in normalized:
                normalized["adx_exit_min"] = float(normalized["adx_exit_max"])
            if "adx_exit_min" in normalized and "adx_exit_max" not in normalized:
                normalized["adx_exit_max"] = float(normalized["adx_exit_min"])
            if "os_dev_persist_bars" in normalized:
                normalized["os_dev_persist_bars"] = int(round(float(normalized["os_dev_persist_bars"])))
            if "adx_rising_bars" in normalized:
                normalized["adx_rising_bars"] = int(round(float(normalized["adx_rising_bars"])))
            if "router_eligible" not in normalized:
                normalized["router_eligible"] = True

            out[mode] = normalized

        self._external_mode_thresholds_path_cache = path
        self._external_mode_thresholds_mtime_cache = mtime
        self._external_mode_thresholds_cache = dict(out)
        return out

    def _mode_threshold_overrides(self, mode_name: str) -> Dict[str, float]:
        mode = self._normalize_mode_name(mode_name)
        profile = self._active_threshold_profile()
        overrides: Dict[str, float] = {}
        if profile == "research_v1":
            if mode == "intraday":
                overrides = {
                    "adx_enter_max": 24.0,
                    "adx_exit_min": 30.0,
                    "adx_exit_max": 30.0,
                    "adx_rising_bars": 3,
                    "bbw_1h_pct_max": 30.0,
                    "ema_dist_max_frac": 0.005,
                    "vol_spike_mult": 1.2,
                    "bbwp_s_enter_low": 15.0,
                    "bbwp_s_enter_high": 45.0,
                    "bbwp_m_enter_low": 10.0,
                    "bbwp_m_enter_high": 55.0,
                    "bbwp_l_enter_low": 10.0,
                    "bbwp_l_enter_high": 65.0,
                    "bbwp_s_max": 45.0,
                    "bbwp_m_max": 55.0,
                    "bbwp_l_max": 65.0,
                    "bbwp_stop_high": 90.0,
                    "atr_source": "1h",
                    "atr_pct_max": 0.015,
                    "os_dev_persist_bars": 24,
                    "os_dev_rvol_max": 1.2,
                    "router_eligible": True,
                }
            elif mode == "swing":
                overrides = {
                    "adx_enter_max": 30.0,
                    "adx_exit_min": 35.0,
                    "adx_exit_max": 35.0,
                    "adx_rising_bars": 2,
                    "bbw_1h_pct_max": 40.0,
                    "ema_dist_max_frac": 0.010,
                    "vol_spike_mult": 1.5,
                    "bbwp_s_enter_low": 10.0,
                    "bbwp_s_enter_high": 65.0,
                    "bbwp_m_enter_low": 10.0,
                    "bbwp_m_enter_high": 65.0,
                    "bbwp_l_enter_low": 10.0,
                    "bbwp_l_enter_high": 75.0,
                    "bbwp_s_max": 65.0,
                    "bbwp_m_max": 65.0,
                    "bbwp_l_max": 75.0,
                    "bbwp_stop_high": 93.0,
                    "atr_source": "4h",
                    "atr_pct_max": 0.030,
                    "os_dev_persist_bars": 12,
                    "os_dev_rvol_max": 1.5,
                    "router_eligible": True,
                }
        external = self._external_mode_threshold_overrides().get(mode, {})
        if external:
            overrides.update(external)
        return overrides

    def _mode_threshold_block(self, mode_name: str) -> Dict[str, float]:
        mode = self._normalize_mode_name(mode_name)
        intraday_block = {
            "mode": "intraday",
            "adx_enter_max": float(self.intraday_adx_enter_max),
            "adx_exit_min": float(self.intraday_adx_exit_min),
            "adx_exit_max": float(self.intraday_adx_exit_min),
            "adx_rising_bars": int(self.intraday_adx_rising_bars),
            "bbw_1h_pct_max": float(self.intraday_bbw_1h_pct_max),
            "ema_dist_max_frac": float(self.intraday_ema_dist_max_frac),
            "vol_spike_mult": float(self.intraday_vol_spike_mult),
            "bbwp_s_enter_low": float(self.intraday_bbwp_s_enter_low),
            "bbwp_s_enter_high": float(self.intraday_bbwp_s_enter_high),
            "bbwp_m_enter_low": float(self.intraday_bbwp_m_enter_low),
            "bbwp_m_enter_high": float(self.intraday_bbwp_m_enter_high),
            "bbwp_l_enter_low": float(self.intraday_bbwp_l_enter_low),
            "bbwp_l_enter_high": float(self.intraday_bbwp_l_enter_high),
            "bbwp_s_max": float(self.intraday_bbwp_s_enter_high),
            "bbwp_m_max": float(self.intraday_bbwp_m_enter_high),
            "bbwp_l_max": float(self.intraday_bbwp_l_enter_high),
            "bbwp_stop_high": float(self.intraday_bbwp_stop_high),
            "atr_source": "1h",
            "atr_pct_max": float(self.intraday_atr_pct_max),
            "os_dev_persist_bars": int(self.intraday_os_dev_persist_bars),
            "os_dev_rvol_max": float(self.intraday_os_dev_rvol_max),
            "router_eligible": True,
        }
        intraday_block.update(self._mode_threshold_overrides("intraday"))
        if mode == "swing":
            swing_block = {
                "mode": "swing",
                "adx_enter_max": float(self.swing_adx_enter_max),
                "adx_exit_min": float(self.swing_adx_exit_min),
                "adx_exit_max": float(self.swing_adx_exit_min),
                "adx_rising_bars": int(self.swing_adx_rising_bars),
                "bbw_1h_pct_max": float(self.swing_bbw_1h_pct_max),
                "ema_dist_max_frac": float(self.swing_ema_dist_max_frac),
                "vol_spike_mult": float(self.swing_vol_spike_mult),
                "bbwp_s_enter_low": float(self.swing_bbwp_s_enter_low),
                "bbwp_s_enter_high": float(self.swing_bbwp_s_enter_high),
                "bbwp_m_enter_low": float(self.swing_bbwp_m_enter_low),
                "bbwp_m_enter_high": float(self.swing_bbwp_m_enter_high),
                "bbwp_l_enter_low": float(self.swing_bbwp_l_enter_low),
                "bbwp_l_enter_high": float(self.swing_bbwp_l_enter_high),
                "bbwp_s_max": float(self.swing_bbwp_s_enter_high),
                "bbwp_m_max": float(self.swing_bbwp_m_enter_high),
                "bbwp_l_max": float(self.swing_bbwp_l_enter_high),
                "bbwp_stop_high": float(self.swing_bbwp_stop_high),
                "atr_source": "4h",
                "atr_pct_max": float(self.swing_atr_pct_max),
                "os_dev_persist_bars": int(self.swing_os_dev_persist_bars),
                "os_dev_rvol_max": float(self.swing_os_dev_rvol_max),
                "router_eligible": True,
            }
            swing_block.update(self._mode_threshold_overrides("swing"))
            return swing_block
        if mode == "pause":
            pause_block = dict(intraday_block)
            pause_block["mode"] = "pause"
            pause_block["router_eligible"] = False
            return pause_block
        return intraday_block

    def _mode_router_score(self, cfg: Dict[str, float], features: Dict[str, Optional[float]]) -> Dict[str, object]:
        adx = self._safe_float(features.get("adx_4h"))
        ema_dist = self._safe_float(features.get("ema_dist_frac_1h"))
        bbw_pct = self._safe_float(features.get("bb_width_1h_pct"))
        vol_ratio = self._safe_float(features.get("vol_ratio_1h"))
        bbwp_s = self._safe_float(features.get("bbwp_15m_pct"))
        bbwp_m = self._safe_float(features.get("bbwp_1h_pct"))
        bbwp_l = self._safe_float(features.get("bbwp_4h_pct"))
        rvol_15m = self._safe_float(features.get("rvol_15m"))
        atr_1h_pct = self._safe_float(features.get("atr_1h_pct"))
        atr_4h_pct = self._safe_float(features.get("atr_4h_pct"))
        atr_source = str(cfg.get("atr_source", "1h")).strip().lower()
        atr_pct = atr_4h_pct if atr_source == "4h" else atr_1h_pct

        checks: Dict[str, Optional[bool]] = {
            "adx_enter_ok": None if adx is None else bool(adx <= float(cfg["adx_enter_max"])),
            "ema_dist_ok": None if ema_dist is None else bool(ema_dist <= float(cfg["ema_dist_max_frac"])),
            "bbw_1h_pct_ok": None if bbw_pct is None else bool(bbw_pct <= float(cfg["bbw_1h_pct_max"])),
            "vol_ratio_ok": None if vol_ratio is None else bool(vol_ratio <= float(cfg["vol_spike_mult"])),
            "bbwp_s_ok": None if bbwp_s is None else bool(float(cfg["bbwp_s_enter_low"]) <= bbwp_s <= float(cfg["bbwp_s_enter_high"])),
            "bbwp_m_ok": None if bbwp_m is None else bool(float(cfg["bbwp_m_enter_low"]) <= bbwp_m <= float(cfg["bbwp_m_enter_high"])),
            "bbwp_l_ok": None if bbwp_l is None else bool(float(cfg["bbwp_l_enter_low"]) <= bbwp_l <= float(cfg["bbwp_l_enter_high"])),
            "atr_pct_ok": None if atr_pct is None else bool(atr_pct <= float(cfg["atr_pct_max"])),
            "rvol_15m_ok": None if rvol_15m is None else bool(rvol_15m <= float(cfg["os_dev_rvol_max"])),
        }
        known = [v for v in checks.values() if v is not None]
        passed = int(sum(1 for v in known if bool(v)))
        total = int(len(known))
        ratio = float(passed / total) if total > 0 else 0.0
        score = float(passed) + ratio
        required_fields = [
            "adx_enter_ok",
            "ema_dist_ok",
            "bbw_1h_pct_ok",
            "vol_ratio_ok",
            "bbwp_s_ok",
            "bbwp_m_ok",
            "bbwp_l_ok",
            "atr_pct_ok",
            "rvol_15m_ok",
        ]
        router_eligible = bool(cfg.get("router_eligible", True))
        known_required = [checks.get(k) for k in required_fields]
        eligible = bool(
            router_eligible
            and all(v is not None for v in known_required)
            and all(bool(v) for v in known_required)
        )
        return {
            "checks": checks,
            "passed": int(passed),
            "total": int(total),
            "ratio": float(ratio),
            "score": float(score),
            "eligible": bool(eligible),
            "atr_source": atr_source,
            "atr_pct": atr_pct,
        }

    def _regime_router_state(
        self,
        pair: str,
        clock_ts: int,
        features: Dict[str, Optional[float]],
    ) -> Dict[str, object]:
        default_mode = self._normalize_mode_name(getattr(self, "regime_router_default_mode", "intraday"))
        forced_raw = str(getattr(self, "regime_router_force_mode", "") or "").strip().lower()
        forced_mode = forced_raw if forced_raw in ("intraday", "swing", "pause") else None
        enabled = bool(getattr(self, "regime_router_enabled", True))
        allow_pause = bool(getattr(self, "regime_router_allow_pause", True))

        current_mode = self._normalize_mode_name(self._mode_by_pair.get(pair, default_mode))
        intraday_cfg = self._mode_threshold_block("intraday")
        swing_cfg = self._mode_threshold_block("swing")
        intraday_eval = self._mode_router_score(intraday_cfg, features)
        swing_eval = self._mode_router_score(swing_cfg, features)
        running_active = bool(features.get("running_active", False))
        running_mode_raw = features.get("running_mode")
        running_mode = None
        if running_active and str(running_mode_raw or "").strip():
            running_mode = self._normalize_mode_name(running_mode_raw)
        calm_flags: List[bool] = []
        for feat_name, threshold in [
            ("adx_4h", float(intraday_cfg["adx_enter_max"])),
            ("ema_dist_frac_1h", float(intraday_cfg["ema_dist_max_frac"])),
            ("bb_width_1h_pct", float(intraday_cfg["bbw_1h_pct_max"])),
            ("vol_ratio_1h", float(intraday_cfg["vol_spike_mult"])),
            ("bbwp_15m_pct", float(intraday_cfg["bbwp_s_max"])),
            ("bbwp_1h_pct", float(intraday_cfg["bbwp_m_max"])),
            ("bbwp_4h_pct", float(intraday_cfg["bbwp_l_max"])),
        ]:
            val = self._safe_float(features.get(feat_name))
            if val is None:
                continue
            calm_flags.append(bool(val <= threshold))
        calm_ratio = float(sum(1 for x in calm_flags if x) / len(calm_flags)) if calm_flags else 0.0
        intraday_score_adj = float(intraday_eval["score"]) + calm_ratio
        swing_score_adj = float(swing_eval["score"]) - calm_ratio

        margin = max(float(getattr(self, "regime_router_switch_margin", 0.0)), 0.0)
        if forced_mode is not None:
            desired_mode = forced_mode
            desired_reason = "forced_mode"
        elif not enabled:
            desired_mode = current_mode
            desired_reason = "router_disabled"
        else:
            intraday_eligible = bool(intraday_eval.get("eligible", False))
            swing_eligible = bool(swing_eval.get("eligible", False))
            if intraday_eligible and (not swing_eligible):
                desired_mode = "intraday"
                desired_reason = "intraday_eligible_only"
            elif swing_eligible and (not intraday_eligible):
                desired_mode = "swing"
                desired_reason = "swing_eligible_only"
            elif intraday_eligible and swing_eligible:
                intraday_score = float(intraday_score_adj)
                swing_score = float(swing_score_adj)
                if swing_score >= (intraday_score + margin):
                    desired_mode = "swing"
                    desired_reason = "swing_score_advantage"
                elif intraday_score >= (swing_score + margin):
                    desired_mode = "intraday"
                    desired_reason = "intraday_score_advantage"
                else:
                    desired_mode = current_mode if current_mode in ("intraday", "swing") else "intraday"
                    desired_reason = "score_tie_hold_current"
            else:
                if allow_pause:
                    desired_mode = "pause"
                    desired_reason = "no_mode_eligible_pause"
                else:
                    desired_mode = current_mode
                    desired_reason = "no_mode_eligible_hold_current"

        handoff_blocked_running_inventory = False
        target_mode = str(desired_mode)
        target_reason = str(desired_reason)
        if (
            forced_mode is None
            and running_active
            and (running_mode in ("intraday", "swing"))
            and (desired_mode in ("intraday", "swing"))
            and (desired_mode != running_mode)
        ):
            handoff_blocked_running_inventory = True
            target_mode = str(running_mode)
            target_reason = "handoff_blocked_running_inventory"

        persist_bars = max(int(getattr(self, "regime_router_switch_persist_bars", 1)), 1)
        cooldown_bars = max(int(getattr(self, "regime_router_switch_cooldown_bars", 0)), 0)
        tf_secs = 15 * 60
        cooldown_until_ts = int(self._mode_cooldown_until_ts_by_pair.get(pair, 0) or 0)
        cooldown_active = bool(cooldown_until_ts and int(clock_ts) < cooldown_until_ts)

        candidate_mode = self._normalize_mode_name(self._mode_candidate_by_pair.get(pair, current_mode))
        candidate_count = int(self._mode_candidate_count_by_pair.get(pair, 0) or 0)
        switched = False

        if forced_mode is not None:
            switched = bool(current_mode != forced_mode)
            current_mode = self._normalize_mode_name(forced_mode)
            candidate_mode = current_mode
            candidate_count = 0
            cooldown_until_ts = 0
            cooldown_active = False
        elif target_mode == current_mode:
            candidate_mode = target_mode
            candidate_count = 0
        else:
            if target_mode == candidate_mode:
                candidate_count += 1
            else:
                candidate_mode = target_mode
                candidate_count = 1
            if (not cooldown_active) and (candidate_count >= persist_bars):
                current_mode = target_mode
                switched = True
                candidate_mode = current_mode
                candidate_count = 0
                cooldown_until_ts = int(clock_ts) + (cooldown_bars * tf_secs)
                cooldown_active = bool(cooldown_until_ts and int(clock_ts) < cooldown_until_ts)

        self._mode_by_pair[pair] = self._normalize_mode_name(current_mode)
        self._mode_candidate_by_pair[pair] = self._normalize_mode_name(candidate_mode)
        self._mode_candidate_count_by_pair[pair] = int(candidate_count)
        self._mode_cooldown_until_ts_by_pair[pair] = int(cooldown_until_ts)

        active_cfg = self._mode_threshold_block(current_mode)
        return {
            "enabled": bool(enabled),
            "forced_mode": forced_mode,
            "active_mode": self._normalize_mode_name(current_mode),
            "active_cfg": active_cfg,
            "desired_mode": self._normalize_mode_name(desired_mode),
            "desired_reason": str(desired_reason),
            "target_mode": self._normalize_mode_name(target_mode),
            "target_reason": str(target_reason),
            "candidate_mode": self._normalize_mode_name(candidate_mode),
            "candidate_count": int(candidate_count),
            "switch_persist_bars": int(persist_bars),
            "switch_cooldown_bars": int(cooldown_bars),
            "switch_margin": float(margin),
            "switch_cooldown_until_ts": int(cooldown_until_ts) if cooldown_until_ts else None,
            "switch_cooldown_active": bool(cooldown_active),
            "switched": bool(switched),
            "running_active": bool(running_active),
            "running_mode": running_mode if running_mode in ("intraday", "swing", "pause") else None,
            "handoff_blocked_running_inventory": bool(handoff_blocked_running_inventory),
            "scores": {
                "calm_ratio": float(calm_ratio),
                "intraday": dict(intraday_eval, **{"score_adjusted": float(intraday_score_adj)}),
                "swing": dict(swing_eval, **{"score_adjusted": float(swing_score_adj)}),
            },
        }

    def _runmode_name(self) -> str:
        rm = None
        try:
            if getattr(self, "dp", None) is not None and hasattr(self.dp, "runmode"):
                rm = getattr(self.dp, "runmode")
        except Exception:
            rm = None
        if rm is None:
            try:
                rm = (self.config or {}).get("runmode")
            except Exception:
                rm = None
        try:
            if hasattr(rm, "value"):
                rm = rm.value
            return str(rm or "").strip().lower()
        except Exception:
            return ""

    def _should_emit_per_candle_history(self) -> bool:
        if not bool(self.emit_per_candle_history_backtest):
            return False
        rm = self._runmode_name()
        return ("backtest" in rm) or ("hyperopt" in rm)

    def _reset_pair_runtime_state(self, pair: str) -> None:
        stores = [
            self._last_written_ts_by_pair,
            self._last_plan_hash_by_pair,
            self._last_mid_by_pair,
            self._reclaim_until_ts_by_pair,
            self._cooldown_until_ts_by_pair,
            self._active_since_ts_by_pair,
            self._running_by_pair,
            self._bbwp_cooloff_by_pair,
            self._os_dev_state_by_pair,
            self._os_dev_candidate_by_pair,
            self._os_dev_candidate_count_by_pair,
            self._os_dev_zero_persist_by_pair,
            self._mrvd_day_poc_prev_by_pair,
            self._cvd_freeze_bars_left_by_pair,
            self._last_adx_by_pair,
            self._adx_rising_count_by_pair,
            self._mode_by_pair,
            self._mode_candidate_by_pair,
            self._mode_candidate_count_by_pair,
            self._mode_cooldown_until_ts_by_pair,
            self._running_mode_by_pair,
            self._history_emit_end_ts_by_pair,
        ]
        for store in stores:
            store.pop(pair, None)

    @staticmethod
    def _ts_to_iso(ts: Optional[int]) -> Optional[str]:
        if ts is None:
            return None
        try:
            return pd.to_datetime(int(ts), unit="s", utc=True).isoformat()
        except Exception:
            return None

    def _plan_dir(self, exchange_name: str, pair: str) -> str:
        safe_pair = pair.replace("/", "_").replace(":", "_")
        root_rel_env = str(os.getenv("GRID_PLANS_ROOT_REL", "") or "").strip()
        if root_rel_env:
            root_base = (
                root_rel_env
                if os.path.isabs(root_rel_env)
                else os.path.join("/freqtrade/user_data", root_rel_env)
            )
        else:
            root_base = os.path.join("/freqtrade/user_data", self.plans_root_rel)
        return os.path.join(root_base, exchange_name, safe_pair)

    def _write_plan(self, exchange_name: str, pair: str, plan: dict) -> None:
        out_dir = self._plan_dir(exchange_name, pair)
        os.makedirs(out_dir, exist_ok=True)

        ts_safe = None
        cts = plan.get("candle_ts")
        if cts is not None:
            try:
                dt = datetime.fromtimestamp(int(cts), tz=timezone.utc)
                ts_safe = dt.strftime("%Y%m%dT%H%M%S%z")
            except Exception:
                ts_safe = None

        if ts_safe is None:
            ctime = plan.get("candle_time_utc")
            if ctime:
                try:
                    dt = pd.Timestamp(ctime)
                    if dt.tzinfo is None:
                        dt = dt.tz_localize("UTC")
                    else:
                        dt = dt.tz_convert("UTC")
                    ts_safe = dt.strftime("%Y%m%dT%H%M%S%z")
                except Exception:
                    ts_safe = None

        if ts_safe is None:
            ts = plan.get("ts", datetime.now(timezone.utc).isoformat())
            ts_safe = str(ts).replace(":", "").replace("-", "").replace(".", "")

        latest_path = os.path.join(out_dir, "grid_plan.latest.json")
        archive_path = os.path.join(out_dir, f"grid_plan.{ts_safe}.json")

        payload = json.dumps(plan, indent=2, sort_keys=True)

        payload_hash = str(hash(payload))
        last_hash = self._last_plan_hash_by_pair.get(pair)
        if last_hash == payload_hash:
            return

        with open(latest_path, "w", encoding="utf-8") as f:
            f.write(payload)
        with open(archive_path, "w", encoding="utf-8") as f:
            f.write(payload)

        self._last_plan_hash_by_pair[pair] = payload_hash

    def _range_candidate(self, df: DataFrame, lookback: int) -> Tuple[float, float]:
        hi = float(df["high"].rolling(lookback).max().iloc[-1])
        lo = float(df["low"].rolling(lookback).min().iloc[-1])
        return lo, hi

    def _build_box_15m(self, df: DataFrame) -> Tuple[float, float, float, int, float]:
        """
        Build 24h H/L box ± pad (0.35*ATR20 15m) and adjust width into [3.5%..6%]
        deterministically by switching lookback.
        Returns: (lo_p, hi_p, width_pct, used_lookback_bars, pad)
        """
        atr = float(df["atr_15m"].iloc[-1])
        pad = self.atr_pad_mult * atr

        def build_for(lb: int) -> Tuple[float, float, float]:
            lo, hi = self._range_candidate(df, lb)
            lo_p = lo - pad
            hi_p = hi + pad
            mid = (hi_p + lo_p) / 2.0
            width_pct = (hi_p - lo_p) / mid if mid > 0 else 0.0
            return lo_p, hi_p, width_pct

        # Start with 24h
        lo_p, hi_p, w = build_for(self.box_lookback_24h_bars)
        used = self.box_lookback_24h_bars

        # If too narrow, expand to 48h
        if w < self.min_width_pct and len(df) >= self.box_lookback_48h_bars:
            lo_p, hi_p, w = build_for(self.box_lookback_48h_bars)
            used = self.box_lookback_48h_bars

        # If too wide, shrink to 18h then 12h
        if w > self.max_width_pct and len(df) >= self.box_lookback_18h_bars:
            lo_p, hi_p, w = build_for(self.box_lookback_18h_bars)
            used = self.box_lookback_18h_bars

        if w > self.max_width_pct and len(df) >= self.box_lookback_12h_bars:
            lo_p, hi_p, w = build_for(self.box_lookback_12h_bars)
            used = self.box_lookback_12h_bars

        return lo_p, hi_p, w, used, pad

    @staticmethod
    def _bbw_percentile_ok(pct: Optional[float], max_pct: float) -> bool:
        if pct is None or not np.isfinite(float(pct)):
            return False
        return float(pct) <= float(max_pct)

    @staticmethod
    def _bbwp_percentile_last(series: pd.Series, lookback: int) -> Optional[float]:
        if series is None or lookback <= 1 or len(series) < 2:
            return None
        window = series.iloc[-lookback:] if len(series) >= lookback else series
        vals = pd.to_numeric(window, errors="coerce").dropna().astype(float)
        if len(vals) < 2:
            return None
        cur = float(vals.iloc[-1])
        hist = vals.to_numpy(dtype=float)
        return float((np.sum(hist <= cur) / len(hist)) * 100.0)

    @staticmethod
    def _vrvp_profile(df: DataFrame, lookback: int, bins: int, value_area_pct: float) -> Dict[str, Optional[float]]:
        if bins <= 1 or len(df) == 0:
            return {"poc": None, "vah": None, "val": None}

        work = df.iloc[-lookback:] if len(df) >= lookback else df
        lows = pd.to_numeric(work["low"], errors="coerce").to_numpy(dtype=float)
        highs = pd.to_numeric(work["high"], errors="coerce").to_numpy(dtype=float)
        closes = pd.to_numeric(work["close"], errors="coerce").to_numpy(dtype=float)
        vols = pd.to_numeric(work["volume"], errors="coerce").to_numpy(dtype=float)

        if len(lows) == 0:
            return {"poc": None, "vah": None, "val": None}

        pmin = float(np.nanmin(lows))
        pmax = float(np.nanmax(highs))
        if not np.isfinite(pmin) or not np.isfinite(pmax):
            return {"poc": None, "vah": None, "val": None}

        if pmax <= pmin:
            px = float(pmin)
            return {"poc": px, "vah": px, "val": px}

        typ = (highs + lows + closes) / 3.0
        edges = np.linspace(pmin, pmax, bins + 1, dtype=float)
        idx = np.searchsorted(edges, typ, side="right") - 1
        idx = np.clip(idx, 0, bins - 1)

        hist = np.zeros(bins, dtype=float)
        for i, vol in zip(idx, vols):
            if np.isfinite(vol) and vol > 0:
                hist[int(i)] += float(vol)

        if not np.isfinite(hist).all() or float(np.sum(hist)) <= 0:
            px = float((pmin + pmax) / 2.0)
            return {"poc": px, "vah": px, "val": px}

        poc_idx = int(np.argmax(hist))
        total = float(np.sum(hist))
        target = float(np.clip(value_area_pct, 0.0, 1.0) * total)
        left = poc_idx
        right = poc_idx
        acc = float(hist[poc_idx])

        while acc < target and (left > 0 or right < bins - 1):
            lv = float(hist[left - 1]) if left > 0 else -1.0
            rv = float(hist[right + 1]) if right < bins - 1 else -1.0
            if rv > lv:
                right += 1
                acc += float(hist[right])
            else:
                left -= 1
                acc += float(hist[left])

        centers = (edges[:-1] + edges[1:]) / 2.0
        poc = float(centers[poc_idx])
        vah = float(edges[right + 1])
        val = float(edges[left])
        return {"poc": poc, "vah": vah, "val": val}

    @staticmethod
    def _interval_overlap_frac(a_low: float, a_high: float, b_low: float, b_high: float) -> float:
        a0 = float(min(a_low, a_high))
        a1 = float(max(a_low, a_high))
        b0 = float(min(b_low, b_high))
        b1 = float(max(b_low, b_high))
        wa = float(a1 - a0)
        if wa <= 0:
            return 0.0
        inter = max(0.0, min(a1, b1) - max(a0, b0))
        return float(inter / wa)

    @staticmethod
    def _mrvd_profile(df: DataFrame, lookback: int, bins: int, value_area_pct: float) -> Dict:
        out = {
            "lookback_bars": int(max(lookback, 0)),
            "bars_used": 0,
            "poc": None,
            "vah": None,
            "val": None,
            "buy_volume": 0.0,
            "sell_volume": 0.0,
            "buy_sell_ratio": None,
            "buy_sell_imbalance": None,
        }
        if bins <= 1 or len(df) == 0:
            return out

        work = df.iloc[-lookback:] if len(df) >= lookback else df
        out["bars_used"] = int(len(work))
        if len(work) == 0:
            return out

        lows = pd.to_numeric(work["low"], errors="coerce").to_numpy(dtype=float)
        highs = pd.to_numeric(work["high"], errors="coerce").to_numpy(dtype=float)
        closes = pd.to_numeric(work["close"], errors="coerce").to_numpy(dtype=float)
        opens = pd.to_numeric(work["open"], errors="coerce").to_numpy(dtype=float)
        vols = pd.to_numeric(work["volume"], errors="coerce").to_numpy(dtype=float)

        if len(lows) == 0:
            return out

        pmin = float(np.nanmin(lows))
        pmax = float(np.nanmax(highs))
        if not np.isfinite(pmin) or not np.isfinite(pmax):
            return out

        buy_total = 0.0
        sell_total = 0.0
        for o, c, v in zip(opens, closes, vols):
            if not np.isfinite(v) or v <= 0:
                continue
            if np.isfinite(c) and np.isfinite(o) and c >= o:
                buy_total += float(v)
            else:
                sell_total += float(v)

        vol_total = buy_total + sell_total
        ratio = (buy_total / sell_total) if sell_total > 0 else None
        imbalance = ((buy_total - sell_total) / vol_total) if vol_total > 0 else None

        out["buy_volume"] = float(buy_total)
        out["sell_volume"] = float(sell_total)
        out["buy_sell_ratio"] = float(ratio) if ratio is not None else None
        out["buy_sell_imbalance"] = float(imbalance) if imbalance is not None else None

        if pmax <= pmin:
            px = float(pmin)
            out["poc"] = px
            out["vah"] = px
            out["val"] = px
            return out

        typ = (highs + lows + closes) / 3.0
        edges = np.linspace(pmin, pmax, bins + 1, dtype=float)
        idx = np.searchsorted(edges, typ, side="right") - 1
        idx = np.clip(idx, 0, bins - 1)

        hist = np.zeros(bins, dtype=float)
        for i, vol in zip(idx, vols):
            if np.isfinite(vol) and vol > 0:
                hist[int(i)] += float(vol)

        if not np.isfinite(hist).all() or float(np.sum(hist)) <= 0:
            px = float((pmin + pmax) / 2.0)
            out["poc"] = px
            out["vah"] = px
            out["val"] = px
            return out

        poc_idx = int(np.argmax(hist))
        total = float(np.sum(hist))
        target = float(np.clip(value_area_pct, 0.0, 1.0) * total)
        left = poc_idx
        right = poc_idx
        acc = float(hist[poc_idx])

        while acc < target and (left > 0 or right < bins - 1):
            lv = float(hist[left - 1]) if left > 0 else -1.0
            rv = float(hist[right + 1]) if right < bins - 1 else -1.0
            if rv > lv:
                right += 1
                acc += float(hist[right])
            else:
                left -= 1
                acc += float(hist[left])

        centers = (edges[:-1] + edges[1:]) / 2.0
        out["poc"] = float(centers[poc_idx])
        out["vah"] = float(edges[right + 1])
        out["val"] = float(edges[left])
        return out

    @staticmethod
    def _pivot_indices(values: np.ndarray, left: int, right: int, is_low: bool) -> List[int]:
        pivots: List[int] = []
        n = len(values)
        if n == 0:
            return pivots
        left = max(int(left), 1)
        right = max(int(right), 1)
        if n < (left + right + 1):
            return pivots

        for i in range(left, n - right):
            v = values[i]
            if not np.isfinite(v):
                continue
            lwin = values[i - left:i]
            rwin = values[i + 1:i + 1 + right]
            if len(lwin) == 0 or len(rwin) == 0:
                continue
            if not np.isfinite(lwin).all() or not np.isfinite(rwin).all():
                continue
            if is_low:
                if v <= float(np.min(lwin)) and v < float(np.min(rwin)):
                    pivots.append(i)
            else:
                if v >= float(np.max(lwin)) and v > float(np.max(rwin)):
                    pivots.append(i)
        return pivots

    def _cvd_state(
        self,
        df: DataFrame,
        lookback: int,
        step_price: float,
        box_low: float,
        box_high: float,
        close: float,
        vrvp_val: Optional[float],
        vrvp_vah: Optional[float],
    ) -> Dict:
        out = {
            "enabled": bool(self.cvd_enabled),
            "lookback_bars": int(lookback),
            "bars_used": 0,
            "cvd": None,
            "cvd_delta": None,
            "near_bottom": False,
            "near_top": False,
            "bull_divergence": False,
            "bear_divergence": False,
            "bull_divergence_near_bottom": False,
            "bear_divergence_near_top": False,
            "bos_up": False,
            "bos_down": False,
            "bos_up_near_bottom": False,
            "bos_down_near_top": False,
            "price_pivot_low_prev": None,
            "price_pivot_low_last": None,
            "price_pivot_high_prev": None,
            "price_pivot_high_last": None,
            "cvd_pivot_low_prev": None,
            "cvd_pivot_low_last": None,
            "cvd_pivot_high_prev": None,
            "cvd_pivot_high_last": None,
            "freeze_bars_left": 0,
            "freeze_active": False,
            "gate_ok": True,
        }
        if not self.cvd_enabled:
            return out

        lb = max(int(lookback), 16)
        work = df.iloc[-lb:] if len(df) >= lb else df
        out["bars_used"] = int(len(work))
        if len(work) < max(self.cvd_bos_lookback + 2, (self.cvd_pivot_left + self.cvd_pivot_right + 3)):
            return out

        lows = pd.to_numeric(work["low"], errors="coerce").to_numpy(dtype=float)
        highs = pd.to_numeric(work["high"], errors="coerce").to_numpy(dtype=float)
        cvd_src = work["cvd_15m"] if "cvd_15m" in work.columns else pd.Series(np.nan, index=work.index)
        cvd_delta_src = (
            work["cvd_delta_15m"] if "cvd_delta_15m" in work.columns else pd.Series(np.nan, index=work.index)
        )
        cvd = pd.to_numeric(cvd_src, errors="coerce").to_numpy(dtype=float)
        cvd_delta = pd.to_numeric(cvd_delta_src, errors="coerce").to_numpy(dtype=float)
        if len(cvd) == 0 or not np.isfinite(cvd[-1]):
            return out

        out["cvd"] = float(cvd[-1])
        if len(cvd_delta) > 0 and np.isfinite(cvd_delta[-1]):
            out["cvd_delta"] = float(cvd_delta[-1])

        near_thr = max(float(self.cvd_near_value_steps) * max(step_price, 0.0), 0.0)
        low_ref = float(vrvp_val) if vrvp_val is not None else float(box_low)
        high_ref = float(vrvp_vah) if vrvp_vah is not None else float(box_high)
        near_bottom = bool(close <= (low_ref + near_thr))
        near_top = bool(close >= (high_ref - near_thr))
        out["near_bottom"] = bool(near_bottom)
        out["near_top"] = bool(near_top)

        low_piv = self._pivot_indices(lows, self.cvd_pivot_left, self.cvd_pivot_right, is_low=True)
        if len(low_piv) >= 2:
            i1, i2 = low_piv[-2], low_piv[-1]
            out["price_pivot_low_prev"] = float(lows[i1]) if np.isfinite(lows[i1]) else None
            out["price_pivot_low_last"] = float(lows[i2]) if np.isfinite(lows[i2]) else None
            out["cvd_pivot_low_prev"] = float(cvd[i1]) if np.isfinite(cvd[i1]) else None
            out["cvd_pivot_low_last"] = float(cvd[i2]) if np.isfinite(cvd[i2]) else None
            if (
                np.isfinite(lows[i1])
                and np.isfinite(lows[i2])
                and np.isfinite(cvd[i1])
                and np.isfinite(cvd[i2])
                and ((len(lows) - 1 - i2) <= int(max(self.cvd_divergence_max_age_bars, 1)))
            ):
                bull_div = bool((lows[i2] < lows[i1]) and (cvd[i2] > cvd[i1]))
                out["bull_divergence"] = bool(bull_div)
                out["bull_divergence_near_bottom"] = bool(bull_div and near_bottom)

        high_piv = self._pivot_indices(highs, self.cvd_pivot_left, self.cvd_pivot_right, is_low=False)
        if len(high_piv) >= 2:
            i1, i2 = high_piv[-2], high_piv[-1]
            out["price_pivot_high_prev"] = float(highs[i1]) if np.isfinite(highs[i1]) else None
            out["price_pivot_high_last"] = float(highs[i2]) if np.isfinite(highs[i2]) else None
            out["cvd_pivot_high_prev"] = float(cvd[i1]) if np.isfinite(cvd[i1]) else None
            out["cvd_pivot_high_last"] = float(cvd[i2]) if np.isfinite(cvd[i2]) else None
            if (
                np.isfinite(highs[i1])
                and np.isfinite(highs[i2])
                and np.isfinite(cvd[i1])
                and np.isfinite(cvd[i2])
                and ((len(highs) - 1 - i2) <= int(max(self.cvd_divergence_max_age_bars, 1)))
            ):
                bear_div = bool((highs[i2] > highs[i1]) and (cvd[i2] < cvd[i1]))
                out["bear_divergence"] = bool(bear_div)
                out["bear_divergence_near_top"] = bool(bear_div and near_top)

        bos_lb = int(max(self.cvd_bos_lookback, 2))
        if len(cvd) >= bos_lb + 1 and np.isfinite(cvd[-1]) and np.isfinite(cvd[-2]):
            prev = cvd[-(bos_lb + 1):-1]
            prev_fin = prev[np.isfinite(prev)]
            if len(prev_fin) > 0:
                prev_max = float(np.max(prev_fin))
                prev_min = float(np.min(prev_fin))
                cur = float(cvd[-1])
                prv = float(cvd[-2])
                bos_up = bool(cur > prev_max and prv <= prev_max)
                bos_down = bool(cur < prev_min and prv >= prev_min)
                out["bos_up"] = bool(bos_up)
                out["bos_down"] = bool(bos_down)
                out["bos_up_near_bottom"] = bool(bos_up and near_bottom)
                out["bos_down_near_top"] = bool(bos_down and near_top)

        return out

    @staticmethod
    def _apply_cvd_rung_bias(
        levels: np.ndarray,
        rung_weights: List[float],
        box_low: float,
        box_high: float,
        bull_div_near_bottom: bool,
        bear_div_near_top: bool,
        strength: float,
        w_min: float,
        w_max: float,
    ) -> List[float]:
        if len(levels) == 0:
            return []
        if len(rung_weights) != len(levels):
            return [float(x) for x in rung_weights]
        if not bull_div_near_bottom and not bear_div_near_top:
            return [float(x) for x in rung_weights]

        width = float(box_high - box_low)
        if width <= 0:
            return [float(x) for x in rung_weights]

        lev = np.array(levels, dtype=float)
        w = np.array(rung_weights, dtype=float)
        pos = np.clip((lev - float(box_low)) / width, 0.0, 1.0)

        s = max(float(strength), 0.0)
        mult = np.ones_like(w)
        if bull_div_near_bottom:
            mult *= (1.0 + s * (1.0 - pos))
        if bear_div_near_top:
            mult *= (1.0 + s * pos)

        out = np.clip(w * mult, float(w_min), float(w_max))
        return [float(x) for x in out.tolist()]

    def _find_numeric_row(
        self,
        row: pd.Series,
        exact: Optional[List[str]] = None,
        contains: Optional[List[str]] = None,
    ) -> Optional[float]:
        exact = exact or []
        contains = contains or []
        idx_map = {str(c).lower(): c for c in row.index}

        for key in exact:
            c = idx_map.get(str(key).lower())
            if c is None:
                continue
            v = self._safe_float(row.get(c))
            if v is not None:
                return v

        if contains:
            for c in row.index:
                lc = str(c).lower()
                if any(token in lc for token in contains):
                    v = self._safe_float(row.get(c))
                    if v is not None:
                        return v
        return None

    def _freqai_overlay_state(
        self,
        last_row: pd.Series,
        close: float,
        step_price: float,
        q1: float,
        q2: float,
        q3: float,
        vrvp_poc: Optional[float],
    ) -> Dict:
        out = {
            "enabled": bool(self.freqai_overlay_enabled),
            "source": "none",
            "do_predict": None,
            "p_range": None,
            "p_breakout": None,
            "ml_confidence": None,
            "strict_predict": bool(self.freqai_overlay_strict_predict),
            "gate_ok": True,
            "breakout_risk_high": False,
            "quick_tp_candidate": None,
        }
        if not self.freqai_overlay_enabled:
            return out

        do_predict_raw = self._find_numeric_row(
            last_row,
            exact=["do_predict", "freqai_do_predict", "predict_ok"],
            contains=["do_predict"],
        )
        do_predict = None
        if do_predict_raw is not None:
            do_predict = 1 if float(do_predict_raw) >= 0.5 else 0

        p_range = self._find_numeric_row(
            last_row,
            exact=["p_range", "prob_range", "range_probability", "&-p_range", "&-s_range"],
            contains=["p_range", "range_prob"],
        )
        p_breakout = self._find_numeric_row(
            last_row,
            exact=["p_breakout", "prob_breakout", "breakout_probability"],
            contains=["p_breakout", "breakout_prob"],
        )
        ml_conf = self._find_numeric_row(
            last_row,
            exact=["ml_confidence", "freqai_confidence", "do_predict_prob", "prediction_confidence"],
            contains=["ml_confidence", "predict_prob", "confidence"],
        )

        source = "none"
        if p_range is not None or p_breakout is not None:
            source = "prob_columns"

        if p_range is None and p_breakout is None:
            s_close = self._find_numeric_row(
                last_row,
                exact=["&-s_close", "s_close", "&-target"],
                contains=["&-s_close", "s_close"],
            )
            if s_close is not None:
                scale = max(float(self.freqai_overlay_breakout_scale), 1e-9)
                pb = float(np.clip(abs(float(s_close)) / scale, 0.0, 1.0))
                p_breakout = pb
                p_range = float(1.0 - pb)
                source = "s_close_proxy"

        if p_range is not None:
            p_range = float(np.clip(p_range, 0.0, 1.0))
        if p_breakout is not None:
            p_breakout = float(np.clip(p_breakout, 0.0, 1.0))
        if p_range is not None and p_breakout is not None:
            s = float(p_range + p_breakout)
            if s > 0:
                p_range = float(p_range / s)
                p_breakout = float(p_breakout / s)

        if ml_conf is not None:
            ml_conf = float(np.clip(ml_conf, 0.0, 1.0))
        elif p_range is not None or p_breakout is not None:
            ml_conf = float(max(p_range or 0.0, p_breakout or 0.0))
        elif do_predict is not None:
            ml_conf = float(1.0 if do_predict == 1 else 0.0)

        gate_ok = True
        if self.freqai_overlay_strict_predict:
            gate_ok = bool(
                do_predict == 1
                and ml_conf is not None
                and ml_conf >= float(self.freqai_overlay_confidence_min)
            )

        breakout_risk_high = bool(
            p_breakout is not None and p_breakout >= float(self.freqai_overlay_breakout_quick_tp_thresh)
        )
        quick_tp_candidate = None
        if breakout_risk_high:
            candidates: List[float] = []
            for px in [vrvp_poc, q2, q1, q3]:
                pxf = self._safe_float(px)
                if pxf is not None and pxf > close:
                    candidates.append(float(pxf))
            if candidates:
                quick_tp_candidate = float(min(candidates))

        out["source"] = source
        out["do_predict"] = do_predict
        out["p_range"] = p_range
        out["p_breakout"] = p_breakout
        out["ml_confidence"] = ml_conf
        out["gate_ok"] = bool(gate_ok)
        out["breakout_risk_high"] = bool(breakout_risk_high)
        out["quick_tp_candidate"] = quick_tp_candidate
        return out

    @staticmethod
    def _apply_ml_rung_safety(
        levels: np.ndarray,
        rung_weights: List[float],
        box_low: float,
        box_high: float,
        p_breakout: Optional[float],
        edge_cut_max: float,
        w_min: float,
        w_max: float,
    ) -> List[float]:
        if p_breakout is None:
            return [float(x) for x in rung_weights]
        if len(levels) == 0 or len(rung_weights) != len(levels):
            return [float(x) for x in rung_weights]
        width = float(box_high - box_low)
        if width <= 0:
            return [float(x) for x in rung_weights]

        risk = float(np.clip(p_breakout, 0.0, 1.0))
        cut = float(max(edge_cut_max, 0.0))
        if risk <= 0 or cut <= 0:
            return [float(x) for x in rung_weights]

        lev = np.array(levels, dtype=float)
        w = np.array(rung_weights, dtype=float)
        pos = np.clip((lev - float(box_low)) / width, 0.0, 1.0)
        edge = np.abs(pos - 0.5) * 2.0
        mult = 1.0 - (risk * cut * edge)
        mult = np.clip(mult, 0.05, 1.0)

        out = np.clip(w * mult, float(w_min), float(w_max))
        return [float(x) for x in out.tolist()]

    @staticmethod
    def _os_dev_from_history(
        closes: np.ndarray,
        mid: float,
        half_span: float,
        range_band: float,
        n_strike: int,
    ) -> Tuple[int, int, int, int]:
        """
        Rebuild os_dev state from historical closes.
        This keeps behavior deterministic in batch backtests where in-memory
        strike counters may not advance candle-by-candle.
        """
        if len(closes) == 0 or half_span <= 0:
            return 0, 0, 0, 0

        state = 0
        candidate = 0
        candidate_count = 0
        zero_persist = 0
        n_strike = max(int(n_strike), 1)

        for c in closes:
            if not np.isfinite(c):
                continue
            norm = (float(c) - float(mid)) / float(half_span)
            raw = 1 if norm > float(range_band) else (-1 if norm < -float(range_band) else 0)

            if raw == state:
                candidate = state
                candidate_count = 0
            else:
                if candidate == raw:
                    candidate_count += 1
                else:
                    candidate = raw
                    candidate_count = 1
                if candidate_count >= n_strike:
                    state = int(raw)
                    candidate = state
                    candidate_count = 0

            if state == 0:
                zero_persist += 1
            else:
                zero_persist = 0

        return int(state), int(candidate), int(candidate_count), int(zero_persist)

    @staticmethod
    def _micro_vap_inside_box(
        df: DataFrame,
        lookback: int,
        bins: int,
        box_low: float,
        box_high: float,
        hvn_quantile: float,
        lvn_quantile: float,
        extrema_count: int,
    ) -> Dict:
        out = {
            "poc": None,
            "hvn_levels": [],
            "lvn_levels": [],
            "density": [],
            "edges": [],
            "lvn_density_threshold": None,
            "top_void": 0.0,
            "bottom_void": 0.0,
            "void_slope": 0.0,
        }
        if bins <= 1 or box_high <= box_low or len(df) == 0:
            return out

        work = df.iloc[-lookback:] if len(df) >= lookback else df
        highs = pd.to_numeric(work["high"], errors="coerce").to_numpy(dtype=float)
        lows = pd.to_numeric(work["low"], errors="coerce").to_numpy(dtype=float)
        closes = pd.to_numeric(work["close"], errors="coerce").to_numpy(dtype=float)
        vols = pd.to_numeric(work["volume"], errors="coerce").to_numpy(dtype=float)
        typ = (highs + lows + closes) / 3.0

        mask = np.isfinite(typ) & np.isfinite(vols) & (vols > 0) & (typ >= box_low) & (typ <= box_high)
        if np.sum(mask) < 2:
            return out

        typ = typ[mask]
        vols = vols[mask]

        edges = np.linspace(float(box_low), float(box_high), int(bins) + 1, dtype=float)
        idx = np.searchsorted(edges, typ, side="right") - 1
        idx = np.clip(idx, 0, int(bins) - 1)
        hist = np.zeros(int(bins), dtype=float)
        for i, vol in zip(idx, vols):
            hist[int(i)] += float(vol)

        total = float(np.sum(hist))
        if total <= 0:
            return out

        dens = hist / total
        centers = (edges[:-1] + edges[1:]) / 2.0
        poc_idx = int(np.argmax(dens))
        poc = float(centers[poc_idx])

        hvn_q = float(np.clip(hvn_quantile, 0.0, 1.0))
        lvn_q = float(np.clip(lvn_quantile, 0.0, 1.0))
        hvn_thr = float(np.quantile(dens, hvn_q))
        lvn_thr = float(np.quantile(dens, lvn_q))

        hvn_idx = np.where(dens >= hvn_thr)[0]
        lvn_idx = np.where(dens <= lvn_thr)[0]

        max_n = max(int(extrema_count), 1)
        if len(hvn_idx) > max_n:
            hvn_idx = hvn_idx[np.argsort(dens[hvn_idx])[-max_n:]]
        if len(lvn_idx) > max_n:
            lvn_idx = lvn_idx[np.argsort(dens[lvn_idx])[:max_n]]

        hvn_levels = sorted([float(centers[i]) for i in hvn_idx])
        lvn_levels = sorted([float(centers[i]) for i in lvn_idx])

        edge_bins = max(2, int(round(int(bins) * 0.12)))
        edge_bins = min(edge_bins, int(bins))
        global_mean = float(np.mean(dens))
        top_mean = float(np.mean(dens[-edge_bins:]))
        bottom_mean = float(np.mean(dens[:edge_bins]))
        if global_mean > 0:
            top_void = float(np.clip((global_mean - top_mean) / global_mean, 0.0, 1.0))
            bottom_void = float(np.clip((global_mean - bottom_mean) / global_mean, 0.0, 1.0))
        else:
            top_void = 0.0
            bottom_void = 0.0
        void_slope = float(max(top_void, bottom_void))

        out["poc"] = poc
        out["hvn_levels"] = hvn_levels
        out["lvn_levels"] = lvn_levels
        out["density"] = [float(x) for x in dens.tolist()]
        out["edges"] = [float(x) for x in edges.tolist()]
        out["lvn_density_threshold"] = float(lvn_thr)
        out["top_void"] = top_void
        out["bottom_void"] = bottom_void
        out["void_slope"] = void_slope
        return out

    @staticmethod
    def _rung_weights_from_micro_vap(
        levels: np.ndarray,
        edges: List[float],
        density: List[float],
        lvn_density_threshold: Optional[float],
        hvn_boost: float,
        lvn_penalty: float,
        w_min: float,
        w_max: float,
    ) -> List[float]:
        n = len(levels)
        if n == 0:
            return []

        try:
            edges_arr = np.array(edges, dtype=float)
            dens_arr = np.array(density, dtype=float)
        except Exception:
            return [1.0] * n

        if len(edges_arr) != len(dens_arr) + 1 or len(dens_arr) == 0:
            return [1.0] * n

        lev = np.array(levels, dtype=float)
        idx = np.searchsorted(edges_arr, lev, side="right") - 1
        idx = np.clip(idx, 0, len(dens_arr) - 1)
        d = dens_arr[idx]

        mean_d = float(np.mean(dens_arr))
        std_d = float(np.std(dens_arr))
        if std_d <= 1e-12:
            z = np.zeros_like(d)
        else:
            z = (d - mean_d) / std_d

        w = 1.0 + float(hvn_boost) * np.maximum(z, 0.0)
        if lvn_density_threshold is not None:
            mask_lvn = d <= float(lvn_density_threshold)
            w = np.where(mask_lvn, w * float(lvn_penalty), w)

        w = np.clip(w, float(w_min), float(w_max))
        return [float(x) for x in w.tolist()]

    def _fvg_stack_state(
        self,
        df: DataFrame,
        lookback: int,
        step_price: float,
        box_low: float,
        box_high: float,
        close: float,
    ) -> Dict:
        out = {
            "enabled": bool(self.fvg_enabled),
            "lookback_bars": int(lookback),
            "count_total": 0,
            "count_bull": 0,
            "count_bear": 0,
            "count_defensive_bull": 0,
            "count_defensive_bear": 0,
            "count_session": 0,
            "nearest_bullish": None,
            "nearest_bearish": None,
            "nearest_defensive_bullish": None,
            "nearest_defensive_bearish": None,
            "straddle_veto_bull": False,
            "straddle_veto_bear": False,
            "straddle_veto": False,
            "imfvg_relax_applied_bull": False,
            "imfvg_relax_applied_bear": False,
            "defensive_bull_conflict": False,
            "defensive_bear_conflict": False,
            "defensive_conflict": False,
            "fresh_defensive_pause": False,
            "session_new_print": False,
            "session_pause_active": False,
            "session_inside_block": False,
            "session_gate_ok": True,
            "gate_ok": True,
            "imfvg_avg_bull": None,
            "imfvg_avg_bear": None,
            "session_fvg_avg": None,
            "positioning_up_avg": None,
            "positioning_down_avg": None,
        }

        if not self.fvg_enabled:
            return out

        if len(df) < 3:
            out["gate_ok"] = False
            out["session_gate_ok"] = False
            return out

        lb = max(int(lookback), 3)
        work = df.iloc[-(lb + 3):] if len(df) > (lb + 3) else df
        n = len(work)
        if n < 3:
            out["gate_ok"] = False
            out["session_gate_ok"] = False
            return out

        highs = pd.to_numeric(work["high"], errors="coerce").to_numpy(dtype=float)
        lows = pd.to_numeric(work["low"], errors="coerce").to_numpy(dtype=float)
        opens = pd.to_numeric(work["open"], errors="coerce").to_numpy(dtype=float)
        closes = pd.to_numeric(work["close"], errors="coerce").to_numpy(dtype=float)
        atr_src = work["atr_15m"] if "atr_15m" in work.columns else pd.Series(np.nan, index=work.index)
        atrs = pd.to_numeric(atr_src, errors="coerce").to_numpy(dtype=float)

        if "date" in work.columns:
            dates = pd.to_datetime(work["date"], utc=True, errors="coerce").to_numpy()
        else:
            dates = pd.to_datetime(work.index, utc=True, errors="coerce").to_numpy()

        last_session = None
        if len(dates) > 0:
            try:
                last_dt = pd.Timestamp(dates[-1])
                if not pd.isna(last_dt):
                    last_session = last_dt.floor("D")
            except Exception:
                last_session = None

        zones: List[Dict] = []
        for i in range(2, n):
            h2 = highs[i - 2]
            l2 = lows[i - 2]
            hi = highs[i]
            lo = lows[i]
            if not np.isfinite(h2) or not np.isfinite(l2) or not np.isfinite(hi) or not np.isfinite(lo):
                continue

            side = None
            z_low = None
            z_high = None

            if lo > h2:
                side = "bull"
                z_low = float(h2)
                z_high = float(lo)
            elif hi < l2:
                side = "bear"
                z_low = float(hi)
                z_high = float(l2)
            else:
                continue

            if z_high <= z_low:
                continue

            gap = float(z_high - z_low)
            atr_ref = float(atrs[i]) if i < len(atrs) and np.isfinite(atrs[i]) and atrs[i] > 0 else None
            gap_atr = (gap / atr_ref) if atr_ref is not None else None
            if gap_atr is not None and gap_atr < float(self.fvg_min_gap_atr):
                continue

            if i - 1 >= 0 and np.isfinite(highs[i - 1]) and np.isfinite(lows[i - 1]):
                r = float(highs[i - 1] - lows[i - 1])
                b = abs(float(closes[i - 1] - opens[i - 1])) if np.isfinite(closes[i - 1]) and np.isfinite(opens[i - 1]) else 0.0
                body_frac = (b / r) if r > 0 else 0.0
                imp_up = bool(closes[i - 1] > opens[i - 1]) if np.isfinite(closes[i - 1]) and np.isfinite(opens[i - 1]) else False
                imp_dn = bool(closes[i - 1] < opens[i - 1]) if np.isfinite(closes[i - 1]) and np.isfinite(opens[i - 1]) else False
            else:
                body_frac = 0.0
                imp_up = False
                imp_dn = False

            defensive = bool(
                self.defensive_fvg_enabled
                and gap_atr is not None
                and gap_atr >= float(self.defensive_fvg_min_gap_atr)
                and body_frac >= float(self.defensive_fvg_body_frac)
                and ((side == "bull" and imp_up) or (side == "bear" and imp_dn))
            )

            mitigated = False
            filled = False
            if i + 1 < n:
                post_l = lows[i + 1:]
                post_h = highs[i + 1:]
                if side == "bull":
                    mitigated = bool(np.any(post_l <= z_high))
                    filled = bool(np.any(post_l <= z_low))
                else:
                    mitigated = bool(np.any(post_h >= z_low))
                    filled = bool(np.any(post_h >= z_high))

            bars_ago = int((n - 1) - i)
            session_match = False
            if last_session is not None:
                try:
                    zi = pd.Timestamp(dates[i])
                    session_match = bool(not pd.isna(zi) and zi.floor("D") == last_session)
                except Exception:
                    session_match = False

            zones.append(
                {
                    "side": side,
                    "low": float(z_low),
                    "high": float(z_high),
                    "mid": float((z_low + z_high) / 2.0),
                    "gap": float(gap),
                    "gap_atr": float(gap_atr) if gap_atr is not None else None,
                    "bars_ago": int(bars_ago),
                    "mitigated": bool(mitigated),
                    "filled": bool(filled),
                    "defensive": bool(defensive),
                    "session_match": bool(session_match),
                }
            )

        if not zones:
            out["gate_ok"] = True
            out["session_gate_ok"] = True
            return out

        bull = [z for z in zones if z["side"] == "bull"]
        bear = [z for z in zones if z["side"] == "bear"]
        def_bull = [z for z in bull if z["defensive"]]
        def_bear = [z for z in bear if z["defensive"]]
        session_zones = [z for z in zones if z["session_match"]]

        out["count_total"] = int(len(zones))
        out["count_bull"] = int(len(bull))
        out["count_bear"] = int(len(bear))
        out["count_defensive_bull"] = int(len(def_bull))
        out["count_defensive_bear"] = int(len(def_bear))
        out["count_session"] = int(len(session_zones))

        def nearest(zs: List[Dict], edge: float, edge_key: str) -> Optional[Dict]:
            if not zs:
                return None
            return min(zs, key=lambda z: abs(float(edge) - float(z[edge_key])))

        def zone_view(z: Optional[Dict]) -> Optional[Dict]:
            if z is None:
                return None
            return {
                "low": float(z["low"]),
                "high": float(z["high"]),
                "mid": float(z["mid"]),
                "gap_atr": z["gap_atr"],
                "bars_ago": int(z["bars_ago"]),
                "mitigated": bool(z["mitigated"]),
                "filled": bool(z["filled"]),
                "defensive": bool(z["defensive"]),
                "session_match": bool(z["session_match"]),
            }

        near_bull = nearest([z for z in bull if not z["filled"]], box_low, "high")
        near_bear = nearest([z for z in bear if not z["filled"]], box_high, "low")
        near_def_bull = nearest([z for z in def_bull if not z["mitigated"]], box_low, "high")
        near_def_bear = nearest([z for z in def_bear if not z["mitigated"]], box_high, "low")

        out["nearest_bullish"] = zone_view(near_bull)
        out["nearest_bearish"] = zone_view(near_bear)
        out["nearest_defensive_bullish"] = zone_view(near_def_bull)
        out["nearest_defensive_bearish"] = zone_view(near_def_bear)

        near_limit = float(max(0.0, self.fvg_straddle_veto_steps * max(step_price, 0.0)))

        def zone_conflict(z: Optional[Dict], edge_price: float, edge_key: str) -> bool:
            if z is None:
                return False
            overlap = min(float(z["high"]), float(box_high)) - max(float(z["low"]), float(box_low))
            inside_or_overlap = bool(overlap > 0.0)
            if inside_or_overlap:
                return True
            if near_limit <= 0:
                return False
            dist = abs(float(edge_price) - float(z[edge_key]))
            return bool(dist <= near_limit)

        bull_conflict_raw = zone_conflict(near_bull, box_low, "high")
        bear_conflict_raw = zone_conflict(near_bear, box_high, "low")

        relax_bull = bool(
            self.imfvg_enabled
            and self.imfvg_mitigated_relax
            and near_bull is not None
            and bool(near_bull["mitigated"])
        )
        relax_bear = bool(
            self.imfvg_enabled
            and self.imfvg_mitigated_relax
            and near_bear is not None
            and bool(near_bear["mitigated"])
        )
        bull_conflict = bool(bull_conflict_raw and not relax_bull)
        bear_conflict = bool(bear_conflict_raw and not relax_bear)
        out["straddle_veto_bull"] = bool(bull_conflict)
        out["straddle_veto_bear"] = bool(bear_conflict)
        out["straddle_veto"] = bool(bull_conflict or bear_conflict)
        out["imfvg_relax_applied_bull"] = bool(relax_bull and bull_conflict_raw)
        out["imfvg_relax_applied_bear"] = bool(relax_bear and bear_conflict_raw)

        def_bull_conflict = zone_conflict(near_def_bull, box_low, "high")
        def_bear_conflict = zone_conflict(near_def_bear, box_high, "low")
        out["defensive_bull_conflict"] = bool(def_bull_conflict)
        out["defensive_bear_conflict"] = bool(def_bear_conflict)
        out["defensive_conflict"] = bool(def_bull_conflict or def_bear_conflict)

        fresh_pause = False
        for z in def_bull + def_bear:
            if z["mitigated"]:
                continue
            if int(z["bars_ago"]) > int(self.defensive_fvg_fresh_bars):
                continue
            if z["side"] == "bull":
                if zone_conflict(z, box_low, "high"):
                    fresh_pause = True
                    break
            elif z["side"] == "bear":
                if zone_conflict(z, box_high, "low"):
                    fresh_pause = True
                    break
        out["fresh_defensive_pause"] = bool(fresh_pause)

        session_new_print = bool(any(int(z["bars_ago"]) == 0 for z in session_zones))
        inside_session = bool(
            any((not z["mitigated"]) and (float(z["low"]) <= float(close) <= float(z["high"])) for z in session_zones)
        )
        session_pause_bars = max(int(self.session_fvg_pause_bars), 0)
        session_pause_active = bool(
            self.session_fvg_enabled
            and session_pause_bars > 0
            and any(int(z["bars_ago"]) < session_pause_bars for z in session_zones)
        )
        session_inside_block = bool(self.session_fvg_enabled and self.session_fvg_inside_gate and inside_session)
        session_gate_ok = bool(not session_pause_active and not session_inside_block)

        out["session_new_print"] = bool(session_new_print)
        out["session_pause_active"] = bool(session_pause_active)
        out["session_inside_block"] = bool(session_inside_block)
        out["session_gate_ok"] = bool(session_gate_ok)

        imfvg_bull = [float(z["mid"]) for z in bull if z["mitigated"]]
        imfvg_bear = [float(z["mid"]) for z in bear if z["mitigated"]]
        sess_mid = [float(z["mid"]) for z in session_zones]

        out["imfvg_avg_bull"] = float(np.mean(imfvg_bull)) if len(imfvg_bull) else None
        out["imfvg_avg_bear"] = float(np.mean(imfvg_bear)) if len(imfvg_bear) else None
        out["session_fvg_avg"] = float(np.mean(sess_mid)) if len(sess_mid) else None

        up_edges = [float(z["high"]) for z in bull]
        dn_edges = [float(z["low"]) for z in bear]
        if len(up_edges):
            out["positioning_up_avg"] = float(np.mean(up_edges[-int(self.fvg_position_avg_count):]))
        if len(dn_edges):
            out["positioning_down_avg"] = float(np.mean(dn_edges[-int(self.fvg_position_avg_count):]))

        out["gate_ok"] = bool(
            not out["straddle_veto"]
            and not out["defensive_conflict"]
            and not out["fresh_defensive_pause"]
            and out["session_gate_ok"]
        )
        return out

    def _grid_sizing(self, lo_p: float, hi_p: float) -> Tuple[int, float, float, float]:
        """
        Choose N in [6..12] so step >= gross_step_min
        gross_step_min = net + fee + spread
        Returns: (n_levels, step_price, step_pct_actual, gross_step_min_pct)
        """
        mid = (hi_p + lo_p) / 2.0
        width_pct = (hi_p - lo_p) / mid if mid > 0 else 0.0

        gross_min = self.target_net_step_pct + self.est_fee_pct + self.est_spread_pct

        if gross_min <= 0:
            n = self.n_min
        else:
            n_cap = int(np.floor(width_pct / gross_min))
            n = int(np.clip(n_cap, self.n_min, self.n_max))

        step_price = (hi_p - lo_p) / float(n) if n > 0 else 0.0
        step_pct_actual = (step_price / mid) if mid > 0 else 0.0
        return n, step_price, step_pct_actual, gross_min

    def _breakout_flags(self, close: float, lo_p: float, hi_p: float, step: float) -> Dict[str, bool]:
        close_outside_up = close > hi_p
        close_outside_dn = close < lo_p
        fast_up = (close - hi_p) > (self.fast_stop_step_multiple * step)
        fast_dn = (lo_p - close) > (self.fast_stop_step_multiple * step)
        return {
            "close_outside_up": close_outside_up,
            "close_outside_dn": close_outside_dn,
            "fast_outside_up": fast_up,
            "fast_outside_dn": fast_dn,
        }

    # ========== Main indicators + plan write ==========
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pair = metadata.get("pair", "UNKNOWN/UNKNOWN")

        # ---- 15m indicators ----
        dataframe["atr_15m"] = ta.ATR(dataframe, timeperiod=self.atr_period_15m)
        dataframe["rsi_15m"] = ta.RSI(dataframe, timeperiod=self.rsi_period_15m)
        tp_15m = qtpylib.typical_price(dataframe)
        bb_15m = qtpylib.bollinger_bands(tp_15m, window=self.bb_window, stds=self.bb_stds)
        dataframe["bb_mid_15m"] = bb_15m["mid"]
        dataframe["bb_upper_15m"] = bb_15m["upper"]
        dataframe["bb_lower_15m"] = bb_15m["lower"]
        dataframe["bb_width_15m"] = (dataframe["bb_upper_15m"] - dataframe["bb_lower_15m"]) / dataframe["bb_mid_15m"]
        dataframe["vol_sma20_15m"] = dataframe["volume"].rolling(self.rvol_window_15m).mean()
        dataframe["rvol_15m"] = dataframe["volume"] / dataframe["vol_sma20_15m"]
        sign_body = np.sign(pd.to_numeric(dataframe["close"], errors="coerce") - pd.to_numeric(dataframe["open"], errors="coerce"))
        sign_fallback = np.sign(pd.to_numeric(dataframe["close"], errors="coerce").diff().fillna(0.0))
        sign_eff = np.where(sign_body != 0.0, sign_body, sign_fallback)
        dataframe["cvd_delta_15m"] = pd.to_numeric(dataframe["volume"], errors="coerce").fillna(0.0) * sign_eff
        dataframe["cvd_15m"] = dataframe["cvd_delta_15m"].cumsum()

        # Use rolling VWAP to avoid lookahead bias in backtesting/runtime checks.
        dataframe["vwap_15m"] = qtpylib.rolling_vwap(
            dataframe,
            window=self.box_lookback_24h_bars,
            min_periods=1,
        )

        # 7d extremes on 15m
        dataframe["hi_7d"] = dataframe["high"].rolling(self.extremes_7d_bars).max()
        dataframe["lo_7d"] = dataframe["low"].rolling(self.extremes_7d_bars).min()

        # Need enough data
        if len(dataframe) < self.startup_candle_count:
            return dataframe

        history_mode = bool(self._should_emit_per_candle_history())
        history_in_progress = bool(self._history_emit_in_progress_by_pair.get(pair, False))
        if history_mode and not history_in_progress:
            frame_end_ts = None
            try:
                dt_last = pd.Timestamp(dataframe["date"].iloc[-1])
                if dt_last.tzinfo is None:
                    dt_last = dt_last.tz_localize("UTC")
                else:
                    dt_last = dt_last.tz_convert("UTC")
                frame_end_ts = int(dt_last.timestamp())
            except Exception:
                frame_end_ts = None

            prev_emitted_end = self._history_emit_end_ts_by_pair.get(pair)
            if frame_end_ts is not None and prev_emitted_end == frame_end_ts:
                return dataframe

            self._history_emit_in_progress_by_pair[pair] = True
            try:
                self._reset_pair_runtime_state(pair)
                start_idx = max(int(self.startup_candle_count) - 1, 0)
                for i in range(start_idx, len(dataframe)):
                    frame = dataframe.iloc[: i + 1].copy()
                    self.populate_indicators(frame, metadata)
            finally:
                self._history_emit_in_progress_by_pair[pair] = False
            if frame_end_ts is not None:
                self._history_emit_end_ts_by_pair[pair] = int(frame_end_ts)
            return dataframe

        last = dataframe.iloc[-1]
        close = float(last["close"])
        rsi = self._safe_float(last.get("rsi_15m"))
        vwap = self._safe_float(last.get("vwap_15m"))
        gate_cfg = self._gate_profile_values()
        gate_profile = str(gate_cfg.get("profile", "strict"))
        gate_adx_4h_max = float(gate_cfg.get("adx_4h_max", self.adx_4h_max))
        gate_adx_4h_exit_min = float(gate_adx_4h_max)
        gate_adx_4h_exit_max = float(gate_adx_4h_exit_min)
        gate_adx_rising_bars = 1
        gate_bbw_1h_pct_max = float(gate_cfg.get("bbw_1h_pct_max", self.bbw_1h_pct_max))
        gate_ema_dist_max_frac = float(gate_cfg.get("ema_dist_max_frac", self.ema_dist_max_frac))
        gate_vol_spike_mult = float(gate_cfg.get("vol_spike_mult", self.vol_spike_mult))
        gate_bbwp_s_enter_low = 0.0
        gate_bbwp_s_enter_high = float(gate_cfg.get("bbwp_s_max", self.bbwp_s_max))
        gate_bbwp_m_enter_low = 0.0
        gate_bbwp_m_enter_high = float(gate_cfg.get("bbwp_m_max", self.bbwp_m_max))
        gate_bbwp_l_enter_low = 0.0
        gate_bbwp_l_enter_high = float(gate_cfg.get("bbwp_l_max", self.bbwp_l_max))
        gate_bbwp_s_max = float(gate_bbwp_s_enter_high)
        gate_bbwp_m_max = float(gate_bbwp_m_enter_high)
        gate_bbwp_l_max = float(gate_bbwp_l_enter_high)
        gate_bbwp_stop_high = float(gate_cfg.get("bbwp_veto_pct", self.bbwp_veto_pct))
        gate_bbwp_veto_pct = float(gate_cfg.get("bbwp_veto_pct", self.bbwp_veto_pct))
        gate_bbwp_cooloff_trigger_pct = float(gate_cfg.get("bbwp_cooloff_trigger_pct", self.bbwp_cooloff_trigger_pct))
        gate_bbwp_cooloff_release_s = float(gate_cfg.get("bbwp_cooloff_release_s", self.bbwp_cooloff_release_s))
        gate_bbwp_cooloff_release_m = float(gate_cfg.get("bbwp_cooloff_release_m", self.bbwp_cooloff_release_m))
        gate_atr_source = "1h"
        gate_atr_pct_max = float(self.intraday_atr_pct_max)
        gate_os_dev_persist_bars = int(gate_cfg.get("os_dev_persist_bars", self.os_dev_persist_bars))
        gate_os_dev_rvol_max = float(gate_cfg.get("os_dev_rvol_max", self.os_dev_rvol_max))
        gate_start_min_pass_ratio = float(gate_cfg.get("start_min_gate_pass_ratio", 1.0))
        active_mode = self._normalize_mode_name(getattr(self, "regime_router_default_mode", "intraday"))
        mode_cfg: Dict[str, float] = self._mode_threshold_block(active_mode)
        router_state: Dict[str, object] = {}
        router_clock_ts = int(datetime.now(timezone.utc).timestamp())
        try:
            if "date" in dataframe.columns:
                router_dt = pd.Timestamp(last["date"])
                if router_dt.tzinfo is None:
                    router_dt = router_dt.tz_localize("UTC")
                else:
                    router_dt = router_dt.tz_convert("UTC")
                router_clock_ts = int(router_dt.timestamp())
            elif isinstance(dataframe.index, pd.DatetimeIndex):
                router_dt = pd.Timestamp(dataframe.index[-1])
                if router_dt.tzinfo is None:
                    router_dt = router_dt.tz_localize("UTC")
                else:
                    router_dt = router_dt.tz_convert("UTC")
                router_clock_ts = int(router_dt.timestamp())
        except Exception:
            pass

        # ---- pull informative columns (1h / 4h) ----
        adx4h = None
        if "adx_4h_4h" in dataframe.columns:
            adx4h = self._safe_float(last.get("adx_4h_4h"))
        elif "adx_4h" in dataframe.columns:
            adx4h = self._safe_float(last.get("adx_4h"))

        bbw15m = self._safe_float(last.get("bb_width_15m"))
        rvol_15m = self._safe_float(last.get("rvol_15m"))
        bbw1h = None
        bbw4h = None
        ema50 = None
        ema100 = None
        atr_1h = None
        atr_4h = None
        plus_di_4h = None
        minus_di_4h = None
        vol_1h = None
        vol_sma20 = None
        squeeze_on_1h = None
        squeeze_released_1h = False

        bbw1h_col = None
        bbw4h_col = None
        squeeze_col = None
        for c in dataframe.columns:
            if bbw1h_col is None and (c.endswith("bb_width_1h_1h") or c == "bb_width_1h"):
                bbw1h_col = c
            if bbw4h_col is None and (c.endswith("bb_width_4h_4h") or c == "bb_width_4h"):
                bbw4h_col = c
            if c.endswith("ema50_1h_1h"):
                ema50 = self._safe_float(last.get(c))
            if c.endswith("ema100_1h_1h"):
                ema100 = self._safe_float(last.get(c))
            if c.endswith("atr_1h_1h"):
                atr_1h = self._safe_float(last.get(c))
            if c.endswith("atr_4h_4h"):
                atr_4h = self._safe_float(last.get(c))
            if c.endswith("plus_di_4h_4h") or c == "plus_di_4h":
                plus_di_4h = self._safe_float(last.get(c))
            if c.endswith("minus_di_4h_4h") or c == "minus_di_4h":
                minus_di_4h = self._safe_float(last.get(c))
            if c.endswith("vol_sma20_1h_1h"):
                vol_sma20 = self._safe_float(last.get(c))
            if squeeze_col is None and (c.endswith("squeeze_on_1h_1h") or c == "squeeze_on_1h"):
                squeeze_col = c

        if bbw1h_col:
            bbw1h = self._safe_float(last.get(bbw1h_col))
        if bbw4h_col:
            bbw4h = self._safe_float(last.get(bbw4h_col))
        if squeeze_col:
            sq = self._safe_float(last.get(squeeze_col))
            if sq is not None:
                squeeze_on_1h = bool(sq >= 0.5)
                if len(dataframe) > 1:
                    sq_prev = self._safe_float(dataframe[squeeze_col].iloc[-2])
                    if sq_prev is not None:
                        squeeze_released_1h = bool(sq_prev >= 0.5 and sq < 0.5)

        if "volume_1h_1h" in dataframe.columns:
            vol_1h = self._safe_float(last.get("volume_1h_1h"))
        elif "volume_1h" in dataframe.columns:
            vol_1h = self._safe_float(last.get("volume_1h"))

        atr_1h_pct = (atr_1h / close) if (atr_1h is not None and close > 0.0) else None
        atr_4h_pct = (atr_4h / close) if (atr_4h is not None and close > 0.0) else None

        # BBW gate on 1h (rolling percentile on pair's own history).
        bbw1h_pct = self._bbwp_percentile_last(dataframe[bbw1h_col], self.bbw_pct_lookback_1h) if bbw1h_col else None

        # EMA distance gate (1h)
        ema_dist_ok = False
        ema_dist_frac = None
        if ema50 is not None and ema100 is not None and close > 0:
            ema_dist_frac = abs(ema50 - ema100) / close
            ema_dist_ok = ema_dist_frac <= gate_ema_dist_max_frac

        # 1h volume gate
        vol_ok = False
        vol_ratio = None
        if vol_1h is not None and vol_sma20 is not None and vol_sma20 > 0:
            vol_ratio = vol_1h / vol_sma20
            vol_ok = vol_ratio <= gate_vol_spike_mult

        adx_rising_count = int(self._adx_rising_count_by_pair.get(pair, 0) or 0)
        prev_adx = self._safe_float(self._last_adx_by_pair.get(pair))
        if adx4h is not None:
            if prev_adx is None:
                adx_rising_count = 0
            elif adx4h > (prev_adx + 1e-9):
                adx_rising_count = int(adx_rising_count + 1)
            elif adx4h < (prev_adx - 1e-9):
                adx_rising_count = 0
            self._last_adx_by_pair[pair] = float(adx4h)
            self._adx_rising_count_by_pair[pair] = int(adx_rising_count)

        # BBWP raw percentiles (S=15m, M=1h, L=4h).
        bbwp_s = self._bbwp_percentile_last(dataframe["bb_width_15m"], self.bbwp_lookback_s)
        bbwp_m = self._bbwp_percentile_last(dataframe[bbw1h_col], self.bbwp_lookback_m) if bbw1h_col else None
        bbwp_l = self._bbwp_percentile_last(dataframe[bbw4h_col], self.bbwp_lookback_l) if bbw4h_col else None
        bbwp_cooloff = bool(self._bbwp_cooloff_by_pair.get(pair, False))

        # Regime router picks intraday/swing mode from raw features, then activates mode thresholds.
        running_active_hint = bool(self._running_by_pair.get(pair, False))
        running_mode_hint = None
        if running_active_hint:
            running_mode_hint = self._normalize_mode_name(self._running_mode_by_pair.get(pair))
        router_features = {
            "adx_4h": adx4h,
            "bb_width_1h_pct": bbw1h_pct,
            "ema_dist_frac_1h": ema_dist_frac,
            "vol_ratio_1h": vol_ratio,
            "bbwp_15m_pct": bbwp_s,
            "bbwp_1h_pct": bbwp_m,
            "bbwp_4h_pct": bbwp_l,
            "atr_1h_pct": atr_1h_pct,
            "atr_4h_pct": atr_4h_pct,
            "rvol_15m": rvol_15m,
            "running_active": running_active_hint,
            "running_mode": running_mode_hint,
        }
        router_state = self._regime_router_state(pair, router_clock_ts, router_features)
        active_mode = str(router_state.get("active_mode", active_mode))
        desired_mode = str(router_state.get("desired_mode", active_mode))
        mode_cfg_raw = router_state.get("active_cfg")
        if isinstance(mode_cfg_raw, dict):
            mode_cfg = dict(mode_cfg_raw)
        gate_adx_4h_max = float(mode_cfg.get("adx_enter_max", gate_adx_4h_max))
        gate_adx_4h_exit_min = float(mode_cfg.get("adx_exit_min", gate_adx_4h_exit_min))
        gate_adx_4h_exit_max = float(mode_cfg.get("adx_exit_max", gate_adx_4h_exit_min))
        gate_adx_rising_bars = int(mode_cfg.get("adx_rising_bars", gate_adx_rising_bars))
        gate_bbw_1h_pct_max = float(mode_cfg.get("bbw_1h_pct_max", gate_bbw_1h_pct_max))
        gate_ema_dist_max_frac = float(mode_cfg.get("ema_dist_max_frac", gate_ema_dist_max_frac))
        gate_vol_spike_mult = float(mode_cfg.get("vol_spike_mult", gate_vol_spike_mult))
        gate_bbwp_s_enter_low = float(mode_cfg.get("bbwp_s_enter_low", gate_bbwp_s_enter_low))
        gate_bbwp_s_enter_high = float(mode_cfg.get("bbwp_s_enter_high", gate_bbwp_s_enter_high))
        gate_bbwp_m_enter_low = float(mode_cfg.get("bbwp_m_enter_low", gate_bbwp_m_enter_low))
        gate_bbwp_m_enter_high = float(mode_cfg.get("bbwp_m_enter_high", gate_bbwp_m_enter_high))
        gate_bbwp_l_enter_low = float(mode_cfg.get("bbwp_l_enter_low", gate_bbwp_l_enter_low))
        gate_bbwp_l_enter_high = float(mode_cfg.get("bbwp_l_enter_high", gate_bbwp_l_enter_high))
        gate_bbwp_s_max = float(mode_cfg.get("bbwp_s_max", gate_bbwp_s_enter_high))
        gate_bbwp_m_max = float(mode_cfg.get("bbwp_m_max", gate_bbwp_m_enter_high))
        gate_bbwp_l_max = float(mode_cfg.get("bbwp_l_max", gate_bbwp_l_enter_high))
        gate_bbwp_stop_high = float(mode_cfg.get("bbwp_stop_high", gate_bbwp_stop_high))
        gate_atr_source = str(mode_cfg.get("atr_source", gate_atr_source)).strip().lower()
        gate_atr_pct_max = float(mode_cfg.get("atr_pct_max", gate_atr_pct_max))
        gate_os_dev_persist_bars = int(mode_cfg.get("os_dev_persist_bars", gate_os_dev_persist_bars))
        gate_os_dev_rvol_max = float(mode_cfg.get("os_dev_rvol_max", gate_os_dev_rvol_max))

        # Apply active mode thresholds.
        mode_pause = bool(active_mode == "pause")
        bbw_nonexp = self._bbw_percentile_ok(bbw1h_pct, gate_bbw_1h_pct_max)
        ema_dist_ok = False
        if ema_dist_frac is not None:
            ema_dist_ok = bool(ema_dist_frac <= gate_ema_dist_max_frac)
        vol_ok = False
        if vol_ratio is not None:
            vol_ok = bool(vol_ratio <= gate_vol_spike_mult)
        atr_mode_pct = atr_4h_pct if gate_atr_source == "4h" else atr_1h_pct
        atr_ok = bool(atr_mode_pct is not None and atr_mode_pct <= gate_atr_pct_max)

        # 4h ADX gate / hysteresis signal.
        adx_rising_confirmed = bool(adx_rising_count >= int(max(gate_adx_rising_bars, 1)))
        adx_ok = (adx4h is not None) and (adx4h <= gate_adx_4h_max)
        adx_exit_overheat = self._adx_exit_hysteresis_trigger(
            adx4h,
            adx_rising_count,
            gate_adx_4h_exit_min,
            gate_adx_rising_bars,
        )
        adx_di_up = bool(
            plus_di_4h is not None and minus_di_4h is not None and plus_di_4h > minus_di_4h
        )
        adx_di_down = bool(
            plus_di_4h is not None and minus_di_4h is not None and minus_di_4h > plus_di_4h
        )
        adx_di_down_risk_stop = self._adx_di_down_risk_trigger(
            adx4h,
            plus_di_4h,
            minus_di_4h,
            adx_rising_count,
            gate_adx_4h_exit_min,
            gate_adx_rising_bars,
            early_margin=2.0,
        )

        # BBWP gate (active mode thresholds + global veto/cooloff).
        if self.bbwp_enabled:
            bbwp_vals = [x for x in [bbwp_s, bbwp_m, bbwp_l] if x is not None]
            bbwp_expansion_stop = any(x >= gate_bbwp_stop_high for x in bbwp_vals)
            bbwp_veto = any(x >= min(gate_bbwp_veto_pct, gate_bbwp_stop_high) for x in bbwp_vals)
            if any(x >= gate_bbwp_cooloff_trigger_pct for x in bbwp_vals):
                bbwp_cooloff = True
            if (
                bbwp_cooloff
                and bbwp_s is not None
                and bbwp_m is not None
                and bbwp_s < gate_bbwp_cooloff_release_s
                and bbwp_m < gate_bbwp_cooloff_release_m
            ):
                bbwp_cooloff = False
            self._bbwp_cooloff_by_pair[pair] = bbwp_cooloff

            bbwp_allow = bool(
                bbwp_s is not None
                and bbwp_m is not None
                and bbwp_l is not None
                and gate_bbwp_s_enter_low <= bbwp_s <= gate_bbwp_s_enter_high
                and gate_bbwp_m_enter_low <= bbwp_m <= gate_bbwp_m_enter_high
                and gate_bbwp_l_enter_low <= bbwp_l <= gate_bbwp_l_enter_high
            )
            bbwp_gate_ok = bool(bbwp_allow and not bbwp_veto and not bbwp_cooloff)
        else:
            bbwp_allow = True
            bbwp_veto = False
            bbwp_cooloff = False
            bbwp_expansion_stop = False
            bbwp_gate_ok = True

        # 7d containment (15m)
        hi7d = self._safe_float(last.get("hi_7d"))
        lo7d = self._safe_float(last.get("lo_7d"))
        inside_7d = True
        if hi7d is not None and lo7d is not None:
            inside_7d = (close <= hi7d) and (close >= lo7d)

        # ---- Build box on 15m ----
        lo_p, hi_p, width_pct, used_lb, pad = self._build_box_15m(dataframe)

        # VRVP POC/VAH/VAL + deterministic box shift toward POC.
        vrvp = self._vrvp_profile(dataframe, self.vrvp_lookback_bars, self.vrvp_bins, self.vrvp_value_area_pct)
        vrvp_poc = self._safe_float(vrvp.get("poc"))
        vrvp_vah = self._safe_float(vrvp.get("vah"))
        vrvp_val = self._safe_float(vrvp.get("val"))
        vrvp_box_shift = 0.0
        vrvp_dist_frac = None
        vrvp_poc_inside_box = False

        if vrvp_poc is not None:
            pre_mid = (hi_p + lo_p) / 2.0
            max_shift = self.vrvp_max_box_shift_frac * pre_mid if pre_mid > 0 else 0.0
            if vrvp_poc > hi_p and max_shift > 0:
                shift = min(vrvp_poc - hi_p, max_shift)
                lo_p += shift
                hi_p += shift
                vrvp_box_shift = float(shift)
            elif vrvp_poc < lo_p and max_shift > 0:
                shift = min(lo_p - vrvp_poc, max_shift)
                lo_p -= shift
                hi_p -= shift
                vrvp_box_shift = float(-shift)

            post_mid = (hi_p + lo_p) / 2.0
            if lo_p <= vrvp_poc <= hi_p:
                vrvp_poc_inside_box = True
                vrvp_dist_frac = 0.0
            else:
                dist = (vrvp_poc - hi_p) if vrvp_poc > hi_p else (lo_p - vrvp_poc)
                vrvp_dist_frac = (dist / post_mid) if post_mid > 0 else None

        vrvp_box_ok = True
        if self.vrvp_reject_if_still_outside and vrvp_poc is not None and vrvp_dist_frac is not None:
            vrvp_box_ok = bool(vrvp_dist_frac <= self.vrvp_poc_outside_box_max_frac)

        # Quartiles
        mid = (hi_p + lo_p) / 2.0
        width_pct = (hi_p - lo_p) / mid if mid > 0 else 0.0
        q1 = lo_p + 0.25 * (hi_p - lo_p)
        q2 = mid
        q3 = lo_p + 0.75 * (hi_p - lo_p)

        # ---- Grid sizing ----
        n_levels, step_price, step_pct_actual, gross_min = self._grid_sizing(lo_p, hi_p)
        tp_price = hi_p + (self.tp_step_multiple * step_price)
        sl_price = lo_p - (self.sl_step_multiple * step_price)

        # MRVD (day/week/month) profile gates + drift pause.
        mrvd_day = self._mrvd_profile(
            dataframe, self.mrvd_day_lookback_bars, self.mrvd_bins, self.mrvd_value_area_pct
        ) if self.mrvd_enabled else {}
        mrvd_week = self._mrvd_profile(
            dataframe, self.mrvd_week_lookback_bars, self.mrvd_bins, self.mrvd_value_area_pct
        ) if self.mrvd_enabled else {}
        mrvd_month = self._mrvd_profile(
            dataframe, self.mrvd_month_lookback_bars, self.mrvd_bins, self.mrvd_value_area_pct
        ) if self.mrvd_enabled else {}

        def mrvd_period_state(profile: Dict) -> Dict:
            poc = self._safe_float(profile.get("poc"))
            vah = self._safe_float(profile.get("vah"))
            val = self._safe_float(profile.get("val"))
            va_overlap_frac = 0.0
            if vah is not None and val is not None:
                va_overlap_frac = self._interval_overlap_frac(val, vah, lo_p, hi_p)
            poc_dist_steps = None
            near_poc = False
            if poc is not None and step_price > 0:
                poc_dist_steps = abs(close - poc) / step_price
                near_poc = bool(poc_dist_steps <= float(self.mrvd_near_poc_steps))
            return {
                "lookback_bars": int(profile.get("lookback_bars", 0) or 0),
                "bars_used": int(profile.get("bars_used", 0) or 0),
                "poc": poc,
                "vah": vah,
                "val": val,
                "buy_volume": float(profile.get("buy_volume", 0.0) or 0.0),
                "sell_volume": float(profile.get("sell_volume", 0.0) or 0.0),
                "buy_sell_ratio": self._safe_float(profile.get("buy_sell_ratio")),
                "buy_sell_imbalance": self._safe_float(profile.get("buy_sell_imbalance")),
                "va_overlap_frac": float(va_overlap_frac),
                "poc_dist_steps": poc_dist_steps,
                "near_poc": bool(near_poc),
            }

        mrvd_day_state = mrvd_period_state(mrvd_day) if self.mrvd_enabled else {
            "lookback_bars": 0,
            "bars_used": 0,
            "poc": None,
            "vah": None,
            "val": None,
            "buy_volume": 0.0,
            "sell_volume": 0.0,
            "buy_sell_ratio": None,
            "buy_sell_imbalance": None,
            "va_overlap_frac": 0.0,
            "poc_dist_steps": None,
            "near_poc": False,
        }
        mrvd_week_state = mrvd_period_state(mrvd_week) if self.mrvd_enabled else dict(mrvd_day_state)
        mrvd_month_state = mrvd_period_state(mrvd_month) if self.mrvd_enabled else dict(mrvd_day_state)

        mrvd_period_states = [mrvd_day_state, mrvd_week_state, mrvd_month_state]
        mrvd_overlap_count = int(
            sum(float(x.get("va_overlap_frac", 0.0) or 0.0) >= float(self.mrvd_va_overlap_min_frac) for x in mrvd_period_states)
        ) if self.mrvd_enabled else int(self.mrvd_required_overlap_count)
        mrvd_overlap_ok = bool(mrvd_overlap_count >= int(self.mrvd_required_overlap_count))
        mrvd_near_any_poc = bool(any(bool(x.get("near_poc", False)) for x in mrvd_period_states)) if self.mrvd_enabled else True

        mrvd_day_poc_prev = self._mrvd_day_poc_prev_by_pair.get(pair)
        mrvd_day_poc = self._safe_float(mrvd_day_state.get("poc"))
        mrvd_week_poc = self._safe_float(mrvd_week_state.get("poc"))
        mrvd_month_poc = self._safe_float(mrvd_month_state.get("poc"))

        mrvd_day_poc_step_move = None
        if mrvd_day_poc_prev is not None and mrvd_day_poc is not None and step_price > 0:
            mrvd_day_poc_step_move = abs(float(mrvd_day_poc) - float(mrvd_day_poc_prev)) / step_price

        mrvd_drift_anchor_prev = None
        mrvd_drift_anchor_cur = None
        mrvd_drift_delta_steps = None
        mrvd_drift_guard_triggered = False
        if self.mrvd_enabled and self.mrvd_drift_guard_enabled and mrvd_day_poc_prev is not None and mrvd_day_poc is not None:
            anchors = [x for x in [mrvd_week_poc, mrvd_month_poc] if x is not None]
            if len(anchors) > 0:
                prev_dist = float(np.mean([abs(float(mrvd_day_poc_prev) - float(a)) for a in anchors]))
                cur_dist = float(np.mean([abs(float(mrvd_day_poc) - float(a)) for a in anchors]))
                mrvd_drift_anchor_prev = prev_dist
                mrvd_drift_anchor_cur = cur_dist
                if step_price > 0:
                    mrvd_drift_delta_steps = (cur_dist - prev_dist) / step_price
                    mrvd_drift_guard_triggered = bool(mrvd_drift_delta_steps >= float(self.mrvd_drift_guard_steps))

        if mrvd_day_poc is not None:
            self._mrvd_day_poc_prev_by_pair[pair] = float(mrvd_day_poc)

        mrvd_pause_entries = bool(self.mrvd_enabled and mrvd_drift_guard_triggered)
        mrvd_gate_ok = bool(
            (not self.mrvd_enabled) or ((mrvd_overlap_ok or mrvd_near_any_poc) and not mrvd_pause_entries)
        )

        # FreqAI confidence overlay (soft nudges only).
        ml_overlay = self._freqai_overlay_state(
            last,
            close,
            step_price,
            q1,
            q2,
            q3,
            vrvp_poc,
        )
        p_range = self._safe_float(ml_overlay.get("p_range"))
        p_breakout = self._safe_float(ml_overlay.get("p_breakout"))
        ml_confidence = self._safe_float(ml_overlay.get("ml_confidence"))
        ml_gate_ok = bool(ml_overlay.get("gate_ok", True))
        ml_quick_tp_candidate = self._safe_float(ml_overlay.get("quick_tp_candidate"))
        ml_breakout_risk_high = bool(ml_overlay.get("breakout_risk_high", False))
        ml_do_predict = ml_overlay.get("do_predict")
        ml_source = str(ml_overlay.get("source", "none"))

        # CVD divergence/BOS module.
        cvd_state = self._cvd_state(
            dataframe,
            self.cvd_lookback_bars,
            step_price,
            lo_p,
            hi_p,
            close,
            vrvp_val,
            vrvp_vah,
        )
        cvd_bos_against_range = bool(
            (bool(cvd_state.get("bos_up", False)) and bool(cvd_state.get("near_top", False)))
            or (bool(cvd_state.get("bos_down", False)) and bool(cvd_state.get("near_bottom", False)))
        )
        cvd_freeze_prev = int(self._cvd_freeze_bars_left_by_pair.get(pair, 0) or 0)
        cvd_freeze_left = max(cvd_freeze_prev - 1, 0)
        if cvd_bos_against_range:
            cvd_freeze_left = int(max(self.cvd_bos_freeze_bars, 1))
        self._cvd_freeze_bars_left_by_pair[pair] = int(cvd_freeze_left)
        cvd_freeze_active = bool(cvd_freeze_left > 0)
        cvd_state["freeze_bars_left"] = int(cvd_freeze_left)
        cvd_state["freeze_active"] = bool(cvd_freeze_active)
        cvd_gate_ok = bool((not self.cvd_enabled) or (not cvd_freeze_active))

        cvd_quick_tp_trigger = bool(
            bool(cvd_state.get("bos_up_near_bottom", False)) or bool(cvd_state.get("bos_down_near_top", False))
        )
        cvd_quick_tp_candidate = None
        if cvd_quick_tp_trigger:
            quick_tp_pool: List[float] = []
            for px in [vrvp_poc, q2, q1, q3]:
                pxf = self._safe_float(px)
                if pxf is not None and pxf > close:
                    quick_tp_pool.append(float(pxf))
            if len(quick_tp_pool):
                cvd_quick_tp_candidate = float(min(quick_tp_pool))

        # FVG stack (Defensive + IMFVG + Session FVG).
        fvg_state = self._fvg_stack_state(
            dataframe,
            self.fvg_lookback_bars,
            step_price,
            lo_p,
            hi_p,
            close,
        )
        fvg_gate_ok = bool((not self.fvg_enabled) or bool(fvg_state.get("gate_ok", False)))
        fvg_straddle_veto = bool(fvg_state.get("straddle_veto", False))
        fvg_defensive_conflict = bool(fvg_state.get("defensive_conflict", False))
        fvg_fresh_pause = bool(fvg_state.get("fresh_defensive_pause", False))
        session_fvg_pause_active = bool(fvg_state.get("session_pause_active", False))
        session_fvg_inside_block = bool(fvg_state.get("session_inside_block", False))

        tp_candidates = {
            "base_tp": float(tp_price),
            "imfvg_avg_bull": self._safe_float(fvg_state.get("imfvg_avg_bull")),
            "imfvg_avg_bear": self._safe_float(fvg_state.get("imfvg_avg_bear")),
            "session_fvg_avg": self._safe_float(fvg_state.get("session_fvg_avg")),
            "fvg_position_up_avg": self._safe_float(fvg_state.get("positioning_up_avg")),
            "fvg_position_down_avg": self._safe_float(fvg_state.get("positioning_down_avg")),
            "mrvd_day_poc": mrvd_day_poc,
            "mrvd_week_poc": mrvd_week_poc,
            "mrvd_month_poc": mrvd_month_poc,
            "cvd_quick_tp_candidate": cvd_quick_tp_candidate,
            "cvd_quick_tp_trigger": bool(cvd_quick_tp_trigger),
            "ml_quick_tp_candidate": ml_quick_tp_candidate,
            "ml_breakout_risk_high": bool(ml_breakout_risk_high),
            "ml_p_range": p_range,
            "ml_p_breakout": p_breakout,
        }
        tp_price_plan = float(tp_price)
        if cvd_quick_tp_candidate is not None:
            tp_price_plan = float(min(tp_price_plan, cvd_quick_tp_candidate))
        if ml_quick_tp_candidate is not None:
            tp_price_plan = float(min(tp_price_plan, ml_quick_tp_candidate))

        # Micro-VAP inside current box.
        micro_vap = self._micro_vap_inside_box(
            dataframe,
            self.micro_vap_lookback_bars,
            self.micro_vap_bins,
            lo_p,
            hi_p,
            self.micro_hvn_quantile,
            self.micro_lvn_quantile,
            self.micro_extrema_count,
        ) if self.micro_vap_enabled else {
            "poc": None,
            "hvn_levels": [],
            "lvn_levels": [],
            "density": [],
            "edges": [],
            "lvn_density_threshold": None,
            "top_void": 0.0,
            "bottom_void": 0.0,
            "void_slope": 0.0,
        }

        micro_poc = self._safe_float(micro_vap.get("poc"))
        micro_hvn_levels = [float(x) for x in (micro_vap.get("hvn_levels") or [])]
        micro_lvn_levels = [float(x) for x in (micro_vap.get("lvn_levels") or [])]
        micro_top_void = float(self._safe_float(micro_vap.get("top_void")) or 0.0)
        micro_bottom_void = float(self._safe_float(micro_vap.get("bottom_void")) or 0.0)
        micro_void_slope = float(self._safe_float(micro_vap.get("void_slope")) or 0.0)

        levels_arr = np.linspace(lo_p, hi_p, n_levels + 1, dtype=float)
        rung_weights = self._rung_weights_from_micro_vap(
            levels_arr,
            micro_vap.get("edges") or [],
            micro_vap.get("density") or [],
            self._safe_float(micro_vap.get("lvn_density_threshold")),
            self.rung_weight_hvn_boost,
            self.rung_weight_lvn_penalty,
            self.rung_weight_min,
            self.rung_weight_max,
        )
        rung_weights = self._apply_cvd_rung_bias(
            levels_arr,
            rung_weights,
            lo_p,
            hi_p,
            bool(cvd_state.get("bull_divergence_near_bottom", False)),
            bool(cvd_state.get("bear_divergence_near_top", False)),
            self.cvd_rung_bias_strength,
            self.rung_weight_min,
            self.rung_weight_max,
        )
        rung_weights = self._apply_ml_rung_safety(
            levels_arr,
            rung_weights,
            lo_p,
            hi_p,
            p_breakout,
            self.freqai_overlay_rung_edge_cut_max,
            self.rung_weight_min,
            self.rung_weight_max,
        )
        micro_poc_vrvp_steps = None
        if micro_poc is not None and vrvp_poc is not None and step_price > 0:
            micro_poc_vrvp_steps = abs(micro_poc - vrvp_poc) / step_price

        # os_dev regime state with strike confirmation.
        os_dev_raw = 0
        os_dev_norm = None
        half_span = (hi_p - lo_p) / 2.0
        if half_span > 0:
            os_dev_norm = (close - mid) / half_span
            if os_dev_norm > self.os_dev_range_band:
                os_dev_raw = 1
            elif os_dev_norm < -self.os_dev_range_band:
                os_dev_raw = -1

        os_dev_state = int(self._os_dev_state_by_pair.get(pair, 0))
        os_dev_candidate = int(self._os_dev_candidate_by_pair.get(pair, os_dev_state))
        os_dev_candidate_count = int(self._os_dev_candidate_count_by_pair.get(pair, 0))
        os_dev_zero_persist = int(self._os_dev_zero_persist_by_pair.get(pair, 0))

        if self.os_dev_enabled:
            close_hist = pd.to_numeric(dataframe["close"], errors="coerce").to_numpy(dtype=float)
            hist_bars = max(int(self.os_dev_history_bars), int(self.os_dev_persist_bars), 1)
            if len(close_hist) > hist_bars:
                close_hist = close_hist[-hist_bars:]

            os_dev_state, os_dev_candidate, os_dev_candidate_count, os_dev_zero_persist = self._os_dev_from_history(
                close_hist,
                mid,
                half_span,
                self.os_dev_range_band,
                self.os_dev_n_strike,
            )

            self._os_dev_state_by_pair[pair] = int(os_dev_state)
            self._os_dev_candidate_by_pair[pair] = int(os_dev_candidate)
            self._os_dev_candidate_count_by_pair[pair] = int(os_dev_candidate_count)
            self._os_dev_zero_persist_by_pair[pair] = int(os_dev_zero_persist)

            os_dev_rvol_ok = bool(rvol_15m is not None and rvol_15m <= gate_os_dev_rvol_max)
            os_dev_build_ok = bool(
                os_dev_state == 0 and os_dev_zero_persist >= gate_os_dev_persist_bars and os_dev_rvol_ok
            )
            os_dev_trend_stop = bool(os_dev_state != 0)
        else:
            os_dev_rvol_ok = True
            os_dev_build_ok = True
            os_dev_trend_stop = False

        # Squeeze gate and release stop trigger.
        squeeze_gate_ok = True
        if self.squeeze_enabled and self.squeeze_require_on_1h:
            squeeze_gate_ok = bool(squeeze_on_1h)
        squeeze_release_break_stop = bool(
            self.squeeze_enabled
            and squeeze_released_1h
            and ((close > (hi_p + step_price)) or (close < (lo_p - step_price)))
        )

        # ---- Stop logic (15m) ----
        flags = self._breakout_flags(close, lo_p, hi_p, step_price)

        c1 = float(dataframe["close"].iloc[-1])
        c2 = float(dataframe["close"].iloc[-2])
        two_up = (c1 > hi_p) and (c2 > hi_p)
        two_dn = (c1 < lo_p) and (c2 < lo_p)

        prev_mid = self._last_mid_by_pair.get(pair)
        shift_stop = False
        shift_frac = None
        if prev_mid is not None and prev_mid > 0:
            shift_frac = abs(mid - prev_mid) / prev_mid
            shift_stop = shift_frac >= self.range_shift_stop_pct
        running_mode_prev = None
        if running_active_hint:
            running_mode_prev = self._normalize_mode_name(self._running_mode_by_pair.get(pair))
        mode_handoff_required_stop = bool(
            running_active_hint
            and (running_mode_prev in ("intraday", "swing"))
            and (desired_mode in ("intraday", "swing"))
            and (desired_mode != running_mode_prev)
        )
        router_pause_stop = bool(running_active_hint and mode_pause)

        lvn_corridor_width = max(self.micro_lvn_corridor_steps * step_price, 0.0)
        upper_edge_lvn = any(abs(float(x) - hi_p) <= lvn_corridor_width for x in micro_lvn_levels)
        lower_edge_lvn = any(abs(float(x) - lo_p) <= lvn_corridor_width for x in micro_lvn_levels)
        lvn_corridor_stop_up = bool(
            flags["close_outside_up"]
            and upper_edge_lvn
            and micro_void_slope >= self.micro_void_slope_threshold
        )
        lvn_corridor_stop_dn = bool(
            flags["close_outside_dn"]
            and lower_edge_lvn
            and micro_void_slope >= self.micro_void_slope_threshold
        )
        lvn_corridor_stop_override = bool(lvn_corridor_stop_up or lvn_corridor_stop_dn)
        fvg_conflict_stop_up = bool(flags["close_outside_up"] and bool(fvg_state.get("defensive_bear_conflict", False)))
        fvg_conflict_stop_dn = bool(flags["close_outside_dn"] and bool(fvg_state.get("defensive_bull_conflict", False)))
        fvg_conflict_stop_override = bool(fvg_conflict_stop_up or fvg_conflict_stop_dn)
        stop_reason_flags_raw = {
            "two_consecutive_outside_up": bool(two_up),
            "two_consecutive_outside_dn": bool(two_dn),
            "fast_outside_up": bool(flags["fast_outside_up"]),
            "fast_outside_dn": bool(flags["fast_outside_dn"]),
            "adx_hysteresis_stop": bool(adx_exit_overheat),
            "adx_di_down_risk_stop": bool(adx_di_down_risk_stop),
            "bbwp_expansion_stop": bool(bbwp_expansion_stop),
            "squeeze_release_break_stop": bool(squeeze_release_break_stop),
            "os_dev_trend_stop": bool(os_dev_trend_stop),
            "lvn_corridor_stop_override": bool(lvn_corridor_stop_override),
            "lvn_corridor_stop_up": bool(lvn_corridor_stop_up),
            "lvn_corridor_stop_dn": bool(lvn_corridor_stop_dn),
            "fvg_conflict_stop_override": bool(fvg_conflict_stop_override),
            "fvg_conflict_stop_up": bool(fvg_conflict_stop_up),
            "fvg_conflict_stop_dn": bool(fvg_conflict_stop_dn),
            "mode_handoff_required_stop": bool(mode_handoff_required_stop),
            "router_pause_stop": bool(router_pause_stop),
            "range_shift_stop": bool(shift_stop),
        }

        hard_stop = bool(
            flags["fast_outside_up"]
            or flags["fast_outside_dn"]
            or adx_exit_overheat
            or adx_di_down_risk_stop
            or bbwp_expansion_stop
            or squeeze_release_break_stop
            or os_dev_trend_stop
            or lvn_corridor_stop_override
            or fvg_conflict_stop_override
            or mode_handoff_required_stop
            or router_pause_stop
        )
        raw_stop_rule = bool(two_up or two_dn or hard_stop or shift_stop)

        # ---- Entry sanity (15m) ----
        price_in_box = (close >= lo_p) and (close <= hi_p)
        rsi_ok = (rsi is not None) and (self.rsi_min <= rsi <= self.rsi_max)
        micro_vap_ok = bool((not self.micro_vap_enabled) or (len(rung_weights) == (n_levels + 1)))

        # ---- Regime allow ----
        gate_checks = [
            ("mode_active_ok", bool(not mode_pause)),
            ("adx_ok", bool(adx_ok)),
            ("bbw_nonexp", bool(bbw_nonexp)),
            ("ema_dist_ok", bool(ema_dist_ok)),
            ("vol_ok", bool(vol_ok)),
            ("atr_ok", bool(atr_ok)),
            ("inside_7d", bool(inside_7d)),
            ("vrvp_box_ok", bool(vrvp_box_ok)),
            ("bbwp_gate_ok", bool(bbwp_gate_ok)),
            ("squeeze_gate_ok", bool(squeeze_gate_ok)),
            ("os_dev_build_ok", bool(os_dev_build_ok)),
            ("micro_vap_ok", bool(micro_vap_ok)),
            ("fvg_gate_ok", bool(fvg_gate_ok)),
            ("mrvd_gate_ok", bool(mrvd_gate_ok)),
            ("cvd_gate_ok", bool(cvd_gate_ok)),
            ("ml_gate_ok", bool(ml_gate_ok)),
        ]
        rule_range_ok = bool(all(ok for _, ok in gate_checks))
        gate_pass_count = int(sum(1 for _, ok in gate_checks if ok))
        gate_total_count = int(len(gate_checks))
        gate_pass_ratio = float(gate_pass_count / gate_total_count) if gate_total_count > 0 else 0.0
        core_gate_names = {"mode_active_ok", "adx_ok", "bbw_nonexp", "ema_dist_ok", "vol_ok", "atr_ok", "inside_7d", "vrvp_box_ok"}
        core_gates_ok = bool(all(ok for name, ok in gate_checks if name in core_gate_names))
        gate_ratio_ok = bool(gate_pass_ratio >= gate_start_min_pass_ratio)

        rule_range_fail_reasons = []
        for gate_name, gate_ok in gate_checks:
            if not gate_ok:
                rule_range_fail_reasons.append(gate_name)

        ex_name = (self.config.get("exchange", {}) or {}).get("name", "unknown")
        ts = datetime.now(timezone.utc).isoformat()

        # Candle timestamp (THIS is what simulator/executor can align to)
        candle_ts = None
        candle_time_utc = None
        try:
            if "date" in dataframe.columns:
                candle_dt = pd.Timestamp(last["date"])
                if candle_dt.tzinfo is None:
                    candle_dt = candle_dt.tz_localize("UTC")
                else:
                    candle_dt = candle_dt.tz_convert("UTC")
                candle_time_utc = candle_dt.isoformat()
                candle_ts = int(candle_dt.timestamp())
            elif isinstance(dataframe.index, pd.DatetimeIndex):
                candle_dt = pd.Timestamp(dataframe.index[-1])
                if candle_dt.tzinfo is None:
                    candle_dt = candle_dt.tz_localize("UTC")
                else:
                    candle_dt = candle_dt.tz_convert("UTC")
                candle_time_utc = candle_dt.isoformat()
                candle_ts = int(candle_dt.timestamp())
        except Exception:
            candle_ts = None
            candle_time_utc = None

        # ---- Reclaim / cooldown / min-runtime handling ----
        clock_ts = candle_ts if candle_ts is not None else int(router_clock_ts)
        min_runtime_secs = int(max(float(self.min_runtime_hours), 0.0) * 3600.0)
        reclaim_secs = int(max(float(self.reclaim_hours), 0.0) * 3600.0)
        cooldown_secs = int(max(float(self.cooldown_minutes), 0.0) * 60.0)

        running_prev = bool(self._running_by_pair.get(pair, False))
        active_since_ts = self._active_since_ts_by_pair.get(pair)
        runtime_secs = None
        if running_prev and active_since_ts is not None:
            runtime_secs = max(int(clock_ts) - int(active_since_ts), 0)

        reclaim_until_ts = int(self._reclaim_until_ts_by_pair.get(pair, 0) or 0)
        cooldown_until_ts = int(self._cooldown_until_ts_by_pair.get(pair, 0) or 0)
        reclaim_active = bool(reclaim_until_ts and int(clock_ts) < reclaim_until_ts)
        cooldown_active = bool(cooldown_until_ts and int(clock_ts) < cooldown_until_ts)

        stop_rule = bool(raw_stop_rule)
        min_runtime_blocked_stop = False
        if (
            stop_rule
            and running_prev
            and not hard_stop
            and runtime_secs is not None
            and runtime_secs < min_runtime_secs
        ):
            stop_rule = False
            min_runtime_blocked_stop = True

        if gate_start_min_pass_ratio >= 0.999:
            start_gate_ok = bool(rule_range_ok)
        else:
            start_gate_ok = bool(core_gates_ok and gate_ratio_ok)
        start_signal = bool(start_gate_ok and price_in_box and rsi_ok)
        start_blocked = bool(start_signal and (reclaim_active or cooldown_active))
        failed_core_gates = [name for name, ok in gate_checks if (name in core_gate_names) and (not ok)]
        failed_all_gates = [name for name, ok in gate_checks if not ok]
        start_block_reasons: List[str] = []
        if not start_gate_ok:
            if gate_start_min_pass_ratio >= 0.999:
                start_block_reasons.extend([f"gate_fail:{name}" for name in failed_all_gates])
            else:
                if not core_gates_ok:
                    start_block_reasons.extend([f"core_gate_fail:{name}" for name in failed_core_gates])
                if not gate_ratio_ok:
                    start_block_reasons.append("gate_ratio_below_required")
        if not price_in_box:
            start_block_reasons.append("price_outside_box")
        if not rsi_ok:
            start_block_reasons.append("rsi_out_of_range")
        if mode_pause:
            start_block_reasons.append("router_pause_mode")
        if reclaim_active:
            start_block_reasons.append("reclaim_active")
        if cooldown_active:
            start_block_reasons.append("cooldown_active")
        if mode_handoff_required_stop:
            start_block_reasons.append("mode_handoff_required_stop")
        if stop_rule:
            start_block_reasons.append("stop_rule_active")
        if raw_stop_rule and (not stop_rule):
            start_block_reasons.append("stop_rule_suppressed_by_min_runtime")
        start_block_reasons = list(dict.fromkeys(start_block_reasons))

        # ---- Action (final) ----
        if stop_rule:
            action = "STOP"
        elif start_signal and not start_blocked:
            action = "START"
        else:
            action = "HOLD"

        if action == "STOP":
            reclaim_until_ts = int(clock_ts) + reclaim_secs
            cooldown_until_ts = int(clock_ts) + cooldown_secs
            self._reclaim_until_ts_by_pair[pair] = reclaim_until_ts
            self._cooldown_until_ts_by_pair[pair] = cooldown_until_ts
            self._running_by_pair[pair] = False
            self._running_mode_by_pair.pop(pair, None)
            self._active_since_ts_by_pair.pop(pair, None)
            active_since_ts = None
            runtime_secs = None
        elif action == "START":
            if (not running_prev) or (active_since_ts is None):
                self._active_since_ts_by_pair[pair] = int(clock_ts)
                active_since_ts = int(clock_ts)
            self._running_by_pair[pair] = True
            self._running_mode_by_pair[pair] = self._normalize_mode_name(active_mode)
            runtime_secs = max(int(clock_ts) - int(active_since_ts), 0)
        else:
            # HOLD preserves previous running state.
            self._running_by_pair[pair] = running_prev
            if running_prev and active_since_ts is not None:
                runtime_secs = max(int(clock_ts) - int(active_since_ts), 0)
            else:
                self._running_mode_by_pair.pop(pair, None)
                active_since_ts = None
                runtime_secs = None

        running_now = bool(self._running_by_pair.get(pair, False))
        reclaim_active_now = bool(reclaim_until_ts and int(clock_ts) < reclaim_until_ts)
        cooldown_active_now = bool(cooldown_until_ts and int(clock_ts) < cooldown_until_ts)
        stop_reason_flags_raw_active = [k for k, v in stop_reason_flags_raw.items() if bool(v)]
        stop_reason_flags_applied_active = stop_reason_flags_raw_active if bool(stop_rule) else []

        plan = {
            "ts": ts,
            "exchange": ex_name,
            "symbol": pair,
            "action": action,
            "mode": str(active_mode),
            "regime_router": {
                "enabled": bool(router_state.get("enabled", False)),
                "forced_mode": router_state.get("forced_mode"),
                "active_mode": str(active_mode),
                "desired_mode": router_state.get("desired_mode"),
                "desired_reason": router_state.get("desired_reason"),
                "target_mode": router_state.get("target_mode"),
                "target_reason": router_state.get("target_reason"),
                "candidate_mode": router_state.get("candidate_mode"),
                "candidate_count": int(router_state.get("candidate_count", 0) or 0),
                "switch_persist_bars": int(router_state.get("switch_persist_bars", 0) or 0),
                "switch_cooldown_bars": int(router_state.get("switch_cooldown_bars", 0) or 0),
                "switch_margin": float(router_state.get("switch_margin", 0.0) or 0.0),
                "switch_cooldown_active": bool(router_state.get("switch_cooldown_active", False)),
                "switch_cooldown_until_ts": router_state.get("switch_cooldown_until_ts"),
                "switch_cooldown_until_utc": self._ts_to_iso(
                    int(router_state["switch_cooldown_until_ts"])
                ) if router_state.get("switch_cooldown_until_ts") is not None else None,
                "switched": bool(router_state.get("switched", False)),
                "running_active": bool(router_state.get("running_active", False)),
                "running_mode": router_state.get("running_mode"),
                "handoff_blocked_running_inventory": bool(
                    router_state.get("handoff_blocked_running_inventory", False)
                ),
                "scores": router_state.get("scores", {}),
            },

            # NEW: align sims/executor to the candle that produced this plan
            "candle_time_utc": candle_time_utc,
            "candle_ts": candle_ts,

            "timeframes": {"exec": "15m", "signal": "1h", "regime": "4h"},

            # NEW: reference price for initial ladder decisions
            "price_ref": {"close": float(close), "vwap_15m": vwap},

            "range": {
                "low": float(lo_p),
                "high": float(hi_p),
                "pad": float(pad),
                "lookback_bars_used": int(used_lb),
                "width_pct": float(width_pct),
                "quartiles": {"q1": float(q1), "q2": float(q2), "q3": float(q3)},
                "volume_profile": {
                    "lookback_bars": int(self.vrvp_lookback_bars),
                    "bins": int(self.vrvp_bins),
                    "value_area_pct": float(self.vrvp_value_area_pct),
                    "poc": vrvp_poc,
                    "vah": vrvp_vah,
                    "val": vrvp_val,
                    "poc_inside_box": bool(vrvp_poc_inside_box),
                    "poc_dist_frac_after_shift": vrvp_dist_frac,
                    "box_shift_applied": float(vrvp_box_shift),
                    "box_ok": bool(vrvp_box_ok),
                },
                "micro_vap": {
                    "enabled": bool(self.micro_vap_enabled),
                    "lookback_bars": int(self.micro_vap_lookback_bars),
                    "bins": int(self.micro_vap_bins),
                    "poc": micro_poc,
                    "hvn_levels": [float(x) for x in micro_hvn_levels],
                    "lvn_levels": [float(x) for x in micro_lvn_levels],
                    "top_void": float(micro_top_void),
                    "bottom_void": float(micro_bottom_void),
                    "void_slope": float(micro_void_slope),
                    "poc_vrvp_dist_steps": micro_poc_vrvp_steps,
                },
                "fvg": {
                    "enabled": bool(self.fvg_enabled),
                    "lookback_bars": int(self.fvg_lookback_bars),
                    "straddle_veto_steps": float(self.fvg_straddle_veto_steps),
                    "count_total": int(fvg_state.get("count_total", 0)),
                    "count_bull": int(fvg_state.get("count_bull", 0)),
                    "count_bear": int(fvg_state.get("count_bear", 0)),
                    "count_defensive_bull": int(fvg_state.get("count_defensive_bull", 0)),
                    "count_defensive_bear": int(fvg_state.get("count_defensive_bear", 0)),
                    "count_session": int(fvg_state.get("count_session", 0)),
                    "nearest_bullish": fvg_state.get("nearest_bullish"),
                    "nearest_bearish": fvg_state.get("nearest_bearish"),
                    "nearest_defensive_bullish": fvg_state.get("nearest_defensive_bullish"),
                    "nearest_defensive_bearish": fvg_state.get("nearest_defensive_bearish"),
                    "straddle_veto": bool(fvg_state.get("straddle_veto", False)),
                    "defensive_conflict": bool(fvg_state.get("defensive_conflict", False)),
                    "fresh_defensive_pause": bool(fvg_state.get("fresh_defensive_pause", False)),
                    "session_new_print": bool(fvg_state.get("session_new_print", False)),
                    "session_pause_active": bool(fvg_state.get("session_pause_active", False)),
                    "session_inside_block": bool(fvg_state.get("session_inside_block", False)),
                    "session_gate_ok": bool(fvg_state.get("session_gate_ok", True)),
                    "gate_ok": bool(fvg_state.get("gate_ok", True)),
                    "imfvg_avg_bull": self._safe_float(fvg_state.get("imfvg_avg_bull")),
                    "imfvg_avg_bear": self._safe_float(fvg_state.get("imfvg_avg_bear")),
                    "session_fvg_avg": self._safe_float(fvg_state.get("session_fvg_avg")),
                    "positioning_up_avg": self._safe_float(fvg_state.get("positioning_up_avg")),
                    "positioning_down_avg": self._safe_float(fvg_state.get("positioning_down_avg")),
                },
                "multi_range_volume": {
                    "enabled": bool(self.mrvd_enabled),
                    "bins": int(self.mrvd_bins),
                    "value_area_pct": float(self.mrvd_value_area_pct),
                    "required_overlap_count": int(self.mrvd_required_overlap_count),
                    "va_overlap_min_frac": float(self.mrvd_va_overlap_min_frac),
                    "near_poc_steps": float(self.mrvd_near_poc_steps),
                    "overlap_count": int(mrvd_overlap_count),
                    "overlap_ok": bool(mrvd_overlap_ok),
                    "near_any_poc": bool(mrvd_near_any_poc),
                    "pause_entries": bool(mrvd_pause_entries),
                    "drift_guard_triggered": bool(mrvd_drift_guard_triggered),
                    "drift_delta_steps": mrvd_drift_delta_steps,
                    "drift_anchor_prev": mrvd_drift_anchor_prev,
                    "drift_anchor_cur": mrvd_drift_anchor_cur,
                    "day_poc_step_move": mrvd_day_poc_step_move,
                    "day": mrvd_day_state,
                    "week": mrvd_week_state,
                    "month": mrvd_month_state,
                },
                "cvd": {
                    "enabled": bool(self.cvd_enabled),
                    "lookback_bars": int(self.cvd_lookback_bars),
                    "state": cvd_state,
                },
                "ml_overlay": {
                    "enabled": bool(self.freqai_overlay_enabled),
                    "strict_predict": bool(self.freqai_overlay_strict_predict),
                    "source": ml_source,
                    "do_predict": ml_do_predict,
                    "p_range": p_range,
                    "p_breakout": p_breakout,
                    "ml_confidence": ml_confidence,
                    "gate_ok": bool(ml_gate_ok),
                    "breakout_risk_high": bool(ml_breakout_risk_high),
                    "quick_tp_candidate": ml_quick_tp_candidate,
                },
            },
            "grid": {
                "n_levels": int(n_levels),
                "target_net_step_pct": float(self.target_net_step_pct),
                "est_fee_pct": float(self.est_fee_pct),
                "est_spread_pct": float(self.est_spread_pct),
                "gross_step_min_pct": float(gross_min),
                "step_pct_actual": float(step_pct_actual),
                "step_price": float(step_price),
                "post_only": True,
                "rung_density_bias": {
                    "enabled": bool(self.micro_vap_enabled),
                    "source": "micro_vap_hvn_lvn",
                    "hvn_boost": float(self.rung_weight_hvn_boost),
                    "lvn_penalty": float(self.rung_weight_lvn_penalty),
                    "weight_min": float(self.rung_weight_min),
                    "weight_max": float(self.rung_weight_max),
                    "weights_by_level_index": [float(x) for x in rung_weights],
                },
            },
            "exit": {
                "enabled": True,
                "tp_price": float(tp_price_plan),
                "tp_price_base": float(tp_price),
                "sl_price": float(sl_price),
                "tp_step_multiple": float(self.tp_step_multiple),
                "sl_step_multiple": float(self.sl_step_multiple),
                "source": "box_plus_step_multiples",
                "tp_candidates": tp_candidates,
            },
            "signals": {
                "mode": str(active_mode),
                "mode_pause": bool(mode_pause),
                "mode_desired": str(desired_mode),
                "adx_4h": adx4h,
                "adx_enter_max_4h": float(gate_adx_4h_max),
                "adx_exit_min_4h": float(gate_adx_4h_exit_min),
                "adx_exit_max_4h": float(gate_adx_4h_exit_max),
                "adx_rising_bars_4h": int(adx_rising_count),
                "adx_rising_required_4h": int(gate_adx_rising_bars),
                "adx_rising_confirmed_4h": bool(adx_rising_confirmed),
                "adx_exit_overheat": bool(adx_exit_overheat),
                "plus_di_4h": plus_di_4h,
                "minus_di_4h": minus_di_4h,
                "adx_di_up": bool(adx_di_up),
                "adx_di_down": bool(adx_di_down),
                "adx_di_down_risk_stop": bool(adx_di_down_risk_stop),
                "bb_width_15m": bbw15m,
                "bb_width_1h": bbw1h,
                "bb_width_4h": bbw4h,
                "bb_width_1h_pct": bbw1h_pct,
                "bb_width_nonexpanding_1h": bool(bbw_nonexp),
                "bbwp_15m_pct": bbwp_s,
                "bbwp_1h_pct": bbwp_m,
                "bbwp_4h_pct": bbwp_l,
                "bbwp_allow": bool(bbwp_allow),
                "bbwp_veto": bool(bbwp_veto),
                "bbwp_cooloff": bool(bbwp_cooloff),
                "bbwp_s_enter_low": float(gate_bbwp_s_enter_low),
                "bbwp_s_enter_high": float(gate_bbwp_s_enter_high),
                "bbwp_m_enter_low": float(gate_bbwp_m_enter_low),
                "bbwp_m_enter_high": float(gate_bbwp_m_enter_high),
                "bbwp_l_enter_low": float(gate_bbwp_l_enter_low),
                "bbwp_l_enter_high": float(gate_bbwp_l_enter_high),
                "bbwp_stop_high": float(gate_bbwp_stop_high),
                "bbwp_expansion_stop": bool(bbwp_expansion_stop),
                "bbwp_gate_ok": bool(bbwp_gate_ok),
                "ema50_1h": ema50,
                "ema100_1h": ema100,
                "ema_dist_frac_1h": ema_dist_frac,
                "atr_1h": atr_1h,
                "atr_4h": atr_4h,
                "atr_1h_pct": atr_1h_pct,
                "atr_4h_pct": atr_4h_pct,
                "atr_mode_source": str(gate_atr_source),
                "atr_mode_pct": atr_mode_pct,
                "atr_mode_max": float(gate_atr_pct_max),
                "atr_ok": bool(atr_ok),
                "vol_ratio_1h": vol_ratio,
                "rvol_15m": rvol_15m,
                "inside_7d": bool(inside_7d),
                "squeeze_on_1h": bool(squeeze_on_1h) if squeeze_on_1h is not None else None,
                "squeeze_released_1h": bool(squeeze_released_1h),
                "squeeze_gate_ok": bool(squeeze_gate_ok),
                "squeeze_require_on_1h": bool(self.squeeze_require_on_1h),
                "vrvp_box_ok": bool(vrvp_box_ok),
                "micro_vap_ok": bool(micro_vap_ok),
                "fvg_gate_ok": bool(fvg_gate_ok),
                "fvg_straddle_veto": bool(fvg_straddle_veto),
                "fvg_defensive_conflict": bool(fvg_defensive_conflict),
                "fvg_fresh_pause": bool(fvg_fresh_pause),
                "session_fvg_pause_active": bool(session_fvg_pause_active),
                "session_fvg_inside_block": bool(session_fvg_inside_block),
                "mrvd_gate_ok": bool(mrvd_gate_ok),
                "mrvd_overlap_count": int(mrvd_overlap_count),
                "mrvd_overlap_ok": bool(mrvd_overlap_ok),
                "mrvd_near_any_poc": bool(mrvd_near_any_poc),
                "mrvd_pause_entries": bool(mrvd_pause_entries),
                "mrvd_drift_guard_triggered": bool(mrvd_drift_guard_triggered),
                "mrvd_drift_delta_steps": mrvd_drift_delta_steps,
                "mrvd_day_poc": mrvd_day_poc,
                "mrvd_week_poc": mrvd_week_poc,
                "mrvd_month_poc": mrvd_month_poc,
                "cvd": self._safe_float(cvd_state.get("cvd")),
                "cvd_delta": self._safe_float(cvd_state.get("cvd_delta")),
                "cvd_near_bottom": bool(cvd_state.get("near_bottom", False)),
                "cvd_near_top": bool(cvd_state.get("near_top", False)),
                "cvd_bull_divergence": bool(cvd_state.get("bull_divergence", False)),
                "cvd_bear_divergence": bool(cvd_state.get("bear_divergence", False)),
                "cvd_bull_divergence_near_bottom": bool(cvd_state.get("bull_divergence_near_bottom", False)),
                "cvd_bear_divergence_near_top": bool(cvd_state.get("bear_divergence_near_top", False)),
                "cvd_bos_up": bool(cvd_state.get("bos_up", False)),
                "cvd_bos_down": bool(cvd_state.get("bos_down", False)),
                "cvd_bos_up_near_bottom": bool(cvd_state.get("bos_up_near_bottom", False)),
                "cvd_bos_down_near_top": bool(cvd_state.get("bos_down_near_top", False)),
                "cvd_bos_against_range": bool(cvd_bos_against_range),
                "cvd_quick_tp_trigger": bool(cvd_quick_tp_trigger),
                "cvd_quick_tp_candidate": cvd_quick_tp_candidate,
                "cvd_freeze_bars_left": int(cvd_freeze_left),
                "cvd_freeze_active": bool(cvd_freeze_active),
                "cvd_gate_ok": bool(cvd_gate_ok),
                "ml_overlay_enabled": bool(self.freqai_overlay_enabled),
                "ml_overlay_source": ml_source,
                "ml_do_predict": ml_do_predict,
                "ml_gate_ok": bool(ml_gate_ok),
                "ml_breakout_risk_high": bool(ml_breakout_risk_high),
                "ml_quick_tp_candidate": ml_quick_tp_candidate,
                "micro_poc": micro_poc,
                "micro_hvn_levels": [float(x) for x in micro_hvn_levels],
                "micro_lvn_levels": [float(x) for x in micro_lvn_levels],
                "micro_void_slope": float(micro_void_slope),
                "micro_poc_vrvp_dist_steps": micro_poc_vrvp_steps,
                "os_dev_raw": int(os_dev_raw),
                "os_dev_norm": os_dev_norm,
                "os_dev_state": int(os_dev_state),
                "os_dev_candidate_count": int(os_dev_candidate_count),
                "os_dev_zero_persist_bars": int(os_dev_zero_persist),
                "os_dev_rvol_ok": bool(os_dev_rvol_ok),
                "os_dev_build_ok": bool(os_dev_build_ok),
                "gate_profile": gate_profile,
                "regime_threshold_profile": str(self._active_threshold_profile()),
                "gate_pass_count": int(gate_pass_count),
                "gate_total_count": int(gate_total_count),
                "gate_pass_ratio": float(gate_pass_ratio),
                "gate_required_ratio": float(gate_start_min_pass_ratio),
                "gate_ratio_ok": bool(gate_ratio_ok),
                "core_gates_ok": bool(core_gates_ok),
                "rsi_15m": rsi,
                "vwap_15m": vwap,
                "rule_range_ok": bool(rule_range_ok),
                "rule_range_fail_reasons": rule_range_fail_reasons,
                "mode_handoff_required_stop": bool(mode_handoff_required_stop),
                "router_pause_stop": bool(router_pause_stop),
                "p_range": p_range,
                "p_breakout": p_breakout,
                "ml_confidence": ml_confidence,
            },
            "risk": {
                "stop_confirm_bars": int(self.stop_confirm_bars),
                "fast_stop_step_multiple": float(self.fast_stop_step_multiple),
                "range_shift_stop_pct": float(self.range_shift_stop_pct),
                "tp_price": float(tp_price_plan),
                "tp_price_base": float(tp_price),
                "sl_price": float(sl_price),
                "stop_rule_triggered": bool(stop_rule),
                "stop_rule_triggered_raw": bool(raw_stop_rule),
                "min_runtime_blocked_stop": bool(min_runtime_blocked_stop),
                "stop_reasons": {
                    "two_consecutive_outside_up": bool(stop_reason_flags_raw["two_consecutive_outside_up"]),
                    "two_consecutive_outside_dn": bool(stop_reason_flags_raw["two_consecutive_outside_dn"]),
                    "fast_outside_up": bool(stop_reason_flags_raw["fast_outside_up"]),
                    "fast_outside_dn": bool(stop_reason_flags_raw["fast_outside_dn"]),
                    "adx_hysteresis_stop": bool(stop_reason_flags_raw["adx_hysteresis_stop"]),
                    "adx_di_down_risk_stop": bool(stop_reason_flags_raw["adx_di_down_risk_stop"]),
                    "bbwp_expansion_stop": bool(stop_reason_flags_raw["bbwp_expansion_stop"]),
                    "squeeze_release_break_stop": bool(stop_reason_flags_raw["squeeze_release_break_stop"]),
                    "os_dev_trend_stop": bool(stop_reason_flags_raw["os_dev_trend_stop"]),
                    "lvn_corridor_stop_override": bool(stop_reason_flags_raw["lvn_corridor_stop_override"]),
                    "lvn_corridor_stop_up": bool(stop_reason_flags_raw["lvn_corridor_stop_up"]),
                    "lvn_corridor_stop_dn": bool(stop_reason_flags_raw["lvn_corridor_stop_dn"]),
                    "lvn_corridor_width": float(lvn_corridor_width),
                    "fvg_conflict_stop_override": bool(stop_reason_flags_raw["fvg_conflict_stop_override"]),
                    "fvg_conflict_stop_up": bool(stop_reason_flags_raw["fvg_conflict_stop_up"]),
                    "fvg_conflict_stop_dn": bool(stop_reason_flags_raw["fvg_conflict_stop_dn"]),
                    "mode_handoff_required_stop": bool(stop_reason_flags_raw["mode_handoff_required_stop"]),
                    "router_pause_stop": bool(stop_reason_flags_raw["router_pause_stop"]),
                    "upper_edge_lvn": bool(upper_edge_lvn),
                    "lower_edge_lvn": bool(lower_edge_lvn),
                    "close_outside_up": bool(flags["close_outside_up"]),
                    "close_outside_dn": bool(flags["close_outside_dn"]),
                    "range_shift_stop": bool(stop_reason_flags_raw["range_shift_stop"]),
                    "range_shift_frac": shift_frac,
                },
                "stop_policy": "DANGER_TO_QUOTE",
            },
            "update_policy": {
                "exec_candle_check": True,
                "event_driven": True,
                "soft_adjust_max_step_frac": float(self.soft_adjust_max_step_frac),
                "bbwp": {
                    "enabled": bool(self.bbwp_enabled),
                    "s_max": float(gate_bbwp_s_max),
                    "m_max": float(gate_bbwp_m_max),
                    "l_max": float(gate_bbwp_l_max),
                    "veto_pct": float(gate_bbwp_veto_pct),
                    "cooloff_trigger_pct": float(gate_bbwp_cooloff_trigger_pct),
                    "cooloff_release_s": float(gate_bbwp_cooloff_release_s),
                    "cooloff_release_m": float(gate_bbwp_cooloff_release_m),
                },
                "squeeze": {
                    "enabled": bool(self.squeeze_enabled),
                    "require_on_1h": bool(self.squeeze_require_on_1h),
                    "kc_atr_mult": float(self.kc_atr_mult),
                },
                "os_dev": {
                    "enabled": bool(self.os_dev_enabled),
                    "n_strike": int(self.os_dev_n_strike),
                    "range_band": float(self.os_dev_range_band),
                    "persist_bars": int(gate_os_dev_persist_bars),
                    "history_bars": int(self.os_dev_history_bars),
                    "rvol_max": float(gate_os_dev_rvol_max),
                },
                "gating": {
                    "profile": gate_profile,
                    "regime_threshold_profile": str(self._active_threshold_profile()),
                    "active_mode": str(active_mode),
                    "start_min_gate_pass_ratio": float(gate_start_min_pass_ratio),
                    "adx_4h_max": float(gate_adx_4h_max),
                    "adx_4h_exit_min": float(gate_adx_4h_exit_min),
                    "adx_4h_exit_max": float(gate_adx_4h_exit_max),
                    "adx_rising_bars": int(gate_adx_rising_bars),
                    "bbw_1h_pct_max": float(gate_bbw_1h_pct_max),
                    "ema_dist_max_frac": float(gate_ema_dist_max_frac),
                    "vol_spike_mult": float(gate_vol_spike_mult),
                    "atr_source": str(gate_atr_source),
                    "atr_pct_max": float(gate_atr_pct_max),
                    "bbwp_s_enter_low": float(gate_bbwp_s_enter_low),
                    "bbwp_s_enter_high": float(gate_bbwp_s_enter_high),
                    "bbwp_m_enter_low": float(gate_bbwp_m_enter_low),
                    "bbwp_m_enter_high": float(gate_bbwp_m_enter_high),
                    "bbwp_l_enter_low": float(gate_bbwp_l_enter_low),
                    "bbwp_l_enter_high": float(gate_bbwp_l_enter_high),
                    "bbwp_stop_high": float(gate_bbwp_stop_high),
                },
                "regime_router": {
                    "enabled": bool(self.regime_router_enabled),
                    "default_mode": self._normalize_mode_name(self.regime_router_default_mode),
                    "force_mode": (
                        self._normalize_mode_name(self.regime_router_force_mode)
                        if str(self.regime_router_force_mode or "").strip()
                        else None
                    ),
                    "threshold_profile": str(self._active_threshold_profile()),
                    "allow_pause": bool(self.regime_router_allow_pause),
                    "switch_persist_bars": int(self.regime_router_switch_persist_bars),
                    "switch_cooldown_bars": int(self.regime_router_switch_cooldown_bars),
                    "switch_margin": float(self.regime_router_switch_margin),
                },
                "intraday": self._mode_threshold_block("intraday"),
                "swing": self._mode_threshold_block("swing"),
                "plan_history": {
                    "per_candle_backtest_enabled": bool(self.emit_per_candle_history_backtest),
                    "per_candle_active": bool(history_mode),
                    "runmode": self._runmode_name(),
                },
                "micro_vap": {
                    "enabled": bool(self.micro_vap_enabled),
                    "lookback_bars": int(self.micro_vap_lookback_bars),
                    "bins": int(self.micro_vap_bins),
                    "hvn_quantile": float(self.micro_hvn_quantile),
                    "lvn_quantile": float(self.micro_lvn_quantile),
                    "extrema_count": int(self.micro_extrema_count),
                    "lvn_corridor_steps": float(self.micro_lvn_corridor_steps),
                    "void_slope_threshold": float(self.micro_void_slope_threshold),
                },
                "fvg": {
                    "enabled": bool(self.fvg_enabled),
                    "lookback_bars": int(self.fvg_lookback_bars),
                    "min_gap_atr": float(self.fvg_min_gap_atr),
                    "straddle_veto_steps": float(self.fvg_straddle_veto_steps),
                    "position_avg_count": int(self.fvg_position_avg_count),
                    "imfvg_enabled": bool(self.imfvg_enabled),
                    "imfvg_mitigated_relax": bool(self.imfvg_mitigated_relax),
                    "defensive_enabled": bool(self.defensive_fvg_enabled),
                    "defensive_min_gap_atr": float(self.defensive_fvg_min_gap_atr),
                    "defensive_body_frac": float(self.defensive_fvg_body_frac),
                    "defensive_fresh_bars": int(self.defensive_fvg_fresh_bars),
                    "session_enabled": bool(self.session_fvg_enabled),
                    "session_inside_gate": bool(self.session_fvg_inside_gate),
                    "session_pause_bars": int(self.session_fvg_pause_bars),
                },
                "mrvd": {
                    "enabled": bool(self.mrvd_enabled),
                    "bins": int(self.mrvd_bins),
                    "value_area_pct": float(self.mrvd_value_area_pct),
                    "day_lookback_bars": int(self.mrvd_day_lookback_bars),
                    "week_lookback_bars": int(self.mrvd_week_lookback_bars),
                    "month_lookback_bars": int(self.mrvd_month_lookback_bars),
                    "required_overlap_count": int(self.mrvd_required_overlap_count),
                    "va_overlap_min_frac": float(self.mrvd_va_overlap_min_frac),
                    "near_poc_steps": float(self.mrvd_near_poc_steps),
                    "drift_guard_enabled": bool(self.mrvd_drift_guard_enabled),
                    "drift_guard_steps": float(self.mrvd_drift_guard_steps),
                },
                "cvd": {
                    "enabled": bool(self.cvd_enabled),
                    "lookback_bars": int(self.cvd_lookback_bars),
                    "pivot_left": int(self.cvd_pivot_left),
                    "pivot_right": int(self.cvd_pivot_right),
                    "divergence_max_age_bars": int(self.cvd_divergence_max_age_bars),
                    "near_value_steps": float(self.cvd_near_value_steps),
                    "bos_lookback": int(self.cvd_bos_lookback),
                    "bos_freeze_bars": int(self.cvd_bos_freeze_bars),
                    "rung_bias_strength": float(self.cvd_rung_bias_strength),
                },
                "ml_overlay": {
                    "enabled": bool(self.freqai_overlay_enabled),
                    "strict_predict": bool(self.freqai_overlay_strict_predict),
                    "confidence_min": float(self.freqai_overlay_confidence_min),
                    "breakout_scale": float(self.freqai_overlay_breakout_scale),
                    "breakout_quick_tp_thresh": float(self.freqai_overlay_breakout_quick_tp_thresh),
                    "rung_edge_cut_max": float(self.freqai_overlay_rung_edge_cut_max),
                },
                "rung_bias": {
                    "hvn_boost": float(self.rung_weight_hvn_boost),
                    "lvn_penalty": float(self.rung_weight_lvn_penalty),
                    "weight_min": float(self.rung_weight_min),
                    "weight_max": float(self.rung_weight_max),
                },
                "runtime_controls": {
                    "reclaim_hours": float(self.reclaim_hours),
                    "cooldown_minutes": int(self.cooldown_minutes),
                    "min_runtime_hours": float(self.min_runtime_hours),
                    "min_runtime_secs": int(min_runtime_secs),
                },
            },
            "runtime_state": {
                "clock_ts": int(clock_ts),
                "clock_time_utc": self._ts_to_iso(int(clock_ts)),
                "active_mode": str(active_mode),
                "running": bool(running_now),
                "running_mode": (
                    self._normalize_mode_name(self._running_mode_by_pair.get(pair))
                    if bool(running_now)
                    else None
                ),
                "active_since_ts": int(active_since_ts) if active_since_ts is not None else None,
                "active_since_utc": self._ts_to_iso(int(active_since_ts)) if active_since_ts is not None else None,
                "runtime_secs": int(runtime_secs) if runtime_secs is not None else None,
                "reclaim_until_ts": int(reclaim_until_ts) if reclaim_until_ts else None,
                "reclaim_until_utc": self._ts_to_iso(int(reclaim_until_ts)) if reclaim_until_ts else None,
                "reclaim_active": bool(reclaim_active_now),
                "cooldown_until_ts": int(cooldown_until_ts) if cooldown_until_ts else None,
                "cooldown_until_utc": self._ts_to_iso(int(cooldown_until_ts)) if cooldown_until_ts else None,
                "cooldown_active": bool(cooldown_active_now),
                "router_target_mode": router_state.get("target_mode"),
                "router_target_reason": router_state.get("target_reason"),
                "router_desired_mode": router_state.get("desired_mode"),
                "router_desired_reason": router_state.get("desired_reason"),
                "router_switched": bool(router_state.get("switched", False)),
                "start_signal": bool(start_signal),
                "start_blocked": bool(start_blocked),
                "start_block_reasons": [str(x) for x in start_block_reasons],
                "stop_reason_flags_raw_active": [str(x) for x in stop_reason_flags_raw_active],
                "stop_reason_flags_applied_active": [str(x) for x in stop_reason_flags_applied_active],
            },
            "diagnostics": {
                "active_mode": str(active_mode),
                "mode_pause": bool(mode_pause),
                "start_gate_ok": bool(start_gate_ok),
                "price_in_box": bool(price_in_box),
                "rsi_ok": bool(rsi_ok),
                "start_signal": bool(start_signal),
                "start_blocked": bool(start_blocked),
                "start_block_reasons": [str(x) for x in start_block_reasons],
                "stop_rule_triggered": bool(stop_rule),
                "stop_rule_triggered_raw": bool(raw_stop_rule),
                "stop_reason_flags_raw_active": [str(x) for x in stop_reason_flags_raw_active],
                "stop_reason_flags_applied_active": [str(x) for x in stop_reason_flags_applied_active],
                "router_target_mode": router_state.get("target_mode"),
                "router_target_reason": router_state.get("target_reason"),
                "router_desired_mode": router_state.get("desired_mode"),
                "router_desired_reason": router_state.get("desired_reason"),
                "router_switched": bool(router_state.get("switched", False)),
            },
            "capital_policy": {
                "mode": "QUOTE_ONLY",
                "grid_budget_pct": float(self.grid_budget_pct),
                "reserve_pct": float(self.reserve_pct),
            },
            "notes": {
                "brain_mode": "deterministic_v1",
                "ml": "freqai_confidence_overlay_v1",
                "expect_0_trades_in_freqtrade": True,
            },
        }

        # Write plan once per base candle timestamp
        if candle_ts is not None:
            last_written = self._last_written_ts_by_pair.get(pair)
            if last_written != candle_ts:
                self._write_plan(ex_name, pair, plan)
                self._last_written_ts_by_pair[pair] = candle_ts
        else:
            self._write_plan(ex_name, pair, plan)

        # Cache mid for shift detection next candle
        self._last_mid_by_pair[pair] = float(mid)

        return dataframe

    # ========= Trading signals intentionally disabled =========
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        return dataframe
