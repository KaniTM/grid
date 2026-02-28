#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FREQTRADE_ROOT="${REPO_ROOT}/freqtrade"
COMPOSE_FILE="${COMPOSE_FILE:-${GRID_COMPOSE_FILE:-${REPO_ROOT}/docker-compose.grid.yml}}"
COMPOSE_SERVICE="${COMPOSE_SERVICE:-freqtrade}"

if [[ ! -f "${COMPOSE_FILE}" ]]; then
  echo "[docker-env] compose file not found: ${COMPOSE_FILE}" >&2
  exit 1
fi

export GRID_UID="${GRID_UID:-$(id -u)}"
export GRID_GID="${GRID_GID:-$(id -g)}"

compose_cmd=(docker compose -f "${COMPOSE_FILE}")

usage() {
  cat <<'EOF'
Usage: scripts/docker_env.sh <command> [args...]

Commands:
  build                      Build the canonical freqtrade env image.
  shell                      Open an interactive shell inside the env container.
  cmd "<bash command>"       Run a custom bash command inside the env container.
  pytest [pytest args]       Run pytest from /workspace.
  backtest [freqtrade args]  Run freqtrade backtesting inside container.
  regression                 Run user regression workflow (dockerized path).
  walkforward [args]         Run walkforward orchestrator (host python, dockerized inner jobs).
  sync [args]                Run data-sync orchestrator (host python, dockerized inner jobs).
  regime [args]              Run regime-audit orchestrator (host python, dockerized inner jobs).

Env overrides:
  COMPOSE_FILE=/abs/path/to/docker-compose.grid.yml
  COMPOSE_SERVICE=freqtrade
EOF
}

run_in_container() {
  local cmd_text="${1:-}"
  "${compose_cmd[@]}" run --rm --entrypoint bash "${COMPOSE_SERVICE}" -lc "${cmd_text}"
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

subcmd="$1"
shift || true

case "${subcmd}" in
  build)
    "${compose_cmd[@]}" build "${COMPOSE_SERVICE}"
    ;;
  shell)
    "${compose_cmd[@]}" run --rm --entrypoint bash "${COMPOSE_SERVICE}"
    ;;
  cmd)
    if [[ $# -lt 1 ]]; then
      echo "[docker-env] cmd requires a command string" >&2
      exit 1
    fi
    run_in_container "$*"
    ;;
  pytest)
    run_in_container "cd /workspace && python3 -m pytest $*"
    ;;
  backtest)
    run_in_container "cd /freqtrade && freqtrade backtesting $*"
    ;;
  regression)
    (
      cd "${FREQTRADE_ROOT}"
      COMPOSE_FILE="${COMPOSE_FILE}" COMPOSE_SERVICE="${COMPOSE_SERVICE}" ./scripts/run-user-regression.sh "$@"
    )
    ;;
  walkforward)
    (
      cd "${FREQTRADE_ROOT}"
      python3 scripts/run-user-walkforward.py \
        --compose-file "${COMPOSE_FILE}" \
        --project-dir "${REPO_ROOT}" \
        "$@"
    )
    ;;
  sync)
    (
      cd "${FREQTRADE_ROOT}"
      python3 scripts/run-user-data-sync.py \
        --compose-file "${COMPOSE_FILE}" \
        --project-dir "${REPO_ROOT}" \
        "$@"
    )
    ;;
  regime)
    (
      cd "${FREQTRADE_ROOT}"
      python3 scripts/run-user-regime-audit.py \
        --compose-file "${COMPOSE_FILE}" \
        --project-dir "${REPO_ROOT}" \
        "$@"
    )
    ;;
  *)
    echo "[docker-env] unknown command: ${subcmd}" >&2
    usage
    exit 1
    ;;
esac
