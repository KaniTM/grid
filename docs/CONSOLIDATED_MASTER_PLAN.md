# CONSOLIDATED MASTER PLAN (Execution-First, Code-First, Human-Readable)

Generated: 2026-02-28 11:54:37 UTC

## 1) Executive Scope
- Purpose: one implementation-grade master plan that keeps every shipped feature (including ad-hoc modules), plus old-plan and new-plan intent, with code-evidence anchors.
- Evidence policy: runtime code is source of truth; plan files are intent unless confirmed in code.
- Read order recommendation: Section 4 (feature cards) -> Section 9 (lifecycle policy) -> Section 10 (prioritized backlog) -> Section 11 (execution order) -> appendices.
- Historical inputs reviewed during consolidation (now removed from repo): `docs/old_plan.txt`, `docs/GRID_MASTER_PLAN.md`, `docs/chatgpt.txt`.

## 2) Status Legend
- `DONE`: implemented and wired in runtime paths, with code anchors.
- `PARTIAL`: substantial implementation exists, but contract scope is incomplete.
- `NOT_IMPLEMENTED`: contract has no runtime implementation yet.
- `REGISTRY_ONLY`: canonical code exists in `core/enums.py` but has no runtime emitter.
- `DEPRECATED_REPLACED`: old behavior/intent was replaced by a newer path and is tracked in replacement cards.

## 3) Audit Snapshot
- Feature modules audited: `95` (`DONE=81`, `PARTIAL=8`, `NOT_IMPLEMENTED=6`).
- Canonical codes audited: `200` (`WIRED=117`, `REGISTRY_ONLY=83`).
- Output emphasis: every feature has a detailed card with implementation guidance, including DONE features.

## 4) Canonical Feature Cards (Mxxx + Ad-hoc)

### Phase A — Governance / Handoff / Stability
- Phase counts: DONE=10 | PARTIAL=0 | NOT_IMPLEMENTED=0

#### M001 - Parameter Inertia + Epoch Replan Policy
`Status`: DONE
`Source`: NEW_PLAN
`Coverage`: old=N | new=Y | code=Y

`Purpose`
- Parameter Inertia + Epoch Replan Policy exists to enforce this contract: Computes materiality class (`noop/soft/material/hardstop`) and gates publish/defer decisions per epoch and delta thresholds.

`Current Implementation`
- Implemented behavior today: Computes materiality class (`noop/soft/material/hardstop`) and gates publish/defer decisions per epoch and delta thresholds.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `planner/replan_policy.py:26`; `planner/replan_policy.py:44`; `freqtrade/user_data/strategies/GridBrainV1.py:1777`; `freqtrade/user_data/strategies/GridBrainV1.py:8469`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:168`

`Canonical Codes`
- REPLAN_*

`Implementation Playbook`
1. Use `planner/replan_policy.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`REPLAN_*`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:168`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M002 - Atomic Brain→Executor Handoff + Idempotency Contract
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Atomic Brain→Executor Handoff + Idempotency Contract exists to enforce this contract: Uses atomic writes and signature fields (`plan_id`, `decision_seq`, `plan_hash`) with executor-side intake validation for idempotency.

`Current Implementation`
- Implemented behavior today: Uses atomic writes and signature fields (`plan_id`, `decision_seq`, `plan_hash`) with executor-side intake validation for idempotency.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `core/atomic_json.py:12`; `freqtrade/user_data/strategies/GridBrainV1.py:1774`; `freqtrade/user_data/strategies/GridBrainV1.py:9571`; `freqtrade/user_data/scripts/grid_executor_v1.py:814`
- Tests: `freqtrade/user_data/tests/test_executor_hardening.py:260`

`Canonical Codes`
- EXEC_PLAN_*

`Implementation Playbook`
1. Use `core/atomic_json.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`EXEC_PLAN_*`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_executor_hardening.py:260`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M003 - Global Start Stability Score (k-of-n)
`Status`: DONE
`Source`: NEW_PLAN
`Coverage`: old=N | new=Y | code=Y

`Purpose`
- Global Start Stability Score (k-of-n) exists to enforce this contract: Builds k-of-n start stability score from gate checks and blocks START when score/required-k fail.

`Current Implementation`
- Implemented behavior today: Builds k-of-n start stability score from gate checks and blocks START when score/required-k fail.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `planner/start_stability.py:9`; `freqtrade/user_data/strategies/GridBrainV1.py:1767`; `freqtrade/user_data/strategies/GridBrainV1.py:7866`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:292`

`Canonical Codes`
- BLOCK_START_STABILITY_LOW

`Implementation Playbook`
1. Use `planner/start_stability.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_START_STABILITY_LOW`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:292`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M004 - Data Quality Quarantine State
`Status`: DONE
`Source`: NEW_PLAN
`Coverage`: old=N | new=Y | code=Y

`Purpose`
- Data Quality Quarantine State exists to enforce this contract: Runs candle-quality checks (gaps, stale, misalign, zero-volume anomalies) and escalates planner health to degraded/quarantine.

`Current Implementation`
- Implemented behavior today: Runs candle-quality checks (gaps, stale, misalign, zero-volume anomalies) and escalates planner health to degraded/quarantine.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `data/data_quality_assessor.py:12`; `freqtrade/user_data/strategies/GridBrainV1.py:1333`; `freqtrade/user_data/strategies/GridBrainV1.py:1750`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:75`; `freqtrade/user_data/tests/test_phase3_validation.py:283`

`Canonical Codes`
- BLOCK_DATA_*, EVENT_DATA_*

`Implementation Playbook`
1. Use `data/data_quality_assessor.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_DATA_*, EVENT_DATA_*`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:75`; `freqtrade/user_data/tests/test_phase3_validation.py:283`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M005 - Meta Drift Guard (Page-Hinkley/CUSUM style)
`Status`: DONE
`Source`: NEW_PLAN
`Coverage`: old=N | new=Y | code=Y

`Purpose`
- Meta Drift Guard (Page-Hinkley/CUSUM style) exists to enforce this contract: Observes multi-channel drift (z-score + CUSUM + Page-Hinkley) and escalates to soft pause or hard stop actions.

`Current Implementation`
- Implemented behavior today: Observes multi-channel drift (z-score + CUSUM + Page-Hinkley) and escalates to soft pause or hard stop actions.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `risk/meta_drift_guard.py:25`; `freqtrade/user_data/strategies/GridBrainV1.py:4791`; `freqtrade/user_data/strategies/GridBrainV1.py:7357`
- Tests: `freqtrade/user_data/tests/test_meta_drift_replay.py:53`; `freqtrade/user_data/tests/test_phase3_validation.py:734`

`Canonical Codes`
- BLOCK_META_DRIFT_SOFT, STOP_META_DRIFT_HARD, EVENT_META_DRIFT_*

`Implementation Playbook`
1. Use `risk/meta_drift_guard.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_META_DRIFT_SOFT, STOP_META_DRIFT_HARD, EVENT_META_DRIFT_*`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_meta_drift_replay.py:53`; `freqtrade/user_data/tests/test_phase3_validation.py:734`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M006 - Volatility Policy Adapter (deterministic)
`Status`: DONE
`Source`: NEW_PLAN
`Coverage`: old=N | new=Y | code=Y

`Purpose`
- Volatility Policy Adapter (deterministic) exists to enforce this contract: Adapts N bounds/width/cooldown/runtime policy deterministically by volatility bucket and ATR/BBWP context.

`Current Implementation`
- Implemented behavior today: Adapts N bounds/width/cooldown/runtime policy deterministically by volatility bucket and ATR/BBWP context.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `planner/volatility_policy_adapter.py:8`; `planner/volatility_policy_adapter.py:258`; `freqtrade/user_data/strategies/GridBrainV1.py:6451`; `freqtrade/user_data/strategies/GridBrainV1.py:5067`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:542`

`Canonical Codes`
- INFO_VOL_BUCKET_CHANGED

`Implementation Playbook`
1. Use `planner/volatility_policy_adapter.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`INFO_VOL_BUCKET_CHANGED`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:542`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M007 - Empirical Execution Cost Calibration Loop
`Status`: DONE
`Source`: NEW_PLAN
`Coverage`: old=N | new=Y | code=Y

`Purpose`
- Empirical Execution Cost Calibration Loop exists to enforce this contract: Combines static and empirical execution-cost floors; publishes lifecycle calibration artifacts and stale warnings.

`Current Implementation`
- Implemented behavior today: Combines static and empirical execution-cost floors; publishes lifecycle calibration artifacts and stale warnings.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `analytics/execution_cost_calibrator.py:9`; `freqtrade/user_data/strategies/GridBrainV1.py:4881`; `freqtrade/user_data/scripts/grid_executor_v1.py:1579`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:557`; `freqtrade/user_data/tests/test_executor_hardening.py:365`

`Canonical Codes`
- WARN_COST_MODEL_STALE

`Implementation Playbook`
1. Use `analytics/execution_cost_calibrator.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`WARN_COST_MODEL_STALE`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:557`; `freqtrade/user_data/tests/test_executor_hardening.py:365`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M008 - Stress/Chaos Replay Harness
`Status`: DONE
`Source`: NEW_PLAN
`Coverage`: old=N | new=Y | code=Y

`Purpose`
- Stress/Chaos Replay Harness exists to enforce this contract: Replay simulator supports validated chaos profiles (latency, reject bursts, spread shocks, partial fills, data gaps) with delta reporting.

`Current Implementation`
- Implemented behavior today: Replay simulator supports validated chaos profiles (latency, reject bursts, spread shocks, partial fills, data gaps) with delta reporting.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `sim/chaos_profiles.py:10`; `freqtrade/user_data/scripts/grid_simulator_v1.py:1229`; `freqtrade/user_data/scripts/grid_simulator_v1.py:1303`; `freqtrade/user_data/scripts/grid_simulator_v1.py:2120`
- Tests: `freqtrade/user_data/tests/test_chaos_replay_harness.py:66`; `freqtrade/user_data/tests/test_stress_replay_standard_validation.py:44`

`Canonical Codes`
- EVENT_POST_ONLY_REJECT_BURST (chaos-path impact)

`Implementation Playbook`
1. Use `sim/chaos_profiles.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`EVENT_POST_ONLY_REJECT_BURST (chaos-path impact)`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_chaos_replay_harness.py:66`; `freqtrade/user_data/tests/test_stress_replay_standard_validation.py:44`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M009 - Depth-Aware Capacity Cap
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Depth-Aware Capacity Cap exists to enforce this contract: Capacity guard computes dynamic caps from spread/depth/notional and enforces rung caps in executor seeding/reconcile paths.

`Current Implementation`
- Implemented behavior today: Capacity guard computes dynamic caps from spread/depth/notional and enforces rung caps in executor seeding/reconcile paths.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `execution/capacity_guard.py:66`; `freqtrade/user_data/scripts/grid_executor_v1.py:1357`; `freqtrade/user_data/scripts/grid_executor_v1.py:1413`
- Tests: `freqtrade/user_data/tests/test_executor_hardening.py:306`

`Canonical Codes`
- BLOCK_CAPACITY_THIN, EXEC_CAPACITY_*

`Implementation Playbook`
1. Use `execution/capacity_guard.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_CAPACITY_THIN, EXEC_CAPACITY_*`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_executor_hardening.py:306`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M010 - Enum Registry + Plan Diff Snapshots
`Status`: DONE
`Source`: NEW_PLAN
`Coverage`: old=N | new=Y | code=Y

`Purpose`
- Enum Registry + Plan Diff Snapshots exists to enforce this contract: Central enums + plan hash/diff snapshots + decision/event logs provide canonical observability and reproducible plan changes.

`Current Implementation`
- Implemented behavior today: Central enums + plan hash/diff snapshots + decision/event logs provide canonical observability and reproducible plan changes.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `core/enums.py:145`; `core/plan_signature.py:95`; `freqtrade/user_data/strategies/GridBrainV1.py:2994`; `freqtrade/user_data/strategies/GridBrainV1.py:9521`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:896`

`Canonical Codes`
- ALL canonical enums

`Implementation Playbook`
1. Use `core/enums.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`ALL canonical enums`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:896`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

### Phase B — Regime + Build Gates
- Phase counts: DONE=12 | PARTIAL=1 | NOT_IMPLEMENTED=0

#### M101 - ADX Gate (4h)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- ADX Gate (4h) exists to enforce this contract: 4h ADX gate with hysteresis/rising confirmation blocks and stop escalation.

`Current Implementation`
- Implemented behavior today: 4h ADX gate with hysteresis/rising confirmation blocks and stop escalation.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:1118`; `freqtrade/user_data/strategies/GridBrainV1.py:6371`; `freqtrade/user_data/strategies/GridBrainV1.py:1739`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:125`

`Canonical Codes`
- BLOCK_ADX_HIGH

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_ADX_HIGH`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:125`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M102 - BBW Quietness Gate (1h)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- BBW Quietness Gate (1h) exists to enforce this contract: 1h BBW percentile + non-expansion gate is required for range eligibility.

`Current Implementation`
- Implemented behavior today: 1h BBW percentile + non-expansion gate is required for range eligibility.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:1679`; `freqtrade/user_data/strategies/GridBrainV1.py:6350`; `freqtrade/user_data/strategies/GridBrainV1.py:1741`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:231`

`Canonical Codes`
- BLOCK_BBW_EXPANDING

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_BBW_EXPANDING`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:231`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M103 - EMA50/EMA100 Compression Gate (1h)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- EMA50/EMA100 Compression Gate (1h) exists to enforce this contract: EMA50/EMA100 distance gate limits trend separation before START.

`Current Implementation`
- Implemented behavior today: EMA50/EMA100 distance gate limits trend separation before START.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:6245`; `freqtrade/user_data/strategies/GridBrainV1.py:6357`; `freqtrade/user_data/strategies/GridBrainV1.py:1743`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:125`

`Canonical Codes`
- BLOCK_EMA_DIST

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_EMA_DIST`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:125`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M104 - rVol Calm Gate (1h/15m)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- rVol Calm Gate (1h/15m) exists to enforce this contract: 1h volume ratio and 15m rVol calm checks gate START.

`Current Implementation`
- Implemented behavior today: 1h volume ratio and 15m rVol calm checks gate START.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:6251`; `freqtrade/user_data/strategies/GridBrainV1.py:6358`; `freqtrade/user_data/strategies/GridBrainV1.py:1745`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:125`

`Canonical Codes`
- BLOCK_RVOL_SPIKE

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_RVOL_SPIKE`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:125`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M105 - 7d Context / Extremes Sanity
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- 7d Context / Extremes Sanity exists to enforce this contract: 7d containment/extremes context gate blocks out-of-context builds.

`Current Implementation`
- Implemented behavior today: 7d containment/extremes context gate blocks out-of-context builds.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:5983`; `freqtrade/user_data/strategies/GridBrainV1.py:6433`; `freqtrade/user_data/strategies/GridBrainV1.py:1747`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:125`

`Canonical Codes`
- BLOCK_7D_EXTREME_CONTEXT

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_7D_EXTREME_CONTEXT`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:125`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M106 - Structural Breakout Fresh-Block + Cached Break Levels
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Structural Breakout Fresh-Block + Cached Break Levels exists to enforce this contract: Detects fresh structural breakout, caches breakout levels, and enforces fresh-block/reclaim discipline.

`Current Implementation`
- Implemented behavior today: Detects fresh structural breakout, caches breakout levels, and enforces fresh-block/reclaim discipline.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:1539`; `freqtrade/user_data/strategies/GridBrainV1.py:1696`; `freqtrade/user_data/strategies/GridBrainV1.py:6738`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:157`; `freqtrade/user_data/tests/test_phase3_validation.py:238`

`Canonical Codes`
- BLOCK_FRESH_BREAKOUT, EVENT_BREAKOUT_*

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_FRESH_BREAKOUT, EVENT_BREAKOUT_*`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:157`; `freqtrade/user_data/tests/test_phase3_validation.py:238`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M107 - Range DI / Deviation-Pivot `os_dev` (Misu-style)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Range DI / Deviation-Pivot `os_dev` (Misu-style) exists to enforce this contract: `os_dev` regime state with strike confirmation and neutral persistence gating.

`Current Implementation`
- Implemented behavior today: `os_dev` regime state with strike confirmation and neutral persistence gating.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:669`; `freqtrade/user_data/strategies/GridBrainV1.py:4169`; `freqtrade/user_data/strategies/GridBrainV1.py:7507`
- Tests: `freqtrade/user_data/tests/test_partial_module_completion.py:293`

`Canonical Codes`
- BLOCK_OS_DEV_*

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_OS_DEV_*`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_partial_module_completion.py:293`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M108 - Band Slope / Drift Slope / Excursion Asymmetry Vetoes
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Band Slope / Drift Slope / Excursion Asymmetry Vetoes exists to enforce this contract: Band-slope, drift-slope, and excursion-asymmetry vetoes are integrated and reason-coded.

`Current Implementation`
- Implemented behavior today: Band-slope, drift-slope, and excursion-asymmetry vetoes are integrated and reason-coded.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:1189`; `freqtrade/user_data/strategies/GridBrainV1.py:6774`; `freqtrade/user_data/strategies/GridBrainV1.py:7732`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:186`; `freqtrade/user_data/tests/test_phase3_validation.py:197`

`Canonical Codes`
- BLOCK_BAND_SLOPE_HIGH, BLOCK_DRIFT_SLOPE_HIGH, BLOCK_EXCURSION_ASYMMETRY

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_BAND_SLOPE_HIGH, BLOCK_DRIFT_SLOPE_HIGH, BLOCK_EXCURSION_ASYMMETRY`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:186`; `freqtrade/user_data/tests/test_phase3_validation.py:197`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M109 - BBWP MTF Gate + Cool-off
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- BBWP MTF Gate + Cool-off exists to enforce this contract: BBWP S/M/L gate, extreme veto, and cooloff lifecycle are fully wired.

`Current Implementation`
- Implemented behavior today: BBWP S/M/L gate, extreme veto, and cooloff lifecycle are fully wired.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:627`; `freqtrade/user_data/strategies/GridBrainV1.py:6394`; `freqtrade/user_data/strategies/GridBrainV1.py:7740`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:144`

`Canonical Codes`
- BLOCK_BBWP_HIGH, COOLOFF_BBWP_EXTREME

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_BBWP_HIGH, COOLOFF_BBWP_EXTREME`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:144`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M110 - Squeeze State Gate (BB inside KC) + release STOP override
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Squeeze State Gate (BB inside KC) + release STOP override exists to enforce this contract: Squeeze state gate plus release-against-bias stop override and TP nudge behavior.

`Current Implementation`
- Implemented behavior today: Squeeze state gate plus release-against-bias stop override and TP nudge behavior.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:1149`; `freqtrade/user_data/strategies/GridBrainV1.py:7575`; `freqtrade/user_data/strategies/GridBrainV1.py:7774`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:223`

`Canonical Codes`
- BLOCK_SQUEEZE_RELEASE_AGAINST_BIAS, STOP_SQUEEZE_RELEASE_AGAINST

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_SQUEEZE_RELEASE_AGAINST_BIAS, STOP_SQUEEZE_RELEASE_AGAINST`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:223`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M111 - Funding Filter (FR 8h est, Binance premium index)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Funding Filter (FR 8h est, Binance premium index) exists to enforce this contract: Optional funding filter and directional funding bias are wired into gating.

`Current Implementation`
- Implemented behavior today: Optional funding filter and directional funding bias are wired into gating.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:1209`; `freqtrade/user_data/strategies/GridBrainV1.py:6440`; `freqtrade/user_data/strategies/GridBrainV1.py:7755`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:203`

`Canonical Codes`
- BLOCK_FUNDING_FILTER

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_FUNDING_FILTER`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:203`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M112 - HVP Gate (HVP vs HVPSMA + BBW expansion)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- HVP Gate (HVP vs HVPSMA + BBW expansion) exists to enforce this contract: Optional HVP expansion gate and quiet-exit TP bias are implemented.

`Current Implementation`
- Implemented behavior today: Optional HVP expansion gate and quiet-exit TP bias are implemented.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:1216`; `freqtrade/user_data/strategies/GridBrainV1.py:7011`; `freqtrade/user_data/strategies/GridBrainV1.py:7757`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:271`

`Canonical Codes`
- BLOCK_HVP_EXPANDING

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_HVP_EXPANDING`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:271`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M113 - Boom & Doom Impulse Guard
`Status`: PARTIAL
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Boom & Doom Impulse Guard exists to enforce this contract: Equivalent behavior exists via BBWP expansion/extreme controls, but explicit Boom/Doom tagging model is not separated.

`Current Implementation`
- Implemented behavior today: Equivalent behavior exists via BBWP expansion/extreme controls, but explicit Boom/Doom tagging model is not separated.
- Coverage note: Add explicit Boom/Doom impulse classifier + event emissions + tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:6401`; `freqtrade/user_data/strategies/GridBrainV1.py:7650`; `freqtrade/user_data/strategies/GridBrainV1.py:8675`
- Tests: None listed.

`Canonical Codes`
- EVENT_BBWP_EXTREME (planned, not emitted)

`Implementation Playbook`
1. Implement missing scope first: Add explicit Boom/Doom impulse classifier + event emissions + tests.
2. Add/adjust runtime logic in `freqtrade/user_data/strategies/GridBrainV1.py` and dependent modules listed in evidence anchors.
3. Emit/align canonical codes (`EVENT_BBWP_EXTREME (planned, not emitted)`) so behavior is externally observable.
4. Add deterministic tests for missing paths and extend suites at: None listed.
5. Promote PARTIAL to DONE only when both behavior and tests are complete.

`Gap / Action`
- Add explicit Boom/Doom impulse classifier + event emissions + tests.

### Phase C — Box Builder + Validation
- Phase counts: DONE=12 | PARTIAL=1 | NOT_IMPLEMENTED=0

#### M201 - Core 24h ± ATR Box Builder
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Core 24h ± ATR Box Builder exists to enforce this contract: 24h high/low ± ATR pad box builder with deterministic lookback switching.

`Current Implementation`
- Implemented behavior today: 24h high/low ± ATR pad box builder with deterministic lookback switching.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:3104`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:16`

`Canonical Codes`
- BLOCK_BOX_WIDTH_*

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_BOX_WIDTH_*`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:16`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M202 - Box Width Target / Hard-Soft Veto Policy
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Box Width Target / Hard-Soft Veto Policy exists to enforce this contract: Width target policy (min/max, rebuild-skip behavior) enforces hard/soft width constraints.

`Current Implementation`
- Implemented behavior today: Width target policy (min/max, rebuild-skip behavior) enforces hard/soft width constraints.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:3127`; `freqtrade/user_data/strategies/GridBrainV1.py:6617`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:305`

`Canonical Codes`
- BLOCK_BOX_WIDTH_TOO_WIDE

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_BOX_WIDTH_TOO_WIDE`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:305`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M204 - Percent-of-Average Width Veto
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Percent-of-Average Width Veto exists to enforce this contract: Rolling percent-of-average width veto blocks oversized rebuild candidates.

`Current Implementation`
- Implemented behavior today: Rolling percent-of-average width veto blocks oversized rebuild candidates.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:1418`; `freqtrade/user_data/strategies/GridBrainV1.py:6513`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:410`

`Canonical Codes`
- BLOCK_BOX_WIDTH_TOO_WIDE

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_BOX_WIDTH_TOO_WIDE`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:410`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M205 - Minimum Range Length + Breakout Confirm Bars
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Minimum Range Length + Breakout Confirm Bars exists to enforce this contract: Minimum range length and breakout confirm bars (buffered, multi-mode) are wired.

`Current Implementation`
- Implemented behavior today: Minimum range length and breakout confirm bars (buffered, multi-mode) are wired.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:1622`; `freqtrade/user_data/strategies/GridBrainV1.py:6877`
- Tests: `freqtrade/user_data/tests/test_min_range_and_breakout_confirm.py:20`

`Canonical Codes`
- BLOCK_MIN_RANGE_LEN_NOT_MET, BLOCK/STOP_BREAKOUT_CONFIRM_*

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_MIN_RANGE_LEN_NOT_MET, BLOCK/STOP_BREAKOUT_CONFIRM_*`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_min_range_and_breakout_confirm.py:20`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M206 - VRVP POC/VAH/VAL (24h deterministic)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- VRVP POC/VAH/VAL (24h deterministic) exists to enforce this contract: Deterministic VRVP (POC/VAH/VAL) with bounded box shift and reject-if-still-outside logic.

`Current Implementation`
- Implemented behavior today: Deterministic VRVP (POC/VAH/VAL) with bounded box shift and reject-if-still-outside logic.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:3630`; `freqtrade/user_data/strategies/GridBrainV1.py:6517`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:22`

`Canonical Codes`
- EVENT_VRVP_POC_SHIFT (registry), BLOCK_BOX_VP_POC_MISPLACED

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`EVENT_VRVP_POC_SHIFT (registry), BLOCK_BOX_VP_POC_MISPLACED`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:22`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M207 - POC Acceptance Gate (cross before first START)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- POC Acceptance Gate (cross before first START) exists to enforce this contract: POC cross acceptance gate is persisted per pair and enforced before START.

`Current Implementation`
- Implemented behavior today: POC cross acceptance gate is persisted per pair and enforced before START.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:1357`; `freqtrade/user_data/strategies/GridBrainV1.py:7125`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:45`

`Canonical Codes`
- BLOCK_NO_POC_ACCEPTANCE

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_NO_POC_ACCEPTANCE`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:45`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M208 - Generic Straddle Veto Framework (shared utility)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Generic Straddle Veto Framework (shared utility) exists to enforce this contract: Shared straddle-veto helpers evaluate breakout/OB/FVG/session/VWAP-level conflicts against box.

`Current Implementation`
- Implemented behavior today: Shared straddle-veto helpers evaluate breakout/OB/FVG/session/VWAP-level conflicts against box.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:1256`; `freqtrade/user_data/strategies/GridBrainV1.py:1309`; `freqtrade/user_data/strategies/GridBrainV1.py:7188`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:33`

`Canonical Codes`
- BLOCK_BOX_STRADDLE_*

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_BOX_STRADDLE_*`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:33`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M209 - Log-Space Quartiles + 1.386 Extensions
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Log-Space Quartiles + 1.386 Extensions exists to enforce this contract: Box quartiles and 1.386 extensions are computed in log-space (with linear fallback).

`Current Implementation`
- Implemented behavior today: Box quartiles and 1.386 extensions are computed in log-space (with linear fallback).
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:3201`; `freqtrade/user_data/strategies/GridBrainV1.py:6787`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:320`

`Canonical Codes`
- EVENT_EXT_1386_* (registry)

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`EVENT_EXT_1386_* (registry)`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:320`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M210 - Overlap Pruning of Mitigated Boxes (≥60%)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Overlap Pruning of Mitigated Boxes (≥60%) exists to enforce this contract: Historical overlap pruning prevents repeated mitigated boxes.

`Current Implementation`
- Implemented behavior today: Historical overlap pruning prevents repeated mitigated boxes.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:3395`; `freqtrade/user_data/strategies/GridBrainV1.py:6514`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:476`

`Canonical Codes`
- BLOCK_BOX_OVERLAP_HIGH

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_BOX_OVERLAP_HIGH`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:476`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M211 - Box-vs-Bands / Envelope Overlap Checks
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Box-vs-Bands / Envelope Overlap Checks exists to enforce this contract: Box-vs-band overlap and envelope ratio checks are enforced with conditional overrides.

`Current Implementation`
- Implemented behavior today: Box-vs-band overlap and envelope ratio checks are enforced with conditional overrides.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:6710`; `freqtrade/user_data/strategies/GridBrainV1.py:6728`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:305`

`Canonical Codes`
- BLOCK_BOX_CHANNEL_OVERLAP_LOW, BLOCK_BOX_ENVELOPE_RATIO_HIGH

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_BOX_CHANNEL_OVERLAP_LOW, BLOCK_BOX_ENVELOPE_RATIO_HIGH`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:305`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M212 - Fallback POC Estimator (when VRVP unavailable)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Fallback POC Estimator (when VRVP unavailable) exists to enforce this contract: Fallback POC estimator (volume-weighted typical price with median fallback) activates when VRVP unavailable.

`Current Implementation`
- Implemented behavior today: Fallback POC estimator (volume-weighted typical price with median fallback) activates when VRVP unavailable.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:1381`; `freqtrade/user_data/strategies/GridBrainV1.py:6525`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:393`

`Canonical Codes`
- WARN_VRVP_UNAVAILABLE_FALLBACK_POC

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`WARN_VRVP_UNAVAILABLE_FALLBACK_POC`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:393`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M213 - Midline Bias Fallback (POC-neutral fallback)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Midline Bias Fallback (POC-neutral fallback) exists to enforce this contract: POC-neutral midline-bias fallback selects safe anchors (channel/basis/donchian/vwap) and optional TP candidate.

`Current Implementation`
- Implemented behavior today: POC-neutral midline-bias fallback selects safe anchors (channel/basis/donchian/vwap) and optional TP candidate.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:3257`; `freqtrade/user_data/strategies/GridBrainV1.py:7237`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:333`

`Canonical Codes`
- INFO_TARGET_SOURCE_SELECTED

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`INFO_TARGET_SOURCE_SELECTED`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:333`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M203 - Channel-Width Veto (BB/ATR/SMA/HL selectable)
`Status`: PARTIAL
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Channel-Width Veto (BB/ATR/SMA/HL selectable) exists to enforce this contract: Channel-width integrity checks exist (band overlap/envelope ratio) but selectable BB/ATR/SMA/HL modes are not implemented.

`Current Implementation`
- Implemented behavior today: Channel-width integrity checks exist (band overlap/envelope ratio) but selectable BB/ATR/SMA/HL modes are not implemented.
- Coverage note: Add selectable channel-width backends (BB/ATR/SMA/HL) and mode-level tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:6707`; `freqtrade/user_data/strategies/GridBrainV1.py:6728`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:305`

`Canonical Codes`
- BLOCK_BOX_CHANNEL_OVERLAP_LOW, BLOCK_BOX_ENVELOPE_RATIO_HIGH

`Implementation Playbook`
1. Implement missing scope first: Add selectable channel-width backends (BB/ATR/SMA/HL) and mode-level tests.
2. Add/adjust runtime logic in `freqtrade/user_data/strategies/GridBrainV1.py` and dependent modules listed in evidence anchors.
3. Emit/align canonical codes (`BLOCK_BOX_CHANNEL_OVERLAP_LOW, BLOCK_BOX_ENVELOPE_RATIO_HIGH`) so behavior is externally observable.
4. Add deterministic tests for missing paths and extend suites at: `freqtrade/user_data/tests/test_phase3_validation.py:305`
5. Promote PARTIAL to DONE only when both behavior and tests are complete.

`Gap / Action`
- Add selectable channel-width backends (BB/ATR/SMA/HL) and mode-level tests.

### Phase D — Grid / Entry / Exit
- Phase counts: DONE=5 | PARTIAL=0 | NOT_IMPLEMENTED=2

#### M301 - Cost-Aware Step Sizing
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Cost-Aware Step Sizing exists to enforce this contract: Cost-aware sizing uses chosen floor (static/empirical) and blocks under-floor step plans.

`Current Implementation`
- Implemented behavior today: Cost-aware sizing uses chosen floor (static/empirical) and blocks under-floor step plans.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:4881`; `freqtrade/user_data/strategies/GridBrainV1.py:6819`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:542`

`Canonical Codes`
- BLOCK_STEP_BELOW_COST, BLOCK_STEP_BELOW_EMPIRICAL_COST

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_STEP_BELOW_COST, BLOCK_STEP_BELOW_EMPIRICAL_COST`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:542`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M302 - N Levels Selection (bounded)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- N Levels Selection (bounded) exists to enforce this contract: N-level selection is bounded and volatility-adapter-aware with deterministic fallback.

`Current Implementation`
- Implemented behavior today: N-level selection is bounded and volatility-adapter-aware with deterministic fallback.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:5067`; `freqtrade/user_data/strategies/GridBrainV1.py:5098`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:542`

`Canonical Codes`
- BLOCK_N_LEVELS_INVALID (registry)

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_N_LEVELS_INVALID (registry)`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:542`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M303 - START Entry Filter Aggregator
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- START Entry Filter Aggregator exists to enforce this contract: START filter aggregator composes all gate checks, stability checks, and structured blocker reasons.

`Current Implementation`
- Implemented behavior today: START filter aggregator composes all gate checks, stability checks, and structured blocker reasons.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:7798`; `freqtrade/user_data/strategies/GridBrainV1.py:8013`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:942`

`Canonical Codes`
- BLOCK_START_*

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_START_*`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:942`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M304 - Deterministic TP/SL Selection (nearest conservative wins)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Deterministic TP/SL Selection (nearest conservative wins) exists to enforce this contract: TP/SL are selected deterministically (nearest conservative TP; SL guarded against LVN/FVG unsafe zones).

`Current Implementation`
- Implemented behavior today: TP/SL are selected deterministically (nearest conservative TP; SL guarded against LVN/FVG unsafe zones).
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:5158`; `freqtrade/user_data/strategies/GridBrainV1.py:5175`; `freqtrade/user_data/strategies/GridBrainV1.py:7284`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:659`; `freqtrade/user_data/tests/test_phase3_validation.py:675`

`Canonical Codes`
- INFO_TARGET_SOURCE_SELECTED, INFO_SL_SOURCE_SELECTED

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`INFO_TARGET_SOURCE_SELECTED, INFO_SL_SOURCE_SELECTED`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:659`; `freqtrade/user_data/tests/test_phase3_validation.py:675`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M305 - Fill Detection / Rung Cross Engine (`Touch` / `Reverse`)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Fill Detection / Rung Cross Engine (`Touch` / `Reverse`) exists to enforce this contract: Fill semantics and rung-cross behavior (`Touch`/`Reverse`) are implemented in simulator and executor with dedupe guards.

`Current Implementation`
- Implemented behavior today: Fill semantics and rung-cross behavior (`Touch`/`Reverse`) are implemented in simulator and executor with dedupe guards.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:8517`; `freqtrade/user_data/scripts/grid_simulator_v1.py:288`; `freqtrade/user_data/scripts/grid_executor_v1.py:2144`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:690`; `freqtrade/user_data/tests/test_phase3_validation.py:703`

`Canonical Codes`
- EXEC_FILL_DUPLICATE_GUARD_HIT

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`EXEC_FILL_DUPLICATE_GUARD_HIT`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:690`; `freqtrade/user_data/tests/test_phase3_validation.py:703`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M306 - Directional skip-one rule (simulator-inspired)
`Status`: NOT_IMPLEMENTED
`Source`: NEW_PLAN
`Coverage`: old=N | new=Y | code=N

`Purpose`
- Directional skip-one rule (simulator-inspired) exists to enforce this contract: Directional skip-one rule is not present in current simulator/executor logic.

`Current Implementation`
- Implemented behavior today: Directional skip-one rule is not present in current simulator/executor logic.
- Coverage note: Implement simulator/executor directional skip-one rung rule and parity tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/scripts/grid_simulator_v1.py:1229`
- Tests: None listed.

`Canonical Codes`
- None explicitly mapped in current card.

`Implementation Playbook`
1. Define an explicit contract (inputs, outputs, config keys, canonical codes) before coding.
2. Implement primary behavior in `freqtrade/user_data/scripts/grid_simulator_v1.py` (or the owning module from evidence anchors).
3. Integrate with strategy -> executor/simulator flow so behavior affects runtime decisions.
4. Wire canonical codes (`none` where applicable) and update decision/event logs.
5. Create dedicated tests plus regression coverage. Target gap: Implement simulator/executor directional skip-one rung rule and parity tests.

`Gap / Action`
- Implement simulator/executor directional skip-one rung rule and parity tests.

#### M307 - Next-rung ghost lines (UI only)
`Status`: NOT_IMPLEMENTED
`Source`: NEW_PLAN
`Coverage`: old=N | new=Y | code=N

`Purpose`
- Next-rung ghost lines (UI only) exists to enforce this contract: Ghost next-rung UI-only layer is not implemented in this repo.

`Current Implementation`
- Implemented behavior today: Ghost next-rung UI-only layer is not implemented in this repo.
- Coverage note: Implement optional ghost-line artifact/output contract for UI consumers.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:1546`
- Tests: None listed.

`Canonical Codes`
- None explicitly mapped in current card.

`Implementation Playbook`
1. Define an explicit contract (inputs, outputs, config keys, canonical codes) before coding.
2. Implement primary behavior in `freqtrade/user_data/strategies/GridBrainV1.py` (or the owning module from evidence anchors).
3. Integrate with strategy -> executor/simulator flow so behavior affects runtime decisions.
4. Wire canonical codes (`none` where applicable) and update decision/event logs.
5. Create dedicated tests plus regression coverage. Target gap: Implement optional ghost-line artifact/output contract for UI consumers.

`Gap / Action`
- Implement optional ghost-line artifact/output contract for UI consumers.

### Phase E — STOP / Protections / Eventing
- Phase counts: DONE=4 | PARTIAL=2 | NOT_IMPLEMENTED=0

#### M401 - STOP Trigger Framework
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- STOP Trigger Framework exists to enforce this contract: Comprehensive STOP framework combines breakout/fast-move/shift/structure/protection triggers.

`Current Implementation`
- Implemented behavior today: Comprehensive STOP framework combines breakout/fast-move/shift/structure/protection triggers.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:7565`; `freqtrade/user_data/strategies/GridBrainV1.py:7694`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:944`

`Canonical Codes`
- STOP_*, BLOCK_*

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`STOP_*, BLOCK_*`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:944`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M403 - Cooldown + Min Runtime + Anti-Flap
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Cooldown + Min Runtime + Anti-Flap exists to enforce this contract: Cooldown and min-runtime anti-flap logic are enforced with runtime state persistence.

`Current Implementation`
- Implemented behavior today: Cooldown and min-runtime anti-flap logic are enforced with runtime state persistence.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:7910`; `freqtrade/user_data/strategies/GridBrainV1.py:7971`
- Tests: `freqtrade/user_data/tests/test_partial_module_completion.py:18`

`Canonical Codes`
- BLOCK_COOLDOWN_ACTIVE, BLOCK_MIN_RUNTIME_NOT_MET (registry)

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_COOLDOWN_ACTIVE, BLOCK_MIN_RUNTIME_NOT_MET (registry)`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_partial_module_completion.py:18`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M404 - Protections Layer (cooldown + drawdown guard + future protections)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Protections Layer (cooldown + drawdown guard + future protections) exists to enforce this contract: Protections layer includes drawdown guard and max-stops-window blocker.

`Current Implementation`
- Implemented behavior today: Protections layer includes drawdown guard and max-stops-window blocker.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:5838`; `freqtrade/user_data/strategies/GridBrainV1.py:5869`
- Tests: `freqtrade/user_data/tests/test_partial_module_completion.py:18`

`Canonical Codes`
- STOP_DRAWDOWN_GUARD, BLOCK_MAX_STOPS_WINDOW

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`STOP_DRAWDOWN_GUARD, BLOCK_MAX_STOPS_WINDOW`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_partial_module_completion.py:18`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M405 - Confirm-Entry / Confirm-Exit Hooks (spread/depth/jump)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Confirm-Entry / Confirm-Exit Hooks (spread/depth/jump) exists to enforce this contract: Executor confirm-entry/confirm-exit hooks validate spread/depth/jump metrics before execution.

`Current Implementation`
- Implemented behavior today: Executor confirm-entry/confirm-exit hooks validate spread/depth/jump metrics before execution.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/scripts/grid_executor_v1.py:1213`; `freqtrade/user_data/scripts/grid_executor_v1.py:2477`; `freqtrade/user_data/scripts/grid_executor_v1.py:2490`
- Tests: `freqtrade/user_data/tests/test_executor_hardening.py:153`; `freqtrade/user_data/tests/test_executor_hardening.py:176`

`Canonical Codes`
- EXEC_CONFIRM_*

`Implementation Playbook`
1. Use `freqtrade/user_data/scripts/grid_executor_v1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`EXEC_CONFIRM_*`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_executor_hardening.py:153`; `freqtrade/user_data/tests/test_executor_hardening.py:176`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M402 - Reclaim Timer + REBUILD Discipline (8h baseline)
`Status`: PARTIAL
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Reclaim Timer + REBUILD Discipline (8h baseline) exists to enforce this contract: Reclaim/cooldown discipline exists, but default reclaim baseline is 4h (not the documented 8h baseline).

`Current Implementation`
- Implemented behavior today: Reclaim/cooldown discipline exists, but default reclaim baseline is 4h (not the documented 8h baseline).
- Coverage note: Align reclaim baseline default/documentation (8h vs current 4h) and add explicit acceptance test.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:7927`; `freqtrade/user_data/strategies/GridBrainV1.py:8095`
- Tests: `freqtrade/user_data/tests/test_replay_golden_consistency.py:126`

`Canonical Codes`
- BLOCK_RECLAIM_PENDING

`Implementation Playbook`
1. Implement missing scope first: Align reclaim baseline default/documentation (8h vs current 4h) and add explicit acceptance test.
2. Add/adjust runtime logic in `freqtrade/user_data/strategies/GridBrainV1.py` and dependent modules listed in evidence anchors.
3. Emit/align canonical codes (`BLOCK_RECLAIM_PENDING`) so behavior is externally observable.
4. Add deterministic tests for missing paths and extend suites at: `freqtrade/user_data/tests/test_replay_golden_consistency.py:126`
5. Promote PARTIAL to DONE only when both behavior and tests are complete.

`Gap / Action`
- Align reclaim baseline default/documentation (8h vs current 4h) and add explicit acceptance test.

#### M406 - Structured Event Bus / Taxonomy
`Status`: PARTIAL
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Structured Event Bus / Taxonomy exists to enforce this contract: Structured event bus exists and emits major events, but many canonical event codes remain registry-only.

`Current Implementation`
- Implemented behavior today: Structured event bus exists and emits major events, but many canonical event codes remain registry-only.
- Coverage note: Emit remaining registry event codes or formally deprecate them.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:8190`; `freqtrade/user_data/strategies/GridBrainV1.py:9538`
- Tests: `freqtrade/user_data/tests/test_partial_module_completion.py:204`

`Canonical Codes`
- EVENT_*

`Implementation Playbook`
1. Implement missing scope first: Emit remaining registry event codes or formally deprecate them.
2. Add/adjust runtime logic in `freqtrade/user_data/strategies/GridBrainV1.py` and dependent modules listed in evidence anchors.
3. Emit/align canonical codes (`EVENT_*`) so behavior is externally observable.
4. Add deterministic tests for missing paths and extend suites at: `freqtrade/user_data/tests/test_partial_module_completion.py:204`
5. Promote PARTIAL to DONE only when both behavior and tests are complete.

`Gap / Action`
- Emit remaining registry event codes or formally deprecate them.

### Phase F — Microstructure Modules
- Phase counts: DONE=32 | PARTIAL=4 | NOT_IMPLEMENTED=4

#### M501 - Micro-VAP inside active box
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Micro-VAP inside active box exists to enforce this contract: Micro-VAP inside active box computes micro POC/HVN/LVN/void metrics.

`Current Implementation`
- Implemented behavior today: Micro-VAP inside active box computes micro POC/HVN/LVN/void metrics.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:4219`; `freqtrade/user_data/strategies/GridBrainV1.py:7088`
- Tests: `freqtrade/user_data/tests/test_partial_module_completion.py:46`

`Canonical Codes`
- EVENT_MICRO_POC_SHIFT (registry)

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`EVENT_MICRO_POC_SHIFT (registry)`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_partial_module_completion.py:46`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M502 - POC Alignment Check (micro_POC vs VRVP_POC)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- POC Alignment Check (micro_POC vs VRVP_POC) exists to enforce this contract: Strict micro-POC vs VRVP-POC alignment gate with cross requirement is wired.

`Current Implementation`
- Implemented behavior today: Strict micro-POC vs VRVP-POC alignment gate with cross requirement is wired.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:1451`; `freqtrade/user_data/strategies/GridBrainV1.py:7126`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:424`

`Canonical Codes`
- BLOCK_POC_ALIGNMENT_FAIL

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_POC_ALIGNMENT_FAIL`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:424`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M504 - LVN-void STOP Accelerator
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- LVN-void STOP Accelerator exists to enforce this contract: LVN-void corridor conditions accelerate STOP and emit LVN-void event.

`Current Implementation`
- Implemented behavior today: LVN-void corridor conditions accelerate STOP and emit LVN-void event.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:7616`; `freqtrade/user_data/strategies/GridBrainV1.py:8241`
- Tests: `freqtrade/user_data/tests/test_partial_module_completion.py:125`

`Canonical Codes`
- STOP_LVN_VOID_EXIT_ACCEL, EVENT_LVN_VOID_EXIT

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`STOP_LVN_VOID_EXIT_ACCEL, EVENT_LVN_VOID_EXIT`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_partial_module_completion.py:125`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M505 - Micro-VAP bias / TP-SL nudges / re-entry discipline
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Micro-VAP bias / TP-SL nudges / re-entry discipline exists to enforce this contract: Micro buy-ratio bias, TP nudges, rung weighting, and micro re-entry cooldown/reclaim controls are wired.

`Current Implementation`
- Implemented behavior today: Micro buy-ratio bias, TP nudges, rung weighting, and micro re-entry cooldown/reclaim controls are wired.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:5221`; `freqtrade/user_data/strategies/GridBrainV1.py:5900`; `freqtrade/user_data/strategies/GridBrainV1.py:7426`
- Tests: `freqtrade/user_data/tests/test_partial_module_completion.py:46`

`Canonical Codes`
- BLOCK_RECLAIM_NOT_CONFIRMED

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_RECLAIM_NOT_CONFIRMED`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_partial_module_completion.py:46`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M601 - Lightweight OB Module
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Lightweight OB Module exists to enforce this contract: Lightweight order-block module (freshness, mitigation, straddle veto, TP nudges, events) is implemented.

`Current Implementation`
- Implemented behavior today: Lightweight order-block module (freshness, mitigation, straddle veto, TP nudges, events) is implemented.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `planner/structure/order_blocks.py:212`; `freqtrade/user_data/strategies/GridBrainV1.py:5526`
- Tests: `freqtrade/user_data/tests/test_order_blocks.py:89`

`Canonical Codes`
- EVENT_OB_*

`Implementation Playbook`
1. Use `planner/structure/order_blocks.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`EVENT_OB_*`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_order_blocks.py:89`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M602 - Basic FVG Detection + Straddle Veto
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Basic FVG Detection + Straddle Veto exists to enforce this contract: Baseline FVG detection with opposite-side straddle veto is implemented.

`Current Implementation`
- Implemented behavior today: Baseline FVG detection with opposite-side straddle veto is implemented.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:4358`
- Tests: `freqtrade/user_data/tests/test_partial_module_completion.py:125`

`Canonical Codes`
- BLOCK_BOX_STRADDLE_FVG_EDGE

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_BOX_STRADDLE_FVG_EDGE`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_partial_module_completion.py:125`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M603 - IMFVG Average as TP Candidate + Mitigation Relax
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- IMFVG Average as TP Candidate + Mitigation Relax exists to enforce this contract: IMFVG mitigated-relax logic and IMFVG average TP candidates are implemented.

`Current Implementation`
- Implemented behavior today: IMFVG mitigated-relax logic and IMFVG average TP candidates are implemented.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:4383`; `freqtrade/user_data/strategies/GridBrainV1.py:4658`
- Tests: `freqtrade/user_data/tests/test_partial_module_completion.py:125`

`Canonical Codes`
- EVENT_IMFVG_AVG_TAG_* (registry)

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`EVENT_IMFVG_AVG_TAG_* (registry)`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_partial_module_completion.py:125`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M604 - Session FVG Module (daily)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Session FVG Module (daily) exists to enforce this contract: Session FVG detection/pause/inside-gate state is implemented.

`Current Implementation`
- Implemented behavior today: Session FVG detection/pause/inside-gate state is implemented.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:4396`; `freqtrade/user_data/strategies/GridBrainV1.py:4647`
- Tests: `freqtrade/user_data/tests/test_partial_module_completion.py:125`

`Canonical Codes`
- EVENT_SESSION_FVG_*

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`EVENT_SESSION_FVG_*`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_partial_module_completion.py:125`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M605 - FVG Positioning Averages (`up_avg`, `down_avg`)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- FVG Positioning Averages (`up_avg`, `down_avg`) exists to enforce this contract: FVG positioning averages (`up_avg`/`down_avg`) are produced and consumed in target logic.

`Current Implementation`
- Implemented behavior today: FVG positioning averages (`up_avg`/`down_avg`) are produced and consumed in target logic.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:4397`; `freqtrade/user_data/strategies/GridBrainV1.py:4666`
- Tests: `freqtrade/user_data/tests/test_partial_module_completion.py:125`

`Canonical Codes`
- INFO_TARGET_SOURCE_SELECTED

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`INFO_TARGET_SOURCE_SELECTED`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_partial_module_completion.py:125`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M606 - FVG-VP (Volume Profile inside FVG) Module
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- FVG-VP (Volume Profile inside FVG) Module exists to enforce this contract: FVG-VP module computes zone-internal POC tags and optional STOP/TP refinements.

`Current Implementation`
- Implemented behavior today: FVG-VP module computes zone-internal POC tags and optional STOP/TP refinements.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:5311`; `freqtrade/user_data/strategies/GridBrainV1.py:7156`
- Tests: `freqtrade/user_data/tests/test_partial_module_completion.py:125`

`Canonical Codes`
- EVENT_FVG_POC_TAG

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`EVENT_FVG_POC_TAG`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_partial_module_completion.py:125`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M607 - Defensive FVG Quality Filter (TradingFinder-style)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Defensive FVG Quality Filter (TradingFinder-style) exists to enforce this contract: Defensive FVG quality filter (gap/body/freshness/impulse constraints) is integrated.

`Current Implementation`
- Implemented behavior today: Defensive FVG quality filter (gap/body/freshness/impulse constraints) is integrated.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:4482`; `freqtrade/user_data/strategies/GridBrainV1.py:4622`
- Tests: `freqtrade/user_data/tests/test_partial_module_completion.py:125`

`Canonical Codes`
- BLOCK_FRESH_FVG_COOLOFF (registry)

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_FRESH_FVG_COOLOFF (registry)`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_partial_module_completion.py:125`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M701 - Donchian Channel Module
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Donchian Channel Module exists to enforce this contract: Donchian high/low/mid context is computed and consumed in TP/stop logic.

`Current Implementation`
- Implemented behavior today: Donchian high/low/mid context is computed and consumed in TP/stop logic.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:5957`; `freqtrade/user_data/strategies/GridBrainV1.py:7212`
- Tests: `freqtrade/user_data/tests/test_partial_module_completion.py:125`

`Canonical Codes`
- EVENT_DONCHIAN_STRONG_BREAK_*

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`EVENT_DONCHIAN_STRONG_BREAK_*`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_partial_module_completion.py:125`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M702 - Smart Breakout Channels (AlgoAlpha-style)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Smart Breakout Channels (AlgoAlpha-style) exists to enforce this contract: Smart breakout channel module detects strong breaks and midline interactions with volume confirmation.

`Current Implementation`
- Implemented behavior today: Smart breakout channel module detects strong breaks and midline interactions with volume confirmation.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:5394`; `freqtrade/user_data/strategies/GridBrainV1.py:7214`
- Tests: `freqtrade/user_data/tests/test_partial_module_completion.py:125`

`Canonical Codes`
- EVENT_CHANNEL_STRONG_BREAK_*, EVENT_CHANNEL_MIDLINE_TOUCH

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`EVENT_CHANNEL_STRONG_BREAK_*, EVENT_CHANNEL_MIDLINE_TOUCH`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_partial_module_completion.py:125`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M704 - Liquidity Sweeps (LuxAlgo-style)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Liquidity Sweeps (LuxAlgo-style) exists to enforce this contract: Liquidity sweep engine (wick and break-retest) is integrated with stop/start decisions.

`Current Implementation`
- Implemented behavior today: Liquidity sweep engine (wick and break-retest) is integrated with stop/start decisions.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `planner/structure/liquidity_sweeps.py:74`; `freqtrade/user_data/strategies/GridBrainV1.py:5704`
- Tests: `freqtrade/user_data/tests/test_liquidity_sweeps.py:59`

`Canonical Codes`
- EVENT_SWEEP_*

`Implementation Playbook`
1. Use `planner/structure/liquidity_sweeps.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`EVENT_SWEEP_*`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_liquidity_sweeps.py:59`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M705 - Sweep mode toggle (Wick/Open) for retest validation
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Sweep mode toggle (Wick/Open) for retest validation exists to enforce this contract: Sweep retest validation mode toggle (`Wick`/`Open`) is wired through sweep config and tests.

`Current Implementation`
- Implemented behavior today: Sweep retest validation mode toggle (`Wick`/`Open`) is wired through sweep config and tests.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `planner/structure/liquidity_sweeps.py:48`; `freqtrade/user_data/strategies/GridBrainV1.py:5741`
- Tests: `freqtrade/user_data/tests/test_liquidity_sweeps.py:76`

`Canonical Codes`
- EVENT_SWEEP_BREAK_RETEST_*

`Implementation Playbook`
1. Use `planner/structure/liquidity_sweeps.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`EVENT_SWEEP_BREAK_RETEST_*`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_liquidity_sweeps.py:76`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M802 - MRVD Module (D/W/M distribution + buy/sell split)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- MRVD Module (D/W/M distribution + buy/sell split) exists to enforce this contract: MRVD day/week/month profiles with buy/sell split and drift guard are implemented.

`Current Implementation`
- Implemented behavior today: MRVD day/week/month profiles with buy/sell split and drift guard are implemented.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:3702`; `freqtrade/user_data/strategies/GridBrainV1.py:6906`
- Tests: `freqtrade/user_data/tests/test_partial_module_completion.py:125`

`Canonical Codes`
- BLOCK_MRVD_*

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_MRVD_*`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_partial_module_completion.py:125`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M803 - Multi-Range Basis / Pivots Module (VWAP default)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Multi-Range Basis / Pivots Module (VWAP default) exists to enforce this contract: Basis/pivot module (VWAP basis + bands + cross confirm) is implemented.

`Current Implementation`
- Implemented behavior today: Basis/pivot module (VWAP basis + bands + cross confirm) is implemented.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:5968`; `freqtrade/user_data/strategies/GridBrainV1.py:7200`
- Tests: `freqtrade/user_data/tests/test_partial_module_completion.py:125`

`Canonical Codes`
- BLOCK_BASIS_CROSS_PENDING

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_BASIS_CROSS_PENDING`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_partial_module_completion.py:125`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M804 - Session VWAP / Daily VWAP TP Candidates
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Session VWAP / Daily VWAP TP Candidates exists to enforce this contract: Session VWAP and daily VWAP are included as TP candidates.

`Current Implementation`
- Implemented behavior today: Session VWAP and daily VWAP are included as TP candidates.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:3153`; `freqtrade/user_data/strategies/GridBrainV1.py:7149`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:484`

`Canonical Codes`
- INFO_TARGET_SOURCE_SELECTED

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`INFO_TARGET_SOURCE_SELECTED`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_phase3_validation.py:484`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M805 - Session High/Low Sweep and Break-Retest Events
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Session High/Low Sweep and Break-Retest Events exists to enforce this contract: Session H/L sweep and break-retest events are implemented and emitted.

`Current Implementation`
- Implemented behavior today: Session H/L sweep and break-retest events are implemented and emitted.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:5704`; `freqtrade/user_data/strategies/GridBrainV1.py:8217`
- Tests: `freqtrade/user_data/tests/test_partial_module_completion.py:125`

`Canonical Codes`
- EVENT_SESSION_*_SWEEP

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`EVENT_SESSION_*_SWEEP`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_partial_module_completion.py:125`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M806 - VAH/VAL/POC Zone Proximity START Gate
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- VAH/VAL/POC Zone Proximity START Gate exists to enforce this contract: VAH/VAL/POC proximity START gate is implemented via MRVD proximity checks and block code.

`Current Implementation`
- Implemented behavior today: VAH/VAL/POC proximity START gate is implemented via MRVD proximity checks and block code.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:7718`; `freqtrade/user_data/strategies/GridBrainV1.py:7791`
- Tests: `freqtrade/user_data/tests/test_partial_module_completion.py:125`

`Canonical Codes`
- BLOCK_VAH_VAL_POC_PROXIMITY

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`BLOCK_VAH_VAL_POC_PROXIMITY`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_partial_module_completion.py:125`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M808 - Average-of-basis with session H/L bands (target candidates)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Average-of-basis with session H/L bands (target candidates) exists to enforce this contract: Basis averages with session H/L and related candidates are integrated in TP set.

`Current Implementation`
- Implemented behavior today: Basis averages with session H/L and related candidates are integrated in TP set.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:7261`; `freqtrade/user_data/strategies/GridBrainV1.py:7339`
- Tests: `freqtrade/user_data/tests/test_partial_module_completion.py:125`

`Canonical Codes`
- INFO_TARGET_SOURCE_SELECTED

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`INFO_TARGET_SOURCE_SELECTED`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_partial_module_completion.py:125`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M809 - Buy-ratio Micro-Bias inside box (mid-band)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Buy-ratio Micro-Bias inside box (mid-band) exists to enforce this contract: Buy-ratio micro-bias around box midband is fully integrated into TP and rung bias.

`Current Implementation`
- Implemented behavior today: Buy-ratio micro-bias around box midband is fully integrated into TP and rung bias.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:5221`; `freqtrade/user_data/strategies/GridBrainV1.py:7464`
- Tests: `freqtrade/user_data/tests/test_partial_module_completion.py:46`

`Canonical Codes`
- INFO_TARGET_SOURCE_SELECTED

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`INFO_TARGET_SOURCE_SELECTED`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_partial_module_completion.py:46`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M901 - CVD Divergence near box edges (advisory)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- CVD Divergence near box edges (advisory) exists to enforce this contract: CVD divergence detection near box/value edges is implemented (advisory + nudges).

`Current Implementation`
- Implemented behavior today: CVD divergence detection near box/value edges is implemented (advisory + nudges).
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:3902`; `freqtrade/user_data/strategies/GridBrainV1.py:8697`
- Tests: `freqtrade/user_data/tests/test_partial_module_completion.py:46`

`Canonical Codes`
- EVENT_CVD_BULL_DIV, EVENT_CVD_BEAR_DIV

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`EVENT_CVD_BULL_DIV, EVENT_CVD_BEAR_DIV`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_partial_module_completion.py:46`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M902 - CVD BOS events (ema filtered style)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- CVD BOS events (ema filtered style) exists to enforce this contract: CVD BOS events and freeze windows are implemented.

`Current Implementation`
- Implemented behavior today: CVD BOS events and freeze windows are implemented.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:3938`; `freqtrade/user_data/strategies/GridBrainV1.py:8701`
- Tests: `freqtrade/user_data/tests/test_partial_module_completion.py:46`

`Canonical Codes`
- EVENT_CVD_BOS_UP, EVENT_CVD_BOS_DN

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`EVENT_CVD_BOS_UP, EVENT_CVD_BOS_DN`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_partial_module_completion.py:46`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M1001 - Maker-first post-only discipline + retry/backoff
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Maker-first post-only discipline + retry/backoff exists to enforce this contract: Maker-first post-only execution with retry/backoff and fallback reprice is implemented.

`Current Implementation`
- Implemented behavior today: Maker-first post-only execution with retry/backoff and fallback reprice is implemented.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/scripts/grid_executor_v1.py:1836`; `freqtrade/user_data/scripts/grid_executor_v1.py:1909`; `freqtrade/user_data/scripts/grid_executor_v1.py:1924`
- Tests: `freqtrade/user_data/tests/test_executor_hardening.py:111`

`Canonical Codes`
- EXEC_POST_ONLY_RETRY, EXEC_POST_ONLY_FALLBACK_REPRICE

`Implementation Playbook`
1. Use `freqtrade/user_data/scripts/grid_executor_v1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`EXEC_POST_ONLY_RETRY, EXEC_POST_ONLY_FALLBACK_REPRICE`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_executor_hardening.py:111`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M1002 - Confirm-entry/exit hooks (spread/depth/jump)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Confirm-entry/exit hooks (spread/depth/jump) exists to enforce this contract: Execution confirm hooks are implemented for START/REBUILD/EXIT flows.

`Current Implementation`
- Implemented behavior today: Execution confirm hooks are implemented for START/REBUILD/EXIT flows.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/scripts/grid_executor_v1.py:1213`; `freqtrade/user_data/scripts/grid_executor_v1.py:2477`; `freqtrade/user_data/scripts/grid_executor_v1.py:2480`
- Tests: `freqtrade/user_data/tests/test_executor_hardening.py:153`

`Canonical Codes`
- EXEC_CONFIRM_START_FAILED, EXEC_CONFIRM_REBUILD_FAILED, EXEC_CONFIRM_EXIT_FAILSAFE

`Implementation Playbook`
1. Use `freqtrade/user_data/scripts/grid_executor_v1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`EXEC_CONFIRM_START_FAILED, EXEC_CONFIRM_REBUILD_FAILED, EXEC_CONFIRM_EXIT_FAILSAFE`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_executor_hardening.py:153`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M1003 - Minimal order-flow metrics (soft veto/confidence)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Minimal order-flow metrics (soft veto/confidence) exists to enforce this contract: Minimal order-flow metrics (spread/depth/imbalance/jump) feed soft veto and confidence modifier.

`Current Implementation`
- Implemented behavior today: Minimal order-flow metrics (spread/depth/imbalance/jump) feed soft veto and confidence modifier.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:5779`; `freqtrade/user_data/scripts/grid_executor_v1.py:1196`
- Tests: `freqtrade/user_data/tests/test_partial_module_completion.py:46`

`Canonical Codes`
- EVENT_SPREAD_SPIKE, EVENT_DEPTH_THIN, EVENT_JUMP_DETECTED

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`EVENT_SPREAD_SPIKE, EVENT_DEPTH_THIN, EVENT_JUMP_DETECTED`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_partial_module_completion.py:46`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M1004 - Atomic handoff + idempotency (duplicate-safe)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Atomic handoff + idempotency (duplicate-safe) exists to enforce this contract: Atomic handoff and duplicate-safe plan intake are fully wired (schema/hash/seq/id checks).

`Current Implementation`
- Implemented behavior today: Atomic handoff and duplicate-safe plan intake are fully wired (schema/hash/seq/id checks).
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/scripts/grid_executor_v1.py:814`; `freqtrade/user_data/scripts/grid_executor_v1.py:840`; `freqtrade/user_data/strategies/GridBrainV1.py:9571`
- Tests: `freqtrade/user_data/tests/test_executor_hardening.py:260`

`Canonical Codes`
- EXEC_PLAN_SCHEMA_INVALID, EXEC_PLAN_HASH_MISMATCH, EXEC_PLAN_DUPLICATE_IGNORED

`Implementation Playbook`
1. Use `freqtrade/user_data/scripts/grid_executor_v1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`EXEC_PLAN_SCHEMA_INVALID, EXEC_PLAN_HASH_MISMATCH, EXEC_PLAN_DUPLICATE_IGNORED`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_executor_hardening.py:260`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M1005 - Empirical execution cost feedback loop
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Empirical execution cost feedback loop exists to enforce this contract: Execution-cost feedback loop publishes artifacts and feeds planner empirical cost floor.

`Current Implementation`
- Implemented behavior today: Execution-cost feedback loop publishes artifacts and feeds planner empirical cost floor.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/scripts/grid_executor_v1.py:1579`; `freqtrade/user_data/strategies/GridBrainV1.py:4881`
- Tests: `freqtrade/user_data/tests/test_executor_hardening.py:365`

`Canonical Codes`
- WARN_COST_MODEL_STALE

`Implementation Playbook`
1. Use `freqtrade/user_data/scripts/grid_executor_v1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`WARN_COST_MODEL_STALE`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_executor_hardening.py:365`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M1006 - Stress/chaos replay as standard validation
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Stress/chaos replay as standard validation exists to enforce this contract: Chaos/stress replay is integrated as standard validation path with deterministic-vs-chaos deltas.

`Current Implementation`
- Implemented behavior today: Chaos/stress replay is integrated as standard validation path with deterministic-vs-chaos deltas.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/scripts/grid_simulator_v1.py:1229`; `freqtrade/user_data/scripts/grid_simulator_v1.py:2120`
- Tests: `freqtrade/user_data/tests/test_chaos_replay_harness.py:161`; `freqtrade/user_data/tests/test_stress_replay_standard_validation.py:44`

`Canonical Codes`
- EXEC/STOP robustness under chaos profiles

`Implementation Playbook`
1. Use `freqtrade/user_data/scripts/grid_simulator_v1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`EXEC/STOP robustness under chaos profiles`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_chaos_replay_harness.py:161`; `freqtrade/user_data/tests/test_stress_replay_standard_validation.py:44`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M1007 - Formal tuning workflow + anti-overfit checks
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Formal tuning workflow + anti-overfit checks exists to enforce this contract: Formal tuning workflow is implemented via walk-forward + tuning protocol scripts and gates.

`Current Implementation`
- Implemented behavior today: Formal tuning workflow is implemented via walk-forward + tuning protocol scripts and gates.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/scripts/run-user-walkforward.py:3`; `freqtrade/scripts/run-user-tuning-protocol.py:3`; `freqtrade/scripts/run-user-tuning-protocol.py:460`; `freqtrade/scripts/run-user-tuning-protocol.py:1077`
- Tests: `freqtrade/user_data/tests/test_tuning_protocol.py:164`; `freqtrade/user_data/tests/test_tuning_protocol.py:325`

`Canonical Codes`
- promotion gates + schema checks (protocol layer)

`Implementation Playbook`
1. Use `freqtrade/scripts/run-user-walkforward.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`promotion gates + schema checks (protocol layer)`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_tuning_protocol.py:164`; `freqtrade/user_data/tests/test_tuning_protocol.py:325`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M1008 - FreqAI/ML confidence overlay (not primary)
`Status`: DONE
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- FreqAI/ML confidence overlay (not primary) exists to enforce this contract: FreqAI/ML confidence overlay is implemented as advisory/strict overlay, not primary logic.

`Current Implementation`
- Implemented behavior today: FreqAI/ML confidence overlay is implemented as advisory/strict overlay, not primary logic.
- Coverage note: Implemented and referenced in runtime plan payload/events/tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:4020`; `freqtrade/user_data/strategies/GridBrainV1.py:7025`; `freqtrade/scripts/run-user-ml-walkforward.py:3`; `freqtrade/scripts/run-user-ml-walkforward.py:411`
- Tests: `freqtrade/user_data/tests/test_ml_overlay_step14.py:108`; `freqtrade/user_data/tests/test_ml_overlay_step14.py:332`

`Canonical Codes`
- ml_overlay gates + confidence checks

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`ml_overlay gates + confidence checks`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_ml_overlay_step14.py:108`; `freqtrade/user_data/tests/test_ml_overlay_step14.py:332`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### M503 - HVN/LVN inside box + min spacing
`Status`: PARTIAL
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- HVN/LVN inside box + min spacing exists to enforce this contract: HVN/LVN extraction is implemented; explicit configurable min-spacing enforcement is limited.

`Current Implementation`
- Implemented behavior today: HVN/LVN extraction is implemented; explicit configurable min-spacing enforcement is limited.
- Coverage note: Add explicit HVN/LVN min-spacing rule with deterministic enforcement and tests.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:4278`; `freqtrade/user_data/strategies/GridBrainV1.py:7109`
- Tests: `freqtrade/user_data/tests/test_phase3_validation.py:675`

`Canonical Codes`
- EVENT_HVN_TOUCH / EVENT_LVN_TOUCH (registry)

`Implementation Playbook`
1. Implement missing scope first: Add explicit HVN/LVN min-spacing rule with deterministic enforcement and tests.
2. Add/adjust runtime logic in `freqtrade/user_data/strategies/GridBrainV1.py` and dependent modules listed in evidence anchors.
3. Emit/align canonical codes (`EVENT_HVN_TOUCH / EVENT_LVN_TOUCH (registry)`) so behavior is externally observable.
4. Add deterministic tests for missing paths and extend suites at: `freqtrade/user_data/tests/test_phase3_validation.py:675`
5. Promote PARTIAL to DONE only when both behavior and tests are complete.

`Gap / Action`
- Add explicit HVN/LVN min-spacing rule with deterministic enforcement and tests.

#### M703 - Zig-Zag Envelope / Channel Enhancements
`Status`: PARTIAL
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- Zig-Zag Envelope / Channel Enhancements exists to enforce this contract: Zig-zag/envelope enhancement is partially represented by contraction gating, not full envelope suite.

`Current Implementation`
- Implemented behavior today: Zig-zag/envelope enhancement is partially represented by contraction gating, not full envelope suite.
- Coverage note: Implement full zig-zag/envelope enhancement set beyond contraction gate.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:5458`; `freqtrade/user_data/strategies/GridBrainV1.py:6603`
- Tests: `freqtrade/user_data/tests/test_partial_module_completion.py:125`

`Canonical Codes`
- EVENT_DRIFT_RETEST_* (registry)

`Implementation Playbook`
1. Implement missing scope first: Implement full zig-zag/envelope enhancement set beyond contraction gate.
2. Add/adjust runtime logic in `freqtrade/user_data/strategies/GridBrainV1.py` and dependent modules listed in evidence anchors.
3. Emit/align canonical codes (`EVENT_DRIFT_RETEST_* (registry)`) so behavior is externally observable.
4. Add deterministic tests for missing paths and extend suites at: `freqtrade/user_data/tests/test_partial_module_completion.py:125`
5. Promote PARTIAL to DONE only when both behavior and tests are complete.

`Gap / Action`
- Implement full zig-zag/envelope enhancement set beyond contraction gate.

#### M801 - MTF POC Confluence (D/W, M advisory) + POC-cross before START
`Status`: PARTIAL
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=Y

`Purpose`
- MTF POC Confluence (D/W, M advisory) + POC-cross before START exists to enforce this contract: MTF POC confluence is partially covered through MRVD D/W/M proximity; explicit dedicated POC-cross gating by TF is incomplete.

`Current Implementation`
- Implemented behavior today: MTF POC confluence is partially covered through MRVD D/W/M proximity; explicit dedicated POC-cross gating by TF is incomplete.
- Coverage note: Add explicit multi-timeframe POC-cross-before-START gate contract (D/W/M).

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:6960`; `freqtrade/user_data/strategies/GridBrainV1.py:7791`
- Tests: `freqtrade/user_data/tests/test_partial_module_completion.py:125`

`Canonical Codes`
- BLOCK_VAH_VAL_POC_PROXIMITY

`Implementation Playbook`
1. Implement missing scope first: Add explicit multi-timeframe POC-cross-before-START gate contract (D/W/M).
2. Add/adjust runtime logic in `freqtrade/user_data/strategies/GridBrainV1.py` and dependent modules listed in evidence anchors.
3. Emit/align canonical codes (`BLOCK_VAH_VAL_POC_PROXIMITY`) so behavior is externally observable.
4. Add deterministic tests for missing paths and extend suites at: `freqtrade/user_data/tests/test_partial_module_completion.py:125`
5. Promote PARTIAL to DONE only when both behavior and tests are complete.

`Gap / Action`
- Add explicit multi-timeframe POC-cross-before-START gate contract (D/W/M).

#### M807 - VAH/VAL Approximation via Quantiles (fallback/optional)
`Status`: PARTIAL
`Source`: BOTH
`Coverage`: old=N | new=Y | code=Y

`Purpose`
- VAH/VAL Approximation via Quantiles (fallback/optional) exists to enforce this contract: Quantile fallback approximation for VAH/VAL is only partially represented (quantiles are used for micro profile, not full VA fallback path).

`Current Implementation`
- Implemented behavior today: Quantile fallback approximation for VAH/VAL is only partially represented (quantiles are used for micro profile, not full VA fallback path).
- Coverage note: Implement VAH/VAL quantile fallback as dedicated module contract, not only micro profile quantiles.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:4273`; `freqtrade/user_data/strategies/GridBrainV1.py:9050`
- Tests: None listed.

`Canonical Codes`
- None explicitly mapped in current card.

`Implementation Playbook`
1. Implement missing scope first: Implement VAH/VAL quantile fallback as dedicated module contract, not only micro profile quantiles.
2. Add/adjust runtime logic in `freqtrade/user_data/strategies/GridBrainV1.py` and dependent modules listed in evidence anchors.
3. Emit/align canonical codes (`none`) so behavior is externally observable.
4. Add deterministic tests for missing paths and extend suites at: None listed.
5. Promote PARTIAL to DONE only when both behavior and tests are complete.

`Gap / Action`
- Implement VAH/VAL quantile fallback as dedicated module contract, not only micro profile quantiles.

#### M903 - CVD Spike + Passive Absorption (Insights style)
`Status`: NOT_IMPLEMENTED
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=N

`Purpose`
- CVD Spike + Passive Absorption (Insights style) exists to enforce this contract: CVD spike + passive absorption module is not implemented as a dedicated signal path.

`Current Implementation`
- Implemented behavior today: CVD spike + passive absorption module is not implemented as a dedicated signal path.
- Coverage note: Implement CVD spike + passive absorption detection path and advisory controls.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:3831`
- Tests: None listed.

`Canonical Codes`
- EVENT_CVD_SPIKE_*, EVENT_PASSIVE_ABSORPTION_* (registry)

`Implementation Playbook`
1. Define an explicit contract (inputs, outputs, config keys, canonical codes) before coding.
2. Implement primary behavior in `freqtrade/user_data/strategies/GridBrainV1.py` (or the owning module from evidence anchors).
3. Integrate with strategy -> executor/simulator flow so behavior affects runtime decisions.
4. Wire canonical codes (`EVENT_CVD_SPIKE_*, EVENT_PASSIVE_ABSORPTION_* (registry)` where applicable) and update decision/event logs.
5. Create dedicated tests plus regression coverage. Target gap: Implement CVD spike + passive absorption detection path and advisory controls.

`Gap / Action`
- Implement CVD spike + passive absorption detection path and advisory controls.

#### M904 - CVD Divergence Oscillator Strong Score (advisory)
`Status`: NOT_IMPLEMENTED
`Source`: BOTH
`Coverage`: old=Y | new=Y | code=N

`Purpose`
- CVD Divergence Oscillator Strong Score (advisory) exists to enforce this contract: CVD divergence oscillator strong-score module is not implemented.

`Current Implementation`
- Implemented behavior today: CVD divergence oscillator strong-score module is not implemented.
- Coverage note: Implement divergence oscillator strong-score computation and TP-priority integration.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:3831`
- Tests: None listed.

`Canonical Codes`
- None explicitly mapped in current card.

`Implementation Playbook`
1. Define an explicit contract (inputs, outputs, config keys, canonical codes) before coding.
2. Implement primary behavior in `freqtrade/user_data/strategies/GridBrainV1.py` (or the owning module from evidence anchors).
3. Integrate with strategy -> executor/simulator flow so behavior affects runtime decisions.
4. Wire canonical codes (`none` where applicable) and update decision/event logs.
5. Create dedicated tests plus regression coverage. Target gap: Implement divergence oscillator strong-score computation and TP-priority integration.

`Gap / Action`
- Implement divergence oscillator strong-score computation and TP-priority integration.

#### M905 - SMA200 / EMA trend filters for directional variants
`Status`: NOT_IMPLEMENTED
`Source`: BOTH
`Coverage`: old=N | new=Y | code=N

`Purpose`
- SMA200 / EMA trend filters for directional variants exists to enforce this contract: Directional SMA200/EMA trend filters are not implemented.

`Current Implementation`
- Implemented behavior today: Directional SMA200/EMA trend filters are not implemented.
- Coverage note: Implement SMA200/EMA trend filters for directional variants with gating toggles.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:730`
- Tests: None listed.

`Canonical Codes`
- None explicitly mapped in current card.

`Implementation Playbook`
1. Define an explicit contract (inputs, outputs, config keys, canonical codes) before coding.
2. Implement primary behavior in `freqtrade/user_data/strategies/GridBrainV1.py` (or the owning module from evidence anchors).
3. Integrate with strategy -> executor/simulator flow so behavior affects runtime decisions.
4. Wire canonical codes (`none` where applicable) and update decision/event logs.
5. Create dedicated tests plus regression coverage. Target gap: Implement SMA200/EMA trend filters for directional variants with gating toggles.

`Gap / Action`
- Implement SMA200/EMA trend filters for directional variants with gating toggles.

#### M906 - CVD extension line touch counter (UI only)
`Status`: NOT_IMPLEMENTED
`Source`: BOTH
`Coverage`: old=N | new=Y | code=N

`Purpose`
- CVD extension line touch counter (UI only) exists to enforce this contract: CVD extension-line touch counter (UI-only) is not implemented.

`Current Implementation`
- Implemented behavior today: CVD extension-line touch counter (UI-only) is not implemented.
- Coverage note: Implement CVD extension-line touch counter (UI/state artifact).

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:1776`
- Tests: None listed.

`Canonical Codes`
- None explicitly mapped in current card.

`Implementation Playbook`
1. Define an explicit contract (inputs, outputs, config keys, canonical codes) before coding.
2. Implement primary behavior in `freqtrade/user_data/strategies/GridBrainV1.py` (or the owning module from evidence anchors).
3. Integrate with strategy -> executor/simulator flow so behavior affects runtime decisions.
4. Wire canonical codes (`none` where applicable) and update decision/event logs.
5. Create dedicated tests plus regression coverage. Target gap: Implement CVD extension-line touch counter (UI/state artifact).

`Gap / Action`
- Implement CVD extension-line touch counter (UI/state artifact).

### Phase G — Ad-hoc Assets To Preserve
- Phase counts: DONE=6 | PARTIAL=0 | NOT_IMPLEMENTED=0

#### AH-001 - Regime Router With Safe Handoffs (intraday/swing/neutral/pause)
`Status`: DONE
`Source`: ADHOC
`Coverage`: old=N | new=N | code=N

`Purpose`
- Regime Router With Safe Handoffs (intraday/swing/neutral/pause) exists to enforce this contract: Score-based router with persistence/cooldown, inventory-aware handoff safety, and mode-specific threshold profiles.

`Current Implementation`
- Implemented behavior today: Score-based router with persistence/cooldown, inventory-aware handoff safety, and mode-specific threshold profiles.
- Coverage note: No matrix row.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:2314`; `freqtrade/user_data/strategies/GridBrainV1.py:2373`; `freqtrade/user_data/strategies/GridBrainV1.py:6304`
- Tests: `freqtrade/user_data/scripts/user_regression_suite.py:603`

`Canonical Codes`
- router_* diagnostics + BLOCK/STOP integration

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`router_* diagnostics + BLOCK/STOP integration`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/scripts/user_regression_suite.py:603`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### AH-002 - Per-Candle Plan History Emit Path For Replay Fidelity
`Status`: DONE
`Source`: ADHOC
`Coverage`: old=N | new=N | code=N

`Purpose`
- Per-Candle Plan History Emit Path For Replay Fidelity exists to enforce this contract: Backtest mode replays full per-candle planning path to preserve exact decision timeline for simulator parity.

`Current Implementation`
- Implemented behavior today: Backtest mode replays full per-candle planning path to preserve exact decision timeline for simulator parity.
- Coverage note: No matrix row.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1.py:938`; `freqtrade/user_data/strategies/GridBrainV1.py:5991`
- Tests: `freqtrade/user_data/tests/test_replay_golden_consistency.py:126`

`Canonical Codes`
- plan_history runtime hints

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`plan_history runtime hints`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_replay_golden_consistency.py:126`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### AH-003 - Strategy Variant Harness For Ablations
`Status`: DONE
`Source`: ADHOC
`Coverage`: old=N | new=N | code=N

`Purpose`
- Strategy Variant Harness For Ablations exists to enforce this contract: Maintains explicit strategy variants (no-neutral/no-fvg/no-pause/router-fast/neutral filters) for controlled ablation experiments.

`Current Implementation`
- Implemented behavior today: Maintains explicit strategy variants (no-neutral/no-fvg/no-pause/router-fast/neutral filters) for controlled ablation experiments.
- Coverage note: No matrix row.

`Evidence Anchors`
- Code: `freqtrade/user_data/strategies/GridBrainV1BaselineNoNeutral.py:4`; `freqtrade/user_data/strategies/GridBrainV1NoFVG.py:4`; `freqtrade/user_data/strategies/GridBrainV1NoPause.py:4`
- Tests: `freqtrade/user_data/tests/test_tuning_protocol.py:164`

`Canonical Codes`
- experiment manifest + tuning gates

`Implementation Playbook`
1. Use `freqtrade/user_data/strategies/GridBrainV1BaselineNoNeutral.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`experiment manifest + tuning gates`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_tuning_protocol.py:164`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### AH-004 - Walkforward Runner + Latest-Ref Publication
`Status`: DONE
`Source`: ADHOC
`Coverage`: old=N | new=N | code=N

`Purpose`
- Walkforward Runner + Latest-Ref Publication exists to enforce this contract: Automates rolling windows, aggregates metrics, writes summary/csv artifacts, and publishes latest refs for downstream tooling.

`Current Implementation`
- Implemented behavior today: Automates rolling windows, aggregates metrics, writes summary/csv artifacts, and publishes latest refs for downstream tooling.
- Runtime hardening added: container-path translation for config/strategy/data paths, warmup-aware backtesting timerange extension (`--backtest-warmup-candles`, auto mode from strategy lookbacks), and explicit diagnostics when plan emission is missing.
- Reliability fix linked to strategy: informative-pair fallback + informative alias normalization to keep feature contract stable during backtesting runtime merges.
- Coverage note: No matrix row.

`Evidence Anchors`
- Code: `freqtrade/scripts/run-user-walkforward.py:159`; `freqtrade/scripts/run-user-walkforward.py:315`; `freqtrade/scripts/run-user-walkforward.py:1162`; `freqtrade/scripts/run-user-walkforward.py:1570`; `freqtrade/scripts/run-user-walkforward.py:1668`; `freqtrade/user_data/strategies/GridBrainV1.py:1106`; `freqtrade/user_data/strategies/GridBrainV1.py:6033`
- Tests: `freqtrade/user_data/tests/test_tuning_protocol.py:164`

`Canonical Codes`
- metrics registry + promotion input

`Implementation Playbook`
1. Use `freqtrade/scripts/run-user-walkforward.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`metrics registry + promotion input`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_tuning_protocol.py:164`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### AH-005 - Formal Tuning Protocol Automation
`Status`: DONE
`Source`: ADHOC
`Coverage`: old=N | new=N | code=N

`Purpose`
- Formal Tuning Protocol Automation exists to enforce this contract: Implements OOS/ablation/chaos/rank/ML gates, champion promotion logic, history registry, and schema validation.

`Current Implementation`
- Implemented behavior today: Implements OOS/ablation/chaos/rank/ML gates, champion promotion logic, history registry, and schema validation.
- Coverage note: No matrix row.

`Evidence Anchors`
- Code: `freqtrade/scripts/run-user-tuning-protocol.py:3`; `freqtrade/scripts/run-user-tuning-protocol.py:460`; `freqtrade/scripts/run-user-tuning-protocol.py:1077`; `freqtrade/scripts/run-user-tuning-protocol.py:1201`
- Tests: `freqtrade/user_data/tests/test_tuning_protocol.py:164`; `freqtrade/user_data/tests/test_tuning_protocol.py:325`

`Canonical Codes`
- promotion gate checks + strict failure contract

`Implementation Playbook`
1. Use `freqtrade/scripts/run-user-tuning-protocol.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`promotion gate checks + strict failure contract`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_tuning_protocol.py:164`; `freqtrade/user_data/tests/test_tuning_protocol.py:325`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

#### AH-006 - ML Overlay Walkforward Evaluator
`Status`: DONE
`Source`: ADHOC
`Coverage`: old=N | new=N | code=N

`Purpose`
- ML Overlay Walkforward Evaluator exists to enforce this contract: Runs leakage-safe ML overlay evaluation with calibration/coverage gates and writes summary artifacts for promotion pipeline.

`Current Implementation`
- Implemented behavior today: Runs leakage-safe ML overlay evaluation with calibration/coverage gates and writes summary artifacts for promotion pipeline.
- Coverage note: No matrix row.

`Evidence Anchors`
- Code: `freqtrade/scripts/run-user-ml-walkforward.py:3`; `freqtrade/scripts/run-user-ml-walkforward.py:318`; `freqtrade/scripts/run-user-ml-walkforward.py:411`
- Tests: `freqtrade/user_data/tests/test_ml_overlay_step14.py:108`; `freqtrade/user_data/tests/test_ml_overlay_step14.py:212`

`Canonical Codes`
- ml_overlay gate metrics

`Implementation Playbook`
1. Use `freqtrade/scripts/run-user-ml-walkforward.py` as the primary edit point for this module's behavior.
2. Keep deterministic behavior unchanged unless the spec is updated in `docs/CONSOLIDATED_MASTER_PLAN.md` in the same change.
3. If logic changes, preserve/adjust canonical codes (`ml_overlay gate metrics`) and keep payload compatibility.
4. Run or extend tests anchored at: `freqtrade/user_data/tests/test_ml_overlay_step14.py:108`; `freqtrade/user_data/tests/test_ml_overlay_step14.py:212`
5. Update this card immediately after code changes so plan and runtime stay synchronized.

`Gap / Action`
- No functional gap is required to keep baseline behavior. Treat this as maintenance + extension guidance.

## 5) Coverage Map (Old Plan vs New Plan vs Code)
- This replaces the dense matrix with status-sorted readable lists. Each feature card above still contains exact old/new/code coverage.

### DONE Modules (75)
- `M001` Parameter Inertia + Epoch Replan Policy | phase=Phase A — Governance / Handoff / Stability | old=N new=Y code=Y
- `M002` Atomic Brain→Executor Handoff + Idempotency Contract | phase=Phase A — Governance / Handoff / Stability | old=Y new=Y code=Y
- `M003` Global Start Stability Score (k-of-n) | phase=Phase A — Governance / Handoff / Stability | old=N new=Y code=Y
- `M004` Data Quality Quarantine State | phase=Phase A — Governance / Handoff / Stability | old=N new=Y code=Y
- `M005` Meta Drift Guard (Page-Hinkley/CUSUM style) | phase=Phase A — Governance / Handoff / Stability | old=N new=Y code=Y
- `M006` Volatility Policy Adapter (deterministic) | phase=Phase A — Governance / Handoff / Stability | old=N new=Y code=Y
- `M007` Empirical Execution Cost Calibration Loop | phase=Phase A — Governance / Handoff / Stability | old=N new=Y code=Y
- `M008` Stress/Chaos Replay Harness | phase=Phase A — Governance / Handoff / Stability | old=N new=Y code=Y
- `M009` Depth-Aware Capacity Cap | phase=Phase A — Governance / Handoff / Stability | old=Y new=Y code=Y
- `M010` Enum Registry + Plan Diff Snapshots | phase=Phase A — Governance / Handoff / Stability | old=N new=Y code=Y
- `M101` ADX Gate (4h) | phase=Phase B — Regime + Build Gates | old=Y new=Y code=Y
- `M102` BBW Quietness Gate (1h) | phase=Phase B — Regime + Build Gates | old=Y new=Y code=Y
- `M103` EMA50/EMA100 Compression Gate (1h) | phase=Phase B — Regime + Build Gates | old=Y new=Y code=Y
- `M104` rVol Calm Gate (1h/15m) | phase=Phase B — Regime + Build Gates | old=Y new=Y code=Y
- `M105` 7d Context / Extremes Sanity | phase=Phase B — Regime + Build Gates | old=Y new=Y code=Y
- `M106` Structural Breakout Fresh-Block + Cached Break Levels | phase=Phase B — Regime + Build Gates | old=Y new=Y code=Y
- `M107` Range DI / Deviation-Pivot `os_dev` (Misu-style) | phase=Phase B — Regime + Build Gates | old=Y new=Y code=Y
- `M108` Band Slope / Drift Slope / Excursion Asymmetry Vetoes | phase=Phase B — Regime + Build Gates | old=Y new=Y code=Y
- `M109` BBWP MTF Gate + Cool-off | phase=Phase B — Regime + Build Gates | old=Y new=Y code=Y
- `M110` Squeeze State Gate (BB inside KC) + release STOP override | phase=Phase B — Regime + Build Gates | old=Y new=Y code=Y
- `M111` Funding Filter (FR 8h est, Binance premium index) | phase=Phase B — Regime + Build Gates | old=Y new=Y code=Y
- `M112` HVP Gate (HVP vs HVPSMA + BBW expansion) | phase=Phase B — Regime + Build Gates | old=Y new=Y code=Y
- `M201` Core 24h ± ATR Box Builder | phase=Phase C — Box Builder + Validation | old=Y new=Y code=Y
- `M202` Box Width Target / Hard-Soft Veto Policy | phase=Phase C — Box Builder + Validation | old=Y new=Y code=Y
- `M204` Percent-of-Average Width Veto | phase=Phase C — Box Builder + Validation | old=Y new=Y code=Y
- `M205` Minimum Range Length + Breakout Confirm Bars | phase=Phase C — Box Builder + Validation | old=Y new=Y code=Y
- `M206` VRVP POC/VAH/VAL (24h deterministic) | phase=Phase C — Box Builder + Validation | old=Y new=Y code=Y
- `M207` POC Acceptance Gate (cross before first START) | phase=Phase C — Box Builder + Validation | old=Y new=Y code=Y
- `M208` Generic Straddle Veto Framework (shared utility) | phase=Phase C — Box Builder + Validation | old=Y new=Y code=Y
- `M209` Log-Space Quartiles + 1.386 Extensions | phase=Phase C — Box Builder + Validation | old=Y new=Y code=Y
- `M210` Overlap Pruning of Mitigated Boxes (≥60%) | phase=Phase C — Box Builder + Validation | old=Y new=Y code=Y
- `M211` Box-vs-Bands / Envelope Overlap Checks | phase=Phase C — Box Builder + Validation | old=Y new=Y code=Y
- `M212` Fallback POC Estimator (when VRVP unavailable) | phase=Phase C — Box Builder + Validation | old=Y new=Y code=Y
- `M213` Midline Bias Fallback (POC-neutral fallback) | phase=Phase C — Box Builder + Validation | old=Y new=Y code=Y
- `M301` Cost-Aware Step Sizing | phase=Phase D — Grid / Entry / Exit | old=Y new=Y code=Y
- `M302` N Levels Selection (bounded) | phase=Phase D — Grid / Entry / Exit | old=Y new=Y code=Y
- `M303` START Entry Filter Aggregator | phase=Phase D — Grid / Entry / Exit | old=Y new=Y code=Y
- `M304` Deterministic TP/SL Selection (nearest conservative wins) | phase=Phase D — Grid / Entry / Exit | old=Y new=Y code=Y
- `M305` Fill Detection / Rung Cross Engine (`Touch` / `Reverse`) | phase=Phase D — Grid / Entry / Exit | old=Y new=Y code=Y
- `M401` STOP Trigger Framework | phase=Phase E — STOP / Protections / Eventing | old=Y new=Y code=Y
- `M403` Cooldown + Min Runtime + Anti-Flap | phase=Phase E — STOP / Protections / Eventing | old=Y new=Y code=Y
- `M404` Protections Layer (cooldown + drawdown guard + future protections) | phase=Phase E — STOP / Protections / Eventing | old=Y new=Y code=Y
- `M405` Confirm-Entry / Confirm-Exit Hooks (spread/depth/jump) | phase=Phase E — STOP / Protections / Eventing | old=Y new=Y code=Y
- `M501` Micro-VAP inside active box | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M502` POC Alignment Check (micro_POC vs VRVP_POC) | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M504` LVN-void STOP Accelerator | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M505` Micro-VAP bias / TP-SL nudges / re-entry discipline | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M601` Lightweight OB Module | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M602` Basic FVG Detection + Straddle Veto | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M603` IMFVG Average as TP Candidate + Mitigation Relax | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M604` Session FVG Module (daily) | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M605` FVG Positioning Averages (`up_avg`, `down_avg`) | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M606` FVG-VP (Volume Profile inside FVG) Module | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M607` Defensive FVG Quality Filter (TradingFinder-style) | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M701` Donchian Channel Module | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M702` Smart Breakout Channels (AlgoAlpha-style) | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M704` Liquidity Sweeps (LuxAlgo-style) | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M705` Sweep mode toggle (Wick/Open) for retest validation | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M802` MRVD Module (D/W/M distribution + buy/sell split) | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M803` Multi-Range Basis / Pivots Module (VWAP default) | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M804` Session VWAP / Daily VWAP TP Candidates | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M805` Session High/Low Sweep and Break-Retest Events | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M806` VAH/VAL/POC Zone Proximity START Gate | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M808` Average-of-basis with session H/L bands (target candidates) | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M809` Buy-ratio Micro-Bias inside box (mid-band) | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M901` CVD Divergence near box edges (advisory) | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M902` CVD BOS events (ema filtered style) | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M1001` Maker-first post-only discipline + retry/backoff | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M1002` Confirm-entry/exit hooks (spread/depth/jump) | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M1003` Minimal order-flow metrics (soft veto/confidence) | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M1004` Atomic handoff + idempotency (duplicate-safe) | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M1005` Empirical execution cost feedback loop | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M1006` Stress/chaos replay as standard validation | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M1007` Formal tuning workflow + anti-overfit checks | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M1008` FreqAI/ML confidence overlay (not primary) | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y

### PARTIAL Modules (8)
- `M113` Boom & Doom Impulse Guard | phase=Phase B — Regime + Build Gates | old=Y new=Y code=Y
- `M203` Channel-Width Veto (BB/ATR/SMA/HL selectable) | phase=Phase C — Box Builder + Validation | old=Y new=Y code=Y
- `M402` Reclaim Timer + REBUILD Discipline (8h baseline) | phase=Phase E — STOP / Protections / Eventing | old=Y new=Y code=Y
- `M406` Structured Event Bus / Taxonomy | phase=Phase E — STOP / Protections / Eventing | old=Y new=Y code=Y
- `M503` HVN/LVN inside box + min spacing | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M703` Zig-Zag Envelope / Channel Enhancements | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M801` MTF POC Confluence (D/W, M advisory) + POC-cross before START | phase=Phase F — Microstructure Modules | old=Y new=Y code=Y
- `M807` VAH/VAL Approximation via Quantiles (fallback/optional) | phase=Phase F — Microstructure Modules | old=N new=Y code=Y

### NOT_IMPLEMENTED Modules (6)
- `M306` Directional skip-one rule (simulator-inspired) | phase=Phase D — Grid / Entry / Exit | old=N new=Y code=N
- `M307` Next-rung ghost lines (UI only) | phase=Phase D — Grid / Entry / Exit | old=N new=Y code=N
- `M903` CVD Spike + Passive Absorption (Insights style) | phase=Phase F — Microstructure Modules | old=Y new=Y code=N
- `M904` CVD Divergence Oscillator Strong Score (advisory) | phase=Phase F — Microstructure Modules | old=Y new=Y code=N
- `M905` SMA200 / EMA trend filters for directional variants | phase=Phase F — Microstructure Modules | old=N new=Y code=N
- `M906` CVD extension line touch counter (UI only) | phase=Phase F — Microstructure Modules | old=N new=Y code=N

### ADHOC Preserved Modules (6)
- `AH-001` Regime Router With Safe Handoffs (intraday/swing/neutral/pause) | status=DONE | source=ADHOC
- `AH-002` Per-Candle Plan History Emit Path For Replay Fidelity | status=DONE | source=ADHOC
- `AH-003` Strategy Variant Harness For Ablations | status=DONE | source=ADHOC
- `AH-004` Walkforward Runner + Latest-Ref Publication | status=DONE | source=ADHOC
- `AH-005` Formal Tuning Protocol Automation | status=DONE | source=ADHOC
- `AH-006` ML Overlay Walkforward Evaluator | status=DONE | source=ADHOC

## 6) Old-Plan Intent Ledger (Readable Cards)
- Non-Mxxx directives are preserved below as migration/continuity cards.

### OI-001 - Brain/Executor/Simulator separation
`Status`: DONE
`Current Reality`
- Architecture preserved.
`Evidence`
- docs/old_plan.txt:7, freqtrade/user_data/strategies/GridBrainV1.py:9599, freqtrade/user_data/scripts/grid_executor_v1.py:2328, freqtrade/user_data/scripts/grid_simulator_v1.py:1229
`Operational Guidance`
1. Keep this directive as baseline unless a replacement is explicitly approved.
2. If changed, update both runtime behavior and linked feature cards.
3. Add regression checks before changing status.

### OI-002 - Deterministic core before ML overlay
`Status`: DONE
`Current Reality`
- ML remains overlay-only.
`Evidence`
- docs/old_plan.txt:38, freqtrade/user_data/strategies/GridBrainV1.py:730, freqtrade/user_data/strategies/GridBrainV1.py:4020
`Operational Guidance`
1. Keep this directive as baseline unless a replacement is explicitly approved.
2. If changed, update both runtime behavior and linked feature cards.
3. Add regression checks before changing status.

### OI-003 - Quote-only inventory default
`Status`: DONE
`Current Reality`
- Historical mixed-inventory intent replaced.
`Evidence`
- docs/old_plan.txt:258, freqtrade/user_data/strategies/GridBrainV1.py:945, freqtrade/user_data/strategies/GridBrainV1.py:9329
`Operational Guidance`
1. Keep this directive as baseline unless a replacement is explicitly approved.
2. If changed, update both runtime behavior and linked feature cards.
3. Add regression checks before changing status.

### OI-004 - One-grid-per-pair operational mode
`Status`: DONE
`Current Reality`
- Enforced by single-plan apply loop.
`Evidence`
- docs/old_plan.txt:40, freqtrade/user_data/strategies/GridBrainV1.py:1033, freqtrade/user_data/scripts/grid_executor_v1.py:2328
`Operational Guidance`
1. Keep this directive as baseline unless a replacement is explicitly approved.
2. If changed, update both runtime behavior and linked feature cards.
3. Add regression checks before changing status.

### OI-005 - Event-driven monitoring and rebuild discipline
`Status`: DONE
`Current Reality`
- Event bus + runtime controls active.
`Evidence`
- docs/old_plan.txt:39, freqtrade/user_data/strategies/GridBrainV1.py:8895, freqtrade/user_data/strategies/GridBrainV1.py:8095
`Operational Guidance`
1. Keep this directive as baseline unless a replacement is explicitly approved.
2. If changed, update both runtime behavior and linked feature cards.
3. Add regression checks before changing status.

### OI-006 - Implementation sequence (deterministic -> simulator -> executor -> modules -> ML)
`Status`: PARTIAL
`Current Reality`
- Sequence mostly implemented; remaining partial modules listed in backlog.
`Evidence`
- docs/old_plan.txt:553, freqtrade/user_data/scripts/run-user-walkforward.py:3, freqtrade/scripts/run-user-tuning-protocol.py:3
`Operational Guidance`
1. Finish remaining implementation scope listed in Current Reality.
2. Add direct tests that prove directive-level behavior.
3. Update status only after code and tests are complete.

## 7) Canonical Reason/Event Wiring Inventory (Readable)
- Format: `CODE` (`status`) | enum=... | emitters=... | tests=...

### BlockReason (WIRED=54, REGISTRY_ONLY=16)
- `BLOCK_7D_EXTREME_CONTEXT` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:1747 ; freqtrade/user_data/strategies/GridBrainV1.py:7730 | tests=freqtrade/user_data/tests/test_phase3_validation.py:139
- `BLOCK_ADX_HIGH` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:1739 | tests=freqtrade/user_data/tests/test_phase3_validation.py:135 ; freqtrade/user_data/tests/test_phase3_validation.py:154
- `BLOCK_BAND_SLOPE_HIGH` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:7732 | tests=none
- `BLOCK_BASIS_CROSS_PENDING` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:7793 ; freqtrade/user_data/strategies/GridBrainV1.py:8040 | tests=none
- `BLOCK_BBWP_HIGH` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:7741 ; freqtrade/user_data/strategies/GridBrainV1.py:7743 | tests=none
- `BLOCK_BBW_EXPANDING` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:1741 | tests=freqtrade/user_data/tests/test_phase3_validation.py:136
- `BLOCK_BOX_CHANNEL_OVERLAP_LOW` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:6723 | tests=none
- `BLOCK_BOX_DONCHIAN_WIDTH_SANITY` (`REGISTRY_ONLY`) | enum=BlockReason | emitters=none | tests=none
- `BLOCK_BOX_ENVELOPE_RATIO_HIGH` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:6737 | tests=none
- `BLOCK_BOX_OVERLAP_HIGH` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:6620 | tests=none
- `BLOCK_BOX_STRADDLE_BREAKOUT_LEVEL` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:7174 | tests=none
- `BLOCK_BOX_STRADDLE_FVG_AVG` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:1263 ; freqtrade/user_data/strategies/GridBrainV1.py:7179 | tests=freqtrade/user_data/tests/test_phase3_validation.py:41
- `BLOCK_BOX_STRADDLE_FVG_EDGE` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:1261 ; freqtrade/user_data/strategies/GridBrainV1.py:7180 ; freqtrade/user_data/strategies/GridBrainV1.py:7181 | tests=freqtrade/user_data/tests/test_phase3_validation.py:40
- `BLOCK_BOX_STRADDLE_HTF_POC` (`REGISTRY_ONLY`) | enum=BlockReason | emitters=none | tests=none
- `BLOCK_BOX_STRADDLE_OB_EDGE` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2948 ; freqtrade/user_data/strategies/GridBrainV1.py:7172 | tests=none
- `BLOCK_BOX_STRADDLE_SESSION_FVG_AVG` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:1268 ; freqtrade/user_data/strategies/GridBrainV1.py:7182 ; freqtrade/user_data/strategies/GridBrainV1.py:7183 ; freqtrade/user_data/strategies/GridBrainV1.py:7184 | tests=freqtrade/user_data/tests/test_phase3_validation.py:42
- `BLOCK_BOX_STRADDLE_VWAP_DONCHIAN_MID` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:7185 ; freqtrade/user_data/strategies/GridBrainV1.py:7186 | tests=none
- `BLOCK_BOX_VP_POC_MISPLACED` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:7178 | tests=none
- `BLOCK_BOX_WIDTH_TOO_NARROW` (`REGISTRY_ONLY`) | enum=BlockReason | emitters=none | tests=none
- `BLOCK_BOX_WIDTH_TOO_WIDE` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:6617 | tests=none
- `BLOCK_BREAKOUT_CONFIRM_DN` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:1664 ; freqtrade/user_data/strategies/GridBrainV1.py:1674 ; freqtrade/user_data/strategies/GridBrainV1.py:6902 ; freqtrade/user_data/strategies/GridBrainV1.py:6903 | tests=none
- `BLOCK_BREAKOUT_CONFIRM_UP` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:1659 ; freqtrade/user_data/strategies/GridBrainV1.py:1673 ; freqtrade/user_data/strategies/GridBrainV1.py:6900 ; freqtrade/user_data/strategies/GridBrainV1.py:6901 | tests=freqtrade/user_data/tests/test_min_range_and_breakout_confirm.py:93
- `BLOCK_BREAKOUT_RECLAIM_PENDING` (`REGISTRY_ONLY`) | enum=BlockReason | emitters=none | tests=none
- `BLOCK_CAPACITY_THIN` (`WIRED`) | enum=BlockReason | emitters=execution/capacity_guard.py:122 ; execution/capacity_guard.py:123 ; freqtrade/user_data/strategies/GridBrainV1.py:7763 ; freqtrade/user_data/strategies/GridBrainV1.py:7795 | tests=freqtrade/user_data/tests/test_executor_hardening.py:361
- `BLOCK_COOLDOWN_ACTIVE` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:8057 | tests=none
- `BLOCK_DATA_DUPLICATE_TS` (`REGISTRY_ONLY`) | enum=BlockReason | emitters=none | tests=none
- `BLOCK_DATA_GAP` (`WIRED`) | enum=BlockReason | emitters=data/data_quality_assessor.py:47 ; data/data_quality_assessor.py:56 ; freqtrade/user_data/strategies/GridBrainV1.py:1756 ; freqtrade/user_data/strategies/GridBrainV1.py:8255 | tests=freqtrade/user_data/tests/test_phase3_validation.py:88 ; freqtrade/user_data/tests/test_phase3_validation.py:289
- `BLOCK_DATA_MISALIGN` (`WIRED`) | enum=BlockReason | emitters=data/data_quality_assessor.py:34 ; data/data_quality_assessor.py:37 ; data/data_quality_assessor.py:40 ; data/data_quality_assessor.py:70 | tests=freqtrade/user_data/tests/test_phase3_validation.py:104
- `BLOCK_DATA_NON_MONOTONIC_TS` (`REGISTRY_ONLY`) | enum=BlockReason | emitters=none | tests=none
- `BLOCK_DRAWDOWN_GUARD` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2920 ; freqtrade/user_data/strategies/GridBrainV1.py:7759 | tests=none
- `BLOCK_DRIFT_SLOPE_HIGH` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:7736 | tests=none
- `BLOCK_EMA_DIST` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:1743 | tests=freqtrade/user_data/tests/test_phase3_validation.py:137
- `BLOCK_EXCURSION_ASYMMETRY` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:7734 | tests=none
- `BLOCK_EXEC_CONFIRM_REBUILD_FAILED` (`REGISTRY_ONLY`) | enum=BlockReason | emitters=none | tests=none
- `BLOCK_EXEC_CONFIRM_START_FAILED` (`REGISTRY_ONLY`) | enum=BlockReason | emitters=none | tests=none
- `BLOCK_FRESH_BREAKOUT` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:581 ; freqtrade/user_data/strategies/GridBrainV1.py:7747 ; freqtrade/user_data/strategies/GridBrainV1.py:8016 | tests=freqtrade/user_data/tests/test_phase3_validation.py:164 ; freqtrade/user_data/tests/test_phase3_validation.py:165
- `BLOCK_FRESH_FVG_COOLOFF` (`REGISTRY_ONLY`) | enum=BlockReason | emitters=none | tests=none
- `BLOCK_FRESH_OB_COOLOFF` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2947 ; freqtrade/user_data/strategies/GridBrainV1.py:7749 ; freqtrade/user_data/strategies/GridBrainV1.py:8018 | tests=none
- `BLOCK_FUNDING_FILTER` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:7755 | tests=none
- `BLOCK_HVP_EXPANDING` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:7757 | tests=none
- `BLOCK_INSIDE_SESSION_FVG` (`REGISTRY_ONLY`) | enum=BlockReason | emitters=none | tests=none
- `BLOCK_LIQ_SWEEP_OPPOSITE_STRUCTURE` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:7761 | tests=none
- `BLOCK_MAX_STOPS_WINDOW` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2921 ; freqtrade/user_data/strategies/GridBrainV1.py:5890 ; freqtrade/user_data/strategies/GridBrainV1.py:8059 | tests=freqtrade/user_data/tests/test_partial_module_completion.py:43
- `BLOCK_META_DRIFT_SOFT` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:7765 | tests=freqtrade/user_data/tests/test_replay_golden_consistency.py:73 ; freqtrade/user_data/tests/test_replay_golden_consistency.py:115 ; freqtrade/user_data/tests/test_replay_golden_consistency.py:116
- `BLOCK_MIN_RANGE_LEN_NOT_MET` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:1640 ; freqtrade/user_data/strategies/GridBrainV1.py:6897 | tests=freqtrade/user_data/tests/test_min_range_and_breakout_confirm.py:31
- `BLOCK_MIN_RUNTIME_NOT_MET` (`REGISTRY_ONLY`) | enum=BlockReason | emitters=none | tests=none
- `BLOCK_MRVD_CONFLUENCE_FAIL` (`REGISTRY_ONLY`) | enum=BlockReason | emitters=none | tests=none
- `BLOCK_MRVD_POC_DRIFT_GUARD` (`REGISTRY_ONLY`) | enum=BlockReason | emitters=none | tests=none
- `BLOCK_NO_POC_ACCEPTANCE` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:7787 ; freqtrade/user_data/strategies/GridBrainV1.py:8071 | tests=none
- `BLOCK_N_LEVELS_INVALID` (`REGISTRY_ONLY`) | enum=BlockReason | emitters=none | tests=none
- `BLOCK_OS_DEV_DIRECTIONAL` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:7770 | tests=none
- `BLOCK_OS_DEV_NEUTRAL_PERSISTENCE` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:7772 | tests=none
- `BLOCK_POC_ALIGNMENT_FAIL` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:1511 ; freqtrade/user_data/strategies/GridBrainV1.py:7789 ; freqtrade/user_data/strategies/GridBrainV1.py:8073 | tests=freqtrade/user_data/tests/test_phase3_validation.py:445
- `BLOCK_RECLAIM_NOT_CONFIRMED` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:5926 ; freqtrade/user_data/strategies/GridBrainV1.py:8061 | tests=freqtrade/user_data/tests/test_partial_module_completion.py:113
- `BLOCK_RECLAIM_PENDING` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:8055 | tests=none
- `BLOCK_RVOL_SPIKE` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:1745 | tests=freqtrade/user_data/tests/test_phase3_validation.py:138
- `BLOCK_SESSION_FVG_PAUSE` (`REGISTRY_ONLY`) | enum=BlockReason | emitters=none | tests=none
- `BLOCK_SQUEEZE_RELEASE_AGAINST_BIAS` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:1327 ; freqtrade/user_data/strategies/GridBrainV1.py:7774 ; freqtrade/user_data/strategies/GridBrainV1.py:7776 | tests=freqtrade/user_data/tests/test_phase3_validation.py:226
- `BLOCK_STALE_FEATURES` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:7767 | tests=none
- `BLOCK_START_BOX_POSITION` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:7783 ; freqtrade/user_data/strategies/GridBrainV1.py:8038 | tests=freqtrade/user_data/tests/test_phase3_validation.py:942 ; freqtrade/user_data/tests/test_partial_module_completion.py:250
- `BLOCK_START_CONFLUENCE_LOW` (`REGISTRY_ONLY`) | enum=BlockReason | emitters=none | tests=none
- `BLOCK_START_PERSISTENCE_FAIL` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:7738 | tests=none
- `BLOCK_START_RSI_BAND` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:7785 ; freqtrade/user_data/strategies/GridBrainV1.py:8051 | tests=none
- `BLOCK_START_STABILITY_LOW` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:8030 | tests=none
- `BLOCK_STEP_BELOW_COST` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:6844 ; freqtrade/user_data/strategies/GridBrainV1.py:6869 | tests=none
- `BLOCK_STEP_BELOW_EMPIRICAL_COST` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:6842 ; freqtrade/user_data/strategies/GridBrainV1.py:6867 | tests=none
- `BLOCK_VAH_VAL_POC_PROXIMITY` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:7791 ; freqtrade/user_data/strategies/GridBrainV1.py:8042 | tests=none
- `BLOCK_VOL_BUCKET_UNSTABLE` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:8028 | tests=none
- `BLOCK_ZERO_VOL_ANOMALY` (`WIRED`) | enum=BlockReason | emitters=data/data_quality_assessor.py:63 | tests=freqtrade/user_data/tests/test_phase3_validation.py:122 ; freqtrade/user_data/tests/test_phase3_validation.py:288
- `COOLOFF_BBWP_EXTREME` (`WIRED`) | enum=BlockReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:7745 | tests=none

### EventType (WIRED=35, REGISTRY_ONLY=26)
- `EVENT_BBWP_EXTREME` (`REGISTRY_ONLY`) | enum=EventType | emitters=none | tests=none
- `EVENT_BREAKOUT_BEAR` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:8205 | tests=none
- `EVENT_BREAKOUT_BULL` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:8203 | tests=none
- `EVENT_CHANNEL_MIDLINE_TOUCH` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2931 ; freqtrade/user_data/strategies/GridBrainV1.py:8215 | tests=none
- `EVENT_CHANNEL_STRONG_BREAK_DN` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2895 ; freqtrade/user_data/strategies/GridBrainV1.py:2930 ; freqtrade/user_data/strategies/GridBrainV1.py:8209 | tests=none
- `EVENT_CHANNEL_STRONG_BREAK_UP` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2894 ; freqtrade/user_data/strategies/GridBrainV1.py:2929 ; freqtrade/user_data/strategies/GridBrainV1.py:8207 | tests=none
- `EVENT_CVD_BEAR_DIV` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:8245 | tests=none
- `EVENT_CVD_BOS_DN` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:8249 | tests=none
- `EVENT_CVD_BOS_UP` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:8247 | tests=none
- `EVENT_CVD_BULL_DIV` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:8243 | tests=none
- `EVENT_CVD_SPIKE_NEG` (`REGISTRY_ONLY`) | enum=EventType | emitters=none | tests=none
- `EVENT_CVD_SPIKE_POS` (`REGISTRY_ONLY`) | enum=EventType | emitters=none | tests=none
- `EVENT_DATA_GAP_DETECTED` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2900 ; freqtrade/user_data/strategies/GridBrainV1.py:2979 ; freqtrade/user_data/strategies/GridBrainV1.py:8256 | tests=none
- `EVENT_DATA_MISALIGN_DETECTED` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2901 ; freqtrade/user_data/strategies/GridBrainV1.py:2980 ; freqtrade/user_data/strategies/GridBrainV1.py:8258 | tests=none
- `EVENT_DEPTH_THIN` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2907 ; freqtrade/user_data/strategies/GridBrainV1.py:2969 ; freqtrade/user_data/strategies/GridBrainV1.py:5814 ; freqtrade/user_data/scripts/grid_executor_v1.py:1256 | tests=none
- `EVENT_DONCHIAN_STRONG_BREAK_DN` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2897 ; freqtrade/user_data/strategies/GridBrainV1.py:2933 ; freqtrade/user_data/strategies/GridBrainV1.py:8213 | tests=none
- `EVENT_DONCHIAN_STRONG_BREAK_UP` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2896 ; freqtrade/user_data/strategies/GridBrainV1.py:2932 ; freqtrade/user_data/strategies/GridBrainV1.py:8211 | tests=none
- `EVENT_DRIFT_RETEST_DN` (`REGISTRY_ONLY`) | enum=EventType | emitters=none | tests=none
- `EVENT_DRIFT_RETEST_UP` (`REGISTRY_ONLY`) | enum=EventType | emitters=none | tests=none
- `EVENT_EXTREME_RETEST_BOTTOM` (`REGISTRY_ONLY`) | enum=EventType | emitters=none | tests=none
- `EVENT_EXTREME_RETEST_TOP` (`REGISTRY_ONLY`) | enum=EventType | emitters=none | tests=none
- `EVENT_EXT_1386_RETEST_BOTTOM` (`REGISTRY_ONLY`) | enum=EventType | emitters=none | tests=none
- `EVENT_EXT_1386_RETEST_TOP` (`REGISTRY_ONLY`) | enum=EventType | emitters=none | tests=none
- `EVENT_FVG_MITIGATED_BEAR` (`REGISTRY_ONLY`) | enum=EventType | emitters=none | tests=none
- `EVENT_FVG_MITIGATED_BULL` (`REGISTRY_ONLY`) | enum=EventType | emitters=none | tests=none
- `EVENT_FVG_NEW_BEAR` (`REGISTRY_ONLY`) | enum=EventType | emitters=none | tests=none
- `EVENT_FVG_NEW_BULL` (`REGISTRY_ONLY`) | enum=EventType | emitters=none | tests=none
- `EVENT_FVG_POC_TAG` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2956 ; freqtrade/user_data/strategies/GridBrainV1.py:8236 | tests=none
- `EVENT_HVN_TOUCH` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2962 | tests=none
- `EVENT_IMFVG_AVG_TAG_BEAR` (`REGISTRY_ONLY`) | enum=EventType | emitters=none | tests=none
- `EVENT_IMFVG_AVG_TAG_BULL` (`REGISTRY_ONLY`) | enum=EventType | emitters=none | tests=none
- `EVENT_JUMP_DETECTED` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2908 ; freqtrade/user_data/strategies/GridBrainV1.py:2970 ; freqtrade/user_data/strategies/GridBrainV1.py:5818 ; freqtrade/user_data/scripts/grid_executor_v1.py:1262 | tests=none
- `EVENT_LVN_TOUCH` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2963 | tests=none
- `EVENT_LVN_VOID_EXIT` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2964 ; freqtrade/user_data/strategies/GridBrainV1.py:8241 | tests=none
- `EVENT_META_DRIFT_HARD` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2893 ; freqtrade/user_data/strategies/GridBrainV1.py:8253 | tests=none
- `EVENT_META_DRIFT_SOFT` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2905 ; freqtrade/user_data/strategies/GridBrainV1.py:8251 | tests=none
- `EVENT_MICRO_POC_SHIFT` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2961 | tests=none
- `EVENT_OB_NEW_BEAR` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2950 ; freqtrade/user_data/strategies/GridBrainV1.py:8229 | tests=none
- `EVENT_OB_NEW_BULL` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2949 ; freqtrade/user_data/strategies/GridBrainV1.py:8227 | tests=none
- `EVENT_OB_TAGGED_BEAR` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2952 ; freqtrade/user_data/strategies/GridBrainV1.py:8233 | tests=none
- `EVENT_OB_TAGGED_BULL` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2951 ; freqtrade/user_data/strategies/GridBrainV1.py:8231 | tests=none
- `EVENT_PASSIVE_ABSORPTION_DN` (`REGISTRY_ONLY`) | enum=EventType | emitters=none | tests=none
- `EVENT_PASSIVE_ABSORPTION_UP` (`REGISTRY_ONLY`) | enum=EventType | emitters=none | tests=none
- `EVENT_POC_ACCEPTANCE_CROSS` (`REGISTRY_ONLY`) | enum=EventType | emitters=none | tests=none
- `EVENT_POC_TEST` (`REGISTRY_ONLY`) | enum=EventType | emitters=none | tests=freqtrade/tests/scripts/test_schema_contracts.py:86
- `EVENT_POST_ONLY_REJECT_BURST` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2909 ; freqtrade/user_data/strategies/GridBrainV1.py:2971 ; freqtrade/user_data/strategies/GridBrainV1.py:5816 ; freqtrade/user_data/scripts/grid_executor_v1.py:1124 | tests=none
- `EVENT_RANGE_HIT_BOTTOM` (`REGISTRY_ONLY`) | enum=EventType | emitters=none | tests=none
- `EVENT_RANGE_HIT_TOP` (`REGISTRY_ONLY`) | enum=EventType | emitters=none | tests=none
- `EVENT_RECLAIM_CONFIRMED` (`REGISTRY_ONLY`) | enum=EventType | emitters=none | tests=none
- `EVENT_SESSION_FVG_MITIGATED` (`REGISTRY_ONLY`) | enum=EventType | emitters=none | tests=none
- `EVENT_SESSION_FVG_NEW` (`REGISTRY_ONLY`) | enum=EventType | emitters=none | tests=none
- `EVENT_SESSION_HIGH_SWEEP` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2941 ; freqtrade/user_data/strategies/GridBrainV1.py:8217 | tests=freqtrade/user_data/tests/test_partial_module_completion.py:254 ; freqtrade/user_data/tests/test_partial_module_completion.py:255 ; freqtrade/user_data/tests/test_partial_module_completion.py:263
- `EVENT_SESSION_LOW_SWEEP` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2942 ; freqtrade/user_data/strategies/GridBrainV1.py:8220 | tests=none
- `EVENT_SPREAD_SPIKE` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2906 ; freqtrade/user_data/strategies/GridBrainV1.py:2968 ; freqtrade/user_data/strategies/GridBrainV1.py:5812 ; freqtrade/user_data/scripts/grid_executor_v1.py:1250 | tests=freqtrade/user_data/tests/test_partial_module_completion.py:98
- `EVENT_SQUEEZE_RELEASE_DN` (`REGISTRY_ONLY`) | enum=EventType | emitters=none | tests=none
- `EVENT_SQUEEZE_RELEASE_UP` (`REGISTRY_ONLY`) | enum=EventType | emitters=none | tests=none
- `EVENT_SWEEP_BREAK_RETEST_HIGH` (`WIRED`) | enum=EventType | emitters=planner/structure/liquidity_sweeps.py:308 ; freqtrade/user_data/strategies/GridBrainV1.py:2898 ; freqtrade/user_data/strategies/GridBrainV1.py:2939 ; freqtrade/user_data/strategies/GridBrainV1.py:8223 | tests=none
- `EVENT_SWEEP_BREAK_RETEST_LOW` (`WIRED`) | enum=EventType | emitters=planner/structure/liquidity_sweeps.py:310 ; freqtrade/user_data/strategies/GridBrainV1.py:2899 ; freqtrade/user_data/strategies/GridBrainV1.py:2940 ; freqtrade/user_data/strategies/GridBrainV1.py:8225 | tests=none
- `EVENT_SWEEP_WICK_HIGH` (`WIRED`) | enum=EventType | emitters=planner/structure/liquidity_sweeps.py:304 ; freqtrade/user_data/strategies/GridBrainV1.py:2937 ; freqtrade/user_data/strategies/GridBrainV1.py:8218 | tests=none
- `EVENT_SWEEP_WICK_LOW` (`WIRED`) | enum=EventType | emitters=planner/structure/liquidity_sweeps.py:306 ; freqtrade/user_data/strategies/GridBrainV1.py:2938 ; freqtrade/user_data/strategies/GridBrainV1.py:8221 | tests=none
- `EVENT_VRVP_POC_SHIFT` (`WIRED`) | enum=EventType | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2960 | tests=none

### ExecCode (WIRED=13, REGISTRY_ONLY=8)
- `EXEC_CAPACITY_NOTIONAL_CAP_APPLIED` (`REGISTRY_ONLY`) | enum=ExecCode | emitters=none | tests=none
- `EXEC_CAPACITY_RUNG_CAP_APPLIED` (`WIRED`) | enum=ExecCode | emitters=freqtrade/user_data/scripts/grid_executor_v1.py:1407 | tests=freqtrade/user_data/tests/test_executor_hardening.py:335
- `EXEC_CONFIRM_EXIT_FAILSAFE` (`WIRED`) | enum=ExecCode | emitters=freqtrade/user_data/scripts/grid_executor_v1.py:2498 ; freqtrade/user_data/scripts/grid_executor_v1.py:2499 | tests=freqtrade/user_data/tests/test_executor_hardening.py:172 ; freqtrade/user_data/tests/test_executor_hardening.py:173
- `EXEC_CONFIRM_REBUILD_FAILED` (`WIRED`) | enum=ExecCode | emitters=freqtrade/user_data/scripts/grid_executor_v1.py:2477 | tests=freqtrade/user_data/tests/test_executor_hardening.py:198
- `EXEC_CONFIRM_START_FAILED` (`WIRED`) | enum=ExecCode | emitters=freqtrade/user_data/scripts/grid_executor_v1.py:2480 | tests=freqtrade/user_data/tests/test_executor_hardening.py:149
- `EXEC_FILL_DUPLICATE_GUARD_HIT` (`REGISTRY_ONLY`) | enum=ExecCode | emitters=none | tests=none
- `EXEC_FILL_REPLACEMENT_PLACED` (`REGISTRY_ONLY`) | enum=ExecCode | emitters=none | tests=none
- `EXEC_ORDER_CANCEL_REPLACE_APPLIED` (`WIRED`) | enum=ExecCode | emitters=freqtrade/user_data/scripts/grid_executor_v1.py:2082 | tests=none
- `EXEC_ORDER_TIMEOUT_REPRICE` (`REGISTRY_ONLY`) | enum=ExecCode | emitters=none | tests=none
- `EXEC_PLAN_APPLIED` (`WIRED`) | enum=ExecCode | emitters=freqtrade/user_data/scripts/grid_executor_v1.py:2335 | tests=freqtrade/tests/scripts/test_grid_executor_handoff.py:94
- `EXEC_PLAN_DUPLICATE_IGNORED` (`WIRED`) | enum=ExecCode | emitters=freqtrade/user_data/scripts/grid_executor_v1.py:856 ; freqtrade/user_data/scripts/grid_executor_v1.py:857 ; freqtrade/user_data/scripts/grid_executor_v1.py:860 ; freqtrade/user_data/scripts/grid_executor_v1.py:861 | tests=freqtrade/tests/scripts/test_grid_executor_handoff.py:107 ; freqtrade/tests/scripts/test_grid_executor_handoff.py:153
- `EXEC_PLAN_EXPIRED_IGNORED` (`WIRED`) | enum=ExecCode | emitters=freqtrade/user_data/scripts/grid_executor_v1.py:851 ; freqtrade/user_data/scripts/grid_executor_v1.py:852 | tests=none
- `EXEC_PLAN_HASH_MISMATCH` (`WIRED`) | enum=ExecCode | emitters=freqtrade/user_data/scripts/grid_executor_v1.py:845 ; freqtrade/user_data/scripts/grid_executor_v1.py:848 | tests=freqtrade/tests/scripts/test_grid_executor_handoff.py:120
- `EXEC_PLAN_SCHEMA_INVALID` (`WIRED`) | enum=ExecCode | emitters=freqtrade/user_data/scripts/grid_executor_v1.py:816 ; freqtrade/user_data/scripts/grid_executor_v1.py:817 ; freqtrade/user_data/scripts/grid_executor_v1.py:821 ; freqtrade/user_data/scripts/grid_executor_v1.py:822 | tests=freqtrade/tests/scripts/test_grid_executor_handoff.py:194 ; freqtrade/tests/scripts/test_grid_executor_handoff.py:206
- `EXEC_PLAN_STALE_SEQ_IGNORED` (`WIRED`) | enum=ExecCode | emitters=freqtrade/user_data/scripts/grid_executor_v1.py:870 ; freqtrade/user_data/scripts/grid_executor_v1.py:873 ; freqtrade/user_data/scripts/grid_executor_v1.py:882 ; freqtrade/user_data/scripts/grid_executor_v1.py:888 | tests=freqtrade/tests/scripts/test_grid_executor_handoff.py:113 ; freqtrade/tests/scripts/test_grid_executor_handoff.py:169 ; freqtrade/tests/scripts/test_grid_executor_handoff.py:183
- `EXEC_POST_ONLY_FALLBACK_REPRICE` (`WIRED`) | enum=ExecCode | emitters=freqtrade/user_data/scripts/grid_executor_v1.py:1924 | tests=freqtrade/user_data/tests/test_executor_hardening.py:128
- `EXEC_POST_ONLY_RETRY` (`WIRED`) | enum=ExecCode | emitters=freqtrade/user_data/scripts/grid_executor_v1.py:1121 ; freqtrade/user_data/scripts/grid_executor_v1.py:1147 ; freqtrade/user_data/scripts/grid_executor_v1.py:1909 | tests=freqtrade/user_data/tests/test_executor_hardening.py:127
- `EXEC_RECONCILE_HOLD_NO_MATERIAL_CHANGE` (`REGISTRY_ONLY`) | enum=ExecCode | emitters=none | tests=none
- `EXEC_RECONCILE_MATERIAL_REBUILD` (`REGISTRY_ONLY`) | enum=ExecCode | emitters=none | tests=none
- `EXEC_RECONCILE_START_LADDER_CREATED` (`REGISTRY_ONLY`) | enum=ExecCode | emitters=none | tests=none
- `EXEC_RECONCILE_STOP_CANCELLED_LADDER` (`REGISTRY_ONLY`) | enum=ExecCode | emitters=none | tests=none

### InfoCode (WIRED=0, REGISTRY_ONLY=5)
- `INFO_BOX_SHIFT_APPLIED` (`REGISTRY_ONLY`) | enum=InfoCode | emitters=none | tests=none
- `INFO_REPLAN_EPOCH_BOUNDARY` (`REGISTRY_ONLY`) | enum=InfoCode | emitters=none | tests=none
- `INFO_SL_SOURCE_SELECTED` (`REGISTRY_ONLY`) | enum=InfoCode | emitters=none | tests=none
- `INFO_TARGET_SOURCE_SELECTED` (`REGISTRY_ONLY`) | enum=InfoCode | emitters=none | tests=none
- `INFO_VOL_BUCKET_CHANGED` (`REGISTRY_ONLY`) | enum=InfoCode | emitters=none | tests=none

### PauseReason (WIRED=1, REGISTRY_ONLY=5)
- `PAUSE_BBWP_COOLOFF` (`REGISTRY_ONLY`) | enum=PauseReason | emitters=none | tests=none
- `PAUSE_DATA_DEGRADED` (`REGISTRY_ONLY`) | enum=PauseReason | emitters=none | tests=none
- `PAUSE_DATA_QUARANTINE` (`REGISTRY_ONLY`) | enum=PauseReason | emitters=none | tests=none
- `PAUSE_EXECUTION_UNSAFE` (`WIRED`) | enum=PauseReason | emitters=freqtrade/user_data/scripts/grid_executor_v1.py:1126 ; freqtrade/user_data/scripts/grid_executor_v1.py:1149 ; freqtrade/user_data/scripts/grid_executor_v1.py:1244 ; freqtrade/user_data/scripts/grid_executor_v1.py:1249 | tests=freqtrade/user_data/tests/test_executor_hardening.py:148
- `PAUSE_META_DRIFT_SOFT` (`REGISTRY_ONLY`) | enum=PauseReason | emitters=none | tests=none
- `PAUSE_SESSION_FVG` (`REGISTRY_ONLY`) | enum=PauseReason | emitters=none | tests=none

### ReplanReason (WIRED=3, REGISTRY_ONLY=6)
- `REPLAN_DEFERRED_ACTIVE_FILL_WINDOW` (`REGISTRY_ONLY`) | enum=ReplanReason | emitters=none | tests=none
- `REPLAN_DUPLICATE_PLAN_HASH` (`REGISTRY_ONLY`) | enum=ReplanReason | emitters=none | tests=none
- `REPLAN_EPOCH_DEFERRED` (`REGISTRY_ONLY`) | enum=ReplanReason | emitters=none | tests=none
- `REPLAN_HARD_STOP_OVERRIDE` (`WIRED`) | enum=ReplanReason | emitters=planner/replan_policy.py:63 | tests=none
- `REPLAN_MATERIAL_BOX_CHANGE` (`WIRED`) | enum=ReplanReason | emitters=planner/replan_policy.py:67 | tests=freqtrade/user_data/tests/test_phase3_validation.py:914 ; freqtrade/user_data/tests/test_executor_hardening.py:31 ; freqtrade/user_data/tests/test_partial_module_completion.py:222
- `REPLAN_MATERIAL_GRID_CHANGE` (`REGISTRY_ONLY`) | enum=ReplanReason | emitters=none | tests=freqtrade/tests/scripts/test_plan_signature_contract.py:77
- `REPLAN_MATERIAL_RISK_CHANGE` (`REGISTRY_ONLY`) | enum=ReplanReason | emitters=none | tests=none
- `REPLAN_NOOP_MINOR_DELTA` (`WIRED`) | enum=ReplanReason | emitters=planner/replan_policy.py:71 ; planner/replan_policy.py:75 | tests=freqtrade/tests/scripts/test_section21_modules.py:203
- `REPLAN_SOFT_ADJUST_ONLY` (`REGISTRY_ONLY`) | enum=ReplanReason | emitters=none | tests=none

### StopReason (WIRED=8, REGISTRY_ONLY=12)
- `STOP_BREAKOUT_2STRIKE_DN` (`REGISTRY_ONLY`) | enum=StopReason | emitters=none | tests=none
- `STOP_BREAKOUT_2STRIKE_UP` (`REGISTRY_ONLY`) | enum=StopReason | emitters=none | tests=none
- `STOP_BREAKOUT_CONFIRM_DN` (`WIRED`) | enum=StopReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:1662 ; freqtrade/user_data/strategies/GridBrainV1.py:1672 ; freqtrade/user_data/strategies/GridBrainV1.py:7644 ; freqtrade/user_data/strategies/GridBrainV1.py:7681 | tests=freqtrade/user_data/tests/test_min_range_and_breakout_confirm.py:112
- `STOP_BREAKOUT_CONFIRM_UP` (`WIRED`) | enum=StopReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:1657 ; freqtrade/user_data/strategies/GridBrainV1.py:1671 ; freqtrade/user_data/strategies/GridBrainV1.py:7643 ; freqtrade/user_data/strategies/GridBrainV1.py:7679 | tests=none
- `STOP_CHANNEL_STRONG_BREAK` (`WIRED`) | enum=StopReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2928 ; freqtrade/user_data/strategies/GridBrainV1.py:7683 | tests=none
- `STOP_DATA_QUARANTINE` (`REGISTRY_ONLY`) | enum=StopReason | emitters=none | tests=none
- `STOP_DRAWDOWN_GUARD` (`WIRED`) | enum=StopReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2922 ; freqtrade/user_data/strategies/GridBrainV1.py:7687 | tests=none
- `STOP_EXEC_CONFIRM_EXIT_FAILSAFE` (`WIRED`) | enum=StopReason | emitters=freqtrade/user_data/scripts/grid_executor_v1.py:2498 | tests=freqtrade/user_data/tests/test_executor_hardening.py:172
- `STOP_FAST_MOVE_DN` (`REGISTRY_ONLY`) | enum=StopReason | emitters=none | tests=none
- `STOP_FAST_MOVE_UP` (`REGISTRY_ONLY`) | enum=StopReason | emitters=none | tests=none
- `STOP_FRESH_STRUCTURE` (`REGISTRY_ONLY`) | enum=StopReason | emitters=none | tests=none
- `STOP_FVG_VOID_CONFLUENCE` (`WIRED`) | enum=StopReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:7689 | tests=none
- `STOP_LIQUIDITY_SWEEP_BREAK_RETEST` (`WIRED`) | enum=StopReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:2943 ; freqtrade/user_data/strategies/GridBrainV1.py:7685 | tests=none
- `STOP_LVN_VOID_EXIT_ACCEL` (`REGISTRY_ONLY`) | enum=StopReason | emitters=none | tests=none
- `STOP_META_DRIFT_HARD` (`WIRED`) | enum=StopReason | emitters=freqtrade/user_data/strategies/GridBrainV1.py:519 | tests=none
- `STOP_MRVD_AVG_BREAK` (`REGISTRY_ONLY`) | enum=StopReason | emitters=none | tests=none
- `STOP_OS_DEV_DIRECTIONAL_FLIP` (`REGISTRY_ONLY`) | enum=StopReason | emitters=none | tests=none
- `STOP_RANGE_SHIFT` (`REGISTRY_ONLY`) | enum=StopReason | emitters=none | tests=freqtrade/user_data/tests/test_phase3_validation.py:944 ; freqtrade/user_data/tests/test_partial_module_completion.py:252
- `STOP_SESSION_FVG_AGAINST_BIAS` (`REGISTRY_ONLY`) | enum=StopReason | emitters=none | tests=none
- `STOP_SQUEEZE_RELEASE_AGAINST` (`REGISTRY_ONLY`) | enum=StopReason | emitters=none | tests=none

### WarningCode (WIRED=3, REGISTRY_ONLY=5)
- `WARN_COST_MODEL_STALE` (`WIRED`) | enum=WarningCode | emitters=freqtrade/user_data/strategies/GridBrainV1.py:5032 | tests=freqtrade/user_data/tests/test_phase3_validation.py:562 ; freqtrade/user_data/tests/test_phase3_validation.py:603 ; freqtrade/user_data/tests/test_phase3_validation.py:650
- `WARN_CVD_DATA_QUALITY_LOW` (`REGISTRY_ONLY`) | enum=WarningCode | emitters=none | tests=none
- `WARN_EXEC_POST_ONLY_RETRY_HIGH` (`WIRED`) | enum=WarningCode | emitters=freqtrade/user_data/scripts/grid_executor_v1.py:1121 ; freqtrade/user_data/scripts/grid_executor_v1.py:1147 | tests=none
- `WARN_EXEC_REPRICE_RATE_HIGH` (`REGISTRY_ONLY`) | enum=WarningCode | emitters=none | tests=none
- `WARN_FEATURE_FALLBACK_USED` (`REGISTRY_ONLY`) | enum=WarningCode | emitters=none | tests=none
- `WARN_PARTIAL_DATA_WINDOW` (`REGISTRY_ONLY`) | enum=WarningCode | emitters=none | tests=none
- `WARN_PLAN_EXPIRES_SOON` (`REGISTRY_ONLY`) | enum=WarningCode | emitters=none | tests=none
- `WARN_VRVP_UNAVAILABLE_FALLBACK_POC` (`WIRED`) | enum=WarningCode | emitters=freqtrade/user_data/strategies/GridBrainV1.py:8083 | tests=none

## 8) Replacement / Removal Ledger (Readable Cards)
- Each card shows what changed, why it changed, and what must stay protected.

### RR-001
`Before`: Mixed inventory planning defaults (`docs/old_plan.txt:260`)
`Now`: Quote-only capital policy in plan runtime (`freqtrade/user_data/strategies/GridBrainV1.py:945`, `freqtrade/user_data/strategies/GridBrainV1.py:9329`)
`Assessment`: Superior for deterministic execution safety
`Regression Risk`: Medium (if mixed inventory use-case returns)
`Action Plan`
1. Keep quote-only default; add explicit variant if mixed mode is revived.
2. Keep assumptions explicit in tests and release notes when behavior changes.
3. Define rollback trigger/owner before high-risk swaps.

### RR-002
`Before`: Static cost-only floor assumptions
`Now`: Empirical+static hybrid floor (`freqtrade/user_data/strategies/GridBrainV1.py:4881`, `freqtrade/user_data/scripts/grid_executor_v1.py:1579`)
`Assessment`: Superior
`Regression Risk`: Low
`Action Plan`
1. Keep empirical stale warnings and live-sample gating.
2. Keep assumptions explicit in tests and release notes when behavior changes.
3. Define rollback trigger/owner before high-risk swaps.

### RR-003
`Before`: Unstructured blocker strings
`Now`: Canonical enums + decision/event logs (`core/enums.py:145`, `freqtrade/user_data/strategies/GridBrainV1.py:2994`)
`Assessment`: Superior
`Regression Risk`: Medium
`Action Plan`
1. Finish registry-only code cleanup to reduce drift.
2. Keep assumptions explicit in tests and release notes when behavior changes.
3. Define rollback trigger/owner before high-risk swaps.

### RR-004
`Before`: Simple range-only mode intent
`Now`: Regime router with mode handoff safety (`freqtrade/user_data/strategies/GridBrainV1.py:2373`)
`Assessment`: Superior
`Regression Risk`: Medium
`Action Plan`
1. Keep router ablation variants for controlled comparisons.
2. Keep assumptions explicit in tests and release notes when behavior changes.
3. Define rollback trigger/owner before high-risk swaps.

### RR-005
`Before`: Manual tuning-only workflow
`Now`: Automated tuning protocol runner (`freqtrade/scripts/run-user-tuning-protocol.py:855`)
`Assessment`: Superior
`Regression Risk`: Low
`Action Plan`
1. Maintain schema + strict gate tests.
2. Keep assumptions explicit in tests and release notes when behavior changes.
3. Define rollback trigger/owner before high-risk swaps.

### RR-006
`Before`: Reclaim baseline 8h historical convention
`Now`: Runtime default 4h (`freqtrade/user_data/strategies/GridBrainV1.py:790`)
`Assessment`: Incomplete equivalence
`Regression Risk`: Medium
`Action Plan`
1. Decide canonical baseline and align docs/config/tests.
2. Keep assumptions explicit in tests and release notes when behavior changes.
3. Define rollback trigger/owner before high-risk swaps.

## 9) Registry Lifecycle Policy (`ACTIVE` / `RETIRED` / `PARKED_FUTURE`)
- This policy is mandatory for every `REGISTRY_ONLY` code and for removed/replaced logic discovered in history analysis.

### `ACTIVE`
- Meaning: required now for live strategy behavior and acceptance gates.
- Required action: wire emitters/consumers and tests; remove `REGISTRY_ONLY` status.

### `RETIRED`
- Meaning: not needed for current strategy direction.
- Code handling:
1. Do not keep commented-out dead logic in runtime modules.
2. If rollback risk is low: hard-delete dead paths in the same change.
3. If rollback risk is medium/high: soft-retire for one checkpoint using explicit feature flag or compatibility shim, then hard-delete at the next checkpoint.
4. Keep traceability in plan/ledger and commit history; do not keep dead code as inline comments.

### `PARKED_FUTURE`
- Meaning: idea is kept intentionally for future scope but not active now.
- Code handling:
1. Keep only minimal contract/documentation markers.
2. Do not wire emitters or runtime branches yet.
3. Promote to `ACTIVE` only with explicit acceptance criteria and owner.

## 10) Consolidated TODO Backlog (Priority Ordered)
### P0 (Immediate, Execution-Critical)
1. `P0-1` Full git-history archaeology for removed/replaced features. `Status`: DONE (`docs/REMOVED_FEATURE_RELEVANCE_LEDGER.md`).
- Acceptance: produce a Removed Feature Relevance Ledger with `RESTORE` / `KEEP_REMOVED` / `INVESTIGATE` for each candidate. `Completed`: 2026-02-28.
2. `P0-2` Registry-only lifecycle triage for all `83` codes in Section 7. `Status`: DONE (`docs/REGISTRY_LIFECYCLE_TRIAGE.md`).
- Acceptance: every code classified as `ACTIVE` / `RETIRED` / `PARKED_FUTURE`, with owner, rationale, and target checkpoint. `Completed`: 2026-02-28.
3. `P0-3` Baseline code review (quality, logic faults, bug risk, security posture). `Status`: DONE (`docs/P0_3_BASELINE_CODE_REVIEW.md`).
- Acceptance: severity-ranked findings list and fix queue. `Completed`: 2026-02-28.
4. `P0-4` Baseline frozen metrics snapshot before behavior changes (`C0`). `Status`: DONE (`docs/C0_BASELINE_SNAPSHOT.md`).
- Acceptance: regression + backtest + walkforward snapshot stored as comparison baseline. `Completed`: 2026-02-28.
5. `P0-5` Implement `M306` Directional skip-one rule.
- Acceptance: simulator/executor parity + deterministic tests.
6. `P0-6` Checkpoint `C1` after `M306`.
- Acceptance: rerun regression + backtest + walkforward; produce delta report vs `C0`; run focused review.
7. `P0-7` Align `M402` reclaim baseline policy (4h vs 8h) across docs/config/tests.
- Acceptance: one canonical baseline value and synchronized assertions.
8. `P0-8` Checkpoint `C2` after `M402`.
- Acceptance: rerun regression + backtest + walkforward; produce delta report vs `C0`; run focused review.
9. `P0-9` Implement `M903` + `M904`.
- Acceptance: bounded advisory effects + dedicated false-positive-control tests.
10. `P0-10` Checkpoint `C3` after `M903/M904`.
- Acceptance: rerun regression + backtest + walkforward; produce delta report vs `C0`; run focused review.

### P1 (Next, Scope Completion)
11. `P1-1` Execute high-impact `ACTIVE` outputs from registry triage first (`BlockReason`, `StopReason`, `ExecCode`, `ReplanReason`, `WarningCode`).
12. `P1-2` Continue remaining module backlog in controlled batches: `M203`, `M503`, `M703`, `M801`, `M807`, `M905`, `M906`, `M113`, `M406`.
13. `P1-3` After each P1 batch, run checkpoint cycle `C4+`:
- Regression + backtest + walkforward rerun.
- Focused code review and bug/security sweep.
- Status promotion only after acceptance passes.

### P2 (Optimization / Challenge Pass)
14. `P2-1` Optional external-model challenge pass (browser ChatGPT) only after internal evidence pass.
- Acceptance: external suggestions are either adopted with repo evidence or rejected with rationale; repo evidence remains source of truth.

## 11) Final Bible Plan (Execution Order)
1. Complete `P0-1` to `P0-4` before changing runtime behavior.
2. Execute feature changes in this strict order: `M306` -> `M402` -> `M903/M904`.
3. Enforce checkpoints after each P0 feature batch (`C1`, `C2`, `C3`), each with regression + backtest + walkforward + focused review.
4. Execute P1 backlog only after P0 checkpoint deltas are accepted.
5. Keep `AH-*` modules preserved unless a replacement is approved and checkpoint-validated.

## 12) Immediate Next Sprint Cut (Recommended)
1. `P0-3` high-severity fixes (`F-001`, `F-002`) implemented with tests. `Status`: DONE (`docs/P0_3_BASELINE_CODE_REVIEW.md`).
2. Close `INVESTIGATE` setup from `P0-1` (`RF-002`, `RF-003`, `RF-004`, `RF-023`, `RF-024`) by defining checkpoint experiments.
3. Resolve known `C0` red gates (regression compile gate + regression recency assertion) before `C1`. `Status`: DONE (`docs/C0_RED_GATES_CLOSURE.md`).
4. Implement `P0-5` (`M306`) and move to checkpoint `C1`.

## 13) Milestone Log (2026-02-28)
### ML-001 — Canonical Docker Runtime Wiring
`Status`: DONE

`What Was Locked`
1. Repo-level compose runtime with shared mounts and deterministic `PYTHONPATH` wiring.
2. Single entry wrapper for build/shell/pytest/backtest/regression/walkforward/sync/regime workflows.
3. Orchestrator defaults moved to repo-level compose wiring (`--compose-file`, `--project-dir`, `--user-data` where needed).

`Evidence Anchors`
- `docker-compose.grid.yml:1`
- `scripts/docker_env.sh:1`
- `freqtrade/scripts/run-user-data-sync.py:29`
- `freqtrade/scripts/run-user-regime-audit.py:23`
- `freqtrade/scripts/run-user-regression.sh:50`
- `docs/DOCKER_RUNTIME_WORKFLOW.md:1`
- `README.md:3`

### ML-002 — Walkforward Docker Reliability Hardening
`Status`: DONE

`What Was Locked`
1. Host/container path resolution for walkforward backtesting and simulation inputs.
2. Warmup-aware backtesting extension (`--backtest-warmup-candles`, auto mode from strategy lookbacks).
3. Strategy-side informative fallback + alias normalization to avoid false feature-contract failures during backtesting merges.

`Evidence Anchors`
- `freqtrade/scripts/run-user-walkforward.py:159`
- `freqtrade/scripts/run-user-walkforward.py:315`
- `freqtrade/scripts/run-user-walkforward.py:1162`
- `freqtrade/scripts/run-user-walkforward.py:1570`
- `freqtrade/user_data/strategies/GridBrainV1.py:1106`
- `freqtrade/user_data/strategies/GridBrainV1.py:6033`

`Validation Snapshot`
- Command: `./scripts/docker_env.sh walkforward --timerange 20260209-20260210 --window-days 1 --step-days 1 --min-window-days 1 --pair ETH/USDT --run-id smoke_wf_fix3 --fail-on-window-error`
- Result: `RUN_COMPLETE return_code=0`; extraction produced plans and simulation completed.

### ML-003 — Registry Lifecycle Triage Finalization (P0-2)
`Status`: DONE

`What Was Locked`
1. Final lifecycle classification for all `83` Section-7 registry-only codes.
2. No inventory drift: `83/83` parity check with no missing/extra triage entries.
3. Execution-ready ACTIVE wiring queue by checkpoint wave.

`Evidence Anchors`
- `docs/REGISTRY_LIFECYCLE_TRIAGE.md:1`
- `docs/REGISTRY_LIFECYCLE_TRIAGE.md:10`
- `docs/REGISTRY_LIFECYCLE_TRIAGE.md:35`
- `docs/REGISTRY_LIFECYCLE_TRIAGE.md:148`
- `docs/REGISTRY_LIFECYCLE_TRIAGE.md:154`

### ML-004 — Baseline Code Review Completion (P0-3)
`Status`: DONE

`What Was Locked`
1. Static baseline review completed with severity-ranked findings and explicit fix queue.
2. High-severity issues isolated before further behavior-expansion work.
3. Review closure gate defined for transition into `C0` baseline freeze.

`Evidence Anchors`
- `docs/P0_3_BASELINE_CODE_REVIEW.md:1`
- `docs/P0_3_BASELINE_CODE_REVIEW.md:21`
- `docs/P0_3_BASELINE_CODE_REVIEW.md:131`
- `docs/P0_3_BASELINE_CODE_REVIEW.md:138`

### ML-005 — C0 Baseline Freeze Completion (P0-4)
`Status`: DONE

`What Was Locked`
1. `C0` baseline run executed for regression/backtest/walkforward using canonical Docker wrapper.
2. Baseline artifacts frozen with machine-readable manifest + human-readable snapshot.
3. Known red gates captured explicitly as baseline facts (not ignored).

`Evidence Anchors`
- `docs/C0_BASELINE_SNAPSHOT.md:1`
- `docs/C0_BASELINE_SNAPSHOT.md:30`
- `docs/C0_BASELINE_SNAPSHOT.md:72`
- `freqtrade/user_data/baselines/c0_20260228T192027Z/metrics/c0_snapshot.json:1`

### ML-006 — High-Severity Fix Batch (`F-001` + `F-002`)
`Status`: DONE

`What Was Locked`
1. Executor warning emission path no longer emits non-canonical warning strings.
2. Capacity guard enforces hard-zero cap blocking and prevents multiplier-driven cap increases.
3. Targeted hardening suite validates the new behavior.

`Evidence Anchors`
- `freqtrade/user_data/scripts/grid_executor_v1.py:13`
- `freqtrade/user_data/scripts/grid_executor_v1.py:1722`
- `execution/capacity_guard.py:91`
- `execution/capacity_guard.py:117`
- `freqtrade/user_data/tests/test_executor_hardening.py:367`
- `freqtrade/user_data/tests/test_executor_hardening.py:412`

### ML-007 — C0 Red Gates Closure
`Status`: DONE

`What Was Locked`
1. Regression workflow compile gate now deterministic on `py_compile` by default.
2. Regression behavior suite adapted to current ML overlay + executor signature/idempotency contracts.
3. Full `./scripts/docker_env.sh regression` path verified green.

`Evidence Anchors`
- `docs/C0_RED_GATES_CLOSURE.md:1`
- `freqtrade/scripts/run-user-regression.sh:31`
- `freqtrade/user_data/scripts/user_regression_suite.py:484`
- `freqtrade/user_data/scripts/user_regression_suite.py:302`
- `freqtrade/user_data/baselines/gatefix_20260228T201012Z/logs/regression.log:1`

## 14) Next Step (Low-Cost) + Plan
`Next Logical Step`
- `P0-1` is complete (`docs/REMOVED_FEATURE_RELEVANCE_LEDGER.md`).
- `P0-2` is complete (`docs/REGISTRY_LIFECYCLE_TRIAGE.md`).
- `P0-3` is complete (`docs/P0_3_BASELINE_CODE_REVIEW.md`).
- `P0-4` is complete (`docs/C0_BASELINE_SNAPSHOT.md`).
- High-severity fix batch (`F-001`, `F-002`) is complete.
- `C0` red gates are closed (`docs/C0_RED_GATES_CLOSURE.md`).
- Next step: execute `P0-5` (`M306`) and move to checkpoint `C1`.

`Execution Plan`
1. Implement `M306` directional skip-one rule in simulator + executor parity paths.
2. Add/extend deterministic tests for rung-skip behavior and parity invariants.
3. Run targeted regression checks and freeze `C1` artifacts (`regression`, `backtest`, `walkforward` delta vs `C0`).
4. Publish `C1` delta summary and proceed to `P0-7` only if acceptance is green.

`Acceptance`
- `M306` behavior is implemented with simulator/executor parity evidence and passing tests.
- `C1` checkpoint artifacts include delta comparison against fixed `C0` baseline.
