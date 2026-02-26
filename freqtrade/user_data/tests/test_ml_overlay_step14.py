# ruff: noqa: S101

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

from freqtrade.user_data.strategies.GridBrainV1 import GridBrainV1Core

LABELS_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "run-user-ml-labels.py"
ML_WF_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "run-user-ml-walkforward.py"
ML_COMPARE_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "run-user-ml-overlay-compare.py"
TP_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "run-user-tuning-protocol.py"


def _window(index: int, pnl_pct: float, stop_events: int, *, status: str = "ok") -> Dict[str, Any]:
    pnl_quote = float(pnl_pct * 10.0)
    return {
        "index": int(index),
        "status": str(status),
        "timerange": f"202001{index:02d}-202001{index + 1:02d}",
        "pnl_quote": float(pnl_quote),
        "pnl_pct": float(pnl_pct),
        "stop_events": int(stop_events),
        "action_start": 20,
        "seed_events": 2,
        "rebuild_events": 1,
        "fills": 20,
        "soft_adjust_events": 1,
    }


def _write_summary(user_data: Path, run_id: str, windows: List[Dict[str, Any]]) -> None:
    run_dir = user_data / "walkforward" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    ok = [w for w in windows if str(w.get("status", "")).lower() == "ok"]
    pnl = [float(w.get("pnl_quote", 0.0)) for w in ok]
    wins = [x for x in pnl if x > 0.0]
    losses = [x for x in pnl if x < 0.0]
    profit_factor = float(sum(wins) / abs(sum(losses))) if losses else 999.0

    summary = {
        "created_utc": "2026-02-26T00:00:00+00:00",
        "run_id": run_id,
        "args": {
            "strategy": "GridBrainV1",
            "pair": "ETH/USDT",
            "timeframe": "15m",
            "timerange": "20200101-20200301",
        },
        "aggregate": {
            "windows_total": int(len(windows)),
            "windows_ok": int(len(ok)),
            "windows_failed": int(len(windows) - len(ok)),
            "sum_pnl_quote": float(sum(pnl)),
            "avg_pnl_pct": float(sum(float(w.get("pnl_pct", 0.0)) for w in ok) / max(1, len(ok))),
            "median_pnl_pct": float(sorted(float(w.get("pnl_pct", 0.0)) for w in ok)[len(ok) // 2]) if ok else 0.0,
            "win_rate": float(100.0 * len(wins) / max(1, len(ok))),
            "profit_factor": float(profit_factor),
            "max_gain_pct": float(max([float(w.get("pnl_pct", 0.0)) for w in ok] or [0.0])),
            "max_loss_pct": float(min([float(w.get("pnl_pct", 0.0)) for w in ok] or [0.0])),
        },
        "windows": windows,
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_schema(path: Path) -> None:
    payload = {
        "version": 1,
        "required_root_fields": ["created_utc", "run_id", "experiments_total", "experiments", "promotions", "strict_failures"],
        "required_experiment_fields": [
            "experiment_id",
            "run_id",
            "slot",
            "status",
            "metrics",
            "oos_gate",
            "ablation_gate",
            "chaos_gate",
            "rank_stability_gate",
            "ml_overlay_gate",
            "promoted",
        ],
        "required_metrics_fields": [
            "windows_ok",
            "windows_failed",
            "sum_pnl_quote",
            "avg_pnl_pct",
            "win_rate",
            "profit_factor",
            "churn_events_per_window",
            "false_start_rate",
            "stop_events_per_window",
            "rank_stability_jaccard",
        ],
        "required_gate_fields": ["passed", "checks"],
    }
    _write_json(path, payload)


def test_step14_ml_scripts_pipeline(tmp_path: Path) -> None:
    user_data = tmp_path / "user_data"

    det_windows = []
    ml_windows = []
    for i in range(1, 17):
        if i % 4 in (1, 2):
            det_windows.append(_window(i, pnl_pct=0.6, stop_events=3))
            ml_windows.append(_window(i, pnl_pct=0.8, stop_events=2))
        else:
            det_windows.append(_window(i, pnl_pct=-0.4, stop_events=14))
            ml_windows.append(_window(i, pnl_pct=-0.2, stop_events=10))

    _write_summary(user_data, "wf_det", det_windows)
    _write_summary(user_data, "wf_ml", ml_windows)

    labels_cmd = [
        sys.executable,
        str(LABELS_SCRIPT),
        "--user-data",
        str(user_data),
        "--walkforward-run-id",
        "wf_det",
        "--run-id",
        "labels_test",
        "--horizon-windows",
        "1",
        "--min-train-samples",
        "6",
    ]
    res_labels = subprocess.run(labels_cmd, capture_output=True, text=True, check=False)
    assert res_labels.returncode == 0, res_labels.stderr + "\n" + res_labels.stdout

    labels_summary = json.loads(
        (user_data / "ml_overlay" / "labels" / "labels_test" / "summary.json").read_text(encoding="utf-8")
    )
    assert int(labels_summary["rows_valid"]) > 0
    assert int(labels_summary["leakage_checks"]["violations"]) == 0

    eval_cmd = [
        sys.executable,
        str(ML_WF_SCRIPT),
        "--user-data",
        str(user_data),
        "--labels-run-id",
        "labels_test",
        "--run-id",
        "ml_eval_test",
        "--min-train-samples",
        "6",
        "--min-range-auc",
        "0.0",
        "--min-breakout-auc",
        "0.0",
        "--max-range-brier",
        "1.0",
        "--max-breakout-brier",
        "1.0",
        "--max-range-ece",
        "1.0",
        "--max-breakout-ece",
        "1.0",
        "--min-coverage",
        "0.0",
    ]
    res_eval = subprocess.run(eval_cmd, capture_output=True, text=True, check=False)
    assert res_eval.returncode == 0, res_eval.stderr + "\n" + res_eval.stdout

    eval_summary = json.loads(
        (user_data / "ml_overlay" / "walkforward" / "ml_eval_test" / "summary.json").read_text(encoding="utf-8")
    )
    assert bool(eval_summary["gates"]["passed"])
    assert int(eval_summary["predictions_total"]) > 0

    compare_cmd = [
        sys.executable,
        str(ML_COMPARE_SCRIPT),
        "--user-data",
        str(user_data),
        "--run-det",
        "wf_det",
        "--run-ml",
        "wf_ml",
        "--run-id",
        "ml_compare_test",
        "--ml-eval-run-id",
        "ml_eval_test",
        "--require-ml-eval-pass",
        "--max-churn-degradation-pct",
        "80",
        "--max-false-start-degradation-pct",
        "80",
        "--max-stop-events-multiplier",
        "2.0",
    ]
    res_compare = subprocess.run(compare_cmd, capture_output=True, text=True, check=False)
    assert res_compare.returncode == 0, res_compare.stderr + "\n" + res_compare.stdout

    compare_summary = json.loads(
        (user_data / "ml_overlay" / "compare" / "ml_compare_test" / "summary.json").read_text(encoding="utf-8")
    )
    assert bool(compare_summary["gates"]["passed"])


def test_tuning_protocol_respects_required_ml_overlay_gate(tmp_path: Path) -> None:
    user_data = tmp_path / "user_data"
    wins_base = [_window(i, pnl_pct=0.2, stop_events=4) for i in range(1, 11)]
    wins_candidate = [_window(i, pnl_pct=0.45, stop_events=3) for i in range(1, 11)]
    _write_summary(user_data, "wf_base", wins_base)
    _write_summary(user_data, "wf_candidate", wins_candidate)
    _write_summary(user_data, "wf_ablation", wins_base)
    _write_summary(user_data, "wf_chaos", wins_base)

    _write_json(
        user_data / "ml_overlay" / "walkforward" / "ml_eval_ok" / "summary.json",
        {
            "run_id": "ml_eval_ok",
            "targets": {
                "range_continuation": {"auc": 0.6, "brier": 0.2, "ece": 0.1, "coverage": 0.5},
                "breakout_risk": {"auc": 0.6, "brier": 0.2, "ece": 0.1, "coverage": 0.5},
            },
            "gates": {"passed": True},
        },
    )
    _write_json(
        user_data / "ml_overlay" / "compare" / "ml_cmp_fail" / "summary.json",
        {
            "run_id": "ml_cmp_fail",
            "gates": {"passed": False},
        },
    )

    manifest = {
        "version": 1,
        "defaults": {
            "oos_gates": {"min_oos_windows_ok": 8, "min_profit_factor": 1.0},
            "ablation_gates": {"enabled": True, "min_required": 1, "max_avg_pnl_pct_drop": 10.0},
            "chaos_gates": {"enabled": True, "min_profiles": 1, "max_avg_pnl_pct_degradation": 10.0, "max_stop_events_multiplier": 5.0},
            "ml_overlay_gates": {
                "enabled": True,
                "require_ml_eval_pass": True,
                "require_compare_pass": True,
                "min_range_auc": 0.5,
                "min_breakout_auc": 0.5,
                "max_range_brier": 1.0,
                "max_breakout_brier": 1.0,
                "max_range_ece": 1.0,
                "max_breakout_ece": 1.0,
                "min_range_coverage": 0.0,
                "min_breakout_coverage": 0.0,
            },
            "promotion": {
                "objective_metric": "avg_pnl_pct",
                "objective_improvement_min": 0.01,
                "require_chaos_pass": True,
                "require_ablation_pass": True,
                "require_rank_stability_pass": False,
                "require_ml_overlay_pass": True,
            },
        },
        "experiments": [
            {
                "id": "candidate_ml_required",
                "enabled": True,
                "slot": "GridBrainV1|ETH/USDT|15m",
                "walkforward": {"run_id": "wf_candidate"},
                "baseline": {"run_id": "wf_base"},
                "ablations": [{"id": "ablation", "run_id": "wf_ablation", "required": True}],
                "chaos": {"profiles": [{"name": "chaos", "run_id": "wf_chaos", "required": True}]},
                "ml_overlay_eval": {"run_id": "ml_eval_ok"},
                "ml_overlay_compare": {"run_id": "ml_cmp_fail"},
            }
        ],
    }

    manifest_path = tmp_path / "experiments" / "manifest.yaml"
    champions_path = tmp_path / "experiments" / "champions.json"
    schema_path = tmp_path / "experiments" / "metrics_schema.json"
    _write_json(manifest_path, manifest)
    _write_schema(schema_path)
    _write_json(
        champions_path,
        {
            "version": 1,
            "updated_utc": "",
            "champions": {
                "GridBrainV1|ETH/USDT|15m": {
                    "run_id": "wf_base",
                    "experiment_id": "baseline",
                    "metrics": {"avg_pnl_pct": 0.2},
                }
            },
            "history": [],
        },
    )

    cmd = [
        sys.executable,
        str(TP_SCRIPT),
        "--manifest",
        str(manifest_path),
        "--champions",
        str(champions_path),
        "--metrics-schema",
        str(schema_path),
        "--user-data",
        str(user_data),
        "--run-id",
        "tp_ml_gate_fail",
        "--strict",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert res.returncode == 1

    tp_summary = json.loads(
        (user_data / "experiments" / "tuning_protocol" / "tp_ml_gate_fail" / "summary.json").read_text(
            encoding="utf-8"
        )
    )
    exp_row = tp_summary["experiments"][0]
    assert not bool(exp_row["ml_overlay_gate"]["passed"])
    assert not bool(exp_row["promoted"])


def test_ml_overlay_defaults_are_advisory_and_off() -> None:
    assert GridBrainV1Core.freqai_overlay_enabled is False
    assert str(GridBrainV1Core.freqai_overlay_gate_mode) == "advisory"
