#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/kani/grid-ml-system"
FT="$ROOT/freqtrade"
cd "$FT"

RUN_ROUTER="wf_exp_router_fast_20200101_20260213_v2_strict"
RUN_OSDEV="wf_exp_osdev_persist_20200101_20260213_v3_strict_seq"
RUN_BBWP="wf_exp_bbwp_plus3_20200101_20260213_v2_strictfix2"

state_file() {
  local run_id="$1"
  printf '%s\n' "user_data/walkforward/${run_id}/_state/state.json"
}

state_json_value() {
  local file="$1"
  local key="$2"
  python3 - <<'PY' "$file" "$key"
import json,sys
p=sys.argv[1]
k=sys.argv[2]
try:
    d=json.load(open(p))
    v=d
    for part in k.split('.'):
        if isinstance(v, dict):
            v=v.get(part)
        else:
            v=None
            break
    if v is None:
        print("")
    else:
        print(v)
except Exception:
    print("")
PY
}

wait_for_clean_complete() {
  local run_id="$1"
  local sf
  sf="$(state_file "$run_id")"
  echo "[orchestrator] waiting run_id=${run_id} state=${sf}"
  while true; do
    if [[ ! -f "$sf" ]]; then
      echo "[orchestrator] state missing for ${run_id}; sleeping 30s"
      sleep 30
      continue
    fi
    local status step failed done total updated
    status="$(state_json_value "$sf" status)"
    step="$(state_json_value "$sf" step_word)"
    failed="$(state_json_value "$sf" windows_failed)"
    done="$(state_json_value "$sf" windows_completed)"
    total="$(state_json_value "$sf" windows_total)"
    updated="$(state_json_value "$sf" updated_utc)"
    echo "[orchestrator] run=${run_id} status=${status:-na} step=${step:-na} done=${done:-na}/${total:-na} failed=${failed:-na} updated=${updated:-na}"

    if [[ "${step}" == "RUN_COMPLETE" && "${status}" == "completed" && "${failed:-0}" == "0" ]]; then
      echo "[orchestrator] run ${run_id} clean complete"
      break
    fi

    if [[ "${status}" == "failed" || "${step}" == "RUN_ABORT_ON_WINDOW_ERROR" ]]; then
      echo "[orchestrator] run ${run_id} failed status=${status} step=${step} failed=${failed}; exiting"
      exit 2
    fi

    sleep 60
  done
}

echo "[orchestrator] start $(date -Is)"

# 1) Wait for osdev (already running in another session) to complete cleanly.
wait_for_clean_complete "$RUN_OSDEV"

# 2) Resume BBWP run to clean completion under supervisor.
python3 scripts/run-user-walkforward-supervisor.py \
  --user-data user_data \
  --max-attempts 8 \
  --retry-delay-sec 20 \
  --retry-backoff-mult 1.5 \
  --max-retry-delay-sec 300 \
  --poll-sec 10 \
  -- \
  --timerange 20200101-20260213 \
  --window-days 14 \
  --step-days 14 \
  --min-window-days 7 \
  --pair ETH/USDT \
  --exchange binance \
  --timeframe 15m \
  --config-path /freqtrade/user_data/config.json \
  --strategy GridBrainV1 \
  --strategy-path /freqtrade/user_data/strategies \
  --data-dir /freqtrade/user_data/data/binance \
  --fee-pct 0.10 \
  --max-orders-per-side 40 \
  --run-id "$RUN_BBWP" \
  --mode-thresholds-path user_data/regime_audit/experiment_overrides/mode_threshold_overrides_bbwp_plus3.json \
  --resume \
  --fail-on-window-error

# 3) Verify integrity of all 3 runs (require RUN_COMPLETE).
python3 scripts/verify-user-integrity.py \
  --user-data user_data \
  --walkforward-run-id "$RUN_ROUTER" \
  --walkforward-run-id "$RUN_OSDEV" \
  --walkforward-run-id "$RUN_BBWP" \
  --require-state-complete

# 4) Generate pairwise AB comparisons for assessment.
python3 scripts/compare-walkforward-runs.py --user-data user_data --run-a "$RUN_ROUTER" --run-b "$RUN_OSDEV" --label router_vs_osdev_strict_clean
python3 scripts/compare-walkforward-runs.py --user-data user_data --run-a "$RUN_ROUTER" --run-b "$RUN_BBWP" --label router_vs_bbwp_strict_clean
python3 scripts/compare-walkforward-runs.py --user-data user_data --run-a "$RUN_OSDEV" --run-b "$RUN_BBWP" --label osdev_vs_bbwp_strict_clean

# 5) Build shortlist docs for main decision paths.
python3 scripts/make-walkforward-tuning-shortlist.py --user-data user_data --run-a "$RUN_ROUTER" --run-b "$RUN_OSDEV" --out-prefix wf_tune_shortlist_router_vs_osdev
python3 scripts/make-walkforward-tuning-shortlist.py --user-data user_data --run-a "$RUN_ROUTER" --run-b "$RUN_BBWP" --out-prefix wf_tune_shortlist_router_vs_bbwp

echo "[orchestrator] done $(date -Is)"
