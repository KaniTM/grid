#!/usr/bin/env python3
"""
Formal tuning protocol runner.

This enforces a deterministic promotion workflow using:
- experiment manifests
- champion/challenger registry
- walk-forward + ablation result automation hooks
- OOS promotion gates
- chaos-profile validation gate
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from latest_refs import publish_latest_ref, rel_payload_path

REPO_ROOT = Path(__file__).resolve().parents[2]
FREQTRADE_ROOT = REPO_ROOT / "freqtrade"
DEFAULT_USER_DATA = FREQTRADE_ROOT / "user_data"
DEFAULT_MANIFEST = REPO_ROOT / "experiments" / "manifest.yaml"
DEFAULT_CHAMPIONS = REPO_ROOT / "experiments" / "champions.json"
DEFAULT_METRICS_SCHEMA = REPO_ROOT / "experiments" / "metrics_schema.json"

DEFAULT_OOS_GATES: Dict[str, Any] = {
    "min_oos_windows_ok": 8,
    "max_failed_windows": 0,
    "min_sum_pnl_quote": 0.0,
    "min_avg_pnl_pct": 0.0,
    "min_win_rate_pct": 45.0,
    "min_profit_factor": 1.05,
    "max_churn_degradation_pct": 20.0,
    "max_false_start_degradation_pct": 25.0,
}

DEFAULT_ABLATION_GATES: Dict[str, Any] = {
    "enabled": True,
    "min_required": 1,
    "max_avg_pnl_pct_drop": 4.0,
}

DEFAULT_CHAOS_GATES: Dict[str, Any] = {
    "enabled": True,
    "min_profiles": 1,
    "max_failed_windows": 0,
    "max_avg_pnl_pct_degradation": 3.0,
    "max_stop_events_multiplier": 1.5,
}

DEFAULT_RANK_STABILITY: Dict[str, Any] = {
    "enabled": True,
    "top_k": 3,
    "min_jaccard": 0.20,
}

DEFAULT_PROMOTION: Dict[str, Any] = {
    "objective_metric": "avg_pnl_pct",
    "objective_improvement_min": 0.05,
    "require_chaos_pass": True,
    "require_ablation_pass": True,
    "require_rank_stability_pass": True,
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None or v == "":
            return float(default)
        return float(v)
    except Exception:
        return float(default)


def _to_int(v: Any, default: int = 0) -> int:
    try:
        if v is None or v == "":
            return int(default)
        return int(v)
    except Exception:
        return int(default)


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
    except Exception:
        return {}
    return {}


def _write_json_atomic(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _deep_merge(base: Dict[str, Any], override: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    out = deepcopy(base)
    if not isinstance(override, dict):
        return out
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out.get(k, {}), v)
        else:
            out[k] = v
    return out


def _load_manifest(path: Path) -> Dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(raw)
        if isinstance(payload, dict):
            return payload
    except Exception:
        pass

    # YAML support is optional; manifest can be JSON-valid YAML.
    try:
        import yaml  # type: ignore

        payload = yaml.safe_load(raw)
        if isinstance(payload, dict):
            return payload
    except Exception as exc:
        raise ValueError(f"Unable to parse manifest: {path} ({exc})") from exc

    raise ValueError(f"Manifest must be an object: {path}")


def _parse_count_map(raw: Any) -> Dict[str, int]:
    data = raw
    if isinstance(data, str):
        txt = data.strip()
        if not txt:
            return {}
        try:
            data = json.loads(txt)
        except Exception:
            return {}
    if not isinstance(data, dict):
        return {}
    out: Dict[str, int] = {}
    for k, v in data.items():
        key = str(k).strip()
        if not key:
            continue
        try:
            n = int(v)
        except Exception:
            continue
        if n <= 0:
            continue
        out[key] = n
    return out


def _merge_counts(counters: List[Dict[str, int]]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for c in counters:
        for k, v in (c or {}).items():
            out[k] = int(out.get(k, 0)) + int(v)
    return {k: int(v) for k, v in sorted(out.items(), key=lambda kv: (-int(kv[1]), str(kv[0])))}


def _top_keys(counter: Dict[str, int], top_k: int) -> List[str]:
    keys = sorted(counter.items(), key=lambda kv: (-int(kv[1]), str(kv[0])))
    return [str(k) for k, _ in keys[: max(0, int(top_k))]]


def _jaccard(a: List[str], b: List[str]) -> float:
    sa = set([str(x) for x in a if str(x).strip()])
    sb = set([str(x) for x in b if str(x).strip()])
    union = sa | sb
    if not union:
        return 1.0
    return float(len(sa & sb) / len(union))


def _summary_path(user_data: Path, run_id: str) -> Path:
    return user_data / "walkforward" / str(run_id).strip() / "summary.json"


def _load_summary(user_data: Path, run_id: str) -> Optional[Dict[str, Any]]:
    rid = str(run_id or "").strip()
    if not rid:
        return None
    path = _summary_path(user_data, rid)
    if not path.exists():
        return None
    payload = _read_json(path)
    return payload if payload else None


def _collect_metrics(summary: Dict[str, Any], run_id: str) -> Dict[str, Any]:
    agg = summary.get("aggregate", {}) if isinstance(summary.get("aggregate"), dict) else {}
    windows = summary.get("windows", []) if isinstance(summary.get("windows"), list) else []
    ok_rows = [w for w in windows if isinstance(w, dict) and str(w.get("status", "")).lower() == "ok"]

    pnl_quotes = [_to_float(w.get("pnl_quote")) for w in ok_rows]
    wins = [x for x in pnl_quotes if x > 0.0]
    losses = [x for x in pnl_quotes if x < 0.0]

    sum_seed = sum(_to_int(w.get("seed_events")) for w in ok_rows)
    sum_rebuild = sum(_to_int(w.get("rebuild_events")) for w in ok_rows)
    sum_stop = sum(_to_int(w.get("stop_events")) for w in ok_rows)
    sum_action_start = sum(_to_int(w.get("action_start")) for w in ok_rows)

    windows_ok = int(agg.get("windows_ok", len(ok_rows)) or len(ok_rows))
    windows_failed = int(agg.get("windows_failed", 0) or 0)

    start_blocker_counts_total = _merge_counts(
        [_parse_count_map(w.get("start_blocker_counts")) for w in ok_rows]
    )
    stop_reason_counts_total = _merge_counts(
        [_parse_count_map(w.get("stop_reason_counts_combined")) for w in ok_rows]
    )

    first_half = ok_rows[: max(1, len(ok_rows) // 2)]
    second_half = ok_rows[max(1, len(ok_rows) // 2) :]
    first_start_counts = _merge_counts([_parse_count_map(w.get("start_blocker_counts")) for w in first_half])
    second_start_counts = _merge_counts([_parse_count_map(w.get("start_blocker_counts")) for w in second_half])
    first_stop_counts = _merge_counts([_parse_count_map(w.get("stop_reason_counts_combined")) for w in first_half])
    second_stop_counts = _merge_counts([_parse_count_map(w.get("stop_reason_counts_combined")) for w in second_half])

    start_rank_jaccard = _jaccard(_top_keys(first_start_counts, 3), _top_keys(second_start_counts, 3))
    stop_rank_jaccard = _jaccard(_top_keys(first_stop_counts, 3), _top_keys(second_stop_counts, 3))
    rank_stability = float((start_rank_jaccard + stop_rank_jaccard) / 2.0)

    avg_pnl_pct = _to_float(agg.get("avg_pnl_pct"), default=0.0)
    win_rate = _to_float(agg.get("win_rate"), default=0.0)
    sum_pnl_quote = _to_float(agg.get("sum_pnl_quote"), default=0.0)
    profit_factor_raw = agg.get("profit_factor")
    profit_factor = _to_float(profit_factor_raw, default=0.0) if profit_factor_raw is not None else 0.0

    if profit_factor <= 0.0 and losses:
        profit_factor = float(sum(wins) / abs(sum(losses))) if wins else 0.0

    churn_total = int(sum_seed + sum_rebuild + sum_stop)
    churn_events_per_window = float(churn_total / max(1, windows_ok))
    false_start_rate = float(sum_stop / max(1, sum_action_start))
    stop_events_per_window = float(sum_stop / max(1, windows_ok))

    return {
        "run_id": str(run_id),
        "windows_total": int(agg.get("windows_total", len(windows)) or len(windows)),
        "windows_ok": int(windows_ok),
        "windows_failed": int(windows_failed),
        "sum_pnl_quote": float(sum_pnl_quote),
        "avg_pnl_pct": float(avg_pnl_pct),
        "median_pnl_pct": _to_float(agg.get("median_pnl_pct"), default=0.0),
        "win_rate": float(win_rate),
        "profit_factor": float(profit_factor),
        "max_loss_pct": _to_float(agg.get("max_loss_pct"), default=0.0),
        "max_gain_pct": _to_float(agg.get("max_gain_pct"), default=0.0),
        "seed_events": int(sum_seed),
        "rebuild_events": int(sum_rebuild),
        "stop_events": int(sum_stop),
        "action_start": int(sum_action_start),
        "churn_events_per_window": float(churn_events_per_window),
        "false_start_rate": float(false_start_rate),
        "stop_events_per_window": float(stop_events_per_window),
        "rank_stability_jaccard": float(rank_stability),
        "start_rank_jaccard": float(start_rank_jaccard),
        "stop_rank_jaccard": float(stop_rank_jaccard),
        "top_start_blocker": _top_keys(start_blocker_counts_total, 1)[0]
        if start_blocker_counts_total
        else "",
        "top_stop_reason": _top_keys(stop_reason_counts_total, 1)[0] if stop_reason_counts_total else "",
    }


def _check(name: str, passed: bool, observed: Any, threshold: Any, op: str, *, skipped: bool = False) -> Dict[str, Any]:
    return {
        "name": str(name),
        "passed": bool(passed),
        "observed": observed,
        "threshold": threshold,
        "operator": str(op),
        "skipped": bool(skipped),
    }


def _evaluate_oos_gates(
    metrics: Dict[str, Any],
    baseline: Optional[Dict[str, Any]],
    cfg: Dict[str, Any],
) -> Dict[str, Any]:
    checks: List[Dict[str, Any]] = []
    checks.append(
        _check(
            "min_oos_windows_ok",
            int(metrics.get("windows_ok", 0)) >= int(cfg.get("min_oos_windows_ok", 0)),
            int(metrics.get("windows_ok", 0)),
            int(cfg.get("min_oos_windows_ok", 0)),
            ">=",
        )
    )
    checks.append(
        _check(
            "max_failed_windows",
            int(metrics.get("windows_failed", 0)) <= int(cfg.get("max_failed_windows", 0)),
            int(metrics.get("windows_failed", 0)),
            int(cfg.get("max_failed_windows", 0)),
            "<=",
        )
    )
    checks.append(
        _check(
            "min_sum_pnl_quote",
            float(metrics.get("sum_pnl_quote", 0.0)) >= float(cfg.get("min_sum_pnl_quote", 0.0)),
            float(metrics.get("sum_pnl_quote", 0.0)),
            float(cfg.get("min_sum_pnl_quote", 0.0)),
            ">=",
        )
    )
    checks.append(
        _check(
            "min_avg_pnl_pct",
            float(metrics.get("avg_pnl_pct", 0.0)) >= float(cfg.get("min_avg_pnl_pct", 0.0)),
            float(metrics.get("avg_pnl_pct", 0.0)),
            float(cfg.get("min_avg_pnl_pct", 0.0)),
            ">=",
        )
    )
    checks.append(
        _check(
            "min_win_rate_pct",
            float(metrics.get("win_rate", 0.0)) >= float(cfg.get("min_win_rate_pct", 0.0)),
            float(metrics.get("win_rate", 0.0)),
            float(cfg.get("min_win_rate_pct", 0.0)),
            ">=",
        )
    )
    checks.append(
        _check(
            "min_profit_factor",
            float(metrics.get("profit_factor", 0.0)) >= float(cfg.get("min_profit_factor", 0.0)),
            float(metrics.get("profit_factor", 0.0)),
            float(cfg.get("min_profit_factor", 0.0)),
            ">=",
        )
    )

    if baseline:
        base_churn = float(baseline.get("churn_events_per_window", 0.0))
        max_churn = base_churn * (1.0 + (float(cfg.get("max_churn_degradation_pct", 0.0)) / 100.0))
        checks.append(
            _check(
                "max_churn_degradation_pct",
                float(metrics.get("churn_events_per_window", 0.0)) <= float(max_churn),
                float(metrics.get("churn_events_per_window", 0.0)),
                float(max_churn),
                "<=",
            )
        )

        base_false_start = float(baseline.get("false_start_rate", 0.0))
        max_false_start = base_false_start * (
            1.0 + (float(cfg.get("max_false_start_degradation_pct", 0.0)) / 100.0)
        )
        checks.append(
            _check(
                "max_false_start_degradation_pct",
                float(metrics.get("false_start_rate", 0.0)) <= float(max_false_start),
                float(metrics.get("false_start_rate", 0.0)),
                float(max_false_start),
                "<=",
            )
        )
    else:
        checks.append(
            _check(
                "max_churn_degradation_pct",
                True,
                float(metrics.get("churn_events_per_window", 0.0)),
                None,
                "<=",
                skipped=True,
            )
        )
        checks.append(
            _check(
                "max_false_start_degradation_pct",
                True,
                float(metrics.get("false_start_rate", 0.0)),
                None,
                "<=",
                skipped=True,
            )
        )

    return {
        "passed": all(bool(c.get("passed")) for c in checks),
        "checks": checks,
    }


def _evaluate_rank_stability(metrics: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    if not bool(cfg.get("enabled", True)):
        return {
            "passed": True,
            "checks": [_check("rank_stability_disabled", True, None, None, "==", skipped=True)],
        }
    observed = float(metrics.get("rank_stability_jaccard", 0.0))
    threshold = float(cfg.get("min_jaccard", 0.0))
    check = _check("min_jaccard", observed >= threshold, observed, threshold, ">=")
    return {"passed": bool(check["passed"]), "checks": [check]}


def _evaluate_ablations(
    base_metrics: Dict[str, Any],
    ablations: List[Dict[str, Any]],
    cfg: Dict[str, Any],
) -> Dict[str, Any]:
    if not bool(cfg.get("enabled", True)):
        return {
            "passed": True,
            "checks": [_check("ablation_gate_disabled", True, None, None, "==", skipped=True)],
            "runs": ablations,
        }

    required = [a for a in ablations if bool(a.get("required", True))]
    available_required = [a for a in required if isinstance(a.get("metrics"), dict)]
    checks: List[Dict[str, Any]] = []

    checks.append(
        _check(
            "required_ablation_coverage",
            len(available_required) == len(required),
            len(available_required),
            len(required),
            "==",
        )
    )

    min_required = int(cfg.get("min_required", 1))
    if len(required) == 0:
        min_required = 0
    checks.append(
        _check(
            "min_required_ablations",
            len(available_required) >= int(min_required),
            len(available_required),
            int(min_required),
            ">=",
        )
    )

    max_drop = float(cfg.get("max_avg_pnl_pct_drop", 4.0))
    for a in available_required:
        mid = str(a.get("ablation_id") or "ablation")
        m = a.get("metrics") or {}
        drop = float(base_metrics.get("avg_pnl_pct", 0.0)) - float(m.get("avg_pnl_pct", 0.0))
        checks.append(
            _check(
                f"max_avg_pnl_pct_drop:{mid}",
                drop <= max_drop,
                float(drop),
                float(max_drop),
                "<=",
            )
        )

    return {
        "passed": all(bool(c.get("passed")) for c in checks),
        "checks": checks,
        "runs": ablations,
    }


def _evaluate_chaos(
    base_metrics: Dict[str, Any],
    chaos_profiles: List[Dict[str, Any]],
    cfg: Dict[str, Any],
) -> Dict[str, Any]:
    if not bool(cfg.get("enabled", True)):
        return {
            "passed": True,
            "checks": [_check("chaos_gate_disabled", True, None, None, "==", skipped=True)],
            "profiles": chaos_profiles,
        }

    checks: List[Dict[str, Any]] = []
    min_profiles = int(cfg.get("min_profiles", 1))
    available = [p for p in chaos_profiles if isinstance(p.get("metrics"), dict)]
    checks.append(
        _check(
            "min_profiles",
            len(available) >= int(min_profiles),
            len(available),
            int(min_profiles),
            ">=",
        )
    )

    max_failed = int(cfg.get("max_failed_windows", 0))
    max_pnl_drop = float(cfg.get("max_avg_pnl_pct_degradation", 3.0))
    max_stop_mult = float(cfg.get("max_stop_events_multiplier", 1.5))

    base_avg_pnl = float(base_metrics.get("avg_pnl_pct", 0.0))
    base_stop_rate = float(base_metrics.get("stop_events_per_window", 0.0))

    for profile in available:
        name = str(profile.get("name") or profile.get("profile") or profile.get("run_id") or "chaos")
        m = profile.get("metrics") or {}
        failed_windows = int(m.get("windows_failed", 0))
        pnl_drop = base_avg_pnl - float(m.get("avg_pnl_pct", 0.0))
        stop_rate = float(m.get("stop_events_per_window", 0.0))
        if base_stop_rate <= 0.0:
            stop_mult = float("inf") if stop_rate > 0.0 else 1.0
        else:
            stop_mult = float(stop_rate / base_stop_rate)

        checks.append(
            _check(
                f"max_failed_windows:{name}",
                failed_windows <= max_failed,
                int(failed_windows),
                int(max_failed),
                "<=",
            )
        )
        checks.append(
            _check(
                f"max_avg_pnl_pct_degradation:{name}",
                pnl_drop <= max_pnl_drop,
                float(pnl_drop),
                float(max_pnl_drop),
                "<=",
            )
        )
        checks.append(
            _check(
                f"max_stop_events_multiplier:{name}",
                stop_mult <= max_stop_mult,
                float(stop_mult),
                float(max_stop_mult),
                "<=",
            )
        )

    return {
        "passed": all(bool(c.get("passed")) for c in checks),
        "checks": checks,
        "profiles": chaos_profiles,
    }


def _infer_slot(exp: Dict[str, Any], summary: Dict[str, Any]) -> str:
    if str(exp.get("slot") or "").strip():
        return str(exp.get("slot")).strip()
    args = summary.get("args", {}) if isinstance(summary.get("args"), dict) else {}
    strategy = str(exp.get("strategy") or args.get("strategy") or "GridBrainV1").strip()
    pair = str(exp.get("pair") or args.get("pair") or "ETH/USDT").strip()
    timeframe = str(exp.get("timeframe") or args.get("timeframe") or "15m").strip()
    return f"{strategy}|{pair}|{timeframe}"


def _load_or_init_registry(path: Path) -> Dict[str, Any]:
    data = _read_json(path)
    if not data:
        return {"version": 1, "updated_utc": "", "champions": {}, "history": []}
    if not isinstance(data.get("champions"), dict):
        data["champions"] = {}
    if not isinstance(data.get("history"), list):
        data["history"] = []
    if "version" not in data:
        data["version"] = 1
    return data


def _objective_value(metrics: Dict[str, Any], objective_metric: str) -> float:
    return float(_to_float(metrics.get(objective_metric), default=0.0))


def _run_walkforward_if_needed(
    run_id: str,
    walkforward_args: Optional[List[Any]],
    execute_missing: bool,
) -> bool:
    if not execute_missing:
        return False
    args = [str(x) for x in (walkforward_args or []) if str(x).strip()]
    if not args:
        return False
    if "--run-id" not in args:
        args.extend(["--run-id", str(run_id)])
    if "--resume" not in args:
        args.append("--resume")
    if "--fail-on-window-error" not in args:
        args.append("--fail-on-window-error")

    cmd = [
        sys.executable,
        str((FREQTRADE_ROOT / "scripts" / "run-user-walkforward.py").resolve()),
        *args,
    ]
    subprocess.run(cmd, cwd=str(FREQTRADE_ROOT), check=True)
    return True


def _validate_summary_with_schema(summary: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    root_required = schema.get("required_root_fields", []) if isinstance(schema, dict) else []
    for k in root_required:
        if k not in summary:
            errors.append(f"missing root field: {k}")

    exp_req = schema.get("required_experiment_fields", []) if isinstance(schema, dict) else []
    gate_req = schema.get("required_gate_fields", []) if isinstance(schema, dict) else []
    metrics_req = schema.get("required_metrics_fields", []) if isinstance(schema, dict) else []

    experiments = summary.get("experiments", []) if isinstance(summary.get("experiments"), list) else []
    for idx, exp in enumerate(experiments):
        if not isinstance(exp, dict):
            errors.append(f"experiment[{idx}] is not object")
            continue
        for k in exp_req:
            if k not in exp:
                errors.append(f"experiment[{idx}] missing field: {k}")
        m = exp.get("metrics", {}) if isinstance(exp.get("metrics"), dict) else {}
        for k in metrics_req:
            if k not in m:
                errors.append(f"experiment[{idx}] metrics missing field: {k}")
        for gate_key in ("oos_gate", "chaos_gate", "ablation_gate", "rank_stability_gate"):
            g = exp.get(gate_key, {}) if isinstance(exp.get(gate_key), dict) else {}
            for rk in gate_req:
                if rk not in g:
                    errors.append(f"experiment[{idx}] {gate_key} missing field: {rk}")
    return errors


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    ap.add_argument("--champions", default=str(DEFAULT_CHAMPIONS))
    ap.add_argument("--metrics-schema", default=str(DEFAULT_METRICS_SCHEMA))
    ap.add_argument("--user-data", default=str(DEFAULT_USER_DATA))
    ap.add_argument("--run-id", default=None)
    ap.add_argument(
        "--execute-missing",
        action="store_true",
        help="Execute missing walkforward runs when args are provided in manifest.",
    )
    ap.add_argument("--dry-run", action="store_true", help="Do not write champions.json updates.")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when any enabled experiment fails gates or validation.",
    )
    return ap


def main() -> int:
    args = build_parser().parse_args()

    manifest_path = Path(str(args.manifest)).resolve()
    champions_path = Path(str(args.champions)).resolve()
    schema_path = Path(str(args.metrics_schema)).resolve()
    user_data = Path(str(args.user_data)).resolve()

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    if not user_data.is_dir():
        raise FileNotFoundError(f"user_data dir not found: {user_data}")

    manifest = _load_manifest(manifest_path)
    registry = _load_or_init_registry(champions_path)
    schema = _read_json(schema_path) if schema_path.exists() else {}

    defaults = manifest.get("defaults", {}) if isinstance(manifest.get("defaults"), dict) else {}
    gates_oos_cfg = _deep_merge(DEFAULT_OOS_GATES, defaults.get("oos_gates"))
    gates_abl_cfg = _deep_merge(DEFAULT_ABLATION_GATES, defaults.get("ablation_gates"))
    gates_chaos_cfg = _deep_merge(DEFAULT_CHAOS_GATES, defaults.get("chaos_gates"))
    gates_rank_cfg = _deep_merge(DEFAULT_RANK_STABILITY, defaults.get("rank_stability"))
    promotion_cfg = _deep_merge(DEFAULT_PROMOTION, defaults.get("promotion"))

    experiments = manifest.get("experiments", []) if isinstance(manifest.get("experiments"), list) else []
    enabled_experiments = [e for e in experiments if isinstance(e, dict) and bool(e.get("enabled", True))]

    run_id = str(args.run_id).strip() if str(args.run_id or "").strip() else datetime.now(timezone.utc).strftime("tp_%Y%m%dT%H%M%SZ")
    out_dir = user_data / "experiments" / "tuning_protocol" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    output_experiments: List[Dict[str, Any]] = []
    output_promotions: List[Dict[str, Any]] = []
    strict_failures = 0

    champions = registry.get("champions", {}) if isinstance(registry.get("champions"), dict) else {}

    for exp in enabled_experiments:
        exp_id = str(exp.get("id") or exp.get("experiment_id") or "").strip() or "experiment"
        walk_cfg = exp.get("walkforward", {}) if isinstance(exp.get("walkforward"), dict) else {}
        run_id_candidate = str(walk_cfg.get("run_id") or exp.get("run_id") or "").strip()
        if not run_id_candidate:
            output_experiments.append(
                {
                    "experiment_id": exp_id,
                    "run_id": "",
                    "slot": str(exp.get("slot") or ""),
                    "status": "failed",
                    "error": "missing walkforward run_id",
                    "metrics": {},
                    "oos_gate": {"passed": False, "checks": []},
                    "ablation_gate": {"passed": False, "checks": []},
                    "chaos_gate": {"passed": False, "checks": []},
                    "rank_stability_gate": {"passed": False, "checks": []},
                    "promoted": False,
                }
            )
            strict_failures += 1
            continue

        summary = _load_summary(user_data, run_id_candidate)
        if summary is None:
            _run_walkforward_if_needed(
                run_id_candidate,
                walk_cfg.get("walkforward_args") if isinstance(walk_cfg.get("walkforward_args"), list) else None,
                bool(args.execute_missing),
            )
            summary = _load_summary(user_data, run_id_candidate)

        if summary is None:
            output_experiments.append(
                {
                    "experiment_id": exp_id,
                    "run_id": run_id_candidate,
                    "slot": str(exp.get("slot") or ""),
                    "status": "failed",
                    "error": "missing walkforward summary",
                    "metrics": {},
                    "oos_gate": {"passed": False, "checks": []},
                    "ablation_gate": {"passed": False, "checks": []},
                    "chaos_gate": {"passed": False, "checks": []},
                    "rank_stability_gate": {"passed": False, "checks": []},
                    "promoted": False,
                }
            )
            strict_failures += 1
            continue

        metrics = _collect_metrics(summary, run_id_candidate)
        slot = _infer_slot(exp, summary)

        baseline_cfg = exp.get("baseline", {}) if isinstance(exp.get("baseline"), dict) else {}
        baseline_run_id = str(
            baseline_cfg.get("run_id")
            or exp.get("baseline_run_id")
            or defaults.get("baseline_run_id")
            or (champions.get(slot, {}) if isinstance(champions.get(slot), dict) else {}).get("run_id")
            or ""
        ).strip()
        baseline_summary = _load_summary(user_data, baseline_run_id) if baseline_run_id else None
        baseline_metrics = (
            _collect_metrics(baseline_summary, baseline_run_id) if isinstance(baseline_summary, dict) else None
        )

        exp_oos_cfg = _deep_merge(gates_oos_cfg, exp.get("oos_gates") if isinstance(exp.get("oos_gates"), dict) else None)
        exp_rank_cfg = _deep_merge(
            gates_rank_cfg,
            exp.get("rank_stability") if isinstance(exp.get("rank_stability"), dict) else None,
        )

        oos_gate = _evaluate_oos_gates(metrics, baseline_metrics, exp_oos_cfg)
        rank_gate = _evaluate_rank_stability(metrics, exp_rank_cfg)

        ablations_cfg = exp.get("ablations", []) if isinstance(exp.get("ablations"), list) else []
        ablations_out: List[Dict[str, Any]] = []
        for ab in ablations_cfg:
            if not isinstance(ab, dict):
                continue
            ab_id = str(ab.get("id") or ab.get("ablation_id") or "ablation").strip()
            ab_run_id = str(ab.get("run_id") or "").strip()
            ab_summary = _load_summary(user_data, ab_run_id) if ab_run_id else None
            if ab_summary is None and ab_run_id:
                _run_walkforward_if_needed(
                    ab_run_id,
                    ab.get("walkforward_args") if isinstance(ab.get("walkforward_args"), list) else None,
                    bool(args.execute_missing),
                )
                ab_summary = _load_summary(user_data, ab_run_id)
            ab_metrics = _collect_metrics(ab_summary, ab_run_id) if isinstance(ab_summary, dict) else None
            ablations_out.append(
                {
                    "ablation_id": ab_id,
                    "run_id": ab_run_id,
                    "required": bool(ab.get("required", True)),
                    "metrics": ab_metrics,
                }
            )

        exp_ab_cfg = _deep_merge(
            gates_abl_cfg,
            exp.get("ablation_gates") if isinstance(exp.get("ablation_gates"), dict) else None,
        )
        ablation_gate = _evaluate_ablations(metrics, ablations_out, exp_ab_cfg)

        chaos_cfg = exp.get("chaos", {}) if isinstance(exp.get("chaos"), dict) else {}
        chaos_profiles_cfg = chaos_cfg.get("profiles", []) if isinstance(chaos_cfg.get("profiles"), list) else []
        chaos_profiles_out: List[Dict[str, Any]] = []
        for cp in chaos_profiles_cfg:
            if not isinstance(cp, dict):
                continue
            cp_name = str(cp.get("name") or cp.get("profile") or cp.get("id") or "chaos").strip()
            cp_run_id = str(cp.get("run_id") or "").strip()
            cp_summary = _load_summary(user_data, cp_run_id) if cp_run_id else None
            if cp_summary is None and cp_run_id:
                _run_walkforward_if_needed(
                    cp_run_id,
                    cp.get("walkforward_args") if isinstance(cp.get("walkforward_args"), list) else None,
                    bool(args.execute_missing),
                )
                cp_summary = _load_summary(user_data, cp_run_id)
            cp_metrics = _collect_metrics(cp_summary, cp_run_id) if isinstance(cp_summary, dict) else None
            chaos_profiles_out.append(
                {
                    "name": cp_name,
                    "run_id": cp_run_id,
                    "required": bool(cp.get("required", True)),
                    "metrics": cp_metrics,
                }
            )

        exp_chaos_cfg = _deep_merge(
            gates_chaos_cfg,
            chaos_cfg.get("gates") if isinstance(chaos_cfg.get("gates"), dict) else None,
        )
        chaos_gate = _evaluate_chaos(metrics, chaos_profiles_out, exp_chaos_cfg)

        exp_promo_cfg = _deep_merge(
            promotion_cfg,
            exp.get("promotion") if isinstance(exp.get("promotion"), dict) else None,
        )

        all_gates_pass = bool(oos_gate.get("passed"))
        if bool(exp_promo_cfg.get("require_rank_stability_pass", True)):
            all_gates_pass = all_gates_pass and bool(rank_gate.get("passed"))
        if bool(exp_promo_cfg.get("require_ablation_pass", True)):
            all_gates_pass = all_gates_pass and bool(ablation_gate.get("passed"))
        if bool(exp_promo_cfg.get("require_chaos_pass", True)):
            all_gates_pass = all_gates_pass and bool(chaos_gate.get("passed"))

        current_champion = champions.get(slot, {}) if isinstance(champions.get(slot), dict) else {}
        objective_metric = str(exp_promo_cfg.get("objective_metric") or "avg_pnl_pct")
        objective_min_delta = float(exp_promo_cfg.get("objective_improvement_min", 0.0))
        candidate_objective = _objective_value(metrics, objective_metric)
        champion_metrics = current_champion.get("metrics", {}) if isinstance(current_champion.get("metrics"), dict) else {}
        champion_objective = _objective_value(champion_metrics, objective_metric)

        improvement = float(candidate_objective - champion_objective)
        has_champion = bool(str(current_champion.get("run_id") or "").strip())
        improvement_pass = (not has_champion) or (improvement >= objective_min_delta)
        promoted = bool(all_gates_pass and improvement_pass)

        promotion_note = ""
        if not all_gates_pass:
            promotion_note = "gates_failed"
        elif has_champion and not improvement_pass:
            promotion_note = "insufficient_objective_improvement"
        else:
            promotion_note = "promoted"

        out_exp = {
            "experiment_id": exp_id,
            "run_id": run_id_candidate,
            "slot": slot,
            "status": "ok",
            "error": "",
            "baseline_run_id": baseline_run_id,
            "metrics": metrics,
            "oos_gate": oos_gate,
            "ablation_gate": ablation_gate,
            "chaos_gate": chaos_gate,
            "rank_stability_gate": rank_gate,
            "promotion": {
                "objective_metric": objective_metric,
                "candidate_objective": candidate_objective,
                "champion_objective": champion_objective,
                "improvement": improvement,
                "min_improvement": objective_min_delta,
                "improvement_pass": bool(improvement_pass),
                "note": promotion_note,
            },
            "promoted": bool(promoted),
        }
        output_experiments.append(out_exp)

        output_promotions.append(
            {
                "experiment_id": exp_id,
                "slot": slot,
                "run_id": run_id_candidate,
                "promoted": bool(promoted),
                "note": promotion_note,
            }
        )

        history_entry = {
            "ts_utc": _utc_now_iso(),
            "run_id": run_id,
            "experiment_id": exp_id,
            "slot": slot,
            "candidate_run_id": run_id_candidate,
            "promoted": bool(promoted),
            "promotion_note": promotion_note,
            "objective_metric": objective_metric,
            "objective_improvement": improvement,
            "oos_pass": bool(oos_gate.get("passed")),
            "ablation_pass": bool(ablation_gate.get("passed")),
            "chaos_pass": bool(chaos_gate.get("passed")),
            "rank_pass": bool(rank_gate.get("passed")),
        }

        registry_history = registry.get("history", []) if isinstance(registry.get("history"), list) else []
        registry_history.append(history_entry)
        registry["history"] = registry_history[-1000:]

        if promoted:
            champions[slot] = {
                "run_id": run_id_candidate,
                "experiment_id": exp_id,
                "updated_utc": _utc_now_iso(),
                "manifest": str(manifest_path),
                "metrics": metrics,
                "promotion": out_exp["promotion"],
                "baseline_run_id": baseline_run_id,
            }

        if bool(args.strict) and (not promoted):
            strict_failures += 1

    registry["champions"] = champions
    registry["updated_utc"] = _utc_now_iso()

    summary_payload: Dict[str, Any] = {
        "created_utc": _utc_now_iso(),
        "run_id": run_id,
        "manifest": str(manifest_path),
        "champions": str(champions_path),
        "metrics_schema": str(schema_path),
        "defaults": {
            "oos_gates": gates_oos_cfg,
            "ablation_gates": gates_abl_cfg,
            "chaos_gates": gates_chaos_cfg,
            "rank_stability": gates_rank_cfg,
            "promotion": promotion_cfg,
        },
        "experiments_total": len(enabled_experiments),
        "experiments": output_experiments,
        "promotions": output_promotions,
        "strict_failures": int(strict_failures),
    }

    validation_errors = _validate_summary_with_schema(summary_payload, schema)
    summary_payload["metrics_schema_validation_errors"] = list(validation_errors)

    out_summary = out_dir / "summary.json"
    _write_json_atomic(out_summary, summary_payload)

    if (not args.dry_run) and (not validation_errors):
        _write_json_atomic(champions_path, registry)

    latest_payload = {
        "run_type": "tuning_protocol",
        "run_id": run_id,
        "out_path": rel_payload_path(user_data, out_summary),
        "manifest": str(manifest_path),
        "champions": str(champions_path),
        "promoted_count": int(sum(1 for p in output_promotions if bool(p.get("promoted")))),
        "strict_failures": int(strict_failures),
    }
    ref = publish_latest_ref(user_data, "tuning_protocol", latest_payload)

    print(f"[tuning-protocol] wrote {out_summary}")
    print(f"[tuning-protocol] latest_ref wrote {ref}")
    if args.dry_run:
        print("[tuning-protocol] dry-run=1 champions registry not updated")
    elif validation_errors:
        print("[tuning-protocol] champions registry update skipped: schema validation failed")

    if validation_errors:
        for err in validation_errors:
            print(f"[tuning-protocol] schema_error: {err}")
        return 1

    if bool(args.strict) and strict_failures > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
