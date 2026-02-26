from __future__ import annotations

import pandas as pd

from planner.structure.liquidity_sweeps import LiquiditySweepConfig, analyze_liquidity_sweeps


def _sweep_df() -> pd.DataFrame:
    dates = pd.date_range("2026-01-02", periods=10, freq="15min", tz="UTC")
    return pd.DataFrame(
        {
            "date": dates,
            "open": [100.0, 100.0, 101.0, 102.0, 103.0, 104.0, 102.5, 102.0, 106.2, 104.7],
            "high": [101.0, 102.0, 103.0, 104.0, 105.0, 103.5, 103.0, 106.0, 105.3, 105.4],
            "low": [99.0, 99.5, 100.0, 101.0, 102.0, 101.5, 101.0, 101.8, 104.8, 103.8],
            "close": [100.0, 101.0, 102.0, 103.0, 104.0, 102.5, 102.0, 105.6, 104.7, 104.5],
        }
    )


def _base_cfg() -> LiquiditySweepConfig:
    return LiquiditySweepConfig(
        enabled=True,
        pivot_len=2,
        max_age_bars=200,
        break_buffer_mode="step",
        break_buffer_value=0.2,
        retest_window_bars=12,
        retest_buffer_mode="step",
        retest_buffer_value=0.2,
        stop_if_through_box_edge=True,
        retest_validation_mode="Wick",
        min_level_separation_steps=1.0,
    )


def test_pivot_confirmation_is_bar_confirmed() -> None:
    cfg = _base_cfg()

    pre_confirm = analyze_liquidity_sweeps(
        _sweep_df().iloc[:6].copy(),
        cfg=cfg,
        step_price=1.0,
        box_low=99.0,
        box_high=105.0,
    )
    assert pre_confirm["swing_high"] is None

    confirmed = analyze_liquidity_sweeps(
        _sweep_df().iloc[:8].copy(),
        cfg=cfg,
        step_price=1.0,
        box_low=99.0,
        box_high=105.0,
    )
    assert confirmed["swing_high"] is not None


def test_wick_sweep_and_break_retest_stop_through_box_edge() -> None:
    cfg = _base_cfg()
    state = analyze_liquidity_sweeps(
        _sweep_df().iloc[:9].copy(),
        cfg=cfg,
        step_price=1.0,
        box_low=99.0,
        box_high=105.0,
        event_hold_bars=2,
    )

    assert state["break_retest_high"] is True
    assert state["through_box_edge"] is True
    assert state["stop_triggered"] is True
    assert state["sweep_high"] is True


def test_retest_validation_mode_toggle_affects_break_retest_only() -> None:
    wick_cfg = _base_cfg()
    open_cfg = LiquiditySweepConfig(**{**wick_cfg.__dict__, "retest_validation_mode": "Open"})

    wick_state = analyze_liquidity_sweeps(
        _sweep_df().iloc[:9].copy(),
        cfg=wick_cfg,
        step_price=1.0,
        box_low=99.0,
        box_high=105.0,
    )
    open_state = analyze_liquidity_sweeps(
        _sweep_df().iloc[:9].copy(),
        cfg=open_cfg,
        step_price=1.0,
        box_low=99.0,
        box_high=105.0,
    )

    assert wick_state["swing_high"] == open_state["swing_high"]
    assert wick_state["sweep_high"] == open_state["sweep_high"]
    assert wick_state["break_retest_high"] is True
    assert open_state["break_retest_high"] is False


def test_determinism_for_same_inputs() -> None:
    cfg = _base_cfg()
    frame = _sweep_df().copy()
    first = analyze_liquidity_sweeps(
        frame,
        cfg=cfg,
        step_price=1.0,
        box_low=99.0,
        box_high=105.0,
    )
    second = analyze_liquidity_sweeps(
        frame,
        cfg=cfg,
        step_price=1.0,
        box_low=99.0,
        box_high=105.0,
    )
    assert first == second
