# Ready Commit Message

## Subject

Checkpoint/docs hardening: C1 green, C2 runner + templates, ops handoff

## Body

- finalize C1 checkpoint as GREEN and freeze associated manifests/docs
- align consolidated plan state:
  - mark P0-6 DONE (GREEN)
  - mark P0-7 DONE
  - set next gate to P0-8 (C2)
- add configurable regression recency window flow:
  - user_regression_suite CLI/env support
  - run-user-regression wrapper propagation
- align reclaim baseline contract to 8h and add explicit test coverage
- add targeted regression tests for recency-window behavior
- add one-command C2 checkpoint runner (`scripts/run_c2_checkpoint.sh`)
- add C2 delta template and C2 post-run checklist docs
- add pointer/artifact validation report and next-session handoff docs
- refresh README with full system workflow, checkpoint model, and operations runbook

## Optional Footer

Refs: P0-6, P0-7, P0-8, M402
