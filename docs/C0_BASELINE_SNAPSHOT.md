# C0 Baseline Snapshot (2026-02-28)

## 1) Snapshot Identity

- `C0 Tag`: `c0_20260228T192027Z`
- `Generated UTC`: `2026-02-28T19:40:05.524890+00:00` (from manifest)
- `Scope`:
1. Pair: `ETH/USDT`
2. Timeframe: `15m`
3. Timerange: `20260209-20260210`
4. Runtime wrapper: `./scripts/docker_env.sh`

## 2) Commands Executed

1. `./scripts/docker_env.sh regression`
2. `./scripts/docker_env.sh backtest --config /freqtrade/user_data/config.json --strategy GridBrainV1 --strategy-path /freqtrade/user_data/strategies --timerange 20260209-20260210 --timeframe 15m --datadir /freqtrade/user_data/data/binance --export trades --export-filename /freqtrade/user_data/baselines/c0_20260228T192027Z/metrics/backtest.json`
3. `./scripts/docker_env.sh walkforward --timerange 20260209-20260210 --window-days 1 --step-days 1 --min-window-days 1 --pair ETH/USDT --run-id c0_20260228T192027Z_wf --fail-on-window-error`
4. `./scripts/docker_env.sh cmd "python /freqtrade/user_data/scripts/user_regression_suite.py --plan '/freqtrade/user_data/grid_plans/binance/ETH_USDT/grid_plan.latest.json' --state-out '/freqtrade/user_data/baselines/c0_20260228T192027Z/metrics/grid_executor_v1.regression.state.json'"`

## 3) Frozen Results

### Regression Wrapper (`./scripts/docker_env.sh regression`)

- `Status`: `FAIL`
- `Failure`: compile/lint gate in `check-user-work.sh`
- `Signal`: `Found 970 errors.`
- `Evidence`: `freqtrade/user_data/baselines/c0_20260228T192027Z/logs/regression.log`

### Backtest

- `Status`: `OK`
- `Trades`: `0`
- `Profit Total`: `0.0`
- `Profit Total Abs`: `0`
- `Profit Factor`: `0.0`
- `Max Drawdown`: `null`
- `Evidence`:
1. `freqtrade/user_data/baselines/c0_20260228T192027Z/logs/backtest.log`
2. `freqtrade/user_data/baselines/c0_20260228T192027Z/metrics/backtest.zip`
3. `freqtrade/user_data/baselines/c0_20260228T192027Z/metrics/backtest.meta.json`

### Walkforward

- `Status`: `OK`
- `Run ID`: `c0_20260228T192027Z_wf`
- `Windows`: `1 total`, `1 ok`, `0 failed`
- `Aggregate PnL`: `avg_pnl_pct=0.0`, `sum_pnl_quote=0.0`
- `Top Start Blocker`: `BLOCK_ADX_HIGH:96`
- `Top Stop Reason`: `os_dev_trend_stop:56`
- `Window-1`: `fills=0`, `stop_events=49`, `action_start=0`, `action_hold=47`, `action_stop=49`
- `Evidence`:
1. `freqtrade/user_data/baselines/c0_20260228T192027Z/logs/walkforward.log`
2. `freqtrade/user_data/walkforward/c0_20260228T192027Z_wf/summary.json`
3. `freqtrade/user_data/walkforward/c0_20260228T192027Z_wf/windows.csv`

### Direct Behavior Regression (`user_regression_suite.py`)

- `Status`: `FAIL`
- `Failure`: `AssertionError: no recent plan snapshots found in plan directory`
- `Evidence`: `freqtrade/user_data/baselines/c0_20260228T192027Z/logs/regression_behavior_direct.log`

## 4) Canonical Manifest

- `freqtrade/user_data/baselines/c0_20260228T192027Z/metrics/c0_snapshot.json`
- `freqtrade/user_data/baselines/.latest_c0_tag`

The manifest above is the machine-readable source for this baseline freeze.

## 5) Interpretation For Next Checkpoints

1. `C0` is frozen and usable for future `C1+` delta comparisons.
2. Baseline includes known red gates:
- regression compile/lint gate failure (`970` findings)
- direct behavior regression recency assertion failure
3. These failures are now part of the baseline truth and should be explicitly tracked in fix queue before/alongside behavior-expansion work.
