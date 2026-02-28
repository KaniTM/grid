# C2 Checkpoint Delta vs C0 (Template)

## 1) Checkpoint Identity

- `C2 Tag`: `<fill-after-run>`
- `C0 Baseline`: `<from freqtrade/user_data/baselines/.latest_c0_tag>`
- `Scope`:
1. Pair: `ETH/USDT` (or overridden `PAIR`)
2. Timeframe: `15m` (or overridden `TIMEFRAME`)
3. Timerange: `20260209-20260210` (or overridden `TIMERANGE`)
4. Runtime wrapper: `./scripts/docker_env.sh`
5. Runner: `./scripts/run_c2_checkpoint.sh`

## 2) Commands Executed

Primary command:
1. `./scripts/run_c2_checkpoint.sh`

Equivalent internal stages:
1. `./scripts/docker_env.sh regression`
2. `./scripts/docker_env.sh backtest --config /freqtrade/user_data/config.json --strategy GridBrainV1 --strategy-path /freqtrade/user_data/strategies --timerange <TIMERANGE> --timeframe <TIMEFRAME> --datadir /freqtrade/user_data/data/binance --export trades --export-filename /freqtrade/user_data/baselines/<C2_TAG>/metrics/backtest.json`
3. `./scripts/docker_env.sh walkforward --timerange <TIMERANGE> --window-days 1 --step-days 1 --min-window-days 1 --pair <PAIR> --run-id <C2_TAG>_wf --fail-on-window-error`
4. `./scripts/docker_env.sh cmd "python /freqtrade/user_data/scripts/user_regression_suite.py --plan '/freqtrade/user_data/grid_plans/binance/<PAIR_FS>/grid_plan.latest.json' --state-out '/freqtrade/user_data/baselines/<C2_TAG>/metrics/grid_executor_v1.regression.state.json' --recent-plan-seconds 3600"`

## 3) C2 Results

### Regression Wrapper

- `Status`: `<OK|FAIL>`
- `Evidence`: `freqtrade/user_data/baselines/<C2_TAG>/logs/regression.log`

### Backtest

- `Status`: `<OK|FAIL>`
- `Evidence`:
1. `freqtrade/user_data/baselines/<C2_TAG>/logs/backtest.log`
2. `freqtrade/user_data/baselines/<C2_TAG>/metrics/backtest.zip`
3. `freqtrade/user_data/baselines/<C2_TAG>/metrics/backtest.meta.json`

### Walkforward

- `Status`: `<OK|FAIL>`
- `Evidence`:
1. `freqtrade/user_data/baselines/<C2_TAG>/logs/walkforward.log`
2. `freqtrade/user_data/baselines/<C2_TAG>/metrics/walkforward.summary.json`
3. `freqtrade/user_data/baselines/<C2_TAG>/metrics/walkforward.windows.csv`

### Direct Behavior Regression

- `Status`: `<OK|FAIL>`
- `Evidence`: `freqtrade/user_data/baselines/<C2_TAG>/logs/regression_behavior_direct.log`

## 4) Delta vs C0

Machine-readable source:
- `freqtrade/user_data/baselines/<C2_TAG>/metrics/c2_snapshot.json`

Summarize:
1. status deltas
2. backtest metric deltas
3. walkforward aggregate and window deltas
4. top blocker/stop reason changes

## 5) Focused Review (M402 Surface)

- Confirm reclaim baseline policy (`8h`) remains stable under checkpoint load.
- Confirm no new high-severity behavior/security regressions.
- Confirm docs/code/tests remain synchronized for `M402`.

## 6) Acceptance Decision

- `C2` is `<GREEN|NOT_GREEN>`.
- Reason: `<brief decision rationale>`
- If green: move to `P0-9` (`M903` + `M904`).

## 7) Canonical Manifest

- `freqtrade/user_data/baselines/<C2_TAG>/metrics/c2_snapshot.json`
- `freqtrade/user_data/baselines/.latest_c2_tag` (written only when all four gates pass)
