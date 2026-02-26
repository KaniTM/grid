# ruff: noqa: S101

import pandas as pd

from freqtrade.user_data.scripts import grid_simulator_v1


def _build_df(rows: int) -> pd.DataFrame:
    dates = pd.date_range("2026-03-01 00:00:00", periods=rows, freq="15min")
    return pd.DataFrame(
        {
            "date": dates,
            "open": [100.0] * rows,
            "high": [100.1] * rows,
            "low": [99.9] * rows,
            "close": [100.0] * rows,
        }
    )


def _plan(
    ts: pd.Timestamp,
    action: str,
    *,
    low: float = 90.0,
    high: float = 110.0,
    n_levels: int = 10,
    replan_decision: str = "publish",
    materiality_class: str = "soft",
    ref_price: float = 99.0,
    start_block_reasons: list[str] | None = None,
    stop_reason_flags: list[str] | None = None,
) -> dict:
    reasons = [str(x) for x in (start_block_reasons or [])]
    stop_flags = [str(x) for x in (stop_reason_flags or [])]
    return {
        "_plan_time": pd.Timestamp(ts),
        "ts": pd.Timestamp(ts).isoformat(),
        "action": str(action).upper(),
        "replan_decision": str(replan_decision),
        "materiality_class": str(materiality_class),
        "range": {"low": float(low), "high": float(high)},
        "grid": {
            "n_levels": int(n_levels),
            "step_price": float((float(high) - float(low)) / int(n_levels)),
            "rung_density_bias": {
                "weights_by_level_index": [1.0] * (int(n_levels) + 1),
            },
        },
        "price_ref": {"close": float(ref_price)},
        "runtime_state": {
            "clock_ts": int(pd.Timestamp(ts).timestamp()),
            "start_block_reasons": reasons,
            "stop_reason_flags_applied_active": stop_flags,
        },
        "diagnostics": {
            "start_block_reasons": reasons,
            "stop_reason_flags_applied_active": stop_flags,
        },
    }


def test_replay_golden_summary_contract_is_strict() -> None:
    df = _build_df(rows=7)
    plans = [
        _plan(df["date"].iloc[0], "START", replan_decision="publish", materiality_class="material"),
        _plan(df["date"].iloc[1], "HOLD", replan_decision="defer", materiality_class="soft"),
        _plan(
            df["date"].iloc[2],
            "HOLD",
            replan_decision="defer",
            materiality_class="soft",
            start_block_reasons=["BLOCK_META_DRIFT_SOFT"],
        ),
        _plan(
            df["date"].iloc[3],
            "STOP",
            replan_decision="publish",
            materiality_class="hard",
            stop_reason_flags=["meta_drift_hard_stop"],
        ),
        _plan(df["date"].iloc[4], "START", replan_decision="publish", materiality_class="material"),
        _plan(
            df["date"].iloc[5],
            "HOLD",
            replan_decision="defer",
            materiality_class="soft",
            start_block_reasons=["cooldown_active"],
        ),
        _plan(
            df["date"].iloc[6],
            "STOP",
            replan_decision="publish",
            materiality_class="hard",
            stop_reason_flags=["stop_rule_triggered"],
        ),
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

    assert summary["actions"] == {"START": 2, "HOLD": 3, "STOP": 2, "NO_PLAN": 0}
    assert summary["raw_actions"] == {"START": 2, "HOLD": 3, "STOP": 2, "NO_PLAN": 0}
    assert summary["stop_events"] == 2
    assert summary["seed_events"] == 2
    assert summary["false_start_count"] == 2
    assert summary["false_start_rate"] == 1.0
    assert summary["start_blocker_counts"] == {"BLOCK_META_DRIFT_SOFT": 1, "cooldown_active": 1}
    assert summary["hold_reason_counts"]["BLOCK_META_DRIFT_SOFT"] == 1
    assert summary["hold_reason_counts"]["cooldown_active"] == 1
    assert summary["stop_reason_counts"] == {"meta_drift_hard_stop": 1, "stop_rule_triggered": 1}
    assert summary["replan_decision_counts"] == {"publish": 4, "defer": 3}
    assert summary["materiality_class_counts"] == {"soft": 3, "hard": 2, "material": 2}
    assert len(summary["selected_plan_snapshots"]) == len(plans)
    assert summary["selected_plan_snapshots"][0]["action"] == "START"
    assert summary["selected_plan_snapshots"][-1]["action"] == "STOP"


def test_replay_brain_simulator_consistency_trace_matches_plans() -> None:
    df = _build_df(rows=6)
    plans = [
        _plan(
            df["date"].iloc[0],
            "START",
            low=90.0,
            high=110.0,
            n_levels=10,
            replan_decision="publish",
            materiality_class="soft",
        ),
        _plan(
            df["date"].iloc[2],
            "HOLD",
            low=92.0,
            high=108.0,
            n_levels=8,
            replan_decision="defer",
            materiality_class="noop",
        ),
        _plan(
            df["date"].iloc[4],
            "STOP",
            low=95.0,
            high=105.0,
            n_levels=5,
            replan_decision="publish",
            materiality_class="hard",
            stop_reason_flags=["STOP_RULE_TRIGGERED"],
        ),
    ]

    res = grid_simulator_v1.simulate_grid_replay(
        df=df,
        plans=plans,
        start_quote=1000.0,
        start_base=0.0,
        maker_fee_pct=0.10,
        touch_fill=True,
    )

    curve = res["curve"]
    expected_plan_indices = [0, 0, 1, 1, 2, 2]
    assert [int(x["plan_index"]) for x in curve] == expected_plan_indices

    for row in curve:
        plan = plans[int(row["plan_index"])]
        expected_step = (float(plan["range"]["high"]) - float(plan["range"]["low"])) / float(
            int(plan["grid"]["n_levels"])
        )
        assert row["plan_action"] == str(plan["action"]).upper()
        assert row["plan_replan_decision"] == str(plan["replan_decision"]).lower()
        assert row["plan_materiality_class"] == str(plan["materiality_class"]).lower()
        assert float(row["plan_box_low"]) == float(plan["range"]["low"])
        assert float(row["plan_box_high"]) == float(plan["range"]["high"])
        assert int(row["plan_n_levels"]) == int(plan["grid"]["n_levels"])
        assert float(row["plan_step_price"]) == expected_step

    summary = res["summary"]
    assert summary["replan_decision_counts"] == {"publish": 2, "defer": 1}
    assert summary["materiality_class_counts"] == {"hard": 1, "noop": 1, "soft": 1}
    assert len(summary["selected_plan_snapshots"]) == 3
