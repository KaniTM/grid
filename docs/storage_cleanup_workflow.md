# Storage Cleanup + Incremental Run Workflow

## Goal
Keep this repo portable across PCs without deleting artifacts that are needed to continue work.

## One Command Daily Workflow

Research run (sync + regime + walkforward resume + export + cleanup):

```bash
cd freqtrade
bash scripts/run-user-daily-workflow.sh --profile research --cleanup conservative
```

Light run (sync + export + cleanup only):

```bash
cd freqtrade
bash scripts/run-user-daily-workflow.sh --profile light --cleanup conservative
```

## Keep vs Delete

Keep:
- `freqtrade/user_data/data/**` (OHLCV history; prevents full re-download)
- `freqtrade/user_data/walkforward/*/summary.json`
- `freqtrade/user_data/walkforward/*/windows.csv`
- `freqtrade/user_data/walkforward/*AB_compare*.json`
- `freqtrade/user_data/regime_audit/*/report.json`
- `freqtrade/user_data/regime_audit/*/mode_threshold_overrides.json`
- `freqtrade/user_data/portable_results/latest/**` (cross-PC handoff payload)

Safe to prune regularly:
- `freqtrade/user_data/backtest_results/*` except `.last_result.json`
- `freqtrade/user_data/walkforward/*/window_*.result*`
- `freqtrade/user_data/walkforward/*/window_*_plans/`
- `freqtrade/user_data/grid_plans/**/grid_plan.*.json` except `grid_plan.latest.json`
- `freqtrade/user_data/regime_audit/*/features.csv`
- `freqtrade/user_data/regime_audit/*/per_candle_verbose.csv`
- `freqtrade/user_data/regime_audit/*/transition_events.csv`
- `freqtrade/user_data/regime_audit/*/transition_events.json`
- `**/__pycache__/`, `*.pyc`

## One-command dry-run cleanup audit

```bash
cd freqtrade
python3 scripts/manage-user-artifacts.py --user-data user_data --list-limit 40
```

## Apply cleanup (conservative, keeps regime feature dumps)

```bash
cd freqtrade
python3 scripts/manage-user-artifacts.py \
  --user-data user_data \
  --no-prune-regime-verbose \
  --apply
```

Notes:
- The cleanup tool protects walkforward runs that cannot safely drop raw files yet.
- It can hydrate missing `end_quote` / `end_base` into summaries when possible.

## Apply cleanup (full, removes regime verbose dumps too)

```bash
cd freqtrade
python3 scripts/manage-user-artifacts.py --user-data user_data --apply
```

## Optional retention pruning

Keep only latest 12 walkforward runs and latest 4 regime runs:

```bash
cd freqtrade
python3 scripts/manage-user-artifacts.py \
  --user-data user_data \
  --keep-walkforward-runs 12 \
  --keep-regime-runs 4 \
  --apply
```

## Incremental OHLCV sync (no full re-download)

Append new candles only:

```bash
cd freqtrade
python3 scripts/run-user-data-sync.py \
  --pairs ETH/USDT \
  --timeframes 15m 1h 4h \
  --mode append \
  --heartbeat-sec 30
```

Backfill older history only:

```bash
cd freqtrade
python3 scripts/run-user-data-sync.py \
  --pairs ETH/USDT \
  --timeframes 15m 1h 4h \
  --mode prepend \
  --start-day 20200101 \
  --heartbeat-sec 30
```

## Resume-friendly long runs

Walkforward:

```bash
cd freqtrade
python3 scripts/run-user-walkforward.py ... \
  --resume \
  --heartbeat-sec 60
```

Regime audit:

```bash
cd freqtrade
python3 scripts/run-user-regime-audit.py ... \
  --heartbeat-sec 60
```
