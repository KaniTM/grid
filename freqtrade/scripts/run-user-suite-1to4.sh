#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

TS="${RUN_TS:-$(date -u +%Y%m%dT%H%M%SZ)}"
TIMERANGE="${RUN_TIMERANGE:-20200101-20260213}"
WINDOW_DAYS="${RUN_WINDOW_DAYS:-14}"
STEP_DAYS="${RUN_STEP_DAYS:-14}"
MIN_WINDOW_DAYS="${RUN_MIN_WINDOW_DAYS:-7}"
PAIR="${RUN_PAIR:-ETH/USDT}"
EXCHANGE="${RUN_EXCHANGE:-binance}"
TIMEFRAME="${RUN_TIMEFRAME:-15m}"
FEE_PCT="${RUN_FEE_PCT:-0.10}"
MAX_ORDERS="${RUN_MAX_ORDERS:-40}"
HEARTBEAT_SEC="${RUN_HEARTBEAT_SEC:-30}"
STALL_MAX="${RUN_STALLED_HEARTBEATS_MAX:-20}"

MODE_BASELINE="user_data/regime_audit/regime_calib_long_20200101_20251101_v1/mode_threshold_overrides.json"
MODE_ROUTER_FAST="user_data/regime_audit/regime_daily_20260214/mode_threshold_overrides.json"
MODE_OSDEV="user_data/regime_audit/experiment_overrides/mode_threshold_overrides_osdev_persist_relaxed.json"
MODE_BBWP3="user_data/regime_audit/experiment_overrides/mode_threshold_overrides_bbwp_plus3.json"
MODE_BBWP5="user_data/regime_audit/experiment_overrides/mode_threshold_overrides_bbwp_plus5.json"

RUN_BASE="wf_step6B_attr_${TS}"
RUN_ROUTER="wf_exp_router_fast_attr_${TS}"
RUN_OSDEV="wf_exp_osdev_persist_attr_${TS}"
RUN_BBWP3="wf_exp_bbwp_plus3_attr_${TS}"
RUN_BBWP5="wf_exp_bbwp_plus5_attr_${TS}"
RUN_NOFVG="wf_exp_nofvg_relax_attr_${TS}"
RUN_NOPAUSE="wf_exp_intraday_to_swing_nopause_attr_${TS}"

STRICT_LABEL="wf_attr_compare_strict_${TS}"
ALL_LABEL="wf_attr_compare_all_${TS}"
MANIFEST_PATH="user_data/walkforward/wf_suite_1to4_${TS}.manifest.json"

log() {
  printf '[suite-1to4] %s\n' "$*"
}

run_wf() {
  local label="$1"
  local run_id="$2"
  local strategy="$3"
  local mode_path="$4"

  log "run label=${label} run_id=${run_id} strategy=${strategy} mode_path=${mode_path}"
  python3 scripts/run-user-walkforward-supervisor.py \
    --user-data user_data \
    --max-attempts 8 \
    --retry-delay-sec 20 \
    --retry-backoff-mult 1.5 \
    --max-retry-delay-sec 300 \
    --poll-sec 20 \
    -- \
    --timerange "$TIMERANGE" \
    --window-days "$WINDOW_DAYS" \
    --step-days "$STEP_DAYS" \
    --min-window-days "$MIN_WINDOW_DAYS" \
    --pair "$PAIR" \
    --exchange "$EXCHANGE" \
    --timeframe "$TIMEFRAME" \
    --config-path /freqtrade/user_data/config.json \
    --strategy "$strategy" \
    --strategy-path /freqtrade/user_data/strategies \
    --data-dir /freqtrade/user_data/data/binance \
    --fee-pct "$FEE_PCT" \
    --max-orders-per-side "$MAX_ORDERS" \
    --run-id "$run_id" \
    --mode-thresholds-path "$mode_path" \
    --heartbeat-sec "$HEARTBEAT_SEC" \
    --stalled-heartbeats-max "$STALL_MAX" \
    --fail-on-window-error
}

verify_runs() {
  local args=()
  for rid in "$@"; do
    args+=(--walkforward-run-id "$rid")
  done
  python3 scripts/verify-user-integrity.py --user-data user_data "${args[@]}" --require-state-complete
}

compare_against_base() {
  local run_b="$1"
  local label="$2"
  python3 scripts/compare-walkforward-runs.py \
    --user-data user_data \
    --run-a "$RUN_BASE" \
    --run-b "$run_b" \
    --label "$label"
}

build_attr_table() {
  local label="$1"
  shift
  local run_args=()
  for rid in "$@"; do
    run_args+=(--run-id "$rid")
  done
  python3 scripts/build-attribution-comparison.py \
    --user-data user_data \
    --baseline-run "$RUN_BASE" \
    "${run_args[@]}" \
    --label "$label"
}

write_manifest() {
  python3 - <<'PY' \
    "$MANIFEST_PATH" "$TS" "$TIMERANGE" "$RUN_BASE" "$RUN_ROUTER" "$RUN_OSDEV" "$RUN_BBWP3" "$RUN_BBWP5" "$RUN_NOFVG" "$RUN_NOPAUSE" "$STRICT_LABEL" "$ALL_LABEL"
import json, sys
from datetime import datetime, timezone
from pathlib import Path

(
    manifest_path,
    ts,
    timerange,
    run_base,
    run_router,
    run_osdev,
    run_bbwp3,
    run_bbwp5,
    run_nofvg,
    run_nopause,
    strict_label,
    all_label,
) = sys.argv[1:]

payload = {
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "suite": "run-user-suite-1to4",
    "timestamp_tag": ts,
    "timerange": timerange,
    "run_ids": {
        "baseline_step6b": run_base,
        "router_fast_strict": run_router,
        "osdev_strict": run_osdev,
        "bbwp_plus3_strict": run_bbwp3,
        "bbwp_plus5_relax": run_bbwp5,
        "nofvg_relax": run_nofvg,
        "intraday_to_swing_nopause": run_nopause,
    },
    "comparison_labels": {
        "strict": strict_label,
        "all": all_label,
    },
}
p = Path(manifest_path)
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(str(p))
PY
}

log "start ts=${TS} timerange=${TIMERANGE}"

# #1 Fresh strict runs with new attribution fields.
run_wf "strict_baseline_step6b" "$RUN_BASE" "GridBrainV1" "$MODE_BASELINE"
run_wf "strict_router_fast" "$RUN_ROUTER" "GridBrainV1" "$MODE_ROUTER_FAST"
run_wf "strict_osdev" "$RUN_OSDEV" "GridBrainV1" "$MODE_OSDEV"
run_wf "strict_bbwp_plus3" "$RUN_BBWP3" "GridBrainV1" "$MODE_BBWP3"
verify_runs "$RUN_BASE" "$RUN_ROUTER" "$RUN_OSDEV" "$RUN_BBWP3"

# #2 Consolidated attribution comparisons for strict set.
compare_against_base "$RUN_ROUTER" "step6b_attr_vs_router_fast_${TS}"
compare_against_base "$RUN_OSDEV" "step6b_attr_vs_osdev_${TS}"
compare_against_base "$RUN_BBWP3" "step6b_attr_vs_bbwp3_${TS}"
build_attr_table "$STRICT_LABEL" "$RUN_BASE" "$RUN_ROUTER" "$RUN_OSDEV" "$RUN_BBWP3"

# #3 Controlled gate-relax runs (bbwp +5, no-fvg).
run_wf "relax_bbwp_plus5" "$RUN_BBWP5" "GridBrainV1" "$MODE_BBWP5"
run_wf "relax_nofvg_gate" "$RUN_NOFVG" "GridBrainV1NoFVG" "$MODE_BASELINE"

# #4 Explicit intraday->swing fallback variant (no pause).
run_wf "fallback_intraday_to_swing_nopause" "$RUN_NOPAUSE" "GridBrainV1NoPause" "$MODE_BASELINE"

verify_runs "$RUN_BBWP5" "$RUN_NOFVG" "$RUN_NOPAUSE"

compare_against_base "$RUN_BBWP5" "step6b_attr_vs_bbwp5_${TS}"
compare_against_base "$RUN_NOFVG" "step6b_attr_vs_nofvg_${TS}"
compare_against_base "$RUN_NOPAUSE" "step6b_attr_vs_nopause_${TS}"
build_attr_table "$ALL_LABEL" "$RUN_BASE" "$RUN_ROUTER" "$RUN_OSDEV" "$RUN_BBWP3" "$RUN_BBWP5" "$RUN_NOFVG" "$RUN_NOPAUSE"

# Portable export for cross-machine handoff.
python3 scripts/export-portable-results.py --user-data user_data --latest-runs 12

write_manifest
log "done manifest=${MANIFEST_PATH}"
