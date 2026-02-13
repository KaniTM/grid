import argparse
import json
import os
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    import ccxt  # optional, only needed for --mode ccxt
except Exception:
    ccxt = None


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
    ts: float
    exchange: str
    symbol: str
    plan_ts: str
    mode: str

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


# -----------------------------
# Helpers
# -----------------------------
def load_json(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, payload: Dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp, path)


def build_levels(box_low: float, box_high: float, n_levels: int) -> np.ndarray:
    if n_levels <= 0:
        return np.array([])
    return np.linspace(box_low, box_high, n_levels + 1)


def plan_signature(plan: Dict) -> Tuple:
    """
    Signature used to detect material plan changes.
    IMPORTANT: do NOT include `action` (prevents churn).
    """
    r = plan["range"]
    g = plan["grid"]
    return (
        round(float(r["low"]), 12),
        round(float(r["high"]), 12),
        int(g["n_levels"]),
        round(float(g["step_price"]), 12),
    )


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
    except Exception:
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
        return vals
    except Exception:
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

    # ---------- ccxt call wrapper ----------
    def _ccxt_call(self, fn, *args, **kwargs):
        if self.exchange is None:
            return None
        last_err = None
        for _ in range(max(self.ccxt_retries, 1)):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                last_err = e
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

        # cap per side
        if len(buys) > self.max_orders_per_side:
            buys = buys[-self.max_orders_per_side:]
        if len(sells) > self.max_orders_per_side:
            sells = sells[:self.max_orders_per_side]

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

        try:
            if side == "buy":
                res = self._ccxt_call(self.exchange.create_limit_buy_order, symbol, qt, px, params=params)
            else:
                res = self._ccxt_call(self.exchange.create_limit_sell_order, symbol, qt, px, params=params)
            return (res or {}).get("id")
        except Exception:
            return None

    def _ccxt_reconcile_set(self, desired: List[RestingOrder], symbol: str, limits: Dict) -> None:
        """
        Diff reconcile:
        - cancel stale orders not in desired
        - place missing desired orders
        """
        open_live = self._ccxt_fetch_open_orders(symbol)

        live_map: Dict[Tuple, str] = {}  # key -> order_id
        for o in open_live:
            try:
                side = str(o.get("side")).lower()
                price = float(o.get("price"))
                amount = float(o.get("amount") or o.get("remaining") or 0.0)
                oid = str(o.get("id") or "")
                if oid:
                    live_map[_key_for(side, price, amount)] = oid
            except Exception:
                continue

        desired_map: Dict[Tuple, RestingOrder] = {}
        for ro in desired:
            desired_map[_key_for(ro.side, ro.price, ro.qty_base)] = ro

        # cancel stale
        for k, oid in live_map.items():
            if k not in desired_map:
                self._ccxt_cancel_order(oid, symbol)

        # place missing
        new_orders: List[RestingOrder] = []
        for k, ro in desired_map.items():
            if k in live_map:
                ro.order_id = live_map[k]
                ro.status = "open"
                new_orders.append(ro)
            else:
                oid = self._ccxt_place_limit(ro.side, symbol, ro.qty_base, ro.price, limits)
                ro.order_id = oid
                ro.status = "open" if oid else "rejected"
                new_orders.append(ro)

        self._orders = new_orders

    # ---------- fill ingestion ----------
    def _levels_for_index(self, levels: np.ndarray, idx: int) -> Optional[float]:
        if idx < 0 or idx >= len(levels):
            return None
        return float(levels[idx])

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

    def _ingest_trades_and_replenish(self, symbol: str, levels: np.ndarray, limits: Dict) -> None:
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
                if ro.side == "buy":
                    next_idx = ro.level_index + 1
                    px = self._levels_for_index(levels, next_idx)
                    if px is not None:
                        new_px = float(quantize_price(self.exchange, symbol, px))
                        new_qty = float(quantize_amount(self.exchange, symbol, filled_qty))
                        if new_qty > 0 and passes_min_notional(limits, new_px, new_qty):
                            new_oid = self._ccxt_place_limit("sell", symbol, new_qty, new_px, limits)
                            self._orders.append(RestingOrder("sell", new_px, new_qty, next_idx, order_id=new_oid, status="open" if new_oid else "rejected"))
                else:
                    next_idx = ro.level_index - 1
                    px = self._levels_for_index(levels, next_idx)
                    if px is not None:
                        new_px = float(quantize_price(self.exchange, symbol, px))
                        new_qty = float(quantize_amount(self.exchange, symbol, filled_qty))
                        if new_qty > 0 and passes_min_notional(limits, new_px, new_qty):
                            new_oid = self._ccxt_place_limit("buy", symbol, new_qty, new_px, limits)
                            self._orders.append(RestingOrder("buy", new_px, new_qty, next_idx, order_id=new_oid, status="open" if new_oid else "rejected"))

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
        if "range" not in plan or "grid" not in plan:
            raise KeyError("Plan schema mismatch: expected keys ['range','grid'].")

        raw_action = str(plan.get("action", "HOLD")).upper()
        if raw_action not in ("START", "HOLD", "STOP"):
            raw_action = "HOLD"
        ex_name = plan.get("exchange", "unknown")
        symbol = plan.get("symbol", "UNKNOWN/UNKNOWN")
        self.symbol = symbol

        box_low = float(plan["range"]["low"])
        box_high = float(plan["range"]["high"])
        n_levels = int(plan["grid"]["n_levels"])
        step = float(plan["grid"]["step_price"])
        rung_weights = _extract_rung_weights(plan, n_levels)

        levels = build_levels(box_low, box_high, n_levels)
        if len(levels) < 2:
            raise ValueError("Not enough levels (n_levels must be >= 1).")

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

        # Refresh balances (ccxt)
        if self.mode == "ccxt":
            self._sync_balance_ccxt()
            # Ingest fills and replenish before we make plan-adjust decisions
            if raw_action != "STOP":
                self._ingest_trades_and_replenish(symbol, levels, limits)

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
            self._write_state(plan, ex_name, symbol, step, n_levels, box_low, box_high)
            self._prev_plan = plan
            self._last_effective_action_signature = _action_signature(
                "STOP", plan_sig, self._last_stop_reason or "plan_stop"
            )
            return

        grid_budget_pct = float(plan.get("capital_policy", {}).get("grid_budget_pct", 1.0))
        grid_budget_pct = float(np.clip(grid_budget_pct, 0.0, 1.0))

        # HOLD: manage only existing ladder, never seed from empty.
        if effective_action == "HOLD":
            if not has_active_orders:
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
                    if self.exchange is not None:
                        px = float(quantize_price(self.exchange, symbol, px))
                    o.price = float(px)

            # Keep live venue in sync without seeding new ladder.
            if self.mode == "ccxt":
                desired = [o for o in self._orders if o.status in ("open", "partial")]
                self._ccxt_reconcile_set(desired, symbol, limits)

            self._write_state(plan, ex_name, symbol, step, n_levels, box_low, box_high)
            self._prev_plan = plan
            self._last_effective_action_signature = _action_signature("HOLD", plan_sig)
            return

        # START: seed/rebuild/soft-adjust.
        if (not has_active_orders) or rebuild or self._prev_plan is None:
            desired = self._desired_initial_ladder(
                levels, ref_price, limits, grid_budget_pct, rung_weights=rung_weights
            )

            if self.exchange is not None:
                for ro in desired:
                    ro.price = float(quantize_price(self.exchange, symbol, ro.price))
                    ro.qty_base = float(quantize_amount(self.exchange, symbol, ro.qty_base))

            if self.mode == "paper":
                self._orders = desired
            else:
                self._ccxt_reconcile_set(desired, symbol, limits)

        elif soft_adjust:
            for o in self._orders:
                px = self._levels_for_index(levels, o.level_index)
                if px is None:
                    continue
                if self.exchange is not None:
                    px = float(quantize_price(self.exchange, symbol, px))
                o.price = float(px)

            if self.mode == "ccxt":
                desired = [o for o in self._orders if o.status in ("open", "partial")]
                self._ccxt_reconcile_set(desired, symbol, limits)

        else:
            # START and no plan change: keep current set.
            pass

        self._write_state(plan, ex_name, symbol, step, n_levels, box_low, box_high)
        self._prev_plan = plan
        self._last_effective_action_signature = _action_signature("START", plan_sig)

    def _write_state(self, plan: Dict, exchange_name: str, symbol: str, step: float, n_levels: int, box_low: float, box_high: float) -> None:
        q_res, b_res = self._reserved_balances_intent()
        q_free, b_free = self._free_balances_intent()

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
        }

        payload = ExecutorState(
            ts=time.time(),
            exchange=exchange_name,
            symbol=symbol,
            plan_ts=str(plan.get("ts", "")),
            mode=self.mode,

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
        )
        write_json(self.state_out, asdict(payload))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True, help="Path to grid_plan.latest.json")
    ap.add_argument("--mode", default="paper", choices=["paper", "ccxt"])
    ap.add_argument("--state-out", default="/freqtrade/user_data/grid_executor_v1.state.json")
    ap.add_argument("--poll-seconds", type=float, default=5.0)
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
        ex.step(plan)
        return

    while True:
        try:
            plan = load_json(args.plan)
            ex.step(plan)
        except Exception as e:
            write_json(args.state_out, {"error": str(e), "ts": time.time()})
        time.sleep(args.poll_seconds)


if __name__ == "__main__":
    main()
