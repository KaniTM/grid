# Replan Policy and Materiality

This document defines when a new planner decision is published to executor.

## Materiality classes

- `noop`: no publish; keep current plan.
- `soft`: publish on epoch cadence even if deltas are small.
- `material`: publish immediately because box/grid/risk deltas crossed thresholds.
- `hardstop`: publish immediately; safety event override.

## Current publish policy

Per pair, planner computes:

- `delta_mid_steps`
- `delta_width_pct`
- `delta_tp_steps`
- `delta_sl_steps`
- epoch counter (`materiality_epoch_bars`)

Publish decision:

1. `hardstop` when hard stop condition exists or action is `STOP`.
2. `material` when any material threshold is crossed.
3. `soft` on epoch boundary (or first plan).
4. `noop` otherwise.

## Contract fields in plan payload

- `materiality_class`
- `replan_decision` (`publish|defer`)
- `replan_reasons` (canonical reason codes)
- `changed_fields` (optional field-level diff hints)

## Acceptance criteria

- Materiality logic is deterministic for same candle inputs.
- `materiality_class` and `replan_reasons` are present on published plans.
- Non-published candles do not churn `decision_seq`.
