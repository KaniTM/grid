# Registry Lifecycle Triage (P0-2, Final v2)

Generated: 2026-02-28

## 1) Scope
- Source of truth for input set: `docs/CONSOLIDATED_MASTER_PLAN.md` Section 7 (`REGISTRY_ONLY` inventory).
- Codes in scope: `83`.
- Required lifecycle classes: `ACTIVE`, `RETIRED`, `PARKED_FUTURE`.
- Owner default: `trading-core`.

## 2) Validation
- Set parity check completed against Section 7.
- Missing codes in triage: `0`.
- Extra codes in triage: `0`.
- Result: all `83/83` registry-only codes are classified.

## 3) Final Classification Rules
- `ACTIVE`
  - Meaning: must be wired and test-covered in near-term checkpoints.
  - Target checkpoint: `<= C3`.
- `PARKED_FUTURE`
  - Meaning: kept in canonical registry, intentionally not wired now.
  - Target checkpoint for re-evaluation: `C4+`.
- `RETIRED`
  - Meaning: no longer part of strategy direction.
  - Code action: `delete_now` or `soft_retire_then_delete_at_next_checkpoint`.

## 4) Summary
- `ACTIVE`: `51`
- `PARKED_FUTURE`: `32`
- `RETIRED`: `0`

## 5) ACTIVE Codes (Target <= C3)
### BlockReason
- `BLOCK_BOX_DONCHIAN_WIDTH_SANITY` | owner=trading-core | checkpoint=C3 | reason=Start/rebuild safety gate should emit explicit blocker semantics.
- `BLOCK_BOX_STRADDLE_HTF_POC` | owner=trading-core | checkpoint=C3 | reason=Start/rebuild safety gate should emit explicit blocker semantics.
- `BLOCK_BOX_WIDTH_TOO_NARROW` | owner=trading-core | checkpoint=C3 | reason=Start/rebuild safety gate should emit explicit blocker semantics.
- `BLOCK_BREAKOUT_RECLAIM_PENDING` | owner=trading-core | checkpoint=C3 | reason=Start/rebuild safety gate should emit explicit blocker semantics.
- `BLOCK_DATA_DUPLICATE_TS` | owner=trading-core | checkpoint=C3 | reason=Data-quality guard should emit explicit blocker semantics.
- `BLOCK_DATA_NON_MONOTONIC_TS` | owner=trading-core | checkpoint=C3 | reason=Data-quality guard should emit explicit blocker semantics.
- `BLOCK_EXEC_CONFIRM_REBUILD_FAILED` | owner=trading-core | checkpoint=C3 | reason=Executor confirmation failures should map to explicit blocker semantics.
- `BLOCK_EXEC_CONFIRM_START_FAILED` | owner=trading-core | checkpoint=C3 | reason=Executor confirmation failures should map to explicit blocker semantics.
- `BLOCK_FRESH_FVG_COOLOFF` | owner=trading-core | checkpoint=C3 | reason=Structure cooldown behavior should emit explicit blocker semantics.
- `BLOCK_INSIDE_SESSION_FVG` | owner=trading-core | checkpoint=C3 | reason=Structure/session gating should emit explicit blocker semantics.
- `BLOCK_MIN_RUNTIME_NOT_MET` | owner=trading-core | checkpoint=C3 | reason=Lifecycle/runtime rails should emit explicit blocker semantics.
- `BLOCK_MRVD_CONFLUENCE_FAIL` | owner=trading-core | checkpoint=C3 | reason=Confluence contract should emit explicit blocker semantics.
- `BLOCK_MRVD_POC_DRIFT_GUARD` | owner=trading-core | checkpoint=C3 | reason=Confluence contract should emit explicit blocker semantics.
- `BLOCK_N_LEVELS_INVALID` | owner=trading-core | checkpoint=C3 | reason=Plan geometry guard should emit explicit blocker semantics.
- `BLOCK_SESSION_FVG_PAUSE` | owner=trading-core | checkpoint=C3 | reason=Session/FVG pause behavior should emit explicit blocker semantics.
- `BLOCK_START_CONFLUENCE_LOW` | owner=trading-core | checkpoint=C3 | reason=Start eligibility should emit explicit blocker semantics.

### EventType
- `EVENT_CVD_SPIKE_NEG` | owner=trading-core | checkpoint=C3 | reason=CVD microstructure events are required for near-term observability.
- `EVENT_CVD_SPIKE_POS` | owner=trading-core | checkpoint=C3 | reason=CVD microstructure events are required for near-term observability.
- `EVENT_PASSIVE_ABSORPTION_DN` | owner=trading-core | checkpoint=C3 | reason=CVD microstructure events are required for near-term observability.
- `EVENT_PASSIVE_ABSORPTION_UP` | owner=trading-core | checkpoint=C3 | reason=CVD microstructure events are required for near-term observability.

### ExecCode
- `EXEC_CAPACITY_NOTIONAL_CAP_APPLIED` | owner=trading-core | checkpoint=C3 | reason=Capacity actions must be externally traceable.
- `EXEC_FILL_DUPLICATE_GUARD_HIT` | owner=trading-core | checkpoint=C3 | reason=Fill guard actions must be externally traceable.
- `EXEC_FILL_REPLACEMENT_PLACED` | owner=trading-core | checkpoint=C3 | reason=Fill replacement actions must be externally traceable.
- `EXEC_ORDER_TIMEOUT_REPRICE` | owner=trading-core | checkpoint=C3 | reason=Execution repricing behavior must be externally traceable.
- `EXEC_RECONCILE_HOLD_NO_MATERIAL_CHANGE` | owner=trading-core | checkpoint=C3 | reason=Reconcile outcomes must be externally traceable.
- `EXEC_RECONCILE_MATERIAL_REBUILD` | owner=trading-core | checkpoint=C3 | reason=Reconcile outcomes must be externally traceable.
- `EXEC_RECONCILE_START_LADDER_CREATED` | owner=trading-core | checkpoint=C3 | reason=Reconcile outcomes must be externally traceable.
- `EXEC_RECONCILE_STOP_CANCELLED_LADDER` | owner=trading-core | checkpoint=C3 | reason=Reconcile outcomes must be externally traceable.

### ReplanReason
- `REPLAN_DEFERRED_ACTIVE_FILL_WINDOW` | owner=trading-core | checkpoint=C3 | reason=Replan deferral semantics must be externally traceable.
- `REPLAN_DUPLICATE_PLAN_HASH` | owner=trading-core | checkpoint=C3 | reason=Replan idempotency semantics must be externally traceable.
- `REPLAN_EPOCH_DEFERRED` | owner=trading-core | checkpoint=C3 | reason=Replan epoch semantics must be externally traceable.
- `REPLAN_MATERIAL_GRID_CHANGE` | owner=trading-core | checkpoint=C3 | reason=Replan materiality semantics must be externally traceable.
- `REPLAN_MATERIAL_RISK_CHANGE` | owner=trading-core | checkpoint=C3 | reason=Replan materiality semantics must be externally traceable.
- `REPLAN_SOFT_ADJUST_ONLY` | owner=trading-core | checkpoint=C3 | reason=Replan soft-adjust semantics must be externally traceable.

### StopReason
- `STOP_BREAKOUT_2STRIKE_DN` | owner=trading-core | checkpoint=C3 | reason=Stop framework outcomes must be externally traceable.
- `STOP_BREAKOUT_2STRIKE_UP` | owner=trading-core | checkpoint=C3 | reason=Stop framework outcomes must be externally traceable.
- `STOP_DATA_QUARANTINE` | owner=trading-core | checkpoint=C3 | reason=Stop framework outcomes must be externally traceable.
- `STOP_FAST_MOVE_DN` | owner=trading-core | checkpoint=C3 | reason=Stop framework outcomes must be externally traceable.
- `STOP_FAST_MOVE_UP` | owner=trading-core | checkpoint=C3 | reason=Stop framework outcomes must be externally traceable.
- `STOP_FRESH_STRUCTURE` | owner=trading-core | checkpoint=C3 | reason=Stop framework outcomes must be externally traceable.
- `STOP_LVN_VOID_EXIT_ACCEL` | owner=trading-core | checkpoint=C3 | reason=Stop framework outcomes must be externally traceable.
- `STOP_MRVD_AVG_BREAK` | owner=trading-core | checkpoint=C3 | reason=Stop framework outcomes must be externally traceable.
- `STOP_OS_DEV_DIRECTIONAL_FLIP` | owner=trading-core | checkpoint=C3 | reason=Stop framework outcomes must be externally traceable.
- `STOP_RANGE_SHIFT` | owner=trading-core | checkpoint=C3 | reason=Stop framework outcomes must be externally traceable.
- `STOP_SESSION_FVG_AGAINST_BIAS` | owner=trading-core | checkpoint=C3 | reason=Stop framework outcomes must be externally traceable.
- `STOP_SQUEEZE_RELEASE_AGAINST` | owner=trading-core | checkpoint=C3 | reason=Stop framework outcomes must be externally traceable.

### WarningCode
- `WARN_CVD_DATA_QUALITY_LOW` | owner=trading-core | checkpoint=C3 | reason=Runtime quality degradations should emit explicit warning semantics.
- `WARN_EXEC_REPRICE_RATE_HIGH` | owner=trading-core | checkpoint=C3 | reason=Runtime quality degradations should emit explicit warning semantics.
- `WARN_FEATURE_FALLBACK_USED` | owner=trading-core | checkpoint=C3 | reason=Runtime quality degradations should emit explicit warning semantics.
- `WARN_PARTIAL_DATA_WINDOW` | owner=trading-core | checkpoint=C3 | reason=Runtime quality degradations should emit explicit warning semantics.
- `WARN_PLAN_EXPIRES_SOON` | owner=trading-core | checkpoint=C3 | reason=Runtime quality degradations should emit explicit warning semantics.

## 6) PARKED_FUTURE Codes (Target review at C4+)
### EventType
- `EVENT_BBWP_EXTREME` | owner=trading-core | checkpoint=C4+ | reason=Useful observability signal, not required for immediate acceptance gates.
- `EVENT_DRIFT_RETEST_DN` | owner=trading-core | checkpoint=C4+ | reason=Useful observability signal, not required for immediate acceptance gates.
- `EVENT_DRIFT_RETEST_UP` | owner=trading-core | checkpoint=C4+ | reason=Useful observability signal, not required for immediate acceptance gates.
- `EVENT_EXTREME_RETEST_BOTTOM` | owner=trading-core | checkpoint=C4+ | reason=Useful observability signal, not required for immediate acceptance gates.
- `EVENT_EXTREME_RETEST_TOP` | owner=trading-core | checkpoint=C4+ | reason=Useful observability signal, not required for immediate acceptance gates.
- `EVENT_EXT_1386_RETEST_BOTTOM` | owner=trading-core | checkpoint=C4+ | reason=Useful observability signal, not required for immediate acceptance gates.
- `EVENT_EXT_1386_RETEST_TOP` | owner=trading-core | checkpoint=C4+ | reason=Useful observability signal, not required for immediate acceptance gates.
- `EVENT_FVG_MITIGATED_BEAR` | owner=trading-core | checkpoint=C4+ | reason=Useful observability signal, not required for immediate acceptance gates.
- `EVENT_FVG_MITIGATED_BULL` | owner=trading-core | checkpoint=C4+ | reason=Useful observability signal, not required for immediate acceptance gates.
- `EVENT_FVG_NEW_BEAR` | owner=trading-core | checkpoint=C4+ | reason=Useful observability signal, not required for immediate acceptance gates.
- `EVENT_FVG_NEW_BULL` | owner=trading-core | checkpoint=C4+ | reason=Useful observability signal, not required for immediate acceptance gates.
- `EVENT_IMFVG_AVG_TAG_BEAR` | owner=trading-core | checkpoint=C4+ | reason=Useful observability signal, not required for immediate acceptance gates.
- `EVENT_IMFVG_AVG_TAG_BULL` | owner=trading-core | checkpoint=C4+ | reason=Useful observability signal, not required for immediate acceptance gates.
- `EVENT_POC_ACCEPTANCE_CROSS` | owner=trading-core | checkpoint=C4+ | reason=Useful observability signal, not required for immediate acceptance gates.
- `EVENT_POC_TEST` | owner=trading-core | checkpoint=C4+ | reason=Useful observability signal, not required for immediate acceptance gates.
- `EVENT_RANGE_HIT_BOTTOM` | owner=trading-core | checkpoint=C4+ | reason=Useful observability signal, not required for immediate acceptance gates.
- `EVENT_RANGE_HIT_TOP` | owner=trading-core | checkpoint=C4+ | reason=Useful observability signal, not required for immediate acceptance gates.
- `EVENT_RECLAIM_CONFIRMED` | owner=trading-core | checkpoint=C4+ | reason=Useful observability signal, not required for immediate acceptance gates.
- `EVENT_SESSION_FVG_MITIGATED` | owner=trading-core | checkpoint=C4+ | reason=Useful observability signal, not required for immediate acceptance gates.
- `EVENT_SESSION_FVG_NEW` | owner=trading-core | checkpoint=C4+ | reason=Useful observability signal, not required for immediate acceptance gates.
- `EVENT_SQUEEZE_RELEASE_DN` | owner=trading-core | checkpoint=C4+ | reason=Useful observability signal, not required for immediate acceptance gates.
- `EVENT_SQUEEZE_RELEASE_UP` | owner=trading-core | checkpoint=C4+ | reason=Useful observability signal, not required for immediate acceptance gates.

### InfoCode
- `INFO_BOX_SHIFT_APPLIED` | owner=trading-core | checkpoint=C4+ | reason=Useful observability signal, not required for immediate acceptance gates.
- `INFO_REPLAN_EPOCH_BOUNDARY` | owner=trading-core | checkpoint=C4+ | reason=Useful observability signal, not required for immediate acceptance gates.
- `INFO_SL_SOURCE_SELECTED` | owner=trading-core | checkpoint=C4+ | reason=Useful observability signal, not required for immediate acceptance gates.
- `INFO_TARGET_SOURCE_SELECTED` | owner=trading-core | checkpoint=C4+ | reason=Useful observability signal, not required for immediate acceptance gates.
- `INFO_VOL_BUCKET_CHANGED` | owner=trading-core | checkpoint=C4+ | reason=Useful observability signal, not required for immediate acceptance gates.

### PauseReason
- `PAUSE_BBWP_COOLOFF` | owner=trading-core | checkpoint=C4+ | reason=Optional pause observability, not required for immediate acceptance gates.
- `PAUSE_DATA_DEGRADED` | owner=trading-core | checkpoint=C4+ | reason=Optional pause observability, not required for immediate acceptance gates.
- `PAUSE_DATA_QUARANTINE` | owner=trading-core | checkpoint=C4+ | reason=Optional pause observability, not required for immediate acceptance gates.
- `PAUSE_META_DRIFT_SOFT` | owner=trading-core | checkpoint=C4+ | reason=Optional pause observability, not required for immediate acceptance gates.
- `PAUSE_SESSION_FVG` | owner=trading-core | checkpoint=C4+ | reason=Optional pause observability, not required for immediate acceptance gates.

## 7) RETIRED Codes
- None in final v2 (`0`).
- Rationale: this pass found no registry-only duplicate aliases safe to retire without additional evidence.

## 8) Execution Queue for ACTIVE Wiring
1. Wave A (`C1-C2`): `BlockReason` set (16 codes).
2. Wave B (`C2`): `StopReason` set (12 codes).
3. Wave C (`C2-C3`): `ExecCode` set (8 codes).
4. Wave D (`C3`): `ReplanReason` set (6 codes).
5. Wave E (`C3`): `WarningCode` set (5 codes).
6. Wave F (`C3`): `EventType` microstructure set (4 codes).

## 9) Retire Handling Rule (for future conversions)
- When any code is moved to `RETIRED`, one of these actions is mandatory:
  1. `delete_now` (low rollback risk), or
  2. `soft_retire_then_delete_at_next_checkpoint` (medium/high rollback risk).
- Keeping dead runtime logic as commented code is not allowed.

## 10) Acceptance Check (P0-2)
- `83/83` registry-only codes classified.
- Each code has lifecycle state + owner + checkpoint + rationale.
- No missing/extra entries versus Section 7 inventory.
- Active wiring execution order is defined.
