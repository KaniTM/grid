from datetime import datetime, timezone
from uuid import uuid4

from core.plan_signature import compute_plan_hash
from core.schema_validation import validate_schema


def _valid_grid_plan() -> dict:
    payload = {
        "schema_version": "1.0.0",
        "planner_version": "gridbrain_v1",
        "pair": "ETH/USDT",
        "exchange": "binance",
        "plan_id": str(uuid4()),
        "decision_seq": 7,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "valid_for_candle_ts": 1700000000,
        "expires_at": None,
        "supersedes_plan_id": None,
        "materiality_class": "material",
        "replan_decision": "publish",
        "replan_reasons": ["REPLAN_MATERIAL_BOX_CHANGE"],
        "action": "HOLD",
        "mode": "intraday",
        "action_reason": "test",
        "blockers": [],
        "planner_health_state": "ok",
        "range_diagnostics": {"lookback_bars_used": 96},
        "box": {"low": 100.0, "high": 110.0, "mid": 105.0, "width_pct": 0.095},
        "grid": {"n_levels": 4, "step_price": 2.5},
        "risk": {"tp_price": 112.0, "sl_price": 98.0},
        "signals_snapshot": {},
        "runtime_hints": {},
        "start_stability_score": 1.0,
        "meta_drift_state": {"severity": "none"},
        "cost_model_snapshot": {"source": "static"},
        "module_states": {},
        "capital_policy": {"grid_budget_pct": 1.0},
        "update_policy": {"soft_adjust_max_step_frac": 0.5}
    }
    payload["plan_hash"] = compute_plan_hash(payload)
    return payload


def test_grid_plan_schema_valid_and_invalid() -> None:
    valid_payload = _valid_grid_plan()
    assert validate_schema(valid_payload, "grid_plan.schema.json") == []

    invalid_payload = dict(valid_payload)
    invalid_payload.pop("plan_id")
    assert validate_schema(invalid_payload, "grid_plan.schema.json")


def test_decision_log_schema_valid_and_invalid() -> None:
    valid_log = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pair": "ETH/USDT",
        "mode_candidate": "intraday",
        "mode_final": "intraday",
        "action": "HOLD",
        "blockers": [],
        "key_features_snapshot": {},
        "box_grid_params": {},
        "start_stability": {"score": 1.0},
        "meta_drift": {"severity": "none"},
        "planner_health": {"state": "ok"},
        "replan_decision": "publish",
        "replan_reasons": ["REPLAN_MATERIAL_BOX_CHANGE"],
        "prev_plan_hash": None,
        "new_plan_hash": "a" * 64,
        "changed_fields": [],
        "event_ids_emitted": []
    }
    assert validate_schema(valid_log, "decision_log.schema.json") == []

    invalid_log = dict(valid_log)
    invalid_log.pop("event_ids_emitted")
    assert validate_schema(invalid_log, "decision_log.schema.json")


def test_event_log_schema_valid_and_invalid() -> None:
    valid_event = {
        "event_id": str(uuid4()),
        "ts": datetime.now(timezone.utc).isoformat(),
        "pair": "ETH/USDT",
        "event_type": "EVENT_POC_TEST",
        "severity": "advisory",
        "source_module": "planner",
        "price": 105.0,
        "side": "buy",
        "metadata": {}
    }
    assert validate_schema(valid_event, "event_log.schema.json") == []

    invalid_event = dict(valid_event)
    invalid_event["severity"] = "critical"
    assert validate_schema(invalid_event, "event_log.schema.json")


def test_execution_cost_and_chaos_schema_valid() -> None:
    calibration = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pair": "ETH/USDT",
        "window": 256,
        "sample_count": 200,
        "cost_model_source": "empirical",
        "percentile": 75,
        "realized_spread_pct": 0.001,
        "adverse_selection_pct": 0.0004,
        "post_only_retry_reject_rate": 0.1,
        "missed_fill_opportunity_rate": 0.05,
        "recommended_cost_floor_bps": 8.5
    }
    assert validate_schema(calibration, "execution_cost_calibration.schema.json") == []

    chaos_profile = {
        "schema_version": "1.0.0",
        "profile_id": "baseline-chaos-v1",
        "name": "baseline",
        "enabled": True,
        "seed": 42,
        "latency_ms": {"mean": 120, "jitter": 40},
        "spread_shock_bps": {"base": 3, "burst": 12},
        "partial_fill_probability": 0.2,
        "reject_burst_probability": 0.1,
        "data_gap_probability": 0.03
    }
    assert validate_schema(chaos_profile, "chaos_profile.schema.json") == []
