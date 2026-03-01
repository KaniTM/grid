# C2 Execution + Post-Run Checklist

## 1) Preflight (Quick)

1. Confirm script exists and is executable:
- `test -x scripts/run_c2_checkpoint.sh`

2. Confirm baseline pointers are present:
- `cat freqtrade/user_data/baselines/.latest_c0_tag`
- `cat freqtrade/user_data/baselines/.latest_c1_tag`

3. Optional: confirm working tree state before run:
- `git status --short`

## 2) Execute C2 (One Command)

Default run:
- `./scripts/run_c2_checkpoint.sh`

Optional overrides:
- `CHECKPOINT_TAG=c2_YYYYMMDDTHHMMSSZ PAIR=ETH/USDT TIMEFRAME=15m TIMERANGE=20260209-20260210 RECENT_PLAN_SECONDS=3600 ./scripts/run_c2_checkpoint.sh`

## 3) Immediate Success Gate

Runner output must show:
- `C2_REGRESSION=0`
- `C2_BACKTEST=0`
- `C2_WALKFORWARD=0`
- `C2_DIRECT_REGRESSION=0`
- `C2_PIPELINE=SUCCESS`

## 4) Artifact Presence Checks

1. Get tag:
- `cat freqtrade/user_data/baselines/.latest_c2_tag`

2. Verify required files exist:
- `freqtrade/user_data/baselines/<C2_TAG>/logs/regression.log`
- `freqtrade/user_data/baselines/<C2_TAG>/logs/backtest.log`
- `freqtrade/user_data/baselines/<C2_TAG>/logs/walkforward.log`
- `freqtrade/user_data/baselines/<C2_TAG>/logs/regression_behavior_direct.log`
- `freqtrade/user_data/baselines/<C2_TAG>/metrics/backtest.zip`
- `freqtrade/user_data/baselines/<C2_TAG>/metrics/backtest.meta.json`
- `freqtrade/user_data/baselines/<C2_TAG>/metrics/walkforward.summary.json`
- `freqtrade/user_data/baselines/<C2_TAG>/metrics/walkforward.windows.csv`
- `freqtrade/user_data/baselines/<C2_TAG>/metrics/c2_snapshot.json`

## 5) Documentation Update

1. Fill:
- `docs/C2_CHECKPOINT_DELTA.md`

2. Source of truth for numbers/deltas:
- `freqtrade/user_data/baselines/<C2_TAG>/metrics/c2_snapshot.json`

3. Plan gate transition:
- If C2 is GREEN -> move to `P0-9` (`M903` + `M904`).
- If C2 is NOT_GREEN -> keep `P0-8` open, log blocker and fix plan.

## 6) Optional Sanity Commands

- `python3 -m json.tool freqtrade/user_data/baselines/<C2_TAG>/metrics/c2_snapshot.json >/dev/null`
- `rg -n "OVERALL|GREEN|NOT_GREEN" docs/C2_CHECKPOINT_DELTA.md`
