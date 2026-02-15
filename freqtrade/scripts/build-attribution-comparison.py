#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple


def _load_summary(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sum_windows(rows: List[Dict], key: str) -> int:
    total = 0
    for row in rows:
        try:
            total += int(row.get(key) or 0)
        except Exception:
            continue
    return int(total)


def _pct_from_counts(counts: Dict[str, int], keys: List[str]) -> Dict[str, float]:
    num = {k: int(counts.get(k, 0) or 0) for k in keys}
    total = int(sum(num.values()))
    if total <= 0:
        return {k: 0.0 for k in keys}
    return {k: round(float(num[k]) / float(total), 6) for k in keys}


def _action_mode_counts(counter: Dict[str, int], action: str) -> Dict[str, int]:
    prefix = f"{str(action).upper()}|"
    out: Dict[str, int] = {}
    for k, v in (counter or {}).items():
        key = str(k or "")
        if not key.startswith(prefix):
            continue
        mode = key[len(prefix) :].strip() or "unknown"
        out[mode] = int(out.get(mode, 0)) + int(v or 0)
    return out


def _run_stats(user_data: Path, run_id: str) -> Dict:
    summary_path = user_data / "walkforward" / run_id / "summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"Missing summary for run_id={run_id}: {summary_path}")
    payload = _load_summary(summary_path)
    agg = payload.get("aggregate", {}) or {}
    windows = payload.get("windows", []) or []

    starts = _sum_windows(windows, "action_start")
    holds = _sum_windows(windows, "action_hold")
    stops = _sum_windows(windows, "action_stop")
    fills = _sum_windows(windows, "fills")

    mode_plan_counts = agg.get("mode_plan_counts_total", {}) or {}
    if not mode_plan_counts:
        # Backward compatibility with older runs: infer from effective action mode counts if present.
        eff = agg.get("effective_action_mode_counts_total", {}) or {}
        for key, val in eff.items():
            parts = str(key).split("|", 1)
            if len(parts) != 2:
                continue
            mode = parts[1].strip() or "unknown"
            mode_plan_counts[mode] = int(mode_plan_counts.get(mode, 0)) + int(val or 0)

    start_mode_counts = agg.get("start_mode_counts_total", {}) or {}
    if not start_mode_counts:
        start_mode_counts = _action_mode_counts(agg.get("effective_action_mode_counts_total", {}) or {}, "START")

    fill_mode_counts = agg.get("fill_mode_counts_total", {}) or {}

    mode_share = _pct_from_counts(mode_plan_counts, ["intraday", "swing", "pause"])
    start_share = _pct_from_counts(start_mode_counts, ["intraday", "swing", "pause"])
    fill_share = _pct_from_counts(fill_mode_counts, ["intraday", "swing", "pause"])

    return {
        "run_id": run_id,
        "summary_path": str(summary_path),
        "sum_pnl_quote": float(agg.get("sum_pnl_quote", 0.0) or 0.0),
        "avg_pnl_pct": float(agg.get("avg_pnl_pct", 0.0) or 0.0),
        "profit_factor": agg.get("profit_factor", None),
        "win_rate": float(agg.get("win_rate", 0.0) or 0.0),
        "windows_failed": int(agg.get("windows_failed", 0) or 0),
        "starts": int(starts),
        "holds": int(holds),
        "stops": int(stops),
        "fills": int(fills),
        "top_start_blocker": str(agg.get("top_start_blocker") or ""),
        "top_stop_reason": str(agg.get("top_stop_reason") or ""),
        "mode_plan_counts": {k: int(v) for k, v in mode_plan_counts.items()},
        "start_mode_counts": {k: int(v) for k, v in start_mode_counts.items()},
        "fill_mode_counts": {k: int(v) for k, v in fill_mode_counts.items()},
        "mode_plan_share": mode_share,
        "start_mode_share": start_share,
        "fill_mode_share": fill_share,
    }


def _fmt_pct(v: float) -> str:
    return f"{100.0 * float(v):.2f}%"


def _fmt_num(v: float) -> str:
    return f"{float(v):.6f}"


def _render_markdown(rows: List[Dict], baseline_id: str) -> str:
    baseline = next((r for r in rows if r["run_id"] == baseline_id), None)
    base_pnl = float(baseline["sum_pnl_quote"]) if baseline else 0.0
    base_avg = float(baseline["avg_pnl_pct"]) if baseline else 0.0
    out: List[str] = []
    out.append("# Attribution Comparison")
    out.append("")
    out.append(
        "| run_id | pnl_quote | delta_pnl_vs_base | avg_pnl_pct | delta_avg_vs_base | pf | win_rate | starts | fills | mode(I/S/P) | start(I/S/P) | fill(I/S/P) | top_start_blocker | top_stop_reason |"
    )
    out.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|")
    for r in rows:
        mode_txt = (
            f"{_fmt_pct(r['mode_plan_share']['intraday'])}/"
            f"{_fmt_pct(r['mode_plan_share']['swing'])}/"
            f"{_fmt_pct(r['mode_plan_share']['pause'])}"
        )
        start_txt = (
            f"{_fmt_pct(r['start_mode_share']['intraday'])}/"
            f"{_fmt_pct(r['start_mode_share']['swing'])}/"
            f"{_fmt_pct(r['start_mode_share']['pause'])}"
        )
        fill_txt = (
            f"{_fmt_pct(r['fill_mode_share']['intraday'])}/"
            f"{_fmt_pct(r['fill_mode_share']['swing'])}/"
            f"{_fmt_pct(r['fill_mode_share']['pause'])}"
        )
        pf = r["profit_factor"]
        pf_txt = "null" if pf is None else _fmt_num(float(pf))
        out.append(
            "| "
            + " | ".join(
                [
                    str(r["run_id"]),
                    _fmt_num(float(r["sum_pnl_quote"])),
                    _fmt_num(float(r["sum_pnl_quote"]) - base_pnl),
                    _fmt_num(float(r["avg_pnl_pct"])),
                    _fmt_num(float(r["avg_pnl_pct"]) - base_avg),
                    pf_txt,
                    _fmt_num(float(r["win_rate"])),
                    str(int(r["starts"])),
                    str(int(r["fills"])),
                    mode_txt,
                    start_txt,
                    fill_txt,
                    str(r["top_start_blocker"]),
                    str(r["top_stop_reason"]),
                ]
            )
            + " |"
        )
    out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user-data", default="user_data")
    ap.add_argument("--baseline-run", required=True)
    ap.add_argument("--run-id", action="append", required=True, help="Repeat for each run to include.")
    ap.add_argument("--label", default="attribution_compare")
    ap.add_argument("--out-json", default="")
    ap.add_argument("--out-md", default="")
    args = ap.parse_args()

    user_data = Path(args.user_data)
    if not user_data.is_absolute():
        user_data = (Path(__file__).resolve().parents[1] / user_data).resolve()

    run_ids: List[str] = []
    seen = set()
    for rid in [str(x).strip() for x in (args.run_id or []) if str(x).strip()]:
        if rid in seen:
            continue
        seen.add(rid)
        run_ids.append(rid)
    if args.baseline_run not in seen:
        run_ids.insert(0, str(args.baseline_run))

    rows = [_run_stats(user_data, rid) for rid in run_ids]
    payload = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "baseline_run": str(args.baseline_run),
        "runs": rows,
    }

    out_json = Path(args.out_json) if str(args.out_json).strip() else (user_data / "walkforward" / f"{args.label}.json")
    out_md = Path(args.out_md) if str(args.out_md).strip() else (user_data / "walkforward" / f"{args.label}.md")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    out_md.write_text(_render_markdown(rows, str(args.baseline_run)), encoding="utf-8")
    print(str(out_json))
    print(str(out_md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
