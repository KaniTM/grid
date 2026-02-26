from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from analytics.execution_cost_calibrator import EmpiricalCostCalibrator
from core.atomic_json import read_json_object, write_json_atomic
from data.data_quality_assessor import assess_data_quality
from execution.capacity_guard import compute_dynamic_capacity_state, load_capacity_hint_state
from planner.replan_policy import ReplanThresholds, evaluate_replan_materiality
from planner.start_stability import evaluate_start_stability
from planner.volatility_policy_adapter import compute_n_level_bounds, compute_volatility_policy_view
from schemas.plan_signature import compute_plan_hash, validate_signature_fields
from sim.chaos_profiles import default_chaos_profile, validate_chaos_profile


def test_start_stability_module() -> None:
    out = evaluate_start_stability([("a", True), ("b", False), ("c", True)], 0.5, 0.5)
    assert out["ok"] is True
    assert out["passed"] == 2
    assert out["total"] == 3


def test_replan_policy_module() -> None:
    out = evaluate_replan_materiality(
        prev_mid=100.0,
        prev_width_pct=0.05,
        prev_tp=105.0,
        prev_sl=95.0,
        epoch_counter=1,
        thresholds=ReplanThresholds(
            epoch_bars=2,
            box_mid_shift_max_step_frac=0.5,
            box_width_change_pct=5.0,
            tp_shift_max_step_frac=0.75,
            sl_shift_max_step_frac=0.75,
        ),
        mid=101.0,
        width_pct=0.05,
        step_price=1.0,
        tp_price=105.0,
        sl_price=95.0,
        hard_stop=False,
        action="HOLD",
    )
    assert out["publish"] is True
    assert str(out["class"]) == "material"


def test_volatility_adapter_module() -> None:
    n_low, n_high, diag = compute_n_level_bounds(
        n_min=6,
        n_max=12,
        active_mode="intraday",
        adapter_enabled=True,
        atr_mode_pct=0.03,
        atr_mode_max=0.01,
        adapter_strength=1.0,
    )
    assert n_low == 6
    assert n_high < 12
    assert diag["adjustment"] > 0


def test_volatility_adapter_runtime_view_fields() -> None:
    out = compute_volatility_policy_view(
        active_mode="intraday",
        adapter_enabled=True,
        adapter_strength=1.0,
        atr_pct_15m=0.03,
        atr_pct_1h=0.04,
        atr_mode_pct=0.04,
        atr_mode_max=0.015,
        bbwp_s=96.0,
        bbwp_m=94.0,
        bbwp_l=92.0,
        squeeze_on_1h=False,
        hvp_state="expanding",
        base_n_min=6,
        base_n_max=12,
        base_box_width_min_pct=0.035,
        base_box_width_max_pct=0.060,
        base_min_step_buffer_bps=0.0,
        base_cooldown_minutes=90.0,
        base_min_runtime_minutes=180.0,
    )
    assert out["vol_bucket"] == "unstable"
    adapted = out["adapted"]
    assert int(adapted["n_max"]) <= 12
    assert float(adapted["box_width_max_pct"]) >= 0.060
    assert float(adapted["min_step_buffer_bps"]) > 0.0
    assert bool(adapted["build_strictness"]["vol_bucket_block_start"]) is True


def test_capacity_guard_module(tmp_path: Path) -> None:
    path = tmp_path / "capacity.json"
    path.write_text(
        json.dumps({"ETH/USDT": {"allow_start": False, "reason": "thin", "preferred_rung_cap": 8}}),
        encoding="utf-8",
    )
    out = load_capacity_hint_state(
        "ETH/USDT",
        capacity_hint_path=str(path),
        capacity_hint_hard_block=True,
    )
    assert out["available"] is True
    assert out["allow_start"] is False
    assert out["reason"] == "thin"
    assert out["advisory_only"] is False


def test_dynamic_capacity_guard_computes_cap_and_delay() -> None:
    out = compute_dynamic_capacity_state(
        max_orders_per_side=20,
        n_levels=10,
        quote_total=1000.0,
        grid_budget_pct=1.0,
        preferred_rung_cap=8,
        runtime_spread_pct=0.01,
        runtime_depth_thinning_score=0.8,
        top_book_notional=50.0,
        runtime_capacity_ok=True,
        runtime_reasons=[],
        spread_wide_threshold=0.002,
        depth_thin_threshold=0.5,
        spread_cap_multiplier=0.5,
        depth_cap_multiplier=0.5,
        min_rung_cap=1,
        top_book_safety_fraction=0.2,
        delay_replenish_on_thin=True,
    )
    assert out["capacity_ok"] is True
    assert out["applied_rung_cap"] >= 1
    assert out["rung_cap_applied"] is True
    assert "DEPTH_THIN_AT_TOP" in out["reasons"]
    assert out["delay_replenishment"] is True


def test_data_quality_assessor_module() -> None:
    start = datetime.now(timezone.utc) - timedelta(minutes=45)
    dates = [start + timedelta(minutes=15 * i) for i in range(4)]
    df = pd.DataFrame(
        {
            "date": dates,
            "volume": [1.0, 1.0, 1.0, 1.0],
            "bb_mid_1h": [100.0, 100.0, 100.0, 100.0],
            "bb_mid_4h": [100.0, 100.0, 100.0, 100.0],
        }
    )
    out = assess_data_quality(
        df,
        expected_candle_seconds=900,
        gap_multiplier=1.5,
        max_stale_minutes=120,
        zero_volume_streak_bars=3,
    )
    assert out["ok"] is True
    assert out["reasons"] == []


def test_execution_cost_calibrator_module() -> None:
    cal = EmpiricalCostCalibrator(window=16)
    for _ in range(10):
        cal.observe(
            "ETH/USDT",
            spread_pct=0.001,
            adverse_selection_pct=0.0003,
            retry_reject_rate=0.1,
            missed_fill_rate=0.2,
            retry_penalty_pct=0.0002,
            missed_fill_penalty_pct=0.0004,
        )
    snap = cal.snapshot("ETH/USDT", percentile=75, min_samples=5, stale_bars=100)
    assert snap["sample_count"] == 10
    assert snap["empirical_floor_pct"] is not None
    assert snap["stale"] is False


def test_chaos_profile_and_plan_signature_wrappers() -> None:
    profile = default_chaos_profile()
    assert validate_chaos_profile(profile) == []

    plan = {
        "schema_version": "1.0.0",
        "planner_version": "gridbrain_v1",
        "pair": "ETH/USDT",
        "exchange": "binance",
        "plan_id": "00000000-0000-0000-0000-000000000001",
        "decision_seq": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "valid_for_candle_ts": 1700000000,
        "materiality_class": "soft",
        "action": "HOLD",
        "mode": "intraday",
        "replan_decision": "publish",
        "replan_reasons": ["REPLAN_NOOP_MINOR_DELTA"],
        "box": {"low": 100, "high": 110, "mid": 105, "width_pct": 0.1},
        "grid": {"n_levels": 8, "step_price": 1.25},
        "risk": {"tp_price": 112, "sl_price": 98},
        "capital_policy": {},
        "update_policy": {},
    }
    plan["plan_hash"] = compute_plan_hash(plan)
    assert validate_signature_fields(plan) == []


def test_atomic_json_wrapper_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "atomic.json"
    payload = {"ok": True, "value": 42}
    write_json_atomic(path, payload)
    out = read_json_object(path)
    assert out == payload
