# P0-3 Baseline Code Review (2026-02-28)

## 1) Scope And Method

This is a static, code-first baseline review focused on runtime correctness, regression risk, and operational safety before further behavior changes.

Reviewed modules:
- `freqtrade/user_data/strategies/GridBrainV1.py`
- `freqtrade/user_data/scripts/grid_executor_v1.py`
- `execution/capacity_guard.py`
- `freqtrade/scripts/run-user-walkforward.py`
- `core/enums.py`
- `core/atomic_json.py`
- `core/plan_signature.py`

Validation pass:
- Syntax integrity check passed (`python3 -m py_compile`) across core runtime modules and primary user scripts.

No direct critical security issue (credential leak / code-exec vector) was identified in this pass. Findings below are logic and robustness issues with production impact potential.

## 2) Findings (Severity-Ordered)

### F-001 (HIGH) Non-Canonical Warning Code Emitted By Executor

What is happening:
- Executor emits `WARN_COST_ARTIFACT_SCHEMA_INVALID`, but this code does not exist in canonical `WarningCode`.
- Runtime warning append path accepts arbitrary strings, so invalid/unregistered warning codes can enter logs and telemetry.

Why this matters:
- Breaks canonical registry discipline and can silently bypass wiring/coverage expectations in Section-7 lifecycle tracking.
- Makes warning analytics and downstream consumers less reliable.

Evidence:
- `core/enums.py:305`
- `core/enums.py:313`
- `freqtrade/user_data/scripts/grid_executor_v1.py:771`
- `freqtrade/user_data/scripts/grid_executor_v1.py:1721`

Fix queue:
1. Add a canonical warning enum member for cost-artifact schema invalidity, or map emitter to an existing canonical warning code with equivalent meaning.
2. Replace raw warning literals in executor with enum-backed values.
3. Add a unit test asserting every executor warning emission is present in canonical warning registry.

Acceptance criteria:
- No executor warning code is emitted unless it is in `WarningCode`.
- Test fails if a non-canonical warning string is introduced.

### F-002 (HIGH) Capacity Guard Can Report `capacity_ok=True` When Base Cap Is Zero

What is happening:
- `base_cap` can be `0` (`max_orders_per_side=0`, `n_levels=0`).
- On spread/depth pressure, logic applies `applied_cap = max(min_cap, reduced)`, which can force `applied_cap=1`.
- Final `capacity_ok` check uses `applied_cap >= min_cap`, so state can become `capacity_ok=True` despite zero base capacity.

Why this matters:
- Violates intuitive hard-cap semantics and can enable order activity when configuration implies no active rungs.
- Creates policy ambiguity between config hard limits and runtime adaptation.

Evidence:
- `execution/capacity_guard.py:86`
- `execution/capacity_guard.py:99`
- `execution/capacity_guard.py:105`
- `execution/capacity_guard.py:125`
- Repro (local one-shot run): output `base=0 applied=1 capacity_ok=True`.

Fix queue:
1. Treat `base_cap <= 0` as hard-zero: return `capacity_ok=False` and `applied_rung_cap=0`.
2. Ensure spread/depth reductions never increase effective cap above base hard limits.
3. Add deterministic tests for hard-zero and non-zero cap regimes.

Acceptance criteria:
- With base cap `0`, output is always `capacity_ok=False` and `applied_rung_cap=0`.
- Runtime multipliers only reduce or keep cap, never elevate a zero base cap.

### F-003 (MEDIUM) Inconsistent Symbol Keying In Execution-Cost Artifact State

What is happening:
- Artifact path cache key uses normalized filesystem-safe pair key (`pair_fs`).
- Archive dedupe map uses raw `symbol` string.

Why this matters:
- If symbol representations vary (aliases/format differences), archive dedupe and path caching can drift, causing duplicate archives or stale sample-write tracking.
- Increases replay/debug noise and artifact lifecycle ambiguity.

Evidence:
- `freqtrade/user_data/scripts/grid_executor_v1.py:347`
- `freqtrade/user_data/scripts/grid_executor_v1.py:1516`
- `freqtrade/user_data/scripts/grid_executor_v1.py:1530`
- `freqtrade/user_data/scripts/grid_executor_v1.py:1735`
- `freqtrade/user_data/scripts/grid_executor_v1.py:1742`

Fix queue:
1. Standardize keying through one helper (recommended: normalized key via `_pair_fs` for all per-pair artifact maps).
2. Migrate existing in-memory map accesses to the chosen key shape in one patch.
3. Add test covering symbol format variants for archive-write dedupe behavior.

Acceptance criteria:
- Artifact path cache and sample-write cache use the same key normalization.
- One logical pair cannot produce duplicated archive streams due only to symbol-string variation.

### F-004 (MEDIUM) Strategy Runtime State Uses Class-Level Mutable Maps

What is happening:
- Large runtime stores are declared as class attributes (mutable dict/deque maps).
- `__init__` initializes only a subset of runtime state maps; many others remain class-level mutable stores.

Why this matters:
- Risks state bleed across strategy instances in shared processes (tests, reloader scenarios, parallel strategy objects).
- Harder to reason about test isolation and deterministic startup state.

Evidence:
- `freqtrade/user_data/strategies/GridBrainV1.py:1044`
- `freqtrade/user_data/strategies/GridBrainV1.py:1103`
- `freqtrade/user_data/strategies/GridBrainV1.py:491`
- `freqtrade/user_data/strategies/GridBrainV1.py:9609`

Fix queue:
1. Move mutable runtime stores to per-instance initialization (`__init__` or dedicated initializer called from `__init__`).
2. Keep only constants and immutable defaults at class scope.
3. Add an isolation test: two strategy instances must not share per-pair runtime state.

Acceptance criteria:
- No mutable runtime state map is shared between strategy instances.
- Isolation test proves independent state across multiple instances.

## 3) Baseline Fix Queue (Execution Order)

1. `F-001` canonical warning code enforcement (high impact, low implementation cost). `Status`: DONE (2026-02-28)
2. `F-002` capacity guard hard-zero semantics (behavior-critical correctness). `Status`: DONE (2026-02-28)
3. `F-003` execution-cost key normalization unification (artifact consistency). `Status`: TODO
4. `F-004` per-instance state isolation refactor (robustness + test determinism). `Status`: TODO

## 4) Resolution Update (2026-02-28)

### F-001 Resolution

- Change: executor schema-invalid warning path now emits canonical warning code (`WARN_FEATURE_FALLBACK_USED`) instead of raw non-canonical string.
- Evidence:
1. `freqtrade/user_data/scripts/grid_executor_v1.py:13`
2. `freqtrade/user_data/scripts/grid_executor_v1.py:1722`
3. `freqtrade/user_data/tests/test_executor_hardening.py:406`
- Validation:
1. `freqtrade/user_data/tests/test_executor_hardening.py:367`
2. `./scripts/docker_env.sh pytest -q freqtrade/user_data/tests/test_executor_hardening.py` -> `17 passed`

### F-002 Resolution

- Change: capacity guard now enforces hard-zero base cap behavior (`capacity_ok=False`, `applied_rung_cap=0`) and clamps multiplier logic to never increase rung cap.
- Evidence:
1. `execution/capacity_guard.py:91`
2. `execution/capacity_guard.py:101`
3. `execution/capacity_guard.py:117`
4. `execution/capacity_guard.py:144`
- Validation:
1. `freqtrade/user_data/tests/test_executor_hardening.py:412`
2. `freqtrade/user_data/tests/test_executor_hardening.py:439`
3. `./scripts/docker_env.sh pytest -q freqtrade/user_data/tests/test_executor_hardening.py` -> `17 passed`

## 5) Closure Gate For P0-3

P0-3 is considered closed when:
1. Findings are tracked in the implementation queue with owners/checkpoints.
2. High-severity findings (`F-001`, `F-002`) are queued before behavior-expansion work.
3. Fix acceptance tests are defined and linked before `C0` freeze comparison runs.
