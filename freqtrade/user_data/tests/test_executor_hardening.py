# ruff: noqa: S101

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from core.plan_signature import compute_plan_hash
from core.schema_validation import validate_schema
from freqtrade.user_data.scripts import grid_executor_v1


def _base_plan(
    action: str = "START",
    *,
    execution_hardening: dict | None = None,
    runtime_state: dict | None = None,
) -> dict:
    plan = {
        "schema_version": "1.0.0",
        "planner_version": "gridbrain_v1",
        "pair": "ETH/USDT",
        "action": str(action),
        "mode": "intraday",
        "action_reason": "test",
        "blockers": [],
        "planner_health_state": "ok",
        "materiality_class": "soft",
        "replan_decision": "publish",
        "replan_reasons": ["REPLAN_MATERIAL_BOX_CHANGE"],
        "plan_id": str(uuid4()),
        "decision_seq": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "valid_for_candle_ts": 1_700_000_000,
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
        "supersedes_plan_id": None,
        "exchange": "binance",
        "symbol": "ETH/USDT",
        "ts": "2026-02-26T00:00:00+00:00",
        "range": {"low": 95.0, "high": 105.0},
        "range_diagnostics": {"lookback_bars_used": 96},
        "box": {"low": 95.0, "high": 105.0, "mid": 100.0, "width_pct": 0.10},
        "grid": {
            "n_levels": 4,
            "step_price": 2.5,
            "post_only": True,
            "fill_detection": {
                "fill_confirmation_mode": "Touch",
                "no_repeat_lsi_guard": True,
                "cooldown_bars": 1,
            },
        },
        "risk": {"tp_price": 108.0, "sl_price": 92.0},
        "signals_snapshot": {},
        "runtime_hints": {},
        "start_stability_score": 1.0,
        "meta_drift_state": {"severity": "none"},
        "cost_model_snapshot": {"source": "static"},
        "module_states": {},
        "capital_policy": {"grid_budget_pct": 1.0},
        "update_policy": {"soft_adjust_max_step_frac": 0.5},
        "price_ref": {"close": 100.0},
        "runtime_state": runtime_state or {"clock_ts": 1_700_000_000},
        "execution_hardening": execution_hardening or {},
    }
    plan["plan_hash"] = compute_plan_hash(plan)
    return plan


class _RetryThenAcceptExchange:
    def __init__(self) -> None:
        self.buy_prices: list[float] = []
        self._attempts = 0

    def price_to_precision(self, _symbol: str, price: float) -> float:
        return float(price)

    def amount_to_precision(self, _symbol: str, qty: float) -> float:
        return float(qty)

    def create_limit_buy_order(self, _symbol: str, _qty: float, price: float, params=None):
        self._attempts += 1
        self.buy_prices.append(float(price))
        if self._attempts < 3:
            raise Exception("post only reject: order would be taker")
        return {"id": f"buy-{self._attempts}", "params": params or {}}


class _ReconcileExchange:
    def __init__(self, open_orders: list[dict]) -> None:
        self._open_orders = list(open_orders)

    def fetch_open_orders(self, _symbol: str) -> list[dict]:
        return list(self._open_orders)


def _executor(tmp_path: Path) -> grid_executor_v1.GridExecutorV1:
    return grid_executor_v1.GridExecutorV1(
        mode="paper",
        state_out=str(tmp_path / "executor_state.json"),
        poll_seconds=1.0,
        quote_budget=1000.0,
        start_base=0.0,
        maker_fee_pct=0.1,
        post_only=True,
        max_orders_per_side=20,
    )


def test_ccxt_place_limit_retries_post_only_with_backoff_and_reprice(tmp_path: Path) -> None:
    ex = _executor(tmp_path)
    fake = _RetryThenAcceptExchange()
    ex.exchange = fake
    ex._tick_size = 0.5
    ex._post_only_place_attempts = 4
    ex._post_only_backoff_ms = 0
    ex._post_only_backoff_max_ms = 0
    ex._post_only_reprice_ticks = 1

    oid = ex._ccxt_place_limit("buy", "ETH/USDT", 1.0, 100.0, limits={})

    assert oid == "buy-3"
    assert fake.buy_prices == [100.0, 99.5, 98.5]
    assert ex._post_only_retry_count_total >= 2
    assert ex._post_only_reprice_count_total >= 2
    assert "EXEC_POST_ONLY_RETRY" in ex._runtime_exec_events
    assert "EXEC_POST_ONLY_FALLBACK_REPRICE" in ex._runtime_exec_events


def test_reject_burst_blocks_start_and_downgrades_to_hold(tmp_path: Path) -> None:
    ex = _executor(tmp_path)
    now = time.time()
    ex._post_only_reject_window_s = 120
    ex._post_only_reject_warn_count = 1
    ex._post_only_reject_hard_count = 2
    ex._post_only_reject_times.append(now - 1)
    ex._post_only_reject_times.append(now - 2)

    plan = _base_plan("START")
    ex.step(plan)

    state = grid_executor_v1.load_json(ex.state_out)
    runtime = state["runtime"]
    assert runtime["raw_action"] == "START"
    assert runtime["effective_action"] == "HOLD"
    assert runtime["action_suppression_reason"] == "confirm_start_failed"
    assert "PAUSE_EXECUTION_UNSAFE" in runtime["pause_reasons"]
    assert "EXEC_CONFIRM_START_FAILED" in runtime["exec_events"]
    assert state["orders"] == []


def test_stop_exit_confirm_uses_failsafe_reason(tmp_path: Path) -> None:
    ex = _executor(tmp_path)
    ex._last_mark_price = 100.0
    plan = _base_plan(
        "STOP",
        execution_hardening={
            "confirm_hooks": {
                "confirm_exit_enabled": True,
                "jump_max": 0.001,
            }
        },
        runtime_state={"clock_ts": 1_700_000_000, "jump_pct": 0.02},
    )

    ex.step(plan)

    state = grid_executor_v1.load_json(ex.state_out)
    runtime = state["runtime"]
    assert runtime["effective_action"] == "STOP"
    assert runtime["stop_reason"] == "STOP_EXEC_CONFIRM_EXIT_FAILSAFE"
    assert "EXEC_CONFIRM_EXIT_FAILSAFE" in runtime["exec_events"]


def test_rebuild_confirm_failure_is_tracked_separately(tmp_path: Path) -> None:
    ex = _executor(tmp_path)
    ex._prev_plan = _base_plan("START")
    ex._orders = [grid_executor_v1.RestingOrder("buy", 99.0, 1.0, 1, status="open")]
    now = time.time()
    ex._post_only_reject_window_s = 120
    ex._post_only_reject_warn_count = 1
    ex._post_only_reject_hard_count = 2
    ex._post_only_reject_times.append(now - 1)
    ex._post_only_reject_times.append(now - 2)

    rebuild_plan = _base_plan("START")
    rebuild_plan["range"]["high"] = 110.0
    rebuild_plan["grid"]["step_price"] = (110.0 - 95.0) / 4.0
    rebuild_plan["plan_hash"] = compute_plan_hash(rebuild_plan)
    ex.step(rebuild_plan)

    state = grid_executor_v1.load_json(ex.state_out)
    runtime = state["runtime"]
    assert runtime["raw_action"] == "START"
    assert runtime["effective_action"] == "HOLD"
    assert runtime["action_suppression_reason"] == "confirm_rebuild_failed"
    assert "EXEC_CONFIRM_REBUILD_FAILED" in runtime["exec_events"]


def test_reconcile_matches_live_orders_with_tolerance(tmp_path: Path) -> None:
    ex = _executor(tmp_path)
    ex.exchange = _ReconcileExchange(
        [
            {
                "id": "live-1",
                "side": "buy",
                "price": 100.0001,
                "amount": 1.01,
            }
        ]
    )
    ex._tick_size = 0.1
    ex._reconcile_price_tol_ticks = 2
    ex._reconcile_qty_tol_frac = 0.02

    canceled: list[str] = []
    placed: list[tuple[str, float, float]] = []
    ex._ccxt_cancel_order = lambda oid, _symbol: canceled.append(str(oid))  # type: ignore[method-assign]
    ex._ccxt_place_limit = lambda side, _symbol, qty, price, _limits: placed.append((side, qty, price)) or "new"  # type: ignore[method-assign]

    desired = [grid_executor_v1.RestingOrder("buy", 100.0, 1.0, 2)]
    ex._ccxt_reconcile_set(desired, "ETH/USDT", limits={})

    assert canceled == []
    assert placed == []
    assert len(ex._orders) == 1
    assert ex._orders[0].order_id == "live-1"
    assert ex._orders[0].status == "open"
    assert ex._last_reconcile_summary["kept_orders"] == 1


def test_reconcile_honors_action_cap(tmp_path: Path) -> None:
    ex = _executor(tmp_path)
    ex.exchange = _ReconcileExchange(
        [
            {"id": "live-1", "side": "buy", "price": 99.0, "amount": 1.0},
            {"id": "live-2", "side": "buy", "price": 98.0, "amount": 1.0},
            {"id": "live-3", "side": "sell", "price": 102.0, "amount": 1.0},
        ]
    )
    ex._reconcile_max_actions_per_tick = 2

    canceled: list[str] = []
    ex._ccxt_cancel_order = lambda oid, _symbol: canceled.append(str(oid))  # type: ignore[method-assign]
    ex._ccxt_place_limit = lambda _side, _symbol, _qty, _price, _limits: "new"  # type: ignore[method-assign]

    desired = [
        grid_executor_v1.RestingOrder("buy", 100.0, 1.0, 0),
        grid_executor_v1.RestingOrder("sell", 101.0, 1.0, 1),
        grid_executor_v1.RestingOrder("sell", 103.0, 1.0, 2),
    ]
    ex._ccxt_reconcile_set(desired, "ETH/USDT", limits={})

    assert len(canceled) <= 2
    assert ex._last_reconcile_skipped_due_cap is True
    assert any(o.status == "rejected" for o in ex._orders)


def test_executor_recovers_state_file_on_startup(tmp_path: Path) -> None:
    state_path = tmp_path / "recover_state.json"
    grid_executor_v1.write_json(
        str(state_path),
        {
            "quote_total": 1234.0,
            "base_total": 0.75,
            "runtime": {
                "last_trade_ms": 1700000000000,
                "fill_guard_bar_seq": 7,
                "fill_guard_last_clock_ts": 1700000000,
            },
            "orders": [
                {
                    "side": "buy",
                    "price": 100.0,
                    "qty_base": 1.0,
                    "level_index": 3,
                    "order_id": "restored-1",
                    "status": "open",
                    "filled_base": 0.0,
                }
            ],
        },
    )

    ex = grid_executor_v1.GridExecutorV1(
        mode="paper",
        state_out=str(state_path),
        poll_seconds=1.0,
        quote_budget=1000.0,
        start_base=0.0,
        maker_fee_pct=0.1,
        post_only=True,
        max_orders_per_side=20,
    )

    assert ex._recovery_loaded is True
    assert ex.quote_total == 1234.0
    assert ex.base_total == 0.75
    assert ex._fill_guard_bar_seq == 7
    assert ex._fill_guard_last_clock_ts == 1700000000
    assert len(ex._orders) == 1
    assert ex._orders[0].order_id == "restored-1"


def test_capacity_rung_cap_limits_seeded_orders_in_paper(tmp_path: Path) -> None:
    ex = _executor(tmp_path)
    plan = _base_plan(
        "START",
        runtime_state={
            "clock_ts": 1_700_000_000,
            "spread_pct": 0.01,
            "depth_thinning_score": 0.9,
        },
        execution_hardening={
            "capacity_cap": {
                "enabled": True,
                "spread_wide_threshold": 0.001,
                "depth_thin_threshold": 0.5,
                "spread_cap_multiplier": 0.5,
                "depth_cap_multiplier": 0.5,
                "min_rung_cap": 1,
            }
        },
    )
    plan["capital_policy"] = {"grid_budget_pct": 1.0, "preferred_rung_cap": 3}
    plan["plan_hash"] = compute_plan_hash(plan)

    ex.step(plan)

    state = grid_executor_v1.load_json(ex.state_out)
    runtime = state["runtime"]
    assert runtime["capacity_guard"]["capacity_ok"] is True
    assert runtime["capacity_guard"]["applied_rung_cap"] == 1
    assert "EXEC_CAPACITY_RUNG_CAP_APPLIED" in runtime["exec_events"]
    assert len(state["orders"]) == 1


def test_capacity_hard_block_prevents_start(tmp_path: Path) -> None:
    ex = _executor(tmp_path)
    plan = _base_plan(
        "START",
        runtime_state={"clock_ts": 1_700_000_000},
        execution_hardening={"capacity_cap": {"enabled": True}},
    )
    plan["runtime_hints"] = {
        "capacity_hint": {
            "allow_start": False,
            "advisory_only": False,
            "reason": "thin_book",
        }
    }
    plan["plan_hash"] = compute_plan_hash(plan)

    ex.step(plan)
    state = grid_executor_v1.load_json(ex.state_out)
    runtime = state["runtime"]
    assert runtime["raw_action"] == "START"
    assert runtime["effective_action"] == "HOLD"
    assert runtime["action_suppression_reason"] == "capacity_thin_block"
    assert "BLOCK_CAPACITY_THIN" in runtime["warnings"]
    assert state["orders"] == []


def test_execution_cost_feedback_writes_artifact_and_lifecycle_logs(tmp_path: Path) -> None:
    ex = _executor(tmp_path)
    plan = _base_plan(
        "START",
        runtime_state={"clock_ts": 1_700_000_000, "spread_pct": 0.002},
        execution_hardening={
            "execution_cost_feedback": {
                "enabled": True,
                "window": 16,
                "percentile": 90.0,
                "min_samples": 1,
                "stale_steps": 32,
            }
        },
    )
    plan["capital_policy"] = {"grid_budget_pct": 1.0}
    plan["plan_hash"] = compute_plan_hash(plan)

    ex.step(plan)
    state = grid_executor_v1.load_json(ex.state_out)
    runtime = state["runtime"]
    artifact = runtime["execution_cost_artifact"]
    paths = runtime["execution_cost_artifact_paths"]

    assert runtime["execution_cost_feedback_enabled"] is True
    assert runtime["execution_cost_step_metrics"]["orders_placed"] > 0
    assert artifact["pair"] == "ETH/USDT"
    assert artifact["sample_count"] >= 1
    assert Path(paths["artifact_latest"]).is_file()
    assert Path(paths["orders_lifecycle"]).is_file()
    assert Path(paths["fills_lifecycle"]).exists()

    artifact_payload = json.loads(Path(paths["artifact_latest"]).read_text(encoding="utf-8"))
    assert validate_schema(artifact_payload, "execution_cost_calibration.schema.json") == []


def test_levels_validation_flags_duplicate_prices_after_tick_rounding() -> None:
    levels = grid_executor_v1.build_levels(100.0, 100.2, n_levels=4, tick_size=1.0)
    err = grid_executor_v1._levels_validation_error(levels, expected_count=5)
    assert err == "levels_non_increasing_or_duplicate"


def test_plan_intake_rejects_invalid_level_geometry(tmp_path: Path) -> None:
    ex = _executor(tmp_path)
    plan = _base_plan("START")
    plan["range"] = {"low": 100.0, "high": 100.2}
    plan["grid"]["n_levels"] = 4
    plan["grid"]["step_price"] = 0.05
    plan["grid"]["tick_size"] = 1.0
    plan["plan_hash"] = compute_plan_hash(plan)

    ex.step(plan)

    state = grid_executor_v1.load_json(ex.state_out)
    runtime = state["runtime"]
    assert runtime["raw_action"] == "HOLD"
    assert runtime["effective_action"] == "HOLD"
    assert runtime["action_suppression_reason"] == "plan_rejected:EXEC_PLAN_SCHEMA_INVALID"
    assert "EXEC_PLAN_SCHEMA_INVALID" in runtime["exec_events"]
    assert "BLOCK_N_LEVELS_INVALID" in runtime["warnings"]
    assert state["orders"] == []


def test_polling_loop_aborts_after_max_consecutive_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class _AlwaysFailExecutor:
        def step(self, _plan: dict) -> None:
            raise RuntimeError("boom")

    monkeypatch.setattr(grid_executor_v1, "load_json", lambda _path: {"action": "HOLD"})
    monkeypatch.setattr(grid_executor_v1.time, "sleep", lambda _seconds: None)

    state_out = tmp_path / "loop_error_state.json"
    with pytest.raises(RuntimeError, match="max_consecutive_errors_reached:2"):
        grid_executor_v1._run_polling_loop(
            ex=_AlwaysFailExecutor(),
            plan_path=str(tmp_path / "plan.json"),
            state_out=str(state_out),
            poll_seconds=0.0,
            max_consecutive_errors=2,
            error_backoff_seconds=0.0,
        )

    payload = json.loads(state_out.read_text(encoding="utf-8"))
    assert payload["consecutive_errors"] == 2
