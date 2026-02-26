# ruff: noqa: S101

import json
import subprocess
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "run-user-tuning-protocol.py"


def _write_summary(
    user_data: Path,
    run_id: str,
    *,
    windows_ok: int,
    windows_failed: int,
    sum_pnl_quote: float,
    avg_pnl_pct: float,
    median_pnl_pct: float,
    win_rate: float,
    profit_factor: float,
    stop_events_total: int,
    action_start_total: int,
    seed_events_total: int,
    rebuild_events_total: int,
) -> None:
    run_dir = user_data / "walkforward" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    windows = []
    def _spread(total: int, n: int, floor_each: int = 0) -> list[int]:
        n = max(1, int(n))
        base, extra = divmod(max(0, int(total)), n)
        vals = [max(int(base), int(floor_each)) for _ in range(n)]
        for i in range(extra):
            vals[i % n] += 1
        return vals

    stop_vals = _spread(stop_events_total, windows_ok, floor_each=0)
    start_vals = _spread(action_start_total, windows_ok, floor_each=1)
    seed_vals = _spread(seed_events_total, windows_ok, floor_each=0)
    rebuild_vals = _spread(rebuild_events_total, windows_ok, floor_each=0)

    for i in range(int(windows_ok)):
        windows.append(
            {
                "index": i + 1,
                "status": "ok",
                "pnl_quote": float(sum_pnl_quote / max(1, windows_ok)),
                "pnl_pct": float(avg_pnl_pct),
                "stop_events": int(stop_vals[i]),
                "action_start": int(start_vals[i]),
                "seed_events": int(seed_vals[i]),
                "rebuild_events": int(rebuild_vals[i]),
                "start_blocker_counts": {"gate_fail:bbwp_gate_ok": 2},
                "stop_reason_counts_combined": {"event:PLAN_STOP": 1},
            }
        )

    summary = {
        "created_utc": "2026-02-26T00:00:00+00:00",
        "args": {
            "pair": "ETH/USDT",
            "timeframe": "15m",
            "strategy": "GridBrainV1",
        },
        "aggregate": {
            "windows_total": int(windows_ok + windows_failed),
            "windows_ok": int(windows_ok),
            "windows_failed": int(windows_failed),
            "sum_pnl_quote": float(sum_pnl_quote),
            "avg_pnl_pct": float(avg_pnl_pct),
            "median_pnl_pct": float(median_pnl_pct),
            "win_rate": float(win_rate),
            "profit_factor": float(profit_factor),
            "max_gain_pct": float(avg_pnl_pct + 1.0),
            "max_loss_pct": float(avg_pnl_pct - 1.0),
        },
        "windows": windows,
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


def _write_manifest(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_registry(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_schema(path: Path) -> None:
    payload = {
        "version": 1,
        "required_root_fields": [
            "created_utc",
            "run_id",
            "experiments_total",
            "experiments",
            "promotions",
            "strict_failures",
        ],
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _run_protocol(
    user_data: Path,
    manifest_path: Path,
    champions_path: Path,
    schema_path: Path,
    run_id: str,
    *,
    strict: bool = False,
) -> subprocess.CompletedProcess:
    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "--manifest",
        str(manifest_path),
        "--champions",
        str(champions_path),
        "--metrics-schema",
        str(schema_path),
        "--user-data",
        str(user_data),
        "--run-id",
        run_id,
    ]
    if strict:
        cmd.append("--strict")
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def test_tuning_protocol_promotes_candidate_with_passed_gates(tmp_path: Path) -> None:
    user_data = tmp_path / "user_data"
    _write_summary(
        user_data,
        "wf_baseline",
        windows_ok=8,
        windows_failed=0,
        sum_pnl_quote=100.0,
        avg_pnl_pct=0.10,
        median_pnl_pct=0.11,
        win_rate=50.0,
        profit_factor=1.20,
        stop_events_total=8,
        action_start_total=24,
        seed_events_total=8,
        rebuild_events_total=4,
    )
    _write_summary(
        user_data,
        "wf_candidate",
        windows_ok=8,
        windows_failed=0,
        sum_pnl_quote=180.0,
        avg_pnl_pct=0.25,
        median_pnl_pct=0.22,
        win_rate=57.0,
        profit_factor=1.35,
        stop_events_total=7,
        action_start_total=24,
        seed_events_total=7,
        rebuild_events_total=4,
    )
    _write_summary(
        user_data,
        "wf_candidate_ablation_meta_off",
        windows_ok=8,
        windows_failed=0,
        sum_pnl_quote=150.0,
        avg_pnl_pct=-0.50,
        median_pnl_pct=-0.45,
        win_rate=49.0,
        profit_factor=1.10,
        stop_events_total=8,
        action_start_total=24,
        seed_events_total=8,
        rebuild_events_total=4,
    )
    _write_summary(
        user_data,
        "wf_candidate_chaos",
        windows_ok=8,
        windows_failed=0,
        sum_pnl_quote=140.0,
        avg_pnl_pct=-1.80,
        median_pnl_pct=-1.75,
        win_rate=48.0,
        profit_factor=1.06,
        stop_events_total=10,
        action_start_total=24,
        seed_events_total=8,
        rebuild_events_total=4,
    )

    manifest_path = tmp_path / "experiments" / "manifest.yaml"
    champions_path = tmp_path / "experiments" / "champions.json"
    schema_path = tmp_path / "experiments" / "metrics_schema.json"
    _write_schema(schema_path)

    _write_manifest(
        manifest_path,
        {
            "version": 1,
            "defaults": {
                "oos_gates": {
                    "min_oos_windows_ok": 8,
                    "min_profit_factor": 1.05,
                    "max_churn_degradation_pct": 30.0,
                    "max_false_start_degradation_pct": 30.0,
                },
                "ablation_gates": {
                    "enabled": True,
                    "min_required": 1,
                    "max_avg_pnl_pct_drop": 4.0,
                },
                "chaos_gates": {
                    "enabled": True,
                    "min_profiles": 1,
                    "max_avg_pnl_pct_degradation": 3.0,
                    "max_stop_events_multiplier": 1.5,
                },
                "promotion": {
                    "objective_metric": "avg_pnl_pct",
                    "objective_improvement_min": 0.05,
                },
            },
            "experiments": [
                {
                    "id": "candidate_main",
                    "enabled": True,
                    "slot": "GridBrainV1|ETH/USDT|15m",
                    "walkforward": {"run_id": "wf_candidate"},
                    "baseline": {"run_id": "wf_baseline"},
                    "ablations": [
                        {
                            "id": "meta_off",
                            "run_id": "wf_candidate_ablation_meta_off",
                            "required": True,
                        }
                    ],
                    "chaos": {
                        "profiles": [
                            {
                                "name": "latency_spread",
                                "run_id": "wf_candidate_chaos",
                                "required": True,
                            }
                        ]
                    },
                }
            ],
        },
    )

    _write_registry(
        champions_path,
        {
            "version": 1,
            "updated_utc": "",
            "champions": {
                "GridBrainV1|ETH/USDT|15m": {
                    "run_id": "wf_baseline",
                    "experiment_id": "baseline",
                    "metrics": {"avg_pnl_pct": 0.10},
                }
            },
            "history": [],
        },
    )

    res = _run_protocol(
        user_data,
        manifest_path,
        champions_path,
        schema_path,
        "tp_success",
        strict=True,
    )
    assert res.returncode == 0, res.stderr + "\n" + res.stdout

    champions = json.loads(champions_path.read_text(encoding="utf-8"))
    slot = champions["champions"]["GridBrainV1|ETH/USDT|15m"]
    assert slot["run_id"] == "wf_candidate"

    summary = json.loads(
        (user_data / "experiments" / "tuning_protocol" / "tp_success" / "summary.json").read_text(
            encoding="utf-8"
        )
    )
    assert summary["experiments"][0]["promoted"] is True


def test_tuning_protocol_strict_fails_when_chaos_gate_fails(tmp_path: Path) -> None:
    user_data = tmp_path / "user_data"
    _write_summary(
        user_data,
        "wf_base",
        windows_ok=8,
        windows_failed=0,
        sum_pnl_quote=100.0,
        avg_pnl_pct=0.10,
        median_pnl_pct=0.11,
        win_rate=50.0,
        profit_factor=1.20,
        stop_events_total=8,
        action_start_total=24,
        seed_events_total=8,
        rebuild_events_total=4,
    )
    _write_summary(
        user_data,
        "wf_candidate_fail_chaos",
        windows_ok=8,
        windows_failed=0,
        sum_pnl_quote=150.0,
        avg_pnl_pct=0.20,
        median_pnl_pct=0.19,
        win_rate=55.0,
        profit_factor=1.30,
        stop_events_total=8,
        action_start_total=24,
        seed_events_total=8,
        rebuild_events_total=4,
    )
    _write_summary(
        user_data,
        "wf_candidate_fail_chaos_ablation",
        windows_ok=8,
        windows_failed=0,
        sum_pnl_quote=130.0,
        avg_pnl_pct=-1.00,
        median_pnl_pct=-1.00,
        win_rate=48.0,
        profit_factor=1.08,
        stop_events_total=9,
        action_start_total=24,
        seed_events_total=8,
        rebuild_events_total=4,
    )
    _write_summary(
        user_data,
        "wf_candidate_fail_chaos_profile",
        windows_ok=8,
        windows_failed=1,
        sum_pnl_quote=20.0,
        avg_pnl_pct=-10.0,
        median_pnl_pct=-9.5,
        win_rate=32.0,
        profit_factor=0.70,
        stop_events_total=30,
        action_start_total=24,
        seed_events_total=8,
        rebuild_events_total=4,
    )

    manifest_path = tmp_path / "experiments" / "manifest.yaml"
    champions_path = tmp_path / "experiments" / "champions.json"
    schema_path = tmp_path / "experiments" / "metrics_schema.json"
    _write_schema(schema_path)

    _write_manifest(
        manifest_path,
        {
            "version": 1,
            "defaults": {},
            "experiments": [
                {
                    "id": "candidate_fail",
                    "enabled": True,
                    "slot": "GridBrainV1|ETH/USDT|15m",
                    "walkforward": {"run_id": "wf_candidate_fail_chaos"},
                    "baseline": {"run_id": "wf_base"},
                    "ablations": [
                        {
                            "id": "meta_off",
                            "run_id": "wf_candidate_fail_chaos_ablation",
                            "required": True,
                        }
                    ],
                    "chaos": {
                        "profiles": [
                            {
                                "name": "stress",
                                "run_id": "wf_candidate_fail_chaos_profile",
                                "required": True,
                            }
                        ]
                    },
                }
            ],
        },
    )

    _write_registry(
        champions_path,
        {
            "version": 1,
            "updated_utc": "",
            "champions": {
                "GridBrainV1|ETH/USDT|15m": {
                    "run_id": "wf_base",
                    "experiment_id": "baseline",
                    "metrics": {"avg_pnl_pct": 0.10},
                }
            },
            "history": [],
        },
    )

    res = _run_protocol(
        user_data,
        manifest_path,
        champions_path,
        schema_path,
        "tp_fail_chaos",
        strict=True,
    )
    assert res.returncode == 1

    champions = json.loads(champions_path.read_text(encoding="utf-8"))
    assert champions["champions"]["GridBrainV1|ETH/USDT|15m"]["run_id"] == "wf_base"


def test_tuning_protocol_strict_fails_when_required_ablation_missing(tmp_path: Path) -> None:
    user_data = tmp_path / "user_data"
    _write_summary(
        user_data,
        "wf_base_ablation",
        windows_ok=8,
        windows_failed=0,
        sum_pnl_quote=100.0,
        avg_pnl_pct=0.10,
        median_pnl_pct=0.10,
        win_rate=50.0,
        profit_factor=1.20,
        stop_events_total=8,
        action_start_total=24,
        seed_events_total=8,
        rebuild_events_total=4,
    )
    _write_summary(
        user_data,
        "wf_candidate_missing_ablation",
        windows_ok=8,
        windows_failed=0,
        sum_pnl_quote=170.0,
        avg_pnl_pct=0.30,
        median_pnl_pct=0.25,
        win_rate=58.0,
        profit_factor=1.35,
        stop_events_total=8,
        action_start_total=24,
        seed_events_total=8,
        rebuild_events_total=4,
    )
    _write_summary(
        user_data,
        "wf_candidate_missing_ablation_chaos",
        windows_ok=8,
        windows_failed=0,
        sum_pnl_quote=140.0,
        avg_pnl_pct=-2.0,
        median_pnl_pct=-1.9,
        win_rate=46.0,
        profit_factor=1.06,
        stop_events_total=10,
        action_start_total=24,
        seed_events_total=8,
        rebuild_events_total=4,
    )

    manifest_path = tmp_path / "experiments" / "manifest.yaml"
    champions_path = tmp_path / "experiments" / "champions.json"
    schema_path = tmp_path / "experiments" / "metrics_schema.json"
    _write_schema(schema_path)

    _write_manifest(
        manifest_path,
        {
            "version": 1,
            "defaults": {},
            "experiments": [
                {
                    "id": "candidate_missing_ablation",
                    "enabled": True,
                    "slot": "GridBrainV1|ETH/USDT|15m",
                    "walkforward": {"run_id": "wf_candidate_missing_ablation"},
                    "baseline": {"run_id": "wf_base_ablation"},
                    "ablations": [
                        {
                            "id": "required_but_missing",
                            "run_id": "wf_does_not_exist",
                            "required": True,
                        }
                    ],
                    "chaos": {
                        "profiles": [
                            {
                                "name": "stress",
                                "run_id": "wf_candidate_missing_ablation_chaos",
                                "required": True,
                            }
                        ]
                    },
                }
            ],
        },
    )

    _write_registry(
        champions_path,
        {
            "version": 1,
            "updated_utc": "",
            "champions": {
                "GridBrainV1|ETH/USDT|15m": {
                    "run_id": "wf_base_ablation",
                    "experiment_id": "baseline",
                    "metrics": {"avg_pnl_pct": 0.10},
                }
            },
            "history": [],
        },
    )

    res = _run_protocol(
        user_data,
        manifest_path,
        champions_path,
        schema_path,
        "tp_fail_ablation",
        strict=True,
    )
    assert res.returncode == 1

    summary = json.loads(
        (user_data / "experiments" / "tuning_protocol" / "tp_fail_ablation" / "summary.json").read_text(
            encoding="utf-8"
        )
    )
    assert summary["experiments"][0]["ablation_gate"]["passed"] is False
