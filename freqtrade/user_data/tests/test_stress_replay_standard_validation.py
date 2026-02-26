# ruff: noqa: S101

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import user_regression_suite as urs  # noqa: E402


def _replay_df(rows: int = 8) -> pd.DataFrame:
    dates = pd.date_range("2026-01-01 00:00:00", periods=rows, freq="15min")
    return pd.DataFrame(
        {
            "date": dates,
            "open": [100.0] * rows,
            "high": [102.0] * rows,
            "low": [98.0] * rows,
            "close": [100.0] * rows,
            "volume": [1.0] * rows,
        }
    )


def _plan(ts: pd.Timestamp, action: str) -> dict:
    return {
        "_plan_time": pd.Timestamp(ts),
        "ts": pd.Timestamp(ts).isoformat(),
        "action": str(action),
        "symbol": "ETH/USDT",
        "range": {"low": 95.0, "high": 105.0},
        "grid": {"n_levels": 6, "step_price": (105.0 - 95.0) / 6.0},
        "runtime_state": {"clock_ts": int(pd.Timestamp(ts).timestamp())},
        "diagnostics": {},
    }


def test_stress_replay_standard_validation_summary_contract() -> None:
    df = _replay_df(rows=8)
    plans = [
        _plan(df["date"].iloc[0], "START"),
        _plan(df["date"].iloc[3], "HOLD"),
        _plan(df["date"].iloc[6], "STOP"),
    ]
    summary = urs.run_stress_replay_validation(
        df=df,
        plans=plans,
        quote_budget=1000.0,
        maker_fee_pct=0.10,
    )
    assert summary["chaos_profile_enabled"] is True
    assert isinstance(summary.get("chaos_counters", {}), dict)
    assert "bars_with_spread_shock" in summary["chaos_counters"]
    assert isinstance(summary.get("deterministic_vs_chaos_delta", {}), dict)
    assert "fills_total_delta" in summary["deterministic_vs_chaos_delta"]
