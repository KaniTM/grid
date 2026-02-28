#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./scripts/run_c2_checkpoint.sh

Optional env overrides:
  CHECKPOINT_PREFIX=c2
  CHECKPOINT_TAG=c2_YYYYMMDDTHHMMSSZ
  BASELINE_TAG=c0_...
  EXCHANGE=binance
  PAIR=ETH/USDT
  TIMEFRAME=15m
  TIMERANGE=20260209-20260210
  WINDOW_DAYS=1
  STEP_DAYS=1
  MIN_WINDOW_DAYS=1
  RECENT_PLAN_SECONDS=3600

Output:
  freqtrade/user_data/baselines/<CHECKPOINT_TAG>/{logs,metrics}
  - logs: regression.log, backtest.log, walkforward.log, regression_behavior_direct.log
  - metrics: backtest.zip, backtest.meta.json, walkforward.summary.json, walkforward.windows.csv, c2_snapshot.json
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

CHECKPOINT_PREFIX="${CHECKPOINT_PREFIX:-c2}"
CHECKPOINT_TAG="${CHECKPOINT_TAG:-${CHECKPOINT_PREFIX}_$(date -u +%Y%m%dT%H%M%SZ)}"
EXCHANGE="${EXCHANGE:-binance}"
PAIR="${PAIR:-ETH/USDT}"
TIMEFRAME="${TIMEFRAME:-15m}"
TIMERANGE="${TIMERANGE:-20260209-20260210}"
WINDOW_DAYS="${WINDOW_DAYS:-1}"
STEP_DAYS="${STEP_DAYS:-1}"
MIN_WINDOW_DAYS="${MIN_WINDOW_DAYS:-1}"
RECENT_PLAN_SECONDS="${RECENT_PLAN_SECONDS:-3600}"

BASELINE_TAG_DEFAULT=""
if [[ -f "freqtrade/user_data/baselines/.latest_c0_tag" ]]; then
  BASELINE_TAG_DEFAULT="$(tr -d '\n' < freqtrade/user_data/baselines/.latest_c0_tag)"
fi
BASELINE_TAG="${BASELINE_TAG:-${BASELINE_TAG_DEFAULT}}"

PAIR_FS="$(printf '%s' "${PAIR}" | tr '/:' '__')"
BASE_DIR="freqtrade/user_data/baselines/${CHECKPOINT_TAG}"
LOG_DIR="${BASE_DIR}/logs"
METRICS_DIR="${BASE_DIR}/metrics"
WF_RUN_ID="${CHECKPOINT_TAG}_wf"
PLAN_PATH="/freqtrade/user_data/grid_plans/${EXCHANGE}/${PAIR_FS}/grid_plan.latest.json"
STATE_OUT="/freqtrade/user_data/baselines/${CHECKPOINT_TAG}/metrics/grid_executor_v1.regression.state.json"

mkdir -p "${LOG_DIR}" "${METRICS_DIR}"

REG_STATUS=0
BT_STATUS=0
WF_STATUS=0
DIR_STATUS=0

if ./scripts/docker_env.sh regression > "${LOG_DIR}/regression.log" 2>&1; then
  REG_STATUS=0
else
  REG_STATUS=$?
fi

if ./scripts/docker_env.sh backtest \
  --config /freqtrade/user_data/config.json \
  --strategy GridBrainV1 \
  --strategy-path /freqtrade/user_data/strategies \
  --timerange "${TIMERANGE}" \
  --timeframe "${TIMEFRAME}" \
  --datadir /freqtrade/user_data/data/binance \
  --export trades \
  --export-filename "/freqtrade/user_data/baselines/${CHECKPOINT_TAG}/metrics/backtest.json" \
  > "${LOG_DIR}/backtest.log" 2>&1; then
  BT_STATUS=0
else
  BT_STATUS=$?
fi

if ./scripts/docker_env.sh walkforward \
  --timerange "${TIMERANGE}" \
  --window-days "${WINDOW_DAYS}" \
  --step-days "${STEP_DAYS}" \
  --min-window-days "${MIN_WINDOW_DAYS}" \
  --pair "${PAIR}" \
  --run-id "${WF_RUN_ID}" \
  --fail-on-window-error \
  > "${LOG_DIR}/walkforward.log" 2>&1; then
  WF_STATUS=0
else
  WF_STATUS=$?
fi

if ./scripts/docker_env.sh cmd \
  "python /freqtrade/user_data/scripts/user_regression_suite.py --plan '${PLAN_PATH}' --state-out '${STATE_OUT}' --recent-plan-seconds '${RECENT_PLAN_SECONDS}'" \
  > "${LOG_DIR}/regression_behavior_direct.log" 2>&1; then
  DIR_STATUS=0
else
  DIR_STATUS=$?
fi

# Copy backtest artifacts from the canonical backtest results pointer.
LATEST_BACKTEST_ZIP="$(
  python3 - <<'PY'
import json
from pathlib import Path
p = Path("freqtrade/user_data/backtest_results/.last_result.json")
if not p.exists():
    print("")
else:
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
        print(str(obj.get("latest_backtest", "")))
    except Exception:
        print("")
PY
)"

if [[ -n "${LATEST_BACKTEST_ZIP}" ]]; then
  SRC_ZIP="freqtrade/user_data/backtest_results/${LATEST_BACKTEST_ZIP}"
  SRC_META="freqtrade/user_data/backtest_results/${LATEST_BACKTEST_ZIP%.zip}.meta.json"
  if [[ -f "${SRC_ZIP}" ]]; then
    cp "${SRC_ZIP}" "${METRICS_DIR}/backtest.zip"
  elif [[ "${BT_STATUS}" -eq 0 ]]; then
    BT_STATUS=97
  fi
  if [[ -f "${SRC_META}" ]]; then
    cp "${SRC_META}" "${METRICS_DIR}/backtest.meta.json"
  elif [[ "${BT_STATUS}" -eq 0 ]]; then
    BT_STATUS=98
  fi
elif [[ "${BT_STATUS}" -eq 0 ]]; then
  BT_STATUS=99
fi

# Copy walkforward summary artifacts into the checkpoint metrics folder.
WF_SUMMARY="freqtrade/user_data/walkforward/${WF_RUN_ID}/summary.json"
WF_WINDOWS="freqtrade/user_data/walkforward/${WF_RUN_ID}/windows.csv"
if [[ -f "${WF_SUMMARY}" ]]; then
  cp "${WF_SUMMARY}" "${METRICS_DIR}/walkforward.summary.json"
elif [[ "${WF_STATUS}" -eq 0 ]]; then
  WF_STATUS=97
fi
if [[ -f "${WF_WINDOWS}" ]]; then
  cp "${WF_WINDOWS}" "${METRICS_DIR}/walkforward.windows.csv"
elif [[ "${WF_STATUS}" -eq 0 ]]; then
  WF_STATUS=98
fi

export CHECKPOINT_TAG BASELINE_TAG PAIR TIMEFRAME TIMERANGE EXCHANGE RECENT_PLAN_SECONDS
export REG_STATUS BT_STATUS WF_STATUS DIR_STATUS

python3 - <<'PY'
from __future__ import annotations

import json
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def to_num(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def delta_num(cur: Any, base: Any) -> float | None:
    cur_n = to_num(cur)
    base_n = to_num(base)
    if cur_n is None or base_n is None:
        return None
    return cur_n - base_n


def infer_reason(log_path: Path) -> str | None:
    if not log_path.exists():
        return "log_missing"
    try:
        lines = [ln.strip() for ln in log_path.read_text(encoding="utf-8", errors="ignore").splitlines() if ln.strip()]
    except Exception:
        return None
    if not lines:
        return None
    markers = ("AssertionError:", "Traceback", "Exception", "ERROR", "failed")
    for marker in markers:
        matches = [ln for ln in lines if marker in ln]
        if matches:
            return matches[-1][:400]
    return None


root = Path("/home/kani/grid-ml-system")
c2_tag = os.environ["CHECKPOINT_TAG"]
baseline_tag = os.environ.get("BASELINE_TAG", "").strip()
pair = os.environ["PAIR"]
timeframe = os.environ["TIMEFRAME"]
timerange = os.environ["TIMERANGE"]
recent_plan_seconds = int(os.environ["RECENT_PLAN_SECONDS"])

reg_status = int(os.environ["REG_STATUS"])
bt_status = int(os.environ["BT_STATUS"])
wf_status = int(os.environ["WF_STATUS"])
dir_status = int(os.environ["DIR_STATUS"])

base_dir = root / "freqtrade/user_data/baselines" / c2_tag
logs_dir = base_dir / "logs"
metrics_dir = base_dir / "metrics"

reg_log = logs_dir / "regression.log"
bt_log = logs_dir / "backtest.log"
wf_log = logs_dir / "walkforward.log"
dir_log = logs_dir / "regression_behavior_direct.log"

snapshot: dict[str, Any] = {
    "c2_tag": c2_tag,
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "based_on_c0_tag": baseline_tag or None,
    "scope": {
        "pair": pair,
        "timeframe": timeframe,
        "timerange": timerange,
        "docker_wrapper": "./scripts/docker_env.sh",
    },
    "runs": {
        "regression_wrapper": {
            "status": "ok" if reg_status == 0 else "fail",
            "reason": None if reg_status == 0 else infer_reason(reg_log),
            "ruff_errors": None,
            "command": "./scripts/docker_env.sh regression",
            "log_path": f"freqtrade/user_data/baselines/{c2_tag}/logs/regression.log",
        },
        "backtest": {
            "status": "ok" if bt_status == 0 else "fail",
            "reason": None if bt_status == 0 else infer_reason(bt_log),
            "command": "./scripts/docker_env.sh backtest --config /freqtrade/user_data/config.json --strategy GridBrainV1 --strategy-path /freqtrade/user_data/strategies --timerange "
            f"{timerange} --timeframe {timeframe} --datadir /freqtrade/user_data/data/binance --export trades --export-filename /freqtrade/user_data/baselines/<C2_TAG>/metrics/backtest.json",
            "log_path": f"freqtrade/user_data/baselines/{c2_tag}/logs/backtest.log",
            "zip_path": f"freqtrade/user_data/baselines/{c2_tag}/metrics/backtest.zip",
            "meta_path": f"freqtrade/user_data/baselines/{c2_tag}/metrics/backtest.meta.json",
            "metrics": {},
        },
        "walkforward": {
            "status": "ok" if wf_status == 0 else "fail",
            "reason": None if wf_status == 0 else infer_reason(wf_log),
            "run_id": f"{c2_tag}_wf",
            "command": "./scripts/docker_env.sh walkforward --timerange "
            f"{timerange} --window-days 1 --step-days 1 --min-window-days 1 --pair {pair} --run-id <C2_TAG>_wf --fail-on-window-error",
            "log_path": f"freqtrade/user_data/baselines/{c2_tag}/logs/walkforward.log",
            "summary_path": f"freqtrade/user_data/baselines/{c2_tag}/metrics/walkforward.summary.json",
            "windows_path": f"freqtrade/user_data/baselines/{c2_tag}/metrics/walkforward.windows.csv",
            "aggregate": {},
            "window_001": {},
        },
        "regression_behavior_direct": {
            "status": "ok" if dir_status == 0 else "fail",
            "reason": None if dir_status == 0 else infer_reason(dir_log),
            "command": "./scripts/docker_env.sh cmd \"python /freqtrade/user_data/scripts/user_regression_suite.py --plan '/freqtrade/user_data/grid_plans/binance/ETH_USDT/grid_plan.latest.json' --state-out '/freqtrade/user_data/baselines/<C2_TAG>/metrics/grid_executor_v1.regression.state.json' --recent-plan-seconds "
            f"{recent_plan_seconds}\"",
            "log_path": f"freqtrade/user_data/baselines/{c2_tag}/logs/regression_behavior_direct.log",
        },
    },
}

# Optional backtest metrics extraction
bt_zip = metrics_dir / "backtest.zip"
if bt_zip.exists():
    try:
        with zipfile.ZipFile(bt_zip) as zf:
            result_json = next(name for name in zf.namelist() if name.endswith(".json") and "_config" not in name)
            payload = json.loads(zf.read(result_json))
        strat = payload.get("strategy", {}).get("GridBrainV1", {})
        snapshot["runs"]["backtest"]["metrics"] = {
            "total_trades": int(strat.get("total_trades", 0) or 0),
            "profit_total": float(strat.get("profit_total", 0.0) or 0.0),
            "profit_total_abs": float(strat.get("profit_total_abs", 0.0) or 0.0),
            "profit_factor": float(strat.get("profit_factor", 0.0) or 0.0),
            "max_drawdown": to_num(strat.get("max_drawdown_account")),
            "wins": int(strat.get("wins", 0) or 0),
            "draws": int(strat.get("draws", 0) or 0),
            "losses": int(strat.get("losses", 0) or 0),
            "winrate": float(strat.get("winrate", 0.0) or 0.0),
        }
    except Exception:
        pass

# Optional walkforward metrics extraction
wf_summary = metrics_dir / "walkforward.summary.json"
if wf_summary.exists():
    try:
        wf_obj = json.loads(wf_summary.read_text(encoding="utf-8"))
        agg = wf_obj.get("aggregate", {})
        w0 = (wf_obj.get("windows") or [{}])[0]
        snapshot["runs"]["walkforward"]["aggregate"] = {
            "windows_total": int(agg.get("windows_total", 0) or 0),
            "windows_ok": int(agg.get("windows_ok", 0) or 0),
            "windows_failed": int(agg.get("windows_failed", 0) or 0),
            "sum_pnl_quote": float(agg.get("sum_pnl_quote", 0.0) or 0.0),
            "avg_pnl_pct": float(agg.get("avg_pnl_pct", 0.0) or 0.0),
            "profit_factor": agg.get("profit_factor"),
            "win_rate": float(agg.get("win_rate", 0.0) or 0.0),
            "top_start_blocker": agg.get("top_start_blocker"),
            "top_stop_reason": agg.get("top_stop_reason"),
        }
        snapshot["runs"]["walkforward"]["window_001"] = {
            "fills": int(w0.get("fills", 0) or 0),
            "stop_events": int(w0.get("stop_events", 0) or 0),
            "action_start": int(w0.get("action_start", 0) or 0),
            "action_hold": int(w0.get("action_hold", 0) or 0),
            "action_stop": int(w0.get("action_stop", 0) or 0),
            "pnl_pct": float(w0.get("pnl_pct", 0.0) or 0.0),
            "pnl_quote": float(w0.get("pnl_quote", 0.0) or 0.0),
            "seed_events": int(w0.get("seed_events", 0) or 0),
            "rebuild_events": int(w0.get("rebuild_events", 0) or 0),
            "soft_adjust_events": int(w0.get("soft_adjust_events", 0) or 0),
        }
    except Exception:
        pass

# Optional delta vs baseline snapshot
delta_vs_baseline: dict[str, Any] = {}
if baseline_tag:
    prefix = baseline_tag.split("_", 1)[0] if "_" in baseline_tag else baseline_tag
    baseline_snapshot = (
        root / "freqtrade/user_data/baselines" / baseline_tag / "metrics" / f"{prefix}_snapshot.json"
    )
    if not baseline_snapshot.exists():
        fallback = root / "freqtrade/user_data/baselines" / baseline_tag / "metrics" / "c0_snapshot.json"
        if fallback.exists():
            baseline_snapshot = fallback
    if baseline_snapshot.exists():
        try:
            base = json.loads(baseline_snapshot.read_text(encoding="utf-8"))
            base_runs = base.get("runs", {})
            base_bt = base_runs.get("backtest", {}).get("metrics", {})
            base_wf_agg = base_runs.get("walkforward", {}).get("aggregate", {})
            base_wf_w0 = base_runs.get("walkforward", {}).get("window_001", {})
            cur_bt = snapshot["runs"]["backtest"].get("metrics", {})
            cur_wf_agg = snapshot["runs"]["walkforward"].get("aggregate", {})
            cur_wf_w0 = snapshot["runs"]["walkforward"].get("window_001", {})
            delta_vs_baseline = {
                "status": {
                    "regression_wrapper": {
                        "baseline": base_runs.get("regression_wrapper", {}).get("status"),
                        "current": snapshot["runs"]["regression_wrapper"]["status"],
                    },
                    "backtest": {
                        "baseline": base_runs.get("backtest", {}).get("status"),
                        "current": snapshot["runs"]["backtest"]["status"],
                    },
                    "walkforward": {
                        "baseline": base_runs.get("walkforward", {}).get("status"),
                        "current": snapshot["runs"]["walkforward"]["status"],
                    },
                    "regression_behavior_direct": {
                        "baseline": base_runs.get("regression_behavior_direct", {}).get("status"),
                        "current": snapshot["runs"]["regression_behavior_direct"]["status"],
                    },
                },
                "backtest": {
                    "total_trades_delta": delta_num(cur_bt.get("total_trades"), base_bt.get("total_trades")),
                    "profit_total_delta": delta_num(cur_bt.get("profit_total"), base_bt.get("profit_total")),
                    "profit_total_abs_delta": delta_num(cur_bt.get("profit_total_abs"), base_bt.get("profit_total_abs")),
                    "profit_factor_delta": delta_num(cur_bt.get("profit_factor"), base_bt.get("profit_factor")),
                    "max_drawdown_delta": delta_num(cur_bt.get("max_drawdown"), base_bt.get("max_drawdown")),
                },
                "walkforward_aggregate": {
                    "windows_total_delta": delta_num(cur_wf_agg.get("windows_total"), base_wf_agg.get("windows_total")),
                    "windows_ok_delta": delta_num(cur_wf_agg.get("windows_ok"), base_wf_agg.get("windows_ok")),
                    "windows_failed_delta": delta_num(cur_wf_agg.get("windows_failed"), base_wf_agg.get("windows_failed")),
                    "sum_pnl_quote_delta": delta_num(cur_wf_agg.get("sum_pnl_quote"), base_wf_agg.get("sum_pnl_quote")),
                    "avg_pnl_pct_delta": delta_num(cur_wf_agg.get("avg_pnl_pct"), base_wf_agg.get("avg_pnl_pct")),
                    "win_rate_delta": delta_num(cur_wf_agg.get("win_rate"), base_wf_agg.get("win_rate")),
                    "top_start_blocker_changed": cur_wf_agg.get("top_start_blocker") != base_wf_agg.get("top_start_blocker"),
                    "top_stop_reason_changed": cur_wf_agg.get("top_stop_reason") != base_wf_agg.get("top_stop_reason"),
                    "top_start_blocker_baseline": base_wf_agg.get("top_start_blocker"),
                    "top_start_blocker_current": cur_wf_agg.get("top_start_blocker"),
                    "top_stop_reason_baseline": base_wf_agg.get("top_stop_reason"),
                    "top_stop_reason_current": cur_wf_agg.get("top_stop_reason"),
                },
                "walkforward_window_001": {
                    "fills_delta": delta_num(cur_wf_w0.get("fills"), base_wf_w0.get("fills")),
                    "stop_events_delta": delta_num(cur_wf_w0.get("stop_events"), base_wf_w0.get("stop_events")),
                    "action_start_delta": delta_num(cur_wf_w0.get("action_start"), base_wf_w0.get("action_start")),
                    "action_hold_delta": delta_num(cur_wf_w0.get("action_hold"), base_wf_w0.get("action_hold")),
                    "action_stop_delta": delta_num(cur_wf_w0.get("action_stop"), base_wf_w0.get("action_stop")),
                    "pnl_pct_delta": delta_num(cur_wf_w0.get("pnl_pct"), base_wf_w0.get("pnl_pct")),
                    "pnl_quote_delta": delta_num(cur_wf_w0.get("pnl_quote"), base_wf_w0.get("pnl_quote")),
                },
            }
        except Exception:
            delta_vs_baseline = {}

snapshot["delta_vs_baseline"] = delta_vs_baseline

out_path = metrics_dir / "c2_snapshot.json"
out_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
PY

echo "CHECKPOINT_TAG=${CHECKPOINT_TAG}"
echo "BASELINE_TAG=${BASELINE_TAG:-unknown}"
echo "C2_REGRESSION=${REG_STATUS}"
echo "C2_BACKTEST=${BT_STATUS}"
echo "C2_WALKFORWARD=${WF_STATUS}"
echo "C2_DIRECT_REGRESSION=${DIR_STATUS}"

if [[ "${REG_STATUS}" -eq 0 && "${BT_STATUS}" -eq 0 && "${WF_STATUS}" -eq 0 && "${DIR_STATUS}" -eq 0 ]]; then
  echo "${CHECKPOINT_TAG}" > freqtrade/user_data/baselines/.latest_c2_tag
  echo "C2_PIPELINE=SUCCESS"
  exit 0
fi

echo "C2_PIPELINE=FAIL"
exit 1
