#!/usr/bin/env python3
"""
Manage user_data artifacts with safe cleanup defaults.

Default behavior is dry-run and conservative:
- Keeps reusable OHLCV data files.
- Keeps walkforward summary artifacts (summary.json / windows.csv / AB compare json).
- Keeps regime calibration reports (report.json / mode_threshold_overrides.json).
- Prunes heavy/debug artifacts that are expensive to store but cheap to regenerate.
"""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


@dataclass(frozen=True)
class Candidate:
    path: Path
    reason: str
    bytes_size: int
    is_dir: bool


KEEP_BACKTEST_FILES = {".gitkeep", ".last_result.json"}
WALKFORWARD_RAW_PATTERNS = (
    "window_*.result.json",
    "window_*.result.events.csv",
    "window_*.result.fills.csv",
    "window_*.result.curve.csv",
)
REGIME_VERBOSE_NAMES = (
    "features.csv",
    "per_candle_verbose.csv",
    "transition_events.csv",
    "transition_events.json",
)


def _to_float_optional(v: object) -> Optional[float]:
    if v in (None, ""):
        return None
    try:
        return float(v)
    except Exception:
        return None


def bytes_h(n: int) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    v = float(max(0, n))
    for unit in units:
        if v < 1024.0 or unit == units[-1]:
            if unit == "B":
                return f"{int(v)}{unit}"
            return f"{v:.2f}{unit}"
        v /= 1024.0
    return f"{int(n)}B"


def path_size(path: Path) -> int:
    try:
        if path.is_file() or path.is_symlink():
            return int(path.stat().st_size)
        if path.is_dir():
            total = 0
            for p in path.rglob("*"):
                if p.is_file() and not p.is_symlink():
                    try:
                        total += int(p.stat().st_size)
                    except Exception:
                        continue
            return int(total)
    except Exception:
        return 0
    return 0


def add_candidate(store: Dict[Path, Candidate], path: Path, reason: str) -> None:
    if not path.exists():
        return
    p = path.resolve()
    if p in store:
        return
    store[p] = Candidate(path=p, reason=reason, bytes_size=path_size(p), is_dir=p.is_dir())


def collapse_nested(candidates: Iterable[Candidate]) -> List[Candidate]:
    items = sorted(candidates, key=lambda c: (len(c.path.parts), str(c.path)))
    kept: List[Candidate] = []
    kept_dirs: List[Path] = []
    for item in items:
        skip = False
        for d in kept_dirs:
            if item.path == d or d in item.path.parents:
                skip = True
                break
        if skip:
            continue
        kept.append(item)
        if item.is_dir:
            kept_dirs.append(item.path)
    return kept


def _latest_run_dirs(parent: Path) -> List[Path]:
    if not parent.is_dir():
        return []
    runs: List[Tuple[float, Path]] = []
    for d in parent.iterdir():
        if not d.is_dir():
            continue
        summary = d / "summary.json"
        windows = d / "windows.csv"
        if summary.exists() and windows.exists():
            try:
                ts = float(summary.stat().st_mtime)
            except Exception:
                ts = 0.0
            runs.append((ts, d))
    runs.sort(key=lambda x: x[0], reverse=True)
    return [d for _, d in runs]


def _prune_old_runs(
    store: Dict[Path, Candidate],
    runs_parent: Path,
    keep_latest: int,
    pinned_names: Set[str],
    reason: str,
) -> None:
    if keep_latest <= 0:
        return
    runs = _latest_run_dirs(runs_parent)
    keep_names: Set[str] = set(pinned_names)
    for d in runs[:keep_latest]:
        keep_names.add(d.name)
    for d in runs:
        if d.name in keep_names:
            continue
        add_candidate(store, d, reason)


def _result_path_for_window(run_dir: Path, row: Dict[str, object]) -> Path:
    rf = str(row.get("result_file") or "").strip()
    if rf:
        p = Path(rf)
        if p.is_absolute():
            return p
        return (run_dir / p).resolve()
    idx = int(row.get("index") or 0)
    return (run_dir / f"window_{idx:03d}.result.json").resolve()


def _extract_end_balances(result_path: Path) -> Tuple[Optional[float], Optional[float]]:
    if not result_path.exists():
        return (None, None)
    try:
        payload = json.loads(result_path.read_text(encoding="utf-8"))
    except Exception:
        return (None, None)
    summary = payload.get("summary", {}) if isinstance(payload, dict) else {}
    if not isinstance(summary, dict):
        return (None, None)
    end_quote = _to_float_optional(summary.get("end_quote"))
    end_base = _to_float_optional(summary.get("end_base"))
    return (end_quote, end_base)


def hydrate_walkforward_summaries(
    user_data: Path,
    apply: bool,
) -> Tuple[Dict[str, object], Set[str]]:
    wf_dir = user_data / "walkforward"
    out = {
        "runs_checked": 0,
        "windows_missing_before": 0,
        "windows_hydratable": 0,
        "windows_hydrated": 0,
        "windows_still_missing": 0,
        "summaries_updated": 0,
    }
    blocked_runs: Set[str] = set()

    if not wf_dir.is_dir():
        return out, blocked_runs

    for summary_path in sorted(wf_dir.glob("*/summary.json")):
        run_dir = summary_path.parent
        try:
            data = json.loads(summary_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        windows = data.get("windows", []) if isinstance(data, dict) else []
        if not isinstance(windows, list):
            continue

        out["runs_checked"] = int(out["runs_checked"]) + 1
        changed = False
        run_missing_after = 0
        for row in windows:
            if not isinstance(row, dict):
                continue
            if str(row.get("status", "")).lower() != "ok":
                continue
            has_end_quote = row.get("end_quote") not in (None, "")
            has_end_base = row.get("end_base") not in (None, "")
            if has_end_quote and has_end_base:
                continue
            out["windows_missing_before"] = int(out["windows_missing_before"]) + 1
            result_path = _result_path_for_window(run_dir, row)
            end_quote, end_base = _extract_end_balances(result_path)
            if (end_quote is not None) and (end_base is not None):
                out["windows_hydratable"] = int(out["windows_hydratable"]) + 1
                if apply:
                    row["end_quote"] = float(end_quote)
                    row["end_base"] = float(end_base)
                    out["windows_hydrated"] = int(out["windows_hydrated"]) + 1
                    changed = True
            else:
                out["windows_still_missing"] = int(out["windows_still_missing"]) + 1
                run_missing_after += 1

        if run_missing_after > 0:
            blocked_runs.add(run_dir.name)
        if changed and apply:
            summary_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            out["summaries_updated"] = int(out["summaries_updated"]) + 1

    return out, blocked_runs


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user-data", default="user_data")
    ap.add_argument("--apply", action="store_true", help="Delete selected artifacts. Default is dry-run.")
    ap.add_argument("--json", action="store_true", help="Print machine-readable JSON summary.")
    ap.add_argument(
        "--list-limit",
        type=int,
        default=40,
        help="How many largest candidate paths to print.",
    )

    ap.add_argument("--prune-pycache", action="store_true", default=True)
    ap.add_argument("--no-prune-pycache", action="store_false", dest="prune_pycache")
    ap.add_argument("--prune-backtest-results", action="store_true", default=True)
    ap.add_argument("--no-prune-backtest-results", action="store_false", dest="prune_backtest_results")
    ap.add_argument("--prune-grid-plan-archives", action="store_true", default=True)
    ap.add_argument("--no-prune-grid-plan-archives", action="store_false", dest="prune_grid_plan_archives")
    ap.add_argument("--prune-walkforward-raw", action="store_true", default=True)
    ap.add_argument("--no-prune-walkforward-raw", action="store_false", dest="prune_walkforward_raw")
    ap.add_argument("--prune-regime-verbose", action="store_true", default=True)
    ap.add_argument("--no-prune-regime-verbose", action="store_false", dest="prune_regime_verbose")
    ap.add_argument("--prune-portable-nonlatest", action="store_true", default=False)
    ap.add_argument(
        "--hydrate-walkforward-balances",
        action="store_true",
        default=True,
        help="Populate missing end_quote/end_base in walkforward summaries from per-window result json.",
    )
    ap.add_argument(
        "--no-hydrate-walkforward-balances",
        action="store_false",
        dest="hydrate_walkforward_balances",
    )
    ap.add_argument(
        "--allow-delete-with-missing-balances",
        action="store_true",
        default=False,
        help=(
            "Allow deleting walkforward raw files even when some summaries still "
            "cannot be hydrated with end balances."
        ),
    )

    ap.add_argument(
        "--keep-walkforward-runs",
        type=int,
        default=0,
        help="If >0, delete full walkforward run directories except latest N.",
    )
    ap.add_argument(
        "--keep-regime-runs",
        type=int,
        default=0,
        help="If >0, delete full regime_audit run directories except latest N.",
    )
    ap.add_argument(
        "--pin-walkforward-run",
        action="append",
        default=[],
        help="Run-id to always keep when --keep-walkforward-runs is used.",
    )
    ap.add_argument(
        "--pin-regime-run",
        action="append",
        default=[],
        help="Run-id to always keep when --keep-regime-runs is used.",
    )
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    root_dir = Path(__file__).resolve().parents[1]
    user_data = Path(args.user_data)
    if not user_data.is_absolute():
        user_data = (root_dir / user_data).resolve()
    if not user_data.is_dir():
        raise FileNotFoundError(f"user_data directory not found: {user_data}")

    candidates: Dict[Path, Candidate] = {}
    hydration_info: Dict[str, object] = {}
    blocked_walkforward_runs: Set[str] = set()

    if args.hydrate_walkforward_balances:
        hydration_info, blocked_walkforward_runs = hydrate_walkforward_summaries(
            user_data=user_data,
            apply=bool(args.apply),
        )

    if args.prune_pycache:
        for p in root_dir.rglob("__pycache__"):
            add_candidate(candidates, p, "pycache_dir")
        for p in root_dir.rglob("*.pyc"):
            add_candidate(candidates, p, "pycache_file")

    if args.prune_backtest_results:
        bt_dir = user_data / "backtest_results"
        if bt_dir.is_dir():
            for p in bt_dir.iterdir():
                if p.name in KEEP_BACKTEST_FILES:
                    continue
                add_candidate(candidates, p, "backtest_result_artifact")

    if args.prune_grid_plan_archives:
        gp_dir = user_data / "grid_plans"
        if gp_dir.is_dir():
            for p in gp_dir.rglob("grid_plan.*.json"):
                if p.name == "grid_plan.latest.json":
                    continue
                add_candidate(candidates, p, "grid_plan_archive")

    if args.prune_walkforward_raw:
        wf_dir = user_data / "walkforward"
        if wf_dir.is_dir():
            for run_dir in wf_dir.iterdir():
                if not run_dir.is_dir():
                    continue
                if (
                    run_dir.name in blocked_walkforward_runs
                    and (not bool(args.allow_delete_with_missing_balances))
                ):
                    continue
                for pattern in WALKFORWARD_RAW_PATTERNS:
                    for p in run_dir.glob(pattern):
                        add_candidate(candidates, p, "walkforward_raw_window_file")
                for p in run_dir.glob("window_*_plans"):
                    add_candidate(candidates, p, "walkforward_window_plan_dir")

    if args.prune_regime_verbose:
        ra_dir = user_data / "regime_audit"
        if ra_dir.is_dir():
            for run_dir in ra_dir.iterdir():
                if not run_dir.is_dir():
                    continue
                for name in REGIME_VERBOSE_NAMES:
                    p = run_dir / name
                    add_candidate(candidates, p, "regime_verbose_artifact")

    if args.prune_portable_nonlatest:
        pr_dir = user_data / "portable_results"
        if pr_dir.is_dir():
            for p in pr_dir.iterdir():
                if p.name == "latest":
                    continue
                add_candidate(candidates, p, "portable_nonlatest")

    _prune_old_runs(
        candidates,
        user_data / "walkforward",
        int(args.keep_walkforward_runs),
        {str(x).strip() for x in args.pin_walkforward_run if str(x).strip()},
        "walkforward_old_run_dir",
    )
    _prune_old_runs(
        candidates,
        user_data / "regime_audit",
        int(args.keep_regime_runs),
        {str(x).strip() for x in args.pin_regime_run if str(x).strip()},
        "regime_old_run_dir",
    )

    probe_file = user_data / ".probe_from_compose"
    if probe_file.exists():
        add_candidate(candidates, probe_file, "compose_probe_file")

    collapsed = collapse_nested(candidates.values())
    collapsed.sort(key=lambda c: c.bytes_size, reverse=True)

    reason_totals: Dict[str, Dict[str, int]] = {}
    total_bytes = 0
    for c in collapsed:
        total_bytes += int(c.bytes_size)
        item = reason_totals.setdefault(c.reason, {"count": 0, "bytes": 0})
        item["count"] += 1
        item["bytes"] += int(c.bytes_size)

    summary = {
        "mode": "apply" if args.apply else "dry-run",
        "user_data": str(user_data),
        "candidates": len(collapsed),
        "bytes_reclaimable": int(total_bytes),
        "walkforward_hydration": hydration_info,
        "walkforward_blocked_runs": sorted(blocked_walkforward_runs),
        "reasons": reason_totals,
        "largest_candidates": [
            {
                "path": str(c.path),
                "reason": c.reason,
                "bytes": int(c.bytes_size),
                "type": "dir" if c.is_dir else "file",
            }
            for c in collapsed[: max(0, int(args.list_limit))]
        ],
    }

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            f"[cleanup] mode={summary['mode']} candidates={summary['candidates']} "
            f"reclaimable={bytes_h(summary['bytes_reclaimable'])}",
            flush=True,
        )
        if hydration_info:
            print(
                "[cleanup] walkforward_hydration "
                f"runs_checked={int(hydration_info.get('runs_checked', 0))} "
                f"missing_before={int(hydration_info.get('windows_missing_before', 0))} "
                f"hydratable={int(hydration_info.get('windows_hydratable', 0))} "
                f"hydrated={int(hydration_info.get('windows_hydrated', 0))} "
                f"still_missing={int(hydration_info.get('windows_still_missing', 0))} "
                f"summaries_updated={int(hydration_info.get('summaries_updated', 0))}",
                flush=True,
            )
            if blocked_walkforward_runs and (not bool(args.allow_delete_with_missing_balances)):
                print(
                    "[cleanup] walkforward_raw_protected_runs "
                    f"count={len(blocked_walkforward_runs)} "
                    "reason=missing_end_balances",
                    flush=True,
                )
        for reason, stats in sorted(
            reason_totals.items(),
            key=lambda kv: (-int(kv[1]["bytes"]), str(kv[0])),
        ):
            print(
                f"[cleanup] reason={reason} count={int(stats['count'])} "
                f"bytes={bytes_h(int(stats['bytes']))}",
                flush=True,
            )
        if collapsed:
            print("[cleanup] largest:", flush=True)
            for c in collapsed[: max(0, int(args.list_limit))]:
                kind = "dir" if c.is_dir else "file"
                print(
                    f"[cleanup] - {bytes_h(c.bytes_size):>9} {kind:>4} {c.reason:>28} {c.path}",
                    flush=True,
                )

    if not args.apply:
        return 0

    deleted = 0
    reclaimed = 0
    errors: List[str] = []
    for c in sorted(collapsed, key=lambda x: (len(x.path.parts), str(x.path)), reverse=True):
        try:
            if not c.path.exists():
                continue
            if c.is_dir:
                shutil.rmtree(c.path)
            else:
                c.path.unlink()
            deleted += 1
            reclaimed += int(c.bytes_size)
        except Exception as exc:
            errors.append(f"{c.path}: {exc}")

    print(
        f"[cleanup] deleted={deleted} reclaimed={bytes_h(reclaimed)} errors={len(errors)}",
        flush=True,
    )
    for msg in errors[:20]:
        print(f"[cleanup] error {msg}", flush=True)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
