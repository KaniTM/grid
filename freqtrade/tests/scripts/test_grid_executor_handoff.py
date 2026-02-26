import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from core.plan_signature import compute_plan_hash
from freqtrade.user_data.scripts.grid_executor_v1 import GridExecutorV1


def _base_plan(*, seq: int, plan_id: str | None = None) -> dict:
    plan = {
        "schema_version": "1.0.0",
        "planner_version": "gridbrain_v1",
        "pair": "ETH/USDT",
        "symbol": "ETH/USDT",
        "exchange": "binance",
        "plan_id": str(plan_id or uuid4()),
        "decision_seq": int(seq),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "valid_for_candle_ts": 1700000000 + int(seq),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
        "supersedes_plan_id": None,
        "materiality_class": "material",
        "mode": "intraday",
        "mode_score": 0.5,
        "action": "HOLD",
        "action_reason": "test",
        "blockers": [],
        "planner_health_state": "ok",
        "replan_decision": "publish",
        "replan_reasons": ["REPLAN_MATERIAL_BOX_CHANGE"],
        "range": {"low": 100.0, "high": 110.0, "width_pct": 0.095},
        "range_diagnostics": {"lookback_bars_used": 96},
        "box": {"low": 100.0, "high": 110.0, "mid": 105.0, "width_pct": 0.095},
        "grid": {
            "n_levels": 4,
            "step_price": 2.5,
            "fill_detection": {
                "fill_confirmation_mode": "Touch",
                "no_repeat_lsi_guard": True,
                "cooldown_bars": 1,
            },
        },
        "risk": {"tp_price": 112.0, "sl_price": 98.0},
        "signals_snapshot": {},
        "runtime_hints": {},
        "start_stability_score": 1.0,
        "meta_drift_state": {"severity": "none"},
        "cost_model_snapshot": {"source": "static"},
        "module_states": {},
        "capital_policy": {"grid_budget_pct": 1.0},
        "update_policy": {"soft_adjust_max_step_frac": 0.5},
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    plan["plan_hash"] = compute_plan_hash(plan)
    return plan


def _state_payload(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_executor(state_path: Path) -> GridExecutorV1:
    return GridExecutorV1(
        mode="paper",
        state_out=str(state_path),
        poll_seconds=1.0,
        quote_budget=1000.0,
        start_base=0.0,
        maker_fee_pct=0.10,
        post_only=False,
        max_orders_per_side=40,
    )


def test_executor_applies_valid_signed_plan(tmp_path: Path) -> None:
    state_path = tmp_path / "executor.state.json"
    ex = _build_executor(state_path)
    plan = _base_plan(seq=1)

    ex.step(plan)
    payload = _state_payload(state_path)

    assert payload["last_applied_plan_id"] == plan["plan_id"]
    assert payload["last_applied_seq"] == 1
    assert payload["last_plan_hash"] == plan["plan_hash"]
    assert "EXEC_PLAN_APPLIED" in payload["runtime"]["exec_events"]


def test_executor_rejects_duplicate_stale_and_hash_mismatch(tmp_path: Path) -> None:
    state_path = tmp_path / "executor.state.json"
    ex = _build_executor(state_path)
    first = _base_plan(seq=2)
    ex.step(first)

    duplicate_id = _base_plan(seq=3, plan_id=first["plan_id"])
    ex.step(duplicate_id)
    payload = _state_payload(state_path)
    assert payload["last_applied_seq"] == 2
    assert "EXEC_PLAN_DUPLICATE_IGNORED" in payload["runtime"]["exec_events"]

    stale = _base_plan(seq=1)
    ex.step(stale)
    payload = _state_payload(state_path)
    assert payload["last_applied_seq"] == 2
    assert "EXEC_PLAN_STALE_SEQ_IGNORED" in payload["runtime"]["exec_events"]

    bad_hash = _base_plan(seq=4)
    bad_hash["plan_hash"] = "0" * 64
    ex.step(bad_hash)
    payload = _state_payload(state_path)
    assert payload["last_applied_seq"] == 2
    assert "EXEC_PLAN_HASH_MISMATCH" in payload["runtime"]["exec_events"]
