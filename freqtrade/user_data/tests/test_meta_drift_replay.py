# ruff: noqa: S101

import pandas as pd

from freqtrade.user_data.scripts import grid_simulator_v1


def _build_replay_df() -> pd.DataFrame:
    dates = pd.date_range("2026-01-01 00:00:00", periods=12, freq="15min")
    return pd.DataFrame(
        {
            "date": dates,
            "open": [100.0] * len(dates),
            "high": [101.0] * len(dates),
            "low": [99.0] * len(dates),
            "close": [100.0] * len(dates),
        }
    )


def _plan_at(
    ts: pd.Timestamp,
    action: str,
    *,
    start_block_reasons: list[str] | None = None,
    stop_reason_flags: list[str] | None = None,
) -> dict:
    step_price = (105.0 - 95.0) / 6.0
    block_reasons = list(start_block_reasons or [])
    stop_flags = list(stop_reason_flags or [])
    return {
        "_plan_time": pd.Timestamp(ts),
        "ts": pd.Timestamp(ts).isoformat(),
        "action": str(action),
        "symbol": "PAIR/DRIFT",
        "range": {"low": 95.0, "high": 105.0},
        "grid": {"n_levels": 6, "step_price": float(step_price)},
        "runtime_state": {
            "clock_ts": int(pd.Timestamp(ts).timestamp()),
            "start_block_reasons": [str(x) for x in block_reasons],
            "stop_reason_flags_applied_active": [str(x) for x in stop_flags],
        },
        "diagnostics": {
            "start_block_reasons": [str(x) for x in block_reasons],
            "stop_reason_flags_applied_active": [str(x) for x in stop_flags],
        },
        "risk": {
            "stop_reasons": {str(x): True for x in stop_flags},
        },
    }


def test_replay_synthetic_regime_shift_tracks_meta_drift_soft_and_hard() -> None:
    df = _build_replay_df()
    plans = [
        _plan_at(df["date"].iloc[0], "START"),
        _plan_at(df["date"].iloc[4], "HOLD", start_block_reasons=["BLOCK_META_DRIFT_SOFT"]),
        _plan_at(df["date"].iloc[7], "STOP", stop_reason_flags=["meta_drift_hard_stop"]),
    ]
    res = grid_simulator_v1.simulate_grid_replay(
        df=df,
        plans=plans,
        start_quote=1000.0,
        start_base=0.0,
        maker_fee_pct=0.10,
        touch_fill=True,
    )

    summary = res["summary"]
    assert int(summary.get("stop_events", 0)) >= 1
    assert int((summary.get("hold_reason_counts") or {}).get("BLOCK_META_DRIFT_SOFT", 0)) >= 1
    assert int((summary.get("stop_reason_counts") or {}).get("meta_drift_hard_stop", 0)) >= 1

    stop_events = [evt for evt in (res.get("events") or []) if str(evt.get("type")) == "STOP"]
    assert stop_events
    assert "meta_drift_hard_stop" in [str(x) for x in (stop_events[-1].get("reason_flags") or [])]

