# Docker Runtime Workflow

## Goal

Provide one permanent environment path for:
- tests
- regression checks
- backtests
- walkforward
- data sync
- regime audit

## Canonical files

- Compose file: `docker-compose.grid.yml`
- Wrapper: `scripts/docker_env.sh`

## Container wiring

- Service: `freqtrade`
- Build context: `./freqtrade` (`freqtrade/docker/Dockerfile.custom`)
- Mounts:
  - `./freqtrade -> /freqtrade`
  - `./ -> /workspace`
- Runtime env:
  - `PYTHONPATH=/workspace:/freqtrade`

This ensures top-level strategy modules (`core/`, `planner/`, etc.) are importable while preserving existing `/freqtrade/user_data/...` paths.

## Daily commands

```bash
# Build/update image
./scripts/docker_env.sh build

# Interactive shell
./scripts/docker_env.sh shell

# Run tests
./scripts/docker_env.sh pytest -q freqtrade/user_data/tests

# Backtesting
./scripts/docker_env.sh backtest --config /freqtrade/user_data/config.json --strategy GridBrainV1 --strategy-path /freqtrade/user_data/strategies --timerange 20260101-20260201 --timeframe 15m --datadir /freqtrade/user_data/data/binance

# Regression suite
./scripts/docker_env.sh regression

# Walkforward orchestrator
./scripts/docker_env.sh walkforward --timerange 20260101-20260201 --window-days 14 --step-days 14 --pair ETH/USDT

# Data sync orchestrator
./scripts/docker_env.sh sync --pairs ETH/USDT --timeframes 15m 1h 4h --mode append

# Regime audit orchestrator
./scripts/docker_env.sh regime --pair ETH/USDT --timeframe 15m --timerange 20250101-20260201
```

Walkforward notes:
- By default it auto-detects strategy startup lookbacks and prepends warmup candles for backtesting.
- Override with `--backtest-warmup-candles <N>` (`0` disables, `-1` keeps auto mode).

## Compose override knobs

- `COMPOSE_FILE` or `GRID_COMPOSE_FILE` to override compose path.
- `COMPOSE_SERVICE` to override service name.
- `GRID_UID` / `GRID_GID` to control container write ownership.

## Script defaults updated

The following scripts now default to the repo-level compose file:
- `freqtrade/scripts/run-user-walkforward.py`
- `freqtrade/scripts/run-user-data-sync.py`
- `freqtrade/scripts/run-user-regime-audit.py`
- `freqtrade/scripts/run-user-regression.sh`

Each supports overriding compose path/project directory when needed.
