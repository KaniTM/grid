from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from core.enums import BlockReason, EventType, StopReason
from core.schema_validation import validate_schema
from freqtrade.user_data.strategies.GridBrainV1 import GridBrainV1Core


def _new_strategy() -> GridBrainV1Core:
    return object.__new__(GridBrainV1Core)


def test_protections_drawdown_and_stop_window_helpers() -> None:
    strategy = _new_strategy()
    strategy.drawdown_guard_enabled = True
    strategy.drawdown_guard_lookback_bars = 8
    strategy.drawdown_guard_max_pct = 0.10

    df = pd.DataFrame({"close": [100.0, 104.0, 102.0, 99.0, 93.0]})
    dd = strategy._drawdown_guard_state(df)
    assert dd["triggered"] is True
    assert dd["drawdown_pct"] >= 0.10

    strategy.max_stops_window_enabled = True
    strategy.max_stops_window_minutes = 60
    strategy.max_stops_window_count = 3
    strategy._stop_timestamps_by_pair = {}

    pair = "ETH/USDT"
    state0 = strategy._max_stops_window_state(pair, clock_ts=3600)
    assert state0["blocked"] is False

    strategy._register_stop_timestamp(pair, 3500)
    strategy._register_stop_timestamp(pair, 3550)
    strategy._register_stop_timestamp(pair, 3590)
    state1 = strategy._max_stops_window_state(pair, clock_ts=3600)
    assert state1["blocked"] is True
    assert state1["block_reason"] == str(BlockReason.BLOCK_MAX_STOPS_WINDOW)


def test_micro_bias_order_flow_and_reentry_helpers() -> None:
    strategy = _new_strategy()

    buy_ratio = strategy._micro_buy_ratio_state(
        edges=[90.0, 95.0, 100.0, 105.0],
        density=[0.50, 0.35, 0.15],
        box_low=90.0,
        box_high=105.0,
        close=97.0,
        midband_half_width=0.40,
        bullish_threshold=0.58,
        bearish_threshold=0.42,
    )
    assert buy_ratio["ready"] is True
    assert buy_ratio["bias"] == 1

    levels = np.array([90.0, 95.0, 100.0, 105.0], dtype=float)
    base = [1.0, 1.0, 1.0, 1.0]
    weighted = strategy._apply_buy_ratio_rung_bias(
        levels,
        base,
        box_low=90.0,
        box_high=105.0,
        bias=1,
        strength=0.35,
        w_min=0.2,
        w_max=3.0,
    )
    assert weighted[0] > weighted[-1]

    strategy.order_flow_enabled = True
    strategy.order_flow_spread_soft_max_pct = 0.002
    strategy.order_flow_depth_thin_soft_max = 0.6
    strategy.order_flow_imbalance_extreme = 0.8
    strategy.order_flow_jump_soft_max_pct = 0.006
    strategy.order_flow_soft_veto_min_flags = 2
    strategy.order_flow_hard_block = True
    strategy.order_flow_confidence_penalty_per_flag = 0.1

    flow = strategy._order_flow_state(
        last_row=pd.Series(
            {
                "spread_pct": 0.003,
                "depth_thinning_score": 0.75,
                "orderbook_imbalance": 0.9,
            }
        ),
        close=100.0,
        prev_close=99.0,
    )
    assert flow["soft_veto"] is True
    assert flow["hard_block"] is True
    assert str(EventType.EVENT_SPREAD_SPIKE) in flow["flags"]

    strategy.micro_reentry_pause_bars = 4
    strategy.micro_reentry_require_poc_reclaim = True
    strategy.micro_reentry_poc_buffer_steps = 0.25
    strategy._micro_reentry_pause_until_ts_by_pair = {"ETH/USDT": 200}

    blocked = strategy._micro_reentry_state(
        pair="ETH/USDT",
        clock_ts=100,
        close=99.0,
        micro_poc=100.0,
        step_price=2.0,
    )
    assert blocked["active"] is True
    assert blocked["block_reason"] == str(BlockReason.BLOCK_RECLAIM_NOT_CONFIRMED)

    reclaimed = strategy._micro_reentry_state(
        pair="ETH/USDT",
        clock_ts=110,
        close=100.0,
        micro_poc=100.0,
        step_price=2.0,
    )
    assert reclaimed["active"] is False


def test_fvg_vp_channel_and_session_sweep_helpers() -> None:
    strategy = _new_strategy()

    strategy.fvg_vp_enabled = True
    strategy.fvg_vp_bins = 16
    strategy.fvg_vp_lookback_bars = 64
    strategy.fvg_vp_poc_tag_step_frac = 0.3

    strategy.smart_channel_enabled = True
    strategy.smart_channel_breakout_step_buffer = 0.25
    strategy.smart_channel_volume_confirm_enabled = True
    strategy.smart_channel_volume_rvol_min = 1.0
    strategy.smart_channel_tp_nudge_step_multiple = 0.5

    strategy.session_sweep_enabled = True
    strategy.session_sweep_retest_lookback_bars = 2

    df = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2026-02-25T00:00:00Z",
                    "2026-02-25T00:15:00Z",
                    "2026-02-25T00:30:00Z",
                    "2026-02-25T00:45:00Z",
                ],
                utc=True,
            ),
            "open": [100.0, 101.0, 105.8, 104.5],
            "high": [102.0, 106.0, 106.5, 107.0],
            "low": [99.0, 100.0, 103.5, 102.0],
            "close": [101.0, 106.2, 104.0, 106.8],
            "volume": [10.0, 12.0, 15.0, 14.0],
        }
    )

    fvg_state = {
        "nearest_bullish": {"low": 99.0, "high": 103.0},
        "nearest_bearish": {"low": 104.0, "high": 107.0},
    }
    fvg_vp = strategy._fvg_vp_state(df, fvg_state=fvg_state, close=106.8, step_price=1.0)
    assert fvg_vp["enabled"] is True
    assert fvg_vp["nearest_poc"] is not None

    channel = strategy._smart_channel_state(
        df,
        close=106.8,
        step_price=1.0,
        channel_midline=103.0,
        channel_upper=106.0,
        channel_lower=100.0,
        donchian_high=106.0,
        donchian_low=99.0,
        rvol_15m=1.2,
    )
    assert channel["stop_triggered"] is True

    sweep = strategy._session_sweep_state(df.iloc[:3].copy())
    assert sweep["sweep_high"] is True
    assert sweep["break_retest_high"] is True


def test_event_bus_emits_reason_and_taxonomy_events(tmp_path: Path, monkeypatch) -> None:
    strategy = _new_strategy()
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
        changed_fields=["box.mid"],
        diff_snapshot={},
        mode_candidate="intraday",
        mode_final="intraday",
        start_stability={"score": 0.9, "ok": True},
        meta_drift_state={"severity": "none"},
        planner_health_state="ok",
        blocker_codes=[str(BlockReason.BLOCK_START_BOX_POSITION)],
        warning_codes=[],
        stop_codes=[str(StopReason.STOP_RANGE_SHIFT)],
        close_price=100.0,
        event_types=[str(EventType.EVENT_SESSION_HIGH_SWEEP)],
        event_metadata={str(EventType.EVENT_SESSION_HIGH_SWEEP): {"level": 105.0}},
    )

    assert len(event_ids) == 3

    event_path = log_root / "binance" / "ETH_USDT" / "event_log.jsonl"
    event_rows = [json.loads(line) for line in event_path.read_text(encoding="utf-8").strip().splitlines()]
    assert all(validate_schema(row, "event_log.schema.json") == [] for row in event_rows)
    taxonomy_rows = [row for row in event_rows if row["event_type"] == str(EventType.EVENT_SESSION_HIGH_SWEEP)]
    assert taxonomy_rows
    assert taxonomy_rows[-1]["metadata"]["taxonomy_event"] is True
    assert float(taxonomy_rows[-1]["metadata"]["level"]) == 105.0
