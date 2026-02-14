#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

usage() {
    cat <<'EOF'
Usage:
  scripts/run-user-daily-workflow.sh [--profile light|research] [--cleanup conservative|full]

Profiles:
  light     Sync + export + cleanup. Run stage is skipped.
  research  Sync + regime audit + walkforward(resume) + export + cleanup.

Cleanup modes:
  conservative  Keeps regime verbose artifacts (features/transition dumps).
  full          Deletes heavy regime verbose artifacts too.

Environment overrides (common):
  PAIRS="ETH/USDT"
  TIMEFRAMES="15m 1h 4h"
  SYNC_MODE="append"              # append | prepend | full
  SYNC_TIMERANGE="20200101-20260214"  # needed for SYNC_MODE=full
  SYNC_START_DAY="20200101"       # needed for SYNC_MODE=prepend
  SYNC_END_DAY="20260214"
  SYNC_STALLED_HEARTBEATS_MAX=10
  EXPORT_LATEST_RUNS=6
  KEEP_WALKFORWARD_RUNS=0         # if >0, prune old run dirs
  KEEP_REGIME_RUNS=0              # if >0, prune old run dirs

Research profile overrides:
  REGIME_TIMERANGE="20200101-20260214"
  REGIME_RUN_ID="regime_daily_20260214"
  REGIME_STALLED_HEARTBEATS_MAX=10
  WF_TIMERANGE="20200101-20260214"
  WF_RUN_ID="wf_daily_eth_14d"
  WF_STALLED_HEARTBEATS_MAX=10
EOF
}

PROFILE="research"
CLEANUP_MODE="conservative"

while (($# > 0)); do
    case "$1" in
        --profile)
            PROFILE="${2:-}"
            shift 2
            ;;
        --cleanup)
            CLEANUP_MODE="${2:-}"
            shift 2
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

if [[ "${PROFILE}" != "light" && "${PROFILE}" != "research" ]]; then
    echo "Invalid --profile: ${PROFILE}" >&2
    exit 1
fi
if [[ "${CLEANUP_MODE}" != "conservative" && "${CLEANUP_MODE}" != "full" ]]; then
    echo "Invalid --cleanup: ${CLEANUP_MODE}" >&2
    exit 1
fi

TODAY_UTC="$(date -u +%Y%m%d)"
PAIRS="${PAIRS:-ETH/USDT}"
TIMEFRAMES="${TIMEFRAMES:-15m 1h 4h}"
SYNC_MODE="${SYNC_MODE:-append}"
SYNC_OVERLAP_DAYS="${SYNC_OVERLAP_DAYS:-2}"
SYNC_HEARTBEAT_SEC="${SYNC_HEARTBEAT_SEC:-30}"
SYNC_STALLED_HEARTBEATS_MAX="${SYNC_STALLED_HEARTBEATS_MAX:-0}"
SYNC_TIMERANGE="${SYNC_TIMERANGE:-}"
SYNC_START_DAY="${SYNC_START_DAY:-}"
SYNC_END_DAY="${SYNC_END_DAY:-}"
SYNC_BOOTSTRAP_START="${SYNC_BOOTSTRAP_START:-20200101}"

EXPORT_LATEST_RUNS="${EXPORT_LATEST_RUNS:-6}"

RUN_REGIME_AUDIT="${RUN_REGIME_AUDIT:-$([[ "${PROFILE}" == "research" ]] && echo 1 || echo 0)}"
RUN_WALKFORWARD="${RUN_WALKFORWARD:-$([[ "${PROFILE}" == "research" ]] && echo 1 || echo 0)}"

REGIME_PAIR="${REGIME_PAIR:-ETH/USDT}"
REGIME_TIMEFRAME="${REGIME_TIMEFRAME:-15m}"
REGIME_TIMERANGE="${REGIME_TIMERANGE:-20200101-${TODAY_UTC}}"
REGIME_RUN_ID="${REGIME_RUN_ID:-regime_daily_${TODAY_UTC}}"
REGIME_HEARTBEAT_SEC="${REGIME_HEARTBEAT_SEC:-60}"
REGIME_STALLED_HEARTBEATS_MAX="${REGIME_STALLED_HEARTBEATS_MAX:-0}"
REGIME_EMIT_FEATURES="${REGIME_EMIT_FEATURES:-0}"
REGIME_EMIT_VERBOSE="${REGIME_EMIT_VERBOSE:-0}"

WF_PAIR="${WF_PAIR:-ETH/USDT}"
WF_EXCHANGE="${WF_EXCHANGE:-binance}"
WF_TIMEFRAME="${WF_TIMEFRAME:-15m}"
WF_TIMERANGE="${WF_TIMERANGE:-20200101-${TODAY_UTC}}"
WF_WINDOW_DAYS="${WF_WINDOW_DAYS:-14}"
WF_STEP_DAYS="${WF_STEP_DAYS:-14}"
WF_MIN_WINDOW_DAYS="${WF_MIN_WINDOW_DAYS:-7}"
WF_PAIR_FS="${WF_PAIR//\//_}"
WF_PAIR_FS="${WF_PAIR_FS//:/_}"
WF_RUN_ID="${WF_RUN_ID:-wf_daily_${WF_PAIR_FS}_w${WF_WINDOW_DAYS}_s${WF_STEP_DAYS}}"
WF_CONFIG_PATH="${WF_CONFIG_PATH:-/freqtrade/user_data/config.json}"
WF_STRATEGY="${WF_STRATEGY:-GridBrainV1}"
WF_STRATEGY_PATH="${WF_STRATEGY_PATH:-/freqtrade/user_data/strategies}"
WF_DATA_DIR="${WF_DATA_DIR:-/freqtrade/user_data/data/binance}"
WF_FEE_PCT="${WF_FEE_PCT:-0.10}"
WF_MAX_ORDERS_PER_SIDE="${WF_MAX_ORDERS_PER_SIDE:-40}"
WF_HEARTBEAT_SEC="${WF_HEARTBEAT_SEC:-60}"
WF_STALLED_HEARTBEATS_MAX="${WF_STALLED_HEARTBEATS_MAX:-0}"
WF_CARRY_CAPITAL="${WF_CARRY_CAPITAL:-0}"
WF_CLOSE_ON_STOP="${WF_CLOSE_ON_STOP:-0}"
WF_REVERSE_FILL="${WF_REVERSE_FILL:-0}"
WF_ALLOW_OVERLAP="${WF_ALLOW_OVERLAP:-0}"
WF_ALLOW_SINGLE_PLAN="${WF_ALLOW_SINGLE_PLAN:-0}"
WF_SKIP_BACKTESTING="${WF_SKIP_BACKTESTING:-0}"
WF_FAIL_ON_WINDOW_ERROR="${WF_FAIL_ON_WINDOW_ERROR:-0}"
WF_BACKTESTING_EXTRA="${WF_BACKTESTING_EXTRA:-}"
WF_SIM_EXTRA="${WF_SIM_EXTRA:-}"
WF_MODE_THRESHOLDS_PATH="${WF_MODE_THRESHOLDS_PATH:-}"
WF_REGIME_THRESHOLD_PROFILE="${WF_REGIME_THRESHOLD_PROFILE:-}"

KEEP_WALKFORWARD_RUNS="${KEEP_WALKFORWARD_RUNS:-0}"
KEEP_REGIME_RUNS="${KEEP_REGIME_RUNS:-0}"
PIN_WALKFORWARD_RUNS="${PIN_WALKFORWARD_RUNS:-}"   # comma-separated run ids
PIN_REGIME_RUNS="${PIN_REGIME_RUNS:-}"             # comma-separated run ids
ALLOW_DELETE_WITH_MISSING_BALANCES="${ALLOW_DELETE_WITH_MISSING_BALANCES:-0}"

parse_csv_to_array() {
    local raw="$1"
    local -n out_ref="$2"
    raw="${raw//,/ }"
    read -r -a out_ref <<<"${raw}"
}

stage() {
    local idx="$1"
    local total="$2"
    local name="$3"
    echo "[daily] ${idx}/${total} ${name}"
}

run_sync() {
    local pairs_arr=()
    local tfs_arr=()
    parse_csv_to_array "${PAIRS}" pairs_arr
    parse_csv_to_array "${TIMEFRAMES}" tfs_arr

    if ((${#pairs_arr[@]} == 0)); then
        echo "[daily] no pairs provided" >&2
        exit 1
    fi
    if ((${#tfs_arr[@]} == 0)); then
        echo "[daily] no timeframes provided" >&2
        exit 1
    fi

    local cmd=(
        python3 scripts/run-user-data-sync.py
        --pairs "${pairs_arr[@]}"
        --timeframes "${tfs_arr[@]}"
        --mode "${SYNC_MODE}"
        --overlap-days "${SYNC_OVERLAP_DAYS}"
        --bootstrap-start "${SYNC_BOOTSTRAP_START}"
        --heartbeat-sec "${SYNC_HEARTBEAT_SEC}"
        --stalled-heartbeats-max "${SYNC_STALLED_HEARTBEATS_MAX}"
    )
    if [[ -n "${SYNC_END_DAY}" ]]; then
        cmd+=(--end-day "${SYNC_END_DAY}")
    fi
    if [[ "${SYNC_MODE}" == "full" ]]; then
        if [[ -z "${SYNC_TIMERANGE}" ]]; then
            echo "[daily] SYNC_MODE=full requires SYNC_TIMERANGE" >&2
            exit 1
        fi
        cmd+=(--timerange "${SYNC_TIMERANGE}")
    elif [[ "${SYNC_MODE}" == "prepend" ]]; then
        if [[ -z "${SYNC_START_DAY}" ]]; then
            echo "[daily] SYNC_MODE=prepend requires SYNC_START_DAY" >&2
            exit 1
        fi
        cmd+=(--start-day "${SYNC_START_DAY}")
    fi

    echo "[daily] sync command: ${cmd[*]}"
    "${cmd[@]}"
}

run_regime_audit() {
    local cmd=(
        python3 scripts/run-user-regime-audit.py
        --pair "${REGIME_PAIR}"
        --timeframe "${REGIME_TIMEFRAME}"
        --timerange "${REGIME_TIMERANGE}"
        --run-id "${REGIME_RUN_ID}"
        --heartbeat-sec "${REGIME_HEARTBEAT_SEC}"
        --stalled-heartbeats-max "${REGIME_STALLED_HEARTBEATS_MAX}"
    )
    if [[ "${REGIME_EMIT_FEATURES}" == "1" ]]; then
        cmd+=(--emit-features-csv)
    fi
    if [[ "${REGIME_EMIT_VERBOSE}" == "1" ]]; then
        cmd+=(--emit-verbose)
    fi
    echo "[daily] regime command: ${cmd[*]}"
    "${cmd[@]}"
}

find_latest_mode_overrides() {
    local latest=""
    latest="$(ls -1t user_data/regime_audit/*/mode_threshold_overrides.json 2>/dev/null | head -n1 || true)"
    if [[ -n "${latest}" ]]; then
        printf '%s\n' "${latest}"
    fi
}

run_walkforward() {
    local mode_thresholds="${WF_MODE_THRESHOLDS_PATH}"
    if [[ -z "${mode_thresholds}" ]]; then
        mode_thresholds="$(find_latest_mode_overrides || true)"
    fi

    local cmd=(
        python3 scripts/run-user-walkforward.py
        --timerange "${WF_TIMERANGE}"
        --window-days "${WF_WINDOW_DAYS}"
        --step-days "${WF_STEP_DAYS}"
        --min-window-days "${WF_MIN_WINDOW_DAYS}"
        --pair "${WF_PAIR}"
        --exchange "${WF_EXCHANGE}"
        --timeframe "${WF_TIMEFRAME}"
        --config-path "${WF_CONFIG_PATH}"
        --strategy "${WF_STRATEGY}"
        --strategy-path "${WF_STRATEGY_PATH}"
        --data-dir "${WF_DATA_DIR}"
        --fee-pct "${WF_FEE_PCT}"
        --max-orders-per-side "${WF_MAX_ORDERS_PER_SIDE}"
        --run-id "${WF_RUN_ID}"
        --resume
        --heartbeat-sec "${WF_HEARTBEAT_SEC}"
        --stalled-heartbeats-max "${WF_STALLED_HEARTBEATS_MAX}"
    )
    if [[ "${WF_CARRY_CAPITAL}" == "1" ]]; then
        cmd+=(--carry-capital)
    fi
    if [[ "${WF_CLOSE_ON_STOP}" == "1" ]]; then
        cmd+=(--close-on-stop)
    fi
    if [[ "${WF_REVERSE_FILL}" == "1" ]]; then
        cmd+=(--reverse-fill)
    fi
    if [[ "${WF_ALLOW_OVERLAP}" == "1" ]]; then
        cmd+=(--allow-overlap)
    fi
    if [[ "${WF_ALLOW_SINGLE_PLAN}" == "1" ]]; then
        cmd+=(--allow-single-plan)
    fi
    if [[ "${WF_SKIP_BACKTESTING}" == "1" ]]; then
        cmd+=(--skip-backtesting)
    fi
    if [[ "${WF_FAIL_ON_WINDOW_ERROR}" == "1" ]]; then
        cmd+=(--fail-on-window-error)
    fi
    if [[ -n "${WF_BACKTESTING_EXTRA}" ]]; then
        cmd+=(--backtesting-extra "${WF_BACKTESTING_EXTRA}")
    fi
    if [[ -n "${WF_SIM_EXTRA}" ]]; then
        cmd+=(--sim-extra "${WF_SIM_EXTRA}")
    fi
    if [[ -n "${WF_REGIME_THRESHOLD_PROFILE}" ]]; then
        cmd+=(--regime-threshold-profile "${WF_REGIME_THRESHOLD_PROFILE}")
    fi
    if [[ -n "${mode_thresholds}" ]]; then
        cmd+=(--mode-thresholds-path "${mode_thresholds}")
    fi
    echo "[daily] walkforward command: ${cmd[*]}"
    "${cmd[@]}"
}

run_export() {
    local cmd=(
        python3 scripts/export-portable-results.py
        --user-data user_data
        --latest-runs "${EXPORT_LATEST_RUNS}"
    )
    echo "[daily] export command: ${cmd[*]}"
    "${cmd[@]}"
}

append_pin_args() {
    local csv="$1"
    local kind="$2"
    local -n out_ref="$3"
    if [[ -z "${csv}" ]]; then
        return
    fi
    local arr=()
    parse_csv_to_array "${csv}" arr
    local item
    for item in "${arr[@]}"; do
        [[ -n "${item}" ]] || continue
        if [[ "${kind}" == "wf" ]]; then
            out_ref+=(--pin-walkforward-run "${item}")
        else
            out_ref+=(--pin-regime-run "${item}")
        fi
    done
}

run_cleanup() {
    local cmd=(
        python3 scripts/manage-user-artifacts.py
        --user-data user_data
        --apply
    )
    if [[ "${CLEANUP_MODE}" == "conservative" ]]; then
        cmd+=(--no-prune-regime-verbose)
    fi
    if [[ "${ALLOW_DELETE_WITH_MISSING_BALANCES}" == "1" ]]; then
        cmd+=(--allow-delete-with-missing-balances)
    fi
    if [[ "${KEEP_WALKFORWARD_RUNS}" -gt 0 ]]; then
        cmd+=(--keep-walkforward-runs "${KEEP_WALKFORWARD_RUNS}")
    fi
    if [[ "${KEEP_REGIME_RUNS}" -gt 0 ]]; then
        cmd+=(--keep-regime-runs "${KEEP_REGIME_RUNS}")
    fi
    append_pin_args "${PIN_WALKFORWARD_RUNS}" "wf" cmd
    append_pin_args "${PIN_REGIME_RUNS}" "regime" cmd

    echo "[daily] cleanup command: ${cmd[*]}"
    "${cmd[@]}"
}

TOTAL_STAGES=4
stage 1 "${TOTAL_STAGES}" "sync"
run_sync

stage 2 "${TOTAL_STAGES}" "run"
if [[ "${RUN_REGIME_AUDIT}" == "1" ]]; then
    run_regime_audit
else
    echo "[daily] regime audit skipped"
fi
if [[ "${RUN_WALKFORWARD}" == "1" ]]; then
    run_walkforward
else
    echo "[daily] walkforward skipped"
fi

stage 3 "${TOTAL_STAGES}" "export"
run_export

stage 4 "${TOTAL_STAGES}" "cleanup"
run_cleanup

echo "[daily] complete profile=${PROFILE} cleanup=${CLEANUP_MODE}"
