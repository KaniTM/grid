# DECISION_REASON_CODES.md

## Purpose

This file is the **canonical vocabulary** for all planner/simulator/executor decisions, blockers, stops, replan outcomes, warnings, and events.

It exists to ensure:

- deterministic and explainable behavior,
- stable analytics across replays and live/paper runs,
- consistency across Brain / Simulator / Executor,
- safe Codex refactors (no accidental string drift),
- traceability from master plan -> implementation -> logs -> experiments.

---

## Scope

This file defines canonical codes for:

- `BLOCK_*` (hard/soft blockers that prevent `START` / `REBUILD`)
- `STOP_*` (runtime stop triggers)
- `REPLAN_*` (materiality / plan inertia decisions)
- `WARN_*` (degraded but non-blocking issues)
- `PAUSE_*` (planner health / quarantine / cooloff state reasons)
- `EXEC_*` (executor-applied runtime controls and actions)
- `EVENT_*` (event bus taxonomy emitted by modules)
- `INFO_*` (optional informational diagnostics, if used)

These codes must be used consistently in:

- `grid_plan.latest.json`
- planner decision logs
- simulator traces/results
- executor audit logs
- experiment outputs / reason distributions

---

## Non-Negotiable Rules

### 1) Canonical only
Do **not** invent ad-hoc strings in code or logs.

✅ Use:
- `BLOCK_BBW_EXPANDING`

❌ Do not use:
- `BBW_BLOCK`
- `block_bbw`
- `bbw_too_wide`

### 2) Stable semantics
Once introduced, a code’s meaning should remain stable.
If semantics change materially, create a new code and deprecate the old one.

### 3) One code = one primary meaning
Avoid overloaded codes that mean multiple different things.

### 4) Multiple reasons are allowed
A decision can contain multiple blockers/reasons. Preserve all applicable reasons (ordered by priority).

### 5) Priority is explicit
When reasons conflict, use the system’s conflict ladder:
- STOP / veto beats START
- Pause beats build
- Safety / quarantine beats normal operation
- Hard execution unsafety beats placement

### 6) Sync with enums
The Python enum registry (e.g., `core/enums.py`) must mirror these codes.
If a new code is added here, add it to the enum registry.

---

## Naming Convention

Format:

`<CATEGORY>_<SUBSYSTEM>_<CONDITION>[_<QUALIFIER>]`

Examples:
- `BLOCK_ADX_HIGH`
- `BLOCK_BBWP_HIGH`
- `STOP_BREAKOUT_2STRIKE_UP`
- `REPLAN_NOOP_MINOR_DELTA`
- `EXEC_CAPACITY_RUNG_CAP_APPLIED`
- `EVENT_POC_TEST`

### Categories
- `BLOCK` = prevents `START` / `REBUILD` (hard or soft gate)
- `STOP` = triggers stop path / idle transition
- `REPLAN` = plan inertia/materiality output
- `WARN` = non-blocking warning
- `PAUSE` = explicit pause/quarantine/cooloff state reason
- `EXEC` = executor runtime action/control
- `EVENT` = event bus records
- `INFO` = optional informational code

---

## Severity Levels (recommended metadata in code/docs)

Each code should be tagged in implementation with one of:

- `hard` → blocks or forces action
- `soft` → influences score / pause / confidence
- `advisory` → analytics / diagnostics / optional nudges

---

## Standard Logging Fields (recommended)

When a code is emitted, attach structured context where relevant:

- `ts`
- `pair`
- `timeframe`
- `module`
- `severity`
- `action_context` (`START` / `HOLD` / `STOP` / `REBUILD`)
- `value`
- `threshold`
- `lookback`
- `side` (if applicable)
- `metadata` (json object)

Example:
```json
{
  "code": "BLOCK_BBW_EXPANDING",
  "module": "bbw_quietness_gate",
  "severity": "hard",
  "action_context": "START",
  "value": 0.0412,
  "threshold": 0.0385,
  "lookback": 3,
  "metadata": {"tol_mult": 1.05}
}
```

---

## Decision Output Contract (recommended)

### Planner (`grid_plan.latest.json`)
Use these fields (or equivalent):
- `blockers: []`
- `action_reason: []` (for final action drivers)
- `warnings: []`
- `events_recent: []` (optional)
- `materiality_class` (`noop|soft|material|hardstop`) + `replan_reasons: []`

### Simulator
- Preserve exact codes in per-candle decisions and summary stats.
- Aggregate reason frequency by canonical code.

### Executor
- Preserve exact `EXEC_*`, `WARN_*`, and applied plan reason context.
- If executor rejects a plan due to schema/hash/idempotency, emit canonical executor codes.

---

## Code Registry

---

# A) BLOCK_* (START / REBUILD blockers)

## A.1 Core Regime / Quietness Gates

### `BLOCK_ADX_HIGH`
- **Module:** ADX gate (4h)
- **Meaning:** ADX is above configured threshold/hysteresis entry bound; directional regime too strong for new grid.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_BBW_EXPANDING`
- **Module:** BBW quietness gate (1h)
- **Meaning:** Bollinger Band Width is expanding beyond configured tolerance over lookback; volatility expansion risk.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_EMA_DIST`
- **Module:** EMA compression gate (1h)
- **Meaning:** Normalized distance between EMA50 and EMA100 exceeds allowed compression threshold.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_RVOL_SPIKE`
- **Module:** relative volume gate
- **Meaning:** Relative volume indicates impulse/spike regime; not calm enough for build/start.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_7D_EXTREME_CONTEXT`
- **Module:** 7d context sanity
- **Meaning:** Current price/box is too close to or beyond unacceptable 7d extremes context for new grid build.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

---

## A.2 Structural Breakout / Drift / Regime State

### `BLOCK_FRESH_BREAKOUT`
- **Module:** local structure breakout fresh-block (15m)
- **Meaning:** A confirmed recent breakout occurred within cooloff window; reclaim wait required.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_BREAKOUT_RECLAIM_PENDING`
- **Module:** breakout reclaim timer
- **Meaning:** Fresh breakout cooloff/reclaim timer still active.
- **Applies to:** `REBUILD`, `START`
- **Severity:** hard

### `BLOCK_OS_DEV_DIRECTIONAL`
- **Module:** Range DI / deviation-pivot regime (`os_dev`)
- **Meaning:** `os_dev` is directional (`-1` or `+1`) and neutral/range state is required.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_OS_DEV_NEUTRAL_PERSISTENCE`
- **Module:** Range DI / deviation-pivot regime (`os_dev`)
- **Meaning:** `os_dev == 0` but neutral persistence duration is insufficient.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_BAND_SLOPE_HIGH`
- **Module:** band slope veto
- **Meaning:** Band midline slope exceeds threshold (% per N bars), indicating hidden trend acceleration.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_DRIFT_SLOPE_HIGH`
- **Module:** drift / pivot-to-pivot slope veto
- **Meaning:** Drift slope exceeds threshold, indicating directional drift incompatible with range build.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_EXCURSION_ASYMMETRY`
- **Module:** excursion asymmetry veto
- **Meaning:** Up/down excursions are too asymmetric relative to allowed range regime bounds.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard or soft (configurable)

### `BLOCK_META_DRIFT_SOFT`
- **Module:** meta drift guard (Page-Hinkley/CUSUM style)
- **Meaning:** Change-point/drift detector indicates distribution drift; pause new starts/rebuilds.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard (for start/rebuild), soft globally

---

## A.3 Volatility Regime / BBWP / Squeeze

### `BLOCK_BBWP_HIGH`
- **Module:** BBWP MTF gate
- **Meaning:** One or more BBWP TF values exceed configured veto threshold (e.g., >=90).
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `COOLOFF_BBWP_EXTREME`
- **Module:** BBWP MTF cooloff
- **Meaning:** BBWP extreme condition triggered cooloff; wait until cooloff recovery thresholds are met.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_SQUEEZE_RELEASE_AGAINST_BIAS`
- **Module:** squeeze state gate
- **Meaning:** Squeeze released against current box/grid bias; starting/rebuilding is blocked.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_VOL_BUCKET_UNSTABLE`
- **Module:** volatility policy adapter
- **Meaning:** Current volatility bucket is `unstable`; planner policy blocks new starts/rebuilds.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

---

## A.4 Box Builder Integrity / Width / Straddle

### `BLOCK_BOX_WIDTH_TOO_NARROW`
- **Module:** box builder
- **Meaning:** Proposed box width is below minimum acceptable threshold and fallback/expansion failed.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_BOX_WIDTH_TOO_WIDE`
- **Module:** box builder
- **Meaning:** Proposed box width exceeds hard limit or mode policy rejects it.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_BOX_STRADDLE_BREAKOUT_LEVEL`
- **Module:** box straddle veto framework
- **Meaning:** Box straddles cached breakout level within disallowed distance (< configured step multiple).
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_BOX_STRADDLE_OB_EDGE`
- **Module:** OB module
- **Meaning:** Box straddles opposite-side order block edge within disallowed distance.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_BOX_STRADDLE_FVG_EDGE`
- **Module:** FVG module
- **Meaning:** Box straddles opposite-side FVG edge within disallowed distance.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_BOX_STRADDLE_FVG_AVG`
- **Module:** IMFVG / FVG avg
- **Meaning:** Box straddles (I)MFVG average within disallowed distance and mitigation relax is not active.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_BOX_STRADDLE_SESSION_FVG_AVG`
- **Module:** Session FVG
- **Meaning:** Box straddles session FVG average within disallowed distance.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_BOX_STRADDLE_HTF_POC`
- **Module:** MRVD / MTF-POC
- **Meaning:** Box straddles higher-timeframe POC within disallowed distance and shift/rebuild rules failed.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_BOX_STRADDLE_VWAP_DONCHIAN_MID`
- **Module:** multi-range basis / pivots
- **Meaning:** Box straddles VWAP/Donchian mid under width conditions that invalidate build.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_BOX_VP_POC_MISPLACED`
- **Module:** VRVP box integrity
- **Meaning:** VRVP POC is too far from the proposed box and allowed shift/reject policy invalidates build.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_BOX_CHANNEL_OVERLAP_LOW`
- **Module:** channel envelope / zig-zag envelope checks
- **Meaning:** Box/channel overlap is below acceptable threshold for valid range representation.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard (or soft if configured)

### `BLOCK_BOX_DONCHIAN_WIDTH_SANITY`
- **Module:** Donchian width gate
- **Meaning:** Donchian width indicates unstable/trending regime relative to proposed box.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

---

## A.5 Acceptance / Confluence / Start Eligibility

### `BLOCK_NO_POC_ACCEPTANCE`
- **Module:** POC acceptance gate
- **Meaning:** No required POC cross/acceptance occurred for current box generation before first START.
- **Applies to:** `START`
- **Severity:** hard

### `BLOCK_POC_ALIGNMENT_FAIL`
- **Module:** micro-VAP / VRVP POC alignment
- **Meaning:** Micro-POC and VRVP POC are misaligned beyond allowed threshold and acceptance cross is pending.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard or soft (configurable)

### `BLOCK_START_BOX_POSITION`
- **Module:** START box-position gate
- **Meaning:** Price is outside the allowed normalized box region for START (e.g., not in middle zone).
- **Applies to:** `START`
- **Severity:** hard

### `BLOCK_START_RSI_BAND`
- **Module:** optional RSI gate
- **Meaning:** RSI is outside allowed band for START (or post-breakout micro guard is active).
- **Applies to:** `START`
- **Severity:** hard (if enabled)

### `BLOCK_START_CONFLUENCE_LOW`
- **Module:** confluence aggregator (MRVD/VAH/VAL/basis/etc.)
- **Meaning:** Required confluence score or proximity conditions are not met.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard (if gate enabled)

### `BLOCK_START_STABILITY_LOW`
- **Module:** global start stability score
- **Meaning:** Start stability score is below required threshold.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_START_PERSISTENCE_FAIL`
- **Module:** start stability k-of-n persistence
- **Meaning:** Score/gates did not persist across required k-of-n window.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_BASIS_CROSS_PENDING`
- **Module:** multi-range basis / pivots module
- **Meaning:** Required basis cross inside current box has not occurred after rebuild/new box.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard (if enabled)

### `BLOCK_VAH_VAL_POC_PROXIMITY`
- **Module:** VAH/VAL/POC proximity gate
- **Meaning:** Price is not within configured proximity band to nearest VAH/VAL/POC.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard (if enabled)

### `BLOCK_MRVD_CONFLUENCE_FAIL`
- **Module:** MRVD module
- **Meaning:** Box lacks required D/W/M volume-profile confluence (bands/POCs).
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_MRVD_POC_DRIFT_GUARD`
- **Module:** MRVD module
- **Meaning:** Day POC drifted materially against higher-period POC alignment and bias; pause until cross/realignment.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

---

## A.6 Cost / Sizing / Capacity / Execution-Aware Start Blocks

### `BLOCK_STEP_BELOW_COST`
- **Module:** cost-aware step sizing
- **Meaning:** Proposed grid step is below static required cost floor (fees + spread + target net).
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_STEP_BELOW_EMPIRICAL_COST`
- **Module:** empirical cost calibrator integration
- **Meaning:** Proposed step is below empirically calibrated cost floor.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_N_LEVELS_INVALID`
- **Module:** N-level selection policy
- **Meaning:** No valid `N` within bounds satisfies width/step/cost constraints.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_CAPACITY_THIN`
- **Module:** depth-aware capacity guard
- **Meaning:** Market depth/spread conditions imply insufficient safe capacity for planned ladder.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard (planner-side) / soft (if executor can cap)

### `BLOCK_EXEC_CONFIRM_START_FAILED`
- **Module:** confirm-entry hook (executor/planner simulation)
- **Meaning:** Execution safety confirmation failed (spread/depth/jump/post-only feasibility).
- **Applies to:** `START`
- **Severity:** hard (runtime)

### `BLOCK_EXEC_CONFIRM_REBUILD_FAILED`
- **Module:** confirm-rebuild hook
- **Meaning:** Execution safety confirmation failed for rebuild action.
- **Applies to:** `REBUILD`
- **Severity:** hard (runtime)

---

## A.7 Cooldown / Reclaim / Runtime Rails

### `BLOCK_RECLAIM_PENDING`
- **Module:** reclaim discipline
- **Meaning:** Reclaim timer is active and rebuild/start is not yet allowed.
- **Applies to:** `REBUILD`, `START`
- **Severity:** hard

### `BLOCK_RECLAIM_NOT_CONFIRMED`
- **Module:** reclaim discipline
- **Meaning:** Reclaim timer elapsed but reclaim conditions (re-entry/gates/acceptance) are not satisfied.
- **Applies to:** `REBUILD`, `START`
- **Severity:** hard

### `BLOCK_COOLDOWN_ACTIVE`
- **Module:** protections layer
- **Meaning:** Cooldown window after STOP/REBUILD/entry is still active.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_MIN_RUNTIME_NOT_MET`
- **Module:** anti-flap rail
- **Meaning:** Min runtime gate prevents non-emergency rebuild/stop-cycle transitions.
- **Applies to:** typically `REBUILD` / non-emergency stop path
- **Severity:** hard (except emergency overrides)

### `BLOCK_DRAWDOWN_GUARD`
- **Module:** protections layer
- **Meaning:** Drawdown guard blocks new entries/rebuilds.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_MAX_STOPS_WINDOW`
- **Module:** protections layer
- **Meaning:** Max stop count breaker in rolling window blocks new starts.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

---

## A.8 Data Quality / Health State Blocks

### `BLOCK_DATA_GAP`
- **Module:** data quality monitor
- **Meaning:** Missing candle gap detected in required input series.
- **Applies to:** `START`, `REBUILD` (and may force pause)
- **Severity:** hard

### `BLOCK_DATA_DUPLICATE_TS`
- **Module:** data quality monitor
- **Meaning:** Duplicate timestamps detected in source/informative data.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_DATA_NON_MONOTONIC_TS`
- **Module:** data quality monitor
- **Meaning:** Non-monotonic timestamps detected.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_DATA_MISALIGN`
- **Module:** multi-timeframe merge integrity
- **Meaning:** 15m/1h/4h alignment failed or informative merge integrity violated.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_ZERO_VOL_ANOMALY`
- **Module:** data quality monitor
- **Meaning:** Suspicious zero-volume streak/anomaly detected.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_STALE_FEATURES`
- **Module:** feature pipeline health
- **Meaning:** One or more critical features are stale/not updated for current decision tick.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

---

## A.9 Module-Specific / Optional Advisory-to-Hard Blocks

### `BLOCK_FRESH_FVG_COOLOFF`
- **Module:** FVG modules (defensive/session/basic)
- **Meaning:** Fresh qualifying FVG against bias/regime triggered cooloff until mitigation/reclaim.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard (if enabled)

### `BLOCK_SESSION_FVG_PAUSE`
- **Module:** Session FVG
- **Meaning:** Session pause bars active after new session FVG print.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_INSIDE_SESSION_FVG`
- **Module:** Session FVG
- **Meaning:** Price is inside active session FVG and required override conditions (RSI/rVol/avg-cross) not met.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_HVP_EXPANDING`
- **Module:** HVP gate
- **Meaning:** Historical volatility proxy (`HVP >= HVPSMA`) plus expansion state blocks new build/start.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard

### `BLOCK_LIQ_SWEEP_OPPOSITE_STRUCTURE`
- **Module:** liquidity sweep veto (optional)
- **Meaning:** Opposite-side sweep structure overlaps/conflicts with box within disallowed distance.
- **Applies to:** `START`, `REBUILD`
- **Severity:** hard (if enabled)

---

# B) STOP_* (runtime stop triggers)

## B.1 Core Breakout / Fast Move / Range Shift

### `STOP_BREAKOUT_2STRIKE_UP`
- **Module:** STOP framework (2-strike breakout)
- **Meaning:** Upward breakout confirmed by 2-strike logic beyond box/structure.
- **Applies to:** running grid
- **Severity:** hard

### `STOP_BREAKOUT_2STRIKE_DN`
- **Module:** STOP framework (2-strike breakout)
- **Meaning:** Downward breakout confirmed by 2-strike logic beyond box/structure.
- **Applies to:** running grid
- **Severity:** hard

### `STOP_FAST_MOVE_UP`
- **Module:** fast-stop override
- **Meaning:** Price moved > configured threshold (e.g., >1 step) outside upper edge; fast stop path triggered.
- **Applies to:** running grid
- **Severity:** hard

### `STOP_FAST_MOVE_DN`
- **Module:** fast-stop override
- **Meaning:** Price moved > configured threshold (e.g., >1 step) outside lower edge; fast stop path triggered.
- **Applies to:** running grid
- **Severity:** hard

### `STOP_RANGE_SHIFT`
- **Module:** range shift detector
- **Meaning:** Material range/box shift beyond threshold (e.g., >0.7%) invalidates current grid.
- **Applies to:** running grid
- **Severity:** hard

### `STOP_FRESH_STRUCTURE`
- **Module:** fresh structure event router
- **Meaning:** New structure event (breakout/channel/FVG/session conflict, etc.) invalidates running grid.
- **Applies to:** running grid
- **Severity:** hard

---

## B.2 Squeeze / Channel / Regime-Driven Overrides

### `STOP_SQUEEZE_RELEASE_AGAINST`
- **Module:** squeeze state gate
- **Meaning:** Squeeze release occurred against active box bias with strong move condition; immediate stop override.
- **Applies to:** running grid
- **Severity:** hard

### `STOP_CHANNEL_STRONG_BREAK`
- **Module:** smart breakout channel / Donchian strong-break
- **Meaning:** Strong close breakout beyond channel bound confirms regime break; stop triggered.
- **Applies to:** running grid
- **Severity:** hard

### `STOP_OS_DEV_DIRECTIONAL_FLIP`
- **Module:** Range DI / deviation-pivot regime
- **Meaning:** `os_dev` flipped to directional state while running, triggering idle/stop policy.
- **Applies to:** running grid
- **Severity:** hard (if enabled)

### `STOP_META_DRIFT_HARD`
- **Module:** meta drift guard
- **Meaning:** Hard change-point/drift condition detected; stop/risk-off action required.
- **Applies to:** running grid
- **Severity:** hard

---

## B.3 Structure / VAP / Void / Liquidity-Based Stops

### `STOP_LVN_VOID_EXIT_ACCEL`
- **Module:** micro-VAP / LVN corridor logic
- **Meaning:** Breakout exited through LVN/void corridor; accelerated stop allowed/triggered.
- **Applies to:** running grid
- **Severity:** hard (if enabled)

### `STOP_FVG_VOID_CONFLUENCE`
- **Module:** FVG + LVN/FVG-VP stop override
- **Meaning:** Breakout into low-volume/FVG vacuum confluence triggers immediate stop.
- **Applies to:** running grid
- **Severity:** hard (if enabled)

### `STOP_LIQUIDITY_SWEEP_BREAK_RETEST`
- **Module:** liquidity sweeps
- **Meaning:** Break-and-retest sweep through box edge confirms invalidation; stop precedence.
- **Applies to:** running grid
- **Severity:** hard

### `STOP_SESSION_FVG_AGAINST_BIAS`
- **Module:** Session FVG
- **Meaning:** Fresh session FVG printed against active bias and policy requires idle/stop.
- **Applies to:** running grid
- **Severity:** hard

### `STOP_MRVD_AVG_BREAK`
- **Module:** FVG positioning averages / average-break stop (optional)
- **Meaning:** Confirmed break of positioning average threshold signals regime break.
- **Applies to:** running grid
- **Severity:** hard (if enabled)

---

## B.4 Protections / Risk / Execution Stops

### `STOP_DRAWDOWN_GUARD`
- **Module:** protections layer
- **Meaning:** Drawdown guard forced stop/risk reduction.
- **Applies to:** running grid
- **Severity:** hard

### `STOP_EXEC_CONFIRM_EXIT_FAILSAFE`
- **Module:** confirm-exit hook / executor safety
- **Meaning:** Exit confirmation/risk logic escalated to fail-safe stop behavior.
- **Applies to:** running grid / executor
- **Severity:** hard

### `STOP_DATA_QUARANTINE`
- **Module:** data quality quarantine state
- **Meaning:** Data entered quarantine state while running; stop/no-new-orders policy triggered.
- **Applies to:** running grid
- **Severity:** hard

---

# C) REPLAN_* (plan inertia / materiality / epoch policy)

## C.1 Primary Replan Outcomes

### `REPLAN_NOOP_MINOR_DELTA`
- **Module:** replan policy / materiality governor
- **Meaning:** New plan candidate differs only by non-material deltas; no executor-facing change.
- **Applies to:** Brain -> Executor handoff
- **Severity:** advisory (decision output)

### `REPLAN_SOFT_ADJUST_ONLY`
- **Module:** replan policy
- **Meaning:** Only soft-adjust fields are updated (e.g., TP/SL/runtime hints/confidence); no ladder rebuild.
- **Applies to:** Brain -> Executor handoff
- **Severity:** advisory

### `REPLAN_MATERIAL_BOX_CHANGE`
- **Module:** replan policy
- **Meaning:** Box/range changes exceed materiality threshold; rebuild path required.
- **Applies to:** Brain -> Executor handoff
- **Severity:** hard for ladder reconcile

### `REPLAN_MATERIAL_GRID_CHANGE`
- **Module:** replan policy
- **Meaning:** `N` / step / ladder geometry changed materially; rebuild path required.
- **Applies to:** Brain -> Executor handoff
- **Severity:** hard for ladder reconcile

### `REPLAN_MATERIAL_RISK_CHANGE`
- **Module:** replan policy
- **Meaning:** TP/SL/risk policy changed beyond soft-adjust thresholds; material rebuild or risk reconcile required.
- **Applies to:** Brain -> Executor handoff
- **Severity:** configurable (soft/hard depending policy)

### `REPLAN_HARD_STOP_OVERRIDE`
- **Module:** replan policy + stop override integration
- **Meaning:** Candidate plan is superseded by a hard-stop event; immediate stop action.
- **Applies to:** Brain -> Executor handoff
- **Severity:** hard

---

## C.2 Replan Timing / Epoch / Idempotency Context

### `REPLAN_EPOCH_DEFERRED`
- **Module:** replan policy epoch scheduler
- **Meaning:** Candidate plan changes are deferred until next epoch boundary (no safety override present).
- **Applies to:** Brain internal decisioning
- **Severity:** advisory

### `REPLAN_DEFERRED_ACTIVE_FILL_WINDOW`
- **Module:** replan policy / runtime coordination
- **Meaning:** Material update deferred due to active fill/reconciliation window, unless hard safety event occurs.
- **Applies to:** Brain/Executor coordination
- **Severity:** advisory

### `REPLAN_DUPLICATE_PLAN_HASH`
- **Module:** atomic handoff / idempotency
- **Meaning:** Candidate plan hash matches previous applied material plan; no re-publication/apply needed.
- **Applies to:** publish/apply pipeline
- **Severity:** advisory

---

# D) PAUSE_* (explicit pause / quarantine / cooloff states)

### `PAUSE_DATA_QUARANTINE`
- **Module:** planner health state machine
- **Meaning:** Planner entered quarantine due to data integrity issues; only HOLD/STOP allowed.
- **Applies to:** planner state
- **Severity:** hard

### `PAUSE_DATA_DEGRADED`
- **Module:** planner health state machine
- **Meaning:** Planner health is degraded; hold/stop allowed, new starts/rebuilds blocked.
- **Applies to:** planner state
- **Severity:** hard

### `PAUSE_META_DRIFT_SOFT`
- **Module:** meta drift guard
- **Meaning:** Soft drift detected; planner pauses starts/rebuilds until drift clears.
- **Applies to:** planner state
- **Severity:** hard (for starts/rebuilds)

### `PAUSE_BBWP_COOLOFF`
- **Module:** BBWP cooloff state
- **Meaning:** BBWP extreme cooloff active.
- **Applies to:** planner state
- **Severity:** hard

### `PAUSE_SESSION_FVG`
- **Module:** Session FVG pause bars
- **Meaning:** Session FVG pause bars active after fresh print.
- **Applies to:** planner state
- **Severity:** hard

### `PAUSE_EXECUTION_UNSAFE`
- **Module:** execution confirm hooks / capacity guard
- **Meaning:** Planner or executor is pausing new placement due to execution safety conditions.
- **Applies to:** planner/executor runtime
- **Severity:** hard for new placements

---

# E) WARN_* (non-blocking warnings)

### `WARN_COST_MODEL_STALE`
- **Module:** empirical cost calibrator integration
- **Meaning:** Empirical cost model is stale/unavailable; static cost model is used.
- **Applies to:** planner
- **Severity:** advisory

### `WARN_CVD_DATA_QUALITY_LOW`
- **Module:** CVD modules
- **Meaning:** CVD source quality is insufficient/degraded; CVD signals downgraded or ignored.
- **Applies to:** planner/simulator
- **Severity:** advisory

### `WARN_VRVP_UNAVAILABLE_FALLBACK_POC`
- **Module:** VP/POC module
- **Meaning:** VRVP unavailable; fallback POC estimator is used.
- **Applies to:** planner
- **Severity:** advisory

### `WARN_FEATURE_FALLBACK_USED`
- **Module:** feature pipeline
- **Meaning:** A non-critical feature/module failed and fallback logic was used.
- **Applies to:** planner/simulator
- **Severity:** advisory

### `WARN_EXEC_POST_ONLY_RETRY_HIGH`
- **Module:** executor maker-first layer
- **Meaning:** Post-only retry rate exceeded warning threshold.
- **Applies to:** executor
- **Severity:** advisory

### `WARN_EXEC_REPRICE_RATE_HIGH`
- **Module:** executor reconcile/reprice
- **Meaning:** Reprice/cancel-replace rate is elevated (churn risk).
- **Applies to:** executor
- **Severity:** advisory

### `WARN_PLAN_EXPIRES_SOON`
- **Module:** atomic plan handoff
- **Meaning:** Plan is near expiry and may be superseded before full application.
- **Applies to:** executor
- **Severity:** advisory

### `WARN_PARTIAL_DATA_WINDOW`
- **Module:** data loader / replay harness
- **Meaning:** Decision computed with shorter-than-ideal warmup/lookback due to edge-of-range data.
- **Applies to:** planner/simulator
- **Severity:** advisory

---

# F) EXEC_* (executor actions / runtime controls / idempotency)

## F.1 Plan Intake / Idempotency / Schema

### `EXEC_PLAN_SCHEMA_INVALID`
- **Module:** executor plan intake
- **Meaning:** Incoming plan JSON failed schema validation.
- **Applies to:** executor
- **Severity:** hard

### `EXEC_PLAN_HASH_MISMATCH`
- **Module:** executor plan intake / signature validation
- **Meaning:** Plan hash does not match recomputed hash of material fields.
- **Applies to:** executor
- **Severity:** hard

### `EXEC_PLAN_DUPLICATE_IGNORED`
- **Module:** executor idempotency
- **Meaning:** Plan has already been applied (`plan_id` duplicate or same `decision_seq`/hash).
- **Applies to:** executor
- **Severity:** advisory

### `EXEC_PLAN_STALE_SEQ_IGNORED`
- **Module:** executor idempotency
- **Meaning:** Incoming plan `decision_seq` is stale (`<= last_applied_seq`); ignored.
- **Applies to:** executor
- **Severity:** advisory

### `EXEC_PLAN_EXPIRED_IGNORED`
- **Module:** executor plan validity
- **Meaning:** Plan `expires_at` is passed; ignored.
- **Applies to:** executor
- **Severity:** advisory or hard (configurable)

### `EXEC_PLAN_APPLIED`
- **Module:** executor plan intake
- **Meaning:** Plan successfully accepted and applied.
- **Applies to:** executor
- **Severity:** info/advisory

---

## F.2 Ladder / Reconcile / Capacity Controls

### `EXEC_RECONCILE_START_LADDER_CREATED`
- **Module:** executor reconcile
- **Meaning:** New ladder seeded/placed from START plan.
- **Applies to:** executor
- **Severity:** info/advisory

### `EXEC_RECONCILE_HOLD_NO_MATERIAL_CHANGE`
- **Module:** executor reconcile
- **Meaning:** HOLD / no-op due to no material ladder changes.
- **Applies to:** executor
- **Severity:** advisory

### `EXEC_RECONCILE_MATERIAL_REBUILD`
- **Module:** executor reconcile
- **Meaning:** Material rebuild applied to ladder/orders.
- **Applies to:** executor
- **Severity:** advisory

### `EXEC_RECONCILE_STOP_CANCELLED_LADDER`
- **Module:** executor reconcile
- **Meaning:** STOP plan caused ladder cancellation / shutdown sequence.
- **Applies to:** executor
- **Severity:** advisory

### `EXEC_CAPACITY_RUNG_CAP_APPLIED`
- **Module:** capacity guard
- **Meaning:** Active rung count was capped due to depth/spread capacity constraints.
- **Applies to:** executor
- **Severity:** advisory (runtime action)

### `EXEC_CAPACITY_NOTIONAL_CAP_APPLIED`
- **Module:** capacity guard
- **Meaning:** Per-rung or aggregate notional was reduced due to capacity constraints.
- **Applies to:** executor
- **Severity:** advisory (runtime action)

### `EXEC_CONFIRM_START_FAILED`
- **Module:** confirm-entry hook
- **Meaning:** Start placement prevented by execution safety checks.
- **Applies to:** executor
- **Severity:** hard

### `EXEC_CONFIRM_REBUILD_FAILED`
- **Module:** confirm-rebuild hook
- **Meaning:** Rebuild placement prevented by execution safety checks.
- **Applies to:** executor
- **Severity:** hard

### `EXEC_CONFIRM_EXIT_FAILSAFE`
- **Module:** confirm-exit hook
- **Meaning:** Exit confirmation escalated to fail-safe stop behavior.
- **Applies to:** executor
- **Severity:** hard

---

## F.3 Maker-First / Placement / Lifecycle

### `EXEC_POST_ONLY_RETRY`
- **Module:** maker-first placement wrapper
- **Meaning:** Post-only placement required retry/backoff.
- **Applies to:** executor
- **Severity:** advisory

### `EXEC_POST_ONLY_FALLBACK_REPRICE`
- **Module:** maker-first placement wrapper
- **Meaning:** Placement moved to bounded reprice after post-only failure.
- **Applies to:** executor
- **Severity:** advisory

### `EXEC_ORDER_TIMEOUT_REPRICE`
- **Module:** order timeout + selective reprice
- **Meaning:** Timed-out order was repriced/replaced per policy.
- **Applies to:** executor
- **Severity:** advisory

### `EXEC_ORDER_CANCEL_REPLACE_APPLIED`
- **Module:** reconcile engine
- **Meaning:** Cancel/replace action performed on ladder order(s).
- **Applies to:** executor
- **Severity:** advisory

### `EXEC_FILL_REPLACEMENT_PLACED`
- **Module:** replace-on-fill loop
- **Meaning:** New order placed to maintain ladder after a fill.
- **Applies to:** executor
- **Severity:** advisory

### `EXEC_FILL_DUPLICATE_GUARD_HIT`
- **Module:** fill dedupe / last-signal-index guard
- **Meaning:** Duplicate/repeated fill event was ignored by no-repeat guard.
- **Applies to:** executor / simulator
- **Severity:** advisory

---

# G) EVENT_* (event bus taxonomy)

> These are **events**, not necessarily blockers/stops. They may later map to blockers, nudges, or STOP actions depending on policy.

## G.1 Acceptance / Retests / Range Events

### `EVENT_POC_TEST`
- POC crossed/tested (generic)

### `EVENT_POC_ACCEPTANCE_CROSS`
- POC acceptance condition satisfied for current box generation

### `EVENT_EXTREME_RETEST_TOP`
- Range/box top extreme retest detected

### `EVENT_EXTREME_RETEST_BOTTOM`
- Range/box bottom extreme retest detected

### `EVENT_EXT_1386_RETEST_TOP`
- 1.386 extension retest top-side

### `EVENT_EXT_1386_RETEST_BOTTOM`
- 1.386 extension retest bottom-side

### `EVENT_RANGE_HIT_TOP`
- Generic range-hit event mapped to bearish/top extreme context

### `EVENT_RANGE_HIT_BOTTOM`
- Generic range-hit event mapped to bullish/bottom extreme context

---

## G.2 Structure Breakouts / Reclaims / Channels

### `EVENT_BREAKOUT_BULL`
- Local bullish breakout detected (bar-confirmed)

### `EVENT_BREAKOUT_BEAR`
- Local bearish breakout detected (bar-confirmed)

### `EVENT_RECLAIM_CONFIRMED`
- Reclaim condition confirmed after stop/fresh breakout

### `EVENT_CHANNEL_STRONG_BREAK_UP`
- Strong breakout above channel bound

### `EVENT_CHANNEL_STRONG_BREAK_DN`
- Strong breakout below channel bound

### `EVENT_CHANNEL_MIDLINE_TOUCH`
- Channel midline touch event

### `EVENT_DONCHIAN_STRONG_BREAK_UP`
- Strong close above Donchian bound

### `EVENT_DONCHIAN_STRONG_BREAK_DN`
- Strong close below Donchian bound

### `EVENT_DRIFT_RETEST_UP`
- Drift-envelope retest (upper) event

### `EVENT_DRIFT_RETEST_DN`
- Drift-envelope retest (lower) event

---

## G.3 Liquidity Sweeps / Session High-Low

### `EVENT_SWEEP_WICK_HIGH`
- Wick-only sweep of swing/session high

### `EVENT_SWEEP_WICK_LOW`
- Wick-only sweep of swing/session low

### `EVENT_SWEEP_BREAK_RETEST_HIGH`
- Break-and-retest sweep through high / upper edge

### `EVENT_SWEEP_BREAK_RETEST_LOW`
- Break-and-retest sweep through low / lower edge

### `EVENT_SESSION_HIGH_SWEEP`
- Daily/session high sweep event

### `EVENT_SESSION_LOW_SWEEP`
- Daily/session low sweep event

---

## G.4 FVG / OB / Session FVG / Mitigation

### `EVENT_FVG_NEW_BULL`
- New bullish FVG printed (qualifying per size/quality if configured)

### `EVENT_FVG_NEW_BEAR`
- New bearish FVG printed

### `EVENT_FVG_MITIGATED_BULL`
- Bullish FVG mitigated/tagged

### `EVENT_FVG_MITIGATED_BEAR`
- Bearish FVG mitigated/tagged

### `EVENT_IMFVG_AVG_TAG_BULL`
- Bullish IMFVG average tagged/mitigated

### `EVENT_IMFVG_AVG_TAG_BEAR`
- Bearish IMFVG average tagged/mitigated

### `EVENT_SESSION_FVG_NEW`
- New session FVG created (daily session boundary)

### `EVENT_SESSION_FVG_MITIGATED`
- Active session FVG mitigated

### `EVENT_OB_NEW_BULL`
- New bullish order block cached

### `EVENT_OB_NEW_BEAR`
- New bearish order block cached

### `EVENT_OB_TAGGED_BULL`
- Bullish OB edge/midline tagged

### `EVENT_OB_TAGGED_BEAR`
- Bearish OB edge/midline tagged

---

## G.5 VAP / VP / HVN-LVN / Volume Structure

### `EVENT_VRVP_POC_SHIFT`
- VRVP POC shifted materially

### `EVENT_MICRO_POC_SHIFT`
- Micro-POC inside box shifted materially

### `EVENT_HVN_TOUCH`
- HVN touch event inside/near box

### `EVENT_LVN_TOUCH`
- LVN touch event inside/near box

### `EVENT_LVN_VOID_EXIT`
- Price exited via LVN/void corridor

### `EVENT_FVG_POC_TAG`
- FVG-VP POC tagged (if module enabled)

---

## G.6 CVD / Flow / Volatility / Drift

### `EVENT_CVD_BULL_DIV`
- Bullish CVD divergence detected

### `EVENT_CVD_BEAR_DIV`
- Bearish CVD divergence detected

### `EVENT_CVD_BOS_UP`
- CVD-based BOS up event

### `EVENT_CVD_BOS_DN`
- CVD-based BOS down event

### `EVENT_CVD_SPIKE_POS`
- Positive CVD divergence spike / >2σ event

### `EVENT_CVD_SPIKE_NEG`
- Negative CVD divergence spike / >2σ event

### `EVENT_PASSIVE_ABSORPTION_UP`
- Passive absorption pattern (price up, CVD down) detected

### `EVENT_PASSIVE_ABSORPTION_DN`
- Passive absorption pattern (price down, CVD up) detected

### `EVENT_META_DRIFT_SOFT`
- Meta drift guard soft detection event

### `EVENT_META_DRIFT_HARD`
- Meta drift guard hard detection event

### `EVENT_BBWP_EXTREME`
- BBWP extreme reached (cooloff trigger event)

### `EVENT_SQUEEZE_RELEASE_UP`
- Squeeze release detected up

### `EVENT_SQUEEZE_RELEASE_DN`
- Squeeze release detected down

---

## G.7 Execution Safety / Runtime Events

### `EVENT_SPREAD_SPIKE`
- Spread exceeded warning/hard thresholds

### `EVENT_DEPTH_THIN`
- Orderbook depth thinning detected

### `EVENT_JUMP_DETECTED`
- Sudden jump / price discontinuity condition detected

### `EVENT_POST_ONLY_REJECT_BURST`
- Burst of post-only rejects detected

### `EVENT_DATA_GAP_DETECTED`
- Data gap detected (input/runtime)

### `EVENT_DATA_MISALIGN_DETECTED`
- Multi-TF alignment issue detected

---

# H) INFO_* (optional informational codes)

> Optional category for observability without action semantics.
> Use sparingly to avoid log spam.

### `INFO_VOL_BUCKET_CHANGED`
- Volatility policy adapter bucket changed (e.g., `normal -> elevated`)

### `INFO_BOX_SHIFT_APPLIED`
- Box shift applied (e.g., toward POC) but build remained valid

### `INFO_TARGET_SOURCE_SELECTED`
- Final TP source selected from candidate framework

### `INFO_SL_SOURCE_SELECTED`
- Final SL source selected from candidate framework

### `INFO_REPLAN_EPOCH_BOUNDARY`
- Replan epoch boundary hit and candidate evaluation executed

---

## Deprecation Policy

If a code should no longer be used:

1. Mark it as deprecated here (do not silently delete).
2. Add replacement code(s).
3. Update enums and analytics mapping.
4. Keep backward compatibility in parsers for historical logs.

Suggested format:

- `DEPRECATED: BLOCK_OLD_NAME` → use `BLOCK_NEW_NAME`

---

## Implementation Checklist (for Codex / developers)

When implementing a new module or changing decision logic:

- [ ] Reuse existing code(s) if semantics match
- [ ] If new semantics are introduced, add canonical code(s) here
- [ ] Add/update enum(s) in `core/enums.py`
- [ ] Emit code(s) in planner/sim/executor logs as structured fields
- [ ] Add/adjust tests covering emitted code(s)
- [ ] Update experiment analytics grouping if needed
- [ ] Update master plan/docs if the feature changed decision semantics

---

## Recommended Companion Files

- `core/enums.py` (Enum definitions mirroring this file)
- `schemas/grid_plan.schema.json` (fields like `blockers`, `action_reason`, `warnings`, `events_recent`)
- `docs/GRID_MASTER_PLAN.md`
- `docs/REPLAN_POLICY_AND_MATERIALITY.md`
- `docs/ATOMIC_PLAN_HANDOFF.md`

---

## Prompting Note for Codex (copy/paste into tasks)

Use only reason/event codes defined in `docs/DECISION_REASON_CODES.md` (and `core/enums.py`).  
Do not invent ad-hoc strings.  
If new logic requires a new reason/event code, update both files and include the change in the patch.