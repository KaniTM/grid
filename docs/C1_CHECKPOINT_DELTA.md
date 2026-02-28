# C1 Checkpoint Delta vs C0 (2026-03-01)

## 1) Checkpoint Identity

- `C1 Tag`: `c1_20260228T225504Z`
- `C0 Baseline`: `c0_20260228T192027Z`
- `Scope`:
1. Pair: `ETH/USDT`
2. Timeframe: `15m`
3. Timerange: `20260209-20260210`
4. Runtime wrapper: `./scripts/docker_env.sh`

## 2) Commands Executed

1. `./scripts/docker_env.sh regression`
2. `./scripts/docker_env.sh backtest --config /freqtrade/user_data/config.json --strategy GridBrainV1 --strategy-path /freqtrade/user_data/strategies --timerange 20260209-20260210 --timeframe 15m --datadir /freqtrade/user_data/data/binance --export trades --export-filename /freqtrade/user_data/baselines/c1_20260228T225504Z/metrics/backtest.json`
3. `./scripts/docker_env.sh walkforward --timerange 20260209-20260210 --window-days 1 --step-days 1 --min-window-days 1 --pair ETH/USDT --run-id c1_20260228T225504Z_wf --fail-on-window-error`
4. `./scripts/docker_env.sh cmd "python /freqtrade/user_data/scripts/user_regression_suite.py --plan '/freqtrade/user_data/grid_plans/binance/ETH_USDT/grid_plan.latest.json' --state-out '/freqtrade/user_data/baselines/c1_20260228T225504Z/metrics/grid_executor_v1.regression.state.json' --recent-plan-seconds 3600"`

## 3) C1 Results

### Regression Wrapper

- `Status`: `OK`
- `Evidence`: `freqtrade/user_data/baselines/c1_20260228T225504Z/logs/regression.log`

### Backtest

- `Status`: `OK`
- `Trades`: `0`
- `Profit Total`: `0.0`
- `Profit Total Abs`: `0.0`
- `Profit Factor`: `0.0`
- `Max Drawdown`: `0.0`
- `Evidence`:
1. `freqtrade/user_data/baselines/c1_20260228T225504Z/logs/backtest.log`
2. `freqtrade/user_data/baselines/c1_20260228T225504Z/metrics/backtest.zip`
3. `freqtrade/user_data/baselines/c1_20260228T225504Z/metrics/backtest.meta.json`

### Walkforward

- `Status`: `OK`
- `Run ID`: `c1_20260228T225504Z_wf`
- `Windows`: `1 total`, `1 ok`, `0 failed`
- `Aggregate PnL`: `avg_pnl_pct=0.0`, `sum_pnl_quote=0.0`
- `Top Start Blocker`: `BLOCK_ADX_HIGH:96`
- `Top Stop Reason`: `os_dev_trend_stop:56`
- `Window-1`: `fills=0`, `stop_events=49`, `action_start=0`, `action_hold=47`, `action_stop=49`
- `Evidence`:
1. `freqtrade/user_data/baselines/c1_20260228T225504Z/logs/walkforward.log`
2. `freqtrade/user_data/baselines/c1_20260228T225504Z/metrics/walkforward.summary.json`
3. `freqtrade/user_data/baselines/c1_20260228T225504Z/metrics/walkforward.windows.csv`

### Direct Behavior Regression

- `Status`: `OK`
- `Evidence`: `freqtrade/user_data/baselines/c1_20260228T225504Z/logs/regression_behavior_direct.log`

## 4) Delta vs C0

### Status Delta

- `regression_wrapper`: `FAIL -> OK` (improved)
- `backtest`: `OK -> OK` (unchanged)
- `walkforward`: `OK -> OK` (unchanged)
- `regression_behavior_direct`: `FAIL -> OK` (improved)

### Metrics Delta

- Backtest deltas vs `C0`: `total_trades=0.0`, `profit_total=0.0`, `profit_total_abs=0.0`, `profit_factor=0.0`, `max_drawdown=null`.
- Walkforward aggregate deltas vs `C0`: `windows_total=0.0`, `windows_ok=0.0`, `windows_failed=0.0`, `sum_pnl_quote=0.0`, `avg_pnl_pct=0.0`, `win_rate=0.0`.
- Top blocker/stop reason unchanged vs `C0`:
1. `top_start_blocker`: `BLOCK_ADX_HIGH:96`
2. `top_stop_reason`: `os_dev_trend_stop:56`
- Window-1 deltas all `0.0`: `fills`, `stop_events`, `action_start`, `action_hold`, `action_stop`, `pnl_pct`, `pnl_quote`.

## 5) Focused Review (M306 + M402 Surface)

- Reviewed changed behavior surface (`user_regression_suite.py`, `run-user-regression.sh`, `GridBrainV1.py`, related tests).
- No new high-severity behavioral regression signal was observed in `C1` metrics relative to `C0`.
- Regression gates are now green under the canonical Docker workflow.

## 6) Acceptance Decision

- `C1` is **GREEN**.
- Reason: regression/backtest/walkforward/direct-regression all succeeded and delta report is frozen.
- `P0-6` acceptance is complete.

## 7) Canonical Manifest

- `freqtrade/user_data/baselines/c1_20260228T225504Z/metrics/c1_snapshot.json`
- `freqtrade/user_data/baselines/.latest_c1_tag`
