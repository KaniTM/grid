#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FREQTRADE_ROOT="${REPO_ROOT}/freqtrade"
COMPOSE_FILE="${COMPOSE_FILE:-${GRID_COMPOSE_FILE:-${REPO_ROOT}/docker-compose.grid.yml}}"
COMPOSE_SERVICE="${COMPOSE_SERVICE:-freqtrade}"
cd "${FREQTRADE_ROOT}"

if [[ ! -f "${COMPOSE_FILE}" ]]; then
  echo "[regression] compose file not found: ${COMPOSE_FILE}" >&2
  exit 1
fi

export GRID_UID="${GRID_UID:-$(id -u)}"
export GRID_GID="${GRID_GID:-$(id -g)}"

compose_cmd=(docker compose -f "${COMPOSE_FILE}")

# Defaults for current project workflow.
PAIR="${PAIR:-ETH/USDT}"
PAIR_FS="${PAIR//\//_}"
EXCHANGE="${EXCHANGE:-binance}"
TIMEFRAME="${TIMEFRAME:-15m}"
TIMERANGE="${TIMERANGE:-20260209-20260210}"
CONFIG_PATH="${CONFIG_PATH:-/freqtrade/user_data/config.json}"
STRATEGY="${STRATEGY:-GridBrainV1}"
STRATEGY_PATH="${STRATEGY_PATH:-/freqtrade/user_data/strategies}"
DATA_DIR="${DATA_DIR:-/freqtrade/user_data/data/binance}"
PLAN_PATH="${PLAN_PATH:-/freqtrade/user_data/grid_plans/${EXCHANGE}/${PAIR_FS}/grid_plan.latest.json}"
CHECK_USER_WORK_FLAGS="${CHECK_USER_WORK_FLAGS:---no-lint}"
RECENT_PLAN_SECONDS="${REGRESSION_RECENT_PLAN_SECONDS:-3600}"

echo "[regression] 1/3 compile gate"
"${compose_cmd[@]}" run --rm --entrypoint bash "${COMPOSE_SERVICE}" -lc \
  "cd /freqtrade && scripts/check-user-work.sh ${CHECK_USER_WORK_FLAGS}"

echo "[regression] 2/3 run brain via backtesting (plan generation path)"
"${compose_cmd[@]}" run --rm --entrypoint bash "${COMPOSE_SERVICE}" -lc \
  "freqtrade backtesting --config '${CONFIG_PATH}' --strategy '${STRATEGY}' --strategy-path '${STRATEGY_PATH}' --timerange '${TIMERANGE}' --timeframe '${TIMEFRAME}' --datadir '${DATA_DIR}'"

echo "[regression] 3/3 run behavior assertions (brain+executor+simulator)"
"${compose_cmd[@]}" run --rm --entrypoint bash "${COMPOSE_SERVICE}" -lc \
  "python /freqtrade/user_data/scripts/user_regression_suite.py --plan '${PLAN_PATH}' --recent-plan-seconds '${RECENT_PLAN_SECONDS}'"

if [[ "${RUN_WALKFORWARD:-0}" == "1" ]]; then
  echo "[regression] 4/4 walk-forward smoke"
  WF_TIMERANGE="${WALKFORWARD_TIMERANGE:-20260207-20260210}"
  WF_WINDOW_DAYS="${WALKFORWARD_WINDOW_DAYS:-2}"
  WF_STEP_DAYS="${WALKFORWARD_STEP_DAYS:-${WF_WINDOW_DAYS}}"
  python3 scripts/run-user-walkforward.py \
    --compose-file "${COMPOSE_FILE}" \
    --project-dir "${REPO_ROOT}" \
    --timerange "${WF_TIMERANGE}" \
    --window-days "${WF_WINDOW_DAYS}" \
    --step-days "${WF_STEP_DAYS}" \
    --min-window-days 2 \
    --pair "${PAIR}" \
    --exchange "${EXCHANGE}" \
    --timeframe "${TIMEFRAME}" \
    --config-path "${CONFIG_PATH}" \
    --strategy "${STRATEGY}" \
    --strategy-path "${STRATEGY_PATH}" \
    --data-dir "${DATA_DIR}" \
    --fee-pct 0.10 \
    --fail-on-window-error
fi

echo "[regression] complete"
