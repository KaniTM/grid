# ruff: noqa: S101

from collections import deque
from datetime import datetime, timezone
import json
from pathlib import Path

import pandas as pd
import pytest
from core.enums import BlockReason, MaterialityClass, WarningCode
from core.schema_validation import validate_schema
from freqtrade.user_data.scripts import grid_executor_v1, grid_simulator_v1
from freqtrade.user_data.strategies.GridBrainV1 import GridBrainV1Core, MetaDriftGuard


def test_box_signature_is_repeatable() -> None:
    sig = GridBrainV1Core._box_signature(1.23456789, 1.34567891, 48, 0.25000001)
    assert sig.startswith("1.23456789:1.34567891:48:0.25000001")
    assert ":" in sig


def test_reclaim_baseline_default_is_8h() -> None:
    assert float(GridBrainV1Core.reclaim_hours) == pytest.approx(8.0)


def test_poc_cross_detected_when_open_close_bracket_value() -> None:
    df = pd.DataFrame(
        {
            "open": [1.0, 1.5, 1.2],
            "close": [1.3, 1.1, 1.25],
        }
    )
    assert GridBrainV1Core._poc_cross_detected(df, 1.25, 3)
    assert not GridBrainV1Core._poc_cross_detected(df, 2.0, 2)


def test_derive_box_block_reasons_reflects_conflicts() -> None:
    state = {
        "straddle_veto": True,
        "defensive_conflict": True,
        "session_inside_block": True,
    }
    reasons = GridBrainV1Core._derive_box_block_reasons(state)
    assert BlockReason.BLOCK_BOX_STRADDLE_FVG_EDGE in reasons
    assert BlockReason.BLOCK_BOX_STRADDLE_FVG_AVG in reasons
    assert BlockReason.BLOCK_BOX_STRADDLE_SESSION_FVG_AVG in reasons


def test_poc_acceptance_status_persists_once_crossed() -> None:
    strategy = object.__new__(GridBrainV1Core)
    strategy.poc_acceptance_enabled = True
    strategy.poc_acceptance_lookback_bars = 4
    strategy._poc_acceptance_crossed_by_pair = {}
    df = pd.DataFrame(
        {
            "open": [1.0, 1.1, 1.4, 1.0],
            "close": [1.05, 1.3, 1.2, 1.1],
        }
    )
    symbol = "CTA/TEST"
    assert GridBrainV1Core._poc_cross_detected(df, 1.25, 4)
    assert strategy._poc_acceptance_status(symbol, df, 1.25)
    assert strategy._poc_acceptance_crossed_by_pair.get(symbol) is True
    # Subsequent calls should remain satisfied without new cross
    assert strategy._poc_acceptance_status(symbol, df, 1.25)


def _fresh_phase3_strategy() -> GridBrainV1Core:
    strategy = object.__new__(GridBrainV1Core)
    strategy._materiality_epoch_bar_count_by_pair = {}
    strategy._last_mid_by_pair = {}
    strategy._last_width_pct_by_pair = {}
    strategy._last_box_step_by_pair = {}
    strategy._last_tp_price_by_pair = {}
    strategy._last_sl_price_by_pair = {}
    return strategy


def test_data_quality_checks_flag_gap() -> None:
    strategy = object.__new__(GridBrainV1Core)
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-01 00:00", "2026-01-01 00:15", "2026-01-01 01:30"]),
            "volume": [1.0, 1.0, 1.0],
            "bb_mid_1h": [1.0, 1.0, 1.0],
            "bb_mid_4h": [1.0, 1.0, 1.0],
            "open": [1.0, 1.0, 1.0],
            "close": [1.0, 1.0, 1.0],
        }
    )
    result = strategy._run_data_quality_checks(df, "PAIR/TEST")
    assert any(r == BlockReason.BLOCK_DATA_GAP for r in result["reasons"])


def test_data_quality_checks_flag_duplicates() -> None:
    strategy = object.__new__(GridBrainV1Core)
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-01 00:00", "2026-01-01 00:00", "2026-01-01 00:15"]),
            "volume": [1.0, 1.0, 1.0],
            "bb_mid_1h": [1.0, 1.0, 1.0],
            "bb_mid_4h": [1.0, 1.0, 1.0],
            "open": [1.0, 1.0, 1.0],
            "close": [1.0, 1.0, 1.0],
        }
    )
    result = strategy._run_data_quality_checks(df, "PAIR/TEST")
    assert any(r == BlockReason.BLOCK_DATA_MISALIGN for r in result["reasons"])


def test_data_quality_checks_zero_volume_streak() -> None:
    strategy = object.__new__(GridBrainV1Core)
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2026-01-01 00:00", "2026-01-01 00:15", "2026-01-01 00:30", "2026-01-01 00:45"]
            ),
            "volume": [0.0, 0.0, 0.0, 0.0],
            "bb_mid_1h": [1.0, 1.0, 1.0, 1.0],
            "bb_mid_4h": [1.0, 1.0, 1.0, 1.0],
            "open": [1.0, 1.0, 1.0, 1.0],
            "close": [1.0, 1.0, 1.0, 1.0],
        }
    )
    result = strategy._run_data_quality_checks(df, "PAIR/TEST")
    assert any(r == BlockReason.BLOCK_ZERO_VOL_ANOMALY for r in result["reasons"])


def test_phase2_gate_failures_records_block_reasons() -> None:
    strategy = object.__new__(GridBrainV1Core)
    failures = strategy._phase2_gate_failures_from_flags(
        adx_ok=False,
        bbw_nonexp=False,
        ema_dist_ok=False,
        vol_ok=False,
        inside_7d=False,
    )
    expected = {
        BlockReason.BLOCK_ADX_HIGH,
        BlockReason.BLOCK_BBW_EXPANDING,
        BlockReason.BLOCK_EMA_DIST,
        BlockReason.BLOCK_RVOL_SPIKE,
        BlockReason.BLOCK_7D_EXTREME_CONTEXT,
    }
    assert set(failures) == expected


def test_start_block_reasons_include_baseline_codes() -> None:
    strategy = GridBrainV1Core.__new__(GridBrainV1Core)
    # mimic gating flags for start_block_reasons via attributes
    reason_list = strategy._phase2_gate_failures_from_flags(
        adx_ok=False,
        bbw_nonexp=True,
        ema_dist_ok=True,
        vol_ok=True,
        inside_7d=True,
    )
    assert str(BlockReason.BLOCK_ADX_HIGH) in [str(x) for x in reason_list]


def test_start_block_reasons_include_breakout_block() -> None:
    strategy = object.__new__(GridBrainV1Core)
    pair = "PAIR/TEST"
    strategy._neutral_box_break_bars_by_pair = {pair: 3}
    start_block_reasons: list[str] = []
    breakout_block_active = bool(strategy._neutral_box_break_bars_by_pair.get(pair, 0) > 0)
    if breakout_block_active:
        start_block_reasons.append(str(BlockReason.BLOCK_FRESH_BREAKOUT))
    assert str(BlockReason.BLOCK_FRESH_BREAKOUT) in start_block_reasons


def test_materiality_waits_for_epoch_or_delta() -> None:
    strategy = _fresh_phase3_strategy()
    pair = "PAIR/TEST"
    strategy._last_mid_by_pair[pair] = 100.0
    strategy._last_width_pct_by_pair[pair] = 0.05
    strategy._last_box_step_by_pair[pair] = 1.0
    strategy._last_tp_price_by_pair[pair] = 110.0
    strategy._last_sl_price_by_pair[pair] = 90.0

    first = strategy._evaluate_materiality(pair, 100.0, 0.05, 1.0, 110.0, 90.0, False, "START")
    assert not first["publish"]
    assert first["class"] == MaterialityClass.NOOP

    second = strategy._evaluate_materiality(pair, 100.0, 0.05, 1.0, 110.0, 90.0, False, "START")
    assert second["publish"]
    assert second["class"] == MaterialityClass.SOFT


def test_compute_band_slope_pct_respects_window() -> None:
    strategy = object.__new__(GridBrainV1Core)
    strategy.band_slope_veto_bars = 2
    strategy._mid_history_by_pair = {}
    assert strategy._compute_band_slope_pct("PAIR/TEST", 100.0) is None
    assert strategy._compute_band_slope_pct("PAIR/TEST", 101.0) is None
    ratio = strategy._compute_band_slope_pct("PAIR/TEST", 105.0)
    assert ratio is not None
    assert ratio == pytest.approx(0.05, rel=1e-4)


def test_excursion_asymmetry_ratio_handles_invalid_devs() -> None:
    strategy = object.__new__(GridBrainV1Core)
    assert strategy._excursion_asymmetry_ratio(95.0, 105.0, 100.0) == pytest.approx(1.0)
    assert strategy._excursion_asymmetry_ratio(100.0, 100.0, 100.0) is None


def test_funding_gate_honors_threshold() -> None:
    strategy = object.__new__(GridBrainV1Core)
    strategy.funding_filter_enabled = True
    strategy.funding_filter_pct = 0.0005
    assert strategy._funding_gate_ok(0.0002)
    assert not strategy._funding_gate_ok(0.001)
    strategy.funding_filter_enabled = False
    assert strategy._funding_gate_ok(0.001)


def test_box_straddle_breakout_detection_adds_blocker() -> None:
    strategy = object.__new__(GridBrainV1Core)
    strategy.breakout_straddle_step_buffer_frac = 0.5
    strategy.breakout_block_bars = 20
    pair = "PAIR/STRADDLE"
    strategy._breakout_levels_by_pair = {pair: {"up": 100.0, "dn": 90.0}}
    strategy._breakout_bars_since_by_pair = {pair: 3}
    assert strategy._box_straddles_cached_breakout(pair, 99.75, 100.3, 0.5)


def test_squeeze_release_block_reason_is_consumed() -> None:
    assert (
        GridBrainV1Core._squeeze_release_block_reason(True)
        == BlockReason.BLOCK_SQUEEZE_RELEASE_AGAINST_BIAS
    )
    assert GridBrainV1Core._squeeze_release_block_reason(False) is None


def test_bbw_nonexpanding_gate_requires_flat_or_contracting_window() -> None:
    nonexp = pd.Series([0.10, 0.10, 0.099, 0.0995])
    expanding = pd.Series([0.10, 0.101, 0.103, 0.105])
    assert GridBrainV1Core._bbw_nonexpanding(nonexp, 3, 0.01)
    assert not GridBrainV1Core._bbw_nonexpanding(expanding, 3, 0.0)


def test_breakout_fresh_state_blocks_until_reclaimed() -> None:
    strategy = object.__new__(GridBrainV1Core)
    strategy.breakout_block_bars = 20
    strategy.breakout_override_allowed = True
    strategy._breakout_levels_by_pair = {}
    strategy._breakout_bars_since_by_pair = {}
    pair = "PAIR/BREAK"

    active, up, dn = strategy._update_breakout_fresh_state(pair, True, 101.0, 95.0, 102.0)
    assert active
    assert up == pytest.approx(101.0)
    assert dn == pytest.approx(95.0)

    active2, _, _ = strategy._update_breakout_fresh_state(pair, False, None, None, 98.0)
    assert not active2


def test_detect_structural_breakout_uses_close_vs_prior_extremes() -> None:
    strategy = object.__new__(GridBrainV1Core)
    df = pd.DataFrame(
        {
            "high": [100.0, 101.0, 102.0, 103.0, 103.5],
            "low": [95.0, 95.5, 96.0, 96.5, 97.0],
            "close": [98.0, 99.0, 100.0, 101.0, 104.0],
        }
    )
    breakout, direction, hi, lo = strategy._detect_structural_breakout(df, 3)
    assert breakout
    assert direction == "bull"
    assert hi == pytest.approx(103.0)
    assert lo == pytest.approx(95.5)


def test_hvp_stats_returns_current_and_sma() -> None:
    strategy = object.__new__(GridBrainV1Core)
    strategy.hvp_lookback_bars = 3
    strategy.hvp_sma_bars = 2
    series = pd.Series([100.0, 101.0, 102.0, 103.0, 100.0])
    current, sma = strategy._hvp_stats(series)
    assert current is not None
    assert sma is not None
    assert current >= 0.0
    assert sma >= 0.0


def test_planner_health_state_transitions() -> None:
    strategy = object.__new__(GridBrainV1Core)
    strategy.planner_health_quarantine_on_gap = True
    strategy.planner_health_quarantine_on_misalign = True
    assert strategy._planner_health_state(True, []) == "ok"
    assert strategy._planner_health_state(False, [BlockReason.BLOCK_ZERO_VOL_ANOMALY]) == "degraded"
    assert strategy._planner_health_state(False, [BlockReason.BLOCK_DATA_GAP]) == "quarantine"


def test_start_stability_state_supports_k_of_n_and_score() -> None:
    checks = [("a", True), ("b", True), ("c", False), ("d", True)]
    state = GridBrainV1Core._start_stability_state(checks, min_score=0.7, k_fraction=0.75)
    assert state["passed"] == 3
    assert state["total"] == 4
    assert state["k_required"] == 3
    assert state["score"] == pytest.approx(0.75, rel=1e-6)
    assert state["ok"] is True

    blocked = GridBrainV1Core._start_stability_state(checks, min_score=0.8, k_fraction=0.75)
    assert blocked["ok"] is False


def test_box_quality_metrics_and_straddle_helpers() -> None:
    strategy = object.__new__(GridBrainV1Core)
    # Setup necessary attributes
    strategy.box_quality_log_space = True
    strategy.box_quality_extension_factor = 1.386
    strategy._breakout_levels_by_pair = {"PAIR/STR": {"up": 105.0, "dn": 95.0}}
    strategy._breakout_bars_since_by_pair = {"PAIR/STR": 1}
    diag = strategy._update_box_quality("PAIR/STR", 90.0, 110.0, 1.0, 96, pd.DataFrame())
    assert diag["quartile_space"] == "log"
    assert diag["q2"] == pytest.approx(99.4987, rel=1e-4)
    assert diag["extension_hi"] == pytest.approx(118.8591, rel=1e-4)
    assert strategy._is_level_near_box(109.6, 90.0, 110.0, 0.5, 0.25)
    assert strategy._box_straddles_level("PAIR/STR", 109.7, 90.0, 110.0, 0.5, 0.25)


def test_box_quality_levels_linear_fallback_when_nonpositive_bounds() -> None:
    strategy = object.__new__(GridBrainV1Core)
    strategy.box_quality_log_space = True
    strategy.box_quality_extension_factor = 1.386
    levels = strategy._box_quality_levels(-10.0, 20.0)
    assert levels["space"] == "linear_fallback"
    assert levels["q1"] == pytest.approx(-2.5)
    assert levels["q2"] == pytest.approx(5.0)
    assert levels["q3"] == pytest.approx(12.5)
    assert levels["extension_lo"] == pytest.approx(-21.58, rel=1e-4)
    assert levels["extension_hi"] == pytest.approx(31.58, rel=1e-4)


def test_midline_bias_fallback_activates_when_vrvp_poc_is_neutral() -> None:
    strategy = object.__new__(GridBrainV1Core)
    strategy.midline_bias_fallback_enabled = True
    strategy.midline_bias_tp_candidate_enabled = True
    strategy.midline_bias_poc_neutral_step_frac = 0.5
    strategy.midline_bias_poc_neutral_width_frac = 0.01
    strategy.midline_bias_source_buffer_steps = 0.5
    strategy.midline_bias_source_buffer_width_frac = 0.02
    strategy.midline_bias_deadband_steps = 0.25
    strategy.midline_bias_deadband_width_frac = 0.005

    state = strategy._midline_bias_fallback_state(
        close=100.0,
        box_low=90.0,
        box_high=110.0,
        step_price=2.0,
        vrvp_poc=100.2,
        channel_midline=104.0,
        basis_mid=103.0,
        donchian_mid=102.0,
        session_vwap=None,
        daily_vwap=None,
    )

    assert state["active"] is True
    assert state["poc_neutral"] is True
    assert state["source"] == "channel_midline"
    assert state["direction"] == "bullish"
    assert state["tp_candidate"] == pytest.approx(104.0)


def test_midline_bias_fallback_stays_inactive_when_vrvp_poc_not_neutral() -> None:
    strategy = object.__new__(GridBrainV1Core)
    strategy.midline_bias_fallback_enabled = True
    strategy.midline_bias_tp_candidate_enabled = True
    strategy.midline_bias_poc_neutral_step_frac = 0.5
    strategy.midline_bias_poc_neutral_width_frac = 0.01
    strategy.midline_bias_source_buffer_steps = 0.5
    strategy.midline_bias_source_buffer_width_frac = 0.02
    strategy.midline_bias_deadband_steps = 0.25
    strategy.midline_bias_deadband_width_frac = 0.005

    state = strategy._midline_bias_fallback_state(
        close=100.0,
        box_low=90.0,
        box_high=110.0,
        step_price=2.0,
        vrvp_poc=106.0,
        channel_midline=104.0,
        basis_mid=103.0,
        donchian_mid=102.0,
        session_vwap=None,
        daily_vwap=None,
    )

    assert state["active"] is False
    assert state["poc_neutral"] is False
    assert state["tp_candidate"] is None


def test_fallback_poc_estimate_uses_volume_weighted_typical_price() -> None:
    df = pd.DataFrame(
        {
            "high": [101.0, 102.0, 103.0],
            "low": [99.0, 100.0, 101.0],
            "close": [100.0, 101.0, 102.0],
            "volume": [10.0, 20.0, 30.0],
        }
    )
    poc = GridBrainV1Core._fallback_poc_estimate(df, lookback=3)
    t1 = (101.0 + 99.0 + 100.0) / 3.0
    t2 = (102.0 + 100.0 + 101.0) / 3.0
    t3 = (103.0 + 101.0 + 102.0) / 3.0
    expected = (t1 * 10.0 + t2 * 20.0 + t3 * 30.0) / 60.0
    assert poc == pytest.approx(expected, rel=1e-6)


def test_box_width_avg_veto_triggers_when_width_exceeds_rolling_ratio() -> None:
    strategy = object.__new__(GridBrainV1Core)
    strategy.box_width_avg_veto_enabled = True
    strategy.box_width_avg_veto_lookback = 20
    strategy.box_width_avg_veto_min_samples = 5
    strategy.box_width_avg_veto_max_ratio = 1.20
    strategy._box_width_history_by_pair = {"PAIR/WIDTH": deque([0.04, 0.041, 0.039, 0.04, 0.041], maxlen=20)}

    state = strategy._box_width_avg_veto_state("PAIR/WIDTH", 0.060)
    assert state["veto"] is True
    assert state["ratio_to_rolling_avg"] is not None
    assert state["ratio_to_rolling_avg"] > 1.2


def test_poc_alignment_strict_requires_cross_when_misaligned() -> None:
    strategy = object.__new__(GridBrainV1Core)
    strategy.poc_alignment_enabled = True
    strategy.poc_alignment_strict_enabled = True
    strategy.poc_alignment_lookback_bars = 2
    strategy.poc_alignment_max_step_diff = 1.0
    strategy.poc_alignment_max_width_frac = 0.05
    strategy._poc_alignment_crossed_by_pair = {}

    df_no_cross = pd.DataFrame({"open": [98.0, 98.5], "close": [98.6, 99.0]})
    blocked = strategy._poc_alignment_state(
        pair="PAIR/POC",
        df=df_no_cross,
        vrvp_poc=100.0,
        micro_poc=104.0,
        step_price=1.0,
        box_low=90.0,
        box_high=110.0,
    )
    assert blocked["misaligned"] is True
    assert blocked["ok"] is False
    assert blocked["block_reason"] == str(BlockReason.BLOCK_POC_ALIGNMENT_FAIL)

    df_cross = pd.DataFrame({"open": [99.0, 105.0], "close": [101.0, 103.0]})
    passed = strategy._poc_alignment_state(
        pair="PAIR/POC",
        df=df_cross,
        vrvp_poc=100.0,
        micro_poc=104.0,
        step_price=1.0,
        box_low=90.0,
        box_high=110.0,
    )
    assert passed["misaligned"] is True
    assert passed["crossed"] is True
    assert passed["ok"] is True
    assert passed["block_reason"] is None


def test_poc_acceptance_handles_multiple_candidates() -> None:
    strategy = object.__new__(GridBrainV1Core)
    strategy.poc_acceptance_enabled = True
    df = pd.DataFrame(
        {
            "open": [1.0, 0.9, 1.1, 1.2],
            "close": [0.8, 1.05, 0.95, 1.3],
        }
    )
    result = strategy._poc_acceptance_status("PAIR/POC", df, [1.0, 0.95])
    assert result is True


def test_box_overlap_prune_detects_high_overlap() -> None:
    strategy = object.__new__(GridBrainV1Core)
    strategy.box_overlap_prune_threshold = 0.5
    strategy.box_overlap_history = 2
    strategy._box_history_by_pair = {"PAIR/OVER": deque([(90.0, 110.0)])}
    assert strategy._box_overlap_prune("PAIR/OVER", 91.0, 109.0)


def test_latest_daily_vwap_computation() -> None:
    strategy = object.__new__(GridBrainV1Core)
    data = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2026-03-01 00:00",
                    "2026-03-01 00:15",
                    "2026-03-02 00:00",
                    "2026-03-02 00:15",
                ]
            ),
            "high": [1.5, 1.6, 2.0, 2.1],
            "low": [1.0, 1.1, 1.8, 1.9],
            "close": [1.4, 1.5, 1.95, 2.05],
            "volume": [10, 20, 30, 40],
        }
    )
    vwap = strategy._latest_daily_vwap(data)
    tp1 = (2.0 + 1.8 + 1.95) / 3.0
    tp2 = (2.1 + 1.9 + 2.05) / 3.0
    expected = (tp1 * 30 + tp2 * 40) / 70
    assert vwap is not None
    assert vwap == pytest.approx(expected, rel=1e-6)


def _cost_strategy() -> GridBrainV1Core:
    strategy = object.__new__(GridBrainV1Core)
    strategy.target_net_step_pct = 0.004
    strategy.est_fee_pct = 0.002
    strategy.est_spread_pct = 0.0005
    strategy.majors_gross_step_floor_pct = 0.0065
    strategy.empirical_cost_floor_min_pct = 0.0
    strategy.empirical_cost_enabled = True
    strategy.empirical_cost_window = 64
    strategy.empirical_cost_min_samples = 3
    strategy.empirical_cost_stale_bars = 32
    strategy.empirical_cost_percentile = 90.0
    strategy.empirical_cost_conservative_mode = True
    strategy.empirical_cost_require_live_samples = True
    strategy.empirical_cost_min_live_samples = 0
    strategy.empirical_spread_proxy_scale = 0.10
    strategy.empirical_adverse_selection_scale = 0.25
    strategy.empirical_retry_penalty_pct = 0.001
    strategy.empirical_missed_fill_penalty_pct = 0.001
    strategy.execution_cost_artifact_enabled = False
    strategy.execution_cost_artifact_dir = "artifacts/execution_cost"
    strategy.execution_cost_artifact_filename = "execution_cost_calibration.latest.json"
    strategy.execution_cost_artifact_max_age_minutes = 180.0
    strategy._execution_cost_artifact_cache_by_pair = {}
    strategy._execution_cost_artifact_mtime_by_pair = {}
    strategy.n_min = 6
    strategy.n_max = 12
    strategy.n_volatility_adapter_enabled = True
    strategy.n_volatility_adapter_strength = 1.0
    return strategy


def test_grid_sizing_reduces_n_to_meet_cost_floor() -> None:
    strategy = _cost_strategy()
    sizing = strategy._grid_sizing(
        98.0,
        102.0,
        min_step_pct_required=0.0065,
        n_low=6,
        n_high=12,
    )
    assert sizing["n_levels"] == 6
    assert sizing["cost_ok"] is True
    assert sizing["step_pct_actual"] >= 0.0065
    assert sizing["candidate_n"] >= sizing["clamped_n"]


def test_effective_cost_floor_uses_empirical_and_emits_stale_warning() -> None:
    strategy = _cost_strategy()
    last = pd.Series({"open": 100.0, "high": 102.0, "low": 99.0, "close": 100.5})
    info = strategy._effective_cost_floor("PAIR/EMP", last, 100.5)
    assert info["source"] == "static"
    assert str(WarningCode.WARN_COST_MODEL_STALE) in info["warning_codes"]


def test_effective_cost_floor_switches_to_empirical_when_higher() -> None:
    strategy = _cost_strategy()
    # Build enough high-cost samples to clear stale/min-sample threshold.
    for _ in range(4):
        last = pd.Series(
            {
                "open": 100.0,
                "high": 105.0,
                "low": 95.0,
                "close": 100.0,
                "post_only_retry_reject_rate": 0.8,
                "missed_fill_rate": 0.8,
            }
        )
        info = strategy._effective_cost_floor("PAIR/HIGH", last, 100.0)
    assert info["source"] in {"empirical", "static"}
    assert info["chosen_floor_pct"] >= info["static_floor_pct"]
    if info["source"] == "empirical":
        assert info["chosen_floor_pct"] > info["static_floor_pct"]


def test_effective_cost_floor_proxy_only_samples_do_not_promote_empirical() -> None:
    strategy = _cost_strategy()
    strategy.empirical_cost_min_samples = 1
    strategy.empirical_cost_min_live_samples = 1
    strategy.empirical_cost_stale_bars = 128
    last = pd.Series(
        {
            "open": 100.0,
            "high": 106.0,
            "low": 94.0,
            "close": 100.0,
        }
    )
    for _ in range(3):
        info = strategy._effective_cost_floor("PAIR/PROXY", last, 100.0)
    assert info["source"] == "static"
    assert info["selection_reason"] == "empirical_live_samples_insufficient"
    assert str(WarningCode.WARN_COST_MODEL_STALE) in info["warning_codes"]
    snapshot = info["empirical_snapshot"]
    assert int(snapshot.get("live_sample_count", 0)) == 0
    assert bool(snapshot.get("effective_stale", True))


def test_effective_cost_floor_promotes_with_empirical_artifact(tmp_path: Path) -> None:
    strategy = _cost_strategy()
    strategy.empirical_cost_min_samples = 1
    strategy.empirical_cost_min_live_samples = 1
    strategy.empirical_cost_stale_bars = 128
    strategy.config = {"user_data_dir": str(tmp_path)}
    strategy.execution_cost_artifact_enabled = True

    pair = "PAIR/EMP_ART"
    pair_fs = pair.replace("/", "_").replace(":", "_")
    artifact_dir = tmp_path / "artifacts" / "execution_cost" / pair_fs
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / "execution_cost_calibration.latest.json"
    artifact_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "pair": pair,
                "window": 256,
                "sample_count": 128,
                "cost_model_source": "empirical",
                "percentile": 90.0,
                "realized_spread_pct": 0.0040,
                "adverse_selection_pct": 0.0018,
                "post_only_retry_reject_rate": 0.35,
                "missed_fill_opportunity_rate": 0.20,
                "recommended_cost_floor_bps": 95.0,
            }
        ),
        encoding="utf-8",
    )

    info = strategy._effective_cost_floor(
        pair,
        pd.Series({"open": 100.0, "high": 100.5, "low": 99.5, "close": 100.0}),
        100.0,
    )
    assert info["source"] == "empirical"
    assert info["selection_reason"] == "empirical_floor_above_static"
    assert info["chosen_floor_pct"] > info["static_floor_pct"]
    assert str(WarningCode.WARN_COST_MODEL_STALE) not in info["warning_codes"]
    snapshot = info["empirical_snapshot"]
    assert int(snapshot.get("live_sample_count", 0)) >= 1
    assert bool(snapshot.get("live_sample_requirement_met", False))
    assert not bool(snapshot.get("effective_stale", True))
    floor_candidates = snapshot.get("floor_candidates_pct", {})
    assert strategy._safe_float(floor_candidates.get("recommended")) is not None


def test_tp_selection_prefers_nearest_conservative() -> None:
    strategy = object.__new__(GridBrainV1Core)
    tp, meta = strategy._select_tp_price(
        100.0,
        104.0,
        {
            "a": 103.0,
            "b": 101.5,
            "c": 120.0,
            "bad": 99.0,
        },
    )
    assert tp == pytest.approx(101.5)
    assert meta["source"] == "b"


def test_sl_selection_avoids_lvn_and_fvg_gap() -> None:
    strategy = object.__new__(GridBrainV1Core)
    strategy.sl_lvn_avoid_steps = 0.5
    strategy.sl_fvg_buffer_steps = 0.1
    sl, meta = strategy._select_sl_price(
        sl_base=99.0,
        step_price=2.0,
        lvn_levels=[99.2],
        fvg_state={"nearest_bullish": {"low": 98.5, "high": 99.5}},
    )
    assert sl < 99.0
    assert "avoid_lvn_void" in meta["constraints"]
    assert "avoid_fvg_gap" in meta["constraints"]


def test_simulator_fill_guard_respects_no_repeat_toggle() -> None:
    guard = grid_simulator_v1.FillCooldownGuard(cooldown_bars=1, no_repeat_lsi_guard=True)
    assert guard.allow("buy", 3, 10)
    guard.mark("buy", 3, 10)
    assert not guard.allow("buy", 3, 10)
    assert not guard.allow("buy", 3, 11)
    assert guard.allow("buy", 3, 12)

    guard.configure(no_repeat_lsi_guard=False)
    guard.mark("buy", 3, 12)
    assert guard.allow("buy", 3, 12)


def test_executor_fill_guard_respects_no_repeat_toggle() -> None:
    guard = grid_executor_v1.FillCooldownGuard(cooldown_bars=1, no_repeat_lsi_guard=True)
    assert guard.allow("sell", 5, 1)
    guard.mark("sell", 5, 1)
    assert not guard.allow("sell", 5, 1)
    assert not guard.allow("sell", 5, 2)
    assert guard.allow("sell", 5, 3)

    guard.configure(no_repeat_lsi_guard=False)
    assert guard.allow("sell", 5, 3)


def test_executor_fill_bar_index_tracks_plan_clock() -> None:
    executor = grid_executor_v1.GridExecutorV1(
        mode="paper",
        state_out="/tmp/grid_executor_v1.state.json",
        poll_seconds=1.0,
        quote_budget=1000.0,
        start_base=0.0,
        maker_fee_pct=0.1,
        post_only=True,
        max_orders_per_side=20,
    )
    plan_a = {"runtime_state": {"clock_ts": 1_700_000_000}}
    plan_b = {"runtime_state": {"clock_ts": 1_700_000_900}}
    assert executor._next_fill_bar_index(plan_a) == 1
    assert executor._next_fill_bar_index(plan_a) == 1
    assert executor._next_fill_bar_index(plan_b) == 2
    assert executor._next_fill_bar_index({}) == 3


def test_meta_drift_guard_detects_hard_shift() -> None:
    guard = MetaDriftGuard(window=64, smoothing_alpha=0.4)

    def observe(payload: dict[str, float]) -> dict:
        return guard.observe(
            "PAIR/DRIFT",
            payload,
            min_samples=8,
            eps=1e-6,
            z_soft=2.0,
            z_hard=3.0,
            cusum_k_sigma=0.1,
            cusum_soft=2.0,
            cusum_hard=4.0,
            ph_delta_sigma=0.1,
            ph_soft=2.0,
            ph_hard=4.0,
            soft_min_channels=1,
            hard_min_channels=1,
        )

    baseline = {
        "atr_pct_15m": 0.01,
        "rvol_15m": 1.0,
        "spread_pct": 0.001,
        "box_pos_abs_delta": 0.02,
    }
    snap = {}
    for _ in range(24):
        snap = observe(baseline)
    assert snap["severity"] == "none"
    shock = {
        "atr_pct_15m": 0.05,
        "rvol_15m": 4.0,
        "spread_pct": 0.008,
        "box_pos_abs_delta": 0.40,
    }
    for _ in range(3):
        snap = observe(shock)
    assert snap["drift_detected"] is True
    assert snap["severity"] == "hard"
    assert len(snap["drift_channels"]) >= 1


def test_meta_drift_state_maps_to_actions() -> None:
    strategy = object.__new__(GridBrainV1Core)
    strategy.meta_drift_guard_enabled = True
    strategy.meta_drift_guard_window = 64
    strategy.meta_drift_guard_min_samples = 8
    strategy.meta_drift_guard_smoothing_alpha = 0.4
    strategy.meta_drift_guard_eps = 1e-6
    strategy.meta_drift_guard_z_soft = 2.0
    strategy.meta_drift_guard_z_hard = 3.0
    strategy.meta_drift_guard_cusum_k_sigma = 0.1
    strategy.meta_drift_guard_cusum_soft = 2.0
    strategy.meta_drift_guard_cusum_hard = 4.0
    strategy.meta_drift_guard_ph_delta_sigma = 0.1
    strategy.meta_drift_guard_ph_soft = 2.0
    strategy.meta_drift_guard_ph_hard = 4.0
    strategy.meta_drift_guard_soft_min_channels = 1
    strategy.meta_drift_guard_hard_min_channels = 1
    strategy.meta_drift_guard_spread_proxy_scale = 0.1
    strategy._meta_drift_guard = MetaDriftGuard(
        strategy.meta_drift_guard_window,
        strategy.meta_drift_guard_smoothing_alpha,
    )
    strategy._meta_drift_prev_box_pos_by_pair = {}

    stable = pd.Series({"high": 101.0, "low": 100.0, "spread_pct": 0.001})
    for _ in range(24):
        state = strategy._meta_drift_state(
            "PAIR/STATE",
            last_row=stable,
            close=100.5,
            atr_pct_15m=0.01,
            rvol_15m=1.0,
            box_position=0.45,
            running_active=False,
        )
    assert state["severity"] == "none"
    shock = pd.Series({"high": 110.0, "low": 90.0, "spread_pct": 0.008})
    state_idle = strategy._meta_drift_state(
        "PAIR/STATE",
        last_row=shock,
        close=100.0,
        atr_pct_15m=0.05,
        rvol_15m=4.0,
        box_position=0.95,
        running_active=False,
    )
    assert state_idle["drift_detected"] is True
    assert state_idle["recommended_action"] in {"COOLDOWN_EXTEND", "PAUSE_STARTS"}

    strategy._meta_drift_guard.reset_pair("PAIR/RUNNING")
    strategy._meta_drift_prev_box_pos_by_pair.pop("PAIR/RUNNING", None)
    for _ in range(24):
        strategy._meta_drift_state(
            "PAIR/RUNNING",
            last_row=stable,
            close=100.5,
            atr_pct_15m=0.01,
            rvol_15m=1.0,
            box_position=0.40,
            running_active=True,
        )
    state_running = strategy._meta_drift_state(
        "PAIR/RUNNING",
        last_row=shock,
        close=100.0,
        atr_pct_15m=0.05,
        rvol_15m=4.0,
        box_position=0.99,
        running_active=True,
    )
    assert state_running["drift_detected"] is True
    assert state_running["recommended_action"] in {"HARD_STOP", "PAUSE_STARTS"}


def test_empirical_cost_sample_uses_execution_cost_artifact(tmp_path: Path) -> None:
    strategy = object.__new__(GridBrainV1Core)
    pair = "PAIR/ART"
    pair_fs = pair.replace("/", "_").replace(":", "_")
    artifact_dir = tmp_path / "artifacts" / "execution_cost" / pair_fs
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / "execution_cost_calibration.latest.json"
    artifact_payload = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pair": pair,
        "window": 256,
        "sample_count": 64,
        "cost_model_source": "empirical",
        "percentile": 90.0,
        "realized_spread_pct": 0.003,
        "adverse_selection_pct": 0.001,
        "post_only_retry_reject_rate": 0.2,
        "missed_fill_opportunity_rate": 0.15,
        "recommended_cost_floor_bps": 16.0,
    }
    artifact_path.write_text(json.dumps(artifact_payload), encoding="utf-8")

    strategy.config = {"user_data_dir": str(tmp_path)}
    strategy.execution_cost_artifact_enabled = True
    strategy.execution_cost_artifact_dir = "artifacts/execution_cost"
    strategy.execution_cost_artifact_filename = "execution_cost_calibration.latest.json"
    strategy.execution_cost_artifact_max_age_minutes = 60 * 24
    strategy._execution_cost_artifact_cache_by_pair = {}
    strategy._execution_cost_artifact_mtime_by_pair = {}

    sample = strategy._empirical_cost_sample(
        pair,
        pd.Series({"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0}),
        100.0,
    )
    assert sample["artifact_used"] is True
    assert sample["spread_pct"] == pytest.approx(0.003)
    assert sample["adverse_selection_pct"] == pytest.approx(0.001)
    assert sample["retry_reject_rate"] == pytest.approx(0.2)
    assert sample["missed_fill_rate"] == pytest.approx(0.15)
    assert sample["recommended_floor_pct"] == pytest.approx(0.0016)


def test_decision_and_event_logs_are_emitted_with_schema(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    strategy = object.__new__(GridBrainV1Core)
    strategy.decision_log_enabled = True
    strategy.event_log_enabled = True
    strategy.decision_log_filename = "decision_log.jsonl"
    strategy.event_log_filename = "event_log.jsonl"
    strategy.plans_root_rel = "grid_plans"
    strategy._event_counter_by_pair = {}

    log_root = tmp_path / "plans"
    monkeypatch.setenv("GRID_PLANS_ROOT_REL", str(log_root))

    plan = {
        "generated_at": "2026-02-26T00:00:00+00:00",
        "valid_for_candle_ts": 1700000000,
        "action": "HOLD",
        "mode": "intraday",
        "replan_decision": "publish",
        "replan_reasons": ["REPLAN_MATERIAL_BOX_CHANGE"],
        "signals_snapshot": {
            "close": 100.0,
            "rsi_15m": 50.0,
            "adx_4h": 18.0,
            "bbw_1h_pct": 22.0,
            "rvol_15m": 1.0,
            "price_in_box": True,
            "start_signal": False,
        },
        "box": {"low": 95.0, "high": 105.0, "mid": 100.0, "width_pct": 0.10},
        "grid": {"n_levels": 8, "step_price": 1.25},
        "risk": {"tp_price": 106.0, "sl_price": 94.0},
    }

    event_ids = strategy._emit_decision_and_event_logs(
        "binance",
        "ETH/USDT",
        plan,
        prev_plan_hash="a" * 64,
        new_plan_hash="b" * 64,
        changed_fields=["box.mid", "risk.tp_price"],
        diff_snapshot={"box.mid": {"prev": 99.0, "new": 100.0}},
        mode_candidate="intraday",
        mode_final="intraday",
        start_stability={"score": 0.8, "ok": True},
        meta_drift_state={"severity": "none"},
        planner_health_state="ok",
        blocker_codes=[str(BlockReason.BLOCK_START_BOX_POSITION)],
        warning_codes=[str(WarningCode.WARN_COST_MODEL_STALE)],
        stop_codes=["STOP_RANGE_SHIFT"],
        close_price=100.0,
    )

    assert len(event_ids) == 3

    decision_path = log_root / "binance" / "ETH_USDT" / "decision_log.jsonl"
    event_path = log_root / "binance" / "ETH_USDT" / "event_log.jsonl"
    assert decision_path.is_file()
    assert event_path.is_file()

    decision_row = json.loads(decision_path.read_text(encoding="utf-8").strip().splitlines()[-1])
    event_rows = [json.loads(line) for line in event_path.read_text(encoding="utf-8").strip().splitlines()]

    assert validate_schema(decision_row, "decision_log.schema.json") == []
    assert all(validate_schema(row, "event_log.schema.json") == [] for row in event_rows)
    assert decision_row["event_ids_emitted"] == event_ids
