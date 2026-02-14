#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
WORKFLOW_DIR="${REPO_ROOT}/.codex-workflow"
PIN_ID_FILE="${WORKFLOW_DIR}/pinned-thread-id"
PIN_ARCHIVE="${WORKFLOW_DIR}/pinned-session.jsonl.gz"

mkdir -p "${WORKFLOW_DIR}"

die() {
    echo "Error: $*" >&2
    exit 1
}

find_session_by_id() {
    local thread_id="$1"
    local found=""

    found="$(find "${HOME}/.codex/sessions" -type f -name '*.jsonl' 2>/dev/null | grep "${thread_id}" | head -n1 || true)"
    if [[ -z "${found}" ]]; then
        found="$(rg -l "\"id\":\"${thread_id}\"" "${HOME}/.codex/sessions" -g '*.jsonl' 2>/dev/null | head -n1 || true)"
    fi
    [[ -n "${found}" ]] && printf '%s\n' "${found}"
}

read_pinned_id() {
    [[ -f "${PIN_ID_FILE}" ]] || die "No pinned thread ID. Run: scripts/codex_thread.sh pin <thread-id>"
    local thread_id
    thread_id="$(tr -d '[:space:]' < "${PIN_ID_FILE}")"
    [[ -n "${thread_id}" ]] || die "Pinned thread ID file is empty: ${PIN_ID_FILE}"
    printf '%s\n' "${thread_id}"
}

detect_codex_bin() {
    if command -v codex >/dev/null 2>&1; then
        command -v codex
        return 0
    fi

    local candidate=""
    candidate="$(ls -d /mnt/c/Users/*/.vscode/extensions/openai.chatgpt-*/bin/linux-x86_64 2>/dev/null | sort -V | tail -n1 || true)"
    if [[ -n "${candidate}" && -x "${candidate}/codex" ]]; then
        printf '%s\n' "${candidate}/codex"
        return 0
    fi

    die "Could not find codex binary. Install/open the Codex VS Code extension first."
}

first_line_timestamp() {
    local file="$1"
    local ts=""
    if command -v jq >/dev/null 2>&1; then
        ts="$(head -n1 "${file}" | jq -r '(.payload.timestamp // .timestamp // empty)' 2>/dev/null || true)"
    fi
    if [[ -z "${ts}" ]]; then
        ts="$(date -u +%Y-%m-%dT%H-%M-%S)"
    fi
    printf '%s\n' "${ts}"
}

import_pinned_session_if_missing() {
    local thread_id="$1"
    local existing=""
    existing="$(find_session_by_id "${thread_id}" || true)"
    if [[ -n "${existing}" ]]; then
        touch "${existing}"
        printf '%s\n' "${existing}"
        return 0
    fi

    [[ -f "${PIN_ARCHIVE}" ]] || die "Pinned session archive not found: ${PIN_ARCHIVE}. Run pin on source machine first."

    local tmp_file
    tmp_file="$(mktemp)"
    gunzip -c "${PIN_ARCHIVE}" > "${tmp_file}"

    local ts ts_sanitized y m d dst_dir dst_file
    ts="$(first_line_timestamp "${tmp_file}")"
    ts_sanitized="$(printf '%s' "${ts}" | sed 's/:/-/g')"

    y="$(date -u -d "${ts}" +%Y 2>/dev/null || date -u +%Y)"
    m="$(date -u -d "${ts}" +%m 2>/dev/null || date -u +%m)"
    d="$(date -u -d "${ts}" +%d 2>/dev/null || date -u +%d)"

    dst_dir="${HOME}/.codex/sessions/${y}/${m}/${d}"
    mkdir -p "${dst_dir}"
    dst_file="${dst_dir}/rollout-${ts_sanitized}-${thread_id}.jsonl"
    cp "${tmp_file}" "${dst_file}"
    rm -f "${tmp_file}"
    touch "${dst_file}"
    printf '%s\n' "${dst_file}"
}

cmd_pin() {
    local thread_id="${1:-}"
    local source_file="${2:-}"
    [[ -n "${thread_id}" ]] || die "Usage: scripts/codex_thread.sh pin <thread-id> [session-file]"

    printf '%s\n' "${thread_id}" > "${PIN_ID_FILE}"

    if [[ -z "${source_file}" ]]; then
        source_file="$(find_session_by_id "${thread_id}" || true)"
    fi

    if [[ -z "${source_file}" || ! -f "${source_file}" ]]; then
        echo "Pinned thread ID saved to ${PIN_ID_FILE}, but no local session file found for ${thread_id}."
        echo "Import that session first, then re-run pin to export archive."
        return 0
    fi

    gzip -c "${source_file}" > "${PIN_ARCHIVE}"
    {
        echo "thread_id=${thread_id}"
        echo "source_file=${source_file}"
        echo "exported_at_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
        echo "archive_bytes=$(wc -c < "${PIN_ARCHIVE}")"
    } > "${WORKFLOW_DIR}/pinned-session.meta"

    echo "Pinned thread ID: ${thread_id}"
    echo "Pinned archive: ${PIN_ARCHIVE}"
    echo "Next machine: run scripts/codex_thread.sh import (or the VS Code task) then open Codex thread list."
}

cmd_import() {
    local thread_id
    thread_id="$(read_pinned_id)"
    local imported
    imported="$(import_pinned_session_if_missing "${thread_id}")"
    echo "Pinned session available at: ${imported}"
    echo "Thread ID: ${thread_id}"
    echo "Now in VS Code Codex sidebar, open thread history and select this thread."
}

cmd_resume() {
    local thread_id
    thread_id="$(read_pinned_id)"
    import_pinned_session_if_missing "${thread_id}" >/dev/null
    local codex_bin
    codex_bin="$(detect_codex_bin)"
    exec "${codex_bin}" resume "${thread_id}"
}

cmd_status() {
    local thread_id=""
    if [[ -f "${PIN_ID_FILE}" ]]; then
        thread_id="$(read_pinned_id)"
    fi
    echo "Workflow dir: ${WORKFLOW_DIR}"
    echo "Pinned ID file: ${PIN_ID_FILE}"
    echo "Pinned thread ID: ${thread_id:-<none>}"
    if [[ -f "${PIN_ARCHIVE}" ]]; then
        echo "Pinned archive: ${PIN_ARCHIVE} ($(wc -c < "${PIN_ARCHIVE}") bytes)"
    else
        echo "Pinned archive: <missing>"
    fi
    if [[ -n "${thread_id}" ]]; then
        local local_file
        local_file="$(find_session_by_id "${thread_id}" || true)"
        echo "Local session file: ${local_file:-<not found>}"
    fi
}

cmd_help() {
    cat <<'EOF'
Usage:
  scripts/codex_thread.sh pin <thread-id> [session-file]
  scripts/codex_thread.sh import
  scripts/codex_thread.sh resume
  scripts/codex_thread.sh status
EOF
}

main() {
    local cmd="${1:-help}"
    shift || true
    case "${cmd}" in
        pin) cmd_pin "$@" ;;
        import) cmd_import "$@" ;;
        resume) cmd_resume "$@" ;;
        status) cmd_status "$@" ;;
        help|-h|--help) cmd_help ;;
        *) die "Unknown command: ${cmd}" ;;
    esac
}

main "$@"
