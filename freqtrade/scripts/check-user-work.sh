#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

USAGE="Usage: scripts/check-user-work.sh [--no-lint] [--require-lint] [--] [file ...]"

run_lint="auto"
require_lint="0"
files=()

while (($# > 0)); do
    case "$1" in
        --no-lint)
            run_lint="off"
            shift
            ;;
        --require-lint)
            run_lint="on"
            require_lint="1"
            shift
            ;;
        --help|-h)
            echo "${USAGE}"
            exit 0
            ;;
        --)
            shift
            while (($# > 0)); do
                files+=("$1")
                shift
            done
            ;;
        *)
            files+=("$1")
            shift
            ;;
    esac
done

if ((${#files[@]} == 0)); then
    files=(
        "scripts/run-user-data-sync.py"
        "scripts/manage-user-artifacts.py"
        "scripts/run-user-regime-audit.py"
        "scripts/run-user-state-supervisor.py"
        "scripts/run-user-walkforward.py"
        "scripts/run-user-walkforward-supervisor.py"
        "scripts/watch-walkforward-progress.py"
        "user_data/scripts/grid_simulator_v1.py"
        "user_data/scripts/regime_audit_v1.py"
        "user_data/scripts/grid_executor_v1.py"
        "user_data/strategies/GridBrainV1.py"
    )
fi

for f in "${files[@]}"; do
    if [[ ! -f "${f}" ]]; then
        echo "[check] Missing file: ${f}" >&2
        exit 1
    fi
done

echo "[check] py_compile"
python3 -m py_compile "${files[@]}"
echo "[check] py_compile OK"

if [[ "${run_lint}" == "off" ]]; then
    echo "[check] lint skipped (--no-lint)"
    exit 0
fi

if command -v ruff >/dev/null 2>&1; then
    echo "[check] ruff check"
    ruff check "${files[@]}"
    echo "[check] ruff OK"
    exit 0
fi

if [[ "${require_lint}" == "1" ]]; then
    echo "[check] ruff not found and --require-lint was set" >&2
    exit 1
fi

echo "[check] ruff not found; lint skipped (optional)"
