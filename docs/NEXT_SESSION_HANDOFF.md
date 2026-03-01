# Next Session Handoff

## Current Status

- Consolidated plan is active and synced with current direction.
- `C1` is GREEN and frozen.
- `P0-7` is complete.
- Next gate is `P0-8` (`C2` checkpoint after `M402`).

## First Command To Run

```bash
./scripts/run_c2_checkpoint.sh
```

## Expected Success Signals

Runner output must include:
- `C2_REGRESSION=0`
- `C2_BACKTEST=0`
- `C2_WALKFORWARD=0`
- `C2_DIRECT_REGRESSION=0`
- `C2_PIPELINE=SUCCESS`

## Required Artifacts After Run

- `freqtrade/user_data/baselines/.latest_c2_tag`
- `freqtrade/user_data/baselines/<C2_TAG>/metrics/c2_snapshot.json`
- `freqtrade/user_data/baselines/<C2_TAG>/metrics/backtest.zip`
- `freqtrade/user_data/baselines/<C2_TAG>/metrics/walkforward.summary.json`
- `freqtrade/user_data/baselines/<C2_TAG>/logs/regression.log`

## Doc Update Flow

1. Fill `docs/C2_CHECKPOINT_DELTA.md` from `c2_snapshot.json`.
2. Update `docs/CONSOLIDATED_MASTER_PLAN.md` (`P0-8` status + next step).
3. If `C2` is GREEN, open `P0-9` (`M903` + `M904`) implementation batch.

## Go / No-Go Rule

- GO: all four C2 gates pass and artifacts are frozen.
- NO-GO: any C2 gate fails; keep `P0-8` open and queue fix tasks first.

