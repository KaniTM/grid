# ruff: noqa: S101

import pandas as pd
import pytest
from core.enums import BlockReason, StopReason
from freqtrade.user_data.strategies.GridBrainV1 import GridBrainV1Core


def _strategy_for_breakout_buffer(mode: str, value: float) -> GridBrainV1Core:
    strategy = object.__new__(GridBrainV1Core)
    strategy.breakout_confirm_buffer_mode = mode
    strategy.breakout_confirm_buffer_value = value
    return strategy


def _close_df(values: list[float]) -> pd.DataFrame:
    return pd.DataFrame({"close": [float(x) for x in values]})


def test_min_range_len_gate_blocks_before_threshold() -> None:
    out = GridBrainV1Core._range_len_gate_state(
        current_bar_index=110,
        box_built_at_bar_index=100,
        min_range_len_bars=20,
        box_gen_id="box-a",
    )
    assert out["ok"] is False
    assert int(out["range_len_bars_current"]) == 11
    assert int(out["min_range_len_bars"]) == 20
    assert out["box_gen_id"] == "box-a"
    assert out["block_reason"] == str(BlockReason.BLOCK_MIN_RANGE_LEN_NOT_MET)


def test_min_range_len_gate_passes_at_threshold() -> None:
    out = GridBrainV1Core._range_len_gate_state(
        current_bar_index=119,
        box_built_at_bar_index=100,
        min_range_len_bars=20,
        box_gen_id="box-a",
    )
    assert out["ok"] is True
    assert int(out["range_len_bars_current"]) == 20
    assert out["block_reason"] is None


def test_min_range_len_gate_resets_on_new_box_generation() -> None:
    old_box = GridBrainV1Core._range_len_gate_state(
        current_bar_index=120,
        box_built_at_bar_index=90,
        min_range_len_bars=20,
        box_gen_id="box-old",
    )
    new_box = GridBrainV1Core._range_len_gate_state(
        current_bar_index=120,
        box_built_at_bar_index=119,
        min_range_len_bars=20,
        box_gen_id="box-new",
    )
    assert old_box["ok"] is True
    assert new_box["ok"] is False
    assert int(new_box["range_len_bars_current"]) == 2


def test_breakout_confirm_single_close_outside_is_not_confirmed() -> None:
    df = _close_df([100.0, 101.2])
    out = GridBrainV1Core._breakout_confirm_state(
        df,
        box_low=95.0,
        box_high=100.0,
        buffer=1.0,
        confirm_bars=2,
    )
    assert out["enabled"] is True
    assert out["enough_history"] is True
    assert out["confirmed_up"] is False
    assert out["confirmed_dn"] is False


def test_breakout_confirm_up_blocks_start_when_not_running() -> None:
    df = _close_df([101.5, 101.6])
    confirm = GridBrainV1Core._breakout_confirm_state(
        df,
        box_low=95.0,
        box_high=100.0,
        buffer=1.0,
        confirm_bars=2,
    )
    reasons = GridBrainV1Core._breakout_confirm_reason_state(
        confirmed_up=bool(confirm["confirmed_up"]),
        confirmed_dn=bool(confirm["confirmed_dn"]),
        running_active=False,
    )
    assert reasons["block_reason"] == str(BlockReason.BLOCK_BREAKOUT_CONFIRM_UP)
    assert reasons["stop_reason"] is None
    assert reasons["gate_ok"] is False


def test_breakout_confirm_dn_stops_when_running() -> None:
    df = _close_df([93.7, 93.6])
    confirm = GridBrainV1Core._breakout_confirm_state(
        df,
        box_low=95.0,
        box_high=100.0,
        buffer=1.0,
        confirm_bars=2,
    )
    reasons = GridBrainV1Core._breakout_confirm_reason_state(
        confirmed_up=bool(confirm["confirmed_up"]),
        confirmed_dn=bool(confirm["confirmed_dn"]),
        running_active=True,
    )
    assert reasons["stop_reason"] == str(StopReason.STOP_BREAKOUT_CONFIRM_DN)
    assert reasons["block_reason"] is None


@pytest.mark.parametrize(
    "mode,value,step,atr,close,expected",
    [
        ("step", 1.0, 2.5, 1.2, 100.0, 2.5),
        ("atr", 1.5, 2.5, 1.2, 100.0, 1.8),
        ("pct", 0.01, 2.5, 1.2, 100.0, 1.0),
        ("abs", 0.75, 2.5, 1.2, 100.0, 0.75),
    ],
)
def test_breakout_confirm_buffer_modes(
    mode: str,
    value: float,
    step: float,
    atr: float,
    close: float,
    expected: float,
) -> None:
    strategy = _strategy_for_breakout_buffer(mode, value)
    out = strategy._breakout_confirm_buffer(step_price=step, atr_15m=atr, close=close)
    assert out == pytest.approx(expected, rel=1e-9, abs=1e-12)


def test_breakout_confirm_determinism_on_same_input() -> None:
    df = _close_df([100.0, 101.5, 101.6])
    first = GridBrainV1Core._breakout_confirm_state(
        df,
        box_low=95.0,
        box_high=100.0,
        buffer=1.0,
        confirm_bars=2,
    )
    second = GridBrainV1Core._breakout_confirm_state(
        df,
        box_low=95.0,
        box_high=100.0,
        buffer=1.0,
        confirm_bars=2,
    )
    assert first == second
