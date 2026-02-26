#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but not found in PATH."
  exit 1
fi

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source ".venv/bin/activate"

ACTIVATE_FILE=".venv/bin/activate"
if ! grep -q "GRID_ML_SYSTEM_PYTEST_ENV" "$ACTIVATE_FILE"; then
  cat >>"$ACTIVATE_FILE" <<'EOF'
# GRID_ML_SYSTEM_PYTEST_ENV
if [ -n "${VIRTUAL_ENV:-}" ]; then
  export TMPDIR="$VIRTUAL_ENV/tmp"
  export TMP="$TMPDIR"
  export TEMP="$TMPDIR"
  mkdir -p "$TMPDIR"
  case " ${PYTEST_ADDOPTS-} " in
    *" --capture=sys "*) ;;
    *) export PYTEST_ADDOPTS="${PYTEST_ADDOPTS:+$PYTEST_ADDOPTS }--capture=sys" ;;
  esac
fi
# END GRID_ML_SYSTEM_PYTEST_ENV
EOF
fi

pip install --upgrade pip
pip install -r freqtrade/requirements.txt
pip install -r freqtrade/requirements-plot.txt
pip install -r freqtrade/requirements-hyperopt.txt
pip install -r freqtrade/requirements-freqai.txt
pip install -r freqtrade/requirements-freqai-rl.txt

pip install \
  pytest==9.0.2 \
  pytest-asyncio==1.3.0 \
  pytest-cov==7.0.0 \
  pytest-mock==3.15.1 \
  pytest-random-order==1.2.0 \
  pytest-timeout==2.4.0 \
  pytest-xdist==3.8.0 \
  ruff==0.14.14 \
  mypy==1.19.1 \
  pre-commit==4.5.1 \
  isort==7.0.0 \
  time-machine==3.2.0 \
  nbconvert==7.17.0

pip install -e freqtrade

echo "Dev environment ready. Activate it with: source .venv/bin/activate"
