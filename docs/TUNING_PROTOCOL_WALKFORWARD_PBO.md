# Tuning Protocol: Walk-Forward + PBO

This document captures process requirements for deterministic tuning and anti-overfit checks.

## Required process

1. Define search space and freeze config snapshot.
2. Run walk-forward splits with out-of-sample windows.
3. Rank candidates by primary metric + guardrail metrics.
4. Compute overfit diagnostics (including PBO-style checks).
5. Register champion with traceable artifact metadata.

## Mandatory artifacts

- split definitions
- per-window metrics
- candidate ranking summary
- champion registry entry
- reproducible seed list

## Guardrails

- deterministic core behavior cannot be changed by tuning process
- safety metrics must be non-regressing
- unstable candidates are rejected even with higher headline return

## Schema linkage

Output summaries should align with project schema conventions and versioning.
