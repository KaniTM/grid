#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple


STATE_KEYS = ("range", "trend", "neutral", "unlabeled")


def _parse_iso_utc(text: str) -> datetime:
    s = str(text or "").strip()
    if not s:
        raise ValueError("empty timestamp")
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _safe_int(v: object, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return int(default)


def _pct(n: int, d: int) -> float:
    if int(d) <= 0:
        return 0.0
    return round(float(n) / float(d), 6)


def _quantile(sorted_vals: List[float], q: float) -> float:
    if not sorted_vals:
        return 0.0
    if q <= 0:
        return float(sorted_vals[0])
    if q >= 1:
        return float(sorted_vals[-1])
    idx = int(round((len(sorted_vals) - 1) * q))
    idx = max(0, min(idx, len(sorted_vals) - 1))
    return float(sorted_vals[idx])


def _segment_stats_from_verbose_csv(path: Path, mode_col: str) -> Dict[str, object]:
    states = {"range", "trend", "neutral"}
    seg_rows: List[Dict[str, object]] = []
    lengths_by_state: Dict[str, List[int]] = {"range": [], "trend": [], "neutral": []}
    transitions: Dict[str, int] = {}

    prev_state: Optional[str] = None
    prev_ts: Optional[datetime] = None
    cur_state: Optional[str] = None
    cur_start: Optional[datetime] = None
    cur_bars = 0

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            state = str(row.get(mode_col) or "").strip().lower()
            if state not in states:
                prev_state = None
                prev_ts = None
                if cur_state is not None and cur_start is not None:
                    lengths_by_state[cur_state].append(int(cur_bars))
                    seg_rows.append(
                        {
                            "state": cur_state,
                            "start_utc": cur_start.isoformat(),
                            "end_utc": (prev_ts or cur_start).isoformat(),
                            "bars": int(cur_bars),
                        }
                    )
                cur_state = None
                cur_start = None
                cur_bars = 0
                continue

            ts = _parse_iso_utc(str(row.get("date") or ""))
            if cur_state is None:
                cur_state = state
                cur_start = ts
                cur_bars = 1
            elif state == cur_state:
                cur_bars += 1
            else:
                lengths_by_state[cur_state].append(int(cur_bars))
                seg_rows.append(
                    {
                        "state": cur_state,
                        "start_utc": cur_start.isoformat(),
                        "end_utc": (prev_ts or cur_start).isoformat(),
                        "bars": int(cur_bars),
                    }
                )
                key = f"{cur_state}->{state}"
                transitions[key] = int(transitions.get(key, 0)) + 1
                cur_state = state
                cur_start = ts
                cur_bars = 1

            prev_state = state
            prev_ts = ts

    if cur_state is not None and cur_start is not None:
        lengths_by_state[cur_state].append(int(cur_bars))
        seg_rows.append(
            {
                "state": cur_state,
                "start_utc": cur_start.isoformat(),
                "end_utc": (prev_ts or cur_start).isoformat(),
                "bars": int(cur_bars),
            }
        )

    out: Dict[str, object] = {"states": {}, "top_segments": {}}
    for state in ("range", "trend", "neutral"):
        vals = sorted(int(x) for x in lengths_by_state[state] if int(x) > 0)
        n = len(vals)
        if n == 0:
            out["states"][state] = {
                "segment_count": 0,
                "mean_bars": 0.0,
                "median_bars": 0.0,
                "p90_bars": 0.0,
                "p99_bars": 0.0,
                "max_bars": 0,
                "mean_days": 0.0,
                "median_days": 0.0,
                "p90_days": 0.0,
                "p99_days": 0.0,
                "max_days": 0.0,
            }
            out["top_segments"][state] = []
            continue
        mean_bars = float(sum(vals) / n)
        med_bars = _quantile(vals, 0.50)
        p90_bars = _quantile(vals, 0.90)
        p99_bars = _quantile(vals, 0.99)
        max_bars = int(vals[-1])
        to_days = lambda b: round(float(b) * 0.25 / 24.0, 6)
        out["states"][state] = {
            "segment_count": int(n),
            "mean_bars": round(mean_bars, 3),
            "median_bars": round(med_bars, 3),
            "p90_bars": round(p90_bars, 3),
            "p99_bars": round(p99_bars, 3),
            "max_bars": int(max_bars),
            "mean_days": to_days(mean_bars),
            "median_days": to_days(med_bars),
            "p90_days": to_days(p90_bars),
            "p99_days": to_days(p99_bars),
            "max_days": to_days(max_bars),
        }
        top = [
            s
            for s in sorted(
                (x for x in seg_rows if str(x.get("state")) == state),
                key=lambda x: int(x.get("bars") or 0),
                reverse=True,
            )[:10]
        ]
        out["top_segments"][state] = top

    out["transitions"] = {
        k: int(v)
        for k, v in sorted(transitions.items(), key=lambda kv: (-int(kv[1]), str(kv[0])))
    }
    return out


def _mode_share_entry(counts: Dict[str, int]) -> Dict[str, object]:
    total = sum(int(counts.get(k, 0)) for k in STATE_KEYS)
    return {
        "counts": {k: int(counts.get(k, 0)) for k in STATE_KEYS},
        "shares": {k: _pct(int(counts.get(k, 0)), int(total)) for k in STATE_KEYS},
        "total": int(total),
    }


def _render_md(payload: Dict[str, object]) -> str:
    lines: List[str] = []
    meta = payload.get("meta", {}) or {}
    lines.append("# Independent Regime Summary")
    lines.append("")
    lines.append(
        f"- pair: `{meta.get('pair')}` timeframe: `{meta.get('timeframe')}` timerange: `{meta.get('timerange')}`"
    )
    lines.append(
        f"- rows_valid_features: `{meta.get('rows_valid_features')}` start: `{meta.get('start_utc')}` end: `{meta.get('end_utc')}`"
    )
    lines.append("")

    lines.append("## State Shares")
    lines.append("")
    lines.append("| mode | range | trend | neutral | unlabeled |")
    lines.append("|---|---:|---:|---:|---:|")
    for mode in ("intraday", "swing"):
        entry = ((payload.get("state_shares") or {}).get(mode) or {})
        shares = entry.get("shares", {}) or {}
        lines.append(
            f"| {mode} | {100.0*float(shares.get('range',0.0)):.2f}% | {100.0*float(shares.get('trend',0.0)):.2f}% | "
            f"{100.0*float(shares.get('neutral',0.0)):.2f}% | {100.0*float(shares.get('unlabeled',0.0)):.2f}% |"
        )
    lines.append("")

    dur = payload.get("segment_duration", {}) or {}
    for mode in ("intraday", "swing"):
        block = dur.get(mode, {}) or {}
        states = block.get("states", {}) or {}
        lines.append(f"## {mode.capitalize()} Durations")
        lines.append("")
        lines.append("| state | segments | median_days | p90_days | p99_days | max_days |")
        lines.append("|---|---:|---:|---:|---:|---:|")
        for state in ("range", "trend", "neutral"):
            s = states.get(state, {}) or {}
            lines.append(
                f"| {state} | {int(s.get('segment_count',0))} | {float(s.get('median_days',0.0)):.4f} | "
                f"{float(s.get('p90_days',0.0)):.4f} | {float(s.get('p99_days',0.0)):.4f} | {float(s.get('max_days',0.0)):.4f} |"
            )
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True, help="regime_audit report.json path")
    ap.add_argument("--verbose-csv", default="", help="optional per_candle_verbose.csv path")
    ap.add_argument("--out-json", default="", help="optional output json path")
    ap.add_argument("--out-md", default="", help="optional output markdown path")
    args = ap.parse_args()

    report_path = Path(args.report).resolve()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    meta = report.get("meta", {}) or {}
    state_counts = report.get("state_counts", {}) or {}

    payload: Dict[str, object] = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_report": str(report_path),
        "meta": {
            "pair": str(meta.get("pair") or ""),
            "timeframe": str(meta.get("timeframe") or ""),
            "timerange": str(meta.get("timerange") or ""),
            "rows_valid_features": _safe_int(meta.get("rows_valid_features"), 0),
            "start_utc": str(meta.get("start_utc") or ""),
            "end_utc": str(meta.get("end_utc") or ""),
        },
        "state_shares": {
            "intraday": _mode_share_entry((state_counts.get("intraday") or {})),
            "swing": _mode_share_entry((state_counts.get("swing") or {})),
        },
        "transition_counts": report.get("transition_counts", {}) or {},
        "segment_duration": {},
    }

    verbose_csv = str(args.verbose_csv or "").strip()
    if verbose_csv:
        verbose_path = Path(verbose_csv).resolve()
        payload["segment_duration"] = {
            "intraday": _segment_stats_from_verbose_csv(verbose_path, "intraday_state"),
            "swing": _segment_stats_from_verbose_csv(verbose_path, "swing_state"),
        }

    out_json = Path(args.out_json).resolve() if str(args.out_json or "").strip() else report_path.with_name(
        "independent_regime_summary.json"
    )
    out_md = Path(args.out_md).resolve() if str(args.out_md or "").strip() else report_path.with_name(
        "independent_regime_summary.md"
    )
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    out_md.write_text(_render_md(payload), encoding="utf-8")
    print(str(out_json))
    print(str(out_md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
