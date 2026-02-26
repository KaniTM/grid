# GRID MASTER PLAN
## Dual-Mode Spot Grid Planner System (Brain + Simulator + Executor + Later ML Overlay)
### Integrated Master Plan (Deterministic-first, Codex-friendly)

**Version:** v2.1 (Integrated)  
**Status:** Master planning spec (source of truth)  
**Scope:** Spot grid planner/executor architecture with deterministic core, simulation, execution safety, anti-churn controls, and future ML confidence overlay.

---

# 0) How to Use This File (for Codex + Humans)

This file is the **single source of truth** for the grid-bot architecture and module roadmap.

Use it in 3 ways:

1. **Implementation guide**  
   Build modules in the sequence defined in **Section 20**.

2. **Audit checklist**  
   For any repo state, compare code against **Section 18 (Module Registry)** and mark each module:
   - `UNKNOWN`
   - `PLANNED`
   - `PARTIAL`
   - `DONE`
   - `DISABLED_BY_DEFAULT`

3. **Refactor safety guard**  
   Before changing logic, validate against:
   - **Global invariants** (Section 3)
   - **Atomic/idempotent handoff contract** (Section 14)
   - **Replan/materiality rules** (Section 7)
   - **Testing + tuning protocol** (Sections 16–17)

---

# 1) Purpose and Scope

## 1.1 Objective

Build a **production-like spot crypto grid planning system** that:

- detects favorable non-trending conditions,
- defines a deterministic box/range and grid ladder,
- outputs a **plan** (`START`, `HOLD`, `STOP`, `REBUILD`),
- validates behavior via replay simulation,
- runs via a separate executor (paper first, live later),
- and only later adds ML as a **confidence overlay** (not the primary decision engine).

## 1.2 Core Design Rule

**Deterministic planner first, ML later.**  
If ML is disabled, the system must still behave sensibly and safely.

## 1.3 Current Scope

- Spot-only (no futures/perps execution assumptions)
- One active grid per pair
- Default inventory mode: **quote-only**
- Multi-exchange support via config/CCXT (executor layer)
- Primary pair/timeframe starting point:
  - `ETH/USDT`
  - Base TF: `15m`
  - Informative TFs: `1h`, `4h`
  - Optional higher periods: `1D`, `1W`, `1M`
- Freqtrade/FreqAI can be used as **Brain/feature framework**, not as the live order engine

## 1.4 Out of Scope (for now)

- Cross-exchange arbitrage
- Full portfolio optimizer / capital allocator across many bots
- Tick-by-tick event-driven HFT engine
- ML-driven autonomous plan generation
- Leveraged/futures liquidation-aware logic

---

# 2) System Architecture (Brain / Simulator / Executor / Overlay)

## 2.1 Brain / Planner (`GridBrainV1`)

### Responsibility
Compute and publish the **current desired grid plan** for a pair.

### Inputs
- OHLCV data (15m + informative TFs)
- Deterministic features
- Optional structure/volume modules (VP/FVG/OB/etc.)
- Runtime state (cooldown, reclaim, health)
- Optional empirical cost calibration snapshot
- Optional ML confidence (later)

### Output
`grid_plan.latest.json` (atomic write, idempotent plan signature fields included)

### Non-responsibilities
- No live order placement
- No exchange-side reconciliation
- No direct position/order management (executor owns that)

## 2.2 Simulator / Replay Harness

### Responsibility
Replay historical candles and simulate:
- Brain decisions
- fills
- STOP/REBUILD logic
- cost assumptions
- replan/materiality behavior
- stress/chaos perturbations (later)

### Output Artifacts
- summary JSON
- fills CSV/parquet
- equity curve
- decision logs
- event logs
- reason-code distributions
- churn/false-start stats
- deterministic vs chaos comparison

## 2.3 Executor (Paper first, Live later)

### Responsibility
Read Brain plan and maintain a ladder consistent with the **latest accepted plan**.

### Features (planned)
- maker-first placement
- post-only retry/backoff
- tick-aware rounding
- diff-based reconcile (later)
- plan idempotency / stale plan rejection
- execution safety hooks (spread/depth/jump)

### Modes
- `paper`
- `live` (later, after safety hardening)
- `replay-paper` (paper engine consuming historical replay + chaos profile)

## 2.4 ML / FreqAI Overlay (Later)

### Responsibility
Provide soft signals / confidence scores (not primary action decisions):
- `p_range_continuation`
- `p_breakout_risk`
- START/REBUILD confidence modifier
- advisory mode scoring

### Guardrail
Planner must remain valid and deterministic without ML.

## 2.5 Canonical Reason/Event Codes

Use only canonical reason/event codes from `docs/DECISION_REASON_CODES.md` (and `core/enums.py`). If new logic adds a code, update both.

# 3) Global Invariants (Must Never Be Violated)

## 3.1 Determinism / No-Repaint

- No feature used in decisions may depend on future candles.
- Cached levels (breakout/FVG/OB/POC/etc.) must be **bar-confirmed** and stable.
- Range/box + VP outputs must be reproducible for same inputs.

## 3.2 Brain / Simulator Consistency

The following must behave the same in Brain and Simulator:
- START gating
- STOP triggers
- REBUILD/reclaim conditions
- cost-aware step checks
- TP/SL selection (or at least plan-level outputs)
- replan/materiality classification
- cooldown/min-runtime logic

## 3.3 Conservative Priority Rule

When modules disagree, **most conservative action wins**:
1. `STOP` / hard veto
2. `PAUSE` / block START
3. `HOLD`
4. `SOFT_ADJUST`
5. `START` / `REBUILD`

Also:
- data quarantine > normal gates
- meta drift hard > all non-emergency runtime rails
- unsafe execution conditions > order placement

## 3.4 Configuration-Driven Thresholds

Thresholds/toggles live in config (JSON/YAML), not hidden in code.

## 3.5 Atomic + Idempotent Brain→Executor Handoff

- Brain writes atomically (tmp + fsync + rename)
- Executor ignores:
  - duplicate `plan_id`
  - stale `decision_seq`
  - invalid `plan_hash`
  - schema-invalid plans

## 3.6 Materiality Before Churn

New plan candidate must not imply executor action unless:
- epoch boundary reached, **or**
- material delta exceeded, **or**
- hard safety event present

## 3.7 Observability First

Every decision must be explainable using:
- reason codes
- feature snapshot
- plan diff snapshot
- source module / event

---

# 4) Core Data Model

## 4.1 Timeframes

### Required
- 15m (base build/execution planner timeframe)
- 1h (range/quietness/regime helpers)
- 4h (trend/ADX/regime)

### Optional / Later
- 1D / 1W / 1M (MRVD, higher-TF POCs, basis/pivot modules)

## 4.2 Data Quality Requirements

Checks required before decisions:
- missing candles
- duplicate timestamps
- non-monotonic timestamps
- stale data age
- suspicious zero-volume streaks
- informative TF misalignment

---

# 5) Planner Health State (Data Quality Quarantine Control Plane)

## 5.1 Purpose

Upgrade data integrity checks into a **first-class planner state**.

## 5.2 State Enum

- `ok`
- `degraded`
- `quarantine`

## 5.3 Behavior

- `ok` → normal operation
- `degraded` → allow `HOLD/STOP`, block `START/REBUILD`
- `quarantine` → only `STOP`; no new placements

## 5.4 Example Triggers

- large gap in 15m candles
- misaligned 1h/4h merge
- duplicate timestamp burst
- suspicious zero-volume streak
- stale feed / delayed candles

## 5.5 Reason Codes (minimum)
- `BLOCK_DATA_GAP`
- `BLOCK_DATA_MISALIGN`
- `BLOCK_ZERO_VOL_ANOMALY`
- `PAUSE_DATA_QUARANTINE`

---

# 6) Planner Decision Loop (High-Level Flow)

At each 15m decision tick:

1. Load/merge data (15m + informative TFs)
2. Run data quality assessor → `planner_health_state`
3. Compute core features
4. Compute optional structure/volume features (enabled modules only)
5. Build/adapt config view (volatility policy adapter)
6. Evaluate Phase-2 gates (regime/build eligibility)
7. Build/validate range box (Phase-3)
8. Compute grid sizing + cost floor + targets (Phase-4)
9. Evaluate Phase-5 runtime controls (STOP/REBUILD/cooldown/reclaim)
10. Compute start stability score
11. Meta drift guard update/action
12. Build new plan candidate
13. Run replan/materiality policy vs previous plan
14. Publish atomic plan JSON (or no-op/soft adjust)
15. Log decision + plan diff + events

---

# 7) Replan Policy + Materiality Layer (Anti-Churn Governor)

## 7.1 Purpose

Prevent:
- tiny signal changes causing constant plan rewrites
- executor cancel/replace churn
- live-vs-backtest mismatch caused by overreactive planning

## 7.2 Replan Decisions

- `NOOP`
- `SOFT_ADJUST`
- `MATERIAL_REBUILD`
- `HARD_STOP`

## 7.3 Trigger Conditions (replan allowed on)

1. Epoch boundary (e.g., every 2 bars on 15m)
2. Material change exceeds thresholds
3. Hard safety event present

## 7.4 Suggested Materiality Metrics

- box mid shift (fraction of step)
- box width change %
- step size change %
- N levels changed (bool)
- TP/SL shift (fraction of step)
- mode/action class changed
- blocker set changed materially
- safety event override present

## 7.5 Example Config

- `replan_epoch_bars = 2`
- `material_box_mid_shift_max_step_frac = 0.5`
- `material_box_width_change_pct = 5.0`
- `material_tp_shift_max_step_frac = 0.75`
- `material_sl_shift_max_step_frac = 0.75`
- `soft_adjust_allowed_fields = ["tp", "sl", "runtime_hints", "confidence"]`

## 7.6 Reason Codes
- `REPLAN_NOOP_MINOR_DELTA`
- `REPLAN_SOFT_ADJUST_ONLY`
- `REPLAN_MATERIAL_BOX_CHANGE`
- `REPLAN_HARD_STOP_OVERRIDE`

---

# 8) Global Start Stability Score (k-of-n Persistence)

## 8.1 Purpose

Avoid STARTs that pass only for one marginal candle.

## 8.2 Design

Compute `start_stability_score` (0–100) from:
- core gate pass count/quality
- persistence over recent bars
- box quality
- POC acceptance state
- no fresh breakout / no drift penalty
- health state penalty
- optional confidence overlay bonus (later, bounded)

Require:
- `score >= start_threshold`
- AND `k of last n` bars above `lower_threshold`

## 8.3 Suggested Config
- `start_stability_enabled = true`
- `start_stability_threshold = 70`
- `start_stability_lower_threshold = 60`
- `start_stability_k = 2`
- `start_stability_n = 3`

## 8.4 Reason Codes
- `BLOCK_START_STABILITY_LOW`
- `BLOCK_START_PERSISTENCE_FAIL`

---

# 9) Volatility Policy Adapter (Deterministic Threshold Adaptation)

## 9.1 Purpose

Provide bounded adaptation without ML, based on volatility regime buckets.

## 9.2 Inputs
- `atr_pct_15m`, `atr_pct_1h`
- `bbwp_s/m/l`
- squeeze state
- optional HVP state

## 9.3 Volatility Buckets
- `calm`
- `normal`
- `elevated`
- `unstable`

## 9.4 Adapted Fields (runtime view only)
- box width target band
- `n_min`, `n_max`
- min step buffer bps
- cooldown minutes
- min runtime minutes (slight)
- build strictness flags (optional)

## 9.5 Rules
- deterministic mapping only
- bounded ranges only
- log both base + adapted thresholds
- do not mutate persisted configs

---

# 10) Meta Drift Guard (Change-Point / Regime Drift Kill-Switch)

## 10.1 Purpose

Catch sudden or gradual distribution changes not fully captured by standard gates.

## 10.2 Candidate Streams (normalized)
- `atr_pct_15m`
- `rvol_15m`
- `spread_pct` (executor/live or simulated approximation)
- `box_pos_abs_delta`
- `orderbook_imbalance` (later)
- `depth_thinning_score` (later)

## 10.3 Detection Approach
- Page-Hinkley / CUSUM-style online drift detection (lightweight)
- smoothed channels + min sample requirement

## 10.4 Output
- `drift_detected`
- `drift_channels`
- `severity = soft|hard`
- `recommended_action = PAUSE_STARTS|HARD_STOP|COOLDOWN_EXTEND`

## 10.5 Planner Integration
- soft drift → block `START/REBUILD`
- hard drift (while running) → `STOP_META_DRIFT_HARD`

## 10.6 Reason Codes
- `BLOCK_META_DRIFT_SOFT`
- `STOP_META_DRIFT_HARD`

### Status update (2026-02-26)
- Implemented in `GridBrainV1` using a smoothed, per-channel detector with z-score + CUSUM/Page-Hinkley style accumulators and minimum-sample gating.
- Active channels:
  - `atr_pct_15m`
  - `rvol_15m`
  - `spread_pct` (direct if available, proxy fallback)
  - `box_pos_abs_delta`
  - optional placeholders: `orderbook_imbalance`, `depth_thinning_score`
- Planner outputs now include:
  - `drift_detected`
  - `drift_channels`
  - `severity`
  - `recommended_action`
- Integration now enforces:
  - soft drift -> `BLOCK_META_DRIFT_SOFT` (blocks START/REBUILD)
  - hard drift while running -> stop path with `STOP_META_DRIFT_HARD`
  - hard drift while idle -> cooldown extension recommendation path
- Dedicated replay validation now exists in `freqtrade/user_data/tests/test_meta_drift_replay.py`, covering synthetic regime-shift sequences end-to-end in `simulate_grid_replay` (soft drift blocker accounting + hard-stop reason/event propagation).

---

# 11) Phase-2: Regime Filters and Build Gates (Detailed)

This phase decides whether a grid can be built/launched/rebuilt.

---

### DONE

#### 11.4 Band / Drift / Slope / Asymmetry Vetoes

### Included ideas
- Band midline slope veto
- Drift slope veto (pivot/channel based)
- Excursion asymmetry veto (up/down deviation ratio bounds)
- Envelope vs box overlap soft/hard checks (later channel modules)

These are optional/toggleable strictness layers to reduce launches into hidden acceleration.

**Status:** Implemented inside `GridBrainV1` (band slope history, drift guard, and excursion ratio helpers feed the phase-2 gate checks, and `test_phase3_validation` now exercises the new helper methods).

#### 11.7 Funding Filter (Optional, Spot Contextual)

### Source/logic (preserved)
Use FR script logic (Binance premium index derived 8h funding estimate):
- `fr_8h_pct`
- `funding_ok = abs(fr_8h_pct) <= 0.05%`
- optional bias = sign(funding)

### Role
Optional Phase-2 advisory/gate, not hard dependency.

**Status:** Implemented via the `funding_filter` toggle in `GridBrainV1`; `fr_8h_pct` must stay within ±0.05% to allow START/REBUILD, otherwise `BLOCK_FUNDING_FILTER` is emitted.

#### 11.8 HVP Gate (High Volatility Percentile style; ON by default later)

### Purpose
Block builds during volatility expansion clusters missed by static gates.

### Behavior
- Compute HVP + HVP SMA
- Block new builds when `HVP >= HVPSMA` and 1h BBW expanding
- Require cool-off (`HVP < HVPSMA`) before (re)build
- Optional quiet-exit bias when HVP drops below SMA

**Status:** Implemented through `GridBrainV1`’s HVP gate (cool-off state tracked per pair, metrics reported in the plan signals, and gating tested via `test_phase3_validation` helpers).

### TODO

#### 11.1 Core Baseline Gates (Must-Have)

##### 11.1.1 ADX Gate (4h)
**Goal:** avoid strong directional regimes.  
Baseline:
- enter allowed if `ADX_4h <= 22`
- optional hysteresis (e.g., enter ≤22, exit ≥25)

Reason code:
- `BLOCK_ADX_HIGH`

##### 11.1.2 BBW Quietness Gate (1h)
**Goal:** avoid volatility expansion / breakout phase.  
Baseline:
- BBW non-expanding over recent bars (configurable lookback + tolerance)

Reason code:
- `BLOCK_BBW_EXPANDING`

##### 11.1.3 EMA Distance Compression Gate (1h)
**Goal:** avoid hidden trend acceleration despite local range.  
Baseline:
- `abs(EMA50 - EMA100)/price <= threshold`

Reason code:
- `BLOCK_EMA_DIST`

##### 11.1.4 rVol Calm Gate (15m and/or 1h)
**Goal:** avoid impulse/event spikes.  
Baseline:
- build prefers `rVol <= ~1.2–1.5` (mode-dependent)

Reason code:
- `BLOCK_RVOL_SPIKE`

##### 11.1.5 7d Context / Extreme Sanity
**Goal:** avoid building directly into macro breakout edges.  
Used as a box/build sanity overlay (not always a hard veto unless configured).

#### 11.2 Structural Breakout Fresh-Block (Non-Repainting)

##### Logic
On build TF (default 15m):
- `bull_break_N = close > highest(high[1], N)`
- `bear_break_N = close < lowest(low[1], N)`
- cache last breakout levels
- track bars since breakout
- if fresh breakout → set `Idle` + start reclaim timer

##### Defaults
- `N = 14`
- fresh breakout block window ~20 bars
- reclaim override allowed (configurable)

##### Cached Levels
- `last_break_up_lvl`
- `last_break_dn_lvl`

##### Integration
- START/REBUILD block
- box straddle veto if box crosses cached breakout level within `< 1 step`

Reason code:
- `BLOCK_FRESH_BREAKOUT`

#### 11.3 Range DI / Deviation-Pivot Regime State (`os_dev`) [Misu-style integration]

##### State
- `-1` bearish directional
- `0` range/neutral
- `+1` bullish directional

##### Characteristics
- deviation pivot based
- strike confirmation (`nStrike=2`)
- persistence requirement for neutral state

##### Defaults / Behavior
- Build eligibility prefers `os_dev=0`
- Require `os_dev=0` persisting ≥ L/2 bars
- If `os_dev` flips to ±1 → set `Idle` + start reclaim timer
- Rebuild only after reclaim + `os_dev=0` persistence + quiet volume

##### Additions
- band slope veto during build (e.g. >0.35% / 20 bars)
- range strike-gated STOP/REBUILD discipline

#### 11.5 BBWP MTF Gate (Core/High Value; ON by default later)

##### Adopted behavior
- Use BBWP percentile across S/M/L TFs
- Build allow when:
  - `S ≤ 35`
  - `M ≤ 50`
  - `L ≤ 60`
  - plus 3-bar non-expansion
- Veto when any `≥ 90`
- Cool-off after any `≥ 98` until S<50 and M<60

##### Additional integrations preserved
- EltAlt auto timeframe ladder mapping for M/L
- BBWP v6 array-based percentile implementation (preferred standard)

Reason codes:
- `BLOCK_BBWP_HIGH`
- `COOLOFF_BBWP_EXTREME`

#### 11.6 Squeeze State Gate (BB inside KC) + Squeeze Momentum

##### Core squeeze logic
- detect BB-inside-KC compression
- prefer builds during squeeze-on with quiet volume
- allow controlled post-release window if range re-normalizes

##### Quick STOP override
- if squeeze releases against box bias and close > 1 step outside box → STOP immediately

##### Squeeze Momentum v2 (LazyBear `val`) integration
- block fresh START if `val` flips against edge context
- TP nudge when `val` decelerates / color flip

#### 11.9 Start Gate Aggregation Order (Recommended)

Apply in this order:
- planner health state (`ok/degraded/quarantine`)
- hard STOP conditions
- phase-2 baseline gates
- structural freshness / `os_dev` / BBWP / squeeze / HVP
- meta drift soft block
- start stability score + k-of-n
- replan/materiality policy (if active plan exists)

---
# 12) Phase-3: Box Builder (Range Definition & Validation)

This is the core of the grid planner and must remain deterministic and explainable.

---

## 12.1 Core Box Builder (Baseline)

### Definition
- 24h rolling H/L from 15m candles
- ATR padding:
  - `pad = 0.35 × ATR(15m,20)`
- Proposed box:
  - `box_low = low_24h - pad`
  - `box_high = high_24h + pad`

### Width Targets (baseline)
- practical target width around `3.5%–6%`
- if too narrow → fallback/expand source window
- if too wide → reduce `N`, widen step, or skip (configurable)

### Required Diagnostics
- width (abs, %)
- box mid
- price position in box
- pad size
- source window metadata

### DONE

#### 12.1 Core Box Builder (Baseline)
- Implementation observes a 24h rolling high/low on 15m candles, pads the range via `atr_15m` (see `GridBrainV1._build_box_15m`), and auto-adjusts lookback windows when the width falls outside the 3.5–6% band. The diagnostics recorded in `_box_candidate_diag` capture the width, midpoint, pad, and lookback metadata every cycle.

#### 12.2 Box Width Adjustment & Veto Policy
- Width and channel thresholds are enforced through the sequential lookback fallbacks in `_build_box_15m`, the overlap pruning (`_box_overlap_prune`), and the envelope/band overlap gates near `GridBrainV1._update_box_quality`. Hard/soft bounds are surfaced via `BlockReason` entries such as `BLOCK_BOX_CHANNEL_OVERLAP_LOW` and `BLOCK_BOX_ENVELOPE_RATIO_HIGH` when the box violates the configured ratios.

#### 12.3 VRVP / Volume Profile (Deterministic, 24h baseline)
- `_vrvp_profile` produces poc/vah/val with fixed bins and window, and `_determine_box_candidate` shifts the candidate range toward the VRVP POC (bounded by `vrvp_max_box_shift_frac`). The subsequent `_vrvp_box_ok` flags cancel builds when the POC remains outside with insufficient tolerance, and the VRVP metadata travels through the plan payload.

#### 12.4 POC Acceptance Gate
- `_poc_acceptance_status` tracks whether a POC cross has occurred for a live signature; the gate is enforced when `poc_acceptance_enabled` is true, emitting `BLOCK_NO_POC_ACCEPTANCE` if unmet and delaying `START` until `open/close` actions cross the stored POC.

#### 12.5 Straddle Veto Framework
- Centralized helpers (`_box_straddles_level`, `_box_straddles_cached_breakout`, `_box_level_straddle_reasons`) evaluate cached breakout, FVG, session, and other structural levels against the candidate box with configurable step buffers (`fvg_straddle_veto_steps`), applying veto flags captured as `fvg_straddle_veto` and providing precise reasons in `extra_level_reasons`.

#### 12.6 Box Quality Enhancements
- Quartiles, log-space extensions, and band/VP overlap heuristics live inside `_update_box_quality`. Overlap pruning, midline bias fallbacks, envelope-width checks, and channel ratio validations all feed into the box diagnostics so future planners can introspect any mutation.

#### 12.7 Session/Range Context Integrations
- Session VWAP/FVG cues, pad shrink when session prints occur, and optional session-based gating (`fvg_state` flags) integrate with the box builder by shrinking pads, shifting boxes, and attaching session metadata to the emitted plan.

---

## 12.2 Box Width Adjustment & Veto Policy

### Included controls (preserved)
- target width band
- hard/soft width limits
- channel-width veto (selectable source: BB/ATR/SMA/HL)
- percent-of-average width veto (e.g. width > 120% rolling avg of accepted widths)
- minimum range length before eligibility
- breakout confirmation bars before invalidating candidate

### Optional
- range-inside-range veto (default OFF due to overlap pruning already present)

---

## 12.3 VRVP / Volume Profile (Deterministic, 24h baseline)

### Required outputs
- `vrvp_poc`
- `vrvp_vah`
- `vrvp_val`

### Rules
- fixed-bin profile
- fixed window
- non-repainting
- deterministic binning

### Box Interaction
- if POC > 0.5% outside box:
  - shift box toward POC (bounded, e.g. ≤0.5%), or
  - reject build

### Additional preserved features
- MTF POC confluence later (D/W/M)
- POC-cross acceptance gate before first START

---

## 12.4 POC Acceptance Gate (Before First START on New Box)

### Preserved behavior
Before first `START` on a new box:
- require one POC cross (open<POC and close>POC OR inverse)

### Variants
- use VRVP POC
- or micro-POC (if module enabled)
- optional alignment rule if both exist and disagree

Reason code:
- `BLOCK_NO_POC_ACCEPTANCE`

---

## 12.5 Generic Straddle Veto Framework (High reuse utility)

### Purpose
Centralize box-level veto logic against structural levels.

### Utility concept
`box_straddles_level(box_low, box_high, level, min_distance)`

### Apply to (preserved ideas)
- cached breakout levels
- OB edges
- FVG edges/avgs
- session FVG avg
- higher-TF POCs
- VWAP / Donchian mid (when configured)
- FVG positioning averages (optional)
- opposite-side structural levels within `< 1 step`

### Behavior
- detect violation
- optionally shift box ≤0.5% toward POC
- else skip build
- log exact veto source and level

---

## 12.6 Box Quality Enhancements (Preserved)

### Included
- Log-space quartiles `Q1/Q2/Q3`
- 1.386 extensions (per side)
- overlap pruning of mitigated/active ranges (e.g. ≥60% overlap keep newest)
- box-vs-bands overlap requirements (e.g. ≥60%)
- envelope overlap soft check with ADX/rVol allowance
- fallback POC estimator if VRVP unavailable
- midline bias fallback if VP/POC neutral
- channel envelope width ratio veto

### Purpose
Improve range quality, bias, and target placement without changing cost invariants.

---

## 12.7 Session/Range Context Integrations (Preserved)

### Included
- Session high/low events and sweeps
- Session VWAP / optional daily VWAP as TP candidates
- Session FVG interactions (separate FVG section)
- Box inside same-side session FVG → optional pad shrink

---

# 13) Phase-4: Grid Sizing, START Filters, Targets, Risk

---

## 13.1 Cost-Aware Step Sizing (Core Invariant)

### Preserved baseline
- net per-step target `T >= 0.40%`
- gross step floor `G = T + fees + spread (+ penalties later)`
- majors baseline often around `~0.65%` gross minimum

### Rule
`actual_step_pct >= min_step_pct_required`

### If violated
- reduce N (within bounds), or
- block START/REBUILD

Reason code:
- `BLOCK_STEP_BELOW_COST`

---

## 13.2 Empirical Cost & Fill Calibration Loop (New, High ROI)

### Purpose
Replace static spread assumptions over time using paper/live execution logs.

### Inputs
- fills log
- order lifecycle log (placed/cancelled/repriced)
- candle/ticker context at fill time
- optional market state buckets (volatility/time of day)

### Compute
- realized spread percentiles
- adverse selection penalty
- post-only retry/reject rate
- missed-fill opportunity rate
- recommended cost floor bps

### Planner integration
- `cost_model_source = static | empirical`
- conservative mode uses max(static, empirical p75/p90 or recommended)

Reason codes:
- `BLOCK_STEP_BELOW_EMPIRICAL_COST`
- `WARN_COST_MODEL_STALE`

---

## 13.3 N Levels Selection Policy

### Core policy
1. derive candidate `N` from box width and target step
2. clamp by mode bounds
3. validate against cost floor
4. optionally adjust by volatility policy adapter
5. record diagnostics

### Preserved bounds
- typical working range: `N in [6..12]` (mode-dependent)

---

## 13.4 START Entry Filters (Mode-aware, Aggregated)

### Preserved + integrated filters
- box position (e.g. middle 35–65%)
- optional RSI neutral/micro guard
- POC acceptance/cross
- MRVD/VAH/VAL/POC proximity gate
- basis-cross confirm
- start stability score
- meta drift soft block
- planner health state
- cooldown/reclaim status
- optional capacity hint (advisory from executor data later)

### Output
Planner should log **all blockers**, not just first blocker.

---

## 13.5 Inventory / Capital Policy (Current default + future-ready schema)

### Current default
- `inventory_mode = quote_only`
- one grid per pair

### Preserve future fields now (schema)
- `inventory_target_bands` (for mixed mode later)
- `reserve_pct`
- `topup_policy`
- `grid_budget_pct`
- `max_concurrent_rebuilds` (if multi-pair later)
- `preferred_rung_cap` (planner hint to executor)

---

## 13.6 TP/SL Computation at START (Deterministic, Logged)

### Baseline defaults (preserved)
- TP ≈ `box_top + 0.75–1.0 × step`
- SL ≈ `box_bottom - 1.0 × step`
- plus reclaim/time-stop / STOP logic path

### TP candidate set (preserved and expanded)
- box default TP
- quartiles `Q1/Q3`
- VRVP POC
- MRVD `D/W/M` POCs
- Donchian mid
- session VWAP / daily VWAP
- basis bands / basis mid
- IMFVG avg
- session FVG avg
- FVG positioning averages (`up_avg/down_avg`)
- HVNs
- FVG-POC (if FVG-VP enabled)
- channel midline/bounds (if closer and conservative)

### Selection rule
**Nearest conservative wins** (faster exit favored if it reduces time-in-trade and remains sensible).

### SL constraints / nudges (preserved)
- avoid placing inside LVN void if possible
- never tighten SL inside FVG gap if unsafe
- use conservative rule among structural constraints

---

## 13.7 Fill Detection / Rung Crossing Logic (Preserved from reviewed scripts)

### Required shared logic
- deterministic rung touch/cross detection
- sorted levels + binary search lookup
- fill confirmation mode:
  - `Touch`
  - `Reverse` (cross + reclaim)
- no-repeat / LSI guard
- cooldown/no-repeat after fill/action
- tick-aware rounding using `syminfo.mintick` equivalent precision helpers

### Executor and simulator should share logic or exact semantics.

### Status update (2026-02-26)
- `fill_detection.no_repeat_lsi_guard` is now enforced (not metadata-only) in both simulator and executor.
- Guard semantics are aligned as side+level scoped cooldown control:
  - key = `(side, level_index)`
  - if enabled, repeated action on the same key is blocked until cooldown bars elapse
  - if disabled, repeated action is allowed
- Simulator and replay paths now both read/apply:
  - `fill_detection.fill_confirmation_mode`
  - `fill_detection.no_repeat_lsi_guard`
  - `fill_detection.cooldown_bars`
- Executor now uses plan clock (`runtime_state.clock_ts`, fallback `candle_ts`) to derive deterministic bar-index progression for the same cooldown semantics.

---

# 14) Brain→Executor Handoff Contract (Atomic + Idempotent)

## 14.1 Why This Is Mandatory

Prevents:
- half-written JSON reads
- duplicate plan application
- stale plan overriding newer one
- loop-mode race conditions

## 14.2 Plan Signature Fields (Required)
- `plan_id` (UUID)
- `decision_seq` (monotonic per pair)
- `plan_hash` (stable hash of material fields)
- `valid_for_candle_ts`
- `generated_at`
- `expires_at` (optional)
- `supersedes_plan_id` (optional)
- `materiality_class` (`noop|soft|material|hardstop`)

## 14.3 Atomic Publish Semantics (Brain)
1. write `grid_plan.latest.json.tmp`
2. flush + fsync
3. atomic rename to `grid_plan.latest.json`

## 14.4 Executor Consume Semantics
Executor must:
- parse schema
- validate `plan_hash`
- ignore if `plan_id` already applied
- ignore if `decision_seq <= last_applied_seq`
- log rejection reason

## 14.5 Shared Helpers (recommended)
- `io/atomic_json.py`
- `schemas/plan_signature.py`

---

# 15) Phase-5: Monitoring, STOP, REBUILD, Runtime Safety Rails

---

## 15.1 STOP Trigger Framework (Preserved + expanded)

### Core triggers
- breakout beyond box (2-strike confirm)
- fast move > 1 step outside box
- range shift > threshold (e.g. 0.7%)
- fresh structure block events
- squeeze release against bias (override)
- strong breakout channel event (override / satisfies 2-strike)
- LVN-void breakout fast STOP (optional)
- meta drift hard STOP
- data quarantine emergency STOP
- execution-unsafe STOP (confirm-exit hook, later)

### Example STOP reason codes
- `STOP_BREAKOUT_2STRIKE_UP`
- `STOP_BREAKOUT_2STRIKE_DN`
- `STOP_FAST_MOVE_UP`
- `STOP_FAST_MOVE_DN`
- `STOP_RANGE_SHIFT`
- `STOP_SQUEEZE_RELEASE_AGAINST`
- `STOP_CHANNEL_STRONG_BREAK`
- `STOP_META_DRIFT_HARD`
- `STOP_DATA_QUARANTINE`
- `STOP_EXECUTION_UNSAFE`

---

## 15.2 REBUILD / Reclaim Discipline (Preserved, strengthened)

### Core behavior
- 8h reclaim timer
- REBUILD only after:
  - reclaim condition satisfied
  - gates pass again
  - quietness returns
  - `os_dev=0` persistence (if enabled)
  - soft drift cleared
  - start stability conditions pass
  - POC/basis acceptance (if enabled)

### Purpose
Prevent STOP→REBUILD flip-flop in unstable regimes.

### Reason codes
- `BLOCK_RECLAIM_PENDING`
- `BLOCK_RECLAIM_NOT_CONFIRMED`

---

## 15.3 Cooldown / Min Runtime / Drawdown Guard (Protections Layer)

### Preserved defaults
- cooldown ~90m
- min runtime ~3h
- drawdown guard (post-fact safety rail)

### New integration
Volatility adapter may adjust these modestly (bounded, logged).

---

## 15.4 Confirm-Entry / Confirm-Exit Hooks (Execution Conditions)

### Purpose
Final safety checks before actioning START/REBUILD/STOP on executor side.

### Candidate checks
- spread threshold
- depth thinning
- top-of-book imbalance extreme
- sudden jump detection
- post-only feasibility / repeated reject burst

### Output
`confirm_ok`, reasons, confidence modifier

---

## 15.5 Structured Event Taxonomy (Recommended)

Use event objects instead of scattered booleans.

### Event fields
- `event_type`
- `ts`
- `price`
- `side`
- `severity`
- `source_module`
- `metadata`

### Example event types
- `POC_TEST`
- `EXTREME_RETEST_TOP`
- `EXTREME_RETEST_BOTTOM`
- `SWEEP_WICK_HIGH`
- `SWEEP_WICK_LOW`
- `BREAK_RETEST_EDGE`
- `FVG_MITIGATED_BULL`
- `CHANNEL_STRONG_BREAK_DN`
- `META_DRIFT_SOFT`
- `META_DRIFT_HARD`
- `DATA_QUALITY_DEGRADED`
- `REPLAN_MATERIAL_CHANGE`

---

# 16) Executor Design (Paper First, Live Hardened Later)

---

## 16.1 Maker-First Execution Discipline (Preserved)

### Required behavior
- post-only first
- tick-aware rounding
- retry/backoff
- timeout + selective reprice
- avoid unnecessary cancel-all churn

### Goal
Reduce adverse selection and execution noise.

---

## 16.2 Minimal Order-Flow Metrics (Preserved)

Use as soft veto/confidence first:
- spread %
- top-of-book imbalance
- depth thinning
- jump detection

Log now → gate later.

---

## 16.3 Depth-Aware Capacity Cap (New, high ROI)

### Purpose
Prevent ladder sizing that exceeds local book credibility.

### Low/medium complexity version
Use top-of-book + first few levels to estimate:
- safe active rung count
- safe per-rung notional
- whether replenishment should be delayed

### Executor hook output
- `capacity_ok`
- `max_safe_active_rungs`
- `max_safe_rung_notional`
- reasons (`DEPTH_THIN_AT_TOP`, `SPREAD_WIDE`, etc.)

### Planner integration
- planner may emit `preferred_rung_cap` hint
- executor enforces actual cap dynamically

### Reason codes
- `BLOCK_CAPACITY_THIN`
- `EXEC_CAPACITY_RUNG_CAP_APPLIED`

---

## 16.4 Paper Executor + Local Fill Harness (Recommended before live)

Paper executor should support:
- ladder seed
- fill simulation hook
- replace-on-fill
- replan reconcile
- capacity cap enforcement
- confirm hooks
- chaos profile perturbations

---

# 17) Testing, Replay, Tuning, and Anti-Overfit Protocol

---

## 17.1 Unit Tests (High ROI)

Must cover:
- breakout detection
- straddle veto utility
- box width constraints
- POC acceptance reset
- cost floor + N selection
- STOP precedence
- cooldown/min-runtime
- fill detection (`Touch`/`Reverse`)
- LSI/no-repeat guard
- replan materiality classification
- start stability score
- data health transitions
- atomic JSON publish/read
- plan hash validation
- capacity guard calculations

---

## 17.2 Golden Replay Tests

Use fixed timeranges and expected outputs:
- START/STOP counts
- reason distributions
- selected plan snapshots
- replan decision distribution
- false-start rate

Purpose: catch regressions during refactors.

---

## 17.3 Brain/Simulator Consistency Tests

On same historical input:
- action sequence should match
- box/grid params should match (within defined tolerance)
- replan/materiality classification consistent

---

## 17.4 Stress/Chaos Replay Harness (New, Mandatory before over-tuning)

### Purpose
Add execution realism without requiring tick data.

### Perturbations
- latency injection
- spread shocks
- partial fills
- post-only reject bursts
- delayed/missing candles
- data gaps

### Example chaos profile fields
- latency p50/p95
- spread multiplier percentiles
- partial fill rate
- post-only reject burst probability
- data gap probability/day

### Acceptance
Strategy remains operationally stable (not necessarily profitable) and safety rails fire correctly.

---

## 17.5 Formal Tuning Protocol (Walk-Forward + Ablation + PBO-aware sanity)

### Why
Prevent “good logic overfit to replay”.

### Required process
1. Frozen baseline config
2. Ablation runs (one module/group on/off)
3. Walk-forward splits
4. Champion/challenger registry
5. PBO-like / rank-stability sanity check (approximate acceptable at first)

### Promotion rule (new)
No config becomes default unless:
- OOS passes on N splits
- churn not worse than baseline by >X%
- false-start rate not worse than baseline by >Y%
- no major chaos-profile degradation (recommended)

### Required experiment artifacts
- IS/OOS metrics
- reason-code distributions
- churn stats
- false-start rate
- parameter hash
- module toggle set
- chaos delta (recommended)

---

# 18) Module Registry (Preserved Ideas + New Additions)
This section is the **auditable checklist**.  
For each module, mark status in code review: `UNKNOWN / PLANNED / PARTIAL / DONE / DISABLED_BY_DEFAULT`.

---

## 18.A Core Planner / Stability / Governance (New + high priority)

### M001 — Parameter Inertia + Epoch Replan Policy
- Purpose: anti-churn governor
- Decision classes: `NOOP/SOFT/MATERIAL/HARD_STOP`
- Status: `PLANNED`
- Default: `ON`
- Check implementation:
  - `planner/replan_policy.py`
  - materiality metrics logged
  - replan decision in plan JSON

### M002 — Atomic Brain→Executor Handoff + Idempotency Contract
- Purpose: eliminate partial/duplicate/stale plan application
- Status: `PLANNED`
- Default: `ON`
- Check:
  - temp write + fsync + rename
  - `plan_id`, `decision_seq`, `plan_hash`
  - executor dedupe logic

### M003 — Global Start Stability Score (k-of-n)
- Purpose: reduce false starts
- Status: `PLANNED`
- Default: `ON`
- Check:
  - score + components logged
  - k-of-n persistence gate active

### M004 — Data Quality Quarantine State
- Purpose: first-class planner health state
- Status: `PLANNED`
- Default: `ON`
- Check:
  - `planner_health_state` in plan/logs
  - degraded/quarantine behavior differs

### M005 — Meta Drift Guard (Page-Hinkley/CUSUM style)
- Purpose: change-point kill-switch
- Status: `PLANNED`
- Default: `ON`
- Check:
  - drift channels tracked
  - soft pause / hard stop paths

### M006 — Volatility Policy Adapter (deterministic)
- Purpose: bounded threshold adaptation pre-ML
- Status: `PLANNED`
- Default: `ON`
- Check:
  - `vol_bucket`
  - base vs adapted thresholds logged

### M007 — Empirical Execution Cost Calibration Loop
- Purpose: replace static spread assumptions over time
- Status: `PLANNED`
- Default: `ON` after sufficient paper/live logs
- Check:
  - periodic calibration artifact
  - planner `cost_model_source`

### M008 — Stress/Chaos Replay Harness
- Purpose: execution realism / robustness
- Status: `PLANNED`
- Default: `ON` for validation (not runtime)
- Check:
  - chaos profiles
  - deterministic vs chaos report delta

### M009 — Depth-Aware Capacity Cap
- Purpose: liquidity-aware sizing / rung cap
- Status: `PLANNED`
- Default: `ON` (executor)
- Check:
  - capacity guard output
  - rung cap applied + logged

### M010 — Enum Registry + Plan Diff Snapshots
- Purpose: analytics consistency + debugging
- Status: `PLANNED`
- Default: `ON`
- Check:
  - central enums file
  - `changed_fields` / plan diff logs

---

## 18.B Phase-2 Regime / Build Gates (Core + preserved expansions)

### M101 — ADX Gate (4h)
- Goal: avoid strong trend regimes
- Default: `ON`
- Status: `PLANNED`
- Threshold baseline: enter ≤22, optional hysteresis

### M102 — BBW Quietness Gate (1h)
- Goal: avoid expansion phase
- Default: `ON`
- Status: `PLANNED`

### M103 — EMA50/EMA100 Compression Gate (1h)
- Goal: avoid hidden trend acceleration
- Default: `ON`
- Status: `PLANNED`

### M104 — rVol Calm Gate (1h/15m)
- Goal: block impulse/event spikes
- Default: `ON`
- Status: `PLANNED`

### M105 — 7d Context / Extremes Sanity
- Goal: macro edge sanity
- Default: `ON`
- Status: `PLANNED`

### M106 — Structural Breakout Fresh-Block + Cached Break Levels
- Includes: `bull_break_N`, `bear_break_N`, cached breakout levels, bars-since, reclaim timer
- Default: `ON`
- Status: `PLANNED`

### M107 — Range DI / Deviation-Pivot `os_dev` (Misu-style)
- Includes strike gating, neutral persistence, STOP/REBUILD sync
- Default: `ON` (can be phased in)
- Status: `PLANNED`

### M108 — Band Slope / Drift Slope / Excursion Asymmetry Vetoes
- Default: mixed (`OFF` initially for some)
- Status: `PLANNED`

### M109 — BBWP MTF Gate + Cool-off
- Includes BBWP core percentile implementation, S/M/L thresholds, cool-off ≥98
- Default: `ON`
- Status: `PLANNED`

### M110 — Squeeze State Gate (BB inside KC) + release STOP override
- Default: `ON`
- Status: `PLANNED`

### M111 — Funding Filter (FR 8h est, Binance premium index)
- Default: `OFF` or advisory
- Status: `PLANNED`

### M112 — HVP Gate (HVP vs HVPSMA + BBW expansion)
- Default: `ON`
- Status: `PLANNED`

### M113 — Boom & Doom Impulse Guard
- Behavior: freeze new entries for 5 bars against impulse; partial TP when aligned
- Default: `ON` (EMA filter OFF)
- Status: `PLANNED`

---

## 18.C Phase-3 Box Builder / Range Quality (Core + preserved)

### M201 — Core 24h ± ATR Box Builder
- 24h H/L + `0.35*ATR(15m,20)` pad
- Width diagnostics
- Default: `ON`
- Status: `PLANNED`

### M202 — Box Width Target / Hard-Soft Veto Policy
- Includes min/target/max bands
- Default: `ON`
- Status: `PLANNED`

### M203 — Channel-Width Veto (BB/ATR/SMA/HL selectable)
- From Range Detect-style review
- Default: `ON`
- Status: `PLANNED`

### M204 — Percent-of-Average Width Veto
- Example: width >120% rolling mean of accepted widths
- Default: `ON`
- Status: `PLANNED`

### M205 — Minimum Range Length + Breakout Confirm Bars
- Default: `ON`
- Status: `PLANNED`

### M206 — VRVP POC/VAH/VAL (24h deterministic)
- Default: `ON`
- Status: `PLANNED`

### M207 — POC Acceptance Gate (cross before first START)
- Default: `ON`
- Status: `PLANNED`

### M208 — Generic Straddle Veto Framework (shared utility)
- Apply to breakout/FVG/OB/POC/VWAP/Donchian/etc.
- Default: `ON`
- Status: `PLANNED`

### M209 — Log-Space Quartiles + 1.386 Extensions
- Default: `ON`
- Status: `PLANNED`

### M210 — Overlap Pruning of Mitigated Boxes (≥60%)
- Default: `ON`
- Status: `PLANNED`

### M211 — Box-vs-Bands / Envelope Overlap Checks
- Default: `ON` (soft/hard thresholds configurable)
- Status: `PLANNED`

### M212 — Fallback POC Estimator (when VRVP unavailable)
- Default: `ON` as fallback only
- Status: `PLANNED`

### M213 — Midline Bias Fallback (POC-neutral fallback)
- Default: `ON`
- Status: `PLANNED`

---

## 18.D Phase-4 Grid Sizing / Targets / Risk (Core + preserved)

### M301 — Cost-Aware Step Sizing
- Invariant: step >= fees + spread + target (+ penalties)
- Default: `ON`
- Status: `PLANNED`

### M302 — N Levels Selection (bounded)
- Default: `ON`
- Status: `PLANNED`

### M303 — START Entry Filter Aggregator
- Box position / RSI / POC / confluence / stability / drift / health / reclaim / cooldown
- Default: `ON`
- Status: `PLANNED`

### M304 — Deterministic TP/SL Selection (nearest conservative wins)
- Default: `ON`
- Status: `PLANNED`

### M305 — Fill Detection / Rung Cross Engine (`Touch` / `Reverse`)
- Includes binary search rung lookup, no-repeat/LSI guard, tick-aware rounding
- Default: `ON`
- Status: `PLANNED`

### M306 — Directional skip-one rule (simulator-inspired)
- Optional in trend mode
- Default: `OFF`
- Status: `PLANNED`

### M307 — Next-rung ghost lines (UI only)
- Default: `OFF`
- Status: `PLANNED`

---

## 18.E Phase-5 Monitoring / STOP / REBUILD / Runtime Controls

### M401 — STOP Trigger Framework
- 2-strike, fast-move, range shift, structure/squeeze/channel/drift overrides
- Default: `ON`
- Status: `PLANNED`

### M402 — Reclaim Timer + REBUILD Discipline (8h baseline)
- Default: `ON`
- Status: `PLANNED`

### M403 — Cooldown + Min Runtime + Anti-Flap
- Default: `ON`
- Status: `PLANNED`

### M404 — Protections Layer (cooldown + drawdown guard + future protections)
- Default: `ON`
- Status: `PLANNED`

### M405 — Confirm-Entry / Confirm-Exit Hooks (spread/depth/jump)
- Default: `ON` (can start as soft checks)
- Status: `PLANNED`

### M406 — Structured Event Bus / Taxonomy
- Default: `ON`
- Status: `PLANNED`

---

## 18.F Volume Profile / VAP / LVN-HVN Family (Preserved)

### M501 — Micro-VAP inside active box
- Fixed bins, body/wick weighting
- Outputs: micro_POC, HVN/LVN, void slope
- Default: `OFF` initially (module ON later)
- Status: `PLANNED`

### M502 — POC Alignment Check (micro_POC vs VRVP_POC)
- Delay START until cross if misaligned > threshold
- Default: `ON`
- Status: `PLANNED`

### M503 — HVN/LVN inside box + min spacing
- TP prefer HVN, avoid SL in LVN voids
- Default: `ON`
- Status: `PLANNED`

### M504 — LVN-void STOP Accelerator
- Breakout exits via LVN corridor → fast STOP
- Default: `ON` (configurable sensitivity)
- Status: `PLANNED`

### M505 — Micro-VAP bias / TP-SL nudges / re-entry discipline
- Default: mixed (some OFF initially)
- Status: `PLANNED`

---

## 18.G FVG / OB / IMFVG / Session FVG / FVG-VP Stack (Preserved, staged)

### M601 — Lightweight OB Module
- latest OB per side, freshness gate, box veto, TP nudge
- Default: `ON` (light)
- Status: `PLANNED`

### M602 — Basic FVG Detection + Straddle Veto
- width filter, latest K per side, opposite-side hard veto near box
- Default: `ON`
- Status: `PLANNED`

### M603 — IMFVG Average as TP Candidate + Mitigation Relax
- IMFVG avg in target set
- mitigated opposite-side IMFVG relaxes straddle veto
- Default: `ON`
- Status: `PLANNED`

### M604 — Session FVG Module (daily)
- latest session FVG cache
- session pause bars
- inside-FVG gate
- avg/edge target candidates
- fresh against-bias session FVG → Idle/reclaim
- Default: `ON`
- Status: `PLANNED`

### M605 — FVG Positioning Averages (`up_avg`, `down_avg`)
- rolling averages of FVG edges
- target candidates ON; veto/STOP options OFF initially
- Default: TP use `ON`, veto/STOP `OFF`
- Status: `PLANNED`

### M606 — FVG-VP (Volume Profile inside FVG) Module
- event-driven, side-capped, cached FVG-POC
- refines veto/targets/STOP
- Default: `OFF`
- Status: `PLANNED`

### M607 — Defensive FVG Quality Filter (TradingFinder-style)
- use Defensive mode by default
- fresh opposite-side quality FVG pauses START until mitigation
- adds FVG prox/dist target candidates
- Default: `ON`
- Status: `PLANNED`

---

## 18.H Channel / Breakout / Sweep Modules (Preserved)

### M701 — Donchian Channel Module
- width gate
- midline TP candidate
- strong-close STOP beyond bound
- Default: `ON`
- Status: `PLANNED`

### M702 — Smart Breakout Channels (AlgoAlpha-style)
- volatility-normalized channel with strongClose breakout
- volume-confirmed breakout (if data available)
- STOP and TP nudges using channel bounds/mid
- Default: `ON`
- Status: `PLANNED`

### M703 — Zig-Zag Envelope / Channel Enhancements
- drift slope veto
- excursion asymmetry
- envelope overlap/ratio
- contraction before rebuild
- Default: mixed (`some OFF`)
- Status: `PLANNED`

### M704 — Liquidity Sweeps (LuxAlgo-style)
- wick sweep + break&retest sweep
- TP nudge vs STOP precedence behaviors
- Default: `ON`
- Status: `PLANNED`

### M705 — Sweep mode toggle (Wick/Open) for retest validation
- Default: `Wick`
- Status: `PLANNED`

---

## 18.I MRVD / POC Confluence / Basis / VWAP / Session HL (Preserved)

### M801 — MTF POC Confluence (D/W, M advisory) + POC-cross before START
- Default: `ON`
- Status: `PLANNED`

### M802 — MRVD Module (D/W/M distribution + buy/sell split)
- confluence gate
- POC drift guard
- box straddle vs higher-TF POCs
- POC targets + buy/sell split bias
- Default: `ON`
- Status: `PLANNED`

### M803 — Multi-Range Basis / Pivots Module (VWAP default)
- basis slope veto
- basis-cross confirm
- basis bands / Donchian mid as TP candidates
- Default: `ON`
- Status: `PLANNED`

### M804 — Session VWAP / Daily VWAP TP Candidates
- TP candidate only (no build veto initially)
- Default: `ON`
- Status: `PLANNED`

### M805 — Session High/Low Sweep and Break-Retest Events
- sweep → TP nudge
- break-retest through edge → STOP/Idle
- Default: `ON`
- Status: `PLANNED`

### M806 — VAH/VAL/POC Zone Proximity START Gate
- allow START only within nearest zone distance band
- Default: `ON`
- Status: `PLANNED`

### M807 — VAH/VAL Approximation via Quantiles (fallback/optional)
- TP tie-breakers only
- Default: `OFF`
- Status: `PLANNED`

### M808 — Average-of-basis with session H/L bands (target candidates)
- Default: `OFF`
- Status: `PLANNED`

### M809 — Buy-ratio Micro-Bias inside box (mid-band)
- bias rung density / TP tie-break
- Default: `ON`
- Status: `PLANNED`

---

## 18.J CVD / Divergence Family (Preserved)

### M901 — CVD Divergence near box edges (advisory)
- bullish div near bottom / bearish div near top
- affects bias/rung density/TP priority
- Default: `ON`
- Status: `PLANNED`

### M902 — CVD BOS events (ema filtered style)
- BOS-up/down near edge -> TP nudge / freeze entries
- Default: `ON`
- Status: `PLANNED`

### M903 — CVD Spike + Passive Absorption (Insights style)
- spike >2σ -> quick TP nudge
- passive absorption -> soft pause START for 5 bars
- Default: spike `ON`, absorption `ON` soft-pause
- Status: `PLANNED`

### M904 — CVD Divergence Oscillator Strong Score (advisory)
- strong ±RD score elevates TP priority only
- Default: `ON` (advisory only)
- Status: `PLANNED`

### M905 — SMA200 / EMA trend filters for directional variants
- optional directional vetoes only
- Default: `OFF`
- Status: `PLANNED`

### M906 — CVD extension line touch counter (UI only)
- Default: `OFF`
- Status: `PLANNED`

---

## 18.K Execution / Ops / Engineering Controls (Preserved + new)

### M1001 — Maker-first post-only discipline + retry/backoff
- Default: `ON`
- Status: `PLANNED`

### M1002 — Confirm-entry/exit hooks (spread/depth/jump)
- Default: `ON`
- Status: `PLANNED`

### M1003 — Minimal order-flow metrics (soft veto/confidence)
- Default: `ON`
- Status: `PLANNED`

### M1004 — Atomic handoff + idempotency (duplicate-safe)
- Default: `ON`
- Status: `PLANNED`

### M1005 — Empirical execution cost feedback loop
- Default: `ON` after data sufficient
- Status: `PLANNED`

### M1006 — Stress/chaos replay as standard validation
- Default: `ON` in validation pipeline
- Status: `PLANNED`

### M1007 — Formal tuning workflow + anti-overfit checks
- Default: `ON` process requirement
- Status: `PLANNED`

### M1008 — FreqAI/ML confidence overlay (not primary)
- Default: `OFF` until deterministic core stable
- Status: `IMPLEMENTED` (confidence-only, bounded, deterministic core preserved)

---

# 19) Plan / State / Log Schemas (Codex-facing Contract)

---

## 19.1 `grid_plan.latest.json` (Brain output) — Required fields

### Identity and integrity
- `schema_version`
- `planner_version`
- `pair`
- `exchange`
- `plan_id`
- `decision_seq`
- `plan_hash`
- `generated_at`
- `valid_for_candle_ts`
- `expires_at` (optional)
- `supersedes_plan_id` (optional)

### Decision
- `mode`
- `mode_score`
- `action` (`START/HOLD/STOP/REBUILD`)
- `action_reason`
- `blockers` (list)
- `planner_health_state`
- `materiality_class`
- `replan_decision`
- `replan_reasons`

### Range/grid
- `range_diagnostics`
- `box` (`low/high/mid/width_pct/...`)
- `grid` (`n_levels`, `step_pct`, `step_price`, ladder summary)
- `risk` (`tp/sl`, stop policy, reclaim policy)

### Diagnostics
- `signals_snapshot`
- `runtime_hints`
- `start_stability_score`
- `meta_drift_state`
- `cost_model_snapshot`
- `module_states` (recommended)
- `changed_fields` (optional if logging separately)

---

## 19.2 Executor State JSON (recommended schema)

Track at minimum:
- `schema_version`
- `mode` (`paper/live`)
- `pair`
- `last_applied_plan_id`
- `last_applied_seq`
- `last_plan_hash`
- executor state machine (`idle/running/rebuilding/stopping`)
- open orders / ladder state
- fills summary
- balances (free/reserved/total)
- runtime stats
- confirm hook results
- capacity guard state
- last errors
- planner health snapshot

---

## 19.3 Decision Log Schema (per decision tick)

Fields:
- timestamp
- pair
- mode candidate/final
- action
- blockers
- key features snapshot
- box/grid params
- start stability
- meta drift
- planner health
- replan decision/materiality
- prev/new plan hash
- changed fields
- event ids emitted

---

## 19.4 Event Log Schema (per event)

Fields:
- event_id
- ts
- pair
- event_type
- severity
- source_module
- price
- side
- metadata

---

# 20) Implementation Sequence (Recommended Build Order)

This order minimizes wasted work and improves quality of all later modules.

---

## Step 1 — Deterministic Core (must lock first)
1. Core features (ATR, ADX, BBW, EMA distance, rVol)
2. Phase-2 baseline gates
3. Phase-3 core 24h ± ATR box builder
4. Phase-4 cost-aware step sizing + N + basic TP/SL
5. Phase-5 STOP/REBUILD/cooldown/min-runtime
6. Core plan JSON schema + reason codes
7. Simulator core with `Touch/Reverse` fill modes

**Acceptance:** replay runs; every START/STOP explainable.

---

## Step 2 — Stability & Contracts Layer (insert early, before heavy feature expansion)
1. Replan policy + materiality thresholds
2. Atomic handoff + idempotency
3. Start stability score
4. Data quality quarantine state
5. Plan diff snapshots + enum registry

**Acceptance:** duplicate plan apply = 0; lower churn; lower false starts.

---

## Step 3 — Paper Executor Validation
1. Paper ladder engine
2. Local fill harness
3. Basic confirm hooks
4. Basic capacity guard
5. Executor state schema + logs

**Acceptance:** replace-on-fill works; state tracks ladder and plan signatures.

---

## Step 4 — Stress/Chaos Replay Harness
1. chaos profiles
2. perturbation layer
3. deterministic vs chaos reports
4. fault-injection tests

**Acceptance:** safety rails explain changes under chaos.

---

## Step 5 — Empirical Cost Calibration Loop
1. order/fill lifecycle logging standardization
2. calibration artifact generator
3. planner `cost_model_source` switch
4. stale calibration warnings

---

## Step 6 — Meta Drift Guard
1. drift channels
2. soft pause + hard stop integration
3. synthetic regime-shift replay validation

**Status (2026-02-26):** Complete, including dedicated synthetic replay coverage in `freqtrade/user_data/tests/test_meta_drift_replay.py`.

---

## Step 7 — VP / POC Quality Core
1. VRVP POC/VAH/VAL
2. POC-cross acceptance gate
3. generic straddle veto utility
4. box shift/reject logic logs

---

## Step 8 — BBWP + Squeeze + Range DI Regime Tightening
1. BBWP MTF + cool-off
2. squeeze state + release STOP override
3. `os_dev` range state + strike gating

---

## Step 9 — Micro-VAP / HVN-LVN / POC Alignment
1. micro-POC
2. HVN/LVN bins
3. POC alignment gate
4. TP/SL safety nudges
5. optional LVN stop acceleration

---

## Step 10 — FVG / OB Stack (incremental)
1. OB lightweight
2. basic FVG + straddle veto
3. IMFVG avg + mitigation relax
4. session FVG
5. defensive FVG quality filter
6. FVG positioning averages
7. FVG-VP (optional last)

---

## Step 11 — Channels / Sweeps / MRVD / Basis / VWAP / CVD Family
Roll in with ablations and clear reason codes:
- Donchian + smart breakout channels
- liquidity sweeps
- MRVD
- basis/VWAP/pivots
- CVD divergences/BOS/absorption/oscillator advisory

---

## Step 12 — Live Execution Hardening
1. maker-first retry/backoff refinement
2. post-only reject burst handling
3. confirm-entry/exit strict enforcement
4. diff-based reconcile optimization
5. reconnect/error recovery hardening

---

## Step 13 — Formal Tuning Protocol Enforcement
1. experiment manifests
2. champion/challenger registry
3. walk-forward + ablation automation
4. OOS promotion gates
5. chaos-profile validation gate

---

## Step 14 — ML/FreqAI Confidence Overlay (last)
1. leakage-safe labels
2. walk-forward ML eval
3. confidence-only integration
4. compare deterministic-only vs deterministic+ML OOS

### Status update (2026-02-26)
- Implemented leakage-safe labeling pipeline: `freqtrade/scripts/run-user-ml-labels.py` (+ wrapper module).
- Implemented ML walk-forward evaluator with calibration/coverage metrics and promotion-friendly gate summary: `freqtrade/scripts/run-user-ml-walkforward.py` (+ wrapper module).
- Implemented deterministic vs ML OOS comparator: `freqtrade/scripts/run-user-ml-overlay-compare.py` (+ wrapper module).
- Hardened planner integration so ML stays confidence-only:
  - default `freqai_overlay_enabled = False`
  - explicit advisory/strict gate mode (`freqai_overlay_gate_mode`)
  - plan diagnostics include raw/effective gate state and applied ML adjustments.
- Extended tuning protocol for optional ML overlay gates (`ml_overlay_gate`) with manifest defaults and strict promotion integration.
- Added dedicated Step-14 pytest coverage in `freqtrade/user_data/tests/test_ml_overlay_step14.py`.

---

# 21) Repo Files to Create (for Codex to target immediately)

## 21.1 Must-have docs/schemas
- `docs/GRID_MASTER_PLAN.md`  ← this file
- `docs/DECISION_REASON_CODES.md`
- `docs/REPLAN_POLICY_AND_MATERIALITY.md`
- `docs/ATOMIC_PLAN_HANDOFF.md`
- `docs/STRESS_REPLAY_PROFILES.md`
- `docs/TUNING_PROTOCOL_WALKFORWARD_PBO.md`
- `schemas/grid_plan.schema.json`
- `schemas/execution_cost_calibration.schema.json`
- `schemas/chaos_profile.schema.json`

## 21.2 Strongly recommended
- `core/enums.py` (or equivalent shared enum registry)
- `schemas/decision_log.schema.json`
- `schemas/event_log.schema.json`
- `experiments/manifest.yaml`
- `experiments/champions.json`
- `experiments/metrics_schema.json`

## 21.3 Core modules (target filenames; exact paths flexible)
- `planner/replan_policy.py`
- `planner/start_stability.py`
- `planner/volatility_policy_adapter.py`
- `risk/meta_drift_guard.py`
- `analytics/execution_cost_calibrator.py`
- `execution/capacity_guard.py`
- `io/atomic_json.py`
- `schemas/plan_signature.py`
- `sim/chaos_profiles.py`
- `data/data_quality_assessor.py`

---

# 22) Codex Working Rules (to reduce accidental regressions)

When asking Codex to implement anything from this file, always include:

1. **exact files to modify**
2. **what must not change**
3. **expected reason codes**
4. **schema fields to preserve/add**
5. **acceptance test(s)**
6. **determinism/no-repaint requirement**
7. **whether module is ON by default or OFF**
8. **whether behavior is advisory vs hard gate**

### Example prompt pattern
> Implement `planner/replan_policy.py` for `NOOP/SOFT/MATERIAL/HARD_STOP` classification using materiality thresholds from this plan. Do not change STOP logic, box builder, or TP/SL selection. Add plan diff logging fields and unit tests for deterministic classification.

---

# 23) Complexity Control Rule (Strategic Guardrail)

The best gains from this point forward come from:

- making the system harder to trick,
- making execution behavior more realistic,
- reducing churn and race-condition failures,
- making tuning harder to overfit,
- and making logs/explanations bulletproof.

**Do not add more signal modules before stabilizing the deterministic core + replan/handoff/testing pipeline.**

---

# 24) Audit Template (Fill This In During Repo Review)

Use this checklist block when auditing the repo:

## 24.1 Core status snapshot
- [ ] Deterministic core planner exists
- [ ] Simulator exists and matches planner decisions
- [ ] Executor (paper) exists
- [ ] Atomic plan write exists
- [ ] Idempotent plan apply exists
- [ ] Replan/materiality exists
- [ ] Start stability score exists
- [ ] Data quality health state exists
- [ ] Chaos replay exists
- [ ] Empirical cost calibration exists
- [ ] Meta drift guard exists
- [ ] Capacity guard exists
- [ ] Formal tuning workflow exists

## 24.2 Module status matrix
For each module M001..M1008 in Section 18, record:
- Status:
- File(s):
- Default toggle:
- Reason codes implemented:
- Tests present:
- Notes / gaps:

---

# 25) Final Notes

This master plan intentionally preserves:
- the original deterministic range/grid architecture,
- the rich module backlog (VP/FVG/OB/channels/CVD/etc.),
- and adds the missing high-ROI “glue”:
  - anti-churn replan policy,
  - atomic/idempotent handoff,
  - data quarantine,
  - drift kill-switch,
  - empirical cost feedback,
  - stress replay,
  - capacity capping,
  - formal anti-overfit tuning process.

This is the intended path to a system that is not only feature-rich, but **stable, testable, and production-credible**.

---

# 26) DONE / TODO Audit (Scope: lines 1-2185)

Audit date: **2026-02-26**  
Audit scope: **only** the original master plan body (`docs/GRID_MASTER_PLAN.md` lines 1-2185), matched against actual code/tests/scripts in this repo.

Status values used:
- `DONE`: implemented and wired in runnable code
- `PARTIAL`: implemented in part, but missing part of the documented contract
- `NOT_IMPLEMENTED`: not present yet
- `DOC_ONLY`: planning/governance text section (no direct code implementation target)

---

## 26.1 DONE

### 26.1.1 Section-by-section status for lines 1-2185

- `Section 0) How to Use This File` -> `DOC_ONLY`
- `Section 1) Purpose and Scope` -> `DOC_ONLY`
- `Section 2) System Architecture` -> `DONE` (Brain/Simulator/Executor present; ML overlay present as confidence-only)
- `Section 3) Global Invariants` -> `PARTIAL` (determinism + brain/sim parity largely implemented; full handoff/idempotency signature contract still incomplete)
- `Section 4) Core Data Model` -> `PARTIAL` (core plan payload exists; full Section 19 signature/schema completeness not finished)
- `Section 5) Planner Health State` -> `DONE`
- `Section 6) Planner Decision Loop` -> `DONE`
- `Section 7) Replan Policy + Materiality` -> `DONE`
- `Section 8) Global Start Stability Score` -> `DONE`
- `Section 9) Volatility Policy Adapter` -> `PARTIAL`
- `Section 10) Meta Drift Guard` -> `DONE`
- `Section 11) Phase-2 Regime Filters and Build Gates` -> `PARTIAL` (core set done; boom/doom still missing)
- `Section 12) Phase-3 Box Builder` -> `PARTIAL` (core done; specific sub-policies still missing)
- `Section 13) Phase-4 Grid Sizing/START/Targets/Risk` -> `DONE`
- `Section 14) Brain->Executor Handoff Contract` -> `PARTIAL` (atomic write done; full plan signature + idempotent consume contract incomplete)
- `Section 15) Monitoring/STOP/REBUILD Runtime Rails` -> `PARTIAL`
- `Section 16) Executor Design` -> `PARTIAL`
- `Section 17) Testing/Replay/Tuning/Anti-overfit` -> `PARTIAL`
- `Section 18) Module Registry` -> `PARTIAL` overall (mixed DONE/PARTIAL/NOT_IMPLEMENTED by module)
- `Section 19) Plan/State/Log Schemas` -> `PARTIAL` (schemas and key fields not fully complete)
- `Section 20) Implementation Sequence` -> `PARTIAL` (Steps 12/13/14 done; several earlier sequence expectations still partial)
- `Section 21) Repo Files to Create` -> `PARTIAL` (several files still missing)
- `Section 22) Codex Working Rules` -> `DOC_ONLY`
- `Section 23) Complexity Control Rule` -> `DOC_ONLY`
- `Section 24) Audit Template` -> `DOC_ONLY` (template remains as template)
- `Section 25) Final Notes` -> `DOC_ONLY`

### 26.1.2 Implementation sequence status (Section 20)

- `Step 1` -> `PARTIAL`
- `Step 2` -> `PARTIAL`
- `Step 3` -> `PARTIAL`
- `Step 4` -> `PARTIAL`
- `Step 5` -> `PARTIAL`
- `Step 6` -> `DONE`
- `Step 7` -> `DONE`
- `Step 8` -> `DONE`
- `Step 9` -> `PARTIAL`
- `Step 10` -> `PARTIAL`
- `Step 11` -> `PARTIAL`
- `Step 12` -> `DONE`
- `Step 13` -> `DONE`
- `Step 14` -> `DONE`

### 26.1.3 Module registry items that are DONE (complete list)

- `M001`, `M003`, `M004`, `M005`
- `M101`, `M102`, `M103`, `M104`, `M105`, `M106`, `M107`, `M108`, `M109`, `M110`, `M111`, `M112`
- `M201`, `M202`, `M203`, `M206`, `M207`, `M208`, `M210`, `M211`
- `M301`, `M302`, `M303`, `M304`, `M305`
- `M401`, `M402`, `M403`, `M405`
- `M501`, `M503`, `M504`
- `M602`, `M603`, `M604`, `M605`, `M607`
- `M701`
- `M801`, `M802`, `M803`, `M804`, `M806`
- `M901`, `M902`
- `M1001`, `M1002`, `M1007`, `M1008`

### 26.1.4 Section 21 file checklist that is DONE

- `docs/GRID_MASTER_PLAN.md`
- `docs/DECISION_REASON_CODES.md`
- `core/enums.py`
- `experiments/manifest.yaml`
- `experiments/champions.json`
- `experiments/metrics_schema.json`

---

## 26.2 TODO (ordered by importance)

### P0 (highest) - correctness contract and schema completion

1. Complete full Section 14/19 handoff contract:
   - missing required plan signature fields in published plan payloads:
     - `schema_version`
     - `planner_version`
     - `pair`
     - `plan_id`
     - `decision_seq`
     - `plan_hash`
     - `generated_at`
     - `valid_for_candle_ts`
     - `materiality_class`
     - `replan_decision`
     - `replan_reasons`
   - complete executor stale/duplicate rejection using signature (`plan_id`/`decision_seq`)
2. Create missing Section 21 must-have docs/schemas:
   - `docs/REPLAN_POLICY_AND_MATERIALITY.md`
   - `docs/ATOMIC_PLAN_HANDOFF.md`
   - `docs/STRESS_REPLAY_PROFILES.md`
   - `docs/TUNING_PROTOCOL_WALKFORWARD_PBO.md`
   - `schemas/grid_plan.schema.json`
   - `schemas/execution_cost_calibration.schema.json`
   - `schemas/chaos_profile.schema.json`
3. Create missing Section 21 strongly recommended schemas:
   - `schemas/decision_log.schema.json`
   - `schemas/event_log.schema.json`

### P1 (high) - missing/partial architecture modules from lines 1-2185

4. Create missing target module files listed in Section 21.3:
   - `planner/replan_policy.py`
   - `planner/start_stability.py`
   - `planner/volatility_policy_adapter.py`
   - `risk/meta_drift_guard.py`
   - `analytics/execution_cost_calibrator.py`
   - `execution/capacity_guard.py`
   - `io/atomic_json.py`
   - `schemas/plan_signature.py`
   - `sim/chaos_profiles.py`
   - `data/data_quality_assessor.py`
5. Complete chaos/stress perturbation harness contract from Sections 16/17 (`latency/spread shocks/partial fills/reject bursts/data gaps` as first-class profiles in replay path).
6. Complete strict golden replay and formal brain/simulator consistency suite coverage from Section 17.
7. Complete depth-aware dynamic capacity cap enforcement (not only hint ingestion) from Sections 16/18.
8. Complete full execution-cost lifecycle feedback loop (fill/order lifecycle standardization + calibration artifact discipline) from Sections 13/18.

### P2 (medium) - module registry remaining items (all non-DONE modules)

#### 26.2.1 Modules currently PARTIAL

- `M002` Atomic handoff + idempotency contract
- `M006` Volatility policy adapter
- `M007` Empirical execution cost calibration loop
- `M008` Stress/chaos replay harness
- `M009` Depth-aware capacity cap
- `M010` Enum registry + plan diff snapshots
- `M205` Minimum range length + breakout confirm bars
- `M209` Log-space quartiles + 1.386 extensions (log-space detail incomplete)
- `M213` Midline bias fallback (full policy incomplete)
- `M404` Protections layer (drawdown/protection extensions incomplete)
- `M406` Structured event taxonomy/bus contract
- `M502` POC alignment check strict behavior
- `M505` Micro-VAP bias/re-entry discipline completeness
- `M606` FVG-VP full module behavior
- `M702` Smart breakout channels full behavior
- `M703` Zig-zag channel enhancement full behavior
- `M805` Session high/low sweep + break-retest event behavior
- `M809` Buy-ratio micro-bias policy usage
- `M1003` Minimal order-flow metrics full module behavior
- `M1004` Atomic handoff duplicate-safe contract completeness
- `M1005` Empirical execution feedback loop completeness
- `M1006` Stress replay as standard validation completeness

#### 26.2.2 Modules currently NOT_IMPLEMENTED

- `M113` Boom & Doom impulse guard
- `M204` Percent-of-average width veto
- `M212` Fallback POC estimator contract
- `M306` Directional skip-one rule
- `M307` Next-rung ghost lines (UI)
- `M601` Lightweight OB module
- `M704` Liquidity sweeps module
- `M705` Sweep mode toggle (`Wick/Open`) module
- `M807` VAH/VAL quantile approximation fallback
- `M808` Average-of-basis with session H/L band candidates
- `M903` CVD spike + passive absorption module
- `M904` CVD divergence oscillator strong-score module
- `M905` SMA200/EMA directional variant trend filters
- `M906` CVD extension-line touch counter (UI)

### P3 (lower, but still in-scope from lines 1-2185)

9. Keep Section 24 audit template synchronized with Section 26 statuses after each implementation wave.
10. Keep Step sequencing notes in Section 20 updated as PARTIAL -> DONE transitions happen.

---

## 26.3 Full module registry status map (no exclusions)

- `M001` DONE
- `M002` PARTIAL
- `M003` DONE
- `M004` DONE
- `M005` DONE
- `M006` PARTIAL
- `M007` PARTIAL
- `M008` PARTIAL
- `M009` PARTIAL
- `M010` PARTIAL

- `M101` DONE
- `M102` DONE
- `M103` DONE
- `M104` DONE
- `M105` DONE
- `M106` DONE
- `M107` DONE
- `M108` DONE
- `M109` DONE
- `M110` DONE
- `M111` DONE
- `M112` DONE
- `M113` NOT_IMPLEMENTED

- `M201` DONE
- `M202` DONE
- `M203` DONE
- `M204` NOT_IMPLEMENTED
- `M205` PARTIAL
- `M206` DONE
- `M207` DONE
- `M208` DONE
- `M209` PARTIAL
- `M210` DONE
- `M211` DONE
- `M212` NOT_IMPLEMENTED
- `M213` PARTIAL

- `M301` DONE
- `M302` DONE
- `M303` DONE
- `M304` DONE
- `M305` DONE
- `M306` NOT_IMPLEMENTED
- `M307` NOT_IMPLEMENTED

- `M401` DONE
- `M402` DONE
- `M403` DONE
- `M404` PARTIAL
- `M405` DONE
- `M406` PARTIAL

- `M501` DONE
- `M502` PARTIAL
- `M503` DONE
- `M504` DONE
- `M505` PARTIAL

- `M601` NOT_IMPLEMENTED
- `M602` DONE
- `M603` DONE
- `M604` DONE
- `M605` DONE
- `M606` PARTIAL
- `M607` DONE

- `M701` DONE
- `M702` PARTIAL
- `M703` PARTIAL
- `M704` NOT_IMPLEMENTED
- `M705` NOT_IMPLEMENTED

- `M801` DONE
- `M802` DONE
- `M803` DONE
- `M804` DONE
- `M805` PARTIAL
- `M806` DONE
- `M807` NOT_IMPLEMENTED
- `M808` NOT_IMPLEMENTED
- `M809` PARTIAL

- `M901` DONE
- `M902` DONE
- `M903` NOT_IMPLEMENTED
- `M904` NOT_IMPLEMENTED
- `M905` NOT_IMPLEMENTED
- `M906` NOT_IMPLEMENTED

- `M1001` DONE
- `M1002` DONE
- `M1003` PARTIAL
- `M1004` PARTIAL
- `M1005` PARTIAL
- `M1006` PARTIAL
- `M1007` DONE
- `M1008` DONE

---
