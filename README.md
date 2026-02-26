# Grid ML System

## Development environment

This repo relies on `pytest-xdist` (the `--dist` flag is part of the default pytest config), but the system Python is externally managed, so dependencies cannot be installed globally. To keep every machine working the same way, run:

```bash
./scripts/setup_dev_env.sh
```

That script creates (or reuses) `.venv`, upgrades `pip`, installs the `freqtrade` requirements, and adds `pytest-xdist`. Once it completes, activate the environment and run tests via the bundled tools:

```bash
source .venv/bin/activate
.venv/bin/pytest -q freqtrade/user_data/tests/test_phase3_validation.py
```

You can use the same `.venv` for other commands; just activate it first.

## Running tests

After activating the venv above, continue to run pytest through `.venv/bin/pytest` so the `--dist` flag works without capture errors. This ensures `pytest-xdist` is always available even on new machines.
