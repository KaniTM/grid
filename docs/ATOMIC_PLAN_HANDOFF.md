# Atomic Plan Handoff

This document defines the Brain -> Executor handoff contract.

## Planner publish semantics

Planner writes:

1. `grid_plan.latest.json.tmp`
2. flush + `fsync`
3. atomic rename to `grid_plan.latest.json`

Archive snapshots (`grid_plan.<ts>.json`) are written with the same atomic method.

## Required plan signature fields

- `schema_version`
- `planner_version`
- `pair`
- `exchange`
- `plan_id` (UUID)
- `decision_seq` (monotonic per pair)
- `plan_hash` (sha256 over material fields)
- `generated_at`
- `valid_for_candle_ts`
- `expires_at` (optional)
- `supersedes_plan_id` (optional)
- `materiality_class`

## Executor intake semantics

Executor must reject plans when any condition is true:

- schema invalid (`EXEC_PLAN_SCHEMA_INVALID`)
- hash mismatch (`EXEC_PLAN_HASH_MISMATCH`)
- duplicate `plan_id`/hash (`EXEC_PLAN_DUPLICATE_IGNORED`)
- stale `decision_seq <= last_applied_seq` (`EXEC_PLAN_STALE_SEQ_IGNORED`)
- expired plan (`EXEC_PLAN_EXPIRED_IGNORED`)

Accepted plan emits `EXEC_PLAN_APPLIED` and updates:

- `last_applied_plan_id`
- `last_applied_seq`
- `last_plan_hash`

## State persistence

Executor state persists signature intake state so restarts remain idempotent.
