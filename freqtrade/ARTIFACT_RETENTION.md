# Artifact Retention Policy

This repo creates many artifacts during sync, regime audit, and walkforward runs.  
Use this policy to keep only what is needed for continuity across machines.

## Keep (Portable + Important)

- `user_data/latest_refs/*.json`  
  Stable pointers to latest data-sync, regime-audit, walkforward, AB compare, and tuning shortlist.
- `user_data/portable_results/latest/**`  
  Compact handoff bundle (summaries, windows CSV, latest compare, latest overrides).
- `user_data/walkforward/*/summary.json`
- `user_data/walkforward/*/windows.csv`
- `user_data/walkforward/*AB_compare*.json`
- `user_data/regime_audit/*/report.json`
- `user_data/regime_audit/*/mode_threshold_overrides.json`
- `user_data/data/binance/*.feather` (or your selected format)  
  Historical market data needed for reproducible backtests and future tuning.

## Usually Safe To Delete

- Walkforward raw replay files:
  - `window_*.result.json`
  - `window_*.result.events.csv`
  - `window_*.result.fills.csv`
  - `window_*.result.curve.csv`
  - `window_*_plans/`
- Regime verbose/debug files:
  - `features.csv`
  - `per_candle_verbose.csv`
  - `transition_events.csv`
  - `transition_events.json`
- Backtest result archives in `user_data/backtest_results` except `.last_result.json`
- Grid plan archives `grid_plan.*.json` except `grid_plan.latest.json`

## When Raw Walkforward Files Are Still Needed

Raw window files are only needed when summaries are missing end balances for one or more successful windows.

Use:

```bash
python3 scripts/manage-user-artifacts.py --user-data user_data --json
```

Check:

- `walkforward_blocked_runs`: raw files should be kept for these runs.
- `walkforward_raw_prunable_runs`: raw files can be removed for these runs.

## Recommended Cleanup Command

Dry-run first:

```bash
python3 scripts/manage-user-artifacts.py --user-data user_data --json
```

Apply cleanup:

```bash
python3 scripts/manage-user-artifacts.py \
  --user-data user_data \
  --apply \
  --keep-walkforward-runs 6 \
  --keep-regime-runs 6
```

`manage-user-artifacts.py` auto-pins latest refs so current important runs are protected.
