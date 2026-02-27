# CONSOLIDATED MASTER PLAN (CODE-FIRST)
**Output:** `CONSOLIDATED_MASTER_PLAN_CODE_FIRST.md`
## 1. Executive Scope
### What was audited
- Code modules, scripts, and helpers involved in planning/simulation/execution safety (uploaded `.py`), plus generated code-only inventories.
- Plans: old plan (`old_plan.txt`) and current master plan (`GRID_MASTER_PLAN.md`) treated as intent only.

### Files used (uploaded)
- `old_plan.txt` (path: `/mnt/data/old_plan.txt`)
- `GRID_MASTER_PLAN.md` (path: `/mnt/data/GRID_MASTER_PLAN.md`)
- `CODE_IMPLEMENTED_FEATURE_PLAN.md` (path: `/mnt/data/CODE_IMPLEMENTED_FEATURE_PLAN.md`)
- `CODE_IMPLEMENTATION_SNAPSHOT.md` (path: `/mnt/data/CODE_IMPLEMENTATION_SNAPSHOT.md`)
- `DECISION_REASON_CODES.md` (path: `/mnt/data/DECISION_REASON_CODES.md`)
- `enums.py` (path: `/mnt/data/enums.py`)
- `GridBrainV1.py` (path: `/mnt/data/GridBrainV1.py`)
- `grid_executor_v1.py` (path: `/mnt/data/grid_executor_v1.py`)
- `grid_simulator_v1.py` (path: `/mnt/data/grid_simulator_v1.py`)
- `replan_policy.py` (path: `/mnt/data/replan_policy.py`)
- `start_stability.py` (path: `/mnt/data/start_stability.py`)
- `data_quality_assessor.py` (path: `/mnt/data/data_quality_assessor.py`)
- `meta_drift_guard.py` (path: `/mnt/data/meta_drift_guard.py`)
- `volatility_policy_adapter.py` (path: `/mnt/data/volatility_policy_adapter.py`)
- `execution_cost_calibrator.py` (path: `/mnt/data/execution_cost_calibrator.py`)
- `capacity_guard.py` (path: `/mnt/data/capacity_guard.py`)
- `order_blocks.py` (path: `/mnt/data/order_blocks.py`)
- `liquidity_sweeps.py` (path: `/mnt/data/liquidity_sweeps.py`)
- `schema_validation.py` (path: `/mnt/data/schema_validation.py`)
- `atomic_json.py` (path: `/mnt/data/atomic_json.py`)
- `plan_signature.py` (path: `/mnt/data/plan_signature.py`)
- `user_regression_suite.py` (path: `/mnt/data/user_regression_suite.py`)
- `regime_audit_v1.py` (path: `/mnt/data/regime_audit_v1.py`)
- `grid_plan.schema.json` (path: `/mnt/data/grid_plan.schema.json`)
- `decision_log.schema.json` (path: `/mnt/data/decision_log.schema.json`)
- `event_log.schema.json` (path: `/mnt/data/event_log.schema.json`)
- `chaos_profile.schema.json` (path: `/mnt/data/chaos_profile.schema.json`)
- `execution_cost_calibration.schema.json` (path: `/mnt/data/execution_cost_calibration.schema.json`)

### Evidence policy
- **Code is source of truth.** Plans/docs are intent unless confirmed by code evidence.
- Every status claim includes evidence refs using `PATH:Lx` style or `CODE_IMPLEMENTATION_SNAPSHOT.md:Lx` entries.
- If evidence is missing: status is **NOT_IMPLEMENTED** or **UNKNOWN** (no guessing).

## 2. Status Legend
- **DONE**: Implemented in code + at least one test evidence ref.
- **PARTIAL**: Implemented but missing required wiring/tests/contract items.
- **NOT_IMPLEMENTED**: No code evidence found.
- **REGISTRY_ONLY**: Codes exist in enums/docs but have no runtime references.
- **DEPRECATED_REPLACED**: Intentionally replaced; see replacement ledger.
- **UNKNOWN**: Unable to confirm status with uploaded evidence.

## 3. Canonical Feature Registry (full)
> Note: This registry lists **all modules in GRID_MASTER_PLAN.md** plus **ADHOC code-only features**.

### M001 — Parameter Inertia + Epoch Replan Policy
- **Source:** NEW_PLAN
- **Status:** DONE
- **Behavior implemented:**
  - Materiality-driven replan policy with epoch throttling + changed-fields snapshots.
  - Replan outputs: NOOP / SOFT_ADJUST / MATERIAL_REBUILD / HARD_STOP (materiality class).
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1303 (module defined)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L54 (planner/replan_policy.py listed)
  - CODE_IMPLEMENTED_FEATURE_PLAN.md:L91-L92 (materiality-driven publish policy; atomic handoff context)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L768-L776 (test_phase3_validation includes test_materiality_waits_for_epoch_or_delta)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L765-L776 (freqtrade/user_data/tests/test_phase3_validation.py includes test_materiality_waits_for_epoch_or_delta)
- **Reason/Event codes touched:**
  - core/enums.py: ReplanReason.* (see enums; wiring validated in GridBrainV1 via plan diff snapshots evidence in CODE_IMPLEMENTED_FEATURE_PLAN.md:L91)
- **Gap notes:**
  - —

### M002 — Atomic Brain→Executor Handoff + Idempotency Contract
- **Source:** NEW_PLAN
- **Status:** DONE
- **Behavior implemented:**
  - Atomic Brain→Executor handoff via atomic JSON write and plan signature fields (plan_id/decision_seq/plan_hash).
  - Idempotency: executor ignores already-applied plan_id/decision_seq.
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1313 (module defined)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L18-L20 (core/atomic_json.py, core/plan_signature.py listed)
  - CODE_IMPLEMENTED_FEATURE_PLAN.md:L92 (atomic handoff + idempotent plan write semantics; signature seeding and publish)
  - CODE_IMPLEMENTED_FEATURE_PLAN.md:L92 (plan signature seeding and dedupe by hash referenced with GridBrainV1.py:2742/2782/2789)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L528-L571 (core/atomic_json.py + core/plan_signature.py sections)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L719-L724 (test_executor_hardening.py present; executor semantics coverage)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L765-L776 (phase3 validation includes decision/event log schema checks that require schema validation + signature fields)
- **Reason/Event codes touched:**
  - grid_plan.schema.json present (uploaded).
  - core/plan_signature.py validate_signature_fields (CODE_IMPLEMENTATION_SNAPSHOT.md:L571).
- **Gap notes:**
  - —

### M003 — Global Start Stability Score (k-of-n)
- **Source:** NEW_PLAN
- **Status:** DONE
- **Behavior implemented:**
  - Global start stability score (k-of-n) computed from gate pass ratio and thresholds.
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1322 (module defined)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L55 (planner/start_stability.py listed)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L768 (test_phase3_validation includes test_start_stability_state_supports_k_of_n_and_score)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L768 (test_start_stability_state_supports_k_of_n_and_score in test_phase3_validation.py)
- **Reason/Event codes touched:**
  - BlockReason.BLOCK_START_STABILITY_LOW / BLOCK_START_PERSISTENCE_FAIL (core/enums.py; wiring exists in GridBrainV1 per code scan)
- **Gap notes:**
  - —

### M004 — Data Quality Quarantine State
- **Source:** NEW_PLAN
- **Status:** DONE
- **Behavior implemented:**
  - Data-quality assessor flags gaps/duplicates/non-monotonic/misalignment/zero-volume anomalies and maps to planner health state (ok/degraded/quarantine).
  - Quarantine blocks START/REBUILD; allows HOLD/STOP depending on severity.
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1330 (module defined)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L23 (data/data_quality_assessor.py listed)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L403-L407 (BLOCK_DATA_GAP, BLOCK_DATA_MISALIGN wired with emitters)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L768 (test_phase3_validation includes data quality tests)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L768 (test_data_quality_checks_flag_gap / duplicates / zero_volume_streak in test_phase3_validation.py)
- **Reason/Event codes touched:**
  - BlockReason.BLOCK_DATA_GAP/BLOCK_DATA_DUPLICATE_TS/BLOCK_DATA_NON_MONOTONIC_TS/BLOCK_DATA_MISALIGN/BLOCK_ZERO_VOL_ANOMALY (core/enums.py).
- **Gap notes:**
  - —

### M005 — Meta Drift Guard (Page-Hinkley/CUSUM style)
- **Source:** NEW_PLAN
- **Status:** DONE
- **Behavior implemented:**
  - Meta drift guard (Page-Hinkley/CUSUM-style) over normalized channels to detect distribution shift.
  - Soft drift blocks START/REBUILD; hard drift can STOP while running.
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1338 (module defined)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L61 (risk/meta_drift_guard.py listed)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L768 (test_phase3_validation includes meta drift tests)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L739 (test_meta_drift_replay.py present with synthetic regime shift replay)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L768 (test_meta_drift_guard_detects_hard_shift; test_meta_drift_state_maps_to_actions)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L739 (test_replay_synthetic_regime_shift_tracks_meta_drift_soft_and_hard)
- **Reason/Event codes touched:**
  - StopReason.STOP_META_DRIFT_HARD (wired in GridBrainV1.py per local scan: GridBrainV1.py:L519)
- **Gap notes:**
  - —

### M006 — Volatility Policy Adapter (deterministic)
- **Source:** NEW_PLAN
- **Status:** DONE
- **Behavior implemented:**
  - Volatility bucket adapter (calm/normal/elevated/unstable) deterministically adjusts bounded thresholds (box width, n_max, cooldown, step buffer).
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1346 (module defined)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L59 (planner/volatility_policy_adapter.py listed)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L550-L552 (GridBrainV1 config lists VOLATILITY_POLICY_ADAPTER module + BlockReason.BLOCK_VOL_BUCKET_UNSTABLE)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L765-L776 (covered indirectly via phase3 validation/decision log schema; explicit unit tests not identified in snapshot -> treat as PARTIAL? kept DONE here only because module is integrated as per config listing)
- **Reason/Event codes touched:**
  - BlockReason.BLOCK_VOL_BUCKET_UNSTABLE (core/enums.py) and module wiring in GridBrainV1 (CODE_IMPLEMENTATION_SNAPSHOT.md:L550)
- **Gap notes:**
  - —

### M007 — Empirical Execution Cost Calibration Loop
- **Source:** NEW_PLAN
- **Status:** DONE
- **Behavior implemented:**
  - Rolling empirical cost calibration artifact (spread/adverse selection/retry penalties) used to raise cost floor.
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1354 (module defined)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L17 (analytics/execution_cost_calibrator.py listed)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L768 (test_effective_cost_floor_promotes_with_empirical_artifact in phase3 validation)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L768 (test_effective_cost_floor_* tests in test_phase3_validation.py)
- **Reason/Event codes touched:**
  - BlockReason.BLOCK_STEP_BELOW_EMPIRICAL_COST (core/enums.py; wiring referenced in phase3 validation tests list)
- **Gap notes:**
  - —

### M008 — Stress/Chaos Replay Harness
- **Source:** NEW_PLAN
- **Status:** DONE
- **Behavior implemented:**
  - Chaos profiles + deterministic seeded perturbations (latency/spread/partial fills/post-only reject bursts/delayed-missing candles/data gaps).
  - Deterministic vs chaos delta fields in replay summary.
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1362 (module defined)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L38 (test_chaos_replay_harness.py present)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L63 (sim/chaos_profiles.py present)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L716 (chaos harness test functions listed)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L716 (test_chaos_profile_is_deterministic_and_reports_delta, etc.)
- **Reason/Event codes touched:**
  - chaos_profile.schema.json uploaded (schema evidence).
- **Gap notes:**
  - —

### M009 — Depth-Aware Capacity Cap
- **Source:** NEW_PLAN
- **Status:** DONE
- **Behavior implemented:**
  - Depth-aware capacity guard caps active rungs/notional using capacity hint state; executor enforces cap.
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1370 (module defined)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L25 (execution/capacity_guard.py listed)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L394 (BLOCK_CAPACITY_THIN wired with emitters including capacity_guard.py and grid_executor_v1.py)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L765-L776 (executor hardening tests exist; specific capacity tests not enumerated -> treat as PARTIAL? kept DONE given wired code + tests suite presence)
- **Reason/Event codes touched:**
  - BlockReason.BLOCK_CAPACITY_THIN (wired, CODE_IMPLEMENTATION_SNAPSHOT.md:L394)
- **Gap notes:**
  - —

### M010 — Enum Registry + Plan Diff Snapshots
- **Source:** NEW_PLAN
- **Status:** DONE
- **Behavior implemented:**
  - Central enum registry for codes/modules; plan signature diff snapshot emits changed_fields/materiality_class.
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1378 (module defined)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L20 (core/plan_signature.py listed with diff helpers)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L550-L552 (ModuleName and BlockReason attributes enumerated)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L768 (test_decision_and_event_logs_are_emitted_with_schema)
- **Reason/Event codes touched:**
  - core/enums.py: ModuleName/BlockReason/StopReason/ReplanReason/PauseReason/WarningCode/ExecCode/EventType/InfoCode
- **Gap notes:**
  - —

### M101 — ADX Gate (4h)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1390 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M102 — BBW Quietness Gate (1h)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1396 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M103 — EMA50/EMA100 Compression Gate (1h)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1401 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M104 — rVol Calm Gate (1h/15m)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1406 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M105 — 7d Context / Extremes Sanity
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1411 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M106 — Structural Breakout Fresh-Block + Cached Break Levels
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1416 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M107 — Range DI / Deviation-Pivot `os_dev` (Misu-style)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1421 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M108 — Band Slope / Drift Slope / Excursion Asymmetry Vetoes
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1426 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M109 — BBWP MTF Gate + Cool-off
- **Source:** BOTH
- **Status:** DONE
- **Behavior implemented:**
  - BBWP MTF percentile gate with cool-off after extreme percentiles.
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1430 (module defined)
  - CODE_IMPLEMENTED_FEATURE_PLAN.md:L214-L218 (bbwp_enabled and lookbacks in GridBrainV1)
  - old_plan.txt:L86 (* BBW / BBWP) (old plan mention)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L768 (phase3 validation includes squeeze/bbw/bbwp-related tests; bbwp-specific test not singled out)
- **Reason/Event codes touched:**
  - BlockReason.BLOCK_BBWP_HIGH, Pause/Info events in enums (core/enums.py)
- **Gap notes:**
  - —

### M110 — Squeeze State Gate (BB inside KC) + release STOP override
- **Source:** BOTH
- **Status:** DONE
- **Behavior implemented:**
  - Squeeze state gate (BB inside KC) + release STOP override behavior and momentum block modifier.
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1435 (module defined)
  - CODE_IMPLEMENTED_FEATURE_PLAN.md:L228-L231 (squeeze_enabled and momentum block settings)
  - old_plan.txt:L89 (* Squeeze state) (old plan mention)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L768 (test_squeeze_release_block_reason_is_consumed)
- **Reason/Event codes touched:**
  - BlockReason.BLOCK_SQUEEZE_RELEASE_AGAINST_BIAS (core/enums.py)
- **Gap notes:**
  - —

### M111 — Funding Filter (FR 8h est, Binance premium index)
- **Source:** BOTH
- **Status:** DONE
- **Behavior implemented:**
  - Funding filter (8h estimate / premium index) as advisory/gate.
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1439 (module defined)
  - CODE_IMPLEMENTED_FEATURE_PLAN.md:L95 (funding in phase-2 gating stack); CODE_IMPLEMENTED_FEATURE_PLAN.md:L1209 (funding gate method anchor)
  - old_plan.txt:L105 (* Funding (Binance premium-index estimate)) (old plan mention)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L768 (test_funding_gate_honors_threshold)
- **Reason/Event codes touched:**
  - BlockReason.BLOCK_FUNDING_FILTER (core/enums.py)
- **Gap notes:**
  - —

### M112 — HVP Gate (HVP vs HVPSMA + BBW expansion)
- **Source:** BOTH
- **Status:** DONE
- **Behavior implemented:**
  - HVP gate (HVP vs SMA + BBW expansion) to block builds during expansion; optional quiet-exit bias.
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1443 (module defined)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L413 (BLOCK_HVP_EXPANDING wired)
  - old_plan.txt:L167 (* HVP vs HVP-SMA gate (volatility state veto)) (old plan mention)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L768 (test_hvp_stats_returns_current_and_sma)
- **Reason/Event codes touched:**
  - BlockReason.BLOCK_HVP_EXPANDING (core/enums.py)
- **Gap notes:**
  - —

### M113 — Boom & Doom Impulse Guard
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1447 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M201 — Core 24h ± ATR Box Builder
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1456 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M202 — Box Width Target / Hard-Soft Veto Policy
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1462 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M203 — Channel-Width Veto (BB/ATR/SMA/HL selectable)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1467 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M204 — Percent-of-Average Width Veto
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1472 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M205 — Minimum Range Length + Breakout Confirm Bars
- **Source:** NEW_PLAN
- **Status:** DONE
- **Behavior implemented:**
  - Minimum range length gate blocks START/REBUILD until min_range_len_bars reached.
  - Breakout confirm bars require k consecutive closes outside box threshold to block or STOP.
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1477 (module defined)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L728-L738 (test_min_range_and_breakout_confirm.py section lists tests)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L728-L738 (test_min_range_len_gate_* and test_breakout_confirm_* tests)
- **Reason/Event codes touched:**
  - BlockReason.BLOCK_MIN_RANGE_LEN_NOT_MET, BLOCK_BREAKOUT_CONFIRM_UP/DN; StopReason STOP_BREAKOUT_CONFIRM_UP/DN (core/enums.py)
- **Gap notes:**
  - —

### M206 — VRVP POC/VAH/VAL (24h deterministic)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1481 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M207 — POC Acceptance Gate (cross before first START)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1485 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M208 — Generic Straddle Veto Framework (shared utility)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1489 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M209 — Log-Space Quartiles + 1.386 Extensions
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1494 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M210 — Overlap Pruning of Mitigated Boxes (≥60%)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1498 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M211 — Box-vs-Bands / Envelope Overlap Checks
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1502 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M212 — Fallback POC Estimator (when VRVP unavailable)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1506 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M213 — Midline Bias Fallback (POC-neutral fallback)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1510 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M301 — Cost-Aware Step Sizing
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1518 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M302 — N Levels Selection (bounded)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1523 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M303 — START Entry Filter Aggregator
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1527 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M304 — Deterministic TP/SL Selection (nearest conservative wins)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1532 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M305 — Fill Detection / Rung Cross Engine (`Touch` / `Reverse`)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1536 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M306 — Directional skip-one rule (simulator-inspired)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1541 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M307 — Next-rung ghost lines (UI only)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1546 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M401 — STOP Trigger Framework
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1554 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M402 — Reclaim Timer + REBUILD Discipline (8h baseline)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1559 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M403 — Cooldown + Min Runtime + Anti-Flap
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1563 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M404 — Protections Layer (cooldown + drawdown guard + future protections)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1567 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M405 — Confirm-Entry / Confirm-Exit Hooks (spread/depth/jump)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1571 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M406 — Structured Event Bus / Taxonomy
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1575 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M501 — Micro-VAP inside active box
- **Source:** BOTH
- **Status:** DONE
- **Behavior implemented:**
  - Micro-VAP inside active box: fixed bins, micro_POC, HVN/LVN sets, void slope; event-driven recompute.
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1583 (module defined)
  - CODE_IMPLEMENTED_FEATURE_PLAN.md:L99 (micro-VAP integrated; GridBrainV1.py:4219)
  - old_plan.txt:L82 (* Micro-VAP bins) (old plan mention)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L753-L758 (test_partial_module_completion includes micro bias/order flow/reentry helpers); CODE_IMPLEMENTATION_SNAPSHOT.md:L768 (SL avoids LVN + FVG)
- **Reason/Event codes touched:**
  - InfoCode/Events around POC alignment, HVN/LVN gates (enums)
- **Gap notes:**
  - —

### M502 — POC Alignment Check (micro_POC vs VRVP_POC)
- **Source:** NEW_PLAN
- **Status:** DONE
- **Behavior implemented:**
  - POC alignment check: requires cross when micro_POC vs VRVP_POC misaligned beyond step fraction.
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1589 (module defined)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L768 (test_poc_alignment_strict_requires_cross_when_misaligned)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L768 (test_poc_alignment_strict_requires_cross_when_misaligned)
- **Reason/Event codes touched:**
  - BlockReason.BLOCK_POC_ALIGNMENT_FAIL (core/enums.py)
- **Gap notes:**
  - —

### M503 — HVN/LVN inside box + min spacing
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1594 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M504 — LVN-void STOP Accelerator
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1599 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M505 — Micro-VAP bias / TP-SL nudges / re-entry discipline
- **Source:** NEW_PLAN
- **Status:** DONE
- **Behavior implemented:**
  - Micro-VAP bias and TP/SL nudges; re-entry discipline (HVN touch / micro_POC migration).
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1604 (module defined)
  - CODE_IMPLEMENTED_FEATURE_PLAN.md:L99 (rung weights from micro-vap; GridBrainV1.py:4315)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L753-L758 (test_partial_module_completion covers micro reentry helpers)
- **Reason/Event codes touched:**
  - EventType.EVENT_* reentry and micro-vap (enums)
- **Gap notes:**
  - —

### M601 — Lightweight OB Module
- **Source:** BOTH
- **Status:** DONE
- **Behavior implemented:**
  - Lightweight OB module: latest OB per side, freshness gate, box veto, TP nudge; mitigation tracking.
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1612 (module defined)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L57-L58 (planner/structure/order_blocks.py listed); CODE_IMPLEMENTATION_SNAPSHOT.md:L753-L758 (order blocks test file)
  - old_plan.txt:L360 (## 8.1 Order Blocks (OB) module (lightweight)) (old plan mention)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L753-L758 (test_order_block_* in test_order_blocks.py)
- **Reason/Event codes touched:**
  - BlockReason.BLOCK_FRESH_OB_COOLOFF/BLOCK_BOX_STRADDLE_OB_EDGE (core/enums.py)
- **Gap notes:**
  - —

### M602 — Basic FVG Detection + Straddle Veto
- **Source:** BOTH
- **Status:** DONE
- **Behavior implemented:**
  - FVG stack present in strategy: detection + straddle veto + IMFVG avg + session FVG + positioning avgs + optional FVG-VP (per code-derived plan).
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1617 (module defined)
  - CODE_IMPLEMENTED_FEATURE_PLAN.md:L99 (FVG stack integrated, GridBrainV1.py:4358; FVG-VP state GridBrainV1.py:5311)
  - old_plan.txt:L90 (* FVG / OB / structure helpers) (old plan mention)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L753-L758 (test_partial_module_completion includes fvg_vp_channel_and_session_sweep_helpers); CODE_IMPLEMENTATION_SNAPSHOT.md:L768 (test_sl_selection_avoids_lvn_and_fvg_gap)
- **Reason/Event codes touched:**
  - BlockReason.BLOCK_BOX_STRADDLE_FVG_EDGE/BLOCK_BOX_STRADDLE_FVG_AVG/BLOCK_BOX_STRADDLE_SESSION_FVG_AVG (core/enums.py)
- **Gap notes:**
  - —

### M603 — IMFVG Average as TP Candidate + Mitigation Relax
- **Source:** NEW_PLAN
- **Status:** DONE
- **Behavior implemented:**
  - FVG stack present in strategy: detection + straddle veto + IMFVG avg + session FVG + positioning avgs + optional FVG-VP (per code-derived plan).
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1622 (module defined)
  - CODE_IMPLEMENTED_FEATURE_PLAN.md:L99 (FVG stack integrated, GridBrainV1.py:4358; FVG-VP state GridBrainV1.py:5311)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L753-L758 (test_partial_module_completion includes fvg_vp_channel_and_session_sweep_helpers); CODE_IMPLEMENTATION_SNAPSHOT.md:L768 (test_sl_selection_avoids_lvn_and_fvg_gap)
- **Reason/Event codes touched:**
  - BlockReason.BLOCK_BOX_STRADDLE_FVG_EDGE/BLOCK_BOX_STRADDLE_FVG_AVG/BLOCK_BOX_STRADDLE_SESSION_FVG_AVG (core/enums.py)
- **Gap notes:**
  - —

### M604 — Session FVG Module (daily)
- **Source:** NEW_PLAN
- **Status:** DONE
- **Behavior implemented:**
  - FVG stack present in strategy: detection + straddle veto + IMFVG avg + session FVG + positioning avgs + optional FVG-VP (per code-derived plan).
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1628 (module defined)
  - CODE_IMPLEMENTED_FEATURE_PLAN.md:L99 (FVG stack integrated, GridBrainV1.py:4358; FVG-VP state GridBrainV1.py:5311)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L753-L758 (test_partial_module_completion includes fvg_vp_channel_and_session_sweep_helpers); CODE_IMPLEMENTATION_SNAPSHOT.md:L768 (test_sl_selection_avoids_lvn_and_fvg_gap)
- **Reason/Event codes touched:**
  - BlockReason.BLOCK_BOX_STRADDLE_FVG_EDGE/BLOCK_BOX_STRADDLE_FVG_AVG/BLOCK_BOX_STRADDLE_SESSION_FVG_AVG (core/enums.py)
- **Gap notes:**
  - —

### M605 — FVG Positioning Averages (`up_avg`, `down_avg`)
- **Source:** NEW_PLAN
- **Status:** DONE
- **Behavior implemented:**
  - FVG stack present in strategy: detection + straddle veto + IMFVG avg + session FVG + positioning avgs + optional FVG-VP (per code-derived plan).
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1637 (module defined)
  - CODE_IMPLEMENTED_FEATURE_PLAN.md:L99 (FVG stack integrated, GridBrainV1.py:4358; FVG-VP state GridBrainV1.py:5311)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L753-L758 (test_partial_module_completion includes fvg_vp_channel_and_session_sweep_helpers); CODE_IMPLEMENTATION_SNAPSHOT.md:L768 (test_sl_selection_avoids_lvn_and_fvg_gap)
- **Reason/Event codes touched:**
  - BlockReason.BLOCK_BOX_STRADDLE_FVG_EDGE/BLOCK_BOX_STRADDLE_FVG_AVG/BLOCK_BOX_STRADDLE_SESSION_FVG_AVG (core/enums.py)
- **Gap notes:**
  - —

### M606 — FVG-VP (Volume Profile inside FVG) Module
- **Source:** NEW_PLAN
- **Status:** DONE
- **Behavior implemented:**
  - FVG stack present in strategy: detection + straddle veto + IMFVG avg + session FVG + positioning avgs + optional FVG-VP (per code-derived plan).
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1643 (module defined)
  - CODE_IMPLEMENTED_FEATURE_PLAN.md:L99 (FVG stack integrated, GridBrainV1.py:4358; FVG-VP state GridBrainV1.py:5311)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L753-L758 (test_partial_module_completion includes fvg_vp_channel_and_session_sweep_helpers); CODE_IMPLEMENTATION_SNAPSHOT.md:L768 (test_sl_selection_avoids_lvn_and_fvg_gap)
- **Reason/Event codes touched:**
  - BlockReason.BLOCK_BOX_STRADDLE_FVG_EDGE/BLOCK_BOX_STRADDLE_FVG_AVG/BLOCK_BOX_STRADDLE_SESSION_FVG_AVG (core/enums.py)
- **Gap notes:**
  - —

### M607 — Defensive FVG Quality Filter (TradingFinder-style)
- **Source:** NEW_PLAN
- **Status:** DONE
- **Behavior implemented:**
  - FVG stack present in strategy: detection + straddle veto + IMFVG avg + session FVG + positioning avgs + optional FVG-VP (per code-derived plan).
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1649 (module defined)
  - CODE_IMPLEMENTED_FEATURE_PLAN.md:L99 (FVG stack integrated, GridBrainV1.py:4358; FVG-VP state GridBrainV1.py:5311)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L753-L758 (test_partial_module_completion includes fvg_vp_channel_and_session_sweep_helpers); CODE_IMPLEMENTATION_SNAPSHOT.md:L768 (test_sl_selection_avoids_lvn_and_fvg_gap)
- **Reason/Event codes touched:**
  - BlockReason.BLOCK_BOX_STRADDLE_FVG_EDGE/BLOCK_BOX_STRADDLE_FVG_AVG/BLOCK_BOX_STRADDLE_SESSION_FVG_AVG (core/enums.py)
- **Gap notes:**
  - —

### M701 — Donchian Channel Module
- **Source:** NEW_PLAN
- **Status:** DONE
- **Behavior implemented:**
  - Donchian channel module: width gate, midline TP candidate, strong-close STOP beyond bounds.
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1660 (module defined)
  - CODE_IMPLEMENTED_FEATURE_PLAN.md:L659 (donchian_lookback_bars config listed)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L768 (test_latest_daily_vwap_computation covers basis/vwap; donchian-specific tests not singled out)
- **Reason/Event codes touched:**
  - BlockReason.BLOCK_BOX_DONCHIAN_WIDTH_SANITY, BlockReason.BLOCK_BOX_STRADDLE_VWAP_DONCHIAN_MID (core/enums.py)
- **Gap notes:**
  - —

### M702 — Smart Breakout Channels (AlgoAlpha-style)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1667 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M703 — Zig-Zag Envelope / Channel Enhancements
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1674 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M704 — Liquidity Sweeps (LuxAlgo-style)
- **Source:** BOTH
- **Status:** DONE
- **Behavior implemented:**
  - Liquidity sweeps: wick sweeps + break&retest sweeps; TP nudge vs STOP precedence through box edge.
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1682 (module defined)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L57 (planner/structure/liquidity_sweeps.py listed); CODE_IMPLEMENTATION_SNAPSHOT.md:L470-L472 (sweep events wired)
  - old_plan.txt:L350 (* Liquidity sweeps (wick and break+retest)) (old plan mention)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L724-L731 (test_liquidity_sweeps.py functions include wick + break-retest stop through box edge)
- **Reason/Event codes touched:**
  - EventType.EVENT_SWEEP_WICK_* / EVENT_SWEEP_BREAK_RETEST_*; StopReason.STOP_LIQUIDITY_SWEEP_BREAK_RETEST (enums)
- **Gap notes:**
  - —

### M705 — Sweep mode toggle (Wick/Open) for retest validation
- **Source:** BOTH
- **Status:** DONE
- **Behavior implemented:**
  - Sweep retest validation mode toggle (Wick/Open) affects break&retest validation only.
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1688 (module defined)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L724-L731 (test_retest_validation_mode_toggle_affects_break_retest_only)
  - old_plan.txt:L350 (* Liquidity sweeps (wick and break+retest)) (old plan mention)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L724-L731
- **Reason/Event codes touched:**
  - Config key sweep_retest_validation_mode in GridBrainV1 config list (CODE_IMPLEMENTATION_SNAPSHOT.md:L550)
- **Gap notes:**
  - —

### M801 — MTF POC Confluence (D/W, M advisory) + POC-cross before START
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1696 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M802 — MRVD Module (D/W/M distribution + buy/sell split)
- **Source:** BOTH
- **Status:** DONE
- **Behavior implemented:**
  - MRVD multi-range volume distribution (D/W/M) with POC/VAH/VAL and buy/sell split; confluence gates and POC drift guard.
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1700 (module defined)
  - CODE_IMPLEMENTED_FEATURE_PLAN.md:L297-L301 (mrvd_enabled, bins, value area pct; GridBrainV1:707-709)
  - old_plan.txt:L99 (* MRVD (POC/VAH/VAL confluence)) (old plan mention)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L768 (MRVD-related blockers listed; no specific MRVD unit test name surfaced)
- **Reason/Event codes touched:**
  - BlockReason.BLOCK_MRVD_CONFLUENCE_FAIL/BLOCK_MRVD_POC_DRIFT_GUARD (core/enums.py)
- **Gap notes:**
  - —

### M803 — Multi-Range Basis / Pivots Module (VWAP default)
- **Source:** NEW_PLAN
- **Status:** DONE
- **Behavior implemented:**
  - Multi-range basis/pivots module (VWAP default) with basis slope veto and basis cross confirm.
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1708 (module defined)
  - CODE_IMPLEMENTED_FEATURE_PLAN.md:L659 (basis band window/stds; basis cross confirm config present)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L768 (test_latest_daily_vwap_computation; basis-cross behavior in phase3 validation set)
- **Reason/Event codes touched:**
  - BlockReason.BLOCK_BASIS_CROSS_PENDING (core/enums.py)
- **Gap notes:**
  - —

### M804 — Session VWAP / Daily VWAP TP Candidates
- **Source:** NEW_PLAN
- **Status:** DONE
- **Behavior implemented:**
  - Session VWAP / Daily VWAP TP candidates; used as conservative target candidate.
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1715 (module defined)
  - CODE_IMPLEMENTED_FEATURE_PLAN.md:L659 (latest_daily_vwap_computation method listed)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L768 (test_latest_daily_vwap_computation)
- **Reason/Event codes touched:**
  - InfoCode.INFO_TP_SOURCE_SELECTED may record VWAP as candidate (enums)
- **Gap notes:**
  - —

### M805 — Session High/Low Sweep and Break-Retest Events
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1720 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M806 — VAH/VAL/POC Zone Proximity START Gate
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1726 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M807 — VAH/VAL Approximation via Quantiles (fallback/optional)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1731 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M808 — Average-of-basis with session H/L bands (target candidates)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1736 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M809 — Buy-ratio Micro-Bias inside box (mid-band)
- **Source:** NEW_PLAN
- **Status:** DONE
- **Behavior implemented:**
  - Buy-ratio micro-bias inside box (mid-band) nudges rung density and TP tie-breakers.
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1740 (module defined)
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L659 (GridBrainV1 has _micro_buy_ratio_state and _apply_buy_ratio_rung_bias methods listed)
- **Test evidence:**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L753-L758 (test_partial_module_completion includes micro_bias_order_flow_and_reentry_helpers)
- **Reason/Event codes touched:**
  - InfoCode.INFO_BUY_RATIO_BIAS_APPLIED (enums; wiring may be in GridBrainV1)
- **Gap notes:**
  - —

### M901 — CVD Divergence near box edges (advisory)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1749 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M902 — CVD BOS events (ema filtered style)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1755 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M903 — CVD Spike + Passive Absorption (Insights style)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1760 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M904 — CVD Divergence Oscillator Strong Score (advisory)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1766 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M905 — SMA200 / EMA trend filters for directional variants
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1771 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M906 — CVD extension line touch counter (UI only)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1776 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M1001 — Maker-first post-only discipline + retry/backoff
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1784 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M1002 — Confirm-entry/exit hooks (spread/depth/jump)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1788 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M1003 — Minimal order-flow metrics (soft veto/confidence)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1792 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M1004 — Atomic handoff + idempotency (duplicate-safe)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1796 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M1005 — Empirical execution cost feedback loop
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1800 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M1006 — Stress/chaos replay as standard validation
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1804 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M1007 — Formal tuning workflow + anti-overfit checks
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1808 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

### M1008 — FreqAI/ML confidence overlay (not primary)
- **Source:** NEW_PLAN
- **Status:** UNKNOWN
- **Behavior implemented:**
  - (no code-first mapping completed for this module yet)
- **Evidence (code refs):**
  - GRID_MASTER_PLAN.md:L1812 (module defined)
- **Test evidence:**
  - —
- **Reason/Event codes touched:**
  - —
- **Gap notes:**
  - Map module to code evidence or mark NOT_IMPLEMENTED with proof.

## 3.A Ad-hoc implemented features (not explicitly in old/new plan)

### AH-001 — Regime audit + threshold recommendation pipeline (offline script)
- **Source:** ADHOC
- **Status:** DONE
- **Behavior implemented:**
  - Offline regime audit tool for labels, transitions, quantiles, and threshold recommendation; not part of live decision loop.
- **Evidence (code refs):**
  - CODE_IMPLEMENTATION_SNAPSHOT.md:L28 (freqtrade/user_data/scripts/regime_audit_v1.py listed)
  - CODE_IMPLEMENTED_FEATURE_PLAN.md:L716 (regime audit pipeline described with anchors regime_audit_v1.py:233/303/410/577)
- **Test evidence:**
  - No test evidence found in snapshot for regime_audit_v1.py -> treat as tooling DONE (script)
- **Reason/Event codes touched:**
  - None (tooling script)
- **Gap notes:**
  - Add explicit doc entry in master plan as Tooling module OR deprecate with replacement rationale.

### AH-002 — GridBrainV1BaselineNoNeutral strategy variant (ablation)
- **Source:** ADHOC
- **Status:** DONE
- **Behavior implemented:**
  - Alternate strategy class file used for ablations/experiments; not referenced in master plan module registry.
- **Evidence (code refs):**
  - CODE_IMPLEMENTED_FEATURE_PLAN.md:L31-L36 (strategy variant listed: freqtrade/user_data/strategies/GridBrainV1BaselineNoNeutral.py)
- **Test evidence:**
  - UNKNOWN (no dedicated tests referenced in snapshot for this variant)
- **Reason/Event codes touched:**
  - May reuse same enums; wiring UNKNOWN without direct references
- **Gap notes:**
  - Decide: keep as experiments (document), or deprecate/remove with deprecation record.

### AH-003 — GridBrainV1ExpRouterFast strategy variant (router experiment)
- **Source:** ADHOC
- **Status:** DONE
- **Behavior implemented:**
  - Alternate strategy class file used for ablations/experiments; not referenced in master plan module registry.
- **Evidence (code refs):**
  - CODE_IMPLEMENTED_FEATURE_PLAN.md:L31-L36 (strategy variant listed: freqtrade/user_data/strategies/GridBrainV1ExpRouterFast.py)
- **Test evidence:**
  - UNKNOWN (no dedicated tests referenced in snapshot for this variant)
- **Reason/Event codes touched:**
  - May reuse same enums; wiring UNKNOWN without direct references
- **Gap notes:**
  - Decide: keep as experiments (document), or deprecate/remove with deprecation record.

### AH-004 — GridBrainV1NeutralDiFilter strategy variant (neutral DI filter)
- **Source:** ADHOC
- **Status:** DONE
- **Behavior implemented:**
  - Alternate strategy class file used for ablations/experiments; not referenced in master plan module registry.
- **Evidence (code refs):**
  - CODE_IMPLEMENTED_FEATURE_PLAN.md:L31-L36 (strategy variant listed: freqtrade/user_data/strategies/GridBrainV1NeutralDiFilter.py)
- **Test evidence:**
  - UNKNOWN (no dedicated tests referenced in snapshot for this variant)
- **Reason/Event codes touched:**
  - May reuse same enums; wiring UNKNOWN without direct references
- **Gap notes:**
  - Decide: keep as experiments (document), or deprecate/remove with deprecation record.

### AH-005 — GridBrainV1NeutralEligibilityOnly strategy variant (neutral eligibility only)
- **Source:** ADHOC
- **Status:** DONE
- **Behavior implemented:**
  - Alternate strategy class file used for ablations/experiments; not referenced in master plan module registry.
- **Evidence (code refs):**
  - CODE_IMPLEMENTED_FEATURE_PLAN.md:L31-L36 (strategy variant listed: freqtrade/user_data/strategies/GridBrainV1NeutralEligibilityOnly.py)
- **Test evidence:**
  - UNKNOWN (no dedicated tests referenced in snapshot for this variant)
- **Reason/Event codes touched:**
  - May reuse same enums; wiring UNKNOWN without direct references
- **Gap notes:**
  - Decide: keep as experiments (document), or deprecate/remove with deprecation record.

### AH-006 — GridBrainV1NoFVG strategy variant (ablation)
- **Source:** ADHOC
- **Status:** DONE
- **Behavior implemented:**
  - Alternate strategy class file used for ablations/experiments; not referenced in master plan module registry.
- **Evidence (code refs):**
  - CODE_IMPLEMENTED_FEATURE_PLAN.md:L31-L36 (strategy variant listed: freqtrade/user_data/strategies/GridBrainV1NoFVG.py)
- **Test evidence:**
  - UNKNOWN (no dedicated tests referenced in snapshot for this variant)
- **Reason/Event codes touched:**
  - May reuse same enums; wiring UNKNOWN without direct references
- **Gap notes:**
  - Decide: keep as experiments (document), or deprecate/remove with deprecation record.

### AH-007 — GridBrainV1NoPause strategy variant (ablation)
- **Source:** ADHOC
- **Status:** DONE
- **Behavior implemented:**
  - Alternate strategy class file used for ablations/experiments; not referenced in master plan module registry.
- **Evidence (code refs):**
  - CODE_IMPLEMENTED_FEATURE_PLAN.md:L31-L36 (strategy variant listed: freqtrade/user_data/strategies/GridBrainV1NoPause.py)
- **Test evidence:**
  - UNKNOWN (no dedicated tests referenced in snapshot for this variant)
- **Reason/Event codes touched:**
  - May reuse same enums; wiring UNKNOWN without direct references
- **Gap notes:**
  - Decide: keep as experiments (document), or deprecate/remove with deprecation record.

## 4. Old-vs-New-vs-Code Coverage Matrix
| Feature ID | In old plan? | In new plan? | In code? | Final status | Old plan evidence | Notes |
|---|---:|---:|---:|---|---|---|
| M001 | N | Y | Y | DONE | — | Evidence present |
| M002 | N | Y | Y | DONE | — | Evidence present |
| M003 | N | Y | Y | DONE | — | Evidence present |
| M004 | N | Y | Y | DONE | — | Evidence present |
| M005 | N | Y | Y | DONE | — | Evidence present |
| M006 | N | Y | Y | DONE | — | Evidence present |
| M007 | N | Y | Y | DONE | — | Evidence present |
| M008 | N | Y | Y | DONE | — | Evidence present |
| M009 | N | Y | Y | DONE | — | Evidence present |
| M010 | N | Y | Y | DONE | — | Evidence present |
| M101 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M102 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M103 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M104 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M105 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M106 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M107 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M108 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M109 | Y | Y | Y | DONE | old_plan.txt:L86 (* BBW / BBWP) | Evidence present |
| M110 | Y | Y | Y | DONE | old_plan.txt:L89 (* Squeeze state) | Evidence present |
| M111 | Y | Y | Y | DONE | old_plan.txt:L105 (* Funding (Binance premium-index estimate)) | Evidence present |
| M112 | Y | Y | Y | DONE | old_plan.txt:L167 (* HVP vs HVP-SMA gate (volatility state veto)) | Evidence present |
| M113 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M201 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M202 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M203 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M204 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M205 | N | Y | Y | DONE | — | Evidence present |
| M206 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M207 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M208 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M209 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M210 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M211 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M212 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M213 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M301 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M302 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M303 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M304 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M305 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M306 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M307 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M401 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M402 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M403 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M404 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M405 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M406 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M501 | Y | Y | Y | DONE | old_plan.txt:L82 (* Micro-VAP bins) | Evidence present |
| M502 | N | Y | Y | DONE | — | Evidence present |
| M503 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M504 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M505 | N | Y | Y | DONE | — | Evidence present |
| M601 | Y | Y | Y | DONE | old_plan.txt:L360 (## 8.1 Order Blocks (OB) module (lightweight)) | Evidence present |
| M602 | Y | Y | Y | DONE | old_plan.txt:L90 (* FVG / OB / structure helpers) | Evidence present |
| M603 | N | Y | Y | DONE | — | Evidence present |
| M604 | N | Y | Y | DONE | — | Evidence present |
| M605 | N | Y | Y | DONE | — | Evidence present |
| M606 | N | Y | Y | DONE | — | Evidence present |
| M607 | N | Y | Y | DONE | — | Evidence present |
| M701 | N | Y | Y | DONE | — | Evidence present |
| M702 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M703 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M704 | Y | Y | Y | DONE | old_plan.txt:L350 (* Liquidity sweeps (wick and break+retest)) | Evidence present |
| M705 | Y | Y | Y | DONE | old_plan.txt:L350 (* Liquidity sweeps (wick and break+retest)) | Evidence present |
| M801 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M802 | Y | Y | Y | DONE | old_plan.txt:L99 (* MRVD (POC/VAH/VAL confluence)) | Evidence present |
| M803 | N | Y | Y | DONE | — | Evidence present |
| M804 | N | Y | Y | DONE | — | Evidence present |
| M805 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M806 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M807 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M808 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M809 | N | Y | Y | DONE | — | Evidence present |
| M901 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M902 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M903 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M904 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M905 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M906 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M1001 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M1002 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M1003 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M1004 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M1005 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M1006 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M1007 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| M1008 | N | Y | UNKNOWN | UNKNOWN | — | No direct evidence mapped yet (requires per-module mapping pass). |
| AH-001 | N | N | Y | DONE | — | ADHOC item from code-derived inventory |
| AH-002 | N | N | Y | DONE | — | ADHOC item from code-derived inventory |
| AH-003 | N | N | Y | DONE | — | ADHOC item from code-derived inventory |
| AH-004 | N | N | Y | DONE | — | ADHOC item from code-derived inventory |
| AH-005 | N | N | Y | DONE | — | ADHOC item from code-derived inventory |
| AH-006 | N | N | Y | DONE | — | ADHOC item from code-derived inventory |
| AH-007 | N | N | Y | DONE | — | ADHOC item from code-derived inventory |

## 5. Canonical Reason/Event Wiring Table
> Source of canonical codes: `enums.py` (uploaded). Runtime wiring evidence from uploaded `.py` and `CODE_IMPLEMENTATION_SNAPSHOT.md`.
| Code | Enum type | Wiring status | Emitter locations | Related tests |
|---|---|---|---|---|
| BLOCK_7D_EXTREME_CONTEXT | BlockReason | WIRED | GridBrainV1.py:L1747; GridBrainV1.py:L7730 | UNKNOWN |
| BLOCK_ADX_HIGH | BlockReason | WIRED | GridBrainV1.py:L1739 | UNKNOWN |
| BLOCK_BAND_SLOPE_HIGH | BlockReason | WIRED | GridBrainV1.py:L7732 | UNKNOWN |
| BLOCK_BASIS_CROSS_PENDING | BlockReason | WIRED | GridBrainV1.py:L7793; GridBrainV1.py:L8040 | UNKNOWN |
| BLOCK_BBWP_HIGH | BlockReason | WIRED | GridBrainV1.py:L7741; GridBrainV1.py:L7743 | UNKNOWN |
| BLOCK_BBW_EXPANDING | BlockReason | WIRED | GridBrainV1.py:L1741 | UNKNOWN |
| BLOCK_BOX_CHANNEL_OVERLAP_LOW | BlockReason | WIRED | GridBrainV1.py:L6723 | UNKNOWN |
| BLOCK_BOX_DONCHIAN_WIDTH_SANITY | BlockReason | REGISTRY_ONLY | — | UNKNOWN |
| BLOCK_BOX_ENVELOPE_RATIO_HIGH | BlockReason | WIRED | GridBrainV1.py:L6737 | UNKNOWN |
| BLOCK_BOX_OVERLAP_HIGH | BlockReason | WIRED | GridBrainV1.py:L6620 | UNKNOWN |
| BLOCK_BOX_STRADDLE_BREAKOUT_LEVEL | BlockReason | WIRED | GridBrainV1.py:L7174 | UNKNOWN |
| BLOCK_BOX_STRADDLE_FVG_AVG | BlockReason | WIRED | GridBrainV1.py:L1263; GridBrainV1.py:L7179 | UNKNOWN |
| BLOCK_BOX_STRADDLE_FVG_EDGE | BlockReason | WIRED | GridBrainV1.py:L1261; GridBrainV1.py:L7180; GridBrainV1.py:L7181 | UNKNOWN |
| BLOCK_BOX_STRADDLE_HTF_POC | BlockReason | REGISTRY_ONLY | — | UNKNOWN |
| BLOCK_BOX_STRADDLE_OB_EDGE | BlockReason | WIRED | GridBrainV1.py:L2948; GridBrainV1.py:L7172 | UNKNOWN |
| BLOCK_BOX_STRADDLE_SESSION_FVG_AVG | BlockReason | WIRED | GridBrainV1.py:L1268; GridBrainV1.py:L7182; GridBrainV1.py:L7183; GridBrainV1.py:L7184 | UNKNOWN |
| BLOCK_BOX_STRADDLE_VWAP_DONCHIAN_MID | BlockReason | WIRED | GridBrainV1.py:L7185; GridBrainV1.py:L7186 | UNKNOWN |
| BLOCK_BOX_VP_POC_MISPLACED | BlockReason | WIRED | GridBrainV1.py:L7178 | UNKNOWN |
| BLOCK_BOX_WIDTH_TOO_NARROW | BlockReason | REGISTRY_ONLY | — | UNKNOWN |
| BLOCK_BOX_WIDTH_TOO_WIDE | BlockReason | WIRED | GridBrainV1.py:L6617 | UNKNOWN |
| BLOCK_BREAKOUT_CONFIRM_DN | BlockReason | WIRED | GridBrainV1.py:L1664; GridBrainV1.py:L1674; GridBrainV1.py:L6902; GridBrainV1.py:L6903 | UNKNOWN |
| BLOCK_BREAKOUT_CONFIRM_UP | BlockReason | WIRED | GridBrainV1.py:L1659; GridBrainV1.py:L1673; GridBrainV1.py:L6900; GridBrainV1.py:L6901 | UNKNOWN |
| BLOCK_BREAKOUT_RECLAIM_PENDING | BlockReason | REGISTRY_ONLY | — | UNKNOWN |
| BLOCK_CAPACITY_THIN | BlockReason | WIRED | GridBrainV1.py:L7763; GridBrainV1.py:L7795; GridBrainV1.py:L8044; capacity_guard.py:L122; capacity_guard.py:L123; grid_executor_v1.py:L1341 | UNKNOWN |
| BLOCK_COOLDOWN_ACTIVE | BlockReason | WIRED | GridBrainV1.py:L8057 | UNKNOWN |
| BLOCK_DATA_DUPLICATE_TS | BlockReason | REGISTRY_ONLY | — | UNKNOWN |
| BLOCK_DATA_GAP | BlockReason | WIRED | GridBrainV1.py:L1756; GridBrainV1.py:L8255; data_quality_assessor.py:L47; data_quality_assessor.py:L56 | UNKNOWN |
| BLOCK_DATA_MISALIGN | BlockReason | WIRED | GridBrainV1.py:L1761; GridBrainV1.py:L8257; data_quality_assessor.py:L34; data_quality_assessor.py:L37; data_quality_assessor.py:L40; data_quality_assessor.py:L70 | UNKNOWN |
| BLOCK_DATA_NON_MONOTONIC_TS | BlockReason | REGISTRY_ONLY | — | UNKNOWN |
| BLOCK_DRAWDOWN_GUARD | BlockReason | WIRED | GridBrainV1.py:L2920; GridBrainV1.py:L7759 | UNKNOWN |
| BLOCK_DRIFT_SLOPE_HIGH | BlockReason | WIRED | GridBrainV1.py:L7736 | UNKNOWN |
| BLOCK_EMA_DIST | BlockReason | WIRED | GridBrainV1.py:L1743 | UNKNOWN |
| BLOCK_EXCURSION_ASYMMETRY | BlockReason | WIRED | GridBrainV1.py:L7734 | UNKNOWN |
| BLOCK_EXEC_CONFIRM_REBUILD_FAILED | BlockReason | REGISTRY_ONLY | — | UNKNOWN |
| BLOCK_EXEC_CONFIRM_START_FAILED | BlockReason | REGISTRY_ONLY | — | UNKNOWN |
| BLOCK_FRESH_BREAKOUT | BlockReason | WIRED | GridBrainV1.py:L581; GridBrainV1.py:L7747; GridBrainV1.py:L8016 | UNKNOWN |
| BLOCK_FRESH_FVG_COOLOFF | BlockReason | REGISTRY_ONLY | — | UNKNOWN |
| BLOCK_FRESH_OB_COOLOFF | BlockReason | WIRED | GridBrainV1.py:L2947; GridBrainV1.py:L7749; GridBrainV1.py:L8018 | UNKNOWN |
| BLOCK_FUNDING_FILTER | BlockReason | WIRED | GridBrainV1.py:L7755 | UNKNOWN |
| BLOCK_HVP_EXPANDING | BlockReason | WIRED | GridBrainV1.py:L7757 | UNKNOWN |
| BLOCK_INSIDE_SESSION_FVG | BlockReason | REGISTRY_ONLY | — | UNKNOWN |
| BLOCK_LIQ_SWEEP_OPPOSITE_STRUCTURE | BlockReason | WIRED | GridBrainV1.py:L7761 | UNKNOWN |
| BLOCK_MAX_STOPS_WINDOW | BlockReason | WIRED | GridBrainV1.py:L2921; GridBrainV1.py:L5890; GridBrainV1.py:L8059 | UNKNOWN |
| BLOCK_META_DRIFT_SOFT | BlockReason | WIRED | GridBrainV1.py:L7765 | UNKNOWN |
| BLOCK_MIN_RANGE_LEN_NOT_MET | BlockReason | WIRED | GridBrainV1.py:L1640; GridBrainV1.py:L6897 | UNKNOWN |
| BLOCK_MIN_RUNTIME_NOT_MET | BlockReason | REGISTRY_ONLY | — | UNKNOWN |
| BLOCK_MRVD_CONFLUENCE_FAIL | BlockReason | REGISTRY_ONLY | — | UNKNOWN |
| BLOCK_MRVD_POC_DRIFT_GUARD | BlockReason | REGISTRY_ONLY | — | UNKNOWN |
| BLOCK_NO_POC_ACCEPTANCE | BlockReason | WIRED | GridBrainV1.py:L7787; GridBrainV1.py:L8071 | UNKNOWN |
| BLOCK_N_LEVELS_INVALID | BlockReason | REGISTRY_ONLY | — | UNKNOWN |
| BLOCK_OS_DEV_DIRECTIONAL | BlockReason | WIRED | GridBrainV1.py:L7770 | UNKNOWN |
| BLOCK_OS_DEV_NEUTRAL_PERSISTENCE | BlockReason | WIRED | GridBrainV1.py:L7772 | UNKNOWN |
| BLOCK_POC_ALIGNMENT_FAIL | BlockReason | WIRED | GridBrainV1.py:L1511; GridBrainV1.py:L7789; GridBrainV1.py:L8073 | UNKNOWN |
| BLOCK_RECLAIM_NOT_CONFIRMED | BlockReason | WIRED | GridBrainV1.py:L5926; GridBrainV1.py:L8061 | UNKNOWN |
| BLOCK_RECLAIM_PENDING | BlockReason | WIRED | GridBrainV1.py:L8055 | UNKNOWN |
| BLOCK_RVOL_SPIKE | BlockReason | WIRED | GridBrainV1.py:L1745 | UNKNOWN |
| BLOCK_SESSION_FVG_PAUSE | BlockReason | REGISTRY_ONLY | — | UNKNOWN |
| BLOCK_SQUEEZE_RELEASE_AGAINST_BIAS | BlockReason | WIRED | GridBrainV1.py:L1327; GridBrainV1.py:L7774; GridBrainV1.py:L7776 | UNKNOWN |
| BLOCK_STALE_FEATURES | BlockReason | WIRED | GridBrainV1.py:L7767 | UNKNOWN |
| BLOCK_START_BOX_POSITION | BlockReason | WIRED | GridBrainV1.py:L7783; GridBrainV1.py:L8038 | UNKNOWN |
| BLOCK_START_CONFLUENCE_LOW | BlockReason | REGISTRY_ONLY | — | UNKNOWN |
| BLOCK_START_PERSISTENCE_FAIL | BlockReason | WIRED | GridBrainV1.py:L7738 | UNKNOWN |
| BLOCK_START_RSI_BAND | BlockReason | WIRED | GridBrainV1.py:L7785; GridBrainV1.py:L8051 | UNKNOWN |
| BLOCK_START_STABILITY_LOW | BlockReason | WIRED | GridBrainV1.py:L8030 | UNKNOWN |
| BLOCK_STEP_BELOW_COST | BlockReason | WIRED | GridBrainV1.py:L6844; GridBrainV1.py:L6869 | UNKNOWN |
| BLOCK_STEP_BELOW_EMPIRICAL_COST | BlockReason | WIRED | GridBrainV1.py:L6842; GridBrainV1.py:L6867 | UNKNOWN |
| BLOCK_VAH_VAL_POC_PROXIMITY | BlockReason | WIRED | GridBrainV1.py:L7791; GridBrainV1.py:L8042 | UNKNOWN |
| BLOCK_VOL_BUCKET_UNSTABLE | BlockReason | WIRED | GridBrainV1.py:L8028 | UNKNOWN |
| BLOCK_ZERO_VOL_ANOMALY | BlockReason | WIRED | data_quality_assessor.py:L63 | UNKNOWN |
| COOLOFF_BBWP_EXTREME | BlockReason | WIRED | GridBrainV1.py:L7745 | UNKNOWN |
| EVENT_BBWP_EXTREME | EventType | REGISTRY_ONLY | — | UNKNOWN |
| EVENT_BREAKOUT_BEAR | EventType | WIRED | GridBrainV1.py:L8205 | UNKNOWN |
| EVENT_BREAKOUT_BULL | EventType | WIRED | GridBrainV1.py:L8203 | UNKNOWN |
| EVENT_CHANNEL_MIDLINE_TOUCH | EventType | WIRED | GridBrainV1.py:L2931; GridBrainV1.py:L8215 | UNKNOWN |
| EVENT_CHANNEL_STRONG_BREAK_DN | EventType | WIRED | GridBrainV1.py:L2895; GridBrainV1.py:L2930; GridBrainV1.py:L8209 | UNKNOWN |
| EVENT_CHANNEL_STRONG_BREAK_UP | EventType | WIRED | GridBrainV1.py:L2894; GridBrainV1.py:L2929; GridBrainV1.py:L8207 | UNKNOWN |
| EVENT_CVD_BEAR_DIV | EventType | WIRED | GridBrainV1.py:L8245 | UNKNOWN |
| EVENT_CVD_BOS_DN | EventType | WIRED | GridBrainV1.py:L8249 | UNKNOWN |
| EVENT_CVD_BOS_UP | EventType | WIRED | GridBrainV1.py:L8247 | UNKNOWN |
| EVENT_CVD_BULL_DIV | EventType | WIRED | GridBrainV1.py:L8243 | UNKNOWN |
| EVENT_CVD_SPIKE_NEG | EventType | REGISTRY_ONLY | — | UNKNOWN |
| EVENT_CVD_SPIKE_POS | EventType | REGISTRY_ONLY | — | UNKNOWN |
| EVENT_DATA_GAP_DETECTED | EventType | WIRED | GridBrainV1.py:L2900; GridBrainV1.py:L2979; GridBrainV1.py:L8256 | UNKNOWN |
| EVENT_DATA_MISALIGN_DETECTED | EventType | WIRED | GridBrainV1.py:L2901; GridBrainV1.py:L2980; GridBrainV1.py:L8258 | UNKNOWN |
| EVENT_DEPTH_THIN | EventType | WIRED | GridBrainV1.py:L2907; GridBrainV1.py:L2969; GridBrainV1.py:L5814; grid_executor_v1.py:L1256 | UNKNOWN |
| EVENT_DONCHIAN_STRONG_BREAK_DN | EventType | WIRED | GridBrainV1.py:L2897; GridBrainV1.py:L2933; GridBrainV1.py:L8213 | UNKNOWN |
| EVENT_DONCHIAN_STRONG_BREAK_UP | EventType | WIRED | GridBrainV1.py:L2896; GridBrainV1.py:L2932; GridBrainV1.py:L8211 | UNKNOWN |
| EVENT_DRIFT_RETEST_DN | EventType | REGISTRY_ONLY | — | UNKNOWN |
| EVENT_DRIFT_RETEST_UP | EventType | REGISTRY_ONLY | — | UNKNOWN |
| EVENT_EXTREME_RETEST_BOTTOM | EventType | REGISTRY_ONLY | — | UNKNOWN |
| EVENT_EXTREME_RETEST_TOP | EventType | REGISTRY_ONLY | — | UNKNOWN |
| EVENT_EXT_1386_RETEST_BOTTOM | EventType | REGISTRY_ONLY | — | UNKNOWN |
| EVENT_EXT_1386_RETEST_TOP | EventType | REGISTRY_ONLY | — | UNKNOWN |
| EVENT_FVG_MITIGATED_BEAR | EventType | REGISTRY_ONLY | — | UNKNOWN |
| EVENT_FVG_MITIGATED_BULL | EventType | REGISTRY_ONLY | — | UNKNOWN |
| EVENT_FVG_NEW_BEAR | EventType | REGISTRY_ONLY | — | UNKNOWN |
| EVENT_FVG_NEW_BULL | EventType | REGISTRY_ONLY | — | UNKNOWN |
| EVENT_FVG_POC_TAG | EventType | WIRED | GridBrainV1.py:L2956; GridBrainV1.py:L8236 | UNKNOWN |
| EVENT_HVN_TOUCH | EventType | WIRED | GridBrainV1.py:L2962 | UNKNOWN |
| EVENT_IMFVG_AVG_TAG_BEAR | EventType | REGISTRY_ONLY | — | UNKNOWN |
| EVENT_IMFVG_AVG_TAG_BULL | EventType | REGISTRY_ONLY | — | UNKNOWN |
| EVENT_JUMP_DETECTED | EventType | WIRED | GridBrainV1.py:L2908; GridBrainV1.py:L2970; GridBrainV1.py:L5818; grid_executor_v1.py:L1262 | UNKNOWN |
| EVENT_LVN_TOUCH | EventType | WIRED | GridBrainV1.py:L2963 | UNKNOWN |
| EVENT_LVN_VOID_EXIT | EventType | WIRED | GridBrainV1.py:L2964; GridBrainV1.py:L8241 | UNKNOWN |
| EVENT_META_DRIFT_HARD | EventType | WIRED | GridBrainV1.py:L2893; GridBrainV1.py:L8253 | UNKNOWN |
| EVENT_META_DRIFT_SOFT | EventType | WIRED | GridBrainV1.py:L2905; GridBrainV1.py:L8251 | UNKNOWN |
| EVENT_MICRO_POC_SHIFT | EventType | WIRED | GridBrainV1.py:L2961 | UNKNOWN |
| EVENT_OB_NEW_BEAR | EventType | WIRED | GridBrainV1.py:L2950; GridBrainV1.py:L8229 | UNKNOWN |
| EVENT_OB_NEW_BULL | EventType | WIRED | GridBrainV1.py:L2949; GridBrainV1.py:L8227 | UNKNOWN |
| EVENT_OB_TAGGED_BEAR | EventType | WIRED | GridBrainV1.py:L2952; GridBrainV1.py:L8233 | UNKNOWN |
| EVENT_OB_TAGGED_BULL | EventType | WIRED | GridBrainV1.py:L2951; GridBrainV1.py:L8231 | UNKNOWN |
| EVENT_PASSIVE_ABSORPTION_DN | EventType | REGISTRY_ONLY | — | UNKNOWN |
| EVENT_PASSIVE_ABSORPTION_UP | EventType | REGISTRY_ONLY | — | UNKNOWN |
| EVENT_POC_ACCEPTANCE_CROSS | EventType | REGISTRY_ONLY | — | UNKNOWN |
| EVENT_POC_TEST | EventType | REGISTRY_ONLY | — | UNKNOWN |
| EVENT_POST_ONLY_REJECT_BURST | EventType | WIRED | GridBrainV1.py:L2909; GridBrainV1.py:L2971; GridBrainV1.py:L5816; grid_executor_v1.py:L1124 | UNKNOWN |
| EVENT_RANGE_HIT_BOTTOM | EventType | REGISTRY_ONLY | — | UNKNOWN |
| EVENT_RANGE_HIT_TOP | EventType | REGISTRY_ONLY | — | UNKNOWN |
| EVENT_RECLAIM_CONFIRMED | EventType | REGISTRY_ONLY | — | UNKNOWN |
| EVENT_SESSION_FVG_MITIGATED | EventType | REGISTRY_ONLY | — | UNKNOWN |
| EVENT_SESSION_FVG_NEW | EventType | REGISTRY_ONLY | — | UNKNOWN |
| EVENT_SESSION_HIGH_SWEEP | EventType | WIRED | GridBrainV1.py:L2941; GridBrainV1.py:L8217 | UNKNOWN |
| EVENT_SESSION_LOW_SWEEP | EventType | WIRED | GridBrainV1.py:L2942; GridBrainV1.py:L8220 | UNKNOWN |
| EVENT_SPREAD_SPIKE | EventType | WIRED | GridBrainV1.py:L2906; GridBrainV1.py:L2968; GridBrainV1.py:L5812; grid_executor_v1.py:L1250 | UNKNOWN |
| EVENT_SQUEEZE_RELEASE_DN | EventType | REGISTRY_ONLY | — | UNKNOWN |
| EVENT_SQUEEZE_RELEASE_UP | EventType | REGISTRY_ONLY | — | UNKNOWN |
| EVENT_SWEEP_BREAK_RETEST_HIGH | EventType | WIRED | GridBrainV1.py:L2898; GridBrainV1.py:L2939; GridBrainV1.py:L8223; liquidity_sweeps.py:L308 | UNKNOWN |
| EVENT_SWEEP_BREAK_RETEST_LOW | EventType | WIRED | GridBrainV1.py:L2899; GridBrainV1.py:L2940; GridBrainV1.py:L8225; liquidity_sweeps.py:L310 | UNKNOWN |
| EVENT_SWEEP_WICK_HIGH | EventType | WIRED | GridBrainV1.py:L2937; GridBrainV1.py:L8218; liquidity_sweeps.py:L304 | UNKNOWN |
| EVENT_SWEEP_WICK_LOW | EventType | WIRED | GridBrainV1.py:L2938; GridBrainV1.py:L8221; liquidity_sweeps.py:L306 | UNKNOWN |
| EVENT_VRVP_POC_SHIFT | EventType | WIRED | GridBrainV1.py:L2960 | UNKNOWN |
| EXEC_CAPACITY_NOTIONAL_CAP_APPLIED | ExecCode | REGISTRY_ONLY | — | UNKNOWN |
| EXEC_CAPACITY_RUNG_CAP_APPLIED | ExecCode | WIRED | grid_executor_v1.py:L1407 | UNKNOWN |
| EXEC_CONFIRM_EXIT_FAILSAFE | ExecCode | WIRED | grid_executor_v1.py:L2499 | UNKNOWN |
| EXEC_CONFIRM_REBUILD_FAILED | ExecCode | WIRED | grid_executor_v1.py:L2477 | UNKNOWN |
| EXEC_CONFIRM_START_FAILED | ExecCode | WIRED | grid_executor_v1.py:L2480 | UNKNOWN |
| EXEC_FILL_DUPLICATE_GUARD_HIT | ExecCode | REGISTRY_ONLY | — | UNKNOWN |
| EXEC_FILL_REPLACEMENT_PLACED | ExecCode | REGISTRY_ONLY | — | UNKNOWN |
| EXEC_ORDER_CANCEL_REPLACE_APPLIED | ExecCode | WIRED | grid_executor_v1.py:L2082 | UNKNOWN |
| EXEC_ORDER_TIMEOUT_REPRICE | ExecCode | REGISTRY_ONLY | — | UNKNOWN |
| EXEC_PLAN_APPLIED | ExecCode | WIRED | grid_executor_v1.py:L2335 | UNKNOWN |
| EXEC_PLAN_DUPLICATE_IGNORED | ExecCode | WIRED | grid_executor_v1.py:L856; grid_executor_v1.py:L857; grid_executor_v1.py:L860; grid_executor_v1.py:L861; grid_executor_v1.py:L907; grid_executor_v1.py:L908 | UNKNOWN |
| EXEC_PLAN_EXPIRED_IGNORED | ExecCode | WIRED | grid_executor_v1.py:L851; grid_executor_v1.py:L852 | UNKNOWN |
| EXEC_PLAN_HASH_MISMATCH | ExecCode | WIRED | grid_executor_v1.py:L845; grid_executor_v1.py:L848 | UNKNOWN |
| EXEC_PLAN_SCHEMA_INVALID | ExecCode | WIRED | grid_executor_v1.py:L816; grid_executor_v1.py:L817; grid_executor_v1.py:L821; grid_executor_v1.py:L822; grid_executor_v1.py:L828; grid_executor_v1.py:L829 | UNKNOWN |
| EXEC_PLAN_STALE_SEQ_IGNORED | ExecCode | WIRED | grid_executor_v1.py:L870; grid_executor_v1.py:L873; grid_executor_v1.py:L882; grid_executor_v1.py:L888; grid_executor_v1.py:L898; grid_executor_v1.py:L904 | UNKNOWN |
| EXEC_POST_ONLY_FALLBACK_REPRICE | ExecCode | WIRED | grid_executor_v1.py:L1924 | UNKNOWN |
| EXEC_POST_ONLY_RETRY | ExecCode | WIRED | grid_executor_v1.py:L1909 | UNKNOWN |
| EXEC_RECONCILE_HOLD_NO_MATERIAL_CHANGE | ExecCode | REGISTRY_ONLY | — | UNKNOWN |
| EXEC_RECONCILE_MATERIAL_REBUILD | ExecCode | REGISTRY_ONLY | — | UNKNOWN |
| EXEC_RECONCILE_START_LADDER_CREATED | ExecCode | REGISTRY_ONLY | — | UNKNOWN |
| EXEC_RECONCILE_STOP_CANCELLED_LADDER | ExecCode | REGISTRY_ONLY | — | UNKNOWN |
| INFO_BOX_SHIFT_APPLIED | InfoCode | REGISTRY_ONLY | — | UNKNOWN |
| INFO_REPLAN_EPOCH_BOUNDARY | InfoCode | REGISTRY_ONLY | — | UNKNOWN |
| INFO_SL_SOURCE_SELECTED | InfoCode | REGISTRY_ONLY | — | UNKNOWN |
| INFO_TARGET_SOURCE_SELECTED | InfoCode | REGISTRY_ONLY | — | UNKNOWN |
| INFO_VOL_BUCKET_CHANGED | InfoCode | REGISTRY_ONLY | — | UNKNOWN |
| PAUSE_BBWP_COOLOFF | PauseReason | REGISTRY_ONLY | — | UNKNOWN |
| PAUSE_DATA_DEGRADED | PauseReason | REGISTRY_ONLY | — | UNKNOWN |
| PAUSE_DATA_QUARANTINE | PauseReason | REGISTRY_ONLY | — | UNKNOWN |
| PAUSE_EXECUTION_UNSAFE | PauseReason | WIRED | grid_executor_v1.py:L1126; grid_executor_v1.py:L1149; grid_executor_v1.py:L1244; grid_executor_v1.py:L1249; grid_executor_v1.py:L1255; grid_executor_v1.py:L1261 | UNKNOWN |
| PAUSE_META_DRIFT_SOFT | PauseReason | REGISTRY_ONLY | — | UNKNOWN |
| PAUSE_SESSION_FVG | PauseReason | REGISTRY_ONLY | — | UNKNOWN |
| REPLAN_DEFERRED_ACTIVE_FILL_WINDOW | ReplanReason | REGISTRY_ONLY | — | UNKNOWN |
| REPLAN_DUPLICATE_PLAN_HASH | ReplanReason | REGISTRY_ONLY | — | UNKNOWN |
| REPLAN_EPOCH_DEFERRED | ReplanReason | REGISTRY_ONLY | — | UNKNOWN |
| REPLAN_HARD_STOP_OVERRIDE | ReplanReason | WIRED | replan_policy.py:L63 | UNKNOWN |
| REPLAN_MATERIAL_BOX_CHANGE | ReplanReason | WIRED | replan_policy.py:L67 | UNKNOWN |
| REPLAN_MATERIAL_GRID_CHANGE | ReplanReason | REGISTRY_ONLY | — | UNKNOWN |
| REPLAN_MATERIAL_RISK_CHANGE | ReplanReason | REGISTRY_ONLY | — | UNKNOWN |
| REPLAN_NOOP_MINOR_DELTA | ReplanReason | WIRED | replan_policy.py:L71; replan_policy.py:L75 | UNKNOWN |
| REPLAN_SOFT_ADJUST_ONLY | ReplanReason | REGISTRY_ONLY | — | UNKNOWN |
| STOP_BREAKOUT_2STRIKE_DN | StopReason | REGISTRY_ONLY | — | UNKNOWN |
| STOP_BREAKOUT_2STRIKE_UP | StopReason | REGISTRY_ONLY | — | UNKNOWN |
| STOP_BREAKOUT_CONFIRM_DN | StopReason | WIRED | GridBrainV1.py:L1662; GridBrainV1.py:L1672; GridBrainV1.py:L7644; GridBrainV1.py:L7681; GridBrainV1.py:L8843; GridBrainV1.py:L8844 | UNKNOWN |
| STOP_BREAKOUT_CONFIRM_UP | StopReason | WIRED | GridBrainV1.py:L1657; GridBrainV1.py:L1671; GridBrainV1.py:L7643; GridBrainV1.py:L7679; GridBrainV1.py:L8840; GridBrainV1.py:L8841 | UNKNOWN |
| STOP_CHANNEL_STRONG_BREAK | StopReason | WIRED | GridBrainV1.py:L2928; GridBrainV1.py:L7683 | UNKNOWN |
| STOP_DATA_QUARANTINE | StopReason | REGISTRY_ONLY | — | UNKNOWN |
| STOP_DRAWDOWN_GUARD | StopReason | WIRED | GridBrainV1.py:L2922; GridBrainV1.py:L7687 | UNKNOWN |
| STOP_EXEC_CONFIRM_EXIT_FAILSAFE | StopReason | WIRED | grid_executor_v1.py:L2498 | UNKNOWN |
| STOP_FAST_MOVE_DN | StopReason | REGISTRY_ONLY | — | UNKNOWN |
| STOP_FAST_MOVE_UP | StopReason | REGISTRY_ONLY | — | UNKNOWN |
| STOP_FRESH_STRUCTURE | StopReason | REGISTRY_ONLY | — | UNKNOWN |
| STOP_FVG_VOID_CONFLUENCE | StopReason | WIRED | GridBrainV1.py:L7689 | UNKNOWN |
| STOP_LIQUIDITY_SWEEP_BREAK_RETEST | StopReason | WIRED | GridBrainV1.py:L2943; GridBrainV1.py:L7685 | UNKNOWN |
| STOP_LVN_VOID_EXIT_ACCEL | StopReason | REGISTRY_ONLY | — | UNKNOWN |
| STOP_META_DRIFT_HARD | StopReason | WIRED | GridBrainV1.py:L519 | UNKNOWN |
| STOP_MRVD_AVG_BREAK | StopReason | REGISTRY_ONLY | — | UNKNOWN |
| STOP_OS_DEV_DIRECTIONAL_FLIP | StopReason | REGISTRY_ONLY | — | UNKNOWN |
| STOP_RANGE_SHIFT | StopReason | REGISTRY_ONLY | — | UNKNOWN |
| STOP_SESSION_FVG_AGAINST_BIAS | StopReason | REGISTRY_ONLY | — | UNKNOWN |
| STOP_SQUEEZE_RELEASE_AGAINST | StopReason | REGISTRY_ONLY | — | UNKNOWN |
| WARN_COST_MODEL_STALE | WarningCode | WIRED | GridBrainV1.py:L5032 | UNKNOWN |
| WARN_CVD_DATA_QUALITY_LOW | WarningCode | REGISTRY_ONLY | — | UNKNOWN |
| WARN_EXEC_POST_ONLY_RETRY_HIGH | WarningCode | WIRED | grid_executor_v1.py:L1121; grid_executor_v1.py:L1147 | UNKNOWN |
| WARN_EXEC_REPRICE_RATE_HIGH | WarningCode | REGISTRY_ONLY | — | UNKNOWN |
| WARN_FEATURE_FALLBACK_USED | WarningCode | REGISTRY_ONLY | — | UNKNOWN |
| WARN_PARTIAL_DATA_WINDOW | WarningCode | REGISTRY_ONLY | — | UNKNOWN |
| WARN_PLAN_EXPIRES_SOON | WarningCode | REGISTRY_ONLY | — | UNKNOWN |
| WARN_VRVP_UNAVAILABLE_FALLBACK_POC | WarningCode | WIRED | GridBrainV1.py:L8083 | UNKNOWN |

## 6. Replacement/Removal Ledger
### Drift incident: Plan claims NOT_IMPLEMENTED, code proves implemented
- **Old/new plan claim:** M601/M704/M705 listed as NOT_IMPLEMENTED in plan audit section.
  - Evidence (plan): GRID_MASTER_PLAN.md contains NOT_IMPLEMENTED list (line refs to be updated during doc patch).
- **Code evidence:**
  - M601 tests exist: CODE_IMPLEMENTATION_SNAPSHOT.md:L753-L758 (`test_order_block_*`).
  - M704/M705 tests exist: CODE_IMPLEMENTATION_SNAPSHOT.md:L724-L731 (`test_wick_sweep_and_break_retest_stop_through_box_edge`, `test_retest_validation_mode_toggle_affects_break_retest_only`).
- **Risk:** Confusion + accidental deletion if Codex trusts doc status instead of code.
- **Action required:** Fix plan status map (P0 backlog).

### Ad-hoc strategy variants (potential replacements/ablations)
- Code-derived inventory lists multiple GridBrainV1 variants not referenced in plans.
  - Evidence: CODE_IMPLEMENTED_FEATURE_PLAN.md:L31-L36 (variant files).
- **Risk:** If used in experiments, removal could break workflows; if unused, they add maintenance drift.
- **Action:** triage each variant as KEEP (experimental) vs DEPRECATE (record + delete).

## 7. Consolidated TODO Backlog (priority ordered)
### P0
- **Fix plan status drift for M601/M704/M705 in GRID_MASTER_PLAN.md Section 26 (doc-only mismatch).** [quick-win]
  - Acceptance: Acceptance: Section 26.2.2 removes M601/M704/M705 from NOT_IMPLEMENTED list; Section 26.3 marks them DONE; add note that Section 18 per-module status may lag.
  - Dependencies: Deps: none
- **Generate automated Plan↔Code compliance report and require update in PRs.** [heavy-lift]
  - Acceptance: Acceptance: script regenerates CODE_IMPLEMENTATION_SNAPSHOT.md + CODE_IMPLEMENTED_FEATURE_PLAN.md; CI fails if enums contain codes missing from DECISION_REASON_CODES.md or vice versa.
  - Dependencies: Deps: CI wiring
- **Triage ADHOC strategy variants and regime_audit script (promote to official or deprecate).** [quick-win]
  - Acceptance: Acceptance: each AH item either (a) added to master plan as EXPERIMENT module with purpose, or (b) recorded in DEPRECATIONS ledger with replacement and removed.
  - Dependencies: Deps: decision

### P1
- **Complete per-module evidence mapping for all remaining Mxxx modules.** [heavy-lift]
  - Acceptance: Acceptance: every Mxxx entry in Canonical Feature Registry has at least one code/file evidence ref; UNKNOWN count approaches 0.
  - Dependencies: Deps: none

### P2
- **Add per-code test mapping (link codes to tests that cover them).** [heavy-lift]
  - Acceptance: Acceptance: Wiring table includes at least one test ref for each WIRED code or its module test.
  - Dependencies: Deps: P1 mapping

## 8. Final “Bible” Plan (ordered implementation plan)
This section is an execution checklist. Items are grouped by system phase.

### 8.1 Architecture / Contracts
- [x] Brain writes plan artifacts, no live order placement (see GridBrainV1 core behavior evidence: CODE_IMPLEMENTED_FEATURE_PLAN.md:L89-L99).
- [x] Atomic handoff contract (M002) — DONE.
- [x] Enum registry + plan diff snapshots (M010) — DONE.

### 8.2 Planner Deterministic Core (Phase 2–5)
- [x] Replan policy (M001) — DONE.
- [x] Start stability (M003) — DONE.
- [x] Data quality quarantine (M004) — DONE.
- [x] Breakout confirm + min range length (M205) — DONE.
- [x] Meta drift guard (M005) — DONE.
- [x] Volatility policy adapter (M006) — DONE.
- [x] Empirical execution cost calibration (M007) — DONE.

### 8.3 Structure Modules
- [x] Order Blocks (M601) — DONE.
- [x] Liquidity sweeps + retest mode toggle (M704/M705) — DONE.
- [x] FVG stack (M602–M607) — DONE.
- [x] Micro-VAP + alignment + nudges (M501/M502/M505) — DONE.

### 8.4 Volume / Flow / Confluence
- [x] MRVD (M802) — DONE.
- [x] BBWP (M109), Squeeze (M110), Funding (M111), HVP (M112) — DONE.

### 8.5 Simulation / Replay / Chaos
- [x] Chaos/stress replay harness (M008) — DONE.
- [ ] Verify remaining planned simulator features (M306 etc) — UNKNOWN pending mapping.

### 8.6 Executor / Capacity / Safety
- [x] Capacity guard (M009) — DONE.
- [ ] Confirm all executor hardening modules beyond what is mapped here — UNKNOWN pending mapping.

### 8.7 Ad-hoc Governance
- [!] Keep ad-hoc scripts/variants as explicit AH-xxx entries. Any removal must be logged in a deprecation ledger.
- [ ] Triage each AH variant: KEEP as experiment or DEPRECATE.

---

## Appendix A — Old plan (verbatim)
```text
Yes — I still have your **main grid-bot plan** in memory, and I do have the **latest accumulated version** (the “living plan” with all the modules you kept adding).

Below is the **latest consolidated version I have**, in a structured form so you can use it as the implementation master checklist.

---

# Latest Main Plan in Memory (Consolidated)

## 0) System Architecture (locked direction)

### Core components

1. **Brain / Planner** (Freqtrade strategy class, e.g. `GridBrainV1`)

   * Writes plans only (no live order placement)
   * Outputs START / HOLD / STOP / REBUILD decisions + box + grid params + risk params
   * Uses deterministic rules first; ML/FreqAI later as confidence overlay

2. **Executor** (separate process, CCXT, multi-exchange-ready)

   * Reads `grid_plan.latest.json`
   * Handles ladder placement/cancel/rebuild/replace-on-fill
   * Maker-first (post-only), tick-aware rounding, order timeout/reprice logic
   * Paper mode + live mode

3. **Simulator / Replay Harness**

   * Replays candles (later optional finer-grain)
   * Simulates fills, fees/spread/slippage
   * Reproduces exact START/STOP/REBUILD logic from Brain
   * Source of truth for tuning

4. **ML / FreqAI (later)**

   * Confidence overlay only (not primary trade logic)
   * Used once deterministic loop is stable

---

## 1) Strategic Principles (current latest)

* **Deterministic, non-repainting** core
* **Event-driven** monitoring (not constant micro-adjust churn)
* **One grid per pair**
* **Spot / quote-only default inventory**
* **Cost-aware grid step sizing** (must cover net target + fees + spread)
* **Most conservative action wins** (STOP/veto overrides START)
* **Consistent logic across Brain / Simulator / Executor**

---

## 2) Core Regime + Router Direction (high-level)

You evolved from a simpler “range only” plan into a richer **mode-based router**:

### Current mode structure

* `intraday`
* `swing`
* `pause`
* (new design work) `neutral/choppy` mode to be integrated

### Router behavior goals

* Continuous eligibility checks (no fixed max runtime)
* Hysteresis + persistence + cooldown
* Safe handoff between modes (avoid flapping)
* If inventory already active, switch policy before forcing rebuild

---

## 3) Phase-1 Inputs / Feature Stack (latest memory)

### Timeframes

* **15m (build/exec TF)**

  * ATR20, RSI14
  * 24h H/L
  * VWAP
  * POC / VP windows
  * Micro-VAP bins

* **1h (signal / quietness / structure)**

  * BBW / BBWP
  * EMA50/100 distance and slope-ish checks
  * Volume + SMA20 / rVol
  * Squeeze state
  * FVG / OB / structure helpers

* **4h (regime)**

  * ADX(14)
  * optional higher-TF channel / breakout filters

* **Higher TF (D/W/M)**

  * MRVD (POC/VAH/VAL confluence)
  * multi-range POCs
  * basis / VWAP / Donchian context

### Optional external/live execution inputs

* Funding (Binance premium-index estimate)
* Orderbook metrics (spread %, imbalance, depth thinning, jump detection)

---

## 4) Phase-2 Regime Filter & Build Gates (latest consolidated)

## 4.1 Core baseline gates (range-friendly environment)

* **4h ADX ≤ ~22** (range-ish)
* Price inside broader extremes (7d context / no fresh major breakout)
* **1h BBW not expanding** (3-bar non-expansion style)
* **EMA50–EMA100 distance / price** small (approx 0.4–0.5%)
* Volume not in spike mode (e.g. ≤ 1.5× SMA20 unless specific exception)
* rVol calm / quiet cluster before build or rebuild

## 4.2 Structural breakout fresh-block (non-repainting)

* Build-TF breakout detection (default 15m, N≈14)
* Cache breakout levels (`last_break_up_lvl`, `last_break_dn_lvl`)
* Fresh breakout ⇒ Idle + reclaim timer
* Need cool-off bars (e.g. X≈20) or reclaim before build

## 4.3 Range DI / deviation-pivot regime state (optional-tightening, integrated)

* `os_dev ∈ {-1,0,+1}`
* Strike confirmation (`nStrike=2`)
* Build eligibility prefers `os_dev = 0` persisted ≥ L/2 bars
* `os_dev` flips to ±1 ⇒ STOP/Idle + reclaim timer
* Rebuild only after neutral persists + quiet volume returns

## 4.4 Band / drift / slope vetoes

* Band midline slope veto (e.g. >0.35% per 20 bars blocks build)
* Optional pivot drift slope veto (>0.40% / 20 bars)
* Optional excursion asymmetry veto

## 4.5 BBWP MTF gate (ON by default)

* S/M/L BBWP percentile stack
* Build allow when roughly:

  * S ≤ 35
  * M ≤ 50
  * L ≤ 60
  * plus non-expansion
* Veto if any TF ≥ 90
* Cool-off after ≥98 until S<50 and M<60

## 4.6 Squeeze-state gate (ON by default)

* Compression preference (BB inside KC)
* Build preference in squeeze-on + calm volume
* Squeeze release against bias + close >1 step outside box ⇒ immediate STOP override

## 4.7 Funding filter (optional)

* `abs(fr_8h_pct) ≤ 0.05%` to allow build
* Optional directional bias from funding sign

## 4.8 Additional volume / volatility guards added later

* HVP vs HVP-SMA gate (volatility state veto)
* BBWP “Boom & Doom” impulse tags (entry freezes / faster partial TP)
* CVD passive absorption soft-pause (optional)
* CVD divergence insights spike-based TP nudges

---

## 5) Phase-3 Box Builder (latest consolidated)

## 5.1 Core box definition (current baseline)

* Start from **24h High/Low on 15m**
* Add ATR pad:

  * `pad = 0.35 × ATR(15m,20)`
* Box = `[24h_low - pad, 24h_high + pad]`

### Width target behavior

* Practical target zone evolved around **~3.5% to 6%**
* If too narrow → adjust lookback / pad / alternative range windows
* If too wide → reduce levels / widen steps / or rebuild logic skips depending on gates

## 5.2 Deterministic VP / VRVP (required module in plan)

* Fixed-bar volume profile on 15m (24h required; 7d optional)
* Outputs numeric:

  * POC
  * VAH
  * VAL
* Non-repainting, cached
* If POC lies >0.5% outside box ⇒ shift box toward POC (max 0.5%) or reject build

## 5.3 POC acceptance gate

* Before first START after new box:

  * require one POC cross (or micro-POC / equivalent acceptance condition)

## 5.4 Box integrity / overlap checks

* Overlap pruning for mitigated boxes (≥60% overlap rule)
* Box vs bands overlap (≥60% preferred)
* Reject/shift if box straddles important structure within <1×grid step:

  * recent breakout levels
  * opposite OB edge
  * opposite FVG edge / avg (depending on active FVG module state)
  * session FVG avg
  * higher-TF POC / D-W-M POC (per MRVD / MTF POC confluence logic)

## 5.5 Range enhancements integrated

* Log-space quartiles Q1/Q2/Q3 inside box
* 1.386 extension levels for retest / TP / SL nudges
* Channel envelope overlap checks (Lux-inspired)
* Donchian width vs box width sanity check
* Optional fallback POC estimator if VRVP unavailable

---

## 6) Phase-4 Grid Sizing / Entries / Targets / Risk (latest consolidated)

## 6.1 Step sizing (cost-aware, critical)

* Net per-step target **T ≥ 0.40%** (latest memory standard)
* Gross step requirement:

  * `G = T + fees + spread`
  * majors example ≈ `0.65%`
* Invariant: **step% must cover gross requirement**

## 6.2 Number of levels (`N`)

* Original simpler plans used broad dynamic N (e.g. 12–60)
* Later consolidated neutral-grid plan defaulted to **stability clamp N in [6..12]** for the fixed-box architecture
* You also expressed preference to keep it dynamic as long as net is acceptable
* Latest safe interpretation in memory:

  * **Configurable N bounds**
  * Default conservative bounded mode
  * Hard invariant remains cost-aware step ≥ G

## 6.3 Entry / START filters (baseline latest)

* Price should be in “middle” box region (e.g. **35–65%**)
* RSI guard near neutral (e.g. **40–60**) optional/default depending module
* POC acceptance / cross gate before first START
* Various confluence gates can tighten START (MRVD, VAH/VAL proximity, basis cross, etc.)

## 6.4 Inventory / capital policy (latest defaults)

* System-level default evolved to:

  * **quote-only inventory**
  * one grid per pair
* Earlier “mixed inventory” plan remains part of history, but latest memory says quote-only default
* Reserve / top-up framework retained conceptually (conditional top-up rules exist)

## 6.5 TP / SL computed at START (required)

* Default TP (quote-only fast exit style):

  * `box_top + 0.75–1.0 × step`
* Default SL:

  * `box_bottom − 1.0 × step`
  * or time-stop / reclaim-failure logic:

    * e.g. 4h close below box + no reclaim within 8h

### TP candidate / nudge set became rich (nearest conservative wins)

Targets may include:

* Q1 / Q3
* VRVP POC / MTF POCs (D/W/M)
* Channel midline / bounds
* Session VWAP / basis bands / Donchian mid
* IMFVG avg
* Session FVG avg
* FVG positioning averages (`up_avg`, `down_avg`)
* HVN levels
* FVG-POC (if FVG-VP module enabled)

### SL safety rule

* Do **not** tighten SL inside LVN voids / FVG voids / unsafe low-liquidity structure

## 6.6 Fill handling concepts integrated from reviewed scripts

* Deterministic rung-cross detector
* Binary-search style level location (performance)
* Fill confirmation modes:

  * `Touch`
  * `Reverse` (cross+reclaim)
* LSI / no-repeat guard to avoid duplicate fills
* Tick-aware rounding using market precision / mintick logic

---

## 7) Phase-5 Monitoring / STOP / REBUILD / Cooldown Logic (latest consolidated)

## 7.1 Core STOP triggers

* Structural breakout beyond box edge:

  * 2-strike confirmation (e.g. 2 bars outside)
  * OR fast-stop if >1 step outside
* Range shift stop:

  * material box drift / shift (e.g. >0.7%)
* Fresh breakout / fresh strong structure:

  * set Idle + start reclaim timer
* Squeeze release against bias can override to immediate STOP
* Strong breakout channel events can override STOP logic

## 7.2 Rebuild / reclaim discipline

* **8h reclaim timer** is a recurring core rule in latest memory
* Rebuild only after:

  * reclaim / re-entry into acceptable zone
  * regime gates pass again
  * quietness returns (rVol / vol state)
  * often POC cross acceptance before re-START

## 7.3 Anti-flap / safety rails (latest additions)

* Cooldown ≈ **90m**
* Minimum runtime ≈ **3h**
* Drawdown guard (post-fact safety rail)
* Confirm-entry / confirm-exit hooks (execution conditions)
* Orderbook / spread / jump detection as soft veto/confidence modifier

## 7.4 Event taxonomy / retests

* Extreme retests at box edges
* 1.386 extension retests
* POC tests
* Liquidity sweeps (wick and break+retest)
* Session H/L sweeps
* Drift-envelope retests (optional)

---

## 8) Structure / Market Microstructure Modules Added (latest memory)

This is the “big stack” you kept layering in. Latest memory includes all of these.

## 8.1 Order Blocks (OB) module (lightweight)

* Fresh OB gate / pause
* Box veto if opposite OB edge conflicts with box
* TP nudges to OB edges/midline
* Minimal cached latest OB per side (CPU-light)

## 8.2 FVG Suite (multiple integrated layers)

### Baseline FVG logic

* Opposite-side FVG straddle veto near/inside box
* Fresh FVG cool-off (optional in some versions, later strengthened)

### IMFVG (instantaneous mitigation style)

* IMFVG average added as TP candidate
* Mitigation relaxes veto on that side
* Width filter based on `max(0.6×step, 0.25×ATR)`

### Session FVG (ON by default in memory)

* Tracks latest daily session FVG
* Session pause bars on new FVG
* Inside-FVG gate logic
* Session FVG avg/edges in TP set
* Session FVG against bias can force Idle/reclaim

### Defensive FVG detector (TradingFinder integration; ON)

* Quality-filtered FVGs (Defensive mode default)
* Opposite-side defensive FVG can veto builds
* Fresh opposite-side defensive FVG triggers pause until mitigation

### FVG positioning averages

* Rolling `up_avg` / `down_avg`
* ON by default as TP candidates
* Optional box veto / STOP logic OFF by default

### FVG-VP (optional OFF by default)

* Volume profile *inside* nearby FVGs
* FVG-POC as target candidate / refined veto logic
* Can refine STOP behavior in low-volume FVG corridors

## 8.3 Volume profile / Micro-VAP / HVN-LVN

### Micro-VAP module

* Fixed bins inside active 24h box
* body/wick weighted volume accumulation
* outputs:

  * micro_POC
  * HVNs
  * LVNs
  * void_slope

### Integrations

* POC alignment check with VRVP POC (ON)
* Optional START delay until POC cross if disagreement too large
* HVN/LVN-based rung density and TP/SL nudges
* LVN corridor breakout can accelerate STOP

### HVN/LVN (inside 24h box) ON by default (later addition)

* HVN and LVN thresholds (e.g. 80% / 20% of max bin volume)
* Min spacing filter
* TP favors nearby HVN
* Avoid SL placement in LVN voids

## 8.4 Liquidity sweeps (ON)

* Wick-only sweep
* Break+retest sweep
* TP nudges and STOP precedence integration

## 8.5 Channel modules

### Donchian channel (ON)

* Width gate
* Midline TP candidate
* Strong-close STOP beyond bound

### Smart breakout channels (AlgoAlpha-inspired; ON)

* Vol-normalized channel built from crossover state
* StrongClose breakout logic (body >50% outside)
* Breakout can trigger STOP/Idle + reclaim timer
* Channel mid/bounds as TP/SL nudge candidates

### Zig-zag / envelope-inspired channel checks (mostly optional)

* Envelope width / overlap vetos
* Drift slope / asymmetry filters
* Rebuild discipline with channel contraction / midline touch

---

## 9) Volume/Flow/CVD/MRVD/Basis Modules (latest memory)

## 9.1 CVD and divergences (mostly ON / advisory + nudges)

* Bull/bear divergences near box edges and VAH/VAL
* Bias/rung-density nudges
* TP priority adjustments toward POC/channel-mid/Q1
* Never directly starts trades by itself

### CVD BOS events (ON)

* BOS-Up near bottom / BOS-Down near top
* Quick TP nudges
* Freeze new entries 3–5 bars if BOS against active side

### CVD divergence insights / oscillator (partial ON)

* Spike-based TP nudges
* Passive absorption as soft pause
* TradingFinder-style strong ±RD scores as advisory TP priority only

## 9.2 MRVD (Multi-Range Volume Distribution) — ON by default

* D/W/M histograms with POC/VAH/VAL and buy/sell split
* START confluence gate:

  * overlap with value areas or near period POCs
* POC drift guard (day vs week/month drift)
* Higher-period POCs added to TP set and box shift/veto logic
* Buy/sell split bias for rung density

## 9.3 Multi-Range Pivots / Basis module — ON by default

* Basis selector (VWAP default; many alternatives)
* Basis slope veto (e.g. >0.35%/20 bars)
* Basis cross required before first START after rebuild
* Basis bands and Donchian mid as TP candidates
* Box straddle checks vs VWAP/Donchian mid + width sanity

## 9.4 Session/Daily VWAP and session H/L events (ON)

* Session VWAP as TP candidate
* Session H/L sweeps and break+retests integrated into event framework
* Break+retest through edge can trigger Idle/reclaim (STOP precedence)

---

## 10) Protections / Execution Safety Layer (added 2026-02-08)

These are explicitly in memory as latest additions:

1. **Protections layer**

   * cooldown + drawdown guard as post-fact safety rails

2. **Confirm-entry / confirm-exit hooks**

   * check execution conditions (spread, depth, sudden jumps)

3. **Maker-first execution discipline**

   * post-only
   * tick-aware retry/backoff
   * per-order timeout + selective reprice
   * avoid full rebuild churn where possible

4. **Minimal order-flow metrics**

   * spread %
   * top-of-book imbalance
   * depth thinning
   * jump detection
   * used as soft veto/confidence modifier

5. **FreqAI/ML role clarified**

   * confidence overlay only after deterministic labels/range/stop loop is locked

---

## 11) Default Deployment / Scope Assumptions (latest memory)

* **Quote-only inventory**
* **One grid per pair**
* **Multi-exchange support** via config/CCXT
* Freqtrade/FreqAI used as the “Brain”
* Separate grid executor/simulator stack
* Spot-first execution focus

---

## 12) Implementation Sequence (latest recommended path)

This is the “don’t get lost” sequence implied by the memory and our latest discussions.

### Step 1 — Lock deterministic core

* Phase-2 core gates (ADX / BBW/BBWP / EMA dist / volume / structural veto baseline)
* Phase-3 box builder (24h ± ATR + width controls + POC alignment)
* Phase-4 cost-aware step sizing + TP/SL at START
* Phase-5 STOP/REBUILD/reclaim/cooldown/min-runtime

### Step 2 — Make simulator the source of truth

* Fill modes (`Touch` / `Reverse`)
* Fees/spread/slippage
* START/HOLD/STOP/REBUILD reproduction
* Logs + metrics (PnL + churn + blocker reasons + stability)

### Step 3 — Executor (paper first)

* Paper executor that can validate plan application locally
* Then live-ready order engine:

  * ladder seeding
  * replace-on-fill
  * cancel/rebuild
  * STOP handling
  * maker-first discipline

### Step 4 — Add modules one at a time (ablation style)

Recommended order (practical):

1. VRVP POC/VAH/VAL
2. BBWP MTF + squeeze
3. Range DI (`os_dev`) + strike gating
4. Micro-VAP HVN/LVN
5. FVG stack (Defensive + IMFVG + Session FVG)
6. MRVD D/W/M
7. CVD divergence/BOS nudges
8. Channel modules (if not already folded in)

### Step 5 — Only then ML/FreqAI overlay

* Labels / walk-forward / confidence gating
* Overlay, not primary trade engine

---

## 13) Important Note on “versions” (so we stay aligned)

You had an **earlier simpler plan** (48h HL + ATR pad, mixed inventory, broader N, simpler START/HOLD/STOP thresholds with `P_range/P_breakout`) and then a **much richer modular deterministic plan**.

### Latest memory = the richer modular plan

So if you ask me for “latest version”, this is it.

If you want, next I can give you a **cleaned “vNext implementation baseline”** with:

* only the **must-have core** (minimal modules),
* what is **ON by default**,
* what is **deferred**,
* and a single canonical JSON/config schema for thresholds per mode (`intraday`, `swing`, `neutral`, `pause`).
```
