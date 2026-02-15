#!/usr/bin/env python3
"""
Generic supervisor for user scripts that write run-state markers.

Features:
- live liveness/progress printouts from a state.json file
- retry with backoff on transient failures
- explicit completion check via step/status markers
- supervisor_state.json + supervisor_events.jsonl outputs

Usage:
  python3 scripts/run-user-state-supervisor.py \
    --run-label data-sync \
    --state-file user_data/run_state/data_sync/my_run/state.json \
    --max-attempts 5 --poll-sec 10 \
    -- \
    python3 scripts/run-user-data-sync.py --run-id my_run ...
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

DEFAULT_TRANSIENT_PATTERNS: List[str] = [
    r"RequestTimeout",
    r"TemporaryError",
    r"timed?\s*out",
    r"Too Many Requests",
    r"\b429\b",
    r"NetworkError",
    r"ServiceUnavailable",
    r"DDoSProtection",
    r"Connection (?:reset|aborted|refused)",
    r"TLS handshake timeout",
    r"context deadline exceeded",
    r"EOF",
    r"No route to host",
]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Dict:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _first_int(d: Dict, keys: Sequence[str], default: int = 0) -> int:
    for k in keys:
        v = d.get(k)
        try:
            if v is not None and str(v) != "":
                return int(v)
        except Exception:
            continue
    return int(default)


def _first_str(d: Dict, keys: Sequence[str], default: str = "") -> str:
    for k in keys:
        v = d.get(k)
        if v is not None and str(v) != "":
            return str(v)
    return str(default)


def _sig(state: Dict) -> Tuple:
    return (
        _first_str(state, ["status"]),
        _first_int(state, ["windows_completed", "tasks_completed", "completed", "progress_done"], 0),
        _first_int(state, ["windows_total", "tasks_total", "total", "progress_total"], 0),
        _first_str(state, ["pct_complete", "progress_pct"]),
        _first_int(state, ["windows_failed", "tasks_failed", "failed"], 0),
        _first_str(state, ["step_word"]),
        _first_str(state, ["last_window_timerange", "last_task", "last_window_index", "timerange"]),
    )


def _compile_patterns(patterns: Sequence[str]) -> List[re.Pattern[str]]:
    out: List[re.Pattern[str]] = []
    for raw in patterns:
        text = str(raw or "").strip()
        if not text:
            continue
        try:
            out.append(re.compile(text, re.IGNORECASE))
        except Exception:
            continue
    return out


def _is_transient(text: str, patterns: Sequence[re.Pattern[str]]) -> bool:
    payload = str(text or "")
    if not payload:
        return False
    return any(p.search(payload) for p in patterns)


def _build_error_blob(state: Dict, error_keys: Sequence[str]) -> str:
    chunks: List[str] = []
    for key in error_keys:
        v = state.get(key)
        if v not in (None, ""):
            chunks.append(f"{key}: {v}")
    for k in ("status", "step_word"):
        v = state.get(k)
        if v not in (None, ""):
            chunks.append(f"{k}: {v}")
    return "\n".join(chunks).strip()


def _has_flag(args: Sequence[str], flag: str) -> bool:
    return any(str(x) == str(flag) for x in args)


def _write_supervisor_state(state_dir: Path, payload: Dict) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    rec = dict(payload)
    rec["updated_utc"] = _utc_now_iso()

    events_file = state_dir / "supervisor_events.jsonl"
    with events_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")

    state_file = state_dir / "supervisor_state.json"
    tmp = state_file.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(rec, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(state_file)


def _parse_bool(text: str) -> bool:
    return str(text).strip().lower() in {"1", "true", "yes", "on", "y"}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-label", default="state-run")
    ap.add_argument("--state-file", required=True, help="State file produced by target command.")
    ap.add_argument(
        "--supervisor-dir",
        default="",
        help="Directory for supervisor_state/events. Default: state file directory.",
    )
    ap.add_argument("--cwd", default="", help="Working directory for child command.")
    ap.add_argument("--max-attempts", type=int, default=5)
    ap.add_argument("--retry-delay-sec", type=int, default=20)
    ap.add_argument("--retry-backoff-mult", type=float, default=1.5)
    ap.add_argument("--max-retry-delay-sec", type=int, default=300)
    ap.add_argument("--poll-sec", type=int, default=10)
    ap.add_argument("--transient-pattern", action="append", default=[])
    ap.add_argument("--error-key", action="append", default=[])
    ap.add_argument("--complete-word", action="append", default=[])
    ap.add_argument("--complete-status", action="append", default=[])
    ap.add_argument(
        "--require-state-complete",
        default="1",
        help="1/0. If 1, rc=0 still requires terminal state markers.",
    )
    ap.add_argument("--ensure-arg", action="append", default=[])
    ap.add_argument(
        "child_args",
        nargs=argparse.REMAINDER,
        help="Child command. Prefix with --",
    )
    return ap


def main() -> int:
    args = build_parser().parse_args()

    child = list(args.child_args or [])
    while child and child[0] == "--":
        child = child[1:]
    if not child:
        raise ValueError("Provide child command arguments after --")

    for token in args.ensure_arg or []:
        t = str(token or "").strip()
        if t and (not _has_flag(child, t)):
            child.append(t)

    cwd = Path(args.cwd).resolve() if str(args.cwd or "").strip() else Path.cwd()
    state_file = Path(args.state_file)
    if not state_file.is_absolute():
        state_file = (cwd / state_file).resolve()

    if str(args.supervisor_dir or "").strip():
        supervisor_dir = Path(args.supervisor_dir)
        if not supervisor_dir.is_absolute():
            supervisor_dir = (cwd / supervisor_dir).resolve()
    else:
        supervisor_dir = state_file.parent

    require_state_complete = _parse_bool(str(args.require_state_complete))

    complete_words = [
        str(x).strip() for x in (args.complete_word or []) if str(x).strip()
    ]
    if not complete_words:
        complete_words = ["RUN_COMPLETE", "RUN_COMPLETE_WITH_ERRORS"]

    complete_statuses = [
        str(x).strip() for x in (args.complete_status or []) if str(x).strip()
    ]
    if not complete_statuses:
        complete_statuses = ["completed", "completed_with_errors"]

    error_keys = [str(x).strip() for x in (args.error_key or []) if str(x).strip()]
    if not error_keys:
        error_keys = [
            "error",
            "last_error",
            "last_error_message",
            "last_exception",
            "stderr",
            "message",
        ]

    patterns = list(DEFAULT_TRANSIENT_PATTERNS)
    for p in args.transient_pattern or []:
        text = str(p or "").strip()
        if text:
            patterns.append(text)
    compiled = _compile_patterns(patterns)

    max_attempts = max(1, int(args.max_attempts))
    poll_sec = max(1, int(args.poll_sec))
    delay_sec = max(1, int(args.retry_delay_sec))
    max_delay_sec = max(1, int(args.max_retry_delay_sec))
    backoff = max(1.0, float(args.retry_backoff_mult))

    print(f"[state-supervisor] run={args.run_label} max_attempts={max_attempts}", flush=True)
    print(f"[state-supervisor] cwd={cwd}", flush=True)
    print(f"[state-supervisor] state_file={state_file}", flush=True)
    print(f"[state-supervisor] cmd={' '.join(str(x) for x in child)}", flush=True)

    for attempt in range(1, max_attempts + 1):
        started = time.time()
        print(f"[state-supervisor] attempt={attempt}/{max_attempts} start={_utc_now_iso()}", flush=True)

        proc = subprocess.Popen(child, cwd=str(cwd))
        last_sig: Optional[Tuple] = None

        while True:
            try:
                rc = int(proc.wait(timeout=poll_sec))
                break
            except subprocess.TimeoutExpired:
                state = _read_json(state_file)
                sig = _sig(state)
                if sig != last_sig:
                    status, done, total, pct, failed, step, last = sig
                    print(
                        f"[state-supervisor] alive run={args.run_label} status={status} "
                        f"done={done}/{total} pct={pct} failed={failed} step={step} last={last}",
                        flush=True,
                    )
                    last_sig = sig
                continue

        elapsed = int(max(0.0, time.time() - started))
        state = _read_json(state_file)
        status = _first_str(state, ["status"])
        step = _first_str(state, ["step_word"])
        done = _first_int(state, ["windows_completed", "tasks_completed", "completed", "progress_done"], 0)
        total = _first_int(state, ["windows_total", "tasks_total", "total", "progress_total"], 0)
        failed = _first_int(state, ["windows_failed", "tasks_failed", "failed"], 0)
        pct = _first_str(state, ["pct_complete", "progress_pct"])
        last = _first_str(state, ["last_window_timerange", "last_task", "last_window_index", "timerange"])

        step_ok = (not complete_words) or (step in complete_words)
        status_ok = (not complete_statuses) or (status in complete_statuses)
        state_ok = bool(step_ok and status_ok)
        success = bool((rc == 0) and ((not require_state_complete) or state_ok))

        error_blob = _build_error_blob(state, error_keys)
        transient = int((rc != 0) and _is_transient(error_blob, compiled))

        print(
            f"[state-supervisor] attempt={attempt} rc={rc} elapsed_sec={elapsed} status={status} "
            f"done={done}/{total} pct={pct} failed={failed} step={step} last={last} "
            f"state_ok={int(state_ok)} transient={transient}",
            flush=True,
        )

        _write_supervisor_state(
            supervisor_dir,
            {
                "run_type": "state_supervisor",
                "run_label": str(args.run_label),
                "attempt": int(attempt),
                "attempts_total": int(max_attempts),
                "return_code": int(rc),
                "status": str(status),
                "step_word": str(step),
                "state_ok": int(state_ok),
                "windows_completed": int(done),
                "windows_total": int(total),
                "windows_failed": int(failed),
                "pct_complete": str(pct),
                "last": str(last),
                "transient_error": int(transient),
                "error_excerpt": str(error_blob[:1000]),
                "state_file": str(state_file),
            },
        )

        if success:
            print(f"[state-supervisor] completed run={args.run_label}", flush=True)
            return 0

        if transient and attempt < max_attempts:
            print(
                f"[state-supervisor] retrying after transient failure in {delay_sec}s",
                flush=True,
            )
            time.sleep(delay_sec)
            delay_sec = min(max_delay_sec, max(delay_sec + 1, int(round(delay_sec * backoff))))
            continue

        print("[state-supervisor] stopping: non-transient failure or max attempts reached.", flush=True)
        return int(rc if rc != 0 else 1)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
