# ruff: noqa: S101

import pandas as pd
import pytest

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


def _base_profile(profile_id: str, *, seed: int = 17) -> dict:
    return {
        "schema_version": "1.0.0",
        "profile_id": str(profile_id),
        "name": str(profile_id).replace("-", "_"),
        "enabled": True,
        "seed": int(seed),
        "latency_ms": {"mean": 0, "jitter": 0, "fill_window_ms": 500},
        "spread_shock_bps": {"base": 0, "burst": 0, "burst_probability": 0.0},
        "partial_fill_probability": 0.0,
        "reject_burst_probability": 0.0,
        "reject_burst_bars": {"min": 1, "max": 1},
        "delayed_candle_probability": 0.0,
        "missing_candle_probability": 0.0,
        "data_gap_probability": 0.0,
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
    profile = _base_profile("stress-deterministic", seed=17)
    profile["latency_ms"] = {"mean": 1000, "jitter": 0, "fill_window_ms": 500}
    profile["spread_shock_bps"] = {"base": 5, "burst": 0, "burst_probability": 0.0}
    profile["reject_burst_probability"] = 1.0

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
    assert s1["deterministic_vs_chaos_delta"] == s2["deterministic_vs_chaos_delta"]
    assert any(abs(float(v)) > 0.0 for v in s1["deterministic_vs_chaos_delta"].values())
    for key in ("start_blocker_counts", "hold_reason_counts", "stop_reason_counts", "stop_reason_counts_combined"):
        assert isinstance(s1.get(key), dict)


def test_chaos_partial_fill_profile_marks_partial_fills() -> None:
    df = _build_replay_df(rows=6)
    profile = _base_profile("partial-only", seed=7)
    profile["partial_fill_probability"] = 1.0
    profile["partial_fill_min_ratio"] = 0.5
    profile["partial_fill_max_ratio"] = 0.5
    res = _simulate(df, profile)
    fills = res["fills"]
    assert fills
    assert any(str(x.get("reason")) == "PARTIAL_FILL" for x in fills)
    assert int(res["summary"]["chaos_counters"]["partial_fill_events"]) > 0


def test_chaos_data_gap_profile_drops_candles() -> None:
    df = _build_replay_df(rows=5)
    profile = _base_profile("gaps-only", seed=5)
    profile["data_gap_probability"] = 1.0
    res = _simulate(df, profile)
    counters = res["summary"]["chaos_counters"]
    assert counters["data_gap_candles"] == len(df)
    assert counters["dropped_candles_total"] == len(df)


@pytest.mark.parametrize(
    "case_name,profile_updates,counter_key,event_type,rail_key",
    [
        (
            "latency",
            {"latency_ms": {"mean": 1000, "jitter": 0, "fill_window_ms": 1}},
            "bars_with_latency_block",
            "CHAOS_LATENCY_BLOCK",
            "pending_fill_candles",
        ),
        (
            "spread",
            {"spread_shock_bps": {"base": 3000, "burst": 0, "burst_probability": 0.0}},
            "bars_with_spread_shock",
            None,
            "fills_total_delta",
        ),
        (
            "reject",
            {"reject_burst_probability": 1.0, "reject_burst_bars": {"min": 1, "max": 1}},
            "bars_with_reject_burst",
            "CHAOS_REJECT_BURST",
            "rejected_fill_attempts",
        ),
        (
            "missing",
            {"missing_candle_probability": 1.0},
            "missing_candles",
            "CHAOS_MISSING_CANDLE",
            "dropped_candles_total",
        ),
        (
            "delayed",
            {"delayed_candle_probability": 1.0},
            "delayed_candles",
            "CHAOS_DELAYED_CANDLE",
            "pending_fill_candles",
        ),
        (
            "data-gap",
            {"data_gap_probability": 1.0},
            "data_gap_candles",
            "CHAOS_DATA_GAP",
            "dropped_candles_total",
        ),
    ],
)
def test_chaos_fault_injection_profiles_trigger_expected_rails(
    case_name: str,
    profile_updates: dict,
    counter_key: str,
    event_type: str | None,
    rail_key: str,
) -> None:
    df = _build_replay_df(rows=8)
    baseline = _simulate(df, None)
    assert len(baseline["fills"]) > 0

    profile = _base_profile(f"{case_name}-only", seed=11)
    profile.update(profile_updates)
    result = _simulate(df, profile)
    summary = result["summary"]
    counters = summary["chaos_counters"]
    assert int(counters[counter_key]) > 0

    delta = summary.get("deterministic_vs_chaos_delta", {}) or {}
    assert isinstance(delta, dict)
    assert "fills_total_delta" in delta
    assert int(delta["fills_total_delta"]) <= 0
    assert any(abs(float(v)) > 0.0 for v in delta.values())

    if rail_key == "fills_total_delta":
        assert int(delta["fills_total_delta"]) < 0
    else:
        assert int(counters[rail_key]) > 0

    if event_type is not None:
        event_types = [str(evt.get("type")) for evt in result.get("events", [])]
        assert event_type in event_types
