#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

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

echo "[regression] 1/3 compile gate"
scripts/check-user-work.sh

echo "[regression] 2/3 run brain via backtesting (plan generation path)"
docker compose run --rm --entrypoint bash freqtrade -lc \
  "freqtrade backtesting --config '${CONFIG_PATH}' --strategy '${STRATEGY}' --strategy-path '${STRATEGY_PATH}' --timerange '${TIMERANGE}' --timeframe '${TIMEFRAME}' --datadir '${DATA_DIR}'"

echo "[regression] 3/3 run behavior assertions (brain+executor+simulator)"
docker compose run --rm --entrypoint bash freqtrade -lc \
  "python /freqtrade/user_data/scripts/user_regression_suite.py --plan '${PLAN_PATH}'"

if [[ "${RUN_WALKFORWARD:-0}" == "1" ]]; then
  echo "[regression] 4/4 walk-forward smoke"
  WF_TIMERANGE="${WALKFORWARD_TIMERANGE:-20260207-20260210}"
  WF_WINDOW_DAYS="${WALKFORWARD_WINDOW_DAYS:-2}"
  WF_STEP_DAYS="${WALKFORWARD_STEP_DAYS:-${WF_WINDOW_DAYS}}"
  python3 scripts/run-user-walkforward.py \
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
