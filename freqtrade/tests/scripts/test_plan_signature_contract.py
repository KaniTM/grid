from datetime import datetime, timedelta, timezone
from uuid import uuid4

from core.plan_signature import compute_plan_hash, plan_is_expired, validate_signature_fields


def _signed_plan() -> dict:
    plan = {
        "schema_version": "1.0.0",
        "planner_version": "gridbrain_v1",
        "pair": "ETH/USDT",
        "exchange": "binance",
        "plan_id": str(uuid4()),
        "decision_seq": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "valid_for_candle_ts": 1700000000,
        "materiality_class": "material",
        "action": "HOLD",
        "mode": "intraday",
        "replan_decision": "publish",
        "replan_reasons": ["REPLAN_MATERIAL_BOX_CHANGE"],
        "box": {"low": 100.0, "high": 110.0, "mid": 105.0, "width_pct": 0.095},
        "grid": {"n_levels": 4, "step_price": 2.5, "fill_detection": {"fill_confirmation_mode": "Touch"}},
        "risk": {"tp_price": 112.0, "sl_price": 98.0},
        "capital_policy": {"grid_budget_pct": 1.0},
        "update_policy": {"soft_adjust_max_step_frac": 0.5},
    }
    plan["plan_hash"] = compute_plan_hash(plan)
    return plan


def test_compute_plan_hash_is_stable_for_non_material_signature_fields() -> None:
    plan = _signed_plan()
    baseline = compute_plan_hash(plan)

    modified = dict(plan)
    modified["plan_id"] = str(uuid4())
    modified["generated_at"] = datetime.now(timezone.utc).isoformat()
    modified["decision_seq"] = 99
    modified["supersedes_plan_id"] = str(uuid4())
    modified["plan_hash"] = "placeholder"

    assert compute_plan_hash(modified) == baseline


def test_validate_signature_fields_accepts_signed_payload() -> None:
    plan = _signed_plan()
    assert validate_signature_fields(plan) == []


def test_validate_signature_fields_reports_missing_fields() -> None:
    errors = validate_signature_fields({})
    assert "missing:schema_version" in errors
    assert "missing:plan_id" in errors
    assert "missing:decision_seq" in errors


def test_plan_is_expired_checks_expires_at() -> None:
    plan = _signed_plan()
    plan["expires_at"] = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    assert plan_is_expired(plan)
