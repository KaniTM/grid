import argparse
import json
import os
import time
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Deque, Dict, List, Optional, Set, Tuple

import numpy as np
from core.atomic_json import write_json_atomic
from core.plan_signature import compute_plan_hash, plan_is_expired, plan_pair, validate_signature_fields
from core.schema_validation import validate_schema
from analytics.execution_cost_calibrator import EmpiricalCostCalibrator
from execution.capacity_guard import compute_dynamic_capacity_state

try:
    import ccxt  # optional, only needed for --mode ccxt
except Exception:
    ccxt = None

SOURCE_PATH = Path(__file__).resolve()
MODULE_NAME = "grid_executor_v1"


def log_event(level: str, message: str, plan: Optional[Dict] = None, **meta: object) -> None:
    payload: Dict[str, object] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": str(level).upper(),
        "module": MODULE_NAME,
        "source_path": str(SOURCE_PATH),
        "message": message,
    }
    if plan is not None:
        payload["plan_context"] = _plan_context(plan)
    payload.update(meta)
    print(json.dumps(payload, sort_keys=True))


def _log_plan_marker(
    label: str, plan: Optional[Dict], level: str = "debug", **meta: object
) -> None:
    log_event(level, label, plan=plan, **meta)


# -----------------------------
# Plan helpers
# -----------------------------
def _plan_context(plan: Optional[Dict]) -> Dict[str, object]:
    if not plan:
        return {}
    out: Dict[str, object] = {}
    path = plan.get("_plan_path") or plan.get("plan_path") or plan.get("path")
    if path:
        out["plan_path"] = str(path)
    pair = plan_pair(plan)
    if pair:
        out["pair"] = pair
    if plan.get("ts"):
        out["plan_ts"] = str(plan.get("ts"))
    if plan.get("plan_id"):
        out["plan_id"] = str(plan.get("plan_id"))
    if plan.get("decision_seq") is not None:
        try:
            out["decision_seq"] = int(plan.get("decision_seq"))
        except Exception:
            out["decision_seq"] = str(plan.get("decision_seq"))
    if plan.get("plan_hash"):
        out["plan_hash"] = str(plan.get("plan_hash"))
    try:
        out["plan_keys"] = sorted(plan.keys())
    except Exception:
        pass
    return out


# -----------------------------
# Data models
# -----------------------------
@dataclass
class RestingOrder:
    side: str               # "buy" or "sell"
    price: float
    qty_base: float
    level_index: int
    order_id: Optional[str] = None
    status: str = "open"    # open/canceled/filled/partial/rejected

    # internal bookkeeping
    filled_base: float = 0.0


@dataclass
class ExecutorState:
    schema_version: str
    ts: float
    exchange: str
    pair: str
    symbol: str
    plan_ts: str
    mode: str
    last_applied_plan_id: Optional[str]
    last_applied_seq: int
    last_applied_valid_for_candle_ts: int
    last_plan_hash: Optional[str]
    executor_state_machine: str

    step: float
    n_levels: int
    box_low: float
    box_high: float

    quote_total: float
    base_total: float

    quote_free: float
    base_free: float
    quote_reserved: float
    base_reserved: float

    runtime: Dict
    orders: List[Dict]
    applied_plan_ids: List[str]
    applied_plan_hashes: List[str]


# -----------------------------
# Helpers
# -----------------------------
def load_json(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, payload: Dict) -> None:
    write_json_atomic(path, payload)


def _round_to_tick(price: float, tick_size: Optional[float]) -> float:
    if tick_size is None or tick_size <= 0:
        return float(price)
    return float(np.round(float(price) / float(tick_size)) * float(tick_size))


def build_levels(
    box_low: float,
    box_high: float,
    n_levels: int,
    tick_size: Optional[float] = None,
) -> np.ndarray:
    if n_levels <= 0:
        return np.array([])
    levels = np.linspace(box_low, box_high, n_levels + 1)
    if tick_size is not None and tick_size > 0:
        levels = np.array([_round_to_tick(float(px), tick_size) for px in levels], dtype=float)
        levels = np.sort(levels)
        if len(levels) != (n_levels + 1):
            levels = np.linspace(float(levels[0]), float(levels[-1]), n_levels + 1)
            levels = np.array([_round_to_tick(float(px), tick_size) for px in levels], dtype=float)
    return levels


def _levels_validation_error(levels: np.ndarray, expected_count: int, eps: float = 1e-12) -> Optional[str]:
    if not isinstance(levels, np.ndarray):
        return "levels_not_array"
    if levels.ndim != 1:
        return "levels_not_vector"
    if len(levels) != int(expected_count):
        return "levels_count_mismatch"
    if len(levels) < 2:
        return "levels_too_few"
    if not np.all(np.isfinite(levels)):
        return "levels_non_finite"
    diffs = np.diff(levels.astype(float))
    if np.any(diffs <= float(eps)):
        return "levels_non_increasing_or_duplicate"
    return None


def _validate_grid_level_geometry(
    box_low: float,
    box_high: float,
    n_levels: int,
    tick_size: Optional[float],
) -> Optional[str]:
    if int(n_levels) <= 0:
        return "invalid_n_levels"
    if not np.isfinite(float(box_low)) or not np.isfinite(float(box_high)):
        return "invalid_box_bounds_non_finite"
    if float(box_high) <= float(box_low):
        return "invalid_box_bounds_order"
    levels = build_levels(float(box_low), float(box_high), int(n_levels), tick_size=tick_size)
    return _levels_validation_error(levels, int(n_levels) + 1)


def plan_signature(plan: Dict) -> Tuple:
    """
    Signature used to detect material plan changes.
    IMPORTANT: do NOT include `action` (prevents churn).
    """
    try:
        r = plan["range"]
        g = plan["grid"]
        signature = (
            round(float(r["low"]), 12),
            round(float(r["high"]), 12),
            int(g["n_levels"]),
            round(float(g["step_price"]), 12),
        )
        _log_plan_marker(
            "plan_signature",
            plan,
            level="debug",
            range_low=float(r["low"]) if r.get("low") is not None else None,
            range_high=float(r["high"]) if r.get("high") is not None else None,
            n_levels=int(g["n_levels"]) if g.get("n_levels") is not None else None,
            step_price=float(g["step_price"]) if g.get("step_price") is not None else None,
        )
        return signature
    except Exception as exc:
        log_event(
            "error",
            "plan_signature_failed",
            error=str(exc),
            **_plan_context(plan),
        )
        raise


def soft_adjust_ok(prev_plan: Dict, new_plan: Dict) -> bool:
    """
    If edges moved only a small fraction of step, allow soft adjust:
    we keep the same order set but reprice each rung by level_index.
    """
    try:
        prev_low = float(prev_plan["range"]["low"])
        prev_high = float(prev_plan["range"]["high"])
        new_low = float(new_plan["range"]["low"])
        new_high = float(new_plan["range"]["high"])
        step = float(new_plan["grid"]["step_price"])
        frac = float(new_plan.get("update_policy", {}).get("soft_adjust_max_step_frac", 0.5))
        tol = frac * step
        return abs(new_low - prev_low) <= tol and abs(new_high - prev_high) <= tol
    except Exception as exc:
        prev_ctx = _plan_context(prev_plan)
        new_ctx = _plan_context(new_plan)
        log_event(
            "warning",
            "soft_adjust_exception",
            error=str(exc),
            prev_plan_ts=prev_ctx.get("plan_ts"),
            new_plan_ts=new_ctx.get("plan_ts"),
            prev_plan_path=prev_ctx.get("plan_path"),
            plan_path=new_ctx.get("plan_path"),
        )
        return False


def _action_signature(action: str, sig: Tuple, stop_reason: Optional[str] = None) -> Tuple:
    a = str(action or "HOLD").upper()
    if a == "STOP":
        return (a, sig, str(stop_reason or "plan_stop"))
    return (a, sig)


def quantize_price(exchange, symbol: str, price: float) -> float:
    if exchange is None:
        return float(price)
    return float(exchange.price_to_precision(symbol, price))


def quantize_amount(exchange, symbol: str, amount: float) -> float:
    if exchange is None:
        return float(amount)
    return float(exchange.amount_to_precision(symbol, amount))


def market_limits(exchange, symbol: str) -> Dict:
    if exchange is None:
        return {}
    try:
        m = exchange.market(symbol)
    except Exception:
        # Some ccxt exchanges need explicit market loading before market() lookup.
        try:
            exchange.load_markets()
            m = exchange.market(symbol)
        except Exception:
            return {}
    return {
        "min_amount": (m.get("limits", {}).get("amount", {}) or {}).get("min"),
        "min_cost": (m.get("limits", {}).get("cost", {}) or {}).get("min"),
    }


def passes_min_notional(limits: Dict, price: float, qty_base: float) -> bool:
    min_cost = limits.get("min_cost")
    if min_cost is None:
        return True
    return (price * qty_base) >= float(min_cost)


def _key_for(side: str, price: float, qty: float) -> Tuple:
    """
    Stable key for matching intended orders to live orders.
    """
    return (side, round(float(price), 12), round(float(qty), 12))


def _safe_float(x, default=None):
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _safe_int(x, default: Optional[int] = None) -> Optional[int]:
    try:
        if x is None:
            return int(default) if default is not None else None
        return int(x)
    except Exception:
        return int(default) if default is not None else None


def _safe_bool(x, default: bool) -> bool:
    if isinstance(x, bool):
        return x
    if isinstance(x, str):
        v = x.strip().lower()
        if v in ("1", "true", "yes", "on"):
            return True
        if v in ("0", "false", "no", "off"):
            return False
    if x is None:
        return bool(default)
    try:
        return bool(x)
    except Exception:
        return bool(default)


def _pair_fs(pair: str) -> str:
    return str(pair or "unknown_pair").replace("/", "_").replace(":", "_").strip("_")


def _extract_rung_weights(plan: Dict, n_levels: int) -> Optional[List[float]]:
    try:
        g = plan.get("grid", {}) or {}
        rb = g.get("rung_density_bias", {}) or {}
        ws = rb.get("weights_by_level_index")
        if ws is None:
            return None
        vals = [max(float(x), 0.0) for x in ws]
        if len(vals) != n_levels + 1:
            return None
        if not any(v > 0 for v in vals):
            return None
        normalized = [float(v) for v in vals]
        _log_plan_marker(
            "rung_weights",
            plan,
            level="debug",
            n_levels=n_levels,
            weights=normalized,
        )
        return normalized
    except Exception as exc:
        log_event(
            "warning",
            "extract_rung_weights_failed",
            error=str(exc),
            n_levels=n_levels,
            **_plan_context(plan),
        )
        return None


def _normalized_side_weights(indices: List[int], rung_weights: Optional[List[float]]) -> List[float]:
    if not indices:
        return []
    if rung_weights is None:
        return [1.0 / len(indices)] * len(indices)

    vals = [max(float(rung_weights[i]), 0.0) if 0 <= i < len(rung_weights) else 0.0 for i in indices]
    s = float(sum(vals))
    if s <= 0:
        return [1.0 / len(indices)] * len(indices)
    return [float(v / s) for v in vals]


class FillCooldownGuard:
    def __init__(self, cooldown_bars: int, no_repeat_lsi_guard: bool = True) -> None:
        self.cooldown_bars = max(int(cooldown_bars), 0)
        self.no_repeat_lsi_guard = bool(no_repeat_lsi_guard)
        self._last_fill_by_key: Dict[Tuple[str, int], int] = {}

    def configure(
        self,
        *,
        cooldown_bars: Optional[int] = None,
        no_repeat_lsi_guard: Optional[bool] = None,
    ) -> None:
        if cooldown_bars is not None:
            self.cooldown_bars = max(int(cooldown_bars), 0)
        if no_repeat_lsi_guard is not None:
            self.no_repeat_lsi_guard = bool(no_repeat_lsi_guard)

    def allow(self, side: str, level_index: int, bar_index: int) -> bool:
        if not self.no_repeat_lsi_guard:
            return True
        last = self._last_fill_by_key.get((str(side), int(level_index)))
        if last is None:
            return True
        return bool((int(bar_index) - int(last)) > self.cooldown_bars)

    def mark(self, side: str, level_index: int, bar_index: int) -> None:
        if not self.no_repeat_lsi_guard:
            return
        self._last_fill_by_key[(str(side), int(level_index))] = int(bar_index)


# -----------------------------
# Core executor logic
# -----------------------------
class GridExecutorV1:
    """
    Executor v1 (Binance Spot ready):
    - paper mode: writes intended ladder (no fills)
    - ccxt mode: places/cancels orders AND ingests fills via fetch_my_trades()

    This stays "small and reliable":
    - We assume LIMIT orders (post-only if enabled).
    - We handle partial fills by placing opposite rung for the filled portion.
    - We refresh balances from the exchange (optional, ON by default in ccxt).
    """

    def __init__(
        self,
        mode: str,
        state_out: str,
        poll_seconds: float,
        quote_budget: float,
        start_base: float,
        maker_fee_pct: float,
        post_only: bool,
        max_orders_per_side: int,
        exchange_name: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        api_password: Optional[str] = None,
        sandbox: bool = False,
        ccxt_retries: int = 3,
        use_exchange_balance: bool = True,
        close_on_stop: bool = False,
        trade_lookback_ms: int = 60_000,
    ):
        self.mode = mode
        self.state_out = state_out
        self.poll_seconds = poll_seconds

        self.quote_total = float(quote_budget)
        self.base_total = float(start_base)

        self.maker_fee_pct = float(maker_fee_pct)
        self.post_only = bool(post_only)
        self.max_orders_per_side = int(max_orders_per_side)

        self.exchange = None
        self.exchange_name = exchange_name
        self.symbol: Optional[str] = None

        self.ccxt_retries = int(ccxt_retries)
        self.use_exchange_balance = bool(use_exchange_balance)
        self.close_on_stop = bool(close_on_stop)
        self._state_schema_version = "1.0.0"

        # runtime
        self._prev_plan: Optional[Dict] = None
        self._orders: List[RestingOrder] = []
        self._seen_trade_ids: set = set()
        self._last_trade_ms: Optional[int] = None
        self._trade_lookback_ms = int(trade_lookback_ms)
        self._last_mark_price: Optional[float] = None
        self._last_tp_price: Optional[float] = None
        self._last_sl_price: Optional[float] = None
        self._last_stop_reason: Optional[str] = None
        self._last_raw_action: Optional[str] = None
        self._last_effective_action: Optional[str] = None
        self._last_action_suppression_reason: Optional[str] = None
        self._last_effective_action_signature: Optional[Tuple] = None
        self._fill_confirmation_mode: str = "Touch"
        self._fill_no_repeat_lsi_guard: bool = True
        self._fill_cooldown_bars: int = 1
        self._fill_guard = FillCooldownGuard(
            self._fill_cooldown_bars,
            no_repeat_lsi_guard=self._fill_no_repeat_lsi_guard,
        )
        self._fill_guard_bar_seq: int = 0
        self._fill_guard_last_clock_ts: Optional[int] = None
        self._tick_size: Optional[float] = None
        self._runtime_warnings: List[str] = []
        self._runtime_exec_events: List[str] = []
        self._runtime_pause_reasons: List[str] = []
        self._runtime_confirm: Dict[str, object] = {}
        self._capacity_guard_state: Dict[str, object] = {}
        self._capacity_rung_cap_applied_total: int = 0
        self._capacity_replenish_skipped_total: int = 0

        # Step-12 hardening defaults; can be overridden per-plan.
        self._post_only_place_attempts: int = max(int(self.ccxt_retries), 3)
        self._post_only_backoff_ms: int = 120
        self._post_only_backoff_max_ms: int = 1200
        self._post_only_reprice_ticks: int = 1
        self._post_only_reject_window_s: int = 120
        self._post_only_reject_warn_count: int = 4
        self._post_only_reject_hard_count: int = 8
        self._post_only_reject_times: Deque[float] = deque()
        self._post_only_reject_streak: int = 0
        self._post_only_retry_count_total: int = 0
        self._post_only_reprice_count_total: int = 0
        self._post_only_burst_hard_active: bool = False

        self._confirm_entry_enabled: bool = True
        self._confirm_exit_enabled: bool = True
        self._confirm_rebuild_enabled: bool = True
        self._confirm_spread_max: Optional[float] = None
        self._confirm_depth_thinning_max: Optional[float] = None
        self._confirm_jump_max: Optional[float] = 0.01
        self._capacity_cap_enabled: bool = True
        self._capacity_spread_wide_threshold: float = 0.0030
        self._capacity_depth_thin_threshold: float = 0.60
        self._capacity_spread_cap_multiplier: float = 0.60
        self._capacity_depth_cap_multiplier: float = 0.60
        self._capacity_min_rung_cap: int = 1
        self._capacity_top_book_safety_fraction: float = 0.25
        self._capacity_delay_replenish_on_thin: bool = True

        self._reconcile_price_tol_ticks: int = 1
        self._reconcile_price_tol_frac: float = 0.00025
        self._reconcile_qty_tol_frac: float = 0.02
        self._reconcile_max_actions_per_tick: int = 100
        self._last_reconcile_summary: Dict[str, int] = {}
        self._last_reconcile_skipped_due_cap: bool = False

        self._ccxt_error_streak: int = 0
        self._ccxt_backoff_base_ms: int = 250
        self._ccxt_backoff_max_ms: int = 5_000
        self._ccxt_backoff_until_ts: float = 0.0
        self._last_ccxt_error: Optional[str] = None
        self._recovery_loaded: bool = False
        self._recovery_error: Optional[str] = None
        self._last_applied_plan_id: Optional[str] = None
        self._last_applied_seq: int = 0
        self._last_applied_valid_for_candle_ts: int = 0
        self._last_applied_plan_hash: Optional[str] = None
        self._applied_plan_ids: Deque[str] = deque(maxlen=4096)
        self._applied_plan_id_set: Set[str] = set()
        self._applied_plan_hashes: Deque[str] = deque(maxlen=4096)
        self._applied_plan_hash_set: Set[str] = set()

        # Section 13.2 / M1005 execution-cost lifecycle feedback loop.
        self._execution_cost_feedback_enabled: bool = True
        self._execution_cost_window: int = 256
        self._execution_cost_percentile: float = 90.0
        self._execution_cost_min_samples: int = 8
        self._execution_cost_stale_steps: int = 128
        self._execution_cost_retry_penalty_pct: float = 0.001
        self._execution_cost_missed_fill_penalty_pct: float = 0.001
        self._execution_cost_calibrator = EmpiricalCostCalibrator(self._execution_cost_window)
        self._execution_cost_last_artifact: Optional[Dict[str, object]] = None
        self._execution_cost_artifact_paths_by_pair: Dict[str, Dict[str, str]] = {}
        self._execution_cost_samples_written_by_pair: Dict[str, int] = {}
        self._execution_cost_step_metrics: Dict[str, object] = {}
        self._execution_cost_artifact_root = (
            Path(self.state_out).resolve().parent / "artifacts" / "execution_cost"
        )

        if self.mode == "ccxt":
            if ccxt is None:
                raise RuntimeError("ccxt is not installed in this environment.")
            if not exchange_name:
                raise ValueError("--exchange required for --mode ccxt")
            ex_cls = getattr(ccxt, exchange_name, None)
            if ex_cls is None:
                raise ValueError(f"Unknown exchange in ccxt: {exchange_name}")

            # NOTE: For Binance spot, defaultType='spot' prevents accidental futures endpoints.
            opts = {
                "enableRateLimit": True,
                "apiKey": api_key or "",
                "secret": api_secret or "",
                "password": api_password or None,
                "options": {"defaultType": "spot"},
            }
            self.exchange = ex_cls(opts)

            if sandbox and hasattr(self.exchange, "set_sandbox_mode"):
                self.exchange.set_sandbox_mode(True)

        self._recover_state_from_disk()

    # ---------- balances / reserves ----------
    def _reserved_balances_intent(self) -> Tuple[float, float]:
        """
        Reserve amounts implied by open orders (intent view).
        """
        fee = self.maker_fee_pct / 100.0
        q_res = 0.0
        b_res = 0.0
        for o in self._orders:
            if o.status not in ("open", "partial"):
                continue
            if o.side == "buy":
                cost = max((o.qty_base - o.filled_base), 0.0) * o.price
                q_res += cost * (1.0 + fee)
            else:
                b_res += max((o.qty_base - o.filled_base), 0.0)
        return q_res, b_res

    def _free_balances_intent(self) -> Tuple[float, float]:
        q_res, b_res = self._reserved_balances_intent()
        return max(self.quote_total - q_res, 0.0), max(self.base_total - b_res, 0.0)

    def _sync_balance_ccxt(self) -> None:
        """
        In ccxt mode, refresh totals from exchange balance.
        Uses the quote/base currencies derived from symbol.
        """
        if self.exchange is None or self.symbol is None:
            return
        if not self.use_exchange_balance:
            return

        try:
            bal = self._ccxt_call(self.exchange.fetch_balance) or {}
            base_ccy, quote_ccy = self.symbol.split("/")
            base = bal.get(base_ccy, {}) or {}
            quote = bal.get(quote_ccy, {}) or {}

            # ccxt returns dicts like {free, used, total}
            base_total = _safe_float(base.get("total"), default=self.base_total)
            quote_total = _safe_float(quote.get("total"), default=self.quote_total)

            if base_total is not None:
                self.base_total = float(base_total)
            if quote_total is not None:
                self.quote_total = float(quote_total)
        except Exception:
            # best-effort only
            pass

    def _recover_state_from_disk(self) -> None:
        if not self.state_out:
            return
        if not os.path.exists(self.state_out):
            return
        try:
            payload = load_json(self.state_out)
            if not isinstance(payload, dict):
                return

            qt = _safe_float(payload.get("quote_total"), default=None)
            bt = _safe_float(payload.get("base_total"), default=None)
            if qt is not None:
                self.quote_total = float(qt)
            if bt is not None:
                self.base_total = float(bt)

            runtime = payload.get("runtime", {}) or {}
            self._last_trade_ms = _safe_int(runtime.get("last_trade_ms"), 0) or None
            self._fill_guard_bar_seq = _safe_int(runtime.get("fill_guard_bar_seq"), self._fill_guard_bar_seq)
            last_clock = _safe_float(runtime.get("fill_guard_last_clock_ts"), default=None)
            self._fill_guard_last_clock_ts = int(last_clock) if last_clock is not None else self._fill_guard_last_clock_ts
            self._post_only_retry_count_total = _safe_int(
                runtime.get("post_only_retry_count_total"),
                self._post_only_retry_count_total,
            )
            self._post_only_reprice_count_total = _safe_int(
                runtime.get("post_only_reprice_count_total"),
                self._post_only_reprice_count_total,
            )

            last_applied_plan_id = payload.get("last_applied_plan_id") or runtime.get("last_applied_plan_id")
            if last_applied_plan_id:
                self._last_applied_plan_id = str(last_applied_plan_id)
            self._last_applied_seq = max(
                _safe_int(payload.get("last_applied_seq"), self._last_applied_seq),
                _safe_int(runtime.get("last_applied_seq"), self._last_applied_seq),
            )
            self._last_applied_valid_for_candle_ts = max(
                _safe_int(
                    payload.get("last_applied_valid_for_candle_ts"),
                    self._last_applied_valid_for_candle_ts,
                ),
                _safe_int(
                    runtime.get("last_applied_valid_for_candle_ts"),
                    self._last_applied_valid_for_candle_ts,
                ),
            )
            last_plan_hash = payload.get("last_plan_hash") or runtime.get("last_plan_hash")
            if last_plan_hash:
                self._last_applied_plan_hash = str(last_plan_hash)

            for pid in payload.get("applied_plan_ids") or []:
                if pid is not None:
                    self._remember_applied_plan_id(str(pid))
            for ph in payload.get("applied_plan_hashes") or []:
                if ph is not None:
                    self._remember_applied_plan_hash(str(ph))
            if self._last_applied_plan_id:
                self._remember_applied_plan_id(self._last_applied_plan_id)
            if self._last_applied_plan_hash:
                self._remember_applied_plan_hash(self._last_applied_plan_hash)

            loaded_orders: List[RestingOrder] = []
            for row in payload.get("orders") or []:
                if not isinstance(row, dict):
                    continue
                status = str(row.get("status", "open")).lower()
                if status not in ("open", "partial"):
                    continue
                loaded_orders.append(
                    RestingOrder(
                        side=str(row.get("side", "")),
                        price=float(row.get("price") or 0.0),
                        qty_base=float(row.get("qty_base") or 0.0),
                        level_index=int(row.get("level_index") or 0),
                        order_id=(str(row.get("order_id")) if row.get("order_id") is not None else None),
                        status=status,
                        filled_base=float(row.get("filled_base") or 0.0),
                    )
                )
            if loaded_orders:
                self._orders = loaded_orders

            self._recovery_loaded = True
            self._recovery_error = None
        except Exception as exc:
            self._recovery_error = str(exc)
            log_event(
                "warning",
                "state_recovery_failed",
                state_out=self.state_out,
                error=str(exc),
            )

    def _reset_runtime_diagnostics(self) -> None:
        self._runtime_warnings = []
        self._runtime_exec_events = []
        self._runtime_pause_reasons = []
        self._runtime_confirm = {}
        self._last_reconcile_summary = {}
        self._last_reconcile_skipped_due_cap = False
        self._capacity_guard_state = {}
        self._execution_cost_step_metrics = {
            "orders_placed": 0,
            "orders_rejected": 0,
            "orders_canceled": 0,
            "orders_repriced": 0,
            "fills": 0,
            "missed_fill_opportunities": 0,
            "fill_spread_samples": [],
            "fill_adverse_selection_samples": [],
        }

    def _append_runtime_warning(self, code: str) -> None:
        c = str(code).strip()
        if c and c not in self._runtime_warnings:
            self._runtime_warnings.append(c)

    def _append_runtime_exec_event(self, code: str) -> None:
        c = str(code).strip()
        if c and c not in self._runtime_exec_events:
            self._runtime_exec_events.append(c)

    def _append_runtime_pause_reason(self, code: str) -> None:
        c = str(code).strip()
        if c and c not in self._runtime_pause_reasons:
            self._runtime_pause_reasons.append(c)

    def _remember_applied_plan_id(self, plan_id: str) -> None:
        pid = str(plan_id or "").strip()
        if not pid or pid in self._applied_plan_id_set:
            return
        if len(self._applied_plan_ids) >= self._applied_plan_ids.maxlen:
            oldest = self._applied_plan_ids.popleft()
            self._applied_plan_id_set.discard(oldest)
        self._applied_plan_ids.append(pid)
        self._applied_plan_id_set.add(pid)

    def _remember_applied_plan_hash(self, plan_hash: str) -> None:
        ph = str(plan_hash or "").strip()
        if not ph or ph in self._applied_plan_hash_set:
            return
        if len(self._applied_plan_hashes) >= self._applied_plan_hashes.maxlen:
            oldest = self._applied_plan_hashes.popleft()
            self._applied_plan_hash_set.discard(oldest)
        self._applied_plan_hashes.append(ph)
        self._applied_plan_hash_set.add(ph)

    def _record_applied_plan(self, plan: Dict) -> None:
        plan_id = str(plan.get("plan_id") or "").strip()
        if plan_id:
            self._remember_applied_plan_id(plan_id)
            self._last_applied_plan_id = plan_id
        try:
            self._last_applied_seq = max(int(plan.get("decision_seq") or 0), self._last_applied_seq)
        except Exception:
            pass
        try:
            valid_for_candle_ts = int(plan.get("valid_for_candle_ts") or 0)
            if valid_for_candle_ts > 0:
                self._last_applied_valid_for_candle_ts = max(
                    valid_for_candle_ts,
                    self._last_applied_valid_for_candle_ts,
                )
        except Exception:
            pass
        plan_hash = str(plan.get("plan_hash") or "").strip()
        if plan_hash:
            self._remember_applied_plan_hash(plan_hash)
            self._last_applied_plan_hash = plan_hash

    def _reject_plan_intake(self, plan: Dict, code: str, reason: str) -> None:
        self._append_runtime_exec_event(code)
        self._last_raw_action = "HOLD"
        self._last_effective_action = "HOLD"
        self._last_action_suppression_reason = f"plan_rejected:{code}"
        log_event(
            "warning",
            "plan_rejected",
            plan=plan,
            code=code,
            reason=reason,
            last_applied_seq=int(self._last_applied_seq),
            last_applied_valid_for_candle_ts=int(self._last_applied_valid_for_candle_ts),
            last_applied_plan_id=self._last_applied_plan_id,
        )

    def _validate_plan_intake(self, plan: Dict) -> Tuple[bool, Optional[str]]:
        if not isinstance(plan, dict):
            self._reject_plan_intake({}, "EXEC_PLAN_SCHEMA_INVALID", "plan_not_object")
            return False, "EXEC_PLAN_SCHEMA_INVALID"

        schema_errors = validate_schema(plan, "grid_plan.schema.json")
        if schema_errors:
            self._reject_plan_intake(plan, "EXEC_PLAN_SCHEMA_INVALID", ",".join(schema_errors[:3]))
            return False, "EXEC_PLAN_SCHEMA_INVALID"

        schema_errors = validate_signature_fields(plan)
        if "range" not in plan or "grid" not in plan:
            schema_errors.append("missing:range_grid")
        if schema_errors:
            self._reject_plan_intake(plan, "EXEC_PLAN_SCHEMA_INVALID", ",".join(schema_errors))
            return False, "EXEC_PLAN_SCHEMA_INVALID"

        range_block = plan.get("range") if isinstance(plan.get("range"), dict) else {}
        grid_block = plan.get("grid") if isinstance(plan.get("grid"), dict) else {}
        try:
            box_low = float(range_block.get("low"))
            box_high = float(range_block.get("high"))
            n_levels = int(grid_block.get("n_levels"))
            tick_size = _safe_float(grid_block.get("tick_size"), default=None)
        except Exception:
            self._append_runtime_warning("BLOCK_N_LEVELS_INVALID")
            self._reject_plan_intake(plan, "EXEC_PLAN_SCHEMA_INVALID", "invalid_levels:parse_error")
            return False, "EXEC_PLAN_SCHEMA_INVALID"

        level_error = _validate_grid_level_geometry(
            box_low=box_low,
            box_high=box_high,
            n_levels=n_levels,
            tick_size=tick_size,
        )
        if level_error:
            self._append_runtime_warning("BLOCK_N_LEVELS_INVALID")
            self._reject_plan_intake(plan, "EXEC_PLAN_SCHEMA_INVALID", f"invalid_levels:{level_error}")
            return False, "EXEC_PLAN_SCHEMA_INVALID"

        plan_symbol = plan_pair(plan)
        if self.symbol and plan_symbol and (str(plan_symbol) != str(self.symbol)):
            self._reject_plan_intake(
                plan,
                "EXEC_PLAN_SCHEMA_INVALID",
                f"pair_mismatch expected={self.symbol} got={plan_symbol}",
            )
            return False, "EXEC_PLAN_SCHEMA_INVALID"

        expected_hash = compute_plan_hash(plan)
        provided_hash = str(plan.get("plan_hash") or "").strip()
        if expected_hash != provided_hash:
            self._reject_plan_intake(
                plan,
                "EXEC_PLAN_HASH_MISMATCH",
                f"expected={expected_hash} provided={provided_hash}",
            )
            return False, "EXEC_PLAN_HASH_MISMATCH"

        if plan_is_expired(plan):
            self._reject_plan_intake(plan, "EXEC_PLAN_EXPIRED_IGNORED", "plan_expired")
            return False, "EXEC_PLAN_EXPIRED_IGNORED"

        plan_id = str(plan.get("plan_id") or "").strip()
        if plan_id and (plan_id in self._applied_plan_id_set):
            self._reject_plan_intake(plan, "EXEC_PLAN_DUPLICATE_IGNORED", "duplicate_plan_id")
            return False, "EXEC_PLAN_DUPLICATE_IGNORED"

        if provided_hash and (provided_hash in self._applied_plan_hash_set):
            self._reject_plan_intake(plan, "EXEC_PLAN_DUPLICATE_IGNORED", "duplicate_plan_hash_seen")
            return False, "EXEC_PLAN_DUPLICATE_IGNORED"

        try:
            decision_seq = int(plan.get("decision_seq") or 0)
        except Exception:
            decision_seq = 0
        if decision_seq <= int(self._last_applied_seq):
            self._reject_plan_intake(
                plan,
                "EXEC_PLAN_STALE_SEQ_IGNORED",
                f"decision_seq={decision_seq} last_applied_seq={self._last_applied_seq}",
            )
            return False, "EXEC_PLAN_STALE_SEQ_IGNORED"

        try:
            valid_for_candle_ts = int(plan.get("valid_for_candle_ts") or 0)
        except Exception:
            valid_for_candle_ts = 0
        if valid_for_candle_ts <= int(self._last_applied_valid_for_candle_ts):
            self._reject_plan_intake(
                plan,
                "EXEC_PLAN_STALE_SEQ_IGNORED",
                (
                    "stale_valid_for_candle_ts="
                    f"{valid_for_candle_ts} last_valid_for_candle_ts={self._last_applied_valid_for_candle_ts}"
                ),
            )
            return False, "EXEC_PLAN_STALE_SEQ_IGNORED"

        supersedes_plan_id = str(plan.get("supersedes_plan_id") or "").strip()
        if (
            supersedes_plan_id
            and self._last_applied_plan_id
            and supersedes_plan_id != str(self._last_applied_plan_id)
        ):
            self._reject_plan_intake(
                plan,
                "EXEC_PLAN_STALE_SEQ_IGNORED",
                (
                    "supersedes_mismatch="
                    f"{supersedes_plan_id} last_applied_plan_id={self._last_applied_plan_id}"
                ),
            )
            return False, "EXEC_PLAN_STALE_SEQ_IGNORED"

        if self._last_applied_plan_hash and provided_hash == self._last_applied_plan_hash:
            self._reject_plan_intake(plan, "EXEC_PLAN_DUPLICATE_IGNORED", "duplicate_plan_hash")
            return False, "EXEC_PLAN_DUPLICATE_IGNORED"

        return True, None

    def _write_rejected_plan_state(self, plan: Dict) -> None:
        ex_name = str(plan.get("exchange") or self.exchange_name or "unknown")
        symbol = plan_pair(plan) or self.symbol or "UNKNOWN/UNKNOWN"
        self.symbol = symbol
        range_block = plan.get("range") if isinstance(plan.get("range"), dict) else {}
        grid_block = plan.get("grid") if isinstance(plan.get("grid"), dict) else {}
        box_low = _safe_float(range_block.get("low"), default=0.0) or 0.0
        box_high = _safe_float(range_block.get("high"), default=0.0) or 0.0
        n_levels = max(_safe_int(grid_block.get("n_levels"), 1), 1)
        step = _safe_float(grid_block.get("step_price"), default=0.0) or 0.0
        self._write_state(plan, ex_name, symbol, step, n_levels, box_low, box_high)

    def _execution_cfg(self, plan: Dict) -> Dict:
        candidates = [
            plan.get("execution_hardening"),
            (plan.get("executor") or {}).get("hardening"),
            plan.get("executor_hardening"),
            (plan.get("grid") or {}).get("execution_hardening"),
            (plan.get("runtime_state") or {}).get("execution_hardening"),
        ]
        for c in candidates:
            if isinstance(c, dict):
                return c
        return {}

    def _apply_execution_hardening_config(self, plan: Dict) -> None:
        cfg = self._execution_cfg(plan)
        post_cfg = cfg.get("post_only", {}) if isinstance(cfg.get("post_only"), dict) else {}
        conf_cfg = cfg.get("confirm_hooks", {}) if isinstance(cfg.get("confirm_hooks"), dict) else {}
        cap_cfg = cfg.get("capacity_cap", {}) if isinstance(cfg.get("capacity_cap"), dict) else {}
        cost_cfg = (
            cfg.get("execution_cost_feedback", {})
            if isinstance(cfg.get("execution_cost_feedback"), dict)
            else {}
        )
        rec_cfg = cfg.get("reconcile", {}) if isinstance(cfg.get("reconcile"), dict) else {}
        ccxt_cfg = cfg.get("ccxt", {}) if isinstance(cfg.get("ccxt"), dict) else {}

        self._post_only_place_attempts = max(
            _safe_int(post_cfg.get("max_attempts"), self._post_only_place_attempts),
            1,
        )
        self._post_only_backoff_ms = max(
            _safe_int(post_cfg.get("backoff_ms"), self._post_only_backoff_ms),
            0,
        )
        self._post_only_backoff_max_ms = max(
            _safe_int(post_cfg.get("backoff_max_ms"), self._post_only_backoff_max_ms),
            self._post_only_backoff_ms,
        )
        self._post_only_reprice_ticks = max(
            _safe_int(post_cfg.get("reprice_ticks"), self._post_only_reprice_ticks),
            0,
        )
        self._post_only_reject_window_s = max(
            _safe_int(post_cfg.get("reject_window_s"), self._post_only_reject_window_s),
            1,
        )
        self._post_only_reject_warn_count = max(
            _safe_int(post_cfg.get("reject_warn_count"), self._post_only_reject_warn_count),
            1,
        )
        self._post_only_reject_hard_count = max(
            _safe_int(post_cfg.get("reject_hard_count"), self._post_only_reject_hard_count),
            self._post_only_reject_warn_count,
        )

        self._confirm_entry_enabled = _safe_bool(
            conf_cfg.get("confirm_entry_enabled"),
            self._confirm_entry_enabled,
        )
        self._confirm_exit_enabled = _safe_bool(
            conf_cfg.get("confirm_exit_enabled"),
            self._confirm_exit_enabled,
        )
        self._confirm_rebuild_enabled = _safe_bool(
            conf_cfg.get("confirm_rebuild_enabled"),
            self._confirm_rebuild_enabled,
        )
        spread_max = _safe_float(conf_cfg.get("spread_max"), default=self._confirm_spread_max)
        self._confirm_spread_max = spread_max if spread_max is not None and spread_max > 0 else None
        depth_max = _safe_float(
            conf_cfg.get("depth_thinning_max"),
            default=self._confirm_depth_thinning_max,
        )
        self._confirm_depth_thinning_max = depth_max if depth_max is not None and depth_max > 0 else None
        jump_max = _safe_float(conf_cfg.get("jump_max"), default=self._confirm_jump_max)
        self._confirm_jump_max = jump_max if jump_max is not None and jump_max > 0 else None

        self._capacity_cap_enabled = _safe_bool(cap_cfg.get("enabled"), self._capacity_cap_enabled)
        self._capacity_spread_wide_threshold = max(
            _safe_float(cap_cfg.get("spread_wide_threshold"), default=self._capacity_spread_wide_threshold) or 0.0,
            0.0,
        )
        self._capacity_depth_thin_threshold = max(
            _safe_float(cap_cfg.get("depth_thin_threshold"), default=self._capacity_depth_thin_threshold) or 0.0,
            0.0,
        )
        self._capacity_spread_cap_multiplier = max(
            _safe_float(cap_cfg.get("spread_cap_multiplier"), default=self._capacity_spread_cap_multiplier) or 0.0,
            0.0,
        )
        self._capacity_depth_cap_multiplier = max(
            _safe_float(cap_cfg.get("depth_cap_multiplier"), default=self._capacity_depth_cap_multiplier) or 0.0,
            0.0,
        )
        self._capacity_min_rung_cap = max(
            _safe_int(cap_cfg.get("min_rung_cap"), self._capacity_min_rung_cap),
            1,
        )
        self._capacity_top_book_safety_fraction = max(
            _safe_float(
                cap_cfg.get("top_book_safety_fraction"),
                default=self._capacity_top_book_safety_fraction,
            )
            or 0.0,
            0.0,
        )
        self._capacity_delay_replenish_on_thin = _safe_bool(
            cap_cfg.get("delay_replenish_on_thin"),
            self._capacity_delay_replenish_on_thin,
        )

        self._execution_cost_feedback_enabled = _safe_bool(
            cost_cfg.get("enabled"),
            self._execution_cost_feedback_enabled,
        )
        window = max(_safe_int(cost_cfg.get("window"), self._execution_cost_window), 1)
        if window != self._execution_cost_window:
            self._execution_cost_window = int(window)
            self._execution_cost_calibrator = EmpiricalCostCalibrator(self._execution_cost_window)
        self._execution_cost_percentile = float(
            np.clip(
                _safe_float(cost_cfg.get("percentile"), default=self._execution_cost_percentile)
                or self._execution_cost_percentile,
                0.0,
                100.0,
            )
        )
        self._execution_cost_min_samples = max(
            _safe_int(cost_cfg.get("min_samples"), self._execution_cost_min_samples),
            1,
        )
        self._execution_cost_stale_steps = max(
            _safe_int(cost_cfg.get("stale_steps"), self._execution_cost_stale_steps),
            0,
        )
        self._execution_cost_retry_penalty_pct = max(
            _safe_float(
                cost_cfg.get("retry_penalty_pct"),
                default=self._execution_cost_retry_penalty_pct,
            )
            or 0.0,
            0.0,
        )
        self._execution_cost_missed_fill_penalty_pct = max(
            _safe_float(
                cost_cfg.get("missed_fill_penalty_pct"),
                default=self._execution_cost_missed_fill_penalty_pct,
            )
            or 0.0,
            0.0,
        )
        artifact_rel = str(cost_cfg.get("artifact_dir") or "").strip()
        if artifact_rel:
            self._execution_cost_artifact_root = (
                Path(self.state_out).resolve().parent / artifact_rel
            )

        self._reconcile_price_tol_ticks = max(
            _safe_int(rec_cfg.get("price_tol_ticks"), self._reconcile_price_tol_ticks),
            0,
        )
        self._reconcile_price_tol_frac = max(
            _safe_float(rec_cfg.get("price_tol_frac"), default=self._reconcile_price_tol_frac) or 0.0,
            0.0,
        )
        self._reconcile_qty_tol_frac = max(
            _safe_float(rec_cfg.get("qty_tol_frac"), default=self._reconcile_qty_tol_frac) or 0.0,
            0.0,
        )
        self._reconcile_max_actions_per_tick = max(
            _safe_int(rec_cfg.get("max_actions_per_tick"), self._reconcile_max_actions_per_tick),
            1,
        )

        self._ccxt_backoff_base_ms = max(
            _safe_int(ccxt_cfg.get("backoff_base_ms"), self._ccxt_backoff_base_ms),
            0,
        )
        self._ccxt_backoff_max_ms = max(
            _safe_int(ccxt_cfg.get("backoff_max_ms"), self._ccxt_backoff_max_ms),
            self._ccxt_backoff_base_ms,
        )

    def _prune_post_only_reject_window(self, now_ts: float) -> None:
        cutoff = float(now_ts) - float(self._post_only_reject_window_s)
        while self._post_only_reject_times and float(self._post_only_reject_times[0]) < cutoff:
            self._post_only_reject_times.popleft()

    def _register_post_only_reject(self, error: str) -> None:
        now_ts = float(time.time())
        self._post_only_reject_streak = int(self._post_only_reject_streak + 1)
        self._post_only_retry_count_total = int(self._post_only_retry_count_total + 1)
        self._post_only_reject_times.append(now_ts)
        self._prune_post_only_reject_window(now_ts)

        reject_count = int(len(self._post_only_reject_times))
        if reject_count >= self._post_only_reject_warn_count:
            self._append_runtime_warning("WARN_EXEC_POST_ONLY_RETRY_HIGH")
        if reject_count >= self._post_only_reject_hard_count:
            if not self._post_only_burst_hard_active:
                self._append_runtime_exec_event("EVENT_POST_ONLY_REJECT_BURST")
            self._post_only_burst_hard_active = True
            self._append_runtime_pause_reason("PAUSE_EXECUTION_UNSAFE")

        log_event(
            "warning",
            "post_only_reject",
            error=str(error),
            reject_count=reject_count,
            reject_window_s=self._post_only_reject_window_s,
            reject_streak=self._post_only_reject_streak,
        )

    def _post_only_burst_status(self) -> Dict[str, object]:
        now_ts = float(time.time())
        self._prune_post_only_reject_window(now_ts)
        reject_count = int(len(self._post_only_reject_times))
        if reject_count == 0:
            self._post_only_reject_streak = 0
        warn_active = reject_count >= self._post_only_reject_warn_count
        hard_active = reject_count >= self._post_only_reject_hard_count
        self._post_only_burst_hard_active = bool(hard_active)
        if warn_active:
            self._append_runtime_warning("WARN_EXEC_POST_ONLY_RETRY_HIGH")
        if hard_active:
            self._append_runtime_pause_reason("PAUSE_EXECUTION_UNSAFE")
        return {
            "reject_count": reject_count,
            "warn_active": bool(warn_active),
            "hard_active": bool(hard_active),
            "window_s": int(self._post_only_reject_window_s),
        }

    def _is_post_only_reject_error(self, error: Exception) -> bool:
        msg = str(error or "").lower()
        if not msg:
            return False
        hints = (
            "post only",
            "postonly",
            "maker",
            "would be taker",
            "immediate-or-cancel",
            "not post only",
            "post-only",
        )
        return any(h in msg for h in hints)

    def _tick_for_price(self, price: float) -> float:
        if self._tick_size is not None and self._tick_size > 0:
            return float(self._tick_size)
        p = abs(float(price))
        return max(p * 0.0001, 1e-8)

    def _reprice_post_only_price(self, side: str, price: float, attempt: int) -> float:
        if self._post_only_reprice_ticks <= 0:
            return float(price)
        tick = self._tick_for_price(price)
        delta = float(max(attempt, 1) * self._post_only_reprice_ticks) * tick
        if str(side).lower() == "buy":
            return float(max(float(price) - delta, tick))
        return float(float(price) + delta)

    def _confirm_metrics(
        self,
        plan: Dict,
        ref_price: Optional[float],
        prev_mark_price: Optional[float],
    ) -> Dict[str, Optional[float]]:
        grid = plan.get("grid", {}) or {}
        runtime = plan.get("runtime_state", {}) or {}
        signals = plan.get("signals", {}) or {}
        spread_pct = _safe_float(runtime.get("spread_pct"), default=None)
        if spread_pct is None:
            spread_pct = _safe_float(grid.get("est_spread_pct"), default=None)
        depth_thinning = _safe_float(runtime.get("depth_thinning_score"), default=None)
        if depth_thinning is None:
            depth_thinning = _safe_float(signals.get("depth_thinning_score"), default=None)
        jump_pct = _safe_float(runtime.get("jump_pct"), default=None)
        if jump_pct is None and ref_price is not None and prev_mark_price not in (None, 0):
            prev = float(prev_mark_price or 0.0)
            if prev > 0:
                jump_pct = abs(float(ref_price) - prev) / prev
        return {
            "spread_pct": spread_pct,
            "depth_thinning_score": depth_thinning,
            "jump_pct": jump_pct,
        }

    def _run_confirm_hook(
        self,
        phase: str,
        plan: Dict,
        ref_price: Optional[float],
        prev_mark_price: Optional[float],
    ) -> Dict[str, object]:
        ph = str(phase or "").lower()
        enabled = True
        if ph == "entry":
            enabled = self._confirm_entry_enabled
        elif ph == "rebuild":
            enabled = self._confirm_rebuild_enabled
        elif ph == "exit":
            enabled = self._confirm_exit_enabled

        metrics = self._confirm_metrics(plan, ref_price, prev_mark_price)
        reasons: List[str] = []
        burst = self._post_only_burst_status()

        if not enabled:
            return {
                "enabled": False,
                "ok": True,
                "phase": ph,
                "reasons": reasons,
                "metrics": metrics,
                "post_only_burst": burst,
            }

        if bool(burst.get("hard_active")):
            reasons.append("PAUSE_EXECUTION_UNSAFE")

        spread_pct = metrics.get("spread_pct")
        if self._confirm_spread_max is not None and spread_pct is not None:
            if float(spread_pct) > float(self._confirm_spread_max):
                reasons.append("PAUSE_EXECUTION_UNSAFE")
                self._append_runtime_exec_event("EVENT_SPREAD_SPIKE")

        depth_thinning = metrics.get("depth_thinning_score")
        if self._confirm_depth_thinning_max is not None and depth_thinning is not None:
            if float(depth_thinning) > float(self._confirm_depth_thinning_max):
                reasons.append("PAUSE_EXECUTION_UNSAFE")
                self._append_runtime_exec_event("EVENT_DEPTH_THIN")

        jump_pct = metrics.get("jump_pct")
        if self._confirm_jump_max is not None and jump_pct is not None:
            if float(jump_pct) > float(self._confirm_jump_max):
                reasons.append("PAUSE_EXECUTION_UNSAFE")
                self._append_runtime_exec_event("EVENT_JUMP_DETECTED")

        ok = len(reasons) == 0
        if not ok:
            self._append_runtime_pause_reason("PAUSE_EXECUTION_UNSAFE")

        return {
            "enabled": True,
            "ok": bool(ok),
            "phase": ph,
            "reasons": sorted(set([str(x) for x in reasons])),
            "metrics": metrics,
            "post_only_burst": burst,
        }

    def _extract_capacity_inputs(self, plan: Dict) -> Dict[str, object]:
        runtime = plan.get("runtime_state", {}) or {}
        runtime_hints = plan.get("runtime_hints", {}) or {}
        signals = plan.get("signals", {}) or {}
        diagnostics = plan.get("diagnostics", {}) or {}
        capacity_hint = runtime_hints.get("capacity_hint") or {}
        if not isinstance(capacity_hint, dict):
            capacity_hint = {}

        spread_pct = _safe_float(runtime.get("spread_pct"), default=None)
        if spread_pct is None:
            spread_pct = _safe_float(diagnostics.get("spread_pct"), default=None)
        if spread_pct is None:
            spread_pct = _safe_float(signals.get("spread_pct"), default=None)
        if spread_pct is None:
            spread_pct = _safe_float((plan.get("grid", {}) or {}).get("est_spread_pct"), default=None)

        depth_thinning = _safe_float(runtime.get("depth_thinning_score"), default=None)
        if depth_thinning is None:
            depth_thinning = _safe_float(diagnostics.get("depth_thinning_score"), default=None)
        if depth_thinning is None:
            depth_thinning = _safe_float(signals.get("depth_thinning_score"), default=None)

        top_book_notional = _safe_float(runtime.get("top_book_notional"), default=None)
        if top_book_notional is None:
            bid_notional = _safe_float(runtime.get("top_bid_notional"), default=None)
            ask_notional = _safe_float(runtime.get("top_ask_notional"), default=None)
            vals = [x for x in [bid_notional, ask_notional] if x is not None and x > 0]
            if vals:
                top_book_notional = float(min(vals))
        if top_book_notional is None:
            depth_top_levels = runtime.get("depth_top_levels_notional")
            if isinstance(depth_top_levels, dict):
                vals = [
                    _safe_float(depth_top_levels.get("bid"), default=None),
                    _safe_float(depth_top_levels.get("ask"), default=None),
                ]
                vals = [x for x in vals if x is not None and x > 0]
                if vals:
                    top_book_notional = float(min(vals))
            else:
                top_book_notional = _safe_float(depth_top_levels, default=None)

        runtime_capacity_ok = True
        runtime_reasons: List[str] = []
        runtime_cap_ok_raw = runtime.get("capacity_ok")
        if isinstance(runtime_cap_ok_raw, bool):
            runtime_capacity_ok = bool(runtime_cap_ok_raw)
        for src in (
            runtime.get("capacity_reasons"),
            diagnostics.get("capacity_reasons"),
            capacity_hint.get("reason"),
        ):
            if isinstance(src, list):
                runtime_reasons.extend([str(x) for x in src if str(x).strip()])
            elif src is not None and str(src).strip():
                runtime_reasons.append(str(src))

        hint_allow = capacity_hint.get("allow_start")
        hint_advisory_only = capacity_hint.get("advisory_only")
        if isinstance(hint_allow, bool):
            advisory = bool(hint_advisory_only) if isinstance(hint_advisory_only, bool) else True
            if not hint_allow and not advisory:
                runtime_capacity_ok = False
                if "BLOCK_CAPACITY_THIN" not in runtime_reasons:
                    runtime_reasons.append("BLOCK_CAPACITY_THIN")

        preferred_rung_cap = _safe_int((plan.get("capital_policy", {}) or {}).get("preferred_rung_cap"), 0)
        if preferred_rung_cap is not None and preferred_rung_cap <= 0:
            preferred_rung_cap = _safe_int(capacity_hint.get("preferred_rung_cap"), default=None)

        return {
            "spread_pct": spread_pct,
            "depth_thinning_score": depth_thinning,
            "top_book_notional": top_book_notional,
            "runtime_capacity_ok": bool(runtime_capacity_ok),
            "runtime_reasons": runtime_reasons,
            "preferred_rung_cap": preferred_rung_cap,
        }

    def _compute_capacity_state(
        self,
        plan: Dict,
        *,
        n_levels: int,
        grid_budget_pct: float,
    ) -> Dict[str, object]:
        if not self._capacity_cap_enabled:
            state = {
                "enabled": False,
                "capacity_ok": True,
                "max_safe_active_rungs": int(self.max_orders_per_side),
                "max_safe_rung_notional": None,
                "reasons": [],
                "delay_replenishment": False,
                "preferred_rung_cap": None,
                "base_rung_cap": int(self.max_orders_per_side),
                "applied_rung_cap": int(self.max_orders_per_side),
                "rung_cap_applied": False,
                "spread_pct": None,
                "depth_thinning_score": None,
                "top_book_notional": None,
            }
            self._capacity_guard_state = state
            return state

        inputs = self._extract_capacity_inputs(plan)
        state = compute_dynamic_capacity_state(
            max_orders_per_side=int(self.max_orders_per_side),
            n_levels=int(n_levels),
            quote_total=float(self.quote_total),
            grid_budget_pct=float(grid_budget_pct),
            preferred_rung_cap=_safe_int(inputs.get("preferred_rung_cap"), default=None),
            runtime_spread_pct=_safe_float(inputs.get("spread_pct"), default=None),
            runtime_depth_thinning_score=_safe_float(inputs.get("depth_thinning_score"), default=None),
            top_book_notional=_safe_float(inputs.get("top_book_notional"), default=None),
            runtime_capacity_ok=bool(inputs.get("runtime_capacity_ok", True)),
            runtime_reasons=[str(x) for x in (inputs.get("runtime_reasons") or [])],
            spread_wide_threshold=float(self._capacity_spread_wide_threshold),
            depth_thin_threshold=float(self._capacity_depth_thin_threshold),
            spread_cap_multiplier=float(self._capacity_spread_cap_multiplier),
            depth_cap_multiplier=float(self._capacity_depth_cap_multiplier),
            min_rung_cap=int(self._capacity_min_rung_cap),
            top_book_safety_fraction=float(self._capacity_top_book_safety_fraction),
            delay_replenish_on_thin=bool(self._capacity_delay_replenish_on_thin),
        )
        state["enabled"] = True
        self._capacity_guard_state = state
        if bool(state.get("rung_cap_applied")):
            self._capacity_rung_cap_applied_total = int(self._capacity_rung_cap_applied_total + 1)
            self._append_runtime_exec_event("EXEC_CAPACITY_RUNG_CAP_APPLIED")
        if not bool(state.get("capacity_ok", True)):
            self._append_runtime_warning("BLOCK_CAPACITY_THIN")
            self._append_runtime_pause_reason("BLOCK_CAPACITY_THIN")
        return state

    def _enforce_capacity_rung_cap(
        self,
        orders: List[RestingOrder],
        *,
        rung_cap: int,
        ref_price: float,
        symbol: Optional[str] = None,
    ) -> List[RestingOrder]:
        cap = max(int(rung_cap), 0)
        if cap <= 0:
            return []

        def _rank(side_orders: List[RestingOrder]) -> List[RestingOrder]:
            return sorted(
                side_orders,
                key=lambda o: (
                    abs(float(o.price) - float(ref_price)),
                    abs(int(o.level_index)),
                    float(o.price),
                ),
            )

        buys = [o for o in orders if str(o.side).lower() == "buy"]
        sells = [o for o in orders if str(o.side).lower() == "sell"]
        keep_ids = {
            id(o)
            for o in (_rank(buys)[:cap] + _rank(sells)[:cap])
        }
        out: List[RestingOrder] = []
        for o in orders:
            if id(o) in keep_ids:
                out.append(o)
            else:
                o.status = "canceled"
                if symbol is not None:
                    self._record_order_lifecycle_event(
                        symbol=symbol,
                        event_type="canceled",
                        side=o.side,
                        price=o.price,
                        qty_base=o.qty_base,
                        level_index=o.level_index,
                        order_id=o.order_id,
                        reason="capacity_rung_cap",
                        phase="capacity",
                    )
        return out

    def _execution_cost_paths(self, symbol: str) -> Dict[str, str]:
        pair_fs = _pair_fs(symbol)
        paths = self._execution_cost_artifact_paths_by_pair.get(pair_fs)
        if paths:
            return paths
        root = Path(self._execution_cost_artifact_root).resolve()
        root.mkdir(parents=True, exist_ok=True)
        pair_dir = root / pair_fs
        pair_dir.mkdir(parents=True, exist_ok=True)
        paths = {
            "artifact_latest": str(pair_dir / "execution_cost_calibration.latest.json"),
            "artifact_archive_dir": str(pair_dir),
            "orders_lifecycle": str(pair_dir / "order_lifecycle.jsonl"),
            "fills_lifecycle": str(pair_dir / "fills_lifecycle.jsonl"),
        }
        self._execution_cost_artifact_paths_by_pair[pair_fs] = paths
        return paths

    @staticmethod
    def _append_jsonl(path: str, payload: Dict[str, object]) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")

    def _record_order_lifecycle_event(
        self,
        *,
        symbol: str,
        event_type: str,
        side: Optional[str] = None,
        price: Optional[float] = None,
        qty_base: Optional[float] = None,
        level_index: Optional[int] = None,
        order_id: Optional[str] = None,
        reason: Optional[str] = None,
        phase: Optional[str] = None,
    ) -> None:
        if not self._execution_cost_feedback_enabled:
            return
        payload: Dict[str, object] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pair": str(symbol),
            "event_type": str(event_type),
            "mode": str(self.mode),
            "side": str(side) if side is not None else None,
            "price": float(price) if price is not None else None,
            "qty_base": float(qty_base) if qty_base is not None else None,
            "level_index": int(level_index) if level_index is not None else None,
            "order_id": str(order_id) if order_id is not None else None,
            "reason": str(reason) if reason is not None else None,
            "phase": str(phase) if phase is not None else None,
        }
        paths = self._execution_cost_paths(symbol)
        self._append_jsonl(paths["orders_lifecycle"], payload)
        step = self._execution_cost_step_metrics
        evt = str(event_type).lower()
        if evt in ("placed", "seeded", "replenished"):
            step["orders_placed"] = int(step.get("orders_placed", 0) + 1)
        elif evt in ("rejected", "post_only_reject"):
            step["orders_rejected"] = int(step.get("orders_rejected", 0) + 1)
        elif evt == "canceled":
            step["orders_canceled"] = int(step.get("orders_canceled", 0) + 1)
        elif evt == "repriced":
            step["orders_repriced"] = int(step.get("orders_repriced", 0) + 1)
        elif evt == "missed_fill":
            step["missed_fill_opportunities"] = int(step.get("missed_fill_opportunities", 0) + 1)

    def _record_fill_lifecycle_event(
        self,
        *,
        symbol: str,
        side: str,
        price: float,
        qty_base: float,
        level_index: int,
        order_id: Optional[str],
        ref_price: Optional[float],
        reason: str,
    ) -> None:
        if not self._execution_cost_feedback_enabled:
            return
        spread_pct = None
        adverse_pct = None
        if ref_price is not None and float(ref_price) > 0:
            spread_pct = abs(float(price) - float(ref_price)) / float(ref_price)
            if str(side).lower() == "buy":
                adverse_pct = max(float(ref_price) - float(price), 0.0) / float(ref_price)
            else:
                adverse_pct = max(float(price) - float(ref_price), 0.0) / float(ref_price)
        payload: Dict[str, object] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pair": str(symbol),
            "event_type": "fill",
            "mode": str(self.mode),
            "side": str(side),
            "price": float(price),
            "qty_base": float(qty_base),
            "level_index": int(level_index),
            "order_id": str(order_id) if order_id is not None else None,
            "ref_price": float(ref_price) if ref_price is not None else None,
            "realized_spread_pct": spread_pct,
            "adverse_selection_pct": adverse_pct,
            "reason": str(reason),
        }
        paths = self._execution_cost_paths(symbol)
        self._append_jsonl(paths["fills_lifecycle"], payload)
        step = self._execution_cost_step_metrics
        step["fills"] = int(step.get("fills", 0) + 1)
        if spread_pct is not None:
            spreads = step.get("fill_spread_samples", [])
            spreads.append(float(spread_pct))
            step["fill_spread_samples"] = spreads
        if adverse_pct is not None:
            advs = step.get("fill_adverse_selection_samples", [])
            advs.append(float(adverse_pct))
            step["fill_adverse_selection_samples"] = advs

    def _publish_execution_cost_artifact(
        self,
        *,
        plan: Dict,
        symbol: str,
        ref_price: Optional[float],
        prev_mark_price: Optional[float],
    ) -> None:
        if not self._execution_cost_feedback_enabled:
            self._execution_cost_last_artifact = None
            return

        step = self._execution_cost_step_metrics
        spreads = [float(x) for x in (step.get("fill_spread_samples") or [])]
        adverse = [float(x) for x in (step.get("fill_adverse_selection_samples") or [])]
        spread_sample = float(np.mean(spreads)) if spreads else _safe_float(
            (plan.get("runtime_state", {}) or {}).get("spread_pct"),
            default=_safe_float((plan.get("grid", {}) or {}).get("est_spread_pct"), default=0.0),
        )
        adverse_sample = float(np.mean(adverse)) if adverse else None
        if adverse_sample is None and prev_mark_price is not None and ref_price not in (None, 0):
            adverse_sample = abs(float(ref_price) - float(prev_mark_price)) / float(ref_price)

        placed = int(step.get("orders_placed", 0))
        rejected = int(step.get("orders_rejected", 0))
        fills = int(step.get("fills", 0))
        missed = int(step.get("missed_fill_opportunities", 0))
        retry_reject_rate = float(rejected / max(placed + rejected, 1))
        missed_fill_rate = float(missed / max(missed + fills, 1))

        sample = self._execution_cost_calibrator.observe(
            symbol,
            spread_pct=spread_sample,
            adverse_selection_pct=adverse_sample,
            retry_reject_rate=retry_reject_rate,
            missed_fill_rate=missed_fill_rate,
            retry_penalty_pct=float(self._execution_cost_retry_penalty_pct),
            missed_fill_penalty_pct=float(self._execution_cost_missed_fill_penalty_pct),
            recommended_floor_pct=None,
            sample_source="lifecycle",
            market_state_bucket=str(plan.get("mode") or "unknown"),
        )
        snapshot = self._execution_cost_calibrator.snapshot(
            symbol,
            percentile=float(self._execution_cost_percentile),
            min_samples=int(self._execution_cost_min_samples),
            stale_bars=int(self._execution_cost_stale_steps),
        )
        cost_model_source = "empirical"
        if bool(snapshot.get("stale", True)):
            cost_model_source = "static"
        total_pct = _safe_float(snapshot.get("total_cost_pct_percentile"), default=None)
        if total_pct is None:
            total_pct = _safe_float(sample.get("total_pct"), default=0.0)
        artifact = {
            "schema_version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "pair": str(symbol),
            "window": int(self._execution_cost_window),
            "sample_count": int(snapshot.get("sample_count", 0)),
            "cost_model_source": str(cost_model_source),
            "percentile": float(self._execution_cost_percentile),
            "realized_spread_pct": float(
                _safe_float(snapshot.get("spread_pct_percentile"), default=spread_sample or 0.0) or 0.0
            ),
            "adverse_selection_pct": float(
                _safe_float(snapshot.get("adverse_selection_pct_percentile"), default=adverse_sample or 0.0) or 0.0
            ),
            "post_only_retry_reject_rate": float(
                _safe_float(snapshot.get("retry_reject_rate_percentile"), default=retry_reject_rate) or 0.0
            ),
            "missed_fill_opportunity_rate": float(
                _safe_float(snapshot.get("missed_fill_rate_percentile"), default=missed_fill_rate) or 0.0
            ),
            "recommended_cost_floor_bps": float(max(total_pct or 0.0, 0.0) * 10_000.0),
            "notes": {
                "orders_placed_step": int(placed),
                "orders_rejected_step": int(rejected),
                "orders_canceled_step": int(step.get("orders_canceled", 0)),
                "orders_repriced_step": int(step.get("orders_repriced", 0)),
                "fills_step": int(fills),
                "missed_fill_opportunities_step": int(missed),
                "capacity_replenish_skipped_total": int(self._capacity_replenish_skipped_total),
                "capacity_rung_cap_applied_total": int(self._capacity_rung_cap_applied_total),
            },
        }
        schema_errors = validate_schema(artifact, "execution_cost_calibration.schema.json")
        if schema_errors:
            self._append_runtime_warning("WARN_COST_ARTIFACT_SCHEMA_INVALID")
            log_event(
                "warning",
                "execution_cost_artifact_schema_invalid",
                errors=schema_errors[:3],
                pair=symbol,
            )
            return

        paths = self._execution_cost_paths(symbol)
        Path(paths["orders_lifecycle"]).touch(exist_ok=True)
        Path(paths["fills_lifecycle"]).touch(exist_ok=True)
        write_json(paths["artifact_latest"], artifact)
        sample_count = int(artifact.get("sample_count", 0))
        prev_written = int(self._execution_cost_samples_written_by_pair.get(symbol, -1))
        if sample_count > prev_written:
            ts_safe = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            archive_path = str(
                Path(paths["artifact_archive_dir"]) / f"execution_cost_calibration.{ts_safe}.json"
            )
            write_json(archive_path, artifact)
            self._execution_cost_samples_written_by_pair[symbol] = sample_count
        self._execution_cost_last_artifact = artifact

    def _order_match_tolerant(
        self,
        desired: RestingOrder,
        live: Dict,
    ) -> bool:
        if str(live.get("side", "")).lower() != str(desired.side).lower():
            return False
        live_px = _safe_float(live.get("price"), default=None)
        live_qty = _safe_float(live.get("amount"), default=None)
        if live_px is None or live_qty is None:
            return False
        if live_px <= 0 or live_qty <= 0:
            return False

        tick_tol = 0.0
        if self._reconcile_price_tol_ticks > 0:
            tick_tol = float(self._tick_for_price(desired.price) * self._reconcile_price_tol_ticks)
        frac_tol = abs(float(desired.price)) * float(self._reconcile_price_tol_frac)
        px_tol = max(tick_tol, frac_tol)
        if abs(float(desired.price) - float(live_px)) > px_tol:
            return False

        qty_tol = max(abs(float(desired.qty_base)) * float(self._reconcile_qty_tol_frac), 1e-12)
        if abs(float(desired.qty_base) - float(live_qty)) > qty_tol:
            return False
        return True

    # ---------- ccxt call wrapper ----------
    def _ccxt_call(self, fn, *args, **kwargs):
        if self.exchange is None:
            return None
        now_ts = float(time.time())
        if now_ts < self._ccxt_backoff_until_ts:
            sleep_s = min(self._ccxt_backoff_until_ts - now_ts, 1.0)
            if sleep_s > 0:
                time.sleep(sleep_s)
        last_err = None
        for _ in range(max(self.ccxt_retries, 1)):
            try:
                res = fn(*args, **kwargs)
                self._ccxt_error_streak = 0
                self._ccxt_backoff_until_ts = 0.0
                self._last_ccxt_error = None
                return res
            except Exception as e:
                last_err = e
                self._last_ccxt_error = str(e)
                self._ccxt_error_streak = int(self._ccxt_error_streak + 1)
                base_ms = max(int(self._ccxt_backoff_base_ms), 0)
                max_ms = max(int(self._ccxt_backoff_max_ms), base_ms)
                backoff_ms = base_ms * (2 ** max(self._ccxt_error_streak - 1, 0))
                backoff_ms = min(backoff_ms, max_ms)
                self._ccxt_backoff_until_ts = max(
                    self._ccxt_backoff_until_ts,
                    float(time.time()) + (float(backoff_ms) / 1000.0),
                )
                time.sleep(0.2)
        if last_err:
            raise last_err
        return None

    # ---------- build ladder ----------
    def _desired_initial_ladder(
        self,
        levels: np.ndarray,
        ref_price: float,
        limits: Dict,
        grid_budget_pct: float,
        rung_cap_per_side: Optional[int] = None,
        rung_weights: Optional[List[float]] = None,
    ) -> List[RestingOrder]:
        """
        v1 initial ladder:
        - buys for all rungs <= ref_price
        - sells for all rungs > ref_price only if base_total > 0
        """
        buys: List[Tuple[int, float]] = []
        sells: List[Tuple[int, float]] = []

        for i, px in enumerate(levels):
            px = float(px)
            if px <= 0:
                continue
            if px <= ref_price:
                buys.append((i, px))
            else:
                if self.base_total > 0:
                    sells.append((i, px))

        side_cap = int(self.max_orders_per_side)
        if rung_cap_per_side is not None:
            side_cap = max(min(int(rung_cap_per_side), side_cap), 0)

        # cap per side
        if len(buys) > side_cap:
            buys = buys[-side_cap:]
        if len(sells) > side_cap:
            sells = sells[:side_cap]

        out: List[RestingOrder] = []
        fee = self.maker_fee_pct / 100.0
        quote_budget = max(self.quote_total * float(grid_budget_pct), 0.0)

        if buys and quote_budget > 0:
            side_w = _normalized_side_weights([i for i, _ in buys], rung_weights)
            for (i, px), w in zip(buys, side_w):
                quote_per = quote_budget * float(w)
                # reserve fee too -> cost = quote_per/(1+fee)
                cost = quote_per / (1.0 + fee) if (1.0 + fee) > 0 else quote_per
                qty = cost / px
                if qty <= 0:
                    continue
                if not passes_min_notional(limits, px, qty):
                    continue
                out.append(RestingOrder("buy", px, qty, i))

        if sells and self.base_total > 0:
            side_w = _normalized_side_weights([i for i, _ in sells], rung_weights)
            for (i, px), w in zip(sells, side_w):
                qty = self.base_total * float(w)
                if qty <= 0:
                    continue
                if not passes_min_notional(limits, px, qty):
                    continue
                out.append(RestingOrder("sell", px, qty, i))

        return out

    # ---------- place/cancel (ccxt) ----------
    def _ccxt_fetch_open_orders(self, symbol: str) -> List[Dict]:
        if self.exchange is None:
            return []
        try:
            return self._ccxt_call(self.exchange.fetch_open_orders, symbol) or []
        except Exception:
            return []

    def _ccxt_cancel_order(self, order_id: str, symbol: str) -> None:
        if self.exchange is None:
            return
        try:
            self._ccxt_call(self.exchange.cancel_order, order_id, symbol)
        except Exception:
            pass

    def _ccxt_place_limit(self, side: str, symbol: str, qty: float, price: float, limits: Dict) -> Optional[str]:
        if self.exchange is None:
            return None

        px = quantize_price(self.exchange, symbol, price)
        qt = quantize_amount(self.exchange, symbol, qty)

        if qt <= 0 or px <= 0:
            return None
        if not passes_min_notional(limits, px, qt):
            return None

        params = {}
        if self.post_only:
            params["postOnly"] = True

        max_attempts = max(
            int(self._post_only_place_attempts if self.post_only else self.ccxt_retries),
            1,
        )
        curr_px = float(px)
        last_err: Optional[str] = None

        for attempt in range(max_attempts):
            curr_px = float(quantize_price(self.exchange, symbol, curr_px))
            if curr_px <= 0:
                return None
            if not passes_min_notional(limits, curr_px, qt):
                return None

            try:
                if side == "buy":
                    res = self.exchange.create_limit_buy_order(symbol, qt, curr_px, params=params)
                else:
                    res = self.exchange.create_limit_sell_order(symbol, qt, curr_px, params=params)
                self._ccxt_error_streak = 0
                self._ccxt_backoff_until_ts = 0.0
                self._last_ccxt_error = None
                self._post_only_reject_streak = 0
                order_id = (res or {}).get("id")
                self._record_order_lifecycle_event(
                    symbol=symbol,
                    event_type="placed",
                    side=side,
                    price=curr_px,
                    qty_base=qt,
                    order_id=str(order_id) if order_id is not None else None,
                    reason="ccxt_create_limit",
                )
                return order_id
            except Exception as exc:
                last_err = str(exc)
                self._last_ccxt_error = str(exc)
                self._ccxt_error_streak = int(self._ccxt_error_streak + 1)
                base_ms = max(int(self._ccxt_backoff_base_ms), 0)
                max_ms = max(int(self._ccxt_backoff_max_ms), base_ms)
                err_backoff_ms = min(
                    base_ms * (2 ** max(self._ccxt_error_streak - 1, 0)),
                    max_ms,
                )
                self._ccxt_backoff_until_ts = max(
                    self._ccxt_backoff_until_ts,
                    float(time.time()) + (float(err_backoff_ms) / 1000.0),
                )
                is_post_only_reject = bool(self.post_only and self._is_post_only_reject_error(exc))
                if not is_post_only_reject:
                    # Unknown venue error; let retry loop handle bounded retries.
                    if attempt < (max_attempts - 1):
                        time.sleep(0.1)
                        continue
                    break

                self._register_post_only_reject(str(exc))
                self._append_runtime_exec_event("EXEC_POST_ONLY_RETRY")
                self._record_order_lifecycle_event(
                    symbol=symbol,
                    event_type="post_only_reject",
                    side=side,
                    price=curr_px,
                    qty_base=qt,
                    reason=str(exc),
                )
                if attempt >= (max_attempts - 1):
                    break

                if self._post_only_reprice_ticks > 0:
                    curr_px = self._reprice_post_only_price(side, curr_px, attempt + 1)
                    self._post_only_reprice_count_total = int(self._post_only_reprice_count_total + 1)
                    self._append_runtime_exec_event("EXEC_POST_ONLY_FALLBACK_REPRICE")

                backoff_ms = self._post_only_backoff_ms * (2 ** attempt)
                backoff_ms = min(backoff_ms, self._post_only_backoff_max_ms)
                if backoff_ms > 0:
                    time.sleep(float(backoff_ms) / 1000.0)

        if last_err is not None:
            self._record_order_lifecycle_event(
                symbol=symbol,
                event_type="rejected",
                side=side,
                price=curr_px,
                qty_base=qt,
                reason=last_err,
            )
            log_event(
                "warning",
                "place_limit_failed",
                side=side,
                symbol=symbol,
                qty=qt,
                price=curr_px,
                attempts=max_attempts,
                error=last_err,
            )
        return None

    def _ccxt_reconcile_set(self, desired: List[RestingOrder], symbol: str, limits: Dict) -> None:
        """
        Diff reconcile:
        - cancel stale orders not in desired
        - place missing desired orders
        """
        open_live = self._ccxt_fetch_open_orders(symbol)
        live_rows: List[Dict[str, object]] = []
        for o in open_live:
            try:
                oid = str(o.get("id") or "").strip()
                if not oid:
                    continue
                side = str(o.get("side") or "").lower().strip()
                if side not in ("buy", "sell"):
                    continue
                price = float(o.get("price"))
                amount = float(o.get("amount") or o.get("remaining") or 0.0)
                if price <= 0 or amount <= 0:
                    continue
                live_rows.append(
                    {
                        "order_id": oid,
                        "side": side,
                        "price": float(price),
                        "amount": float(amount),
                    }
                )
            except Exception:
                continue

        unmatched_live = set(range(len(live_rows)))
        matched_live_by_desired_idx: Dict[int, int] = {}

        for idx, ro in enumerate(desired):
            best_j: Optional[int] = None
            best_score: Optional[float] = None
            for j in list(unmatched_live):
                live = live_rows[j]
                if not self._order_match_tolerant(ro, live):
                    continue
                px_den = max(abs(float(ro.price)), 1e-12)
                qty_den = max(abs(float(ro.qty_base)), 1e-12)
                score = (
                    abs(float(ro.price) - float(live["price"])) / px_den
                    + abs(float(ro.qty_base) - float(live["amount"])) / qty_den
                )
                if best_score is None or score < best_score:
                    best_score = score
                    best_j = j
            if best_j is not None:
                matched_live_by_desired_idx[idx] = int(best_j)
                unmatched_live.discard(int(best_j))

        action_budget = max(int(self._reconcile_max_actions_per_tick), 1)
        cancel_count = 0
        place_count = 0
        kept_count = 0
        skipped_due_cap = False

        # Cancel stale live orders first to reduce accidental over-allocation risk.
        for j in sorted(unmatched_live):
            if action_budget <= 0:
                skipped_due_cap = True
                break
            oid = str(live_rows[j].get("order_id") or "").strip()
            if not oid:
                continue
            side = str(live_rows[j].get("side") or "")
            price = _safe_float(live_rows[j].get("price"), default=None)
            qty = _safe_float(live_rows[j].get("amount"), default=None)
            self._ccxt_cancel_order(oid, symbol)
            self._record_order_lifecycle_event(
                symbol=symbol,
                event_type="canceled",
                side=side,
                price=price,
                qty_base=qty,
                order_id=oid,
                reason="reconcile_stale",
                phase="reconcile",
            )
            action_budget -= 1
            cancel_count += 1

        new_orders: List[RestingOrder] = []
        for idx, ro in enumerate(desired):
            if idx in matched_live_by_desired_idx:
                matched_live = live_rows[matched_live_by_desired_idx[idx]]
                ro.order_id = str(matched_live.get("order_id") or "")
                ro.status = "open"
                kept_count += 1
                new_orders.append(ro)
                continue

            if action_budget <= 0:
                ro.order_id = None
                ro.status = "rejected"
                skipped_due_cap = True
                self._record_order_lifecycle_event(
                    symbol=symbol,
                    event_type="rejected",
                    side=ro.side,
                    price=ro.price,
                    qty_base=ro.qty_base,
                    level_index=ro.level_index,
                    reason="reconcile_action_cap",
                    phase="reconcile",
                )
                new_orders.append(ro)
                continue

            oid = self._ccxt_place_limit(ro.side, symbol, ro.qty_base, ro.price, limits)
            ro.order_id = oid
            ro.status = "open" if oid else "rejected"
            place_count += 1
            action_budget -= 1
            new_orders.append(ro)

        self._orders = new_orders
        self._last_reconcile_summary = {
            "live_open_orders": int(len(live_rows)),
            "desired_orders": int(len(desired)),
            "kept_orders": int(kept_count),
            "cancelled_orders": int(cancel_count),
            "placed_orders": int(place_count),
        }
        self._last_reconcile_skipped_due_cap = bool(skipped_due_cap)

        if cancel_count > 0 or place_count > 0:
            self._append_runtime_exec_event("EXEC_ORDER_CANCEL_REPLACE_APPLIED")
        if skipped_due_cap:
            log_event(
                "warning",
                "reconcile_action_cap_reached",
                action_cap=self._reconcile_max_actions_per_tick,
                reconcile_summary=self._last_reconcile_summary,
            )

    # ---------- fill ingestion ----------
    def _levels_for_index(self, levels: np.ndarray, idx: int) -> Optional[float]:
        if idx < 0 or idx >= len(levels):
            return None
        return float(levels[idx])

    def _next_fill_bar_index(self, plan: Dict) -> int:
        runtime_state = plan.get("runtime_state") or {}
        clock_ts = runtime_state.get("clock_ts")
        if clock_ts is None:
            clock_ts = plan.get("candle_ts")
        clock_ts_int = _safe_float(clock_ts, default=None)
        if clock_ts_int is not None:
            clock_ts_value = int(clock_ts_int)
            if self._fill_guard_last_clock_ts != clock_ts_value:
                self._fill_guard_last_clock_ts = clock_ts_value
                self._fill_guard_bar_seq = int(self._fill_guard_bar_seq + 1)
            return int(max(self._fill_guard_bar_seq, 1))
        self._fill_guard_bar_seq = int(self._fill_guard_bar_seq + 1)
        return int(self._fill_guard_bar_seq)

    def _extract_exit_levels(self, plan: Dict) -> Tuple[Optional[float], Optional[float]]:
        """
        Read TP/SL levels from plan, supporting both new and legacy locations.
        """
        tp = None
        sl = None
        try:
            ex = plan.get("exit", {}) or {}
            tp = _safe_float(ex.get("tp_price"), default=None)
            sl = _safe_float(ex.get("sl_price"), default=None)
        except Exception:
            tp = None
            sl = None

        if tp is None or sl is None:
            try:
                rk = plan.get("risk", {}) or {}
                if tp is None:
                    tp = _safe_float(rk.get("tp_price"), default=None)
                if sl is None:
                    sl = _safe_float(rk.get("sl_price"), default=None)
            except Exception:
                pass

        return tp, sl

    def _find_order_by_id(self, oid: str) -> Optional[RestingOrder]:
        for o in self._orders:
            if o.order_id and str(o.order_id) == str(oid):
                return o
        return None

    def _ingest_trades_and_replenish(
        self,
        symbol: str,
        levels: np.ndarray,
        limits: Dict,
        *,
        fill_bar_index: int,
        ref_price: Optional[float],
        capacity_state: Dict[str, object],
    ) -> None:
        """
        Fetch user trades since last_trade_ms and:
        - match them to our tracked orders (by trade['order'])
        - update filled qty
        - place opposite rung order for the FILLED PORTION
        """
        if self.exchange is None:
            return

        now_ms = int(time.time() * 1000)
        since = self._last_trade_ms
        if since is None:
            since = now_ms - self._trade_lookback_ms
        else:
            # small overlap
            since = max(since - 5_000, 0)

        trades = []
        try:
            trades = self._ccxt_call(self.exchange.fetch_my_trades, symbol, since) or []
        except Exception:
            return

        max_seen_ms = self._last_trade_ms or since

        for tr in trades:
            tid = str(tr.get("id") or "")
            if not tid or tid in self._seen_trade_ids:
                # still update max time
                tms = int(tr.get("timestamp") or 0)
                if tms > max_seen_ms:
                    max_seen_ms = tms
                continue

            self._seen_trade_ids.add(tid)
            tms = int(tr.get("timestamp") or 0)
            if tms > max_seen_ms:
                max_seen_ms = tms

            oid = str(tr.get("order") or "")
            side = str(tr.get("side") or "").lower()
            amount = float(tr.get("amount") or 0.0)  # base filled
            price = float(tr.get("price") or 0.0)

            if amount <= 0 or price <= 0 or side not in ("buy", "sell"):
                continue

            # try match to our tracked order by order_id
            ro = self._find_order_by_id(oid) if oid else None

            # If we cannot match (manual fill / older state), we skip replenishment but balances still refresh elsewhere.
            if ro is None:
                continue

            # update filled amount on that order
            ro.filled_base += amount
            remaining = max(ro.qty_base - ro.filled_base, 0.0)

            # if fully filled (or effectively)
            fully_filled = remaining <= 0.0 or remaining < 1e-12

            # Place opposite rung for the filled portion ONLY
            filled_qty = amount
            if filled_qty > 0:
                if self._fill_guard.allow(ro.side, ro.level_index, fill_bar_index):
                    self._record_fill_lifecycle_event(
                        symbol=symbol,
                        side=side,
                        price=price,
                        qty_base=filled_qty,
                        level_index=ro.level_index,
                        order_id=oid if oid else ro.order_id,
                        ref_price=ref_price,
                        reason="trade_fill",
                    )
                    action_attempted = False
                    replenish_side = "sell" if ro.side == "buy" else "buy"
                    rung_cap = max(_safe_int(capacity_state.get("applied_rung_cap"), self.max_orders_per_side), 0)
                    delay_replenish = bool(capacity_state.get("delay_replenishment", False))
                    active_on_side = int(
                        len(
                            [
                                x
                                for x in self._orders
                                if x.status in ("open", "partial")
                                and str(x.side).lower() == replenish_side
                            ]
                        )
                    )
                    if delay_replenish:
                        self._capacity_replenish_skipped_total = int(self._capacity_replenish_skipped_total + 1)
                        self._record_order_lifecycle_event(
                            symbol=symbol,
                            event_type="missed_fill",
                            side=replenish_side,
                            qty_base=filled_qty,
                            reason="capacity_delay_replenishment",
                            phase="replenish",
                        )
                        continue
                    if rung_cap > 0 and active_on_side >= rung_cap:
                        self._capacity_replenish_skipped_total = int(self._capacity_replenish_skipped_total + 1)
                        self._record_order_lifecycle_event(
                            symbol=symbol,
                            event_type="missed_fill",
                            side=replenish_side,
                            qty_base=filled_qty,
                            reason="capacity_rung_cap_reached",
                            phase="replenish",
                        )
                        continue
                    if ro.side == "buy":
                        next_idx = ro.level_index + 1
                        px = self._levels_for_index(levels, next_idx)
                        if px is not None:
                            new_px = float(quantize_price(self.exchange, symbol, px))
                            new_qty = float(quantize_amount(self.exchange, symbol, filled_qty))
                            if new_qty > 0 and passes_min_notional(limits, new_px, new_qty):
                                action_attempted = True
                                new_oid = self._ccxt_place_limit("sell", symbol, new_qty, new_px, limits)
                                self._orders.append(RestingOrder("sell", new_px, new_qty, next_idx, order_id=new_oid, status="open" if new_oid else "rejected"))
                                if new_oid is not None:
                                    self._record_order_lifecycle_event(
                                        symbol=symbol,
                                        event_type="replenished",
                                        side="sell",
                                        price=new_px,
                                        qty_base=new_qty,
                                        level_index=next_idx,
                                        order_id=str(new_oid),
                                        reason="replace_on_fill",
                                        phase="replenish",
                                    )
                    else:
                        next_idx = ro.level_index - 1
                        px = self._levels_for_index(levels, next_idx)
                        if px is not None:
                            new_px = float(quantize_price(self.exchange, symbol, px))
                            new_qty = float(quantize_amount(self.exchange, symbol, filled_qty))
                            if new_qty > 0 and passes_min_notional(limits, new_px, new_qty):
                                action_attempted = True
                                new_oid = self._ccxt_place_limit("buy", symbol, new_qty, new_px, limits)
                                self._orders.append(RestingOrder("buy", new_px, new_qty, next_idx, order_id=new_oid, status="open" if new_oid else "rejected"))
                                if new_oid is not None:
                                    self._record_order_lifecycle_event(
                                        symbol=symbol,
                                        event_type="replenished",
                                        side="buy",
                                        price=new_px,
                                        qty_base=new_qty,
                                        level_index=next_idx,
                                        order_id=str(new_oid),
                                        reason="replace_on_fill",
                                        phase="replenish",
                                    )
                    if action_attempted:
                        self._fill_guard.mark(ro.side, ro.level_index, fill_bar_index)

            if fully_filled:
                ro.status = "filled"
            else:
                ro.status = "partial"

        self._last_trade_ms = max_seen_ms

        # Cleanup: drop fully filled orders from our local list (optional but keeps state tidy)
        self._orders = [o for o in self._orders if o.status not in ("filled", "canceled")]

        # Prevent memory blow-up from seen_trade_ids
        if len(self._seen_trade_ids) > 50_000:
            # keep last ~10k by clearing; balance refresh will keep totals correct
            self._seen_trade_ids = set()

    # ---------- main tick ----------
    def step(self, plan: Dict) -> None:
        self._reset_runtime_diagnostics()
        intake_ok, _ = self._validate_plan_intake(plan)
        if not intake_ok:
            self._write_rejected_plan_state(plan if isinstance(plan, dict) else {})
            return

        self._append_runtime_exec_event("EXEC_PLAN_APPLIED")
        self._apply_execution_hardening_config(plan)

        raw_action = str(plan.get("action", "HOLD")).upper()
        if raw_action == "REBUILD":
            raw_action = "START"
        if raw_action not in ("START", "HOLD", "STOP"):
            raw_action = "HOLD"
        ex_name = str(plan.get("exchange", "unknown"))
        symbol = plan_pair(plan) or str(plan.get("symbol", "UNKNOWN/UNKNOWN"))
        self.symbol = symbol

        box_low = float(plan["range"]["low"])
        box_high = float(plan["range"]["high"])
        n_levels = int(plan["grid"]["n_levels"])
        step = float(plan["grid"]["step_price"])
        fill_cfg = (plan.get("grid", {}) or {}).get("fill_detection", {}) or {}
        self._fill_confirmation_mode = str(fill_cfg.get("fill_confirmation_mode", "Touch"))
        self._fill_no_repeat_lsi_guard = bool(fill_cfg.get("no_repeat_lsi_guard", True))
        self._fill_cooldown_bars = int(fill_cfg.get("cooldown_bars", 1) or 1)
        self._fill_guard.configure(
            cooldown_bars=self._fill_cooldown_bars,
            no_repeat_lsi_guard=self._fill_no_repeat_lsi_guard,
        )
        fill_bar_index = self._next_fill_bar_index(plan)
        self._tick_size = _safe_float((plan.get("grid", {}) or {}).get("tick_size"), default=None)
        rung_weights = _extract_rung_weights(plan, n_levels)

        levels = build_levels(box_low, box_high, n_levels, tick_size=self._tick_size)
        level_error = _levels_validation_error(levels, n_levels + 1)
        if level_error:
            self._append_runtime_warning("BLOCK_N_LEVELS_INVALID")
            raise ValueError(f"invalid_levels:{level_error}")

        limits = market_limits(self.exchange, symbol)

        # Determine mark/reference price for initial ladder and TP/SL checks.
        ref_price = _safe_float((plan.get("price_ref", {}) or {}).get("close"), default=None)
        if ref_price is None:
            ref_price = (box_low + box_high) / 2.0
        if self.exchange is not None:
            try:
                t = self._ccxt_call(self.exchange.fetch_ticker, symbol) or {}
                ref_price = float(t.get("last") or t.get("close") or ref_price)
            except Exception:
                pass

        prev_mark_price = self._last_mark_price
        tp_price, sl_price = self._extract_exit_levels(plan)
        self._last_mark_price = _safe_float(ref_price, default=None)
        self._last_tp_price = _safe_float(tp_price, default=None)
        self._last_sl_price = _safe_float(sl_price, default=None)
        self._last_stop_reason = None

        if raw_action != "STOP":
            if tp_price is not None and ref_price is not None and ref_price >= tp_price:
                raw_action = "STOP"
                self._last_stop_reason = "tp_hit"
            elif sl_price is not None and ref_price is not None and ref_price <= sl_price:
                raw_action = "STOP"
                self._last_stop_reason = "sl_hit"

        grid_budget_pct = float(plan.get("capital_policy", {}).get("grid_budget_pct", 1.0))
        grid_budget_pct = float(np.clip(grid_budget_pct, 0.0, 1.0))
        capacity_state = self._compute_capacity_state(
            plan,
            n_levels=n_levels,
            grid_budget_pct=grid_budget_pct,
        )

        # Refresh balances (ccxt)
        if self.mode == "ccxt":
            self._sync_balance_ccxt()
            # Ingest fills and replenish before we make plan-adjust decisions
            if raw_action != "STOP":
                self._ingest_trades_and_replenish(
                    symbol,
                    levels,
                    limits,
                    fill_bar_index=fill_bar_index,
                    ref_price=ref_price,
                    capacity_state=capacity_state,
                )

        rebuild = False
        soft_adjust = False
        if self._prev_plan is None:
            rebuild = True
        else:
            sig_prev = plan_signature(self._prev_plan)
            sig_new = plan_signature(plan)
            if sig_prev != sig_new:
                if soft_adjust_ok(self._prev_plan, plan):
                    soft_adjust = True
                else:
                    rebuild = True

        active_orders = [o for o in self._orders if o.status in ("open", "partial")]
        has_active_orders = len(active_orders) > 0
        plan_sig = plan_signature(plan)
        self._runtime_confirm["runtime"] = {
            "post_only_burst": self._post_only_burst_status(),
        }

        effective_action = raw_action
        suppression_reason: Optional[str] = None

        if raw_action == "START" and has_active_orders and (not rebuild) and (not soft_adjust):
            # START is a seed signal only; when a ladder is already live and unchanged, manage as HOLD.
            effective_action = "HOLD"
            suppression_reason = "duplicate_start_manage_existing"
        elif raw_action == "STOP":
            has_flatten_work = self.close_on_stop and self.base_total > 0.0
            stop_sig = _action_signature("STOP", plan_sig, self._last_stop_reason or "plan_stop")
            if (not has_active_orders) and (not has_flatten_work):
                if self._last_effective_action_signature == stop_sig:
                    # Duplicate STOP on already-cleared state: suppress churn.
                    effective_action = "HOLD"
                    suppression_reason = "duplicate_stop_already_cleared"

        if effective_action == "START":
            if not bool(capacity_state.get("capacity_ok", True)):
                effective_action = "HOLD"
                suppression_reason = "capacity_thin_block"
                self._append_runtime_exec_event("BLOCK_CAPACITY_THIN")
                log_event(
                    "warning",
                    "capacity_blocked_start",
                    capacity_state=capacity_state,
                )

        if effective_action == "START":
            confirm_phase = "rebuild" if (rebuild and has_active_orders) else "entry"
            confirm_res = self._run_confirm_hook(
                confirm_phase,
                plan,
                ref_price,
                prev_mark_price,
            )
            self._runtime_confirm[confirm_phase] = confirm_res
            if not bool(confirm_res.get("ok")):
                effective_action = "HOLD"
                if confirm_phase == "rebuild":
                    suppression_reason = "confirm_rebuild_failed"
                    self._append_runtime_exec_event("EXEC_CONFIRM_REBUILD_FAILED")
                else:
                    suppression_reason = "confirm_start_failed"
                    self._append_runtime_exec_event("EXEC_CONFIRM_START_FAILED")
                log_event(
                    "warning",
                    "confirm_hook_blocked_start",
                    confirm_phase=confirm_phase,
                    reasons=confirm_res.get("reasons"),
                    metrics=confirm_res.get("metrics"),
                )

        if effective_action == "STOP":
            confirm_exit = self._run_confirm_hook(
                "exit",
                plan,
                ref_price,
                prev_mark_price,
            )
            self._runtime_confirm["exit"] = confirm_exit
            if not bool(confirm_exit.get("ok")):
                self._last_stop_reason = "STOP_EXEC_CONFIRM_EXIT_FAILSAFE"
                self._append_runtime_exec_event("EXEC_CONFIRM_EXIT_FAILSAFE")
                log_event(
                    "warning",
                    "confirm_hook_exit_failsafe",
                    reasons=confirm_exit.get("reasons"),
                    metrics=confirm_exit.get("metrics"),
                )

        self._last_raw_action = raw_action
        self._last_effective_action = effective_action
        self._last_action_suppression_reason = suppression_reason

        # STOP: cancel all open orders (and optionally close)
        if effective_action == "STOP":
            if self._last_stop_reason is None:
                self._last_stop_reason = "plan_stop"

            if self.mode == "ccxt" and self.exchange is not None:
                for o in self._ccxt_fetch_open_orders(symbol):
                    oid = str(o.get("id") or "")
                    if oid:
                        self._ccxt_cancel_order(oid, symbol)
                if self.close_on_stop:
                    # minimal / optional; you can keep OFF
                    try:
                        base_ccy, quote_ccy = symbol.split("/")
                        bal = self._ccxt_call(self.exchange.fetch_balance) or {}
                        base = bal.get(base_ccy, {}) or {}
                        base_free = _safe_float(base.get("free"), default=0.0) or 0.0
                        qty = float(quantize_amount(self.exchange, symbol, base_free))
                        if qty > 0:
                            self._ccxt_call(self.exchange.create_market_sell_order, symbol, qty)
                    except Exception:
                        pass
            elif self.mode == "paper" and self.close_on_stop:
                # Optional paper flattening for STOP parity with ccxt close_on_stop.
                try:
                    px = float(ref_price)
                    if px > 0 and self.base_total > 0:
                        fee = self.maker_fee_pct / 100.0
                        proceeds = self.base_total * px
                        self.quote_total += proceeds * (1.0 - fee)
                        self.base_total = 0.0
                except Exception:
                    pass

            self._orders = []
            self._record_applied_plan(plan)
            self._publish_execution_cost_artifact(
                plan=plan,
                symbol=symbol,
                ref_price=ref_price,
                prev_mark_price=prev_mark_price,
            )
            self._write_state(plan, ex_name, symbol, step, n_levels, box_low, box_high)
            self._prev_plan = plan
            self._last_effective_action_signature = _action_signature(
                "STOP", plan_sig, self._last_stop_reason or "plan_stop"
            )
            return

        # HOLD: manage only existing ladder, never seed from empty.
        if effective_action == "HOLD":
            if not has_active_orders:
                self._record_applied_plan(plan)
                self._publish_execution_cost_artifact(
                    plan=plan,
                    symbol=symbol,
                    ref_price=ref_price,
                    prev_mark_price=prev_mark_price,
                )
                self._write_state(plan, ex_name, symbol, step, n_levels, box_low, box_high)
                self._prev_plan = plan
                self._last_effective_action_signature = _action_signature("HOLD", plan_sig)
                return

            # Reprice existing orders when plan drift is soft-adjust eligible.
            if soft_adjust:
                for o in self._orders:
                    px = self._levels_for_index(levels, o.level_index)
                    if px is None:
                        continue
                    old_px = float(o.price)
                    if self.exchange is not None:
                        px = float(quantize_price(self.exchange, symbol, px))
                    o.price = float(px)
                    if abs(float(old_px) - float(o.price)) > 1e-12:
                        self._record_order_lifecycle_event(
                            symbol=symbol,
                            event_type="repriced",
                            side=o.side,
                            price=o.price,
                            qty_base=o.qty_base,
                            level_index=o.level_index,
                            order_id=o.order_id,
                            phase="soft_adjust",
                        )

            desired = [o for o in self._orders if o.status in ("open", "partial")]
            desired = self._enforce_capacity_rung_cap(
                desired,
                rung_cap=_safe_int(
                    capacity_state.get("applied_rung_cap"),
                    self.max_orders_per_side,
                ),
                ref_price=float(ref_price),
                symbol=symbol,
            )

            # Keep live venue in sync without seeding new ladder.
            if self.mode == "ccxt":
                self._ccxt_reconcile_set(desired, symbol, limits)
            else:
                self._orders = desired

            self._record_applied_plan(plan)
            self._publish_execution_cost_artifact(
                plan=plan,
                symbol=symbol,
                ref_price=ref_price,
                prev_mark_price=prev_mark_price,
            )
            self._write_state(plan, ex_name, symbol, step, n_levels, box_low, box_high)
            self._prev_plan = plan
            self._last_effective_action_signature = _action_signature("HOLD", plan_sig)
            return

        # START: seed/rebuild/soft-adjust.
        if (not has_active_orders) or rebuild or self._prev_plan is None:
            desired = self._desired_initial_ladder(
                levels,
                ref_price,
                limits,
                grid_budget_pct,
                rung_cap_per_side=_safe_int(
                    capacity_state.get("applied_rung_cap"),
                    self.max_orders_per_side,
                ),
                rung_weights=rung_weights,
            )
            desired = self._enforce_capacity_rung_cap(
                desired,
                rung_cap=_safe_int(
                    capacity_state.get("applied_rung_cap"),
                    self.max_orders_per_side,
                ),
                ref_price=float(ref_price),
                symbol=symbol,
            )

            if self.exchange is not None:
                for ro in desired:
                    ro.price = float(quantize_price(self.exchange, symbol, ro.price))
                    ro.qty_base = float(quantize_amount(self.exchange, symbol, ro.qty_base))

            if self.mode == "paper":
                self._orders = desired
                for ro in desired:
                    self._record_order_lifecycle_event(
                        symbol=symbol,
                        event_type="seeded",
                        side=ro.side,
                        price=ro.price,
                        qty_base=ro.qty_base,
                        level_index=ro.level_index,
                        order_id=ro.order_id,
                        phase="seed",
                    )
            else:
                self._ccxt_reconcile_set(desired, symbol, limits)

        elif soft_adjust:
            for o in self._orders:
                px = self._levels_for_index(levels, o.level_index)
                if px is None:
                    continue
                old_px = float(o.price)
                if self.exchange is not None:
                    px = float(quantize_price(self.exchange, symbol, px))
                o.price = float(px)
                if abs(float(old_px) - float(o.price)) > 1e-12:
                    self._record_order_lifecycle_event(
                        symbol=symbol,
                        event_type="repriced",
                        side=o.side,
                        price=o.price,
                        qty_base=o.qty_base,
                        level_index=o.level_index,
                        order_id=o.order_id,
                        phase="soft_adjust",
                    )

            if self.mode == "ccxt":
                desired = [o for o in self._orders if o.status in ("open", "partial")]
                desired = self._enforce_capacity_rung_cap(
                    desired,
                    rung_cap=_safe_int(
                        capacity_state.get("applied_rung_cap"),
                        self.max_orders_per_side,
                    ),
                    ref_price=float(ref_price),
                    symbol=symbol,
                )
                self._ccxt_reconcile_set(desired, symbol, limits)
            else:
                desired = [o for o in self._orders if o.status in ("open", "partial")]
                self._orders = self._enforce_capacity_rung_cap(
                    desired,
                    rung_cap=_safe_int(
                        capacity_state.get("applied_rung_cap"),
                        self.max_orders_per_side,
                    ),
                    ref_price=float(ref_price),
                    symbol=symbol,
                )

        else:
            # START and no plan change: keep current set.
            pass

        self._record_applied_plan(plan)
        self._publish_execution_cost_artifact(
            plan=plan,
            symbol=symbol,
            ref_price=ref_price,
            prev_mark_price=prev_mark_price,
        )
        self._write_state(plan, ex_name, symbol, step, n_levels, box_low, box_high)
        self._prev_plan = plan
        self._last_effective_action_signature = _action_signature("START", plan_sig)

    def _executor_state_machine(self) -> str:
        has_active_orders = bool(any(o.status in ("open", "partial") for o in self._orders))
        effective = str(self._last_effective_action or "").upper()
        if effective == "STOP":
            return "stopping"
        if effective == "START":
            return "rebuilding" if self._prev_plan is not None else "running"
        if has_active_orders:
            return "running"
        return "idle"

    def _write_state(self, plan: Dict, exchange_name: str, symbol: str, step: float, n_levels: int, box_low: float, box_high: float) -> None:
        q_res, b_res = self._reserved_balances_intent()
        q_free, b_free = self._free_balances_intent()
        executor_state_machine = self._executor_state_machine()

        runtime = {
            "last_trade_ms": self._last_trade_ms,
            "seen_trade_ids": len(self._seen_trade_ids),
            "use_exchange_balance": self.use_exchange_balance,
            "mark_price": self._last_mark_price,
            "tp_price": self._last_tp_price,
            "sl_price": self._last_sl_price,
            "stop_reason": self._last_stop_reason,
            "raw_action": self._last_raw_action,
            "effective_action": self._last_effective_action,
            "action_suppression_reason": self._last_action_suppression_reason,
            "fill_confirmation_mode": self._fill_confirmation_mode,
            "fill_no_repeat_lsi_guard": self._fill_no_repeat_lsi_guard,
            "fill_cooldown_bars": int(self._fill_cooldown_bars),
            "tick_size": self._tick_size,
            "warnings": [str(x) for x in self._runtime_warnings],
            "exec_events": [str(x) for x in self._runtime_exec_events],
            "pause_reasons": [str(x) for x in self._runtime_pause_reasons],
            "confirm": self._runtime_confirm,
            "post_only_retry_count_total": int(self._post_only_retry_count_total),
            "post_only_reprice_count_total": int(self._post_only_reprice_count_total),
            "post_only_reject_streak": int(self._post_only_reject_streak),
            "post_only_reject_window_count": int(len(self._post_only_reject_times)),
            "reconcile_summary": self._last_reconcile_summary,
            "reconcile_skipped_due_cap": bool(self._last_reconcile_skipped_due_cap),
            "fill_guard_bar_seq": int(self._fill_guard_bar_seq),
            "fill_guard_last_clock_ts": self._fill_guard_last_clock_ts,
            "capacity_guard": dict(self._capacity_guard_state or {}),
            "capacity_rung_cap_applied_total": int(self._capacity_rung_cap_applied_total),
            "capacity_replenish_skipped_total": int(self._capacity_replenish_skipped_total),
            "execution_cost_feedback_enabled": bool(self._execution_cost_feedback_enabled),
            "execution_cost_step_metrics": dict(self._execution_cost_step_metrics or {}),
            "execution_cost_artifact": dict(self._execution_cost_last_artifact or {}),
            "execution_cost_artifact_paths": dict(
                self._execution_cost_paths(symbol) if self._execution_cost_feedback_enabled else {}
            ),
            "ccxt_error_streak": int(self._ccxt_error_streak),
            "ccxt_backoff_until_ts": float(self._ccxt_backoff_until_ts),
            "last_ccxt_error": self._last_ccxt_error,
            "state_recovery_loaded": bool(self._recovery_loaded),
            "state_recovery_error": self._recovery_error,
            "last_applied_plan_id": self._last_applied_plan_id,
            "last_applied_seq": int(self._last_applied_seq),
            "last_applied_valid_for_candle_ts": int(self._last_applied_valid_for_candle_ts),
            "last_plan_hash": self._last_applied_plan_hash,
            "executor_state_machine": executor_state_machine,
        }

        payload = ExecutorState(
            schema_version=str(self._state_schema_version),
            ts=time.time(),
            exchange=exchange_name,
            pair=symbol,
            symbol=symbol,
            plan_ts=str(plan.get("ts", "")),
            mode=self.mode,
            last_applied_plan_id=self._last_applied_plan_id,
            last_applied_seq=int(self._last_applied_seq),
            last_applied_valid_for_candle_ts=int(self._last_applied_valid_for_candle_ts),
            last_plan_hash=self._last_applied_plan_hash,
            executor_state_machine=executor_state_machine,

            step=step,
            n_levels=n_levels,
            box_low=box_low,
            box_high=box_high,

            quote_total=self.quote_total,
            base_total=self.base_total,

            quote_free=q_free,
            base_free=b_free,
            quote_reserved=q_res,
            base_reserved=b_res,

            runtime=runtime,
            orders=[asdict(o) for o in self._orders],
            applied_plan_ids=list(self._applied_plan_ids),
            applied_plan_hashes=list(self._applied_plan_hashes),
        )
        write_json(self.state_out, asdict(payload))


def _run_polling_loop(
    ex: "GridExecutorV1",
    *,
    plan_path: str,
    state_out: str,
    poll_seconds: float,
    max_consecutive_errors: int,
    error_backoff_seconds: float,
) -> None:
    poll_delay = max(float(poll_seconds), 0.0)
    error_delay = max(float(error_backoff_seconds), 0.0)
    consecutive_errors = 0

    while True:
        try:
            plan = load_json(plan_path)
            plan["_plan_path"] = plan_path
            ex.step(plan)
            consecutive_errors = 0
        except Exception as exc:
            consecutive_errors += 1
            write_json(
                state_out,
                {
                    "error": str(exc),
                    "ts": time.time(),
                    "consecutive_errors": int(consecutive_errors),
                },
            )
            if int(max_consecutive_errors) > 0 and consecutive_errors >= int(max_consecutive_errors):
                raise RuntimeError(f"max_consecutive_errors_reached:{consecutive_errors}") from exc
            if error_delay > 0:
                time.sleep(error_delay)
            continue

        if poll_delay > 0:
            time.sleep(poll_delay)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True, help="Path to grid_plan.latest.json")
    ap.add_argument("--mode", default="paper", choices=["paper", "ccxt"])
    ap.add_argument("--state-out", default="/freqtrade/user_data/grid_executor_v1.state.json")
    ap.add_argument("--poll-seconds", type=float, default=5.0)
    ap.add_argument(
        "--max-consecutive-errors",
        type=int,
        default=20,
        help="Abort polling loop after this many consecutive step errors (<=0 disables).",
    )
    ap.add_argument(
        "--error-backoff-seconds",
        type=float,
        default=1.0,
        help="Sleep time after an error before retrying.",
    )
    ap.add_argument("--once", action="store_true", help="Run a single tick and exit (testing)")

    ap.add_argument("--quote-budget", type=float, default=1000.0)
    ap.add_argument("--start-base", type=float, default=0.0)
    ap.add_argument("--maker-fee-pct", type=float, default=0.10)
    ap.add_argument("--post-only", action="store_true", help="Try post-only in ccxt mode")
    ap.add_argument("--max-orders-per-side", type=int, default=40)

    # ccxt-only
    ap.add_argument("--exchange", default=None, help="ccxt exchange id (e.g. binance)")
    ap.add_argument("--api-key", default=None)
    ap.add_argument("--api-secret", default=None)
    ap.add_argument("--api-password", default=None)
    ap.add_argument("--sandbox", action="store_true")

    ap.add_argument("--use-exchange-balance", action="store_true", help="Refresh balances from exchange (ccxt)")
    ap.add_argument("--no-use-exchange-balance", action="store_true", help="Disable refresh balances from exchange (ccxt)")
    ap.add_argument("--close-on-stop", action="store_true", help="Attempt market-sell inventory on STOP (ccxt only)")

    ap.add_argument("--ccxt-retries", type=int, default=3)
    ap.add_argument("--trade-lookback-ms", type=int, default=60_000)

    args = ap.parse_args()

    use_ex_bal = True
    if args.no_use_exchange_balance:
        use_ex_bal = False
    if args.use_exchange_balance:
        use_ex_bal = True

    ex = GridExecutorV1(
        mode=args.mode,
        state_out=args.state_out,
        poll_seconds=args.poll_seconds,
        quote_budget=args.quote_budget,
        start_base=args.start_base,
        maker_fee_pct=args.maker_fee_pct,
        post_only=args.post_only,
        max_orders_per_side=args.max_orders_per_side,
        exchange_name=args.exchange,
        api_key=args.api_key,
        api_secret=args.api_secret,
        api_password=args.api_password,
        sandbox=args.sandbox,
        ccxt_retries=args.ccxt_retries,
        use_exchange_balance=use_ex_bal,
        close_on_stop=args.close_on_stop,
        trade_lookback_ms=args.trade_lookback_ms,
    )

    if args.once:
        plan = load_json(args.plan)
        plan["_plan_path"] = args.plan
        ex.step(plan)
        return

    _run_polling_loop(
        ex=ex,
        plan_path=args.plan,
        state_out=args.state_out,
        poll_seconds=args.poll_seconds,
        max_consecutive_errors=args.max_consecutive_errors,
        error_backoff_seconds=args.error_backoff_seconds,
    )


if __name__ == "__main__":
    main()
