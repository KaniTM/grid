# Registry Lifecycle Triage (P0-2, Draft v1)

Generated: 2026-02-28 14:54:02 UTC

## 1) Scope
- Input: registry-only codes listed in `docs/CONSOLIDATED_MASTER_PLAN.md` Section 7.
- Codes classified: `83`.
- Classes: `ACTIVE`, `RETIRED`, `PARKED_FUTURE`.

## 2) Classification Rules (v1)
- `ACTIVE`: control-plane, risk, execution, replan, or warning codes required for immediate operational clarity.
- `PARKED_FUTURE`: observability/optional orchestration codes not required for immediate acceptance gates.
- `RETIRED`: none in this first pass (to be decided after module-level owner review).

## 3) Summary
- `ACTIVE`: 51
- `PARKED_FUTURE`: 32
- `RETIRED`: 0
- Owner default: `trading-core` for all entries unless reassigned.

## 4) ACTIVE Codes (Target <= C3)
### BlockReason
- `BLOCK_BOX_DONCHIAN_WIDTH_SANITY` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `BLOCK_BOX_STRADDLE_HTF_POC` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `BLOCK_BOX_WIDTH_TOO_NARROW` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `BLOCK_BREAKOUT_RECLAIM_PENDING` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `BLOCK_DATA_DUPLICATE_TS` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `BLOCK_DATA_NON_MONOTONIC_TS` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `BLOCK_EXEC_CONFIRM_REBUILD_FAILED` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `BLOCK_EXEC_CONFIRM_START_FAILED` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `BLOCK_FRESH_FVG_COOLOFF` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `BLOCK_INSIDE_SESSION_FVG` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `BLOCK_MIN_RUNTIME_NOT_MET` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `BLOCK_MRVD_CONFLUENCE_FAIL` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `BLOCK_MRVD_POC_DRIFT_GUARD` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `BLOCK_N_LEVELS_INVALID` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `BLOCK_SESSION_FVG_PAUSE` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `BLOCK_START_CONFLUENCE_LOW` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.

### EventType
- `EVENT_CVD_SPIKE_NEG` | owner=trading-core | checkpoint=C3 | reason=Near-term observability requirement for active/soon-to-be-active CVD or drift modules.
- `EVENT_CVD_SPIKE_POS` | owner=trading-core | checkpoint=C3 | reason=Near-term observability requirement for active/soon-to-be-active CVD or drift modules.
- `EVENT_PASSIVE_ABSORPTION_DN` | owner=trading-core | checkpoint=C3 | reason=Near-term observability requirement for active/soon-to-be-active CVD or drift modules.
- `EVENT_PASSIVE_ABSORPTION_UP` | owner=trading-core | checkpoint=C3 | reason=Near-term observability requirement for active/soon-to-be-active CVD or drift modules.

### ExecCode
- `EXEC_CAPACITY_NOTIONAL_CAP_APPLIED` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `EXEC_FILL_DUPLICATE_GUARD_HIT` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `EXEC_FILL_REPLACEMENT_PLACED` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `EXEC_ORDER_TIMEOUT_REPRICE` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `EXEC_RECONCILE_HOLD_NO_MATERIAL_CHANGE` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `EXEC_RECONCILE_MATERIAL_REBUILD` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `EXEC_RECONCILE_START_LADDER_CREATED` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `EXEC_RECONCILE_STOP_CANCELLED_LADDER` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.

### ReplanReason
- `REPLAN_DEFERRED_ACTIVE_FILL_WINDOW` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `REPLAN_DUPLICATE_PLAN_HASH` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `REPLAN_EPOCH_DEFERRED` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `REPLAN_MATERIAL_GRID_CHANGE` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `REPLAN_MATERIAL_RISK_CHANGE` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `REPLAN_SOFT_ADJUST_ONLY` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.

### StopReason
- `STOP_BREAKOUT_2STRIKE_DN` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `STOP_BREAKOUT_2STRIKE_UP` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `STOP_DATA_QUARANTINE` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `STOP_FAST_MOVE_DN` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `STOP_FAST_MOVE_UP` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `STOP_FRESH_STRUCTURE` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `STOP_LVN_VOID_EXIT_ACCEL` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `STOP_MRVD_AVG_BREAK` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `STOP_OS_DEV_DIRECTIONAL_FLIP` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `STOP_RANGE_SHIFT` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `STOP_SESSION_FVG_AGAINST_BIAS` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `STOP_SQUEEZE_RELEASE_AGAINST` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.

### WarningCode
- `WARN_CVD_DATA_QUALITY_LOW` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `WARN_EXEC_REPRICE_RATE_HIGH` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `WARN_FEATURE_FALLBACK_USED` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `WARN_PARTIAL_DATA_WINDOW` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.
- `WARN_PLAN_EXPIRES_SOON` | owner=trading-core | checkpoint=C3 | reason=Control-plane / risk / execution semantics should be explicit and test-covered.

## 5) PARKED_FUTURE Codes (Target review at C4+)
### EventType
- `EVENT_BBWP_EXTREME` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.
- `EVENT_DRIFT_RETEST_DN` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.
- `EVENT_DRIFT_RETEST_UP` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.
- `EVENT_EXTREME_RETEST_BOTTOM` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.
- `EVENT_EXTREME_RETEST_TOP` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.
- `EVENT_EXT_1386_RETEST_BOTTOM` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.
- `EVENT_EXT_1386_RETEST_TOP` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.
- `EVENT_FVG_MITIGATED_BEAR` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.
- `EVENT_FVG_MITIGATED_BULL` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.
- `EVENT_FVG_NEW_BEAR` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.
- `EVENT_FVG_NEW_BULL` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.
- `EVENT_IMFVG_AVG_TAG_BEAR` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.
- `EVENT_IMFVG_AVG_TAG_BULL` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.
- `EVENT_POC_ACCEPTANCE_CROSS` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.
- `EVENT_POC_TEST` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.
- `EVENT_RANGE_HIT_BOTTOM` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.
- `EVENT_RANGE_HIT_TOP` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.
- `EVENT_RECLAIM_CONFIRMED` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.
- `EVENT_SESSION_FVG_MITIGATED` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.
- `EVENT_SESSION_FVG_NEW` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.
- `EVENT_SQUEEZE_RELEASE_DN` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.
- `EVENT_SQUEEZE_RELEASE_UP` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.

### InfoCode
- `INFO_BOX_SHIFT_APPLIED` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.
- `INFO_REPLAN_EPOCH_BOUNDARY` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.
- `INFO_SL_SOURCE_SELECTED` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.
- `INFO_TARGET_SOURCE_SELECTED` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.
- `INFO_VOL_BUCKET_CHANGED` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.

### PauseReason
- `PAUSE_BBWP_COOLOFF` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.
- `PAUSE_DATA_DEGRADED` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.
- `PAUSE_DATA_QUARANTINE` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.
- `PAUSE_META_DRIFT_SOFT` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.
- `PAUSE_SESSION_FVG` | owner=trading-core | checkpoint=C4+ | reason=Observability or optional orchestration code; not required for immediate runtime acceptance gates.

## 6) RETIRED Codes
- None in draft v1. Promote entries here only after explicit owner decision and rollback plan.

## 7) Required Follow-up
1. Review `ACTIVE` list and confirm no code should be downgraded to `PARKED_FUTURE`.
2. Identify any clear duplicates/legacy aliases and move them to `RETIRED` with rollback notes.
3. Integrate accepted triage output back into the consolidated plan backlog and checkpoint tasks.
