#!/usr/bin/env python3
"""
Behavior-level regression checks for the user_data Brain/Executor/Simulator stack.

Add new assertions here whenever a new module/feature is introduced.
This keeps "it compiles" separate from "it actually behaves as designed".
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd

# Import sibling scripts directly from user_data/scripts.
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
STRATEGY_DIR = SCRIPT_DIR.parent / "strategies"
if str(STRATEGY_DIR) not in sys.path:
    sys.path.insert(0, str(STRATEGY_DIR))

from grid_executor_v1 import GridExecutorV1
from grid_simulator_v1 import (
    build_desired_ladder,
    build_levels,
    simulate_grid_replay,
)
from GridBrainV1 import GridBrainV1


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def _plan_get(d: dict, *path, default=None):
    cur = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def check_plan_schema_and_feature_outputs(plan: dict) -> None:
    print("[regression] check: plan schema + feature outputs")

    _require("range" in plan and "grid" in plan and "risk" in plan and "signals" in plan, "plan base keys missing")
    _require("mode" in plan, "plan.mode missing")
    _require("regime_router" in plan, "plan.regime_router missing")
    rr = plan.get("regime_router", {}) or {}
    for key in ["active_mode", "desired_mode", "target_mode", "scores"]:
        _require(key in rr, f"plan.regime_router.{key} missing")

    n_levels = int(_plan_get(plan, "grid", "n_levels", default=0) or 0)
    _require(n_levels >= 1, "grid.n_levels must be >= 1")

    # VRVP module outputs.
    vp = _plan_get(plan, "range", "volume_profile", default={}) or {}
    for key in ["poc", "vah", "val", "box_ok"]:
        _require(key in vp, f"range.volume_profile.{key} missing")

    # Micro-VAP module outputs.
    micro = _plan_get(plan, "range", "micro_vap", default={}) or {}
    for key in ["poc", "hvn_levels", "lvn_levels", "void_slope"]:
        _require(key in micro, f"range.micro_vap.{key} missing")

    # FVG stack outputs.
    fvg = _plan_get(plan, "range", "fvg", default={}) or {}
    for key in ["straddle_veto", "defensive_conflict", "session_gate_ok", "gate_ok"]:
        _require(key in fvg, f"range.fvg.{key} missing")

    # MRVD outputs.
    mrvd = _plan_get(plan, "range", "multi_range_volume", default={}) or {}
    for key in ["overlap_count", "overlap_ok", "near_any_poc", "day", "week", "month"]:
        _require(key in mrvd, f"range.multi_range_volume.{key} missing")

    # CVD outputs.
    cvd = _plan_get(plan, "range", "cvd", default={}) or {}
    for key in ["enabled", "state"]:
        _require(key in cvd, f"range.cvd.{key} missing")

    # ML overlay outputs.
    ml = _plan_get(plan, "range", "ml_overlay", default={}) or {}
    for key in ["enabled", "source", "p_range", "p_breakout", "ml_confidence", "gate_ok"]:
        _require(key in ml, f"range.ml_overlay.{key} missing")

    diag = _plan_get(plan, "diagnostics", default={}) or {}
    for key in [
        "start_gate_ok",
        "price_in_box",
        "rsi_ok",
        "start_signal",
        "start_blocked",
        "start_block_reasons",
        "stop_rule_triggered",
        "stop_rule_triggered_raw",
        "stop_reason_flags_raw_active",
        "stop_reason_flags_applied_active",
    ]:
        _require(key in diag, f"diagnostics.{key} missing")

    # Rung bias must exist and align with ladder levels.
    rb = _plan_get(plan, "grid", "rung_density_bias", default={}) or {}
    _require("weights_by_level_index" in rb, "grid.rung_density_bias.weights_by_level_index missing")
    weights = [float(x) for x in (rb.get("weights_by_level_index") or [])]
    _require(len(weights) == (n_levels + 1), "rung weights length must be n_levels + 1")
    _require(all(w >= 0 for w in weights), "rung weights must be non-negative")
    _require(max(weights) > min(weights), "rung weights are flat; expected HVN/LVN bias effect")

    # New stop override reason should be present.
    stop_reasons = _plan_get(plan, "risk", "stop_reasons", default={}) or {}
    _require("lvn_corridor_stop_override" in stop_reasons, "risk.stop_reasons.lvn_corridor_stop_override missing")
    _require("fvg_conflict_stop_override" in stop_reasons, "risk.stop_reasons.fvg_conflict_stop_override missing")
    _require("adx_hysteresis_stop" in stop_reasons, "risk.stop_reasons.adx_hysteresis_stop missing")
    _require("adx_di_down_risk_stop" in stop_reasons, "risk.stop_reasons.adx_di_down_risk_stop missing")
    _require("bbwp_expansion_stop" in stop_reasons, "risk.stop_reasons.bbwp_expansion_stop missing")
    _require("mode_handoff_required_stop" in stop_reasons, "risk.stop_reasons.mode_handoff_required_stop missing")
    _require("router_pause_stop" in stop_reasons, "risk.stop_reasons.router_pause_stop missing")
    _require("micro_vap_ok" in (plan.get("signals") or {}), "signals.micro_vap_ok missing")
    _require("fvg_gate_ok" in (plan.get("signals") or {}), "signals.fvg_gate_ok missing")
    _require("mrvd_gate_ok" in (plan.get("signals") or {}), "signals.mrvd_gate_ok missing")
    _require("cvd_gate_ok" in (plan.get("signals") or {}), "signals.cvd_gate_ok missing")
    _require("cvd_freeze_active" in (plan.get("signals") or {}), "signals.cvd_freeze_active missing")
    _require("cvd_bos_up" in (plan.get("signals") or {}), "signals.cvd_bos_up missing")
    _require("cvd_bos_down" in (plan.get("signals") or {}), "signals.cvd_bos_down missing")
    _require("ml_gate_ok" in (plan.get("signals") or {}), "signals.ml_gate_ok missing")
    _require("ml_overlay_source" in (plan.get("signals") or {}), "signals.ml_overlay_source missing")
    _require("ml_do_predict" in (plan.get("signals") or {}), "signals.ml_do_predict missing")
    _require("bb_width_1h_pct" in (plan.get("signals") or {}), "signals.bb_width_1h_pct missing")
    _require("mode" in (plan.get("signals") or {}), "signals.mode missing")
    _require("mode_pause" in (plan.get("signals") or {}), "signals.mode_pause missing")
    _require("mode_desired" in (plan.get("signals") or {}), "signals.mode_desired missing")
    _require("regime_threshold_profile" in (plan.get("signals") or {}), "signals.regime_threshold_profile missing")
    _require("adx_enter_max_4h" in (plan.get("signals") or {}), "signals.adx_enter_max_4h missing")
    _require("adx_exit_min_4h" in (plan.get("signals") or {}), "signals.adx_exit_min_4h missing")
    _require("adx_exit_max_4h" in (plan.get("signals") or {}), "signals.adx_exit_max_4h missing")
    _require("adx_exit_overheat" in (plan.get("signals") or {}), "signals.adx_exit_overheat missing")
    _require("adx_rising_bars_4h" in (plan.get("signals") or {}), "signals.adx_rising_bars_4h missing")
    _require("adx_rising_required_4h" in (plan.get("signals") or {}), "signals.adx_rising_required_4h missing")
    _require("adx_rising_confirmed_4h" in (plan.get("signals") or {}), "signals.adx_rising_confirmed_4h missing")
    _require("plus_di_4h" in (plan.get("signals") or {}), "signals.plus_di_4h missing")
    _require("minus_di_4h" in (plan.get("signals") or {}), "signals.minus_di_4h missing")
    _require("atr_mode_source" in (plan.get("signals") or {}), "signals.atr_mode_source missing")
    _require("atr_mode_pct" in (plan.get("signals") or {}), "signals.atr_mode_pct missing")
    _require("atr_mode_max" in (plan.get("signals") or {}), "signals.atr_mode_max missing")
    _require("atr_ok" in (plan.get("signals") or {}), "signals.atr_ok missing")
    _require("bbwp_stop_high" in (plan.get("signals") or {}), "signals.bbwp_stop_high missing")
    _require("bbwp_expansion_stop" in (plan.get("signals") or {}), "signals.bbwp_expansion_stop missing")
    _require("mode_handoff_required_stop" in (plan.get("signals") or {}), "signals.mode_handoff_required_stop missing")
    _require("router_pause_stop" in (plan.get("signals") or {}), "signals.router_pause_stop missing")

    gating = _plan_get(plan, "update_policy", "gating", default={}) or {}
    _require("adx_4h_max" in gating, "update_policy.gating.adx_4h_max missing")
    _require("adx_4h_exit_min" in gating, "update_policy.gating.adx_4h_exit_min missing")
    _require("bbw_1h_pct_max" in gating, "update_policy.gating.bbw_1h_pct_max missing")
    _require("active_mode" in gating, "update_policy.gating.active_mode missing")
    _require("adx_4h_exit_max" in gating, "update_policy.gating.adx_4h_exit_max missing")
    _require("atr_source" in gating, "update_policy.gating.atr_source missing")
    _require("atr_pct_max" in gating, "update_policy.gating.atr_pct_max missing")
    _require("bbwp_stop_high" in gating, "update_policy.gating.bbwp_stop_high missing")
    _require(isinstance(_plan_get(plan, "update_policy", "intraday", default={}), dict), "update_policy.intraday missing")
    _require(isinstance(_plan_get(plan, "update_policy", "swing", default={}), dict), "update_policy.swing missing")
    _require(isinstance(_plan_get(plan, "update_policy", "regime_router", default={}), dict), "update_policy.regime_router missing")
    _require(
        "allow_pause" in (_plan_get(plan, "update_policy", "regime_router", default={}) or {}),
        "update_policy.regime_router.allow_pause missing",
    )
    _require(
        "threshold_profile" in (_plan_get(plan, "update_policy", "regime_router", default={}) or {}),
        "update_policy.regime_router.threshold_profile missing",
    )

    tp_candidates = _plan_get(plan, "exit", "tp_candidates", default={}) or {}
    _require("imfvg_avg_bull" in tp_candidates, "exit.tp_candidates.imfvg_avg_bull missing")
    _require("session_fvg_avg" in tp_candidates, "exit.tp_candidates.session_fvg_avg missing")
    _require("mrvd_day_poc" in tp_candidates, "exit.tp_candidates.mrvd_day_poc missing")
    _require("mrvd_week_poc" in tp_candidates, "exit.tp_candidates.mrvd_week_poc missing")
    _require("cvd_quick_tp_candidate" in tp_candidates, "exit.tp_candidates.cvd_quick_tp_candidate missing")
    _require("ml_quick_tp_candidate" in tp_candidates, "exit.tp_candidates.ml_quick_tp_candidate missing")

    print("[regression] check: plan schema + feature outputs OK")


def check_recent_plan_history(plan_path: Path, recent_seconds: int = 600) -> None:
    print("[regression] check: per-candle plan history coverage")
    plan_dir = plan_path.parent
    if not plan_dir.is_dir():
        raise AssertionError(f"plan directory missing: {plan_dir}")

    now = time.time()
    files = sorted(plan_dir.glob("grid_plan*.json"))
    recent_files = []
    for p in files:
        try:
            if (now - float(p.stat().st_mtime)) <= float(recent_seconds):
                recent_files.append(p)
        except Exception:
            continue

    _require(len(recent_files) > 0, "no recent plan snapshots found in plan directory")

    unique_candle_ts = set()
    for p in recent_files:
        try:
            with p.open("r", encoding="utf-8") as f:
                pl = json.load(f)
        except Exception:
            continue
        cts = _plan_get(pl, "candle_ts", default=None)
        if cts is None:
            continue
        try:
            unique_candle_ts.add(int(cts))
        except Exception:
            continue

    _require(
        len(unique_candle_ts) >= 2,
        "expected >=2 unique recent candle_ts plan snapshots (time-varying plans), got fewer",
    )
    print("[regression] check: per-candle plan history coverage OK")


def _base_paper_executor(state_out: str, quote_budget: float, maker_fee_pct: float) -> GridExecutorV1:
    return GridExecutorV1(
        mode="paper",
        state_out=state_out,
        poll_seconds=0.0,
        quote_budget=float(quote_budget),
        start_base=0.0,
        maker_fee_pct=float(maker_fee_pct),
        post_only=True,
        max_orders_per_side=40,
        exchange_name=None,
        api_key=None,
        api_secret=None,
        api_password=None,
        sandbox=False,
        ccxt_retries=1,
        use_exchange_balance=False,
        close_on_stop=False,
        trade_lookback_ms=60_000,
    )


def _force_ref_inside_box(plan: dict) -> dict:
    p = copy.deepcopy(plan)
    lo = float(_plan_get(p, "range", "low"))
    hi = float(_plan_get(p, "range", "high"))
    mid = (lo + hi) / 2.0
    p.setdefault("price_ref", {})
    p["price_ref"]["close"] = float(mid)
    return p


def check_executor_action_semantics(plan: dict, state_out: str, quote_budget: float, maker_fee_pct: float) -> None:
    print("[regression] check: executor action semantics")

    start_plan = _force_ref_inside_box(plan)
    hold_plan = _force_ref_inside_box(plan)
    stop_plan = _force_ref_inside_box(plan)
    start_plan["action"] = "START"
    hold_plan["action"] = "HOLD"
    stop_plan["action"] = "STOP"

    ex = _base_paper_executor(state_out, quote_budget, maker_fee_pct)
    ex.step(start_plan)
    start_orders = [o for o in ex._orders if o.status in ("open", "partial")]
    _require(len(start_orders) > 0, "START must seed orders")

    ex.step(hold_plan)
    hold_orders = [o for o in ex._orders if o.status in ("open", "partial")]
    _require(len(hold_orders) == len(start_orders), "HOLD with active ladder should manage existing orders")

    ex.step(stop_plan)
    _require(len(ex._orders) == 0, "STOP must clear all orders")

    # HOLD from cold start should not seed.
    ex2 = _base_paper_executor(state_out, quote_budget, maker_fee_pct)
    ex2.step(hold_plan)
    _require(len(ex2._orders) == 0, "HOLD from empty must not seed orders")

    print("[regression] check: executor action semantics OK")


def check_weighted_ladder_and_simulator(plan: dict, quote_budget: float, maker_fee_pct: float) -> None:
    print("[regression] check: weighted ladder + simulator behavior")

    n_levels = int(_plan_get(plan, "grid", "n_levels"))
    lo = float(_plan_get(plan, "range", "low"))
    hi = float(_plan_get(plan, "range", "high"))
    levels = build_levels(lo, hi, n_levels)
    ref_price = float(_plan_get(plan, "price_ref", "close", default=(lo + hi) / 2.0))
    rung_weights = [float(x) for x in (_plan_get(plan, "grid", "rung_density_bias", "weights_by_level_index", default=[]) or [])]

    ladder = build_desired_ladder(
        levels=levels,
        ref_price=ref_price,
        quote_total=float(quote_budget),
        base_total=0.0,
        maker_fee_pct=float(maker_fee_pct),
        grid_budget_pct=1.0,
        max_orders_per_side=40,
        rung_weights=rung_weights if rung_weights else None,
    )
    buys = [o for o in ladder if o.side == "buy"]
    _require(len(buys) > 0, "weighted ladder should produce buy orders")
    uniq = len({round(float(o.qty_base), 12) for o in buys})
    _require(uniq > 1, "weighted ladder should produce non-uniform order sizes")

    # Replay semantic check with synthetic candles and action transitions.
    t0 = pd.Timestamp("2026-01-01T00:00:00Z")
    df = pd.DataFrame(
        [
            {"date": t0, "open": ref_price, "high": ref_price * 1.001, "low": ref_price * 0.999, "close": ref_price, "volume": 1.0},
            {"date": t0 + pd.Timedelta(minutes=15), "open": ref_price, "high": ref_price * 1.001, "low": ref_price * 0.995, "close": ref_price * 0.997, "volume": 1.0},
            {"date": t0 + pd.Timedelta(minutes=30), "open": ref_price * 0.997, "high": ref_price * 1.000, "low": ref_price * 0.994, "close": ref_price * 0.996, "volume": 1.0},
            {"date": t0 + pd.Timedelta(minutes=45), "open": ref_price * 0.996, "high": ref_price * 0.998, "low": ref_price * 0.990, "close": ref_price * 0.992, "volume": 1.0},
        ]
    )

    p_start = _force_ref_inside_box(plan)
    p_hold = _force_ref_inside_box(plan)
    p_stop = _force_ref_inside_box(plan)
    p_start["action"] = "START"
    p_hold["action"] = "HOLD"
    p_stop["action"] = "STOP"
    p_start["_plan_time"] = t0
    p_hold["_plan_time"] = t0 + pd.Timedelta(minutes=30)
    p_stop["_plan_time"] = t0 + pd.Timedelta(minutes=45)
    p_start["_plan_path"] = "regression_start"
    p_hold["_plan_path"] = "regression_hold"
    p_stop["_plan_path"] = "regression_stop"

    res = simulate_grid_replay(
        df=df,
        plans=[p_start, p_hold, p_stop],
        start_quote=float(quote_budget),
        start_base=0.0,
        maker_fee_pct=float(maker_fee_pct),
        stop_out_steps=1,
        touch_fill=True,
        max_orders_per_side=40,
        close_on_stop=False,
    )
    summary = res.get("summary", {})
    _require(int(summary.get("seed_events", 0)) >= 1, "replay should seed on START")
    _require(int(summary.get("stop_events", 0)) >= 1, "replay should stop on STOP")
    acts = summary.get("actions", {}) or {}
    _require(int(acts.get("START", 0)) >= 1, "replay should process START action")
    _require(int(acts.get("HOLD", 0)) >= 1, "replay should process HOLD action")
    _require(int(acts.get("STOP", 0)) >= 1, "replay should process STOP action")
    _require(isinstance(summary.get("start_blocker_counts", {}), dict), "summary.start_blocker_counts must be a dict")
    _require(
        isinstance(summary.get("start_counterfactual_single_counts", {}), dict),
        "summary.start_counterfactual_single_counts must be a dict",
    )
    _require(
        isinstance(summary.get("start_counterfactual_combo_counts", {}), dict),
        "summary.start_counterfactual_combo_counts must be a dict",
    )
    _require(isinstance(summary.get("hold_reason_counts", {}), dict), "summary.hold_reason_counts must be a dict")
    _require(isinstance(summary.get("stop_reason_counts", {}), dict), "summary.stop_reason_counts must be a dict")
    _require(isinstance(summary.get("stop_event_reason_counts", {}), dict), "summary.stop_event_reason_counts must be a dict")
    _require(
        isinstance(summary.get("stop_reason_counts_combined", {}), dict),
        "summary.stop_reason_counts_combined must be a dict",
    )
    curve_rows = res.get("curve", []) or []
    _require(len(curve_rows) > 0, "replay curve rows should not be empty")
    first_curve = curve_rows[0]
    _require(
        "start_counterfactual_required_count" in first_curve,
        "curve rows must include start_counterfactual_required_count",
    )
    _require("start_counterfactual_combo" in first_curve, "curve rows must include start_counterfactual_combo")

    print("[regression] check: weighted ladder + simulator behavior OK")


def check_ml_overlay_behavior() -> None:
    print("[regression] check: ML overlay behavior")

    brain = GridBrainV1(
        config={
            "candle_type_def": "spot",
            "exchange": {"name": "binance"},
            "runmode": "backtest",
            "freqai": {"enabled": False},
        }
    )

    row_prob = pd.Series({"do_predict": 1, "p_range": 0.8, "p_breakout": 0.2, "ml_confidence": 0.9})
    st_prob = brain._freqai_overlay_state(
        row_prob, close=100.0, step_price=1.0, q1=95.0, q2=100.0, q3=105.0, vrvp_poc=101.0
    )
    _require(st_prob.get("source") == "prob_columns", "ML overlay should prefer explicit probability columns")
    _require(abs(float(st_prob.get("p_range", 0.0)) - 0.8) < 1e-9, "p_range extraction mismatch")
    _require(abs(float(st_prob.get("p_breakout", 0.0)) - 0.2) < 1e-9, "p_breakout extraction mismatch")
    _require(bool(st_prob.get("gate_ok")), "non-strict ML gate should pass when overlay is available")

    brain.freqai_overlay_strict_predict = True
    row_strict_fail = pd.Series({"do_predict": 0, "p_range": 0.9, "p_breakout": 0.1, "ml_confidence": 0.9})
    st_strict_fail = brain._freqai_overlay_state(
        row_strict_fail, close=100.0, step_price=1.0, q1=95.0, q2=100.0, q3=105.0, vrvp_poc=101.0
    )
    _require(not bool(st_strict_fail.get("gate_ok")), "strict ML gate should fail when do_predict=0")

    row_strict_pass = pd.Series({"do_predict": 1, "p_range": 0.9, "p_breakout": 0.1, "ml_confidence": 0.95})
    st_strict_pass = brain._freqai_overlay_state(
        row_strict_pass, close=100.0, step_price=1.0, q1=95.0, q2=105.0, q3=110.0, vrvp_poc=108.0
    )
    _require(bool(st_strict_pass.get("gate_ok")), "strict ML gate should pass for confident do_predict=1")

    brain.freqai_overlay_strict_predict = False
    row_proxy = pd.Series({"&-s_close": 0.10})
    st_proxy = brain._freqai_overlay_state(
        row_proxy, close=100.0, step_price=1.0, q1=95.0, q2=105.0, q3=110.0, vrvp_poc=108.0
    )
    _require(st_proxy.get("source") == "s_close_proxy", "ML overlay should use s_close proxy when probs absent")
    _require(float(st_proxy.get("p_breakout") or 0.0) > float(st_proxy.get("p_range") or 0.0), "proxy should indicate breakout risk for large |s_close|")
    _require(bool(st_proxy.get("breakout_risk_high")), "proxy case should trigger high-breakout state")
    _require(st_proxy.get("quick_tp_candidate") is not None, "high-breakout proxy should provide quick TP candidate")

    levels = np.array([90.0, 95.0, 100.0, 105.0, 110.0], dtype=float)
    base_weights = [1.0] * len(levels)
    safe_weights = brain._apply_ml_rung_safety(
        levels=levels,
        rung_weights=base_weights,
        box_low=90.0,
        box_high=110.0,
        p_breakout=0.8,
        edge_cut_max=0.5,
        w_min=0.2,
        w_max=3.0,
    )
    _require(len(safe_weights) == len(base_weights), "ML rung safety must preserve weights shape")
    _require(safe_weights[2] >= safe_weights[0], "ML rung safety should cut edge risk more than center")
    _require(safe_weights[2] >= safe_weights[-1], "ML rung safety should cut edge risk more than center")
    _require(safe_weights[0] < 1.0 and safe_weights[-1] < 1.0, "ML rung safety should reduce edge weights under breakout risk")

    print("[regression] check: ML overlay behavior OK")


def check_adx_hysteresis_behavior() -> None:
    print("[regression] check: ADX hysteresis stop confirmation")

    brain = GridBrainV1(
        config={
            "candle_type_def": "spot",
            "exchange": {"name": "binance"},
            "runmode": "backtest",
        }
    )
    _require(
        not brain._adx_exit_hysteresis_trigger(
            adx_value=31.0,
            rising_count=2,
            exit_min=30.0,
            rising_bars_required=3,
        ),
        "ADX stop should not trigger before rising-bars confirmation",
    )
    _require(
        brain._adx_exit_hysteresis_trigger(
            adx_value=31.0,
            rising_count=3,
            exit_min=30.0,
            rising_bars_required=3,
        ),
        "ADX stop should trigger after rising-bars confirmation",
    )
    _require(
        brain._adx_di_down_risk_trigger(
            adx_value=29.0,
            plus_di_value=12.0,
            minus_di_value=24.0,
            rising_count=3,
            exit_min=30.0,
            rising_bars_required=3,
            early_margin=2.0,
        ),
        "Down-DI risk stop should trigger in early-warning band",
    )
    _require(
        not brain._adx_di_down_risk_trigger(
            adx_value=29.0,
            plus_di_value=24.0,
            minus_di_value=12.0,
            rising_count=3,
            exit_min=30.0,
            rising_bars_required=3,
            early_margin=2.0,
        ),
        "Down-DI risk stop should not trigger when +DI dominates",
    )

    print("[regression] check: ADX hysteresis stop confirmation OK")


def check_mode_router_handoff_behavior() -> None:
    print("[regression] check: regime router mode selection + handoff")

    brain = GridBrainV1(
        config={
            "candle_type_def": "spot",
            "exchange": {"name": "binance"},
            "runmode": "backtest",
        }
    )
    brain.regime_router_enabled = True
    brain.regime_router_default_mode = "intraday"
    brain.regime_router_force_mode = ""
    brain.regime_router_allow_pause = True
    brain.regime_router_switch_persist_bars = 2
    brain.regime_router_switch_cooldown_bars = 2
    brain.regime_router_switch_margin = 1.0

    pair = "ETH/USDT"
    brain._reset_pair_runtime_state(pair)

    intraday_features = {
        "adx_4h": 14.0,
        "ema_dist_frac_1h": 0.003,
        "bb_width_1h_pct": 20.0,
        "vol_ratio_1h": 1.0,
        "bbwp_15m_pct": 25.0,
        "bbwp_1h_pct": 30.0,
        "bbwp_4h_pct": 40.0,
        "atr_1h_pct": 0.010,
        "atr_4h_pct": 0.020,
        "rvol_15m": 1.0,
        "running_active": False,
        "running_mode": None,
    }
    swing_features = {
        "adx_4h": 26.0,
        "ema_dist_frac_1h": 0.008,
        "bb_width_1h_pct": 35.0,
        "vol_ratio_1h": 1.4,
        "bbwp_15m_pct": 50.0,
        "bbwp_1h_pct": 55.0,
        "bbwp_4h_pct": 70.0,
        "atr_1h_pct": 0.020,
        "atr_4h_pct": 0.020,
        "rvol_15m": 1.3,
        "running_active": False,
        "running_mode": None,
    }
    pause_features = {
        "adx_4h": 44.0,
        "ema_dist_frac_1h": 0.030,
        "bb_width_1h_pct": 95.0,
        "vol_ratio_1h": 3.5,
        "bbwp_15m_pct": 96.0,
        "bbwp_1h_pct": 97.0,
        "bbwp_4h_pct": 98.0,
        "atr_1h_pct": 0.080,
        "atr_4h_pct": 0.080,
        "rvol_15m": 3.0,
        "running_active": False,
        "running_mode": None,
    }

    t0 = 1_700_000_000
    st0 = brain._regime_router_state(pair, t0, intraday_features)
    _require(st0.get("active_mode") == "intraday", "router should start in intraday mode")
    _require(not bool(st0.get("switched")), "router should not report switch on first stable state")

    st1 = brain._regime_router_state(pair, t0 + 900, pause_features)
    _require(st1.get("active_mode") == "intraday", "router should wait for persistence before switching")
    _require(st1.get("candidate_mode") == "pause", "router candidate should move to pause")
    _require(int(st1.get("candidate_count", 0)) == 1, "router candidate count should increment")

    st2 = brain._regime_router_state(pair, t0 + 1800, pause_features)
    _require(st2.get("active_mode") == "pause", "router should switch to pause when no mode is eligible")
    _require(bool(st2.get("switched")), "router should report pause handoff")

    brain._reset_pair_runtime_state(pair)
    running_intraday = dict(intraday_features)
    running_intraday["running_active"] = True
    running_intraday["running_mode"] = "intraday"
    running_swing = dict(swing_features)
    running_swing["running_active"] = True
    running_swing["running_mode"] = "intraday"

    st3 = brain._regime_router_state(pair, t0 + 2700, running_intraday)
    _require(st3.get("active_mode") == "intraday", "running mode should remain intraday on first running tick")

    st4 = brain._regime_router_state(pair, t0 + 3600, running_swing)
    _require(st4.get("active_mode") == "intraday", "router must not switch mode while running inventory")
    _require(
        bool(st4.get("handoff_blocked_running_inventory")),
        "router should mark handoff blocked while running inventory",
    )
    _require(st4.get("desired_mode") == "swing", "router should still report desired swing mode")

    st5 = brain._regime_router_state(pair, t0 + 4500, swing_features)
    _require(st5.get("active_mode") == "intraday", "router should require persistence before switching to swing")
    st6 = brain._regime_router_state(pair, t0 + 5400, swing_features)
    _require(st6.get("active_mode") == "swing", "router should switch to swing after persistence when not running")
    _require(bool(st6.get("switched")), "router should report swing handoff")

    brain.regime_router_force_mode = "pause"
    st7 = brain._regime_router_state(pair, t0 + 6300, intraday_features)
    _require(st7.get("active_mode") == "pause", "forced pause mode should override score-based selection")
    _require(st7.get("target_reason") == "forced_mode", "forced mode reason should be explicit")

    print("[regression] check: regime router mode selection + handoff OK")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True, help="Path to latest generated plan json")
    ap.add_argument("--state-out", default="/tmp/grid_executor_v1.regression.state.json")
    ap.add_argument("--quote-budget", type=float, default=1000.0)
    ap.add_argument("--maker-fee-pct", type=float, default=0.10)
    args = ap.parse_args()

    plan_path = Path(args.plan)
    if not plan_path.is_file():
        raise FileNotFoundError(f"Plan not found: {plan_path}")

    with plan_path.open("r", encoding="utf-8") as f:
        plan = json.load(f)

    check_recent_plan_history(plan_path)
    check_plan_schema_and_feature_outputs(plan)
    check_ml_overlay_behavior()
    check_adx_hysteresis_behavior()
    check_mode_router_handoff_behavior()
    check_executor_action_semantics(plan, args.state_out, args.quote_budget, args.maker_fee_pct)
    check_weighted_ladder_and_simulator(plan, args.quote_budget, args.maker_fee_pct)

    print("[regression] all checks passed")


if __name__ == "__main__":
    main()
