from __future__ import annotations

import pandas as pd

from planner.structure.order_blocks import OrderBlockConfig, build_order_block_snapshot
from freqtrade.user_data.strategies.GridBrainV1 import GridBrainV1Core


def _new_strategy() -> GridBrainV1Core:
    return object.__new__(GridBrainV1Core)


def _bull_ob_df() -> pd.DataFrame:
    dates = pd.date_range("2026-01-01", periods=6, freq="1h", tz="UTC")
    return pd.DataFrame(
        {
            "date": dates,
            "open": [100.0, 100.1, 99.9, 101.5, 101.8, 101.2],
            "high": [100.5, 100.4, 101.8, 102.0, 102.1, 101.5],
            "low": [99.8, 99.7, 99.8, 101.0, 100.9, 100.7],
            "close": [100.1, 99.9, 101.5, 101.8, 101.2, 101.0],
        }
    )


def _bear_ob_df() -> pd.DataFrame:
    dates = pd.date_range("2026-01-01", periods=8, freq="1h", tz="UTC")
    return pd.DataFrame(
        {
            "date": dates,
            "open": [100.0, 100.2, 101.0, 101.8, 100.3, 99.4, 98.6, 98.8],
            "high": [100.5, 101.0, 102.0, 102.1, 100.8, 99.8, 99.0, 99.2],
            "low": [99.6, 99.9, 100.5, 100.0, 99.2, 98.4, 98.2, 98.5],
            "close": [100.2, 100.8, 101.8, 100.3, 99.4, 98.6, 98.8, 99.0],
        }
    )


def _as_strategy_df(df_1h: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({"date": pd.to_datetime(df_1h["date"], utc=True)})
    out["open_1h"] = df_1h["open"]
    out["high_1h"] = df_1h["high"]
    out["low_1h"] = df_1h["low"]
    out["close_1h"] = df_1h["close"]
    return out


def test_order_block_detects_bull_and_mitigation() -> None:
    cfg = OrderBlockConfig(
        enabled=True,
        tf="1h",
        use_wick_zone=True,
        impulse_lookahead=2,
        impulse_atr_len=2,
        impulse_atr_mult=1.0,
        fresh_bars=20,
        max_age_bars=400,
        mitigation_mode="wick",
    )
    snapshot = build_order_block_snapshot(_bull_ob_df(), cfg)

    assert snapshot.bull_valid is True
    assert snapshot.bull is not None
    assert snapshot.bull.mitigated is True
    assert snapshot.bull.top > snapshot.bull.bottom
    assert snapshot.bull.mid == (snapshot.bull.top + snapshot.bull.bottom) / 2.0


def test_order_block_detects_bear_and_freshness_window() -> None:
    cfg = OrderBlockConfig(
        enabled=True,
        tf="1h",
        use_wick_zone=True,
        impulse_lookahead=3,
        impulse_atr_len=2,
        impulse_atr_mult=1.0,
        fresh_bars=2,
        max_age_bars=400,
        mitigation_mode="close",
    )
    snapshot = build_order_block_snapshot(_bear_ob_df(), cfg)

    assert snapshot.bear_valid is True
    assert snapshot.bear is not None
    assert snapshot.bear_fresh is False
    assert snapshot.bear_age_bars is not None and snapshot.bear_age_bars > cfg.fresh_bars


def test_order_block_strategy_state_applies_fresh_gate_straddle_and_tp_nudges() -> None:
    strategy = _new_strategy()
    strategy.ob_enabled = True
    strategy.ob_tf = "1h"
    strategy.ob_use_wick_zone = True
    strategy.ob_impulse_lookahead = 3
    strategy.ob_impulse_atr_len = 2
    strategy.ob_impulse_atr_mult = 1.0
    strategy.ob_fresh_bars = 20
    strategy.ob_max_age_bars = 400
    strategy.ob_mitigation_mode = "close"
    strategy.ob_straddle_min_step_mult = 1.0
    strategy.ob_tp_nudge_max_steps = 4.0
    strategy._ob_state_by_pair = {}

    frame = _as_strategy_df(_bear_ob_df())
    state = strategy._order_block_state(
        pair="ETH/USDT",
        dataframe=frame,
        close=99.0,
        step_price=1.0,
        box_low=99.0,
        box_high=100.2,
    )

    assert state["fresh_block"] is True
    assert "bear" in state["fresh_block_sides"]
    assert state["straddle_veto"] is True
    assert state["tp_mid"] is not None
    assert state["tp_edge"] is not None
