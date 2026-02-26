# ruff: noqa: S101

import time
from pathlib import Path

from freqtrade.user_data.scripts import grid_executor_v1


def _base_plan(
    action: str = "START",
    *,
    execution_hardening: dict | None = None,
    runtime_state: dict | None = None,
) -> dict:
    return {
        "action": str(action),
        "exchange": "binance",
        "symbol": "ETH/USDT",
        "ts": "2026-02-26T00:00:00+00:00",
        "range": {"low": 95.0, "high": 105.0},
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
        "price_ref": {"close": 100.0},
        "runtime_state": runtime_state or {"clock_ts": 1_700_000_000},
        "execution_hardening": execution_hardening or {},
    }


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
