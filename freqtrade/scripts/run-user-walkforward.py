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
import ast
import csv
import json
import math
import os
import re
import shlex
import shutil
import statistics
import subprocess
import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from latest_refs import publish_latest_ref, rel_payload_path
from run_state import RunStateTracker
from long_run_monitor import LongRunMonitor, MonitorConfig

REPO_ROOT = Path(__file__).resolve().parents[2]
FREQTRADE_ROOT = REPO_ROOT / "freqtrade"
DEFAULT_USER_DATA = FREQTRADE_ROOT / "user_data"
DEFAULT_COMPOSE_FILE = REPO_ROOT / "docker-compose.grid.yml"


@dataclass
class WindowResult:
    index: int
    timerange: str
    start_day: str
    end_day: str
    status: str
    error: str = ""
    error_report_file: str = ""
    result_file: str = ""
    plans_file_count: int = 0
    pnl_quote: Optional[float] = None
    pnl_pct: Optional[float] = None
    initial_equity: Optional[float] = None
    end_equity: Optional[float] = None
    end_quote: Optional[float] = None
    end_base: Optional[float] = None
    fills: Optional[int] = None
    stop_events: Optional[int] = None
    seed_events: Optional[int] = None
    rebuild_events: Optional[int] = None
    soft_adjust_events: Optional[int] = None
    action_start: Optional[int] = None
    action_hold: Optional[int] = None
    action_stop: Optional[int] = None
    mode_plan_counts: Optional[Dict[str, int]] = None
    mode_desired_counts: Optional[Dict[str, int]] = None
    raw_action_mode_counts: Optional[Dict[str, int]] = None
    effective_action_mode_counts: Optional[Dict[str, int]] = None
    fill_mode_counts: Optional[Dict[str, int]] = None
    fill_mode_side_counts: Optional[Dict[str, int]] = None
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
            "error_report_file": self.error_report_file,
            "result_file": self.result_file,
            "plans_file_count": self.plans_file_count,
            "pnl_quote": self.pnl_quote,
            "pnl_pct": self.pnl_pct,
            "initial_equity": self.initial_equity,
            "end_equity": self.end_equity,
            "end_quote": self.end_quote,
            "end_base": self.end_base,
            "fills": self.fills,
            "stop_events": self.stop_events,
            "seed_events": self.seed_events,
            "rebuild_events": self.rebuild_events,
            "soft_adjust_events": self.soft_adjust_events,
            "action_start": self.action_start,
            "action_hold": self.action_hold,
            "action_stop": self.action_stop,
            "mode_plan_counts": json.dumps(self.mode_plan_counts or {}, sort_keys=True),
            "mode_desired_counts": json.dumps(self.mode_desired_counts or {}, sort_keys=True),
            "raw_action_mode_counts": json.dumps(self.raw_action_mode_counts or {}, sort_keys=True),
            "effective_action_mode_counts": json.dumps(self.effective_action_mode_counts or {}, sort_keys=True),
            "fill_mode_counts": json.dumps(self.fill_mode_counts or {}, sort_keys=True),
            "fill_mode_side_counts": json.dumps(self.fill_mode_side_counts or {}, sort_keys=True),
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


def _resolve_repo_path(value: str) -> Path:
    text = str(value or "").strip()
    if not text:
        return Path(text)
    candidate = Path(text)
    if candidate.is_absolute():
        return candidate.resolve()
    return (REPO_ROOT / candidate).resolve()


def _resolve_host_and_container_path(value: str) -> Tuple[Path, str]:
    text = str(value or "").strip()
    if not text:
        raise ValueError("Path value cannot be empty.")

    # Accept already-containerized paths and map them back to host for validation.
    if text == "/freqtrade" or text.startswith("/freqtrade/"):
        rel = Path(text).relative_to("/freqtrade")
        return (FREQTRADE_ROOT / rel).resolve(), text
    if text == "/workspace" or text.startswith("/workspace/"):
        rel = Path(text).relative_to("/workspace")
        return (REPO_ROOT / rel).resolve(), text

    host_path = _resolve_repo_path(text)
    host_resolved = host_path.resolve()
    repo_root_resolved = REPO_ROOT.resolve()
    freqtrade_root_resolved = FREQTRADE_ROOT.resolve()
    try:
        rel = host_resolved.relative_to(freqtrade_root_resolved)
        return host_resolved, f"/freqtrade/{rel.as_posix()}"
    except Exception:
        pass
    try:
        rel = host_resolved.relative_to(repo_root_resolved)
        return host_resolved, f"/workspace/{rel.as_posix()}"
    except Exception:
        pass
    raise ValueError(
        f"Path is not mounted into container (expected under {freqtrade_root_resolved} or {repo_root_resolved}): {host_resolved}"
    )


def _timeframe_to_minutes(timeframe: str) -> int:
    text = str(timeframe or "").strip().lower()
    match = re.fullmatch(r"(\d+)([mhdw])", text)
    if not match:
        raise ValueError(f"Unsupported timeframe format: {timeframe!r} (expected like 15m, 1h, 4h, 1d)")
    value = int(match.group(1))
    unit = str(match.group(2))
    unit_minutes = {
        "m": 1,
        "h": 60,
        "d": 60 * 24,
        "w": 60 * 24 * 7,
    }
    return int(max(value, 1) * unit_minutes[unit])


def _ast_numeric_value(node: ast.AST) -> Optional[float]:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        raw = _ast_numeric_value(node.operand)
        if raw is None:
            return None
        return float(raw) if isinstance(node.op, ast.UAdd) else -float(raw)
    if isinstance(node, ast.BinOp):
        left = _ast_numeric_value(node.left)
        right = _ast_numeric_value(node.right)
        if left is None or right is None:
            return None
        if isinstance(node.op, ast.Add):
            return float(left + right)
        if isinstance(node.op, ast.Sub):
            return float(left - right)
        if isinstance(node.op, ast.Mult):
            return float(left * right)
        if isinstance(node.op, ast.Div):
            if float(right) == 0.0:
                return None
            return float(left / right)
        if isinstance(node.op, ast.FloorDiv):
            if float(right) == 0.0:
                return None
            return float(left // right)
        if isinstance(node.op, ast.Mod):
            if float(right) == 0.0:
                return None
            return float(left % right)
    return None


def _extract_class_numeric_assignments(class_node: ast.ClassDef) -> Dict[str, float]:
    attrs: Dict[str, float] = {}
    for stmt in class_node.body:
        target_name: Optional[str] = None
        value_node: Optional[ast.AST] = None
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
            target_name = str(stmt.targets[0].id)
            value_node = stmt.value
        elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            target_name = str(stmt.target.id)
            value_node = stmt.value
        if not target_name or value_node is None:
            continue
        raw = _ast_numeric_value(value_node)
        if raw is None:
            continue
        attrs[target_name] = float(raw)
    return attrs


def _extract_lookback_suffixes(tree: ast.Module) -> Tuple[str, ...]:
    default_suffixes = ("_bars", "_lookback", "_window", "_period")
    for stmt in tree.body:
        if not isinstance(stmt, ast.Assign):
            continue
        if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
            continue
        if str(stmt.targets[0].id) != "LOOKBACK_SUFFIXES":
            continue
        value = stmt.value
        if not isinstance(value, (ast.Tuple, ast.List)):
            continue
        out: List[str] = []
        for item in value.elts:
            if isinstance(item, ast.Constant) and isinstance(item.value, str):
                text = str(item.value).strip()
                if text:
                    out.append(text)
        if out:
            return tuple(out)
    return default_suffixes


def _collect_class_attrs_recursive(
    class_name: str,
    class_nodes: Dict[str, ast.ClassDef],
    cache: Dict[str, Dict[str, float]],
    visiting: Optional[set] = None,
) -> Dict[str, float]:
    if class_name in cache:
        return dict(cache[class_name])
    if visiting is None:
        visiting = set()
    if class_name in visiting:
        return {}
    node = class_nodes.get(class_name)
    if node is None:
        return {}
    visiting.add(class_name)
    merged: Dict[str, float] = {}
    for base in node.bases:
        base_name: Optional[str] = None
        if isinstance(base, ast.Name):
            base_name = str(base.id)
        elif isinstance(base, ast.Attribute):
            base_name = str(base.attr)
        if base_name and base_name in class_nodes:
            merged.update(_collect_class_attrs_recursive(base_name, class_nodes, cache, visiting))
    merged.update(_extract_class_numeric_assignments(node))
    visiting.remove(class_name)
    cache[class_name] = dict(merged)
    return dict(merged)


def _estimate_strategy_startup_candles(strategy_file: Path, strategy_name: str) -> Optional[int]:
    try:
        source = strategy_file.read_text(encoding="utf-8")
    except Exception:
        return None
    try:
        tree = ast.parse(source, filename=str(strategy_file))
    except Exception:
        return None
    class_nodes = {
        str(node.name): node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
    }
    if strategy_name not in class_nodes:
        return None
    attrs = _collect_class_attrs_recursive(strategy_name, class_nodes, cache={})
    suffixes = _extract_lookback_suffixes(tree)

    lookback_values: List[int] = []
    for key, raw_value in attrs.items():
        if not isinstance(raw_value, (int, float)):
            continue
        key_s = str(key)
        if not any(key_s.endswith(s) for s in suffixes):
            continue
        lookback_values.append(int(math.ceil(float(raw_value))))

    lookback_buffer = int(max(0, math.ceil(float(attrs.get("lookback_buffer", 0.0)))))
    startup_attr = int(max(0, math.ceil(float(attrs.get("startup_candle_count", 0.0)))))
    required_from_lookbacks = (max(lookback_values) + lookback_buffer) if lookback_values else 0
    required = int(max(startup_attr, required_from_lookbacks))
    return required if required > 0 else None


def _locate_strategy_source_file(strategy_path: Path, strategy_name: str) -> Optional[Path]:
    direct = strategy_path / f"{strategy_name}.py"
    if direct.is_file():
        return direct.resolve()

    class_pat = re.compile(rf"^\s*class\s+{re.escape(str(strategy_name))}\b", re.MULTILINE)
    for candidate in sorted(strategy_path.glob("*.py")):
        try:
            text = candidate.read_text(encoding="utf-8")
        except Exception:
            continue
        if class_pat.search(text):
            return candidate.resolve()
    return None


def emit_run_marker(label: str, **meta: object) -> None:
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "marker": label,
    }
    payload.update(meta)
    print(json.dumps(payload, sort_keys=True), flush=True)


def _collect_resume_mismatches(
    existing_args: Dict[str, object],
    current_args: argparse.Namespace,
) -> Tuple[List[Tuple[str, object, object]], List[Tuple[str, object, object]]]:
    compare_keys = (
        "window_days",
        "step_days",
        "min_window_days",
        "pair",
        "exchange",
        "timeframe",
        "strategy",
        "strategy_path",
        "data_dir",
        "config_path",
        "start_quote",
        "start_base",
        "carry_capital",
        "fee_pct",
        "max_orders_per_side",
        "close_on_stop",
        "reverse_fill",
        "regime_threshold_profile",
        "mode_thresholds_path",
        "backtest_warmup_candles",
        "backtesting_extra",
        "sim_extra",
    )
    core_resume_keys = {
        "window_days",
        "step_days",
        "min_window_days",
        "pair",
        "exchange",
        "timeframe",
        "strategy",
        "strategy_path",
    }
    trim_keys = {"mode_thresholds_path", "strategy_path", "config_path", "data_dir"}
    mismatches: List[Tuple[str, object, object]] = []
    for key in compare_keys:
        cur = getattr(current_args, key, None)
        prev = existing_args.get(key, None)
        if key in trim_keys:
            cur = str(cur or "").strip()
            prev = str(prev or "").strip()
        if cur != prev:
            mismatches.append((key, cur, prev))

    fatal_mismatches = [m for m in mismatches if m[0] in core_resume_keys]
    optional_mismatches = [m for m in mismatches if m[0] not in core_resume_keys]
    return fatal_mismatches, optional_mismatches


def _safe_path_fragment(text: str) -> str:
    raw = str(text or "")
    out = "".join(ch if (ch.isalnum() or ch in ("-", "_")) else "_" for ch in raw)
    out = out.strip("_")
    return out or "run"


_TRANSIENT_ERROR_PATTERNS: List[re.Pattern[str]] = [
    re.compile(r"RequestTimeout", re.IGNORECASE),
    re.compile(r"TemporaryError", re.IGNORECASE),
    re.compile(r"Could not load markets", re.IGNORECASE),
    re.compile(r"timed?\s*out", re.IGNORECASE),
    re.compile(r"Too Many Requests", re.IGNORECASE),
    re.compile(r"\b429\b"),
    re.compile(r"DDoSProtection", re.IGNORECASE),
    re.compile(r"NetworkError", re.IGNORECASE),
    re.compile(r"ServiceUnavailable", re.IGNORECASE),
    re.compile(r"Connection (?:reset|aborted|refused)", re.IGNORECASE),
]


def _is_transient_error(text: str) -> bool:
    payload = str(text or "")
    if not payload:
        return False
    return any(p.search(payload) for p in _TRANSIENT_ERROR_PATTERNS)


def _write_window_error_report(
    out_dir: Path,
    run_id: str,
    window_index: int,
    timerange: str,
    stage: str,
    stage_cmd: str,
    exc: Exception,
) -> Path:
    err_dir = out_dir / "errors"
    err_dir.mkdir(parents=True, exist_ok=True)
    report_path = err_dir / f"window_{int(window_index):03d}.error.json"
    err_text = str(exc) or repr(exc)
    payload = {
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": str(run_id),
        "window_index": int(window_index),
        "timerange": str(timerange),
        "stage": str(stage or ""),
        "stage_cmd": str(stage_cmd or ""),
        "error_type": type(exc).__name__,
        "error": err_text,
        "error_transient": int(_is_transient_error(err_text)),
        "traceback": traceback.format_exc(),
    }
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    return report_path


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


def _proc_usage(pid: int) -> Dict[str, object]:
    stat_path = Path(f"/proc/{int(pid)}/stat")
    if not stat_path.exists():
        return {}
    try:
        raw = stat_path.read_text(encoding="utf-8")
        rparen = raw.rfind(")")
        if rparen < 0:
            return {}
        rest = raw[rparen + 2 :].split()
        utime = float(rest[11])
        stime = float(rest[12])
        rss_pages = int(rest[21])
        clk = float(os.sysconf("SC_CLK_TCK"))
        page_size = float(os.sysconf("SC_PAGE_SIZE"))
        cpu_sec = (utime + stime) / clk
        rss_mb = (rss_pages * page_size) / (1024.0 * 1024.0)
        return {"cpu_sec": round(cpu_sec, 3), "rss_mb": round(rss_mb, 1)}
    except Exception:
        return {}


def _format_pct(done: int, total: int) -> str:
    if int(total) <= 0:
        return "0.00%"
    return f"{(100.0 * float(done) / float(total)):.2f}%"


def _count_plan_files(plan_dir: Path) -> int:
    if not plan_dir.is_dir():
        return 0
    n = 0
    for p in plan_dir.glob("grid_plan*.json"):
        if p.is_file():
            n += 1
    return n


def _probe_path_sizes(paths: Dict[str, Path]) -> Dict[str, object]:
    out: Dict[str, object] = {}
    for key, path in paths.items():
        if path.exists():
            try:
                out[f"{key}_bytes"] = int(path.stat().st_size)
            except Exception:
                out[f"{key}_bytes"] = -1
        else:
            out[f"{key}_bytes"] = 0
    return out


def _compose_env() -> Dict[str, str]:
    env = dict(os.environ)
    try:
        env.setdefault("GRID_UID", str(os.getuid()))
        env.setdefault("GRID_GID", str(os.getgid()))
    except Exception:
        pass
    return env


def run_compose_inner(
    project_dir: Path,
    compose_file: Path,
    service: str,
    inner_cmd: str,
    env_exports: Optional[List[str]] = None,
    heartbeat_sec: int = 60,
    progress_label: str = "",
    progress_probe: Optional[Callable[[], Dict[str, object]]] = None,
    stalled_heartbeats_max: int = 0,
    dry_run: bool = False,
) -> None:
    if env_exports:
        exports = [str(x).strip() for x in env_exports if str(x).strip()]
        if exports:
            inner_cmd = f"{'; '.join(exports)}; {inner_cmd}"
    cmd = [
        "docker",
        "compose",
        "-f",
        str(compose_file),
        "run",
        "--rm",
        "--entrypoint",
        "bash",
        service,
        "-lc",
        inner_cmd,
    ]
    print(f"[walkforward] $ {' '.join(shlex.quote(x) for x in cmd)}", flush=True)
    if dry_run:
        return
    hb = int(heartbeat_sec)
    if hb <= 0:
        subprocess.run(cmd, cwd=str(project_dir), env=_compose_env(), check=True)
        return
    proc = subprocess.Popen(cmd, cwd=str(project_dir), env=_compose_env())
    started = time.time()
    label = str(progress_label).strip() or "compose"
    last_probe: Dict[str, object] = {}
    stale_heartbeats = 0
    stale_max = int(max(0, int(stalled_heartbeats_max)))
    while True:
        try:
            rc = proc.wait(timeout=hb)
            if rc != 0:
                raise subprocess.CalledProcessError(rc, cmd)
            return
        except subprocess.TimeoutExpired:
            elapsed = int(max(0.0, time.time() - started))
            usage = _proc_usage(int(proc.pid))
            probe: Dict[str, object] = {}
            if progress_probe is not None:
                try:
                    probe = progress_probe() or {}
                except Exception as exc:
                    probe = {"probe_error": str(exc)}
            changed = int(probe != last_probe)
            last_probe = dict(probe)
            if changed:
                stale_heartbeats = 0
            else:
                stale_heartbeats += 1
            usage_txt = " ".join(f"{k}={v}" for k, v in usage.items())
            probe_txt = json.dumps(probe, sort_keys=True) if probe else "{}"
            print(
                f"[walkforward] heartbeat stage={label} elapsed_sec={elapsed} {usage_txt} "
                f"progress_changed={changed} stale_heartbeats={stale_heartbeats} probe={probe_txt} still_running=1",
                flush=True,
            )
            if stale_max > 0 and stale_heartbeats >= stale_max:
                try:
                    proc.terminate()
                except Exception:
                    pass
                raise TimeoutError(
                    f"Stalled: no observable probe progress for {stale_heartbeats} heartbeats at stage={label}."
                )
        except KeyboardInterrupt:
            try:
                proc.terminate()
            except Exception:
                pass
            raise


def _to_float_optional(value: object) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except Exception:
        return None


def _to_int_optional(value: object) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except Exception:
        return None


def _to_dict_counts(value: object) -> Dict[str, int]:
    raw = value
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return {}
        try:
            raw = json.loads(text)
        except Exception:
            return {}
    if raw is None:
        return {}
    return _coerce_reason_counts(raw)


def window_result_from_dict(raw: Dict) -> WindowResult:
    return WindowResult(
        index=int(raw.get("index")),
        timerange=str(raw.get("timerange", "")),
        start_day=str(raw.get("start_day", "")),
        end_day=str(raw.get("end_day", "")),
        status=str(raw.get("status", "")),
        error=str(raw.get("error", "")),
        error_report_file=str(raw.get("error_report_file", "")),
        result_file=str(raw.get("result_file", "")),
        plans_file_count=int(raw.get("plans_file_count") or 0),
        pnl_quote=_to_float_optional(raw.get("pnl_quote")),
        pnl_pct=_to_float_optional(raw.get("pnl_pct")),
        initial_equity=_to_float_optional(raw.get("initial_equity")),
        end_equity=_to_float_optional(raw.get("end_equity")),
        end_quote=_to_float_optional(raw.get("end_quote")),
        end_base=_to_float_optional(raw.get("end_base")),
        fills=_to_int_optional(raw.get("fills")),
        stop_events=_to_int_optional(raw.get("stop_events")),
        seed_events=_to_int_optional(raw.get("seed_events")),
        rebuild_events=_to_int_optional(raw.get("rebuild_events")),
        soft_adjust_events=_to_int_optional(raw.get("soft_adjust_events")),
        action_start=_to_int_optional(raw.get("action_start")),
        action_hold=_to_int_optional(raw.get("action_hold")),
        action_stop=_to_int_optional(raw.get("action_stop")),
        mode_plan_counts=_to_dict_counts(raw.get("mode_plan_counts")),
        mode_desired_counts=_to_dict_counts(raw.get("mode_desired_counts")),
        raw_action_mode_counts=_to_dict_counts(raw.get("raw_action_mode_counts")),
        effective_action_mode_counts=_to_dict_counts(raw.get("effective_action_mode_counts")),
        fill_mode_counts=_to_dict_counts(raw.get("fill_mode_counts")),
        fill_mode_side_counts=_to_dict_counts(raw.get("fill_mode_side_counts")),
        start_blocker_counts=_to_dict_counts(raw.get("start_blocker_counts")),
        start_counterfactual_single_counts=_to_dict_counts(raw.get("start_counterfactual_single_counts")),
        start_counterfactual_combo_counts=_to_dict_counts(raw.get("start_counterfactual_combo_counts")),
        hold_reason_counts=_to_dict_counts(raw.get("hold_reason_counts")),
        stop_reason_counts=_to_dict_counts(raw.get("stop_reason_counts")),
        stop_event_reason_counts=_to_dict_counts(raw.get("stop_event_reason_counts")),
        stop_reason_counts_combined=_to_dict_counts(raw.get("stop_reason_counts_combined")),
        top_start_blocker=(str(raw.get("top_start_blocker")) if raw.get("top_start_blocker") not in (None, "") else None),
        top_start_counterfactual_single=(
            str(raw.get("top_start_counterfactual_single"))
            if raw.get("top_start_counterfactual_single") not in (None, "")
            else None
        ),
        top_start_counterfactual_combo=(
            str(raw.get("top_start_counterfactual_combo"))
            if raw.get("top_start_counterfactual_combo") not in (None, "")
            else None
        ),
        top_stop_reason=(str(raw.get("top_stop_reason")) if raw.get("top_stop_reason") not in (None, "") else None),
    )


def write_outputs(out_dir: Path, run_id: str, args: argparse.Namespace, rows: List[WindowResult]) -> Tuple[Path, Path, Dict]:
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
    return summary_path, csv_path, agg


def aggregate_brief(agg: Dict) -> Dict:
    keys = [
        "windows_total",
        "windows_ok",
        "windows_failed",
        "sum_pnl_quote",
        "avg_pnl_pct",
        "median_pnl_pct",
        "win_rate",
        "profit_factor",
        "max_gain_pct",
        "max_loss_pct",
        "top_start_blocker",
        "top_start_counterfactual_combo",
        "top_stop_reason",
    ]
    out: Dict[str, object] = {}
    for k in keys:
        out[k] = agg.get(k)
    return out


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


def _project_action_mode_counts(counter: Dict[str, int], action: str) -> Dict[str, int]:
    out: Dict[str, int] = {}
    prefix = f"{str(action or '').strip().upper()}|"
    if not prefix.strip("|"):
        return out
    for raw_key, raw_val in (counter or {}).items():
        key = str(raw_key or "")
        if not key.startswith(prefix):
            continue
        mode = key[len(prefix) :].strip() or "unknown"
        out[mode] = int(out.get(mode, 0)) + int(raw_val or 0)
    return {k: int(v) for k, v in sorted(out.items(), key=lambda kv: (-int(kv[1]), str(kv[0])))}


def _count_shares(counter: Dict[str, int]) -> Dict[str, float]:
    total = int(sum(int(v) for v in (counter or {}).values()))
    if total <= 0:
        return {}
    out: Dict[str, float] = {}
    for k, v in (counter or {}).items():
        out[str(k)] = round(float(int(v) / total), 6)
    return {k: float(v) for k, v in sorted(out.items(), key=lambda kv: (-float(kv[1]), str(kv[0])))}


def load_sim_summary(result_path: Path) -> Dict:
    with result_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    summary = payload.get("summary", {}) or {}
    fills = payload.get("fills", []) or []
    actions = summary.get("actions", {}) or {}
    mode_plan_counts = _coerce_reason_counts(summary.get("mode_plan_counts", {}))
    mode_desired_counts = _coerce_reason_counts(summary.get("mode_desired_counts", {}))
    raw_action_mode_counts = _coerce_reason_counts(summary.get("raw_action_mode_counts", {}))
    effective_action_mode_counts = _coerce_reason_counts(summary.get("effective_action_mode_counts", {}))
    fill_mode_counts = _coerce_reason_counts(summary.get("fill_mode_counts", {}))
    fill_mode_side_counts = _coerce_reason_counts(summary.get("fill_mode_side_counts", {}))
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
        "mode_plan_counts": mode_plan_counts,
        "mode_desired_counts": mode_desired_counts,
        "raw_action_mode_counts": raw_action_mode_counts,
        "effective_action_mode_counts": effective_action_mode_counts,
        "fill_mode_counts": fill_mode_counts,
        "fill_mode_side_counts": fill_mode_side_counts,
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
    mode_plan_counts_total = _merge_reason_counts(
        [r.mode_plan_counts or {} for r in ok if r.mode_plan_counts is not None]
    )
    mode_desired_counts_total = _merge_reason_counts(
        [r.mode_desired_counts or {} for r in ok if r.mode_desired_counts is not None]
    )
    raw_action_mode_counts_total = _merge_reason_counts(
        [r.raw_action_mode_counts or {} for r in ok if r.raw_action_mode_counts is not None]
    )
    effective_action_mode_counts_total = _merge_reason_counts(
        [r.effective_action_mode_counts or {} for r in ok if r.effective_action_mode_counts is not None]
    )
    fill_mode_counts_total = _merge_reason_counts(
        [r.fill_mode_counts or {} for r in ok if r.fill_mode_counts is not None]
    )
    fill_mode_side_counts_total = _merge_reason_counts(
        [r.fill_mode_side_counts or {} for r in ok if r.fill_mode_side_counts is not None]
    )
    out["start_blocker_counts_total"] = start_blocker_counts_total
    out["start_counterfactual_single_counts_total"] = start_counterfactual_single_counts_total
    out["start_counterfactual_combo_counts_total"] = start_counterfactual_combo_counts_total
    out["hold_reason_counts_total"] = hold_reason_counts_total
    out["stop_reason_counts_total"] = stop_reason_counts_total
    out["stop_event_reason_counts_total"] = stop_event_reason_counts_total
    out["stop_reason_counts_combined_total"] = stop_reason_counts_combined_total
    out["mode_plan_counts_total"] = mode_plan_counts_total
    out["mode_desired_counts_total"] = mode_desired_counts_total
    out["raw_action_mode_counts_total"] = raw_action_mode_counts_total
    out["effective_action_mode_counts_total"] = effective_action_mode_counts_total
    out["fill_mode_counts_total"] = fill_mode_counts_total
    out["fill_mode_side_counts_total"] = fill_mode_side_counts_total
    out["start_mode_counts_total"] = _project_action_mode_counts(effective_action_mode_counts_total, "START")
    out["hold_mode_counts_total"] = _project_action_mode_counts(effective_action_mode_counts_total, "HOLD")
    out["stop_mode_counts_total"] = _project_action_mode_counts(effective_action_mode_counts_total, "STOP")
    out["mode_plan_shares_total"] = _count_shares(mode_plan_counts_total)
    out["mode_desired_shares_total"] = _count_shares(mode_desired_counts_total)
    out["start_mode_shares_total"] = _count_shares(out["start_mode_counts_total"])
    out["fill_mode_shares_total"] = _count_shares(fill_mode_counts_total)
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

    ap.add_argument("--config-path", default=str(DEFAULT_USER_DATA / "config.json"))
    ap.add_argument("--strategy", default="GridBrainV1")
    ap.add_argument("--strategy-path", default=str(DEFAULT_USER_DATA / "strategies"))
    ap.add_argument("--data-dir", default=str(DEFAULT_USER_DATA / "data" / "binance"))
    ap.add_argument("--user-data", default=str(DEFAULT_USER_DATA), help="Local user_data directory path.")

    ap.add_argument("--run-id", default=None, help="Output subdir under user_data/walkforward")
    ap.add_argument("--service", default="freqtrade", help="docker compose service")
    ap.add_argument(
        "--compose-file",
        default=str(DEFAULT_COMPOSE_FILE),
        help="docker compose file path (defaults to repo-level docker-compose.grid.yml)",
    )
    ap.add_argument(
        "--project-dir",
        default=str(REPO_ROOT),
        help="docker compose project directory (defaults to repo root).",
    )
    ap.add_argument("--regime-threshold-profile", default=None, help="Override profile via GRID_REGIME_THRESHOLD_PROFILE")
    ap.add_argument("--mode-thresholds-path", default=None, help="Path to mode threshold overrides json (sets GRID_MODE_THRESHOLDS_PATH)")
    ap.add_argument("--skip-backtesting", action="store_true")
    ap.add_argument(
        "--backtest-warmup-candles",
        type=int,
        default=-1,
        help="Warmup candles prepended to each backtesting window (-1=auto from strategy lookbacks, 0=disable).",
    )
    ap.add_argument("--backtesting-extra", default="", help="Extra args appended to freqtrade backtesting command")
    ap.add_argument("--sim-extra", default="", help="Extra args appended to simulator command")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resume", action="store_true", help="Resume existing run-id by skipping completed windows.")
    ap.add_argument(
        "--resume-require-result-files",
        action="store_true",
        help="With --resume, only skip a window if status=ok and result_file still exists.",
    )
    ap.add_argument(
        "--heartbeat-sec",
        type=int,
        default=60,
        help="Print periodic heartbeat while compose commands are running (0 disables).",
    )
    ap.add_argument(
        "--stalled-heartbeats-max",
        type=int,
        default=0,
        help="If >0, abort when probe output is unchanged for this many heartbeats.",
    )
    ap.add_argument(
        "--fail-on-window-error",
        action="store_true",
        help="Fail fast on first window error (stop run early and return non-zero).",
    )
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
    ap.add_argument(
        "--disable-run-state",
        action="store_true",
        help="Disable _state marker files (state.json + events.jsonl).",
    )
    ap.add_argument(
        "--enable-liveness",
        action="store_true",
        help="Print liveness + state marker lines and optionally run stall hooks.",
    )
    ap.add_argument(
        "--stall-threshold-sec",
        type=int,
        default=0,
        help="If >0 and liveness enabled, raise when no progress for this many seconds.",
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

    freqtrade_root = FREQTRADE_ROOT
    project_dir = _resolve_repo_path(args.project_dir)
    compose_file = _resolve_repo_path(args.compose_file)
    if not project_dir.is_dir():
        raise FileNotFoundError(f"Compose project directory missing (--project-dir): {project_dir}")
    if not compose_file.is_file():
        raise FileNotFoundError(f"Compose file missing (--compose-file): {compose_file}")
    user_data_dir = _resolve_repo_path(args.user_data)
    if not user_data_dir.is_dir():
        raise FileNotFoundError(f"user_data directory not found: {user_data_dir}")

    start, end = parse_day_timerange(args.timerange)
    windows = iter_windows(start, end, args.window_days, args.step_days, args.min_window_days)
    if not windows:
        raise ValueError("No windows produced. Adjust timerange/window-days/step-days.")
    config_path, config_path_container = _resolve_host_and_container_path(args.config_path)
    strategy_path, strategy_path_container = _resolve_host_and_container_path(args.strategy_path)
    data_dir, data_dir_container = _resolve_host_and_container_path(args.data_dir)
    if not config_path.is_file():
        raise FileNotFoundError(f"Config file missing (--config-path): {config_path}")
    if not strategy_path.is_dir():
        raise FileNotFoundError(f"Strategy path missing or invalid (--strategy-path): {strategy_path}")
    if not data_dir.is_dir():
        raise FileNotFoundError(f"Data directory missing (--data-dir): {data_dir}")
    if int(args.backtest_warmup_candles) < -1:
        raise ValueError(
            f"backtest-warmup-candles must be >= -1 (got {args.backtest_warmup_candles})"
        )

    timeframe_minutes = _timeframe_to_minutes(args.timeframe)
    warmup_source = "explicit"
    resolved_backtest_warmup_candles = int(args.backtest_warmup_candles)
    strategy_source_path: Optional[Path] = None
    if resolved_backtest_warmup_candles < 0:
        warmup_source = "auto"
        strategy_source_path = _locate_strategy_source_file(strategy_path, args.strategy)
        if strategy_source_path is not None:
            estimated = _estimate_strategy_startup_candles(strategy_source_path, args.strategy)
            if estimated is not None:
                resolved_backtest_warmup_candles = int(estimated)
            else:
                resolved_backtest_warmup_candles = 0
                warmup_source = "auto_unavailable"
        else:
            resolved_backtest_warmup_candles = 0
            warmup_source = "auto_unavailable"
    if resolved_backtest_warmup_candles < 0:
        resolved_backtest_warmup_candles = 0
    resolved_backtest_warmup_days = (
        int(math.ceil((float(resolved_backtest_warmup_candles) * float(timeframe_minutes)) / 1440.0))
        if resolved_backtest_warmup_candles > 0
        else 0
    )
    if int(args.backtest_warmup_candles) < 0:
        args.backtest_warmup_candles = int(resolved_backtest_warmup_candles)

    run_id = args.run_id or datetime.now(timezone.utc).strftime("wf_%Y%m%dT%H%M%SZ")
    out_dir = user_data_dir / "walkforward" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    invocation_tag = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    plan_root_rel = (
        f"walkforward_runtime_plans/{_safe_path_fragment(run_id)}_{invocation_tag}_{int(os.getpid())}"
    )
    summary_path = out_dir / "summary.json"
    run_state: Optional[RunStateTracker] = None
    if not args.disable_run_state:
        run_state = RunStateTracker(out_dir / "_state" / "state.json", out_dir / "_state" / "events.jsonl")
        run_state.update(
            run_type="walkforward",
            run_id=run_id,
            out_dir=str(out_dir),
            timerange=str(args.timerange),
            status="running",
            step_word="RUN_START",
            windows_total=int(len(windows)),
            windows_completed=0,
            windows_ok=0,
            windows_failed=0,
            pct_complete=_format_pct(0, len(windows)),
            dry_run=int(bool(args.dry_run)),
            runtime_plans_root_rel=str(plan_root_rel),
            backtest_warmup_candles=int(resolved_backtest_warmup_candles),
            backtest_warmup_days=int(resolved_backtest_warmup_days),
            backtest_warmup_source=str(warmup_source),
        )
        run_state.event(
            "RUN_START",
            run_id=run_id,
            timerange=str(args.timerange),
            windows_total=int(len(windows)),
            runtime_plans_root_rel=str(plan_root_rel),
            backtest_warmup_candles=int(resolved_backtest_warmup_candles),
            backtest_warmup_days=int(resolved_backtest_warmup_days),
            backtest_warmup_source=str(warmup_source),
        )
    monitor_state_dir = out_dir / "_state" if not args.disable_run_state else None
    monitor = LongRunMonitor(
        MonitorConfig(
            run_id=run_id,
            run_type="walkforward",
            total_steps=int(len(windows)),
            enabled=args.enable_liveness,
            state_dir=monitor_state_dir,
            stall_threshold_sec=args.stall_threshold_sec,
        ),
        run_state=run_state if args.enable_liveness else None,
    )
    monitor.start(message=f"timerange={args.timerange}", total_steps=len(windows))
    emit_run_marker(
        "RUN_START",
        run_id=run_id,
        timerange=str(args.timerange),
        windows_total=len(windows),
        user_data=str(user_data_dir),
        runtime_plans_root_rel=str(plan_root_rel),
        backtest_warmup_candles=int(resolved_backtest_warmup_candles),
        backtest_warmup_days=int(resolved_backtest_warmup_days),
        backtest_warmup_source=str(warmup_source),
        strategy_source_path=(str(strategy_source_path) if strategy_source_path is not None else ""),
    )
    print(
        f"[walkforward] warmup backtest_candles={int(resolved_backtest_warmup_candles)} "
        f"backtest_days={int(resolved_backtest_warmup_days)} source={warmup_source}",
        flush=True,
    )

    existing_rows_by_index: Dict[int, WindowResult] = {}
    if args.resume and summary_path.exists():
        with summary_path.open("r", encoding="utf-8") as f:
            existing = json.load(f)
        existing_args = existing.get("args", {}) or {}
        prev_timerange = str(existing_args.get("timerange") or "").strip()
        cur_timerange = str(args.timerange or "").strip()
        timerange_extended = False
        if prev_timerange and cur_timerange and (prev_timerange != cur_timerange):
            try:
                prev_start, prev_end = parse_day_timerange(prev_timerange)
                cur_start, cur_end = parse_day_timerange(cur_timerange)
            except Exception:
                raise RuntimeError(
                    "Resume refused: existing summary timerange is incompatible with current timerange "
                    f"(current={cur_timerange!r} previous={prev_timerange!r})."
                )
            if cur_start == prev_start and cur_end >= prev_end:
                timerange_extended = bool(cur_end > prev_end)
            else:
                raise RuntimeError(
                    "Resume refused: timerange mismatch is not an extension from the same start.\n"
                    f"current={cur_timerange!r} previous={prev_timerange!r}"
                )
        fatal_mismatches, optional_mismatches = _collect_resume_mismatches(existing_args, args)

        def _format_mismatch(entry: Tuple[str, object, object]) -> str:
            key, cur, prev = entry
            return f"{key}: current={cur!r} previous={prev!r}"

        if fatal_mismatches:
            raise RuntimeError(
                "Resume refused: existing summary args mismatch current args.\n"
                + "\n".join(_format_mismatch(m) for m in fatal_mismatches)
            )
        if optional_mismatches:
            warning_lines = ", ".join(
                f"{m[0]}(current={m[1]!r} prev={m[2]!r})" for m in optional_mismatches
            )
            print(
                "[walkforward] resume warning optional args changed: "
                f"{warning_lines}",
                flush=True,
            )
        if timerange_extended:
            print(
                f"[walkforward] resume timerange extension previous={prev_timerange} current={cur_timerange}",
                flush=True,
            )
        for row_raw in existing.get("windows", []) or []:
            try:
                parsed = window_result_from_dict(row_raw)
                existing_rows_by_index[int(parsed.index)] = parsed
            except Exception:
                continue
        print(
            f"[walkforward] resume loaded previous windows={len(existing_rows_by_index)} from {summary_path}",
            flush=True,
        )
        if run_state is not None:
            run_state.event(
                "RESUME_SCAN_DONE",
                summary_path=str(summary_path),
                previous_windows=int(len(existing_rows_by_index)),
            )
        monitor.event(
            "RESUME_SCAN_DONE",
            summary_path=str(summary_path),
            previous_windows=int(len(existing_rows_by_index)),
        )

    env_exports: List[str] = []
    env_exports.append(f"export GRID_PLANS_ROOT_REL={q(str(plan_root_rel))}")
    if args.regime_threshold_profile:
        env_exports.append(f"export GRID_REGIME_THRESHOLD_PROFILE={q(str(args.regime_threshold_profile).strip())}")
    if args.mode_thresholds_path:
        mode_path_input = str(args.mode_thresholds_path).strip()
        mode_path_out = mode_path_input
        mode_path_local = Path(mode_path_input)
        if not mode_path_local.is_absolute():
            mode_path_local = (freqtrade_root / mode_path_local).resolve()
        if mode_path_local.exists():
            try:
                mode_path_out = to_container_user_data_path(mode_path_local, user_data_dir)
            except Exception:
                mode_path_out = str(mode_path_local)
        env_exports.append(f"export GRID_MODE_THRESHOLDS_PATH={q(mode_path_out)}")

    pair_fs = args.pair.replace("/", "_").replace(":", "_")
    src_plan_dir = user_data_dir / Path(plan_root_rel) / args.exchange / pair_fs

    print(
        f"[walkforward] windows={len(windows)} out_dir={out_dir} "
        f"runtime_plans_root_rel={plan_root_rel}",
        flush=True,
    )

    rows: List[WindowResult] = []
    cur_quote = float(args.start_quote)
    cur_base = float(args.start_base)

    for idx, ws, we in windows:
        timerange = f"{fmt_day(ws)}-{fmt_day(we)}"
        if run_state is not None:
            run_state.event(
                "WINDOW_START",
                window_index=int(idx),
                windows_total=int(len(windows)),
                timerange=timerange,
            )
        monitor.event(
            "WINDOW_START",
            window_index=int(idx),
            windows_total=int(len(windows)),
            timerange=timerange,
        )
        existing_row = existing_rows_by_index.get(int(idx))
        if args.resume and existing_row and str(existing_row.status).lower() == "ok":
            result_file_exists = False
            rf = str(existing_row.result_file or "").strip()
            if rf:
                result_file_exists = Path(rf).exists()
            if (not args.resume_require_result_files) or result_file_exists:
                rows.append(existing_row)
                done = len(rows)
                print(
                    f"[walkforward] window {idx}/{len(windows)} timerange={timerange} "
                    f"resume=skip status=ok result_file_exists={int(result_file_exists)} "
                    f"completed={done}/{len(windows)} pct={_format_pct(done, len(windows))}",
                    flush=True,
                )
                if args.carry_capital:
                    if existing_row.end_quote is not None and existing_row.end_base is not None:
                        cur_quote = float(existing_row.end_quote)
                        cur_base = float(existing_row.end_base)
                    elif result_file_exists:
                        sim = load_sim_summary(Path(rf))
                        existing_row.end_quote = float(sim["end_quote"])
                        existing_row.end_base = float(sim["end_base"])
                        cur_quote = float(existing_row.end_quote)
                        cur_base = float(existing_row.end_base)
                    else:
                        raise RuntimeError(
                            f"Cannot resume carry-capital for window {idx}: missing end_quote/end_base and result_file."
                        )
                elif not args.carry_capital:
                    cur_quote = float(args.start_quote)
                    cur_base = float(args.start_base)
            if not args.dry_run:
                summary_path_ckpt, csv_path_ckpt, agg_ckpt = write_outputs(out_dir, run_id, args, rows)
                print(
                    f"[walkforward] checkpoint done={len(rows)}/{len(windows)} "
                    f"ok={int(agg_ckpt.get('windows_ok', 0))} failed={int(agg_ckpt.get('windows_failed', 0))}",
                    flush=True,
                )
                print(f"[walkforward] checkpoint wrote {summary_path_ckpt}", flush=True)
                print(f"[walkforward] checkpoint wrote {csv_path_ckpt}", flush=True)
            else:
                print(
                    f"[walkforward] checkpoint done={len(rows)}/{len(windows)} dry_run=1 (no files written)",
                    flush=True,
                )
                agg_ckpt = aggregate(rows)
                if run_state is not None:
                    run_state.event(
                        "WINDOW_RESUME_SKIP",
                        window_index=int(idx),
                        timerange=timerange,
                        result_file_exists=int(result_file_exists),
                    )
                run_state.update(
                    status="running",
                    step_word="WINDOW_DONE",
                    last_window_index=int(idx),
                    last_window_timerange=timerange,
                    last_window_status="ok",
                    windows_completed=int(len(rows)),
                    windows_ok=int(agg_ckpt.get("windows_ok", 0)),
                    windows_failed=int(agg_ckpt.get("windows_failed", 0)),
                    pct_complete=_format_pct(len(rows), len(windows)),
                )
            monitor.event(
                "WINDOW_RESUME_SKIP",
                window_index=int(idx),
                timerange=timerange,
                result_file_exists=int(result_file_exists),
            )
            monitor.progress(
                done=len(rows),
                stage="WINDOW_RESUME_SKIP",
                total=len(windows),
                message=timerange,
            )
            continue

        print(
            f"[walkforward] window {idx}/{len(windows)} timerange={timerange} "
            f"start_quote={cur_quote:.6f} start_base={cur_base:.6f} "
            f"completed={len(rows)}/{len(windows)} pct={_format_pct(len(rows), len(windows))}",
            flush=True,
        )

        row = WindowResult(
            index=idx,
            timerange=timerange,
            start_day=fmt_day(ws),
            end_day=fmt_day(we),
            status="ok",
        )
        backtest_timerange = timerange
        if int(resolved_backtest_warmup_days) > 0:
            backtest_start = ws - timedelta(days=int(resolved_backtest_warmup_days))
            backtest_timerange = f"{fmt_day(backtest_start)}-{fmt_day(we)}"

        window_stage = "init"
        window_stage_cmd = ""
        try:
            window_started_epoch = time.time()
            if not args.skip_backtesting:
                if src_plan_dir.exists():
                    shutil.rmtree(src_plan_dir)
                backtesting_inner = (
                f"freqtrade backtesting "
                f"--config {q(str(config_path_container))} "
                f"--strategy {q(args.strategy)} "
                f"--strategy-path {q(str(strategy_path_container))} "
                f"--timerange {q(backtest_timerange)} "
                f"--timeframe {q(args.timeframe)} "
                f"--datadir {q(str(data_dir_container))} "
                    f"--cache none"
                )
                if args.backtesting_extra.strip():
                    backtesting_inner = f"{backtesting_inner} {args.backtesting_extra.strip()}"
                window_stage = "backtesting"
                window_stage_cmd = backtesting_inner
                backtest_started = time.time()
                print(
                    f"[walkforward] window {idx} stage=backtesting status=start "
                    f"timerange={timerange} backtest_timerange={backtest_timerange}",
                    flush=True,
                )
                if run_state is not None:
                    run_state.event(
                        "WINDOW_BACKTEST_START",
                        window_index=int(idx),
                        timerange=timerange,
                        backtest_timerange=backtest_timerange,
                    )
                backtest_probe = lambda: {"plan_files": int(_count_plan_files(src_plan_dir))}
                run_compose_inner(
                    project_dir,
                    compose_file,
                    args.service,
                    backtesting_inner,
                    env_exports=env_exports,
                    heartbeat_sec=int(args.heartbeat_sec),
                    progress_label=f"window_{idx:03d}_backtesting",
                    progress_probe=backtest_probe,
                    stalled_heartbeats_max=int(args.stalled_heartbeats_max),
                    dry_run=args.dry_run,
                )
                print(
                    f"[walkforward] window {idx} stage=backtesting status=done elapsed_sec={int(max(0.0, time.time() - backtest_started))}",
                    flush=True,
                )
                if run_state is not None:
                    run_state.event(
                        "WINDOW_BACKTEST_DONE",
                        window_index=int(idx),
                        timerange=timerange,
                        backtest_timerange=backtest_timerange,
                    )
                if (not args.dry_run) and (not src_plan_dir.is_dir()):
                    raise RuntimeError(
                        "Plan source directory not found after backtesting: "
                        f"{src_plan_dir} (backtest_timerange={backtest_timerange}, "
                        f"warmup_candles={resolved_backtest_warmup_candles}, "
                        f"warmup_days={resolved_backtest_warmup_days})"
                    )

            window_plan_dir = out_dir / f"window_{idx:03d}_plans"
            min_mtime_epoch = None if args.skip_backtesting else (window_started_epoch - 5.0)
            window_stage = "extract_plans"
            window_stage_cmd = ""
            extract_started = time.time()
            plan_count = extract_window_plans(
                src_plan_dir,
                window_plan_dir,
                ws,
                we,
                min_mtime_epoch=min_mtime_epoch,
            )
            row.plans_file_count = int(plan_count)
            print(
                f"[walkforward] window {idx} stage=extract_plans status=done plans={int(plan_count)} "
                f"elapsed_sec={int(max(0.0, time.time() - extract_started))}",
                flush=True,
            )
            if run_state is not None:
                run_state.event(
                    "WINDOW_EXTRACT_DONE",
                    window_index=int(idx),
                    timerange=timerange,
                    plan_count=int(plan_count),
                )
            if plan_count <= 0:
                raise RuntimeError(
                    f"No plan snapshots found for window {timerange} under {src_plan_dir} "
                    f"(backtest_timerange={backtest_timerange}, "
                    f"warmup_candles={resolved_backtest_warmup_candles}, "
                    f"warmup_days={resolved_backtest_warmup_days})"
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
                f"--data-dir {q(str(data_dir_container))} "
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
            window_stage = "simulate"
            window_stage_cmd = sim_inner
            sim_started = time.time()
            print(f"[walkforward] window {idx} stage=simulate status=start timerange={timerange}", flush=True)
            if run_state is not None:
                run_state.event("WINDOW_SIM_START", window_index=int(idx), timerange=timerange)
            sim_paths = {
                "result_json": result_local,
                "fills_csv": Path(str(result_local).replace(".json", ".fills.csv")),
                "curve_csv": Path(str(result_local).replace(".json", ".curve.csv")),
                "events_csv": Path(str(result_local).replace(".json", ".events.csv")),
            }
            sim_probe = lambda: _probe_path_sizes(sim_paths)
            run_compose_inner(
                project_dir,
                compose_file,
                args.service,
                sim_inner,
                env_exports=env_exports,
                heartbeat_sec=int(args.heartbeat_sec),
                progress_label=f"window_{idx:03d}_simulate",
                progress_probe=sim_probe,
                stalled_heartbeats_max=int(args.stalled_heartbeats_max),
                dry_run=args.dry_run,
            )
            print(
                f"[walkforward] window {idx} stage=simulate status=done elapsed_sec={int(max(0.0, time.time() - sim_started))}",
                flush=True,
            )
            if run_state is not None:
                run_state.event("WINDOW_SIM_DONE", window_index=int(idx), timerange=timerange)

            row.result_file = str(result_local)
            if not args.dry_run:
                sim = load_sim_summary(result_local)
                row.pnl_quote = sim["pnl_quote"]
                row.pnl_pct = sim["pnl_pct"]
                row.initial_equity = sim["initial_equity"]
                row.end_equity = sim["end_equity"]
                row.end_quote = sim["end_quote"]
                row.end_base = sim["end_base"]
                row.fills = sim["fills"]
                row.stop_events = sim["stop_events"]
                row.seed_events = sim["seed_events"]
                row.rebuild_events = sim["rebuild_events"]
                row.soft_adjust_events = sim["soft_adjust_events"]
                row.action_start = sim["action_start"]
                row.action_hold = sim["action_hold"]
                row.action_stop = sim["action_stop"]
                row.mode_plan_counts = sim["mode_plan_counts"]
                row.mode_desired_counts = sim["mode_desired_counts"]
                row.raw_action_mode_counts = sim["raw_action_mode_counts"]
                row.effective_action_mode_counts = sim["effective_action_mode_counts"]
                row.fill_mode_counts = sim["fill_mode_counts"]
                row.fill_mode_side_counts = sim["fill_mode_side_counts"]
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
        except KeyboardInterrupt:
            if run_state is not None:
                run_state.update(
                    status="interrupted",
                    step_word="INTERRUPTED",
                    last_window_index=int(idx),
                    last_window_timerange=timerange,
                    last_window_status="interrupted",
                    windows_completed=int(len(rows)),
                    pct_complete=_format_pct(len(rows), len(windows)),
                )
                run_state.event(
                    "INTERRUPTED",
                    window_index=int(idx),
                    timerange=timerange,
                    windows_completed=int(len(rows)),
                )
            monitor.event(
                "INTERRUPTED",
                window_index=int(idx),
                timerange=timerange,
                windows_completed=int(len(rows)),
            )
            emit_run_marker(
                "RUN_ABORTED",
                run_id=run_id,
                timerange=timerange,
                window_index=int(idx),
                reason="keyboard_interrupt",
            )
            raise
        except Exception as exc:
            row.status = "error"
            row.error = str(exc) or repr(exc)
            err_report = _write_window_error_report(
                out_dir=out_dir,
                run_id=run_id,
                window_index=int(idx),
                timerange=timerange,
                stage=window_stage,
                stage_cmd=window_stage_cmd,
                exc=exc,
            )
            row.error_report_file = str(err_report)
            transient = int(_is_transient_error(row.error))
            if run_state is not None:
                run_state.event(
                    "WINDOW_ERROR",
                    window_index=int(idx),
                    timerange=timerange,
                    stage=window_stage,
                    error=row.error,
                    error_transient=transient,
                    error_report_file=str(err_report),
                )
                run_state.update(
                    error=row.error,
                    last_error_stage=str(window_stage),
                    last_error_window_index=int(idx),
                    last_error_timerange=timerange,
                    last_error_transient=transient,
                last_error_report_file=str(err_report),
            )
            monitor.event(
                "WINDOW_ERROR",
                window_index=int(idx),
                timerange=timerange,
                stage=window_stage,
                error=row.error,
                error_transient=transient,
                error_report_file=str(err_report),
            )
            if not args.carry_capital:
                cur_quote = float(args.start_quote)
                cur_base = float(args.start_base)

        rows.append(row)
        if row.status != "ok":
            print(f"[walkforward] window {idx} ERROR: {row.error}", flush=True)

        if (not args.carry_capital) and row.status == "ok":
            cur_quote = float(args.start_quote)
            cur_base = float(args.start_base)

        done = len(rows)
        if not args.dry_run:
            summary_path_ckpt, csv_path_ckpt, agg_ckpt = write_outputs(out_dir, run_id, args, rows)
            print(
                f"[walkforward] checkpoint done={done}/{len(windows)} pct={_format_pct(done, len(windows))} "
                f"ok={int(agg_ckpt.get('windows_ok', 0))} failed={int(agg_ckpt.get('windows_failed', 0))}",
                flush=True,
            )
            print(f"[walkforward] checkpoint wrote {summary_path_ckpt}", flush=True)
            print(f"[walkforward] checkpoint wrote {csv_path_ckpt}", flush=True)
        else:
            print(
                f"[walkforward] checkpoint done={done}/{len(windows)} pct={_format_pct(done, len(windows))} "
                "dry_run=1 (no files written)",
                flush=True,
            )
            agg_ckpt = aggregate(rows)

        if run_state is not None:
            run_state.event(
                "WINDOW_DONE",
                window_index=int(idx),
                timerange=timerange,
                status=str(row.status),
                plans_file_count=int(row.plans_file_count or 0),
            )
            update_payload = dict(
                status="running",
                step_word=("WINDOW_DONE" if str(row.status).lower() == "ok" else "WINDOW_ERROR"),
                last_window_index=int(idx),
                last_window_timerange=timerange,
                last_window_status=str(row.status),
                windows_completed=int(done),
                windows_ok=int(agg_ckpt.get("windows_ok", 0)),
                windows_failed=int(agg_ckpt.get("windows_failed", 0)),
                pct_complete=_format_pct(done, len(windows)),
            )
            if str(row.status).lower() != "ok":
                update_payload.update(
                    error=str(row.error or ""),
                    last_error_stage=str(window_stage),
                    last_error_window_index=int(idx),
                    last_error_timerange=timerange,
                    last_error_transient=int(_is_transient_error(str(row.error or ""))),
                    last_error_report_file=str(row.error_report_file or ""),
                )
            run_state.update(**update_payload)
        monitor.event(
            "WINDOW_DONE",
            window_index=int(idx),
            timerange=timerange,
            status=str(row.status),
            plans_file_count=int(row.plans_file_count or 0),
        )
        monitor.progress(done=done, stage=f"WINDOW_{idx:03d}", total=len(windows), message=timerange)

        if args.fail_on_window_error and str(row.status).lower() != "ok":
            print(
                f"[walkforward] fail-fast enabled: aborting run after window {idx} error.",
                flush=True,
            )
            if run_state is not None:
                run_state.event(
                    "RUN_ABORT_ON_WINDOW_ERROR",
                    window_index=int(idx),
                    timerange=timerange,
                    error=str(row.error or ""),
                )
            emit_run_marker(
                "RUN_FAILED",
                run_id=run_id,
                reason="fail_on_window_error",
                window_index=int(idx),
                timerange=timerange,
            )
            break

    agg = aggregate(rows)
    if not args.dry_run:
        summary_path, csv_path, agg = write_outputs(out_dir, run_id, args, rows)
        print(f"[walkforward] wrote {summary_path}", flush=True)
        print(f"[walkforward] wrote {csv_path}", flush=True)
    else:
        print(
            f"[walkforward] dry_run complete run_id={run_id} out_dir={out_dir} (no summary/csv written)",
            flush=True,
        )
    print(f"[walkforward] aggregate: {json.dumps(aggregate_brief(agg), sort_keys=True)}", flush=True)

    rc = 0
    final_word = "RUN_COMPLETE"
    final_status = "completed"
    if args.fail_on_window_error and any(r.status != "ok" for r in rows):
        rc = 1
        final_word = "RUN_FAILED"
        final_status = "failed"
    elif int(agg.get("windows_ok", 0)) == 0:
        rc = 2
        final_word = "RUN_FAILED"
        final_status = "failed"

    if run_state is not None:
        run_state.update(
            status=final_status,
            step_word=final_word,
            windows_completed=int(len(rows)),
            windows_ok=int(agg.get("windows_ok", 0)),
            windows_failed=int(agg.get("windows_failed", 0)),
            pct_complete=_format_pct(len(rows), len(windows)),
            return_code=int(rc),
        )
        run_state.event(
            final_word,
            run_id=run_id,
            return_code=int(rc),
            windows_total=int(agg.get("windows_total", 0)),
            windows_ok=int(agg.get("windows_ok", 0)),
            windows_failed=int(agg.get("windows_failed", 0)),
        )
    emit_run_marker(
        "RUN_COMPLETE",
        run_id=run_id,
        status=final_status,
        step_word=final_word,
        windows_completed=int(len(rows)),
        windows_ok=int(agg.get("windows_ok", 0)),
        windows_failed=int(agg.get("windows_failed", 0)),
        pct_complete=_format_pct(len(rows), len(windows)),
        return_code=int(rc),
    )

    if not args.dry_run:
        summary_out = out_dir / "summary.json"
        windows_out = out_dir / "windows.csv"
        rows_ok = [r for r in rows if str(r.status).lower() == "ok"]
        rows_missing_bal = [r for r in rows_ok if (r.end_quote is None) or (r.end_base is None)]
        latest_payload = {
            "run_type": "walkforward",
            "run_id": str(run_id),
            "status": str(final_status),
            "step_word": str(final_word),
            "return_code": int(rc),
            "timerange": str(args.timerange),
            "out_dir": rel_payload_path(user_data_dir, out_dir),
            "summary_path": rel_payload_path(user_data_dir, summary_out),
            "windows_path": rel_payload_path(user_data_dir, windows_out),
            "aggregate": aggregate_brief(agg),
            "raw_window_files_prunable": bool(len(rows_missing_bal) == 0),
            "raw_window_files_blocked_count": int(len(rows_missing_bal)),
        }
        latest_ref = publish_latest_ref(user_data_dir, "walkforward", latest_payload)
        print(f"[walkforward] latest_ref wrote {latest_ref}", flush=True)
    monitor.complete(final_word, message=f"windows_ok={int(agg.get('windows_ok', 0))}", return_code=rc)
    return int(rc)


if __name__ == "__main__":
    raise SystemExit(main())
