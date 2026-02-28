# Removed / Replaced Feature Relevance Ledger (P0-1)

Generated: 2026-02-28
Branch: `main`
History scanned: `65` commits (up to `a9d43ee5`)

## 1) Scope and Method
- This pass focused on runtime behavior transitions in:
  - `freqtrade/user_data/strategies`
  - `freqtrade/user_data/scripts`
  - `freqtrade/scripts`
  - `core`, `planner`, `risk`, `execution`, `analytics`, `data`, `sim`
- Deletion scan result: no deleted runtime Python modules were found in those paths.
  - Evidence: `git log --diff-filter=D --name-only -- core planner risk execution analytics data sim freqtrade/user_data/strategies freqtrade/user_data/scripts freqtrade/scripts` (no `.py` hits).
- Because no runtime `.py` module deletions were found, candidates below are behavior transitions/replacements and compatibility retirements.

## 2) Decision Legend
- `RESTORE`: restore removed behavior now.
- `KEEP_REMOVED`: keep current replacement path; do not restore legacy behavior.
- `INVESTIGATE`: run targeted A/B or checkpoint test before final keep/restore decision.

## 3) Candidate Cards

### RF-001 Legacy `_bbw_nonexpanding` implementation shape retired
- Transition commit(s): `ee3bd36b`
- What changed:
  - Legacy BBW non-expanding logic shape was replaced while router/gating logic expanded.
- Current anchors:
  - `freqtrade/user_data/strategies/GridBrainV1.py:1688`
  - `freqtrade/user_data/strategies/GridBrainV1.py:6375`
  - `freqtrade/user_data/strategies/GridBrainV1.py:6421`
- Test anchors:
  - No dedicated unit pinned to this helper signature.
- Decision: `KEEP_REMOVED`
- Reason:
  - Capability is preserved through the current helper and call sites.
- Follow-up:
  - Keep only if BBW gate behavior remains stable in checkpoint deltas.

### RF-002 Early router scoring path replaced by calibrated score thresholds
- Transition commit(s): `ee3bd36b`, `1ef1c115`
- What changed:
  - Router switched to score-driven mode decisions with persistence/cooldown semantics.
- Current anchors:
  - `freqtrade/user_data/strategies/GridBrainV1.py:849`
  - `freqtrade/user_data/strategies/GridBrainV1.py:850`
  - `freqtrade/user_data/strategies/GridBrainV1.py:2440`
  - `freqtrade/user_data/strategies/GridBrainV1.py:2441`
- Test anchors:
  - Covered indirectly via regression flows; no isolated A/B guard test.
- Decision: `INVESTIGATE`
- Reason:
  - This can materially affect mode switching and PnL.
- Follow-up:
  - Run A/B in checkpoint plan: calibrated score path vs prior simpler thresholding behavior.

### RF-003 Static threshold profile replaced by `manual/research_v1` profile selection
- Transition commit(s): `6942784e`, `59fcea6b`
- What changed:
  - Added runtime profile selection and exposed active profile in outputs.
- Current anchors:
  - `freqtrade/user_data/strategies/GridBrainV1.py:894`
  - `freqtrade/user_data/strategies/GridBrainV1.py:2100`
  - `freqtrade/user_data/strategies/GridBrainV1.py:8811`
- Test anchors:
  - `freqtrade/tests/scripts/test_run_user_walkforward.py:43`
- Decision: `INVESTIGATE`
- Reason:
  - Profile choice can change production behavior significantly.
- Follow-up:
  - Lock one canonical profile after C1/C2 walkforward comparison.

### RF-004 In-code-only threshold tuning replaced by external override path support
- Transition commit(s): `59fcea6b`
- What changed:
  - Added `GRID_MODE_THRESHOLDS_PATH` runtime override and loader/cache.
- Current anchors:
  - `freqtrade/user_data/strategies/GridBrainV1.py:2107`
  - `freqtrade/user_data/strategies/GridBrainV1.py:2187`
  - `freqtrade/scripts/run-user-walkforward.py:1159`
  - `freqtrade/scripts/run-user-walkforward.py:1447`
- Test anchors:
  - `freqtrade/tests/scripts/test_run_user_walkforward_args.py:18`
  - `freqtrade/tests/scripts/test_run_user_walkforward_args.py:65`
- Decision: `INVESTIGATE`
- Reason:
  - Useful for research, but drift risk is high if override files are unmanaged.
- Follow-up:
  - Define policy: allowed override contexts, ownership, and artifact pinning.

### RF-005 Static-only cost floor path replaced by hybrid empirical+static cost floor
- Transition commit(s): `24f9bb21`, `fddd1952`
- What changed:
  - Cost floor now selects between static and empirical snapshot with stale/live-sample checks.
- Current anchors:
  - `freqtrade/user_data/strategies/GridBrainV1.py:4890`
  - `freqtrade/user_data/strategies/GridBrainV1.py:5040`
  - `freqtrade/user_data/scripts/grid_executor_v1.py:1707`
  - `analytics/execution_cost_calibrator.py:83`
- Test anchors:
  - `freqtrade/user_data/tests/test_phase3_validation.py:562`
  - `freqtrade/user_data/tests/test_phase3_validation.py:603`
  - `freqtrade/user_data/tests/test_phase3_validation.py:650`
- Decision: `KEEP_REMOVED`
- Reason:
  - Hybrid path is safer than static-only under changing microstructure.
- Follow-up:
  - Preserve stale-warning behavior (`WARN_COST_MODEL_STALE`) as non-negotiable guard.

### RF-006 No runtime cost-feedback artifact path replaced by artifact-backed calibration
- Transition commit(s): `24f9bb21`, `fddd1952`
- What changed:
  - Executor now publishes cost calibration artifacts consumed by strategy-side sampling.
- Current anchors:
  - `freqtrade/user_data/scripts/grid_executor_v1.py:1633`
  - `freqtrade/user_data/scripts/grid_executor_v1.py:1707`
  - `freqtrade/user_data/strategies/GridBrainV1.py:3524`
- Test anchors:
  - `freqtrade/user_data/tests/test_executor_hardening.py:367`
  - `freqtrade/user_data/tests/test_executor_hardening.py:400`
- Decision: `KEEP_REMOVED`
- Reason:
  - This replaced brittle static assumptions with measured execution costs.
- Follow-up:
  - Keep schema validation on artifact writes.

### RF-007 Capacity-agnostic seeding replaced by dynamic capacity guard
- Transition commit(s): `24f9bb21`
- What changed:
  - Capacity state now affects start/replenish and can cap rung count.
- Current anchors:
  - `execution/capacity_guard.py:66`
  - `freqtrade/user_data/scripts/grid_executor_v1.py:1438`
  - `freqtrade/user_data/scripts/grid_executor_v1.py:2511`
- Test anchors:
  - `freqtrade/user_data/tests/test_executor_hardening.py:308`
  - `freqtrade/user_data/tests/test_executor_hardening.py:341`
- Decision: `KEEP_REMOVED`
- Reason:
  - Prevents unsafe starts in thin conditions.
- Follow-up:
  - Keep capacity block semantics wired and test-covered.

### RF-008 Unguarded level geometry acceptance replaced by strict level validation
- Transition commit(s): `828af27e`
- What changed:
  - Plan intake now rejects invalid/increasing/duplicate level geometry.
- Current anchors:
  - `freqtrade/user_data/scripts/grid_executor_v1.py:182`
  - `freqtrade/user_data/scripts/grid_executor_v1.py:874`
- Test anchors:
  - `freqtrade/user_data/tests/test_executor_hardening.py:406`
- Decision: `KEEP_REMOVED`
- Reason:
  - Legacy permissiveness can create invalid ladders.
- Follow-up:
  - Keep `BLOCK_N_LEVELS_INVALID` as hard intake rejection path.

### RF-009 Infinite polling retry loop replaced by bounded consecutive-error cap
- Transition commit(s): `86299384`
- What changed:
  - Poll loop now aborts after a configurable consecutive error count.
- Current anchors:
  - `freqtrade/user_data/scripts/grid_executor_v1.py:2885`
  - `freqtrade/user_data/scripts/grid_executor_v1.py:2928`
- Test anchors:
  - `freqtrade/user_data/tests/test_executor_hardening.py:430`
- Decision: `KEEP_REMOVED`
- Reason:
  - Avoids silent infinite failure loops.
- Follow-up:
  - Keep max-consecutive-errors wired in runtime operators.

### RF-010 Manual temp-file JSON writes replaced by atomic fsync writer
- Transition commit(s): `2c050c13`
- What changed:
  - Replaced ad-hoc temp/replace with shared atomic writer.
- Current anchors:
  - `core/atomic_json.py:32`
  - `freqtrade/user_data/scripts/grid_executor_v1.py:138`
  - `freqtrade/user_data/strategies/GridBrainV1.py:1784`
- Test anchors:
  - `freqtrade/tests/scripts/test_section21_modules.py:214`
- Decision: `KEEP_REMOVED`
- Reason:
  - Atomic writer improves durability and consistency across planner/executor.
- Follow-up:
  - Preserve single writer utility usage.

### RF-011 Absolute default state path replaced by repo-relative default
- Transition commit(s): `ee29af96`
- What changed:
  - Executor default state path moved away from fixed container absolute path.
- Current anchors:
  - `freqtrade/user_data/scripts/grid_executor_v1.py:25`
  - `freqtrade/user_data/scripts/grid_executor_v1.py:2928`
- Test anchors:
  - `freqtrade/user_data/tests/test_executor_hardening.py:453`
- Decision: `KEEP_REMOVED`
- Reason:
  - Relative default works consistently in host and container execution.
- Follow-up:
  - Keep compatibility with explicit `--state-out` overrides.

### RF-012 Schema-light intake replaced by strict JSON-schema validation
- Transition commit(s): `1704ba75`
- What changed:
  - Strategy/executor now validate `grid_plan.schema.json` before accepting payloads.
- Current anchors:
  - `core/schema_validation.py:38`
  - `freqtrade/user_data/scripts/grid_executor_v1.py:850`
  - `freqtrade/user_data/strategies/GridBrainV1.py:2841`
- Test anchors:
  - `freqtrade/tests/scripts/test_schema_contracts.py:47`
  - `freqtrade/tests/scripts/test_schema_contracts.py:51`
  - `freqtrade/tests/scripts/test_grid_executor_handoff.py:197`
- Decision: `KEEP_REMOVED`
- Reason:
  - Prevents malformed plan payloads from entering runtime.
- Follow-up:
  - Keep schema and code contracts synchronized.

### RF-013 Weak intake idempotency replaced by signature/sequence contract
- Transition commit(s): `0ae1cc13`
- What changed:
  - Added `plan_id`, `decision_seq`, `plan_hash`, `supersedes_plan_id`, expiry checks.
- Current anchors:
  - `core/plan_signature.py:169`
  - `core/plan_signature.py:184`
  - `freqtrade/user_data/scripts/grid_executor_v1.py:855`
  - `freqtrade/user_data/scripts/grid_executor_v1.py:918`
  - `freqtrade/user_data/scripts/grid_executor_v1.py:944`
  - `freqtrade/user_data/strategies/GridBrainV1.py:9595`
- Test anchors:
  - `freqtrade/tests/scripts/test_plan_signature_contract.py:38`
  - `freqtrade/tests/scripts/test_grid_executor_handoff.py:132`
  - `freqtrade/tests/scripts/test_grid_executor_handoff.py:156`
- Decision: `KEEP_REMOVED`
- Reason:
  - Legacy behavior lacked robust duplicate/stale protection.
- Follow-up:
  - Treat signature fields as immutable contract.

### RF-014 Separate `REBUILD` runtime branch retired into `START` compatibility normalization
- Transition commit(s): `0ae1cc13`
- What changed:
  - Runtime normalizes `REBUILD` action into `START` semantics for compatibility.
- Current anchors:
  - `freqtrade/user_data/scripts/grid_executor_v1.py:2393`
- Test anchors:
  - Covered indirectly in handoff/executor flow tests.
- Decision: `KEEP_REMOVED`
- Reason:
  - Reduces branching complexity while preserving old input compatibility.
- Follow-up:
  - Keep compatibility mapping unless contract versioning changes.

### RF-015 Raw START/STOP churn replaced by effective-action suppression signatures
- Transition commit(s): `59fcea6b`
- What changed:
  - Duplicate START/STOP intents can be suppressed to HOLD when semantically redundant.
- Current anchors:
  - `freqtrade/user_data/scripts/grid_executor_v1.py:261`
  - `freqtrade/user_data/scripts/grid_executor_v1.py:2499`
  - `freqtrade/user_data/scripts/grid_executor_v1.py:2507`
  - `freqtrade/user_data/scripts/grid_simulator_v1.py:1607`
  - `freqtrade/user_data/scripts/grid_simulator_v1.py:1615`
- Test anchors:
  - Indirect coverage through executor hardening behavior tests.
- Decision: `KEEP_REMOVED`
- Reason:
  - Reduces unnecessary churn and duplicate side effects.
- Follow-up:
  - Keep suppression reason telemetry in runtime state.

### RF-016 Fill replenishment without per-level cooldown retired by no-repeat LSI guard
- Transition commit(s): `b08993b4`
- What changed:
  - Added cooldown guard that prevents immediate repeated fills on same side/level key.
- Current anchors:
  - `freqtrade/user_data/scripts/grid_executor_v1.py:396`
  - `freqtrade/user_data/scripts/grid_executor_v1.py:2407`
  - `freqtrade/user_data/scripts/grid_simulator_v1.py:339`
  - `freqtrade/user_data/scripts/grid_simulator_v1.py:2246`
  - `freqtrade/user_data/strategies/GridBrainV1.py:977`
- Test anchors:
  - `freqtrade/user_data/tests/test_phase3_validation.py:691`
  - `freqtrade/user_data/tests/test_phase3_validation.py:704`
- Decision: `KEEP_REMOVED`
- Reason:
  - Prevents pathological refill loops and unrealistic replay fills.
- Follow-up:
  - Keep guard defaults aligned between planner, simulator, executor.

### RF-017 Walkforward path assumptions retired by host/container path resolver
- Transition commit(s): `a9d43ee5`
- What changed:
  - Walkforward now resolves local paths to mounted container paths deterministically.
- Current anchors:
  - `freqtrade/scripts/run-user-walkforward.py:159`
  - `freqtrade/scripts/run-user-walkforward.py:1250`
  - `freqtrade/scripts/run-user-walkforward.py:1251`
  - `freqtrade/scripts/run-user-walkforward.py:1252`
- Test anchors:
  - No dedicated unit for resolver yet.
- Decision: `KEEP_REMOVED`
- Reason:
  - Fixes path mismatch failures between host and container runtime.
- Follow-up:
  - Add resolver-specific argument tests if failures recur.

### RF-018 Fixed/implicit warmup logic retired by auto lookback-based warmup
- Transition commit(s): `a9d43ee5`
- What changed:
  - Walkforward can auto-infer warmup from strategy lookbacks (`-1` mode).
- Current anchors:
  - `freqtrade/scripts/run-user-walkforward.py:1266`
  - `freqtrade/scripts/run-user-walkforward.py:1274`
  - `freqtrade/scripts/run-user-walkforward.py:1289`
  - `docs/DOCKER_RUNTIME_WORKFLOW.md:59`
- Test anchors:
  - No dedicated warmup estimator unit yet.
- Decision: `KEEP_REMOVED`
- Reason:
  - Reduces under-warmup artifacts in backtest windows.
- Follow-up:
  - Add targeted unit coverage for estimator parsing edge cases.

### RF-019 Informative-pair DP hard dependency retired by config whitelist fallback
- Transition commit(s): `a9d43ee5`
- What changed:
  - Strategy now falls back to `config.exchange.pair_whitelist` when DP whitelist is unavailable.
- Current anchors:
  - `freqtrade/user_data/strategies/GridBrainV1.py:1106`
- Test anchors:
  - No dedicated fallback unit yet.
- Decision: `KEEP_REMOVED`
- Reason:
  - Improves runtime resilience in backtest/compose contexts.
- Follow-up:
  - Add test for missing DP + config-based fallback behavior.

### RF-020 Informative column naming brittleness retired by alias normalization
- Transition commit(s): `a9d43ee5`
- What changed:
  - Canonical informative names are normalized from timeframe-suffixed aliases.
- Current anchors:
  - `freqtrade/user_data/strategies/GridBrainV1.py:6033`
- Test anchors:
  - No dedicated alias normalization unit yet.
- Decision: `KEEP_REMOVED`
- Reason:
  - Prevents false feature-contract failures due to column suffix variants.
- Follow-up:
  - Add test coverage for alias-only input frames.

### RF-021 Multi-file helper plan stack retired by single consolidated master plan
- Transition commit(s): `51577a2e`
- What changed:
  - Transitional helper docs were removed; consolidated plan became canonical execution document.
- Current anchors:
  - `docs/CONSOLIDATED_MASTER_PLAN.md:1`
  - `docs/CONSOLIDATED_MASTER_PLAN.md:9`
- Test anchors:
  - N/A (documentation governance transition).
- Decision: `KEEP_REMOVED`
- Reason:
  - Reduces duplicate/planning drift between helper files.
- Follow-up:
  - Keep all backlog updates in the consolidated plan only.

### RF-022 Local-venv-first workflow retired by Docker-first canonical environment
- Transition commit(s): `a9d43ee5`
- What changed:
  - Canonical run path moved to `docker-compose.grid.yml` + `scripts/docker_env.sh`.
- Current anchors:
  - `README.md:3`
  - `docker-compose.grid.yml:1`
  - `scripts/docker_env.sh:1`
  - `freqtrade/scripts/run-user-regression.sh:6`
- Test anchors:
  - Operational workflow; not unit-tested as a single path.
- Decision: `KEEP_REMOVED`
- Reason:
  - Ensures environment parity across machines and sessions.
- Follow-up:
  - Keep local venv as fallback only.

### RF-023 Historical reclaim baseline convention (8h intent) diverged to runtime 4h
- Transition commit(s): historical intent tracked in replacement ledger; runtime state present in code now
- What changed:
  - Runtime default is `reclaim_hours = 4.0`; earlier planning convention referenced 8h.
- Current anchors:
  - `freqtrade/user_data/strategies/GridBrainV1.py:790`
  - `docs/CONSOLIDATED_MASTER_PLAN.md:3250`
  - `docs/CONSOLIDATED_MASTER_PLAN.md:3252`
- Test anchors:
  - No explicit 4h-vs-8h decision test yet.
- Decision: `INVESTIGATE`
- Reason:
  - This directly affects rebuild cadence, risk, and profit profile.
- Follow-up:
  - Run explicit 4h vs 8h checkpoint A/B and freeze one canonical value.

### RF-024 Mixed-inventory planning intent retired by quote-only runtime mode
- Transition commit(s): tracked through replacement ledger and consolidated history inputs
- What changed:
  - Runtime policy is quote-only (`inventory_mode = "quote_only"`).
- Current anchors:
  - `freqtrade/user_data/strategies/GridBrainV1.py:945`
  - `freqtrade/user_data/strategies/GridBrainV1.py:9354`
  - `docs/CONSOLIDATED_MASTER_PLAN.md:3199`
- Test anchors:
  - No active mixed-inventory runtime tests.
- Decision: `INVESTIGATE`
- Reason:
  - Mixed mode could be useful in specific regimes but adds execution complexity.
- Follow-up:
  - Keep quote-only baseline; evaluate mixed mode only as separate variant.

### RF-025 Trust-first data ingestion retired by explicit data-quality quarantine gates
- Transition commit(s): `97de5e35`
- What changed:
  - Data quality is formally assessed and can trigger block/pause/quarantine behavior.
- Current anchors:
  - `data/data_quality_assessor.py:12`
  - `freqtrade/user_data/strategies/GridBrainV1.py:1342`
  - `freqtrade/user_data/strategies/GridBrainV1.py:6051`
  - `core/enums.py:220`
  - `core/enums.py:221`
  - `core/enums.py:266`
- Test anchors:
  - `freqtrade/user_data/tests/test_phase3_validation.py` (data quality and guards coverage set).
- Decision: `KEEP_REMOVED`
- Reason:
  - Legacy trust-first behavior is unsafe for live operation.
- Follow-up:
  - Keep data-quality reasons wired and checkpoint-tested.

### RF-026 Direct legacy strategy class dependency retired by explicit compatibility alias
- Transition commit(s): `97de5e35`
- What changed:
  - Runtime core class split uses a compatibility alias to preserve imports.
- Current anchors:
  - `freqtrade/user_data/strategies/GridBrainV1.py:9633`
- Test anchors:
  - Indirect through all strategy import/execution tests.
- Decision: `KEEP_REMOVED`
- Reason:
  - Alias preserves compatibility while allowing internal class organization.
- Follow-up:
  - Keep alias until all external import references are confirmed migrated.

## 4) Decision Summary
- `RESTORE`: 0
- `KEEP_REMOVED`: 20
- `INVESTIGATE`: 6

## 5) Priority Follow-up Queue (from INVESTIGATE set)
1. `RF-023` reclaim baseline decision (4h vs 8h), with checkpoint A/B and canonical lock.
2. `RF-002` router scoring calibration A/B vs simpler thresholding.
3. `RF-003` profile policy lock (`manual` vs `research_v1`) based on walkforward evidence.
4. `RF-004` external threshold override governance (allowed contexts + ownership).
5. `RF-024` mixed-inventory variant feasibility (separate branch, not baseline).
6. Add missing targeted tests for `RF-017`/`RF-018`/`RF-019`/`RF-020` to harden these replacements.

## 6) P0-1 Acceptance Check
- Full history archaeology pass completed.
- Runtime module deletion check completed (none found).
- Candidate ledger exceeds top-20 requirement with commit and code anchors.
- Classification complete for every listed candidate.
