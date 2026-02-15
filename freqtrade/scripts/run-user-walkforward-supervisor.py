#!/usr/bin/env python3
"""
Supervise walkforward runs with auto-resume on transient failures.

Usage pattern:
  python3 scripts/run-user-walkforward-supervisor.py --max-attempts 6 -- \
    --timerange 20200101-20260213 ... --run-id wf_example --fail-on-window-error
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
    r"Could not load markets",
    r"timed?\s*out",
    r"Too Many Requests",
    r"\b429\b",
    r"DDoSProtection",
    r"NetworkError",
    r"ServiceUnavailable",
    r"Connection (?:reset|aborted|refused)",
]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Dict:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
    except Exception:
        return {}
    return {}


def _extract_opt_value(args: Sequence[str], opt: str) -> Optional[str]:
    vals: List[str] = []
    i = 0
    while i < len(args):
        token = str(args[i])
        if token == opt and (i + 1) < len(args):
            vals.append(str(args[i + 1]))
            i += 2
            continue
        if token.startswith(f"{opt}="):
            vals.append(token.split("=", 1)[1])
        i += 1
    if not vals:
        return None
    return vals[-1]


def _has_flag(args: Sequence[str], flag: str) -> bool:
    return any(str(x) == flag for x in args)


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


def _load_error_blob(run_dir: Path, state: Dict) -> str:
    chunks: List[str] = []
    err_text = str(state.get("error") or "")
    if err_text:
        chunks.append(err_text)
    report_path = str(state.get("last_error_report_file") or "").strip()
    report: Dict = {}
    if report_path:
        report = _read_json(Path(report_path))
    if not report:
        err_dir = run_dir / "errors"
        if err_dir.is_dir():
            candidates = sorted(err_dir.glob("window_*.error.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            if candidates:
                report = _read_json(candidates[0])
    if report:
        for k in ("error", "error_type", "stage", "traceback"):
            v = report.get(k)
            if v not in (None, ""):
                chunks.append(f"{k}: {v}")
    return "\n".join(chunks).strip()


def _sig(state: Dict) -> Tuple:
    return (
        str(state.get("status") or ""),
        int(state.get("windows_completed") or 0),
        int(state.get("windows_total") or 0),
        str(state.get("pct_complete") or ""),
        int(state.get("windows_failed") or 0),
        str(state.get("step_word") or ""),
        str(state.get("last_window_timerange") or ""),
    )


def _write_supervisor_state(run_dir: Path, payload: Dict) -> None:
    state_dir = run_dir / "_state"
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user-data", default="user_data")
    ap.add_argument("--max-attempts", type=int, default=5)
    ap.add_argument("--retry-delay-sec", type=int, default=20)
    ap.add_argument("--retry-backoff-mult", type=float, default=1.5)
    ap.add_argument("--max-retry-delay-sec", type=int, default=300)
    ap.add_argument("--poll-sec", type=int, default=10)
    ap.add_argument("--transient-pattern", action="append", default=[])
    ap.add_argument("--no-resume", action="store_true")
    ap.add_argument("--no-fail-fast", action="store_true")
    ap.add_argument(
        "child_args",
        nargs=argparse.REMAINDER,
        help="Arguments for run-user-walkforward.py. Prefix with --",
    )
    return ap


def main() -> int:
    args = build_parser().parse_args()
    root_dir = Path(__file__).resolve().parents[1]
    user_data = Path(args.user_data)
    if not user_data.is_absolute():
        user_data = (root_dir / user_data).resolve()
    child = list(args.child_args or [])
    if child and child[0] == "--":
        child = child[1:]
    if not child:
        raise ValueError("Provide run-user-walkforward arguments after --")

    if (not args.no_resume) and (not _has_flag(child, "--resume")):
        child.append("--resume")
    if (not args.no_fail_fast) and (not _has_flag(child, "--fail-on-window-error")):
        child.append("--fail-on-window-error")

    run_id = _extract_opt_value(child, "--run-id")
    if not str(run_id or "").strip():
        raise ValueError("Supervisor requires explicit --run-id in child args.")
    run_id = str(run_id).strip()
    run_dir = user_data / "walkforward" / run_id
    state_path = run_dir / "_state" / "state.json"

    patterns = list(DEFAULT_TRANSIENT_PATTERNS)
    for item in args.transient_pattern or []:
        text = str(item or "").strip()
        if text:
            patterns.append(text)
    compiled = _compile_patterns(patterns)

    max_attempts = max(1, int(args.max_attempts))
    poll_sec = max(1, int(args.poll_sec))
    delay_sec = max(1, int(args.retry_delay_sec))
    max_delay_sec = max(1, int(args.max_retry_delay_sec))
    backoff = max(1.0, float(args.retry_backoff_mult))

    cmd = ["python3", str((root_dir / "scripts" / "run-user-walkforward.py").resolve()), *child]
    print(f"[wf-supervisor] run_id={run_id} max_attempts={max_attempts}", flush=True)
    print(f"[wf-supervisor] cmd={' '.join(cmd)}", flush=True)

    for attempt in range(1, max_attempts + 1):
        attempt_started = time.time()
        print(f"[wf-supervisor] attempt={attempt}/{max_attempts} start={_utc_now_iso()}", flush=True)
        proc = subprocess.Popen(cmd, cwd=str(root_dir))
        last_sig: Optional[Tuple] = None
        while True:
            try:
                rc = int(proc.wait(timeout=poll_sec))
                break
            except subprocess.TimeoutExpired:
                state = _read_json(state_path)
                sig = _sig(state)
                if sig != last_sig:
                    status, done, total, pct, failed, step, tr = sig
                    print(
                        f"[wf-supervisor] alive run={run_id} status={status} done={done}/{total} "
                        f"pct={pct} failed={failed} step={step} last={tr}",
                        flush=True,
                    )
                    last_sig = sig
                continue

        elapsed = int(max(0.0, time.time() - attempt_started))
        state = _read_json(state_path)
        error_blob = _load_error_blob(run_dir, state)
        transient = int(_is_transient(error_blob, compiled))
        status = str(state.get("status") or "")
        done = int(state.get("windows_completed") or 0)
        total = int(state.get("windows_total") or 0)
        failed = int(state.get("windows_failed") or 0)
        step = str(state.get("step_word") or "")
        last_timerange = str(state.get("last_window_timerange") or "")
        print(
            f"[wf-supervisor] attempt={attempt} rc={rc} elapsed_sec={elapsed} status={status} "
            f"done={done}/{total} failed={failed} step={step} last={last_timerange} transient={transient}",
            flush=True,
        )
        _write_supervisor_state(
            run_dir,
            {
                "run_type": "walkforward_supervisor",
                "run_id": run_id,
                "attempt": int(attempt),
                "attempts_total": int(max_attempts),
                "return_code": int(rc),
                "status": str(status),
                "windows_completed": int(done),
                "windows_total": int(total),
                "windows_failed": int(failed),
                "step_word": str(step),
                "last_window_timerange": str(last_timerange),
                "transient_error": int(transient),
                "error_excerpt": str(error_blob[:1000]),
            },
        )
        if rc == 0:
            print(f"[wf-supervisor] completed run_id={run_id}", flush=True)
            return 0
        if transient and attempt < max_attempts:
            print(
                f"[wf-supervisor] retrying after transient failure in {delay_sec}s (resume enabled).",
                flush=True,
            )
            time.sleep(delay_sec)
            delay_sec = min(max_delay_sec, max(delay_sec + 1, int(round(delay_sec * backoff))))
            continue
        print("[wf-supervisor] stopping: non-transient failure or max attempts reached.", flush=True)
        return int(rc if rc != 0 else 1)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
