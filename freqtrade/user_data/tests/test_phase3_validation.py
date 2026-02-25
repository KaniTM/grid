# ruff: noqa: S101

import pandas as pd
from core.enums import BlockReason, MaterialityClass
from freqtrade.user_data.strategies.GridBrainV1 import GridBrainV1Core


def test_box_signature_is_repeatable() -> None:
    sig = GridBrainV1Core._box_signature(1.23456789, 1.34567891, 48, 0.25000001)
    assert sig.startswith("1.23456789:1.34567891:48:0.25000001")
    assert ":" in sig


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
