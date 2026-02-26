import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from core.plan_signature import compute_plan_hash
from freqtrade.user_data.scripts.grid_executor_v1 import GridExecutorV1


def _base_plan(
    *,
    seq: int,
    plan_id: str | None = None,
    pair: str = "ETH/USDT",
    supersedes_plan_id: str | None = None,
    valid_for_candle_ts: int | None = None,
) -> dict:
    plan = {
        "schema_version": "1.0.0",
        "planner_version": "gridbrain_v1",
        "pair": pair,
        "symbol": pair,
        "exchange": "binance",
        "plan_id": str(plan_id or uuid4()),
        "decision_seq": int(seq),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "valid_for_candle_ts": int(valid_for_candle_ts or (1700000000 + int(seq))),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
        "supersedes_plan_id": supersedes_plan_id,
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


def test_executor_rejects_duplicate_hash_seen_across_non_adjacent_plans(tmp_path: Path) -> None:
    state_path = tmp_path / "executor.state.json"
    ex = _build_executor(state_path)

    first = _base_plan(seq=1)
    ex.step(first)
    payload = _state_payload(state_path)
    assert payload["last_applied_seq"] == 1

    second = _base_plan(seq=2, supersedes_plan_id=first["plan_id"])
    second["box"]["high"] = 111.0
    second["box"]["mid"] = 105.5
    second["risk"]["tp_price"] = 113.0
    second["plan_hash"] = compute_plan_hash(second)
    ex.step(second)
    payload = _state_payload(state_path)
    assert payload["last_applied_seq"] == 2

    duplicate_hash = _base_plan(
        seq=3,
        supersedes_plan_id=second["plan_id"],
        valid_for_candle_ts=int(first["valid_for_candle_ts"]),
    )
    duplicate_hash["box"] = dict(first["box"])
    duplicate_hash["risk"] = dict(first["risk"])
    duplicate_hash["grid"] = dict(first["grid"])
    duplicate_hash["plan_hash"] = first["plan_hash"]
    ex.step(duplicate_hash)
    payload = _state_payload(state_path)
    assert payload["last_applied_seq"] == 2
    assert "EXEC_PLAN_DUPLICATE_IGNORED" in payload["runtime"]["exec_events"]


def test_executor_rejects_supersedes_pair_and_valid_for_regressions(tmp_path: Path) -> None:
    state_path = tmp_path / "executor.state.json"
    ex = _build_executor(state_path)
    first = _base_plan(seq=5)
    ex.step(first)

    bad_supersedes = _base_plan(
        seq=6,
        supersedes_plan_id="00000000-0000-0000-0000-000000000999",
    )
    ex.step(bad_supersedes)
    payload = _state_payload(state_path)
    assert payload["last_applied_seq"] == 5
    assert "EXEC_PLAN_STALE_SEQ_IGNORED" in payload["runtime"]["exec_events"]

    stale_candle = _base_plan(
        seq=6,
        supersedes_plan_id=first["plan_id"],
        valid_for_candle_ts=int(first["valid_for_candle_ts"]),
    )
    stale_candle["box"]["high"] = 111.0
    stale_candle["box"]["mid"] = 105.5
    stale_candle["risk"]["tp_price"] = 113.0
    stale_candle["plan_hash"] = compute_plan_hash(stale_candle)
    ex.step(stale_candle)
    payload = _state_payload(state_path)
    assert payload["last_applied_seq"] == 5
    assert "EXEC_PLAN_STALE_SEQ_IGNORED" in payload["runtime"]["exec_events"]

    pair_mismatch = _base_plan(
        seq=6,
        pair="BTC/USDT",
        supersedes_plan_id=first["plan_id"],
        valid_for_candle_ts=int(first["valid_for_candle_ts"]) + 1,
    )
    ex.step(pair_mismatch)
    payload = _state_payload(state_path)
    assert payload["last_applied_seq"] == 5
    assert "EXEC_PLAN_SCHEMA_INVALID" in payload["runtime"]["exec_events"]


def test_executor_rejects_schema_invalid_plan(tmp_path: Path) -> None:
    state_path = tmp_path / "executor.state.json"
    ex = _build_executor(state_path)
    invalid = _base_plan(seq=1)
    invalid.pop("box")

    ex.step(invalid)
    payload = _state_payload(state_path)
    assert payload["last_applied_seq"] == 0
    assert "EXEC_PLAN_SCHEMA_INVALID" in payload["runtime"]["exec_events"]
