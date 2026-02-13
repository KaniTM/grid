#!/usr/bin/env python3
"""
Rolling walk-forward runner for the GridBrain/Executor/Simulator stack.

For each window:
1) Run freqtrade backtesting so GridBrain writes plan snapshots.
2) Extract plan snapshots that belong to the window.
3) Run replay simulator on the same window.
4) Collect per-window metrics and aggregate summary.
"""

from __future__ import annotations

import argparse
import csv
import json
import shlex
import shutil
import statistics
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class WindowResult:
    index: int
    timerange: str
    start_day: str
    end_day: str
    status: str
    error: str = ""
    result_file: str = ""
    plans_file_count: int = 0
    pnl_quote: Optional[float] = None
    pnl_pct: Optional[float] = None
    initial_equity: Optional[float] = None
    end_equity: Optional[float] = None
    fills: Optional[int] = None
    stop_events: Optional[int] = None
    seed_events: Optional[int] = None
    rebuild_events: Optional[int] = None
    soft_adjust_events: Optional[int] = None
    action_start: Optional[int] = None
    action_hold: Optional[int] = None
    action_stop: Optional[int] = None
    start_blocker_counts: Optional[Dict[str, int]] = None
    start_counterfactual_single_counts: Optional[Dict[str, int]] = None
    start_counterfactual_combo_counts: Optional[Dict[str, int]] = None
    hold_reason_counts: Optional[Dict[str, int]] = None
    stop_reason_counts: Optional[Dict[str, int]] = None
    stop_event_reason_counts: Optional[Dict[str, int]] = None
    stop_reason_counts_combined: Optional[Dict[str, int]] = None
    top_start_blocker: Optional[str] = None
    top_start_counterfactual_single: Optional[str] = None
    top_start_counterfactual_combo: Optional[str] = None
    top_stop_reason: Optional[str] = None

    def as_dict(self) -> Dict:
        return {
            "index": self.index,
            "timerange": self.timerange,
            "start_day": self.start_day,
            "end_day": self.end_day,
            "status": self.status,
            "error": self.error,
            "result_file": self.result_file,
            "plans_file_count": self.plans_file_count,
            "pnl_quote": self.pnl_quote,
            "pnl_pct": self.pnl_pct,
            "initial_equity": self.initial_equity,
            "end_equity": self.end_equity,
            "fills": self.fills,
            "stop_events": self.stop_events,
            "seed_events": self.seed_events,
            "rebuild_events": self.rebuild_events,
            "soft_adjust_events": self.soft_adjust_events,
            "action_start": self.action_start,
            "action_hold": self.action_hold,
            "action_stop": self.action_stop,
            "start_blocker_counts": json.dumps(self.start_blocker_counts or {}, sort_keys=True),
            "start_counterfactual_single_counts": json.dumps(
                self.start_counterfactual_single_counts or {}, sort_keys=True
            ),
            "start_counterfactual_combo_counts": json.dumps(
                self.start_counterfactual_combo_counts or {}, sort_keys=True
            ),
            "hold_reason_counts": json.dumps(self.hold_reason_counts or {}, sort_keys=True),
            "stop_reason_counts": json.dumps(self.stop_reason_counts or {}, sort_keys=True),
            "stop_event_reason_counts": json.dumps(self.stop_event_reason_counts or {}, sort_keys=True),
            "stop_reason_counts_combined": json.dumps(self.stop_reason_counts_combined or {}, sort_keys=True),
            "top_start_blocker": self.top_start_blocker,
            "top_start_counterfactual_single": self.top_start_counterfactual_single,
            "top_start_counterfactual_combo": self.top_start_counterfactual_combo,
            "top_stop_reason": self.top_stop_reason,
        }


def parse_day_timerange(timerange: str) -> Tuple[datetime, datetime]:
    if "-" not in timerange:
        raise ValueError("timerange must be YYYYMMDD-YYYYMMDD")
    a, b = timerange.split("-", 1)
    start = datetime.strptime(a, "%Y%m%d").replace(tzinfo=timezone.utc)
    end = datetime.strptime(b, "%Y%m%d").replace(tzinfo=timezone.utc)
    if end <= start:
        raise ValueError("timerange end must be after start")
    return start, end


def fmt_day(dt: datetime) -> str:
    return dt.strftime("%Y%m%d")


def iter_windows(
    start: datetime,
    end: datetime,
    window_days: int,
    step_days: int,
    min_window_days: int,
) -> List[Tuple[int, datetime, datetime]]:
    if window_days <= 0:
        raise ValueError("window_days must be > 0")
    if step_days <= 0:
        raise ValueError("step_days must be > 0")
    if min_window_days <= 0:
        raise ValueError("min_window_days must be > 0")

    out: List[Tuple[int, datetime, datetime]] = []
    idx = 1
    cur = start
    while cur < end:
        w_end = min(cur + timedelta(days=window_days), end)
        if (w_end - cur).days < min_window_days:
            break
        out.append((idx, cur, w_end))
        idx += 1
        cur = cur + timedelta(days=step_days)
    return out


def plan_effective_time(plan: Dict) -> Optional[datetime]:
    ct = plan.get("candle_time_utc")
    if ct:
        try:
            return datetime.fromisoformat(str(ct).replace("Z", "+00:00")).astimezone(timezone.utc)
        except Exception:
            pass

    cts = plan.get("candle_ts")
    if cts is not None:
        try:
            return datetime.fromtimestamp(int(cts), tz=timezone.utc)
        except Exception:
            pass

    ts = plan.get("ts")
    if ts:
        try:
            return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).astimezone(timezone.utc)
        except Exception:
            pass
    return None


def to_container_user_data_path(local_path: Path, user_data_dir: Path) -> str:
    rel = local_path.resolve().relative_to(user_data_dir.resolve())
    return f"/freqtrade/user_data/{rel.as_posix()}"


def q(text: str) -> str:
    return shlex.quote(text)


def run_compose_inner(
    root_dir: Path,
    service: str,
    inner_cmd: str,
    dry_run: bool = False,
) -> None:
    cmd = ["docker", "compose", "run", "--rm", "--entrypoint", "bash", service, "-lc", inner_cmd]
    print(f"[walkforward] $ {' '.join(shlex.quote(x) for x in cmd)}", flush=True)
    if dry_run:
        return
    subprocess.run(cmd, cwd=str(root_dir), check=True)


def extract_window_plans(
    src_plan_dir: Path,
    dst_plan_dir: Path,
    window_start: datetime,
    window_end: datetime,
    min_mtime_epoch: Optional[float] = None,
) -> int:
    if not src_plan_dir.is_dir():
        raise FileNotFoundError(f"Plan source directory not found: {src_plan_dir}")

    if dst_plan_dir.exists():
        shutil.rmtree(dst_plan_dir)
    dst_plan_dir.mkdir(parents=True, exist_ok=True)

    candidates = sorted(src_plan_dir.glob("grid_plan*.json"))

    def _mtime(path: Path) -> float:
        try:
            return float(path.stat().st_mtime)
        except Exception:
            return 0.0

    def _collect(require_mtime: bool, enforce_window: bool = True) -> List[Tuple[datetime, Path, Dict]]:
        out: List[Tuple[datetime, Path, Dict]] = []
        for path in candidates:
            if require_mtime and (min_mtime_epoch is not None):
                if _mtime(path) < float(min_mtime_epoch):
                    continue
            try:
                with path.open("r", encoding="utf-8") as f:
                    plan = json.load(f)
            except Exception:
                continue
            ptime = plan_effective_time(plan)
            if ptime is None:
                continue
            if enforce_window and not (window_start <= ptime < window_end):
                continue
            if not enforce_window:
                out.append((ptime, path, plan))
                continue
            if window_start <= ptime < window_end:
                out.append((ptime, path, plan))
        return out

    fallback_used = False
    matched = _collect(require_mtime=(min_mtime_epoch is not None))
    if (not matched) and (min_mtime_epoch is not None):
        # Boundary fallback: prefer a plan created in this run, even if its effective
        # candle lands right at/after window_end and therefore does not fall inside
        # [window_start, window_end).
        recent = _collect(require_mtime=True, enforce_window=False)
        if recent:
            recent.sort(key=lambda x: (x[0], _mtime(x[1]), x[1].name))
            eligible = [x for x in recent if x[0] <= window_end]
            matched = [eligible[-1] if eligible else recent[0]]

    if (not matched) and (min_mtime_epoch is not None):
        # Last-resort fallback: content can be unchanged between runs, so mtime may not move.
        fallback_used = True
        matched = _collect(require_mtime=False)

    if not matched:
        return 0

    if fallback_used and matched:
        # Avoid mixing older archives from previous runs when we had to fallback.
        matched.sort(key=lambda x: (_mtime(x[1]), x[1].name))
        matched = [matched[-1]]

    # Dedup by effective plan timestamp so `latest` + archive variants at the same
    # candle time do not over-count window coverage.
    matched.sort(key=lambda x: (x[0], _mtime(x[1]), x[1].name))
    dedup_by_time: Dict[datetime, Tuple[datetime, Path, Dict]] = {}
    for item in matched:
        dedup_by_time[item[0]] = item
    matched = [dedup_by_time[k] for k in sorted(dedup_by_time.keys())]

    for _, src, _ in matched:
        shutil.copy2(src, dst_plan_dir / src.name)

    latest_plan = matched[-1][2]
    latest_out = dst_plan_dir / "grid_plan.latest.json"
    with latest_out.open("w", encoding="utf-8") as f:
        json.dump(latest_plan, f, indent=2, sort_keys=True)
    return len(matched)


def _coerce_reason_counts(raw: object) -> Dict[str, int]:
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, int] = {}
    for k, v in raw.items():
        key = str(k).strip()
        if not key:
            continue
        try:
            val = int(v)
        except Exception:
            continue
        if val <= 0:
            continue
        out[key] = int(val)
    return {k: int(v) for k, v in sorted(out.items(), key=lambda kv: (-int(kv[1]), str(kv[0])))}


def _merge_reason_counts(counters: List[Dict[str, int]]) -> Dict[str, int]:
    merged: Dict[str, int] = {}
    for counter in counters:
        for k, v in (counter or {}).items():
            merged[k] = int(merged.get(k, 0)) + int(v)
    return {k: int(v) for k, v in sorted(merged.items(), key=lambda kv: (-int(kv[1]), str(kv[0])))}


def _top_reason(counter: Dict[str, int]) -> Optional[str]:
    if not counter:
        return None
    k, v = next(iter(counter.items()))
    return f"{k}:{int(v)}"


def load_sim_summary(result_path: Path) -> Dict:
    with result_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    summary = payload.get("summary", {}) or {}
    fills = payload.get("fills", []) or []
    actions = summary.get("actions", {}) or {}
    start_blocker_counts = _coerce_reason_counts(summary.get("start_blocker_counts", {}))
    start_counterfactual_single_counts = _coerce_reason_counts(
        summary.get("start_counterfactual_single_counts", {})
    )
    start_counterfactual_combo_counts = _coerce_reason_counts(
        summary.get("start_counterfactual_combo_counts", {})
    )
    hold_reason_counts = _coerce_reason_counts(summary.get("hold_reason_counts", {}))
    stop_reason_counts = _coerce_reason_counts(summary.get("stop_reason_counts", {}))
    stop_event_reason_counts = _coerce_reason_counts(summary.get("stop_event_reason_counts", {}))
    stop_reason_counts_combined = _coerce_reason_counts(summary.get("stop_reason_counts_combined", {}))
    return {
        "pnl_quote": float(summary.get("pnl_quote", 0.0)),
        "pnl_pct": float(summary.get("pnl_pct", 0.0)),
        "initial_equity": float(summary.get("initial_equity", 0.0)),
        "end_equity": float(summary.get("equity", 0.0)),
        "fills": int(len(fills)),
        "stop_events": int(summary.get("stop_events", 0)),
        "seed_events": int(summary.get("seed_events", 0)),
        "rebuild_events": int(summary.get("rebuild_events", 0)),
        "soft_adjust_events": int(summary.get("soft_adjust_events", 0)),
        "action_start": int(actions.get("START", 0)),
        "action_hold": int(actions.get("HOLD", 0)),
        "action_stop": int(actions.get("STOP", 0)),
        "end_quote": float(summary.get("end_quote", 0.0)),
        "end_base": float(summary.get("end_base", 0.0)),
        "start_blocker_counts": start_blocker_counts,
        "start_counterfactual_single_counts": start_counterfactual_single_counts,
        "start_counterfactual_combo_counts": start_counterfactual_combo_counts,
        "hold_reason_counts": hold_reason_counts,
        "stop_reason_counts": stop_reason_counts,
        "stop_event_reason_counts": stop_event_reason_counts,
        "stop_reason_counts_combined": stop_reason_counts_combined,
        "top_start_blocker": _top_reason(start_blocker_counts),
        "top_start_counterfactual_single": _top_reason(start_counterfactual_single_counts),
        "top_start_counterfactual_combo": _top_reason(start_counterfactual_combo_counts),
        "top_stop_reason": _top_reason(stop_reason_counts_combined),
    }


def aggregate(rows: List[WindowResult]) -> Dict:
    ok = [r for r in rows if r.status == "ok" and r.pnl_quote is not None and r.pnl_pct is not None]
    failed = [r for r in rows if r.status != "ok"]

    pnl_quotes = [float(r.pnl_quote) for r in ok if r.pnl_quote is not None]
    pnl_pcts = [float(r.pnl_pct) for r in ok if r.pnl_pct is not None]
    wins = [x for x in pnl_quotes if x > 0.0]
    losses = [x for x in pnl_quotes if x < 0.0]

    out: Dict[str, object] = {
        "windows_total": int(len(rows)),
        "windows_ok": int(len(ok)),
        "windows_failed": int(len(failed)),
        "sum_pnl_quote": float(sum(pnl_quotes)) if pnl_quotes else 0.0,
        "avg_pnl_pct": float(statistics.fmean(pnl_pcts)) if pnl_pcts else 0.0,
        "median_pnl_pct": float(statistics.median(pnl_pcts)) if pnl_pcts else 0.0,
        "win_rate": float((len(wins) / len(ok)) * 100.0) if ok else 0.0,
        "max_gain_pct": float(max(pnl_pcts)) if pnl_pcts else 0.0,
        "max_loss_pct": float(min(pnl_pcts)) if pnl_pcts else 0.0,
    }
    start_blocker_counts_total = _merge_reason_counts(
        [r.start_blocker_counts or {} for r in ok if r.start_blocker_counts is not None]
    )
    start_counterfactual_single_counts_total = _merge_reason_counts(
        [r.start_counterfactual_single_counts or {} for r in ok if r.start_counterfactual_single_counts is not None]
    )
    start_counterfactual_combo_counts_total = _merge_reason_counts(
        [r.start_counterfactual_combo_counts or {} for r in ok if r.start_counterfactual_combo_counts is not None]
    )
    hold_reason_counts_total = _merge_reason_counts(
        [r.hold_reason_counts or {} for r in ok if r.hold_reason_counts is not None]
    )
    stop_reason_counts_total = _merge_reason_counts(
        [r.stop_reason_counts or {} for r in ok if r.stop_reason_counts is not None]
    )
    stop_event_reason_counts_total = _merge_reason_counts(
        [r.stop_event_reason_counts or {} for r in ok if r.stop_event_reason_counts is not None]
    )
    stop_reason_counts_combined_total = _merge_reason_counts(
        [r.stop_reason_counts_combined or {} for r in ok if r.stop_reason_counts_combined is not None]
    )
    out["start_blocker_counts_total"] = start_blocker_counts_total
    out["start_counterfactual_single_counts_total"] = start_counterfactual_single_counts_total
    out["start_counterfactual_combo_counts_total"] = start_counterfactual_combo_counts_total
    out["hold_reason_counts_total"] = hold_reason_counts_total
    out["stop_reason_counts_total"] = stop_reason_counts_total
    out["stop_event_reason_counts_total"] = stop_event_reason_counts_total
    out["stop_reason_counts_combined_total"] = stop_reason_counts_combined_total
    out["top_start_blocker"] = _top_reason(start_blocker_counts_total)
    out["top_start_counterfactual_single"] = _top_reason(start_counterfactual_single_counts_total)
    out["top_start_counterfactual_combo"] = _top_reason(start_counterfactual_combo_counts_total)
    out["top_stop_reason"] = _top_reason(stop_reason_counts_combined_total)

    if losses:
        out["profit_factor"] = float(sum(wins) / abs(sum(losses))) if wins else 0.0
    else:
        out["profit_factor"] = None if not wins else float("inf")
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timerange", required=True, help="Global range: YYYYMMDD-YYYYMMDD")
    ap.add_argument("--window-days", type=int, default=7)
    ap.add_argument("--step-days", type=int, default=7)
    ap.add_argument("--min-window-days", type=int, default=2)

    ap.add_argument("--pair", default="ETH/USDT")
    ap.add_argument("--exchange", default="binance")
    ap.add_argument("--timeframe", default="15m")

    ap.add_argument("--start-quote", type=float, default=1000.0)
    ap.add_argument("--start-base", type=float, default=0.0)
    ap.add_argument("--carry-capital", action="store_true", help="Carry end balances into next window")

    ap.add_argument("--fee-pct", type=float, default=0.10)
    ap.add_argument("--max-orders-per-side", type=int, default=40)
    ap.add_argument("--close-on-stop", action="store_true")
    ap.add_argument("--reverse-fill", action="store_true")

    ap.add_argument("--config-path", default="/freqtrade/user_data/config.json")
    ap.add_argument("--strategy", default="GridBrainV1")
    ap.add_argument("--strategy-path", default="/freqtrade/user_data/strategies")
    ap.add_argument("--data-dir", default="/freqtrade/user_data/data/binance")

    ap.add_argument("--run-id", default=None, help="Output subdir under user_data/walkforward")
    ap.add_argument("--service", default="freqtrade", help="docker compose service")
    ap.add_argument("--skip-backtesting", action="store_true")
    ap.add_argument("--backtesting-extra", default="", help="Extra args appended to freqtrade backtesting command")
    ap.add_argument("--sim-extra", default="", help="Extra args appended to simulator command")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--fail-on-window-error", action="store_true")
    ap.add_argument(
        "--allow-overlap",
        action="store_true",
        help="Allow overlapping windows (step-days < window-days).",
    )
    ap.add_argument(
        "--allow-single-plan",
        action="store_true",
        help="Allow windows with only one plan snapshot (disables time-varying coverage enforcement).",
    )
    return ap


def main() -> int:
    args = build_parser().parse_args()
    if int(args.window_days) <= 0:
        raise ValueError(f"window-days must be > 0 (got {args.window_days})")
    if int(args.step_days) <= 0:
        raise ValueError(f"step-days must be > 0 (got {args.step_days})")
    if (not bool(args.allow_overlap)) and int(args.step_days) < int(args.window_days):
        raise ValueError(
            "Overlapping windows are disabled by default: "
            f"step-days ({args.step_days}) must be >= window-days ({args.window_days}). "
            "Use --allow-overlap to override."
        )

    root_dir = Path(__file__).resolve().parents[1]
    user_data_dir = root_dir / "user_data"
    if not user_data_dir.is_dir():
        raise FileNotFoundError(f"user_data directory not found: {user_data_dir}")

    start, end = parse_day_timerange(args.timerange)
    windows = iter_windows(start, end, args.window_days, args.step_days, args.min_window_days)
    if not windows:
        raise ValueError("No windows produced. Adjust timerange/window-days/step-days.")

    run_id = args.run_id or datetime.now(timezone.utc).strftime("wf_%Y%m%dT%H%M%SZ")
    out_dir = user_data_dir / "walkforward" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    pair_fs = args.pair.replace("/", "_").replace(":", "_")
    src_plan_dir = user_data_dir / "grid_plans" / args.exchange / pair_fs

    print(f"[walkforward] windows={len(windows)} out_dir={out_dir}", flush=True)

    rows: List[WindowResult] = []
    cur_quote = float(args.start_quote)
    cur_base = float(args.start_base)

    for idx, ws, we in windows:
        timerange = f"{fmt_day(ws)}-{fmt_day(we)}"
        print(
            f"[walkforward] window {idx}/{len(windows)} timerange={timerange} "
            f"start_quote={cur_quote:.6f} start_base={cur_base:.6f}",
            flush=True,
        )

        row = WindowResult(
            index=idx,
            timerange=timerange,
            start_day=fmt_day(ws),
            end_day=fmt_day(we),
            status="ok",
        )

        try:
            window_started_epoch = time.time()
            if not args.skip_backtesting:
                if src_plan_dir.exists():
                    shutil.rmtree(src_plan_dir)
                backtesting_inner = (
                    f"freqtrade backtesting "
                    f"--config {q(args.config_path)} "
                    f"--strategy {q(args.strategy)} "
                    f"--strategy-path {q(args.strategy_path)} "
                    f"--timerange {q(timerange)} "
                    f"--timeframe {q(args.timeframe)} "
                    f"--datadir {q(args.data_dir)} "
                    f"--cache none"
                )
                if args.backtesting_extra.strip():
                    backtesting_inner = f"{backtesting_inner} {args.backtesting_extra.strip()}"
                run_compose_inner(root_dir, args.service, backtesting_inner, dry_run=args.dry_run)

            window_plan_dir = out_dir / f"window_{idx:03d}_plans"
            min_mtime_epoch = None if args.skip_backtesting else (window_started_epoch - 5.0)
            plan_count = extract_window_plans(
                src_plan_dir,
                window_plan_dir,
                ws,
                we,
                min_mtime_epoch=min_mtime_epoch,
            )
            row.plans_file_count = int(plan_count)
            if plan_count <= 0:
                raise RuntimeError(
                    f"No plan snapshots found for window {timerange} under {src_plan_dir}"
                )
            if plan_count < 2 and not bool(args.allow_single_plan):
                raise RuntimeError(
                    f"Window {timerange} has only {plan_count} plan snapshot(s). "
                    f"Expected time-varying replay with >=2 snapshots."
                )

            plan_window_latest_local = window_plan_dir / "grid_plan.latest.json"
            plan_window_latest_container = to_container_user_data_path(plan_window_latest_local, user_data_dir)
            plan_window_dir_container = to_container_user_data_path(window_plan_dir, user_data_dir)

            result_local = out_dir / f"window_{idx:03d}.result.json"
            result_container = to_container_user_data_path(result_local, user_data_dir)

            fill_flag = "--reverse-fill" if args.reverse_fill else "--touch-fill"
            close_flag = "--close-on-stop" if args.close_on_stop else ""
            sim_inner = (
                f"python /freqtrade/user_data/scripts/grid_simulator_v1.py "
                f"--pair {q(args.pair)} "
                f"--timeframe {q(args.timeframe)} "
                f"--data-dir {q(args.data_dir)} "
                f"--plan {q(plan_window_latest_container)} "
                f"--plans-dir {q(plan_window_dir_container)} "
                f"--replay-plans "
                f"--timerange {q(timerange)} "
                f"--start-at {q(fmt_day(ws))} "
                f"--start-quote {cur_quote:.12f} "
                f"--start-base {cur_base:.12f} "
                f"--fee-pct {float(args.fee_pct):.12f} "
                f"--max-orders-per-side {int(args.max_orders_per_side)} "
                f"{fill_flag} {close_flag} "
                f"--out {q(result_container)}"
            )
            if args.sim_extra.strip():
                sim_inner = f"{sim_inner} {args.sim_extra.strip()}"
            run_compose_inner(root_dir, args.service, sim_inner, dry_run=args.dry_run)

            row.result_file = str(result_local)
            if not args.dry_run:
                sim = load_sim_summary(result_local)
                row.pnl_quote = sim["pnl_quote"]
                row.pnl_pct = sim["pnl_pct"]
                row.initial_equity = sim["initial_equity"]
                row.end_equity = sim["end_equity"]
                row.fills = sim["fills"]
                row.stop_events = sim["stop_events"]
                row.seed_events = sim["seed_events"]
                row.rebuild_events = sim["rebuild_events"]
                row.soft_adjust_events = sim["soft_adjust_events"]
                row.action_start = sim["action_start"]
                row.action_hold = sim["action_hold"]
                row.action_stop = sim["action_stop"]
                row.start_blocker_counts = sim["start_blocker_counts"]
                row.start_counterfactual_single_counts = sim["start_counterfactual_single_counts"]
                row.start_counterfactual_combo_counts = sim["start_counterfactual_combo_counts"]
                row.hold_reason_counts = sim["hold_reason_counts"]
                row.stop_reason_counts = sim["stop_reason_counts"]
                row.stop_event_reason_counts = sim["stop_event_reason_counts"]
                row.stop_reason_counts_combined = sim["stop_reason_counts_combined"]
                row.top_start_blocker = sim["top_start_blocker"]
                row.top_start_counterfactual_single = sim["top_start_counterfactual_single"]
                row.top_start_counterfactual_combo = sim["top_start_counterfactual_combo"]
                row.top_stop_reason = sim["top_stop_reason"]
                print(
                    f"[walkforward] window {idx} reason_top "
                    f"start_blocker={row.top_start_blocker or 'n/a'} "
                    f"start_cf={row.top_start_counterfactual_combo or 'n/a'} "
                    f"stop={row.top_stop_reason or 'n/a'}",
                    flush=True,
                )
                if args.carry_capital:
                    cur_quote = float(sim["end_quote"])
                    cur_base = float(sim["end_base"])
            elif not args.carry_capital:
                cur_quote = float(args.start_quote)
                cur_base = float(args.start_base)
        except Exception as exc:
            row.status = "error"
            row.error = str(exc)
            if not args.carry_capital:
                cur_quote = float(args.start_quote)
                cur_base = float(args.start_base)

        rows.append(row)
        if row.status != "ok":
            print(f"[walkforward] window {idx} ERROR: {row.error}", flush=True)

        if (not args.carry_capital) and row.status == "ok":
            cur_quote = float(args.start_quote)
            cur_base = float(args.start_base)

    agg = aggregate(rows)
    summary = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "args": vars(args),
        "aggregate": agg,
        "windows": [r.as_dict() for r in rows],
    }

    summary_path = out_dir / "summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    csv_path = out_dir / "windows.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].as_dict().keys()) if rows else [])
        if rows:
            writer.writeheader()
            for r in rows:
                writer.writerow(r.as_dict())

    print(f"[walkforward] wrote {summary_path}", flush=True)
    print(f"[walkforward] wrote {csv_path}", flush=True)
    print(f"[walkforward] aggregate: {agg}", flush=True)

    if args.fail_on_window_error and any(r.status != "ok" for r in rows):
        return 1
    if int(agg.get("windows_ok", 0)) == 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
