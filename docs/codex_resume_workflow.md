# Codex Thread Resume Workflow (Cross-PC)

This repo now includes a pinned-thread workflow under `.codex-workflow/`.

## What is stored
- `.codex-workflow/pinned-thread-id`
- `.codex-workflow/pinned-session.jsonl.gz`
- `.codex-workflow/pinned-session.meta`

## VS Code one-click tasks
Use `Terminal -> Run Task...`:

1. `Codex: Import Pinned Thread`
2. Open the **Codex** sidebar and select the restored thread from history.

Optional fallback:
- `Codex: Resume Pinned Thread (Terminal)` runs `codex resume <pinned-id>` directly.

## Pin or update the pinned thread
Run task:
- `Codex: Pin Thread ID`

Or run:
```bash
bash scripts/codex_thread.sh pin <thread-id>
```

## Switch to another computer
1. Pull latest repo.
2. Run task `Codex: Import Pinned Thread`.
3. Open Codex sidebar history and continue from the pinned thread.

## Notes
- Codex sidebar does not currently expose a true "pin" action for a specific thread id.
- This workflow emulates pinning by keeping the thread id + session export in repo and restoring locally.
