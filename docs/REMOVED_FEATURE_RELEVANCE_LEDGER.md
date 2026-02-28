# Removed Feature Relevance Ledger (P0-1)

Generated: 2026-02-28
Scope: full git history scan on `main` up to `51577a2e`.

## 1) Method
- Reviewed full commit history (`57` commits).
- Checked for deleted source modules under runtime paths:
  - `freqtrade/user_data/strategies`
  - `freqtrade/user_data/scripts`
  - `planner`, `core`, `risk`, `execution`, `analytics`, `data`, `sim`, `freqtrade/scripts`
- Reviewed high-change commits and replacement deltas in strategy/executor/simulator.

## 2) Global Finding
- No runtime source modules were deleted from those paths in git history.
- Deleted files found were helper/docs/cache artifacts, not core runtime strategy modules.

## 3) Decision Legend
- `RESTORE`: bring back removed behavior now.
- `KEEP_REMOVED`: keep current replacement; do not restore old behavior.
- `INVESTIGATE`: run targeted A/B or checkpoint experiment before deciding.

## 4) Relevance Entries

### RF-001 Legacy BBW non-expanding helper implementation
- Evidence:
  - Removal/replacement commit: `ee3bd36b` (removed old `_bbw_nonexpanding` implementation shape and thresholds).
  - Current replacement present: `freqtrade/user_data/strategies/GridBrainV1.py:1679`, `freqtrade/user_data/strategies/GridBrainV1.py:6351`.
- Current state:
  - Behavior still exists via generalized helper and broader reuse.
- Decision: `KEEP_REMOVED`
- Rationale:
  - Functional capability is preserved with a more reusable implementation.
- Rollback note:
  - If regression appears, restore old helper logic from `ee3bd36b^` into isolated experiment branch only.

### RF-002 Router scoring transition (early scoring -> calibrated score thresholds/artifacts)
- Evidence:
  - Transition commit: `1ef1c115` (`regime_router_score_enter/exit/persistence` artifact path introduced).
  - Current runtime anchors: `freqtrade/user_data/strategies/GridBrainV1.py:2422`, `freqtrade/user_data/strategies/GridBrainV1.py:2641`.
- Current state:
  - Router remains active, but scoring path evolved during development.
- Decision: `INVESTIGATE`
- Rationale:
  - Profit impact is plausible; should be validated empirically instead of assumed.
- Investigation task:
  - Add a controlled ablation comparing current scoring vs prior-style thresholding on same walkforward windows.

### RF-003 Static-only cost floor path
- Evidence:
  - Replacement commits: `24f9bb21`, `fddd1952`.
  - Current hybrid path anchors: `analytics/execution_cost_calibrator.py:9`, `freqtrade/user_data/strategies/GridBrainV1.py:6802`, `freqtrade/user_data/scripts/grid_executor_v1.py:1579`.
- Current state:
  - Static+empirical floor selection with stale/sample guards is in place.
- Decision: `KEEP_REMOVED`
- Rationale:
  - Hybrid model is structurally safer than static-only assumptions and already integrated into tests/checks.
- Rollback note:
  - Keep fallback to static floor; no full restore of static-only path recommended.

### RF-004 Reclaim baseline convention (8h intent vs 4h runtime)
- Evidence:
  - Current runtime default: `freqtrade/user_data/strategies/GridBrainV1.py:790` (`reclaim_hours = 4.0`).
  - Convention conflict documented in consolidated plan (`M402` partial).
- Current state:
  - Not a code-removal event found in history; this is a policy divergence from legacy intent.
- Decision: `INVESTIGATE`
- Rationale:
  - Directly impacts STOP/REBUILD cadence and therefore PnL and risk profile.
- Investigation task:
  - Run explicit 4h vs 8h A/B in checkpoint cycle (`C2` gate), then lock one canonical policy.

### RF-005 Mixed-inventory planning concept
- Evidence:
  - Current runtime mode is quote-only: `freqtrade/user_data/strategies/GridBrainV1.py:945`, `freqtrade/user_data/strategies/GridBrainV1.py:9329`.
  - Legacy mixed-inventory intent referenced in old planning lineage (not present as active runtime implementation).
- Current state:
  - Mixed inventory is not an active runtime mode.
- Decision: `INVESTIGATE`
- Rationale:
  - Could be useful for specific market regimes, but adds complexity/risk.
- Investigation task:
  - Evaluate as optional strategy variant only after P0 gaps close; do not reintroduce into baseline now.

### RF-006 Removed helper planning docs (repo cleanup)
- Evidence:
  - Removal commit: `51577a2e`.
  - Removed docs: `docs/CODE_IMPLEMENTED_FEATURE_PLAN.md`, `docs/CODE_IMPLEMENTATION_SNAPSHOT.md`, `docs/GRID_MASTER_PLAN.md`, `docs/CONSOLIDATED_MASTER_PLAN_CODE_FIRST.md`, `docs/codex_resume_workflow.md`.
- Current state:
  - Consolidated plan is now the single source document.
- Decision: `KEEP_REMOVED`
- Rationale:
  - Helpers were transitional and superseded by the consolidated execution plan.
- Rollback note:
  - If needed, restore by reverting commit `51577a2e` selectively.

## 5) Summary for P0 Execution
- `RESTORE` now: none.
- `KEEP_REMOVED`: `RF-001`, `RF-003`, `RF-006`.
- `INVESTIGATE`: `RF-002`, `RF-004`, `RF-005`.

## 6) Next Actions
1. Start `P0-2` registry lifecycle triage (`ACTIVE`/`RETIRED`/`PARKED_FUTURE`).
2. Queue investigation experiments for `RF-002`, `RF-004`, `RF-005` into checkpoint plan (`C1/C2/C3`).
3. Keep rollback-ready practice: one change per commit, tag before retirement checkpoints.
