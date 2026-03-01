# Grid ML System

Execution-first, code-first trading system around `GridBrainV1`, with deterministic planning, strict runtime contracts, and checkpoint-based validation (`C0`, `C1`, `C2+`).

## Current Project State

- Consolidated implementation plan: `docs/CONSOLIDATED_MASTER_PLAN.md`
- `C0` baseline frozen: `docs/C0_BASELINE_SNAPSHOT.md`
- `C1` checkpoint completed and GREEN: `docs/C1_CHECKPOINT_DELTA.md`
- `P0-7 (M402 reclaim baseline alignment)` completed
- Next primary gate: `P0-8 / C2` checkpoint

## Repository Map

- Strategy/runtime entrypoints:
  - `freqtrade/user_data/strategies/GridBrainV1.py`
  - `freqtrade/user_data/scripts/grid_executor_v1.py`
  - `freqtrade/user_data/scripts/grid_simulator_v1.py`
- Core modules:
  - `core/` (enums, schema validation, signatures, atomic writes)
  - `planner/` (replan policy, start stability, volatility policy, structure)
  - `risk/` (meta drift guard)
  - `execution/` (capacity guard)
  - `analytics/` (execution cost calibration)
  - `data/` (data quality assessor)
  - `sim/` (chaos profiles)
- Schemas:
  - `schemas/*.schema.json`
- Tests:
  - `freqtrade/user_data/tests/test_*.py`

## Canonical Docs (Read First)

1. `docs/CONSOLIDATED_MASTER_PLAN.md`
2. `docs/C0_BASELINE_SNAPSHOT.md`
3. `docs/C1_CHECKPOINT_DELTA.md`
4. `docs/C2_CHECKPOINT_DELTA.md`
5. `docs/C2_EXECUTION_CHECKLIST.md`
6. `docs/DOCKER_RUNTIME_WORKFLOW.md`
7. `docs/CODING_RULES.md`

## Environment (Canonical)

Use Docker as the single source of truth.

- Compose: `docker-compose.grid.yml`
- Wrapper: `scripts/docker_env.sh`

Container wiring:
- `./freqtrade -> /freqtrade`
- `./ -> /workspace`
- `PYTHONPATH=/workspace:/freqtrade`

This keeps root modules (`core/`, `planner/`, etc.) importable while preserving Freqtrade runtime paths.

## Daily Commands

```bash
# Build image
./scripts/docker_env.sh build

# Shell
./scripts/docker_env.sh shell

# Full tests
./scripts/docker_env.sh pytest -q freqtrade/user_data/tests

# Regression workflow
./scripts/docker_env.sh regression

# Backtest
./scripts/docker_env.sh backtest \
  --config /freqtrade/user_data/config.json \
  --strategy GridBrainV1 \
  --strategy-path /freqtrade/user_data/strategies \
  --timerange 20260209-20260210 \
  --timeframe 15m \
  --datadir /freqtrade/user_data/data/binance

# Walkforward
./scripts/docker_env.sh walkforward \
  --timerange 20260209-20260210 \
  --window-days 1 \
  --step-days 1 \
  --min-window-days 1 \
  --pair ETH/USDT
```

## Checkpoints and Baselines

Baseline/checkpoint artifacts are stored under:
- `freqtrade/user_data/baselines/<tag>/logs`
- `freqtrade/user_data/baselines/<tag>/metrics`

Pointer files:
- `freqtrade/user_data/baselines/.latest_c0_tag`
- `freqtrade/user_data/baselines/.latest_c1_tag`
- `freqtrade/user_data/baselines/.latest_c2_tag` (created after first successful C2)

Current known pointers:
- `c0_20260228T192027Z`
- `c1_20260228T225504Z`

## C2 (Next Gate)

One-command runner:

```bash
./scripts/run_c2_checkpoint.sh
```

Optional overrides:

```bash
CHECKPOINT_TAG=c2_YYYYMMDDTHHMMSSZ \
PAIR=ETH/USDT \
TIMEFRAME=15m \
TIMERANGE=20260209-20260210 \
RECENT_PLAN_SECONDS=3600 \
./scripts/run_c2_checkpoint.sh
```

C2 execution artifacts and decision flow:
- Checklist: `docs/C2_EXECUTION_CHECKLIST.md`
- Delta template: `docs/C2_CHECKPOINT_DELTA.md`
- Machine-readable manifest produced by runner: `freqtrade/user_data/baselines/<C2_TAG>/metrics/c2_snapshot.json`

## Quality Gates

Minimum bar before moving to next P0 feature batch:

1. `regression` passes
2. `backtest` completes and artifacts are frozen
3. `walkforward` completes and artifacts are frozen
4. direct behavior regression passes
5. checkpoint delta doc is updated from manifest data

## Development Rules (Operational)

- Code is source of truth; docs are intent unless backed by code/tests.
- Keep plan, code, and tests synchronized in the same change.
- Preserve deterministic behavior unless there is an explicit policy decision.
- Prefer canonical enums/events/reasons (`core/enums.py`) for observability.
- Do not leave dead code commented inline; use deletion or short-lived compatibility paths with clear checkpoint removal.

## Artifacts and Cross-Machine Continuity

If you want full continuity across machines/sessions, include runtime artifacts in commits/pushes (plans, logs, baseline metrics, latest refs), not only source files.

Useful references:
- `docs/NEXT_COMMIT_SCOPE.md`
- `docs/CHECKPOINT_POINTER_REPORT.md`

## Troubleshooting

- If regression fails on plan recency:
  - use `--recent-plan-seconds` in `user_regression_suite.py` path
  - or set `REGRESSION_RECENT_PLAN_SECONDS`
- If checkpoint runner fails but a stage succeeded:
  - inspect per-stage logs in `freqtrade/user_data/baselines/<TAG>/logs`
  - verify required copied artifacts exist in `metrics`
- If Docker path/import issues appear:
  - re-check `docker-compose.grid.yml` mounts and `PYTHONPATH`

## Local Fallback (Optional)

Use only when Docker is unavailable:

```bash
./scripts/setup_dev_env.sh
source .venv/bin/activate
.venv/bin/pytest -q freqtrade/user_data/tests
```

