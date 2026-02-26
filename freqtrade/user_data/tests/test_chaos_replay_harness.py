# ruff: noqa: S101

import pandas as pd

from freqtrade.user_data.scripts import grid_simulator_v1


def _build_replay_df(rows: int = 10) -> pd.DataFrame:
    dates = pd.date_range("2026-01-01 00:00:00", periods=rows, freq="15min")
    return pd.DataFrame(
        {
            "date": dates,
            "open": [100.0] * rows,
            "high": [102.5] * rows,
            "low": [97.5] * rows,
            "close": [100.0] * rows,
        }
    )


def _plan_at(ts: pd.Timestamp, action: str) -> dict:
    return {
        "_plan_time": pd.Timestamp(ts),
        "ts": pd.Timestamp(ts).isoformat(),
        "action": str(action),
        "symbol": "PAIR/CHAOS",
        "range": {"low": 95.0, "high": 105.0},
        "grid": {"n_levels": 6, "step_price": (105.0 - 95.0) / 6.0},
        "runtime_state": {"clock_ts": int(pd.Timestamp(ts).timestamp())},
        "diagnostics": {},
    }


def _simulate(df: pd.DataFrame, profile: dict | None) -> dict:
    plans = [_plan_at(df["date"].iloc[0], "START")]
    return grid_simulator_v1.simulate_grid_replay(
        df=df,
        plans=plans,
        start_quote=1000.0,
        start_base=0.0,
        maker_fee_pct=0.10,
        touch_fill=True,
        chaos_profile=profile,
    )


def test_chaos_profile_is_deterministic_and_reports_delta() -> None:
    df = _build_replay_df(rows=8)
    profile = {
        "schema_version": "1.0.0",
        "profile_id": "stress-deterministic",
        "name": "stress_deterministic",
        "enabled": True,
        "seed": 17,
        "latency_ms": {"mean": 1000, "jitter": 0, "fill_window_ms": 500},
        "spread_shock_bps": {"base": 5, "burst": 0, "burst_probability": 0.0},
        "partial_fill_probability": 0.0,
        "reject_burst_probability": 1.0,
        "reject_burst_bars": {"min": 1, "max": 1},
        "delayed_candle_probability": 0.0,
        "missing_candle_probability": 0.0,
        "data_gap_probability": 0.0,
    }

    first = _simulate(df, profile)
    second = _simulate(df, profile)

    s1 = first["summary"]
    s2 = second["summary"]
    assert s1["chaos_profile_enabled"] is True
    assert s1["chaos_profile_id"] == "stress-deterministic"
    assert s1["chaos_seed"] == 17
    assert s1["chaos_counters"] == s2["chaos_counters"]
    assert s1["chaos_counters"]["bars_with_latency_block"] == len(df)
    assert s1["chaos_counters"]["bars_with_reject_burst"] == len(df)
    assert "deterministic_vs_chaos_delta" in s1


def test_chaos_partial_fill_profile_marks_partial_fills() -> None:
    df = _build_replay_df(rows=6)
    profile = {
        "schema_version": "1.0.0",
        "profile_id": "partial-only",
        "name": "partial_only",
        "enabled": True,
        "seed": 7,
        "latency_ms": {"mean": 0, "jitter": 0},
        "spread_shock_bps": {"base": 0, "burst": 0},
        "partial_fill_probability": 1.0,
        "partial_fill_min_ratio": 0.5,
        "partial_fill_max_ratio": 0.5,
        "reject_burst_probability": 0.0,
        "data_gap_probability": 0.0,
    }
    res = _simulate(df, profile)
    fills = res["fills"]
    assert fills
    assert any(str(x.get("reason")) == "PARTIAL_FILL" for x in fills)
    assert int(res["summary"]["chaos_counters"]["partial_fill_events"]) > 0


def test_chaos_data_gap_profile_drops_candles() -> None:
    df = _build_replay_df(rows=5)
    profile = {
        "schema_version": "1.0.0",
        "profile_id": "gaps-only",
        "name": "gaps_only",
        "enabled": True,
        "seed": 5,
        "latency_ms": {"mean": 0, "jitter": 0},
        "spread_shock_bps": {"base": 0, "burst": 0},
        "partial_fill_probability": 0.0,
        "reject_burst_probability": 0.0,
        "data_gap_probability": 1.0,
    }
    res = _simulate(df, profile)
    counters = res["summary"]["chaos_counters"]
    assert counters["data_gap_candles"] == len(df)
    assert counters["dropped_candles_total"] == len(df)
