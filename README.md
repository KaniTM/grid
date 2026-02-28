# Grid ML System

## Canonical environment (Docker)

Use the repo-level Docker workflow as the single source of truth for tests/backtests/walkforward:

```bash
# build the env image
./scripts/docker_env.sh build

# open a shell in the container
./scripts/docker_env.sh shell

# run tests
./scripts/docker_env.sh pytest -q freqtrade/user_data/tests

# run regression workflow
./scripts/docker_env.sh regression
```

This flow uses `docker-compose.grid.yml` and mounts both:
- `/freqtrade` -> `./freqtrade`
- `/workspace` -> repo root (`.`)

So strategy modules in repo root (`core/`, `planner/`, `risk/`, `execution/`, etc.) are available together with Freqtrade runtime paths.

## Local fallback (optional)

If Docker is unavailable, use the local setup helper:

```bash
./scripts/setup_dev_env.sh
source .venv/bin/activate
.venv/bin/pytest -q freqtrade/user_data/tests
```
