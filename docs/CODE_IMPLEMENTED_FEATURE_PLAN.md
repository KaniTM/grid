# Code-Derived Implemented Feature Plan

This file is generated from current code only. It is intended as a clean implementation baseline for plan comparison/merge work.

- Generated: `2026-02-26T22:07:39.503473+00:00`
- Source scope: custom project modules + `freqtrade/user_data` code + schemas/tests.
- Excluded: upstream framework internals under `freqtrade/freqtrade/**`.

## 1) Source Coverage (All Code Files Scanned)

- Python files scanned: `48`
- Schema/config files scanned: `10`

### 1.1 Python Files

- `analytics/__init__.py`
- `analytics/execution_cost_calibrator.py`
- `core/atomic_json.py`
- `core/enums.py`
- `core/plan_signature.py`
- `core/schema_validation.py`
- `data/__init__.py`
- `data/data_quality_assessor.py`
- `execution/__init__.py`
- `execution/capacity_guard.py`
- `freqtrade/user_data/scripts/grid_executor_v1.py`
- `freqtrade/user_data/scripts/grid_simulator_v1.py`
- `freqtrade/user_data/scripts/regime_audit_v1.py`
- `freqtrade/user_data/scripts/user_regression_suite.py`
- `freqtrade/user_data/strategies/GridBrainV1.py`
- `freqtrade/user_data/strategies/GridBrainV1BaselineNoNeutral.py`
- `freqtrade/user_data/strategies/GridBrainV1ExpRouterFast.py`
- `freqtrade/user_data/strategies/GridBrainV1NeutralDiFilter.py`
- `freqtrade/user_data/strategies/GridBrainV1NeutralEligibilityOnly.py`
- `freqtrade/user_data/strategies/GridBrainV1NoFVG.py`
- `freqtrade/user_data/strategies/GridBrainV1NoPause.py`
- `freqtrade/user_data/strategies/sample_strategy.py`
- `freqtrade/user_data/tests/test_chaos_replay_harness.py`
- `freqtrade/user_data/tests/test_executor_hardening.py`
- `freqtrade/user_data/tests/test_liquidity_sweeps.py`
- `freqtrade/user_data/tests/test_meta_drift_replay.py`
- `freqtrade/user_data/tests/test_min_range_and_breakout_confirm.py`
- `freqtrade/user_data/tests/test_ml_overlay_step14.py`
- `freqtrade/user_data/tests/test_order_blocks.py`
- `freqtrade/user_data/tests/test_partial_module_completion.py`
- `freqtrade/user_data/tests/test_phase3_validation.py`
- `freqtrade/user_data/tests/test_replay_golden_consistency.py`
- `freqtrade/user_data/tests/test_stress_replay_standard_validation.py`
- `freqtrade/user_data/tests/test_tuning_protocol.py`
- `freqtrade_cli.py`
- `io/__init__.py`
- `io/atomic_json.py`
- `planner/__init__.py`
- `planner/replan_policy.py`
- `planner/start_stability.py`
- `planner/structure/__init__.py`
- `planner/structure/liquidity_sweeps.py`
- `planner/structure/order_blocks.py`
- `planner/volatility_policy_adapter.py`
- `risk/__init__.py`
- `risk/meta_drift_guard.py`
- `sim/__init__.py`
- `sim/chaos_profiles.py`

### 1.2 Schema/Config Files

- `experiments/champions.json`
- `experiments/manifest.yaml`
- `experiments/metrics_schema.json`
- `schemas/__init__.py`
- `schemas/chaos_profile.schema.json`
- `schemas/decision_log.schema.json`
- `schemas/event_log.schema.json`
- `schemas/execution_cost_calibration.schema.json`
- `schemas/grid_plan.schema.json`
- `schemas/plan_signature.py`

## 2) Implemented Runtime Feature Surface (Code-Derived)

### 2.1 Core Platform Contracts

- **Atomic JSON write/read utilities** with fsync-parent durability path (`core/atomic_json.py:12`, `core/atomic_json.py:32`).
- **Plan signature + material diff contract**: deterministic hash, changed-fields snapshot, signature field validation, expiry checks (`core/plan_signature.py:55`, `core/plan_signature.py:123`, `core/plan_signature.py:169`, `core/plan_signature.py:220`).
- **Schema validation layer** with cached schema loading and formatted errors (`core/schema_validation.py:25`, `core/schema_validation.py:38`).
- **Canonical reason/event taxonomy** implemented as enums (`core/enums.py:145`).

### 2.2 Planner Brain (`GridBrainV1Core`) — Implemented Capabilities

- **MTF deterministic signal pipeline** (15m base + 1h + 4h informative indicators) (`freqtrade/user_data/strategies/GridBrainV1.py:1117`, `freqtrade/user_data/strategies/GridBrainV1.py:1132`, `freqtrade/user_data/strategies/GridBrainV1.py:5931`).
- **Data-quality + planner-health control plane**: gaps/misalign/zero-volume checks, health state mapping, quarantine-aware gating (`freqtrade/user_data/strategies/GridBrainV1.py:1333`, `freqtrade/user_data/strategies/GridBrainV1.py:1750`).
- **Materiality-driven publish policy**: epoch throttling + hard-stop override + changed-fields snapshots (`freqtrade/user_data/strategies/GridBrainV1.py:1777`, `freqtrade/user_data/strategies/GridBrainV1.py:9178`).
- **Atomic handoff + idempotent plan write semantics**: signature seeding, dedupe by hash, latest + archive publish (`freqtrade/user_data/strategies/GridBrainV1.py:2742`, `freqtrade/user_data/strategies/GridBrainV1.py:2782`, `freqtrade/user_data/strategies/GridBrainV1.py:2789`).
- **Decision log + structured event bus** with schema validation and module/severity attribution (`freqtrade/user_data/strategies/GridBrainV1.py:2883`, `freqtrade/user_data/strategies/GridBrainV1.py:2915`, `freqtrade/user_data/strategies/GridBrainV1.py:2994`).
- **Regime router/mode state machine** with persistence/cooldown and inventory-safe handoff behavior (`freqtrade/user_data/strategies/GridBrainV1.py:2053`, `freqtrade/user_data/strategies/GridBrainV1.py:2373`).
- **Phase-2 gating stack**: ADX/BBW/EMA/rVol/7d + breakout freshness + os_dev + BBWP + squeeze + funding + HVP + stability aggregation (`freqtrade/user_data/strategies/GridBrainV1.py:6239`, `freqtrade/user_data/strategies/GridBrainV1.py:6394`, `freqtrade/user_data/strategies/GridBrainV1.py:7507`, `freqtrade/user_data/strategies/GridBrainV1.py:7805`).
- **Phase-3 box/range stack**: 24h box build, width policies, VRVP/MRVD, POC acceptance/alignment, straddle-veto utilities, overlap prune (`freqtrade/user_data/strategies/GridBrainV1.py:3104`, `freqtrade/user_data/strategies/GridBrainV1.py:3630`, `freqtrade/user_data/strategies/GridBrainV1.py:3702`, `freqtrade/user_data/strategies/GridBrainV1.py:3380`).
- **Phase-4 sizing/risk stack**: cost-aware sizing, empirical floor, N-bounds adapter, deterministic TP/SL selector with structural nudges (`freqtrade/user_data/strategies/GridBrainV1.py:4881`, `freqtrade/user_data/strategies/GridBrainV1.py:5067`, `freqtrade/user_data/strategies/GridBrainV1.py:5083`, `freqtrade/user_data/strategies/GridBrainV1.py:5158`, `freqtrade/user_data/strategies/GridBrainV1.py:5175`).
- **Phase-5 runtime rails**: STOP framework, reclaim/cooldown/min-runtime, drawdown/max-stops window, micro-reentry discipline (`freqtrade/user_data/strategies/GridBrainV1.py:7564`, `freqtrade/user_data/strategies/GridBrainV1.py:7906`, `freqtrade/user_data/strategies/GridBrainV1.py:5838`, `freqtrade/user_data/strategies/GridBrainV1.py:5869`, `freqtrade/user_data/strategies/GridBrainV1.py:5900`).
- **Structure/confluence modules integrated in brain**: micro-VAP, FVG stack + FVG-VP, CVD, smart channels, liquidity sweeps, order blocks, order-flow soft/hard gating (`freqtrade/user_data/strategies/GridBrainV1.py:4219`, `freqtrade/user_data/strategies/GridBrainV1.py:4358`, `freqtrade/user_data/strategies/GridBrainV1.py:5311`, `freqtrade/user_data/strategies/GridBrainV1.py:3831`, `freqtrade/user_data/strategies/GridBrainV1.py:5394`, `freqtrade/user_data/strategies/GridBrainV1.py:5704`, `freqtrade/user_data/strategies/GridBrainV1.py:5526`, `freqtrade/user_data/strategies/GridBrainV1.py:5779`).

### 2.3 GridBrain Config/Knob Surface (Extracted from Class Attributes)

#### General

- `INTERFACE_VERSION = 3` (`freqtrade/user_data/strategies/GridBrainV1.py:515`)
- `STOP_REASON_TREND_ADX = "STOP_TREND_ADX"` (`freqtrade/user_data/strategies/GridBrainV1.py:516`)
- `STOP_REASON_VOL_EXPANSION = "STOP_VOL_EXPANSION"` (`freqtrade/user_data/strategies/GridBrainV1.py:517`)
- `STOP_REASON_BOX_BREAK = "STOP_BOX_BREAK"` (`freqtrade/user_data/strategies/GridBrainV1.py:518`)
- `STOP_REASON_META_DRIFT_HARD = str(StopReason.STOP_META_DRIFT_HARD)` (`freqtrade/user_data/strategies/GridBrainV1.py:519`)

#### 4h : regime ADX

- `timeframe = "15m"` (`freqtrade/user_data/strategies/GridBrainV1.py:525`)
- `can_short = can_short: bool = False` (`freqtrade/user_data/strategies/GridBrainV1.py:526`)
- `minimal_roi = {"0": 0.0}` (`freqtrade/user_data/strategies/GridBrainV1.py:528`)
- `stoploss = -0.99` (`freqtrade/user_data/strategies/GridBrainV1.py:529`)
- `trailing_stop = False` (`freqtrade/user_data/strategies/GridBrainV1.py:530`)
- `process_only_new_candles = True` (`freqtrade/user_data/strategies/GridBrainV1.py:532`)
- `lookback_buffer = lookback_buffer: int = 32` (`freqtrade/user_data/strategies/GridBrainV1.py:533`)

#### startup will be computed based on the heaviest lookback + buffer

- `startup_candle_count = startup_candle_count: int = 1` (`freqtrade/user_data/strategies/GridBrainV1.py:536`)

#### Data quality enforcement (Section 4.2)

- `data_quality_expected_candle_seconds = data_quality_expected_candle_seconds: int = 900` (`freqtrade/user_data/strategies/GridBrainV1.py:539`)
- `data_quality_gap_multiplier = data_quality_gap_multiplier: float = 1.5` (`freqtrade/user_data/strategies/GridBrainV1.py:540`)
- `data_quality_max_stale_minutes = data_quality_max_stale_minutes: float = 60.0` (`freqtrade/user_data/strategies/GridBrainV1.py:541`)
- `data_quality_zero_volume_streak_bars = data_quality_zero_volume_streak_bars: int = 4` (`freqtrade/user_data/strategies/GridBrainV1.py:542`)

#### Materiality Before Churn thresholds (Section 3.6)

- `materiality_epoch_bars = materiality_epoch_bars: int = 2` (`freqtrade/user_data/strategies/GridBrainV1.py:545`)
- `materiality_box_mid_shift_max_step_frac = materiality_box_mid_shift_max_step_frac: float = 0.5` (`freqtrade/user_data/strategies/GridBrainV1.py:546`)
- `materiality_box_width_change_pct = materiality_box_width_change_pct: float = 5.0` (`freqtrade/user_data/strategies/GridBrainV1.py:547`)
- `materiality_tp_shift_max_step_frac = materiality_tp_shift_max_step_frac: float = 0.75` (`freqtrade/user_data/strategies/GridBrainV1.py:548`)
- `materiality_sl_shift_max_step_frac = materiality_sl_shift_max_step_frac: float = 0.75` (`freqtrade/user_data/strategies/GridBrainV1.py:549`)
- `poc_acceptance_enabled = poc_acceptance_enabled: bool = True` (`freqtrade/user_data/strategies/GridBrainV1.py:551`)
- `poc_acceptance_lookback_bars = poc_acceptance_lookback_bars: int = 8` (`freqtrade/user_data/strategies/GridBrainV1.py:552`)
- `poc_alignment_enabled = poc_alignment_enabled: bool = True` (`freqtrade/user_data/strategies/GridBrainV1.py:553`)
- `poc_alignment_strict_enabled = poc_alignment_strict_enabled: bool = True` (`freqtrade/user_data/strategies/GridBrainV1.py:554`)
- `poc_alignment_lookback_bars = poc_alignment_lookback_bars: int = 8` (`freqtrade/user_data/strategies/GridBrainV1.py:555`)
- `poc_alignment_max_step_diff = poc_alignment_max_step_diff: float = 1.0` (`freqtrade/user_data/strategies/GridBrainV1.py:556`)
- `poc_alignment_max_width_frac = poc_alignment_max_width_frac: float = 0.05` (`freqtrade/user_data/strategies/GridBrainV1.py:557`)

#### Box builder (15m)

- `box_lookback_24h_bars = 96     # 24h on 15m` (`freqtrade/user_data/strategies/GridBrainV1.py:561`)
- `box_lookback_48h_bars = 192    # 48h on 15m` (`freqtrade/user_data/strategies/GridBrainV1.py:562`)
- `box_lookback_18h_bars = 72` (`freqtrade/user_data/strategies/GridBrainV1.py:563`)
- `box_lookback_12h_bars = 48` (`freqtrade/user_data/strategies/GridBrainV1.py:564`)
- `extremes_7d_bars = 7 * 24 * 4  # 672` (`freqtrade/user_data/strategies/GridBrainV1.py:565`)
- `box_overlap_prune_threshold = 0.6` (`freqtrade/user_data/strategies/GridBrainV1.py:566`)
- `box_overlap_history = 4` (`freqtrade/user_data/strategies/GridBrainV1.py:567`)
- `box_band_overlap_required = 0.6` (`freqtrade/user_data/strategies/GridBrainV1.py:568`)
- `box_band_adx_allow = 25.0` (`freqtrade/user_data/strategies/GridBrainV1.py:569`)
- `box_band_rvol_allow = 1.2` (`freqtrade/user_data/strategies/GridBrainV1.py:570`)
- `box_envelope_ratio_max = 2.0` (`freqtrade/user_data/strategies/GridBrainV1.py:571`)
- `box_envelope_adx_threshold = 25.0` (`freqtrade/user_data/strategies/GridBrainV1.py:572`)
- `box_envelope_rvol_threshold = 1.2` (`freqtrade/user_data/strategies/GridBrainV1.py:573`)
- `session_box_pad_shrink_pct = 0.2` (`freqtrade/user_data/strategies/GridBrainV1.py:574`)

#### Structural breakout guard

- `breakout_lookback_bars = 14` (`freqtrade/user_data/strategies/GridBrainV1.py:577`)
- `breakout_block_bars = 20` (`freqtrade/user_data/strategies/GridBrainV1.py:578`)
- `breakout_override_allowed = True` (`freqtrade/user_data/strategies/GridBrainV1.py:579`)
- `breakout_straddle_step_buffer_frac = 0.25` (`freqtrade/user_data/strategies/GridBrainV1.py:580`)
- `breakout_reason_code = BlockReason.BLOCK_FRESH_BREAKOUT` (`freqtrade/user_data/strategies/GridBrainV1.py:581`)
- `min_range_len_bars = 20` (`freqtrade/user_data/strategies/GridBrainV1.py:582`)
- `breakout_confirm_bars = 2` (`freqtrade/user_data/strategies/GridBrainV1.py:583`)
- `breakout_confirm_buffer_mode = "step"  # step | atr | pct | abs` (`freqtrade/user_data/strategies/GridBrainV1.py:584`)
- `breakout_confirm_buffer_value = 1.0` (`freqtrade/user_data/strategies/GridBrainV1.py:585`)
- `atr_period_15m = 20` (`freqtrade/user_data/strategies/GridBrainV1.py:587`)
- `atr_pad_mult = 0.35` (`freqtrade/user_data/strategies/GridBrainV1.py:588`)
- `rsi_period_15m = 14` (`freqtrade/user_data/strategies/GridBrainV1.py:590`)
- `rsi_min = 40` (`freqtrade/user_data/strategies/GridBrainV1.py:591`)
- `rsi_max = 60` (`freqtrade/user_data/strategies/GridBrainV1.py:592`)

#### Regime gate (4h ADX)

- `adx_period = 14` (`freqtrade/user_data/strategies/GridBrainV1.py:595`)
- `adx_4h_max = 22` (`freqtrade/user_data/strategies/GridBrainV1.py:596`)

#### 1h gates

- `ema_fast = 50` (`freqtrade/user_data/strategies/GridBrainV1.py:599`)
- `ema_slow = 100` (`freqtrade/user_data/strategies/GridBrainV1.py:600`)
- `ema_dist_max_frac = 0.012  # 1.2%` (`freqtrade/user_data/strategies/GridBrainV1.py:601`)
- `bb_window = 20` (`freqtrade/user_data/strategies/GridBrainV1.py:603`)
- `bb_stds = 2.0` (`freqtrade/user_data/strategies/GridBrainV1.py:604`)
- `bbw_pct_lookback_1h = 252` (`freqtrade/user_data/strategies/GridBrainV1.py:605`)
- `bbw_1h_pct_max = 50.0` (`freqtrade/user_data/strategies/GridBrainV1.py:606`)
- `bbw_nonexp_lookback_bars = 3` (`freqtrade/user_data/strategies/GridBrainV1.py:607`)
- `bbw_nonexp_tolerance_frac = 0.01` (`freqtrade/user_data/strategies/GridBrainV1.py:608`)
- `context_7d_hard_veto = True` (`freqtrade/user_data/strategies/GridBrainV1.py:609`)
- `vol_sma_window = 20` (`freqtrade/user_data/strategies/GridBrainV1.py:611`)
- `vol_spike_mult = 1.5  # 1h volume <= 1.5 * SMA20` (`freqtrade/user_data/strategies/GridBrainV1.py:612`)
- `rvol_window_15m = 20` (`freqtrade/user_data/strategies/GridBrainV1.py:613`)
- `rvol_15m_max = 1.5` (`freqtrade/user_data/strategies/GridBrainV1.py:614`)

#### VRVP (fixed-window volume profile)

- `vrvp_lookback_bars = 96` (`freqtrade/user_data/strategies/GridBrainV1.py:617`)
- `vrvp_bins = 48` (`freqtrade/user_data/strategies/GridBrainV1.py:618`)
- `vrvp_value_area_pct = 0.70` (`freqtrade/user_data/strategies/GridBrainV1.py:619`)
- `vrvp_poc_outside_box_max_frac = 0.005` (`freqtrade/user_data/strategies/GridBrainV1.py:620`)
- `vrvp_max_box_shift_frac = 0.005` (`freqtrade/user_data/strategies/GridBrainV1.py:621`)
- `vrvp_reject_if_still_outside = True` (`freqtrade/user_data/strategies/GridBrainV1.py:622`)
- `fallback_poc_estimator_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:623`)
- `fallback_poc_lookback_bars = 96` (`freqtrade/user_data/strategies/GridBrainV1.py:624`)

#### BBWP + squeeze gates

- `bbwp_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:627`)
- `bbwp_lookback_s = 252  # 15m` (`freqtrade/user_data/strategies/GridBrainV1.py:628`)
- `bbwp_lookback_m = 252  # 1h` (`freqtrade/user_data/strategies/GridBrainV1.py:629`)
- `bbwp_lookback_l = 252  # 4h` (`freqtrade/user_data/strategies/GridBrainV1.py:630`)
- `bbwp_s_max = 35.0` (`freqtrade/user_data/strategies/GridBrainV1.py:631`)
- `bbwp_m_max = 50.0` (`freqtrade/user_data/strategies/GridBrainV1.py:632`)
- `bbwp_l_max = 60.0` (`freqtrade/user_data/strategies/GridBrainV1.py:633`)
- `bbwp_veto_pct = 90.0` (`freqtrade/user_data/strategies/GridBrainV1.py:634`)
- `bbwp_cooloff_trigger_pct = 98.0` (`freqtrade/user_data/strategies/GridBrainV1.py:635`)
- `bbwp_cooloff_release_s = 50.0` (`freqtrade/user_data/strategies/GridBrainV1.py:636`)
- `bbwp_cooloff_release_m = 60.0` (`freqtrade/user_data/strategies/GridBrainV1.py:637`)
- `bbwp_nonexp_bars = 3` (`freqtrade/user_data/strategies/GridBrainV1.py:638`)
- `squeeze_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:639`)
- `squeeze_require_on_1h = False` (`freqtrade/user_data/strategies/GridBrainV1.py:640`)
- `squeeze_momentum_block_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:641`)
- `squeeze_tp_nudge_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:642`)
- `squeeze_tp_nudge_step_multiple = 0.5` (`freqtrade/user_data/strategies/GridBrainV1.py:643`)
- `kc_atr_mult = 1.5` (`freqtrade/user_data/strategies/GridBrainV1.py:644`)

#### Optional strictness gates

- `band_slope_veto_enabled = False` (`freqtrade/user_data/strategies/GridBrainV1.py:647`)
- `band_slope_veto_bars = 20` (`freqtrade/user_data/strategies/GridBrainV1.py:648`)
- `band_slope_veto_pct = 0.0035` (`freqtrade/user_data/strategies/GridBrainV1.py:649`)
- `drift_slope_veto_enabled = False` (`freqtrade/user_data/strategies/GridBrainV1.py:650`)
- `excursion_asymmetry_veto_enabled = False` (`freqtrade/user_data/strategies/GridBrainV1.py:651`)
- `excursion_asymmetry_min_ratio = 0.7` (`freqtrade/user_data/strategies/GridBrainV1.py:652`)
- `excursion_asymmetry_max_ratio = 1.5` (`freqtrade/user_data/strategies/GridBrainV1.py:653`)
- `hvp_enabled = False` (`freqtrade/user_data/strategies/GridBrainV1.py:654`)
- `hvp_lookback_bars = 32` (`freqtrade/user_data/strategies/GridBrainV1.py:655`)
- `hvp_sma_bars = 8` (`freqtrade/user_data/strategies/GridBrainV1.py:656`)
- `funding_filter_enabled = False` (`freqtrade/user_data/strategies/GridBrainV1.py:657`)
- `funding_filter_pct = 0.0005` (`freqtrade/user_data/strategies/GridBrainV1.py:658`)

#### instrumentation lookbacks

- `instrumentation_er_lookback = 20` (`freqtrade/user_data/strategies/GridBrainV1.py:661`)
- `instrumentation_chop_lookback = 20` (`freqtrade/user_data/strategies/GridBrainV1.py:662`)
- `instrumentation_di_flip_lookback = 50` (`freqtrade/user_data/strategies/GridBrainV1.py:663`)
- `instrumentation_wickiness_lookback = 50` (`freqtrade/user_data/strategies/GridBrainV1.py:664`)
- `instrumentation_containment_lookback = 96` (`freqtrade/user_data/strategies/GridBrainV1.py:665`)
- `instrumentation_atr_pct_percentile = 10.0` (`freqtrade/user_data/strategies/GridBrainV1.py:666`)
- `instrumentation_atr_pct_lookback = 96` (`freqtrade/user_data/strategies/GridBrainV1.py:667`)

#### os_dev regime state

- `os_dev_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:670`)
- `os_dev_n_strike = 2` (`freqtrade/user_data/strategies/GridBrainV1.py:671`)
- `os_dev_range_band = 0.75` (`freqtrade/user_data/strategies/GridBrainV1.py:672`)
- `os_dev_persist_bars = 24` (`freqtrade/user_data/strategies/GridBrainV1.py:673`)
- `os_dev_rvol_max = 1.2` (`freqtrade/user_data/strategies/GridBrainV1.py:674`)
- `os_dev_history_bars = 960` (`freqtrade/user_data/strategies/GridBrainV1.py:675`)

#### Micro-VAP + HVN/LVN

- `micro_vap_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:678`)
- `micro_vap_lookback_bars = 96` (`freqtrade/user_data/strategies/GridBrainV1.py:679`)
- `micro_vap_bins = 64` (`freqtrade/user_data/strategies/GridBrainV1.py:680`)
- `micro_hvn_quantile = 0.80` (`freqtrade/user_data/strategies/GridBrainV1.py:681`)
- `micro_lvn_quantile = 0.20` (`freqtrade/user_data/strategies/GridBrainV1.py:682`)
- `micro_extrema_count = 6` (`freqtrade/user_data/strategies/GridBrainV1.py:683`)
- `micro_lvn_corridor_steps = 1.0` (`freqtrade/user_data/strategies/GridBrainV1.py:684`)
- `micro_void_slope_threshold = 0.55` (`freqtrade/user_data/strategies/GridBrainV1.py:685`)

#### FVG stack (Defensive + IMFVG + Session FVG)

- `fvg_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:688`)
- `fvg_lookback_bars = 192` (`freqtrade/user_data/strategies/GridBrainV1.py:689`)
- `fvg_min_gap_atr = 0.05` (`freqtrade/user_data/strategies/GridBrainV1.py:690`)
- `fvg_straddle_veto_steps = 0.75` (`freqtrade/user_data/strategies/GridBrainV1.py:691`)
- `fvg_position_avg_count = 8` (`freqtrade/user_data/strategies/GridBrainV1.py:692`)
- `imfvg_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:694`)
- `imfvg_mitigated_relax = True` (`freqtrade/user_data/strategies/GridBrainV1.py:695`)
- `defensive_fvg_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:697`)
- `defensive_fvg_min_gap_atr = 0.20` (`freqtrade/user_data/strategies/GridBrainV1.py:698`)
- `defensive_fvg_body_frac = 0.55` (`freqtrade/user_data/strategies/GridBrainV1.py:699`)
- `defensive_fvg_fresh_bars = 16` (`freqtrade/user_data/strategies/GridBrainV1.py:700`)
- `session_fvg_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:702`)
- `session_fvg_inside_gate = True` (`freqtrade/user_data/strategies/GridBrainV1.py:703`)
- `session_fvg_pause_bars = 0` (`freqtrade/user_data/strategies/GridBrainV1.py:704`)

#### MRVD (multi-range volume distribution: day/week/month)

- `mrvd_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:707`)
- `mrvd_bins = 64` (`freqtrade/user_data/strategies/GridBrainV1.py:708`)
- `mrvd_value_area_pct = 0.70` (`freqtrade/user_data/strategies/GridBrainV1.py:709`)
- `mrvd_day_lookback_bars = 96         # 1 day on 15m` (`freqtrade/user_data/strategies/GridBrainV1.py:710`)
- `mrvd_week_lookback_bars = 7 * 96    # 1 week on 15m` (`freqtrade/user_data/strategies/GridBrainV1.py:711`)
- `mrvd_month_lookback_bars = 30 * 96  # 30 days on 15m (falls back to available bars)` (`freqtrade/user_data/strategies/GridBrainV1.py:712`)
- `mrvd_required_overlap_count = 2     # >= 2/3 periods` (`freqtrade/user_data/strategies/GridBrainV1.py:713`)
- `mrvd_va_overlap_min_frac = 0.10` (`freqtrade/user_data/strategies/GridBrainV1.py:714`)
- `mrvd_near_poc_steps = 1.0` (`freqtrade/user_data/strategies/GridBrainV1.py:715`)
- `mrvd_drift_guard_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:716`)
- `mrvd_drift_guard_steps = 0.75` (`freqtrade/user_data/strategies/GridBrainV1.py:717`)

#### CVD (divergence + BOS nudges)

- `cvd_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:720`)
- `cvd_lookback_bars = 192` (`freqtrade/user_data/strategies/GridBrainV1.py:721`)
- `cvd_pivot_left = 3` (`freqtrade/user_data/strategies/GridBrainV1.py:722`)
- `cvd_pivot_right = 3` (`freqtrade/user_data/strategies/GridBrainV1.py:723`)
- `cvd_divergence_max_age_bars = 64` (`freqtrade/user_data/strategies/GridBrainV1.py:724`)
- `cvd_near_value_steps = 1.0` (`freqtrade/user_data/strategies/GridBrainV1.py:725`)
- `cvd_bos_lookback = 20` (`freqtrade/user_data/strategies/GridBrainV1.py:726`)
- `cvd_bos_freeze_bars = 4` (`freqtrade/user_data/strategies/GridBrainV1.py:727`)
- `cvd_rung_bias_strength = 0.35` (`freqtrade/user_data/strategies/GridBrainV1.py:728`)

#### FreqAI confidence overlay (soft nudges; deterministic loop remains primary)

- `freqai_overlay_enabled = False` (`freqtrade/user_data/strategies/GridBrainV1.py:731`)
- `freqai_overlay_gate_mode = "advisory"  # advisory | strict` (`freqtrade/user_data/strategies/GridBrainV1.py:732`)
- `freqai_overlay_strict_predict = False` (`freqtrade/user_data/strategies/GridBrainV1.py:733`)
- `freqai_overlay_confidence_min = 0.55` (`freqtrade/user_data/strategies/GridBrainV1.py:734`)
- `freqai_overlay_breakout_scale = 0.02` (`freqtrade/user_data/strategies/GridBrainV1.py:735`)
- `freqai_overlay_breakout_quick_tp_thresh = 0.70` (`freqtrade/user_data/strategies/GridBrainV1.py:736`)
- `freqai_overlay_rung_edge_cut_max = 0.45` (`freqtrade/user_data/strategies/GridBrainV1.py:737`)

#### Rung density bias (executor/simulator consume these weights)

- `rung_weight_hvn_boost = 1.0` (`freqtrade/user_data/strategies/GridBrainV1.py:740`)
- `rung_weight_lvn_penalty = 0.40` (`freqtrade/user_data/strategies/GridBrainV1.py:741`)
- `rung_weight_min = 0.20` (`freqtrade/user_data/strategies/GridBrainV1.py:742`)
- `rung_weight_max = 3.00` (`freqtrade/user_data/strategies/GridBrainV1.py:743`)

#### Net target per step (>=0.40%), gross = net + fee + spread

- `target_net_step_pct = 0.0040` (`freqtrade/user_data/strategies/GridBrainV1.py:747`)
- `est_fee_pct = 0.0020     # default 0.20% (tweak per exchange/VIP)` (`freqtrade/user_data/strategies/GridBrainV1.py:748`)
- `est_spread_pct = 0.0005  # default 0.05% majors` (`freqtrade/user_data/strategies/GridBrainV1.py:749`)
- `majors_gross_step_floor_pct = 0.0065` (`freqtrade/user_data/strategies/GridBrainV1.py:750`)
- `n_min = 6` (`freqtrade/user_data/strategies/GridBrainV1.py:751`)
- `n_max = 12` (`freqtrade/user_data/strategies/GridBrainV1.py:752`)
- `n_volatility_adapter_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:753`)
- `n_volatility_adapter_strength = 1.0` (`freqtrade/user_data/strategies/GridBrainV1.py:754`)
- `volatility_min_step_buffer_bps = 0.0` (`freqtrade/user_data/strategies/GridBrainV1.py:755`)

#### Empirical cost calibration (Section 13.2).

- `empirical_cost_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:758`)
- `empirical_cost_window = 256` (`freqtrade/user_data/strategies/GridBrainV1.py:759`)
- `empirical_cost_min_samples = 24` (`freqtrade/user_data/strategies/GridBrainV1.py:760`)
- `empirical_cost_stale_bars = 96` (`freqtrade/user_data/strategies/GridBrainV1.py:761`)
- `empirical_cost_percentile = 90.0` (`freqtrade/user_data/strategies/GridBrainV1.py:762`)
- `empirical_cost_conservative_mode = True` (`freqtrade/user_data/strategies/GridBrainV1.py:763`)
- `empirical_cost_require_live_samples = True` (`freqtrade/user_data/strategies/GridBrainV1.py:764`)
- `empirical_cost_min_live_samples = 0` (`freqtrade/user_data/strategies/GridBrainV1.py:765`)
- `empirical_spread_proxy_scale = 0.10` (`freqtrade/user_data/strategies/GridBrainV1.py:766`)
- `empirical_adverse_selection_scale = 0.25` (`freqtrade/user_data/strategies/GridBrainV1.py:767`)
- `empirical_retry_penalty_pct = 0.0010` (`freqtrade/user_data/strategies/GridBrainV1.py:768`)
- `empirical_missed_fill_penalty_pct = 0.0010` (`freqtrade/user_data/strategies/GridBrainV1.py:769`)
- `empirical_cost_floor_min_pct = 0.0` (`freqtrade/user_data/strategies/GridBrainV1.py:770`)
- `execution_cost_artifact_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:771`)
- `execution_cost_artifact_dir = "artifacts/execution_cost"` (`freqtrade/user_data/strategies/GridBrainV1.py:772`)
- `execution_cost_artifact_filename = "execution_cost_calibration.latest.json"` (`freqtrade/user_data/strategies/GridBrainV1.py:773`)
- `execution_cost_artifact_max_age_minutes = 180.0` (`freqtrade/user_data/strategies/GridBrainV1.py:774`)

#### Width constraints for the box

- `min_width_pct = 0.035  # 3.5%` (`freqtrade/user_data/strategies/GridBrainV1.py:777`)
- `max_width_pct = 0.060  # 6.0%` (`freqtrade/user_data/strategies/GridBrainV1.py:778`)
- `box_width_avg_veto_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:779`)
- `box_width_avg_veto_lookback = 20` (`freqtrade/user_data/strategies/GridBrainV1.py:780`)
- `box_width_avg_veto_min_samples = 5` (`freqtrade/user_data/strategies/GridBrainV1.py:781`)
- `box_width_avg_veto_max_ratio = 1.20` (`freqtrade/user_data/strategies/GridBrainV1.py:782`)

#### Stop rules (15m)

- `stop_confirm_bars = 2` (`freqtrade/user_data/strategies/GridBrainV1.py:785`)
- `fast_stop_step_multiple = 1.0  # 1 * step beyond edge` (`freqtrade/user_data/strategies/GridBrainV1.py:786`)
- `range_shift_stop_pct = 0.007   # 0.7% mid shift vs previous plan` (`freqtrade/user_data/strategies/GridBrainV1.py:787`)
- `tp_step_multiple = 0.75` (`freqtrade/user_data/strategies/GridBrainV1.py:788`)
- `sl_step_multiple = 1.0` (`freqtrade/user_data/strategies/GridBrainV1.py:789`)
- `reclaim_hours = 4.0` (`freqtrade/user_data/strategies/GridBrainV1.py:790`)
- `cooldown_minutes = 90` (`freqtrade/user_data/strategies/GridBrainV1.py:791`)
- `min_runtime_hours = 3.0` (`freqtrade/user_data/strategies/GridBrainV1.py:792`)
- `neutral_stop_adx_bars = 3` (`freqtrade/user_data/strategies/GridBrainV1.py:793`)
- `neutral_box_break_bars = 2` (`freqtrade/user_data/strategies/GridBrainV1.py:794`)
- `neutral_box_break_step_multiple = 1.0` (`freqtrade/user_data/strategies/GridBrainV1.py:795`)
- `drawdown_guard_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:796`)
- `drawdown_guard_lookback_bars = 96` (`freqtrade/user_data/strategies/GridBrainV1.py:797`)
- `drawdown_guard_max_pct = 0.030` (`freqtrade/user_data/strategies/GridBrainV1.py:798`)
- `max_stops_window_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:799`)
- `max_stops_window_minutes = 360` (`freqtrade/user_data/strategies/GridBrainV1.py:800`)
- `max_stops_window_count = 4` (`freqtrade/user_data/strategies/GridBrainV1.py:801`)

#### Gate tuning profile (START gating debug/tune helper)

- `gate_profile = "strict"  # strict | balanced | aggressive` (`freqtrade/user_data/strategies/GridBrainV1.py:804`)
- `start_min_gate_pass_ratio = 1.0  # keep 1.0 for strict all-gates behavior` (`freqtrade/user_data/strategies/GridBrainV1.py:805`)
- `start_stability_min_score = 1.0` (`freqtrade/user_data/strategies/GridBrainV1.py:806`)
- `start_stability_k_fraction = 1.0` (`freqtrade/user_data/strategies/GridBrainV1.py:807`)
- `start_box_position_guard_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:808`)
- `start_box_position_min_frac = 0.35` (`freqtrade/user_data/strategies/GridBrainV1.py:809`)
- `start_box_position_max_frac = 0.65` (`freqtrade/user_data/strategies/GridBrainV1.py:810`)
- `basis_cross_confirm_enabled = False` (`freqtrade/user_data/strategies/GridBrainV1.py:811`)
- `capacity_hint_path = ""` (`freqtrade/user_data/strategies/GridBrainV1.py:812`)
- `capacity_hint_hard_block = False` (`freqtrade/user_data/strategies/GridBrainV1.py:813`)

#### Planner health / meta drift / runtime rails.

- `planner_health_quarantine_on_gap = True` (`freqtrade/user_data/strategies/GridBrainV1.py:816`)
- `planner_health_quarantine_on_misalign = True` (`freqtrade/user_data/strategies/GridBrainV1.py:817`)
- `meta_drift_soft_block_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:818`)
- `meta_drift_soft_block_steps = 0.75` (`freqtrade/user_data/strategies/GridBrainV1.py:819`)
- `meta_drift_guard_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:820`)
- `meta_drift_guard_window = 256` (`freqtrade/user_data/strategies/GridBrainV1.py:821`)
- `meta_drift_guard_min_samples = 24` (`freqtrade/user_data/strategies/GridBrainV1.py:822`)
- `meta_drift_guard_smoothing_alpha = 0.20` (`freqtrade/user_data/strategies/GridBrainV1.py:823`)
- `meta_drift_guard_eps = 1e-6` (`freqtrade/user_data/strategies/GridBrainV1.py:824`)
- `meta_drift_guard_z_soft = 2.5` (`freqtrade/user_data/strategies/GridBrainV1.py:825`)
- `meta_drift_guard_z_hard = 4.0` (`freqtrade/user_data/strategies/GridBrainV1.py:826`)
- `meta_drift_guard_cusum_k_sigma = 0.25` (`freqtrade/user_data/strategies/GridBrainV1.py:827`)
- `meta_drift_guard_cusum_soft = 4.0` (`freqtrade/user_data/strategies/GridBrainV1.py:828`)
- `meta_drift_guard_cusum_hard = 7.0` (`freqtrade/user_data/strategies/GridBrainV1.py:829`)
- `meta_drift_guard_ph_delta_sigma = 0.10` (`freqtrade/user_data/strategies/GridBrainV1.py:830`)
- `meta_drift_guard_ph_soft = 4.0` (`freqtrade/user_data/strategies/GridBrainV1.py:831`)
- `meta_drift_guard_ph_hard = 7.0` (`freqtrade/user_data/strategies/GridBrainV1.py:832`)
- `meta_drift_guard_soft_min_channels = 1` (`freqtrade/user_data/strategies/GridBrainV1.py:833`)
- `meta_drift_guard_hard_min_channels = 2` (`freqtrade/user_data/strategies/GridBrainV1.py:834`)
- `meta_drift_guard_cooldown_extend_minutes = 120` (`freqtrade/user_data/strategies/GridBrainV1.py:835`)
- `meta_drift_guard_spread_proxy_scale = 0.10` (`freqtrade/user_data/strategies/GridBrainV1.py:836`)
- `breakout_idle_reclaim_on_fresh = True` (`freqtrade/user_data/strategies/GridBrainV1.py:837`)
- `hvp_quiet_exit_bias_enabled = False` (`freqtrade/user_data/strategies/GridBrainV1.py:838`)
- `hvp_quiet_exit_step_multiple = 0.5` (`freqtrade/user_data/strategies/GridBrainV1.py:839`)

#### Regime router (intraday / neutral_choppy / swing / pause).

- `regime_router_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:842`)
- `regime_router_default_mode = "intraday"  # intraday | neutral_choppy | swing | pause` (`freqtrade/user_data/strategies/GridBrainV1.py:843`)
- `regime_router_force_mode = ""  # empty for auto, else intraday | neutral_choppy | swing | pause` (`freqtrade/user_data/strategies/GridBrainV1.py:844`)
- `regime_router_switch_persist_bars = 4` (`freqtrade/user_data/strategies/GridBrainV1.py:845`)
- `regime_router_switch_cooldown_bars = 6` (`freqtrade/user_data/strategies/GridBrainV1.py:846`)
- `regime_router_switch_margin = 1.0` (`freqtrade/user_data/strategies/GridBrainV1.py:847`)
- `regime_router_allow_pause = True` (`freqtrade/user_data/strategies/GridBrainV1.py:848`)
- `regime_router_score_enter = 0.7` (`freqtrade/user_data/strategies/GridBrainV1.py:849`)
- `regime_router_score_exit = 0.55` (`freqtrade/user_data/strategies/GridBrainV1.py:850`)
- `regime_router_score_persistence_bars = 4` (`freqtrade/user_data/strategies/GridBrainV1.py:851`)
- `regime_router_score_artifact_run_id = ""` (`freqtrade/user_data/strategies/GridBrainV1.py:852`)
- `regime_router_score_artifact_dir = "artifacts/regime_bands"` (`freqtrade/user_data/strategies/GridBrainV1.py:853`)
- `regime_router_score_artifact_file = "neutral_bands.json"` (`freqtrade/user_data/strategies/GridBrainV1.py:854`)
- `neutral_adx_enter_pct = 55.0` (`freqtrade/user_data/strategies/GridBrainV1.py:855`)
- `neutral_adx_exit_pct = 65.0` (`freqtrade/user_data/strategies/GridBrainV1.py:856`)
- `neutral_adx_veto_pct = 70.0` (`freqtrade/user_data/strategies/GridBrainV1.py:857`)
- `neutral_bbwp_enter_min_pct = 20.0` (`freqtrade/user_data/strategies/GridBrainV1.py:858`)
- `neutral_bbwp_enter_max_pct = 60.0` (`freqtrade/user_data/strategies/GridBrainV1.py:859`)
- `neutral_bbwp_veto_pct = 85.0` (`freqtrade/user_data/strategies/GridBrainV1.py:860`)
- `neutral_bbwp_dead_pct = 10.0` (`freqtrade/user_data/strategies/GridBrainV1.py:861`)
- `neutral_atr_pct_min = 0.15` (`freqtrade/user_data/strategies/GridBrainV1.py:862`)
- `neutral_spread_bps_max = 10.0` (`freqtrade/user_data/strategies/GridBrainV1.py:863`)
- `neutral_spread_step_frac = 0.15` (`freqtrade/user_data/strategies/GridBrainV1.py:864`)

#### Neutral persistence knobs (from audit recommendations)

- `neutral_enter_persist_min = 10` (`freqtrade/user_data/strategies/GridBrainV1.py:867`)
- `neutral_enter_persist_max = 60` (`freqtrade/user_data/strategies/GridBrainV1.py:868`)
- `neutral_exit_persist_ratio = 0.5` (`freqtrade/user_data/strategies/GridBrainV1.py:869`)
- `neutral_cooldown_multiplier = 2.0` (`freqtrade/user_data/strategies/GridBrainV1.py:870`)
- `neutral_min_runtime_hours_offset = 0.0` (`freqtrade/user_data/strategies/GridBrainV1.py:871`)
- `neutral_persistence_default_enter = 24` (`freqtrade/user_data/strategies/GridBrainV1.py:872`)
- `neutral_grid_levels_ratio = 0.6` (`freqtrade/user_data/strategies/GridBrainV1.py:873`)
- `neutral_grid_budget_ratio = 0.5` (`freqtrade/user_data/strategies/GridBrainV1.py:874`)
- `neutral_rebuild_shift_pct = 0.007` (`freqtrade/user_data/strategies/GridBrainV1.py:875`)
- `neutral_rebuild_max_bars = 6` (`freqtrade/user_data/strategies/GridBrainV1.py:876`)
- `regime_threshold_profile = "manual"  # manual | research_v1` (`freqtrade/user_data/strategies/GridBrainV1.py:894`)

#### Intraday (scalper-ish) mode thresholds.

- `intraday_adx_enter_max = 22.0` (`freqtrade/user_data/strategies/GridBrainV1.py:897`)
- `intraday_adx_exit_min = 30.0` (`freqtrade/user_data/strategies/GridBrainV1.py:898`)
- `intraday_adx_rising_bars = 3` (`freqtrade/user_data/strategies/GridBrainV1.py:899`)
- `intraday_bbw_1h_pct_max = 30.0` (`freqtrade/user_data/strategies/GridBrainV1.py:900`)
- `intraday_bbw_nonexp_lookback_bars = 3` (`freqtrade/user_data/strategies/GridBrainV1.py:901`)
- `intraday_bbw_nonexp_tolerance_frac = 0.01` (`freqtrade/user_data/strategies/GridBrainV1.py:902`)
- `intraday_ema_dist_max_frac = 0.005` (`freqtrade/user_data/strategies/GridBrainV1.py:903`)
- `intraday_vol_spike_mult = 1.2` (`freqtrade/user_data/strategies/GridBrainV1.py:904`)
- `intraday_rvol_15m_max = 1.2` (`freqtrade/user_data/strategies/GridBrainV1.py:905`)
- `intraday_bbwp_s_enter_low = 15.0` (`freqtrade/user_data/strategies/GridBrainV1.py:906`)
- `intraday_bbwp_s_enter_high = 45.0` (`freqtrade/user_data/strategies/GridBrainV1.py:907`)
- `intraday_bbwp_m_enter_low = 10.0` (`freqtrade/user_data/strategies/GridBrainV1.py:908`)
- `intraday_bbwp_m_enter_high = 55.0` (`freqtrade/user_data/strategies/GridBrainV1.py:909`)
- `intraday_bbwp_l_enter_low = 10.0` (`freqtrade/user_data/strategies/GridBrainV1.py:910`)
- `intraday_bbwp_l_enter_high = 65.0` (`freqtrade/user_data/strategies/GridBrainV1.py:911`)
- `intraday_bbwp_stop_high = 90.0` (`freqtrade/user_data/strategies/GridBrainV1.py:912`)
- `intraday_atr_pct_max = 0.015` (`freqtrade/user_data/strategies/GridBrainV1.py:913`)
- `intraday_os_dev_persist_bars = 24` (`freqtrade/user_data/strategies/GridBrainV1.py:914`)
- `intraday_os_dev_rvol_max = 1.2` (`freqtrade/user_data/strategies/GridBrainV1.py:915`)

#### Swing range mode thresholds.

- `swing_adx_enter_max = 28.0` (`freqtrade/user_data/strategies/GridBrainV1.py:918`)
- `swing_adx_exit_min = 35.0` (`freqtrade/user_data/strategies/GridBrainV1.py:919`)
- `swing_adx_rising_bars = 2` (`freqtrade/user_data/strategies/GridBrainV1.py:920`)
- `swing_bbw_1h_pct_max = 40.0` (`freqtrade/user_data/strategies/GridBrainV1.py:921`)
- `swing_bbw_nonexp_lookback_bars = 3` (`freqtrade/user_data/strategies/GridBrainV1.py:922`)
- `swing_bbw_nonexp_tolerance_frac = 0.015` (`freqtrade/user_data/strategies/GridBrainV1.py:923`)
- `swing_ema_dist_max_frac = 0.010` (`freqtrade/user_data/strategies/GridBrainV1.py:924`)
- `swing_vol_spike_mult = 1.8` (`freqtrade/user_data/strategies/GridBrainV1.py:925`)
- `swing_rvol_15m_max = 1.8` (`freqtrade/user_data/strategies/GridBrainV1.py:926`)
- `swing_bbwp_s_enter_low = 10.0` (`freqtrade/user_data/strategies/GridBrainV1.py:927`)
- `swing_bbwp_s_enter_high = 65.0` (`freqtrade/user_data/strategies/GridBrainV1.py:928`)
- `swing_bbwp_m_enter_low = 10.0` (`freqtrade/user_data/strategies/GridBrainV1.py:929`)
- `swing_bbwp_m_enter_high = 65.0` (`freqtrade/user_data/strategies/GridBrainV1.py:930`)
- `swing_bbwp_l_enter_low = 10.0` (`freqtrade/user_data/strategies/GridBrainV1.py:931`)
- `swing_bbwp_l_enter_high = 75.0` (`freqtrade/user_data/strategies/GridBrainV1.py:932`)
- `swing_bbwp_stop_high = 93.0` (`freqtrade/user_data/strategies/GridBrainV1.py:933`)
- `swing_atr_pct_max = 0.030` (`freqtrade/user_data/strategies/GridBrainV1.py:934`)
- `swing_os_dev_persist_bars = 12` (`freqtrade/user_data/strategies/GridBrainV1.py:935`)
- `swing_os_dev_rvol_max = 1.8` (`freqtrade/user_data/strategies/GridBrainV1.py:936`)

#### Backtest/walk-forward: write full per-candle plan history for true replay.

- `emit_per_candle_history_backtest = True` (`freqtrade/user_data/strategies/GridBrainV1.py:939`)

#### Update policy

- `soft_adjust_max_step_frac = 0.5  # if edges move < 0.5*step => soft adjust allowed` (`freqtrade/user_data/strategies/GridBrainV1.py:942`)

#### Capital policy (quote-only for now)

- `inventory_mode = "quote_only"` (`freqtrade/user_data/strategies/GridBrainV1.py:945`)
- `inventory_target_base_min_pct = 0.0` (`freqtrade/user_data/strategies/GridBrainV1.py:946`)
- `inventory_target_base_max_pct = 0.0` (`freqtrade/user_data/strategies/GridBrainV1.py:947`)
- `topup_policy = "manual"` (`freqtrade/user_data/strategies/GridBrainV1.py:948`)
- `max_concurrent_rebuilds = 1` (`freqtrade/user_data/strategies/GridBrainV1.py:949`)
- `preferred_rung_cap = 0` (`freqtrade/user_data/strategies/GridBrainV1.py:950`)
- `grid_budget_pct = 0.70` (`freqtrade/user_data/strategies/GridBrainV1.py:951`)
- `reserve_pct = 0.30` (`freqtrade/user_data/strategies/GridBrainV1.py:952`)

#### TP/SL target expansion (Section 13.6).

- `donchian_lookback_bars = 96` (`freqtrade/user_data/strategies/GridBrainV1.py:955`)
- `basis_band_window = 96` (`freqtrade/user_data/strategies/GridBrainV1.py:956`)
- `basis_band_stds = 2.0` (`freqtrade/user_data/strategies/GridBrainV1.py:957`)
- `fvg_vp_enabled = False` (`freqtrade/user_data/strategies/GridBrainV1.py:958`)
- `fvg_vp_bins = 32` (`freqtrade/user_data/strategies/GridBrainV1.py:959`)
- `fvg_vp_lookback_bars = 256` (`freqtrade/user_data/strategies/GridBrainV1.py:960`)
- `fvg_vp_poc_tag_step_frac = 0.30` (`freqtrade/user_data/strategies/GridBrainV1.py:961`)
- `sl_lvn_avoid_steps = 0.25` (`freqtrade/user_data/strategies/GridBrainV1.py:962`)
- `sl_fvg_buffer_steps = 0.10` (`freqtrade/user_data/strategies/GridBrainV1.py:963`)
- `box_quality_log_space = True` (`freqtrade/user_data/strategies/GridBrainV1.py:964`)
- `box_quality_extension_factor = 1.386` (`freqtrade/user_data/strategies/GridBrainV1.py:965`)
- `midline_bias_fallback_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:966`)
- `midline_bias_tp_candidate_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:967`)
- `midline_bias_poc_neutral_step_frac = 0.35` (`freqtrade/user_data/strategies/GridBrainV1.py:968`)
- `midline_bias_poc_neutral_width_frac = 0.01` (`freqtrade/user_data/strategies/GridBrainV1.py:969`)
- `midline_bias_source_buffer_steps = 0.50` (`freqtrade/user_data/strategies/GridBrainV1.py:970`)
- `midline_bias_source_buffer_width_frac = 0.02` (`freqtrade/user_data/strategies/GridBrainV1.py:971`)
- `midline_bias_deadband_steps = 0.25` (`freqtrade/user_data/strategies/GridBrainV1.py:972`)
- `midline_bias_deadband_width_frac = 0.005` (`freqtrade/user_data/strategies/GridBrainV1.py:973`)

#### Shared fill semantics metadata (Section 13.7).

- `fill_confirmation_mode = "Touch"  # Touch | Reverse` (`freqtrade/user_data/strategies/GridBrainV1.py:976`)
- `fill_no_repeat_lsi_guard = True` (`freqtrade/user_data/strategies/GridBrainV1.py:977`)
- `fill_no_repeat_cooldown_bars = 1` (`freqtrade/user_data/strategies/GridBrainV1.py:978`)
- `tick_size_step_frac = 0.01` (`freqtrade/user_data/strategies/GridBrainV1.py:979`)
- `tick_size_floor = 1e-8` (`freqtrade/user_data/strategies/GridBrainV1.py:980`)

#### M505 / M809 / M1003 / M702 / M703 / M805 extensions.

- Knobs in this group: `58`
- `micro_reentry_pause_bars = 4` (`freqtrade/user_data/strategies/GridBrainV1.py:983`)
- `micro_reentry_require_poc_reclaim = True` (`freqtrade/user_data/strategies/GridBrainV1.py:984`)
- `micro_reentry_poc_buffer_steps = 0.25` (`freqtrade/user_data/strategies/GridBrainV1.py:985`)
- `buy_ratio_bias_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:986`)
- `buy_ratio_midband_half_width = 0.35` (`freqtrade/user_data/strategies/GridBrainV1.py:987`)
- `buy_ratio_bullish_threshold = 0.58` (`freqtrade/user_data/strategies/GridBrainV1.py:988`)
- `buy_ratio_bearish_threshold = 0.42` (`freqtrade/user_data/strategies/GridBrainV1.py:989`)
- `buy_ratio_rung_bias_strength = 0.35` (`freqtrade/user_data/strategies/GridBrainV1.py:990`)
- `buy_ratio_bearish_tp_step_multiple = 0.50` (`freqtrade/user_data/strategies/GridBrainV1.py:991`)
- `smart_channel_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:992`)
- `smart_channel_breakout_step_buffer = 0.25` (`freqtrade/user_data/strategies/GridBrainV1.py:993`)
- `smart_channel_volume_confirm_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:994`)
- `smart_channel_volume_rvol_min = 1.10` (`freqtrade/user_data/strategies/GridBrainV1.py:995`)
- `smart_channel_tp_nudge_step_multiple = 0.50` (`freqtrade/user_data/strategies/GridBrainV1.py:996`)
- `ob_enabled = True` (`freqtrade/user_data/strategies/GridBrainV1.py:997`)
- `ob_tf = "1h"` (`freqtrade/user_data/strategies/GridBrainV1.py:998`)
- `ob_use_wick_zone = True` (`freqtrade/user_data/strategies/GridBrainV1.py:999`)
- `ob_impulse_lookahead = 3` (`freqtrade/user_data/strategies/GridBrainV1.py:1000`)
- `ob_impulse_atr_len = 14` (`freqtrade/user_data/strategies/GridBrainV1.py:1001`)
- `ob_impulse_atr_mult = 1.0` (`freqtrade/user_data/strategies/GridBrainV1.py:1002`)
- ... plus `38` additional knobs in this group.

#### -------- internal state (best-effort, per process) --------

- Knobs in this group: `60`
- `_last_written_ts_by_pair = _last_written_ts_by_pair: Dict[str, int] = {}` (`freqtrade/user_data/strategies/GridBrainV1.py:1044`)
- `_last_plan_hash_by_pair = _last_plan_hash_by_pair: Dict[str, str] = {}` (`freqtrade/user_data/strategies/GridBrainV1.py:1045`)
- `_last_plan_base_hash_by_pair = _last_plan_base_hash_by_pair: Dict[str, str] = {}` (`freqtrade/user_data/strategies/GridBrainV1.py:1046`)
- `_last_material_plan_payload_by_pair = _last_material_plan_payload_by_pair: Dict[str, Dict[str, object]] = {}` (`freqtrade/user_data/strategies/GridBrainV1.py:1047`)
- `_last_plan_id_by_pair = _last_plan_id_by_pair: Dict[str, str] = {}` (`freqtrade/user_data/strategies/GridBrainV1.py:1048`)
- `_last_decision_seq_by_pair = _last_decision_seq_by_pair: Dict[str, int] = {}` (`freqtrade/user_data/strategies/GridBrainV1.py:1049`)
- `_event_counter_by_pair = _event_counter_by_pair: Dict[str, int] = {}` (`freqtrade/user_data/strategies/GridBrainV1.py:1050`)
- `_last_mid_by_pair = _last_mid_by_pair: Dict[str, float] = {}` (`freqtrade/user_data/strategies/GridBrainV1.py:1051`)
- `_last_box_step_by_pair = _last_box_step_by_pair: Dict[str, float] = {}` (`freqtrade/user_data/strategies/GridBrainV1.py:1052`)
- `_reclaim_until_ts_by_pair = _reclaim_until_ts_by_pair: Dict[str, int] = {}` (`freqtrade/user_data/strategies/GridBrainV1.py:1053`)
- `_cooldown_until_ts_by_pair = _cooldown_until_ts_by_pair: Dict[str, int] = {}` (`freqtrade/user_data/strategies/GridBrainV1.py:1054`)
- `_micro_reentry_pause_until_ts_by_pair = _micro_reentry_pause_until_ts_by_pair: Dict[str, int] = {}` (`freqtrade/user_data/strategies/GridBrainV1.py:1055`)
- `_stop_timestamps_by_pair = _stop_timestamps_by_pair: Dict[str, deque] = {}` (`freqtrade/user_data/strategies/GridBrainV1.py:1056`)
- `_active_since_ts_by_pair = _active_since_ts_by_pair: Dict[str, int] = {}` (`freqtrade/user_data/strategies/GridBrainV1.py:1057`)
- `_running_by_pair = _running_by_pair: Dict[str, bool] = {}` (`freqtrade/user_data/strategies/GridBrainV1.py:1058`)
- `_bbwp_cooloff_by_pair = _bbwp_cooloff_by_pair: Dict[str, bool] = {}` (`freqtrade/user_data/strategies/GridBrainV1.py:1059`)
- `_os_dev_state_by_pair = _os_dev_state_by_pair: Dict[str, int] = {}` (`freqtrade/user_data/strategies/GridBrainV1.py:1060`)
- `_os_dev_candidate_by_pair = _os_dev_candidate_by_pair: Dict[str, int] = {}` (`freqtrade/user_data/strategies/GridBrainV1.py:1061`)
- `_os_dev_candidate_count_by_pair = _os_dev_candidate_count_by_pair: Dict[str, int] = {}` (`freqtrade/user_data/strategies/GridBrainV1.py:1062`)
- `_os_dev_zero_persist_by_pair = _os_dev_zero_persist_by_pair: Dict[str, int] = {}` (`freqtrade/user_data/strategies/GridBrainV1.py:1063`)
- ... plus `40` additional knobs in this group.

#### ========== Helpers ==========

- `MODE_TRADING = ("intraday", "swing", "neutral_choppy")` (`freqtrade/user_data/strategies/GridBrainV1.py:2047`)
- `MODE_TRADING_WITH_PAUSE = MODE_TRADING + ("pause",)` (`freqtrade/user_data/strategies/GridBrainV1.py:2048`)
- `MODE_VALUES = ("intraday", "swing", "pause", "neutral_choppy")` (`freqtrade/user_data/strategies/GridBrainV1.py:2050`)

### 2.4 GridBrain Method Capability Map

#### Box Builder and Volume-Profile Stack

- Methods: `22`
- `_box_signature` (`freqtrade/user_data/strategies/GridBrainV1.py:1233`), `_poc_cross_detected` (`freqtrade/user_data/strategies/GridBrainV1.py:1239`), `_derive_box_block_reasons` (`freqtrade/user_data/strategies/GridBrainV1.py:1256`), `_box_straddles_cached_breakout` (`freqtrade/user_data/strategies/GridBrainV1.py:1271`), `_box_straddles_level` (`freqtrade/user_data/strategies/GridBrainV1.py:1296`), `_box_level_straddle_reasons` (`freqtrade/user_data/strategies/GridBrainV1.py:1309`), `_poc_acceptance_status` (`freqtrade/user_data/strategies/GridBrainV1.py:1357`), `_fallback_poc_estimate` (`freqtrade/user_data/strategies/GridBrainV1.py:1381`), `_box_width_history` (`freqtrade/user_data/strategies/GridBrainV1.py:1406`), `_box_width_avg_veto_state` (`freqtrade/user_data/strategies/GridBrainV1.py:1418`), `_record_accepted_box_width` (`freqtrade/user_data/strategies/GridBrainV1.py:1447`), `_poc_alignment_state` (`freqtrade/user_data/strategies/GridBrainV1.py:1451`), `_build_box_15m` (`freqtrade/user_data/strategies/GridBrainV1.py:3104`), `_is_level_near_box` (`freqtrade/user_data/strategies/GridBrainV1.py:3175`), `_box_quality_levels` (`freqtrade/user_data/strategies/GridBrainV1.py:3201`), `_update_box_quality` (`freqtrade/user_data/strategies/GridBrainV1.py:3350`), `_box_overlap_fraction` (`freqtrade/user_data/strategies/GridBrainV1.py:3380`), `_box_overlap_prune` (`freqtrade/user_data/strategies/GridBrainV1.py:3395`), `_record_box_history` (`freqtrade/user_data/strategies/GridBrainV1.py:3405`), `_vrvp_profile` (`freqtrade/user_data/strategies/GridBrainV1.py:3630`), `_mrvd_profile` (`freqtrade/user_data/strategies/GridBrainV1.py:3702`), `_micro_vap_inside_box` (`freqtrade/user_data/strategies/GridBrainV1.py:4219`)

#### Data Quality and Health

- Methods: `4`
- `_run_data_quality_checks` (`freqtrade/user_data/strategies/GridBrainV1.py:1333`), `_planner_health_state` (`freqtrade/user_data/strategies/GridBrainV1.py:1750`), `_validate_feature_contract` (`freqtrade/user_data/strategies/GridBrainV1.py:1816`), `_log_feature_contract_violation` (`freqtrade/user_data/strategies/GridBrainV1.py:1839`)

#### Decision and Event Logging

- Methods: `6`
- `_decision_log_path` (`freqtrade/user_data/strategies/GridBrainV1.py:2865`), `_event_log_path` (`freqtrade/user_data/strategies/GridBrainV1.py:2870`), `_severity_for_code` (`freqtrade/user_data/strategies/GridBrainV1.py:2883`), `_source_module_for_code` (`freqtrade/user_data/strategies/GridBrainV1.py:2915`), `_next_event_id` (`freqtrade/user_data/strategies/GridBrainV1.py:2989`), `_emit_decision_and_event_logs` (`freqtrade/user_data/strategies/GridBrainV1.py:2994`)

#### Indicator and Main Loop Entry Points

- Methods: `6`
- `informative_pairs` (`freqtrade/user_data/strategies/GridBrainV1.py:1106`), `populate_indicators_4h` (`freqtrade/user_data/strategies/GridBrainV1.py:1117`), `populate_indicators_1h` (`freqtrade/user_data/strategies/GridBrainV1.py:1132`), `populate_indicators` (`freqtrade/user_data/strategies/GridBrainV1.py:5931`), `populate_entry_trend` (`freqtrade/user_data/strategies/GridBrainV1.py:9599`), `populate_exit_trend` (`freqtrade/user_data/strategies/GridBrainV1.py:9603`)

#### Other

- Methods: `65`
- `__init__` (`freqtrade/user_data/strategies/GridBrainV1.py:491`), `_determine_regime_bands_run_id` (`freqtrade/user_data/strategies/GridBrainV1.py:878`), `_safe_float` (`freqtrade/user_data/strategies/GridBrainV1.py:1164`), `_record_mid_history` (`freqtrade/user_data/strategies/GridBrainV1.py:1179`), `_excursion_asymmetry_ratio` (`freqtrade/user_data/strategies/GridBrainV1.py:1199`), `_funding_gate_ok` (`freqtrade/user_data/strategies/GridBrainV1.py:1209`), `_hvp_stats` (`freqtrade/user_data/strategies/GridBrainV1.py:1216`), `_squeeze_release_block_reason` (`freqtrade/user_data/strategies/GridBrainV1.py:1326`), `_append_reason` (`freqtrade/user_data/strategies/GridBrainV1.py:1329`), `_percentile` (`freqtrade/user_data/strategies/GridBrainV1.py:1346`), `_efficiency_ratio` (`freqtrade/user_data/strategies/GridBrainV1.py:1526`), `_detect_structural_breakout` (`freqtrade/user_data/strategies/GridBrainV1.py:1539`), `_breakout_confirm_buffer` (`freqtrade/user_data/strategies/GridBrainV1.py:1560`), `_breakout_confirm_state` (`freqtrade/user_data/strategies/GridBrainV1.py:1581`), `_range_len_gate_state` (`freqtrade/user_data/strategies/GridBrainV1.py:1622`), `_breakout_confirm_reason_state` (`freqtrade/user_data/strategies/GridBrainV1.py:1647`), `_bbw_nonexpanding` (`freqtrade/user_data/strategies/GridBrainV1.py:1679`), `_update_breakout_fresh_state` (`freqtrade/user_data/strategies/GridBrainV1.py:1696`), `_phase2_gate_failures_from_flags` (`freqtrade/user_data/strategies/GridBrainV1.py:1729`), `_start_stability_state` (`freqtrade/user_data/strategies/GridBrainV1.py:1767`), `_atomic_write_json` (`freqtrade/user_data/strategies/GridBrainV1.py:1774`), `_choppiness_index` (`freqtrade/user_data/strategies/GridBrainV1.py:1854`), `_di_flip_rate` (`freqtrade/user_data/strategies/GridBrainV1.py:1878`), `_wickiness` (`freqtrade/user_data/strategies/GridBrainV1.py:1903`), `_containment_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:1929`), `_adx_exit_hysteresis_trigger` (`freqtrade/user_data/strategies/GridBrainV1.py:1960`), `_adx_di_down_risk_trigger` (`freqtrade/user_data/strategies/GridBrainV1.py:1973`), `_gate_profile_values` (`freqtrade/user_data/strategies/GridBrainV1.py:1993`), `_neutral_adx_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:2063`), `_neutral_spread_bps` (`freqtrade/user_data/strategies/GridBrainV1.py:2072`), `_neutral_step_bps` (`freqtrade/user_data/strategies/GridBrainV1.py:2080`), `_should_emit_per_candle_history` (`freqtrade/user_data/strategies/GridBrainV1.py:2668`), `_reset_pair_runtime_state` (`freqtrade/user_data/strategies/GridBrainV1.py:2674`), `_ts_to_iso` (`freqtrade/user_data/strategies/GridBrainV1.py:2721`), `_append_jsonl` (`freqtrade/user_data/strategies/GridBrainV1.py:2876`), `_range_candidate` (`freqtrade/user_data/strategies/GridBrainV1.py:3099`), `_latest_daily_vwap` (`freqtrade/user_data/strategies/GridBrainV1.py:3153`), `_midline_bias_fallback_state` (`freqtrade/user_data/strategies/GridBrainV1.py:3257`), `_bbw_percentile_ok` (`freqtrade/user_data/strategies/GridBrainV1.py:3413`), `_bbwp_percentile_last` (`freqtrade/user_data/strategies/GridBrainV1.py:3419`), `_user_data_dir` (`freqtrade/user_data/strategies/GridBrainV1.py:3430`), `_regime_bands_artifact_path` (`freqtrade/user_data/strategies/GridBrainV1.py:3435`), `_pair_fs` (`freqtrade/user_data/strategies/GridBrainV1.py:3443`), `_load_regime_bands_entries` (`freqtrade/user_data/strategies/GridBrainV1.py:3525`), `_neutral_band_entry` (`freqtrade/user_data/strategies/GridBrainV1.py:3547`), `_normalize_from_band` (`freqtrade/user_data/strategies/GridBrainV1.py:3552`), `_neutral_persistence_for_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:3575`), `_compute_chop_score` (`freqtrade/user_data/strategies/GridBrainV1.py:3591`), `_interval_overlap_frac` (`freqtrade/user_data/strategies/GridBrainV1.py:3690`), `_pivot_indices` (`freqtrade/user_data/strategies/GridBrainV1.py:3803`), `_find_numeric_row` (`freqtrade/user_data/strategies/GridBrainV1.py:3993`), `_freqai_overlay_state` (`freqtrade/user_data/strategies/GridBrainV1.py:4020`), `_apply_ml_rung_safety` (`freqtrade/user_data/strategies/GridBrainV1.py:4136`), `_os_dev_from_history` (`freqtrade/user_data/strategies/GridBrainV1.py:4170`), `_capacity_hint_state` (`freqtrade/user_data/strategies/GridBrainV1.py:4678`), `_meta_drift_state` (`freqtrade/user_data/strategies/GridBrainV1.py:4791`), `_nearest_above` (`freqtrade/user_data/strategies/GridBrainV1.py:5144`), `_infer_tick_size` (`freqtrade/user_data/strategies/GridBrainV1.py:5202`), `_breakout_flags` (`freqtrade/user_data/strategies/GridBrainV1.py:5208`), `_micro_buy_ratio_state` (`freqtrade/user_data/strategies/GridBrainV1.py:5221`), `_apply_buy_ratio_rung_bias` (`freqtrade/user_data/strategies/GridBrainV1.py:5281`), `_zigzag_contraction_state` (`freqtrade/user_data/strategies/GridBrainV1.py:5458`), `_informative_ohlc_frame` (`freqtrade/user_data/strategies/GridBrainV1.py:5497`), `_order_flow_state` (`freqtrade/user_data/strategies/GridBrainV1.py:5779`), `_micro_reentry_state` (`freqtrade/user_data/strategies/GridBrainV1.py:5900`)

#### Plan Signature, Materiality, and Publish

- Methods: `5`
- `_evaluate_materiality` (`freqtrade/user_data/strategies/GridBrainV1.py:1777`), `_plan_dir` (`freqtrade/user_data/strategies/GridBrainV1.py:2729`), `_seed_plan_signature_state` (`freqtrade/user_data/strategies/GridBrainV1.py:2742`), `_next_plan_identity` (`freqtrade/user_data/strategies/GridBrainV1.py:2782`), `_write_plan` (`freqtrade/user_data/strategies/GridBrainV1.py:2789`)

#### Regime Router and Mode Thresholds

- Methods: `9`
- `_normalize_mode_name` (`freqtrade/user_data/strategies/GridBrainV1.py:2053`), `_neutral_spread_threshold` (`freqtrade/user_data/strategies/GridBrainV1.py:2086`), `_active_threshold_profile` (`freqtrade/user_data/strategies/GridBrainV1.py:2091`), `_external_mode_threshold_overrides` (`freqtrade/user_data/strategies/GridBrainV1.py:2097`), `_mode_threshold_overrides` (`freqtrade/user_data/strategies/GridBrainV1.py:2176`), `_mode_threshold_block` (`freqtrade/user_data/strategies/GridBrainV1.py:2242`), `_mode_router_score` (`freqtrade/user_data/strategies/GridBrainV1.py:2314`), `_regime_router_state` (`freqtrade/user_data/strategies/GridBrainV1.py:2373`), `_runmode_name` (`freqtrade/user_data/strategies/GridBrainV1.py:2649`)

#### Runtime Safety Rails

- Methods: `3`
- `_drawdown_guard_state` (`freqtrade/user_data/strategies/GridBrainV1.py:5838`), `_max_stops_window_state` (`freqtrade/user_data/strategies/GridBrainV1.py:5869`), `_register_stop_timestamp` (`freqtrade/user_data/strategies/GridBrainV1.py:5893`)

#### Sizing, Targets, and Cost Model

- Methods: `9`
- `_compute_band_slope_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:1189`), `_execution_cost_artifact_path` (`freqtrade/user_data/strategies/GridBrainV1.py:3446`), `_load_execution_cost_artifact` (`freqtrade/user_data/strategies/GridBrainV1.py:3451`), `_empirical_cost_sample` (`freqtrade/user_data/strategies/GridBrainV1.py:4685`), `_effective_cost_floor` (`freqtrade/user_data/strategies/GridBrainV1.py:4881`), `_n_level_bounds` (`freqtrade/user_data/strategies/GridBrainV1.py:5067`), `_grid_sizing` (`freqtrade/user_data/strategies/GridBrainV1.py:5083`), `_select_tp_price` (`freqtrade/user_data/strategies/GridBrainV1.py:5158`), `_select_sl_price` (`freqtrade/user_data/strategies/GridBrainV1.py:5175`)

#### Structure Modules and Confluence

- Methods: `9`
- `_cvd_state` (`freqtrade/user_data/strategies/GridBrainV1.py:3831`), `_apply_cvd_rung_bias` (`freqtrade/user_data/strategies/GridBrainV1.py:3957`), `_rung_weights_from_micro_vap` (`freqtrade/user_data/strategies/GridBrainV1.py:4315`), `_fvg_stack_state` (`freqtrade/user_data/strategies/GridBrainV1.py:4358`), `_meta_drift_channels` (`freqtrade/user_data/strategies/GridBrainV1.py:4756`), `_fvg_vp_state` (`freqtrade/user_data/strategies/GridBrainV1.py:5311`), `_smart_channel_state` (`freqtrade/user_data/strategies/GridBrainV1.py:5394`), `_order_block_state` (`freqtrade/user_data/strategies/GridBrainV1.py:5526`), `_session_sweep_state` (`freqtrade/user_data/strategies/GridBrainV1.py:5704`)

### 2.5 Dedicated Planner/Analytics/Risk Modules

- **Empirical execution cost calibrator** with source-aware sample tracking and p75/p90 floor outputs (`analytics/execution_cost_calibrator.py:8`).
- **Meta drift guard engine** using EMA + z-score + CUSUM + Page-Hinkley channel voting (`risk/meta_drift_guard.py:25`).
- **Volatility policy adapter** for bucketed runtime threshold adaptation + N-level diagnostics (`planner/volatility_policy_adapter.py:64`).
- **Start stability evaluator** (k-of-n + minimum score) (`planner/start_stability.py:9`).
- **Replan materiality policy** with class/reason output (`planner/replan_policy.py:18`).
- **Order block module** (latest per side, freshness, mitigation, age gating) (`planner/structure/order_blocks.py:263`).
- **Liquidity sweep module** (confirmed pivots, wick sweeps, break-retest, Wick/Open retest mode) (`planner/structure/liquidity_sweeps.py:90`).
- **Dynamic capacity guard** (spread/depth/notional-based rung cap + block semantics) (`execution/capacity_guard.py:66`).
- **Chaos profile utilities** (defaults + schema validation + load) (`sim/chaos_profiles.py:10`).

### 2.6 Executor (`grid_executor_v1.py`) — Implemented Features

- **Plan intake hardening**: signature validation, schema checks, expiry checks, duplicate/idempotent suppression (`freqtrade/user_data/scripts/grid_executor_v1.py:798`, `freqtrade/user_data/scripts/grid_executor_v1.py:814`).
- **Executor state machine with persisted recovery** (`freqtrade/user_data/scripts/grid_executor_v1.py:626`, `freqtrade/user_data/scripts/grid_executor_v1.py:2730`, `freqtrade/user_data/scripts/grid_executor_v1.py:2741`).
- **Maker-first and post-only reject management**: retry/backoff/reprice and reject-burst diagnostics (`freqtrade/user_data/scripts/grid_executor_v1.py:1107`, `freqtrade/user_data/scripts/grid_executor_v1.py:1178`).
- **Confirm-entry/confirm-exit hooks** with runtime metric extraction (`freqtrade/user_data/scripts/grid_executor_v1.py:1187`, `freqtrade/user_data/scripts/grid_executor_v1.py:1213`).
- **Capacity cap enforcement** integrated via dynamic capacity state + rung-cap pruning (`freqtrade/user_data/scripts/grid_executor_v1.py:1277`, `freqtrade/user_data/scripts/grid_executor_v1.py:1357`, `freqtrade/user_data/scripts/grid_executor_v1.py:1413`).
- **Order/fill lifecycle logging + execution-cost artifact publishing** (`freqtrade/user_data/scripts/grid_executor_v1.py:1486`, `freqtrade/user_data/scripts/grid_executor_v1.py:1529`, `freqtrade/user_data/scripts/grid_executor_v1.py:1579`).
- **Reconciliation and tolerant matching paths for live/open-order sync** (`freqtrade/user_data/scripts/grid_executor_v1.py:1691`, `freqtrade/user_data/scripts/grid_executor_v1.py:1820`, `freqtrade/user_data/scripts/grid_executor_v1.py:1952`).
- **Fill cooldown/no-repeat guard** implemented (`freqtrade/user_data/scripts/grid_executor_v1.py:365`).

### 2.7 Simulator/Replay (`grid_simulator_v1.py`) — Implemented Features

- **Single-plan simulation** with deterministic tick-aware levels and configurable fill confirmation mode (`Touch`/`Reverse`) (`freqtrade/user_data/scripts/grid_simulator_v1.py:964`, `freqtrade/user_data/scripts/grid_simulator_v1.py:279`, `freqtrade/user_data/scripts/grid_simulator_v1.py:254`).
- **Replay over plan sequence** with START/HOLD/STOP semantics and action suppression signatures (`freqtrade/user_data/scripts/grid_simulator_v1.py:1229`, `freqtrade/user_data/scripts/grid_simulator_v1.py:607`).
- **Reason-code extraction and replay summaries** (start blockers, stop reasons, hold counts, materiality/replan counters) (`freqtrade/user_data/scripts/grid_simulator_v1.py:783`, `freqtrade/user_data/scripts/grid_simulator_v1.py:894`, `freqtrade/user_data/scripts/grid_simulator_v1.py:1416`).
- **Chaos/stress perturbation runtime**: latency, spread shocks, partial fills, reject bursts, delayed/missing/data-gap candles + deterministic seed control (`freqtrade/user_data/scripts/grid_simulator_v1.py:396`, `freqtrade/user_data/scripts/grid_simulator_v1.py:1303`, `freqtrade/user_data/scripts/grid_simulator_v1.py:1337`).
- **Brain/simulator alignment helpers** for timerange/start_at/plan-effective-time and ladder generation (`freqtrade/user_data/scripts/grid_simulator_v1.py:147`, `freqtrade/user_data/scripts/grid_simulator_v1.py:614`, `freqtrade/user_data/scripts/grid_simulator_v1.py:914`).
- **Fill cooldown/no-repeat guard** implemented (`freqtrade/user_data/scripts/grid_simulator_v1.py:339`).

### 2.8 Research/Validation Utility Scripts

- **Regime audit + threshold recommendation pipeline** with labels, transition analysis, quantile stats (`freqtrade/user_data/scripts/regime_audit_v1.py:233`, `freqtrade/user_data/scripts/regime_audit_v1.py:303`, `freqtrade/user_data/scripts/regime_audit_v1.py:410`, `freqtrade/user_data/scripts/regime_audit_v1.py:577`).
- **Regression suite harness** validating plan schema/features, executor semantics, weighted ladder behavior, stress replay contract, ML overlay behavior, router handoff behavior (`freqtrade/user_data/scripts/user_regression_suite.py:78`, `freqtrade/user_data/scripts/user_regression_suite.py:290`, `freqtrade/user_data/scripts/user_regression_suite.py:342`, `freqtrade/user_data/scripts/user_regression_suite.py:53`, `freqtrade/user_data/scripts/user_regression_suite.py:483`, `freqtrade/user_data/scripts/user_regression_suite.py:603`).

### 2.9 Schemas and Contracts Implemented

- `schemas/grid_plan.schema.json`: planner plan payload contract.
- `schemas/decision_log.schema.json`: decision log row contract.
- `schemas/event_log.schema.json`: event log row contract.
- `schemas/chaos_profile.schema.json`: stress profile contract.
- `schemas/execution_cost_calibration.schema.json`: execution-cost artifact contract.
- `schemas/plan_signature.py`: shared material plan fields used for hashing/diffs.

## 3) Test-Validated Implementations (By Test File)

### `freqtrade/user_data/tests/test_chaos_replay_harness.py`

- Tests: `4`
- `test_chaos_profile_is_deterministic_and_reports_delta` (`freqtrade/user_data/tests/test_chaos_replay_harness.py:66`), `test_chaos_partial_fill_profile_marks_partial_fills` (`freqtrade/user_data/tests/test_chaos_replay_harness.py:91`), `test_chaos_data_gap_profile_drops_candles` (`freqtrade/user_data/tests/test_chaos_replay_harness.py:104`), `test_chaos_fault_injection_profiles_trigger_expected_rails` (`freqtrade/user_data/tests/test_chaos_replay_harness.py:161`)

### `freqtrade/user_data/tests/test_executor_hardening.py`

- Tests: `10`
- `test_ccxt_place_limit_retries_post_only_with_backoff_and_reprice` (`freqtrade/user_data/tests/test_executor_hardening.py:111`), `test_reject_burst_blocks_start_and_downgrades_to_hold` (`freqtrade/user_data/tests/test_executor_hardening.py:131`), `test_stop_exit_confirm_uses_failsafe_reason` (`freqtrade/user_data/tests/test_executor_hardening.py:153`), `test_rebuild_confirm_failure_is_tracked_separately` (`freqtrade/user_data/tests/test_executor_hardening.py:176`), `test_reconcile_matches_live_orders_with_tolerance` (`freqtrade/user_data/tests/test_executor_hardening.py:201`), `test_reconcile_honors_action_cap` (`freqtrade/user_data/tests/test_executor_hardening.py:233`), `test_executor_recovers_state_file_on_startup` (`freqtrade/user_data/tests/test_executor_hardening.py:260`), `test_capacity_rung_cap_limits_seeded_orders_in_paper` (`freqtrade/user_data/tests/test_executor_hardening.py:306`), `test_capacity_hard_block_prevents_start` (`freqtrade/user_data/tests/test_executor_hardening.py:339`), `test_execution_cost_feedback_writes_artifact_and_lifecycle_logs` (`freqtrade/user_data/tests/test_executor_hardening.py:365`)

### `freqtrade/user_data/tests/test_liquidity_sweeps.py`

- Tests: `4`
- `test_pivot_confirmation_is_bar_confirmed` (`freqtrade/user_data/tests/test_liquidity_sweeps.py:37`), `test_wick_sweep_and_break_retest_stop_through_box_edge` (`freqtrade/user_data/tests/test_liquidity_sweeps.py:59`), `test_retest_validation_mode_toggle_affects_break_retest_only` (`freqtrade/user_data/tests/test_liquidity_sweeps.py:76`), `test_determinism_for_same_inputs` (`freqtrade/user_data/tests/test_liquidity_sweeps.py:101`)

### `freqtrade/user_data/tests/test_meta_drift_replay.py`

- Tests: `1`
- `test_replay_synthetic_regime_shift_tracks_meta_drift_soft_and_hard` (`freqtrade/user_data/tests/test_meta_drift_replay.py:53`)

### `freqtrade/user_data/tests/test_min_range_and_breakout_confirm.py`

- Tests: `8`
- `test_min_range_len_gate_blocks_before_threshold` (`freqtrade/user_data/tests/test_min_range_and_breakout_confirm.py:20`), `test_min_range_len_gate_passes_at_threshold` (`freqtrade/user_data/tests/test_min_range_and_breakout_confirm.py:34`), `test_min_range_len_gate_resets_on_new_box_generation` (`freqtrade/user_data/tests/test_min_range_and_breakout_confirm.py:46`), `test_breakout_confirm_single_close_outside_is_not_confirmed` (`freqtrade/user_data/tests/test_min_range_and_breakout_confirm.py:64`), `test_breakout_confirm_up_blocks_start_when_not_running` (`freqtrade/user_data/tests/test_min_range_and_breakout_confirm.py:79`), `test_breakout_confirm_dn_stops_when_running` (`freqtrade/user_data/tests/test_min_range_and_breakout_confirm.py:98`), `test_breakout_confirm_buffer_modes` (`freqtrade/user_data/tests/test_min_range_and_breakout_confirm.py:125`), `test_breakout_confirm_determinism_on_same_input` (`freqtrade/user_data/tests/test_min_range_and_breakout_confirm.py:138`)

### `freqtrade/user_data/tests/test_ml_overlay_step14.py`

- Tests: `3`
- `test_step14_ml_scripts_pipeline` (`freqtrade/user_data/tests/test_ml_overlay_step14.py:108`), `test_tuning_protocol_respects_required_ml_overlay_gate` (`freqtrade/user_data/tests/test_ml_overlay_step14.py:212`), `test_ml_overlay_defaults_are_advisory_and_off` (`freqtrade/user_data/tests/test_ml_overlay_step14.py:332`)

### `freqtrade/user_data/tests/test_order_blocks.py`

- Tests: `3`
- `test_order_block_detects_bull_and_mitigation` (`freqtrade/user_data/tests/test_order_blocks.py:48`), `test_order_block_detects_bear_and_freshness_window` (`freqtrade/user_data/tests/test_order_blocks.py:69`), `test_order_block_strategy_state_applies_fresh_gate_straddle_and_tp_nudges` (`freqtrade/user_data/tests/test_order_blocks.py:89`)

### `freqtrade/user_data/tests/test_partial_module_completion.py`

- Tests: `4`
- `test_protections_drawdown_and_stop_window_helpers` (`freqtrade/user_data/tests/test_partial_module_completion.py:18`), `test_micro_bias_order_flow_and_reentry_helpers` (`freqtrade/user_data/tests/test_partial_module_completion.py:46`), `test_fvg_vp_channel_and_session_sweep_helpers` (`freqtrade/user_data/tests/test_partial_module_completion.py:125`), `test_event_bus_emits_reason_and_taxonomy_events` (`freqtrade/user_data/tests/test_partial_module_completion.py:204`)

### `freqtrade/user_data/tests/test_phase3_validation.py`

- Tests: `46`
- `test_box_signature_is_repeatable` (`freqtrade/user_data/tests/test_phase3_validation.py:16`), `test_poc_cross_detected_when_open_close_bracket_value` (`freqtrade/user_data/tests/test_phase3_validation.py:22`), `test_derive_box_block_reasons_reflects_conflicts` (`freqtrade/user_data/tests/test_phase3_validation.py:33`), `test_poc_acceptance_status_persists_once_crossed` (`freqtrade/user_data/tests/test_phase3_validation.py:45`), `test_data_quality_checks_flag_gap` (`freqtrade/user_data/tests/test_phase3_validation.py:75`), `test_data_quality_checks_flag_duplicates` (`freqtrade/user_data/tests/test_phase3_validation.py:91`), `test_data_quality_checks_zero_volume_streak` (`freqtrade/user_data/tests/test_phase3_validation.py:107`), `test_phase2_gate_failures_records_block_reasons` (`freqtrade/user_data/tests/test_phase3_validation.py:125`), `test_start_block_reasons_include_baseline_codes` (`freqtrade/user_data/tests/test_phase3_validation.py:144`), `test_start_block_reasons_include_breakout_block` (`freqtrade/user_data/tests/test_phase3_validation.py:157`), `test_materiality_waits_for_epoch_or_delta` (`freqtrade/user_data/tests/test_phase3_validation.py:168`), `test_compute_band_slope_pct_respects_window` (`freqtrade/user_data/tests/test_phase3_validation.py:186`), `test_excursion_asymmetry_ratio_handles_invalid_devs` (`freqtrade/user_data/tests/test_phase3_validation.py:197`), `test_funding_gate_honors_threshold` (`freqtrade/user_data/tests/test_phase3_validation.py:203`), `test_box_straddle_breakout_detection_adds_blocker` (`freqtrade/user_data/tests/test_phase3_validation.py:213`), `test_squeeze_release_block_reason_is_consumed` (`freqtrade/user_data/tests/test_phase3_validation.py:223`), `test_bbw_nonexpanding_gate_requires_flat_or_contracting_window` (`freqtrade/user_data/tests/test_phase3_validation.py:231`), `test_breakout_fresh_state_blocks_until_reclaimed` (`freqtrade/user_data/tests/test_phase3_validation.py:238`), `test_detect_structural_breakout_uses_close_vs_prior_extremes` (`freqtrade/user_data/tests/test_phase3_validation.py:255`), `test_hvp_stats_returns_current_and_sma` (`freqtrade/user_data/tests/test_phase3_validation.py:271`), `test_planner_health_state_transitions` (`freqtrade/user_data/tests/test_phase3_validation.py:283`), `test_start_stability_state_supports_k_of_n_and_score` (`freqtrade/user_data/tests/test_phase3_validation.py:292`), `test_box_quality_metrics_and_straddle_helpers` (`freqtrade/user_data/tests/test_phase3_validation.py:305`), `test_box_quality_levels_linear_fallback_when_nonpositive_bounds` (`freqtrade/user_data/tests/test_phase3_validation.py:320`), `test_midline_bias_fallback_activates_when_vrvp_poc_is_neutral` (`freqtrade/user_data/tests/test_phase3_validation.py:333`), `test_midline_bias_fallback_stays_inactive_when_vrvp_poc_not_neutral` (`freqtrade/user_data/tests/test_phase3_validation.py:364`), `test_fallback_poc_estimate_uses_volume_weighted_typical_price` (`freqtrade/user_data/tests/test_phase3_validation.py:393`), `test_box_width_avg_veto_triggers_when_width_exceeds_rolling_ratio` (`freqtrade/user_data/tests/test_phase3_validation.py:410`), `test_poc_alignment_strict_requires_cross_when_misaligned` (`freqtrade/user_data/tests/test_phase3_validation.py:424`), `test_poc_acceptance_handles_multiple_candidates` (`freqtrade/user_data/tests/test_phase3_validation.py:463`), `test_box_overlap_prune_detects_high_overlap` (`freqtrade/user_data/tests/test_phase3_validation.py:476`), `test_latest_daily_vwap_computation` (`freqtrade/user_data/tests/test_phase3_validation.py:484`), `test_grid_sizing_reduces_n_to_meet_cost_floor` (`freqtrade/user_data/tests/test_phase3_validation.py:542`), `test_effective_cost_floor_uses_empirical_and_emits_stale_warning` (`freqtrade/user_data/tests/test_phase3_validation.py:557`), `test_effective_cost_floor_switches_to_empirical_when_higher` (`freqtrade/user_data/tests/test_phase3_validation.py:565`), `test_effective_cost_floor_proxy_only_samples_do_not_promote_empirical` (`freqtrade/user_data/tests/test_phase3_validation.py:586`), `test_effective_cost_floor_promotes_with_empirical_artifact` (`freqtrade/user_data/tests/test_phase3_validation.py:609`), `test_tp_selection_prefers_nearest_conservative` (`freqtrade/user_data/tests/test_phase3_validation.py:659`), `test_sl_selection_avoids_lvn_and_fvg_gap` (`freqtrade/user_data/tests/test_phase3_validation.py:675`), `test_simulator_fill_guard_respects_no_repeat_toggle` (`freqtrade/user_data/tests/test_phase3_validation.py:690`), `test_executor_fill_guard_respects_no_repeat_toggle` (`freqtrade/user_data/tests/test_phase3_validation.py:703`), `test_executor_fill_bar_index_tracks_plan_clock` (`freqtrade/user_data/tests/test_phase3_validation.py:715`), `test_meta_drift_guard_detects_hard_shift` (`freqtrade/user_data/tests/test_phase3_validation.py:734`), `test_meta_drift_state_maps_to_actions` (`freqtrade/user_data/tests/test_phase3_validation.py:778`), `test_empirical_cost_sample_uses_execution_cost_artifact` (`freqtrade/user_data/tests/test_phase3_validation.py:852`), `test_decision_and_event_logs_are_emitted_with_schema` (`freqtrade/user_data/tests/test_phase3_validation.py:896`)

### `freqtrade/user_data/tests/test_replay_golden_consistency.py`

- Tests: `2`
- `test_replay_golden_summary_contract_is_strict` (`freqtrade/user_data/tests/test_replay_golden_consistency.py:63`), `test_replay_brain_simulator_consistency_trace_matches_plans` (`freqtrade/user_data/tests/test_replay_golden_consistency.py:126`)

### `freqtrade/user_data/tests/test_stress_replay_standard_validation.py`

- Tests: `1`
- `test_stress_replay_standard_validation_summary_contract` (`freqtrade/user_data/tests/test_stress_replay_standard_validation.py:44`)

### `freqtrade/user_data/tests/test_tuning_protocol.py`

- Tests: `3`
- `test_tuning_protocol_promotes_candidate_with_passed_gates` (`freqtrade/user_data/tests/test_tuning_protocol.py:164`), `test_tuning_protocol_strict_fails_when_chaos_gate_fails` (`freqtrade/user_data/tests/test_tuning_protocol.py:325`), `test_tuning_protocol_strict_fails_when_required_ablation_missing` (`freqtrade/user_data/tests/test_tuning_protocol.py:456`)

## 4) Wiring Status for Canonical Codes

### 4.1 Wired Codes (Detected in Runtime Source)

- `BLOCK_7D_EXTREME_CONTEXT` (`BlockReason.BLOCK_7D_EXTREME_CONTEXT`) -> `freqtrade/user_data/strategies/GridBrainV1.py:1747`
- `BLOCK_ADX_HIGH` (`BlockReason.BLOCK_ADX_HIGH`) -> `freqtrade/user_data/strategies/GridBrainV1.py:1739`
- `BLOCK_BAND_SLOPE_HIGH` (`BlockReason.BLOCK_BAND_SLOPE_HIGH`) -> `freqtrade/user_data/strategies/GridBrainV1.py:7732`
- `BLOCK_BASIS_CROSS_PENDING` (`BlockReason.BLOCK_BASIS_CROSS_PENDING`) -> `freqtrade/user_data/strategies/GridBrainV1.py:7793`
- `BLOCK_BBWP_HIGH` (`BlockReason.BLOCK_BBWP_HIGH`) -> `freqtrade/user_data/strategies/GridBrainV1.py:7741`
- `BLOCK_BBW_EXPANDING` (`BlockReason.BLOCK_BBW_EXPANDING`) -> `freqtrade/user_data/strategies/GridBrainV1.py:1741`
- `BLOCK_BOX_CHANNEL_OVERLAP_LOW` (`BlockReason.BLOCK_BOX_CHANNEL_OVERLAP_LOW`) -> `freqtrade/user_data/strategies/GridBrainV1.py:6723`
- `BLOCK_BOX_ENVELOPE_RATIO_HIGH` (`BlockReason.BLOCK_BOX_ENVELOPE_RATIO_HIGH`) -> `freqtrade/user_data/strategies/GridBrainV1.py:6737`
- `BLOCK_BOX_OVERLAP_HIGH` (`BlockReason.BLOCK_BOX_OVERLAP_HIGH`) -> `freqtrade/user_data/strategies/GridBrainV1.py:6620`
- `BLOCK_BOX_STRADDLE_BREAKOUT_LEVEL` (`BlockReason.BLOCK_BOX_STRADDLE_BREAKOUT_LEVEL`) -> `freqtrade/user_data/strategies/GridBrainV1.py:7174`
- `BLOCK_BOX_STRADDLE_FVG_AVG` (`BlockReason.BLOCK_BOX_STRADDLE_FVG_AVG`) -> `freqtrade/user_data/strategies/GridBrainV1.py:1263`
- `BLOCK_BOX_STRADDLE_FVG_EDGE` (`BlockReason.BLOCK_BOX_STRADDLE_FVG_EDGE`) -> `freqtrade/user_data/strategies/GridBrainV1.py:1261`
- `BLOCK_BOX_STRADDLE_OB_EDGE` (`BlockReason.BLOCK_BOX_STRADDLE_OB_EDGE`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2948`
- `BLOCK_BOX_STRADDLE_SESSION_FVG_AVG` (`BlockReason.BLOCK_BOX_STRADDLE_SESSION_FVG_AVG`) -> `freqtrade/user_data/strategies/GridBrainV1.py:1268`
- `BLOCK_BOX_STRADDLE_VWAP_DONCHIAN_MID` (`BlockReason.BLOCK_BOX_STRADDLE_VWAP_DONCHIAN_MID`) -> `freqtrade/user_data/strategies/GridBrainV1.py:7185`
- `BLOCK_BOX_VP_POC_MISPLACED` (`BlockReason.BLOCK_BOX_VP_POC_MISPLACED`) -> `freqtrade/user_data/strategies/GridBrainV1.py:7178`
- `BLOCK_BOX_WIDTH_TOO_WIDE` (`BlockReason.BLOCK_BOX_WIDTH_TOO_WIDE`) -> `freqtrade/user_data/strategies/GridBrainV1.py:6617`
- `BLOCK_BREAKOUT_CONFIRM_DN` (`BlockReason.BLOCK_BREAKOUT_CONFIRM_DN`) -> `freqtrade/user_data/strategies/GridBrainV1.py:1664`
- `BLOCK_BREAKOUT_CONFIRM_UP` (`BlockReason.BLOCK_BREAKOUT_CONFIRM_UP`) -> `freqtrade/user_data/strategies/GridBrainV1.py:1659`
- `BLOCK_CAPACITY_THIN` (`BlockReason.BLOCK_CAPACITY_THIN`) -> `execution/capacity_guard.py:122`, `freqtrade/user_data/scripts/grid_executor_v1.py:1341`, `freqtrade/user_data/strategies/GridBrainV1.py:7763`
- `BLOCK_COOLDOWN_ACTIVE` (`BlockReason.BLOCK_COOLDOWN_ACTIVE`) -> `freqtrade/user_data/strategies/GridBrainV1.py:8057`
- `BLOCK_DATA_GAP` (`BlockReason.BLOCK_DATA_GAP`) -> `data/data_quality_assessor.py:47`, `freqtrade/user_data/strategies/GridBrainV1.py:1756`
- `BLOCK_DATA_MISALIGN` (`BlockReason.BLOCK_DATA_MISALIGN`) -> `data/data_quality_assessor.py:34`, `freqtrade/user_data/strategies/GridBrainV1.py:1761`
- `BLOCK_DRAWDOWN_GUARD` (`BlockReason.BLOCK_DRAWDOWN_GUARD`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2920`
- `BLOCK_DRIFT_SLOPE_HIGH` (`BlockReason.BLOCK_DRIFT_SLOPE_HIGH`) -> `freqtrade/user_data/strategies/GridBrainV1.py:7736`
- `BLOCK_EMA_DIST` (`BlockReason.BLOCK_EMA_DIST`) -> `freqtrade/user_data/strategies/GridBrainV1.py:1743`
- `BLOCK_EXCURSION_ASYMMETRY` (`BlockReason.BLOCK_EXCURSION_ASYMMETRY`) -> `freqtrade/user_data/strategies/GridBrainV1.py:7734`
- `BLOCK_FRESH_BREAKOUT` (`BlockReason.BLOCK_FRESH_BREAKOUT`) -> `freqtrade/user_data/strategies/GridBrainV1.py:581`
- `BLOCK_FRESH_OB_COOLOFF` (`BlockReason.BLOCK_FRESH_OB_COOLOFF`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2947`
- `BLOCK_FUNDING_FILTER` (`BlockReason.BLOCK_FUNDING_FILTER`) -> `freqtrade/user_data/strategies/GridBrainV1.py:7755`
- `BLOCK_HVP_EXPANDING` (`BlockReason.BLOCK_HVP_EXPANDING`) -> `freqtrade/user_data/strategies/GridBrainV1.py:7757`
- `BLOCK_LIQ_SWEEP_OPPOSITE_STRUCTURE` (`BlockReason.BLOCK_LIQ_SWEEP_OPPOSITE_STRUCTURE`) -> `freqtrade/user_data/strategies/GridBrainV1.py:7761`
- `BLOCK_MAX_STOPS_WINDOW` (`BlockReason.BLOCK_MAX_STOPS_WINDOW`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2921`
- `BLOCK_META_DRIFT_SOFT` (`BlockReason.BLOCK_META_DRIFT_SOFT`) -> `freqtrade/user_data/strategies/GridBrainV1.py:7765`
- `BLOCK_MIN_RANGE_LEN_NOT_MET` (`BlockReason.BLOCK_MIN_RANGE_LEN_NOT_MET`) -> `freqtrade/user_data/strategies/GridBrainV1.py:1640`
- `BLOCK_NO_POC_ACCEPTANCE` (`BlockReason.BLOCK_NO_POC_ACCEPTANCE`) -> `freqtrade/user_data/strategies/GridBrainV1.py:7787`
- `BLOCK_OS_DEV_DIRECTIONAL` (`BlockReason.BLOCK_OS_DEV_DIRECTIONAL`) -> `freqtrade/user_data/strategies/GridBrainV1.py:7770`
- `BLOCK_OS_DEV_NEUTRAL_PERSISTENCE` (`BlockReason.BLOCK_OS_DEV_NEUTRAL_PERSISTENCE`) -> `freqtrade/user_data/strategies/GridBrainV1.py:7772`
- `BLOCK_POC_ALIGNMENT_FAIL` (`BlockReason.BLOCK_POC_ALIGNMENT_FAIL`) -> `freqtrade/user_data/strategies/GridBrainV1.py:1511`
- `BLOCK_RECLAIM_NOT_CONFIRMED` (`BlockReason.BLOCK_RECLAIM_NOT_CONFIRMED`) -> `freqtrade/user_data/strategies/GridBrainV1.py:5926`
- `BLOCK_RECLAIM_PENDING` (`BlockReason.BLOCK_RECLAIM_PENDING`) -> `freqtrade/user_data/strategies/GridBrainV1.py:8055`
- `BLOCK_RVOL_SPIKE` (`BlockReason.BLOCK_RVOL_SPIKE`) -> `freqtrade/user_data/strategies/GridBrainV1.py:1745`
- `BLOCK_SQUEEZE_RELEASE_AGAINST_BIAS` (`BlockReason.BLOCK_SQUEEZE_RELEASE_AGAINST_BIAS`) -> `freqtrade/user_data/strategies/GridBrainV1.py:1327`
- `BLOCK_STALE_FEATURES` (`BlockReason.BLOCK_STALE_FEATURES`) -> `freqtrade/user_data/strategies/GridBrainV1.py:7767`
- `BLOCK_START_BOX_POSITION` (`BlockReason.BLOCK_START_BOX_POSITION`) -> `freqtrade/user_data/strategies/GridBrainV1.py:7783`
- `BLOCK_START_PERSISTENCE_FAIL` (`BlockReason.BLOCK_START_PERSISTENCE_FAIL`) -> `freqtrade/user_data/strategies/GridBrainV1.py:7738`
- `BLOCK_START_RSI_BAND` (`BlockReason.BLOCK_START_RSI_BAND`) -> `freqtrade/user_data/strategies/GridBrainV1.py:7785`
- `BLOCK_START_STABILITY_LOW` (`BlockReason.BLOCK_START_STABILITY_LOW`) -> `freqtrade/user_data/strategies/GridBrainV1.py:8030`
- `BLOCK_STEP_BELOW_COST` (`BlockReason.BLOCK_STEP_BELOW_COST`) -> `freqtrade/user_data/strategies/GridBrainV1.py:6844`
- `BLOCK_STEP_BELOW_EMPIRICAL_COST` (`BlockReason.BLOCK_STEP_BELOW_EMPIRICAL_COST`) -> `freqtrade/user_data/strategies/GridBrainV1.py:6842`
- `BLOCK_VAH_VAL_POC_PROXIMITY` (`BlockReason.BLOCK_VAH_VAL_POC_PROXIMITY`) -> `freqtrade/user_data/strategies/GridBrainV1.py:7791`
- `BLOCK_VOL_BUCKET_UNSTABLE` (`BlockReason.BLOCK_VOL_BUCKET_UNSTABLE`) -> `freqtrade/user_data/strategies/GridBrainV1.py:8028`
- `BLOCK_ZERO_VOL_ANOMALY` (`BlockReason.BLOCK_ZERO_VOL_ANOMALY`) -> `data/data_quality_assessor.py:63`
- `COOLOFF_BBWP_EXTREME` (`BlockReason.COOLOFF_BBWP_EXTREME`) -> `freqtrade/user_data/strategies/GridBrainV1.py:7745`
- `EVENT_BREAKOUT_BEAR` (`EventType.EVENT_BREAKOUT_BEAR`) -> `freqtrade/user_data/strategies/GridBrainV1.py:8205`
- `EVENT_BREAKOUT_BULL` (`EventType.EVENT_BREAKOUT_BULL`) -> `freqtrade/user_data/strategies/GridBrainV1.py:8203`
- `EVENT_CHANNEL_MIDLINE_TOUCH` (`EventType.EVENT_CHANNEL_MIDLINE_TOUCH`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2931`
- `EVENT_CHANNEL_STRONG_BREAK_DN` (`EventType.EVENT_CHANNEL_STRONG_BREAK_DN`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2895`
- `EVENT_CHANNEL_STRONG_BREAK_UP` (`EventType.EVENT_CHANNEL_STRONG_BREAK_UP`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2894`
- `EVENT_CVD_BEAR_DIV` (`EventType.EVENT_CVD_BEAR_DIV`) -> `freqtrade/user_data/strategies/GridBrainV1.py:8245`
- `EVENT_CVD_BOS_DN` (`EventType.EVENT_CVD_BOS_DN`) -> `freqtrade/user_data/strategies/GridBrainV1.py:8249`
- `EVENT_CVD_BOS_UP` (`EventType.EVENT_CVD_BOS_UP`) -> `freqtrade/user_data/strategies/GridBrainV1.py:8247`
- `EVENT_CVD_BULL_DIV` (`EventType.EVENT_CVD_BULL_DIV`) -> `freqtrade/user_data/strategies/GridBrainV1.py:8243`
- `EVENT_DATA_GAP_DETECTED` (`EventType.EVENT_DATA_GAP_DETECTED`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2900`
- `EVENT_DATA_MISALIGN_DETECTED` (`EventType.EVENT_DATA_MISALIGN_DETECTED`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2901`
- `EVENT_DEPTH_THIN` (`EventType.EVENT_DEPTH_THIN`) -> `freqtrade/user_data/scripts/grid_executor_v1.py:1256`, `freqtrade/user_data/strategies/GridBrainV1.py:2907`
- `EVENT_DONCHIAN_STRONG_BREAK_DN` (`EventType.EVENT_DONCHIAN_STRONG_BREAK_DN`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2897`
- `EVENT_DONCHIAN_STRONG_BREAK_UP` (`EventType.EVENT_DONCHIAN_STRONG_BREAK_UP`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2896`
- `EVENT_FVG_POC_TAG` (`EventType.EVENT_FVG_POC_TAG`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2956`
- `EVENT_HVN_TOUCH` (`EventType.EVENT_HVN_TOUCH`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2962`
- `EVENT_JUMP_DETECTED` (`EventType.EVENT_JUMP_DETECTED`) -> `freqtrade/user_data/scripts/grid_executor_v1.py:1262`, `freqtrade/user_data/strategies/GridBrainV1.py:2908`
- `EVENT_LVN_TOUCH` (`EventType.EVENT_LVN_TOUCH`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2963`
- `EVENT_LVN_VOID_EXIT` (`EventType.EVENT_LVN_VOID_EXIT`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2964`
- `EVENT_META_DRIFT_HARD` (`EventType.EVENT_META_DRIFT_HARD`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2893`
- `EVENT_META_DRIFT_SOFT` (`EventType.EVENT_META_DRIFT_SOFT`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2905`
- `EVENT_MICRO_POC_SHIFT` (`EventType.EVENT_MICRO_POC_SHIFT`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2961`
- `EVENT_OB_NEW_BEAR` (`EventType.EVENT_OB_NEW_BEAR`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2950`
- `EVENT_OB_NEW_BULL` (`EventType.EVENT_OB_NEW_BULL`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2949`
- `EVENT_OB_TAGGED_BEAR` (`EventType.EVENT_OB_TAGGED_BEAR`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2952`
- `EVENT_OB_TAGGED_BULL` (`EventType.EVENT_OB_TAGGED_BULL`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2951`
- `EVENT_POST_ONLY_REJECT_BURST` (`EventType.EVENT_POST_ONLY_REJECT_BURST`) -> `freqtrade/user_data/scripts/grid_executor_v1.py:1124`, `freqtrade/user_data/strategies/GridBrainV1.py:2909`
- `EVENT_SESSION_HIGH_SWEEP` (`EventType.EVENT_SESSION_HIGH_SWEEP`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2941`
- `EVENT_SESSION_LOW_SWEEP` (`EventType.EVENT_SESSION_LOW_SWEEP`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2942`
- `EVENT_SPREAD_SPIKE` (`EventType.EVENT_SPREAD_SPIKE`) -> `freqtrade/user_data/scripts/grid_executor_v1.py:1250`, `freqtrade/user_data/strategies/GridBrainV1.py:2906`
- `EVENT_SWEEP_BREAK_RETEST_HIGH` (`EventType.EVENT_SWEEP_BREAK_RETEST_HIGH`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2898`, `planner/structure/liquidity_sweeps.py:308`
- `EVENT_SWEEP_BREAK_RETEST_LOW` (`EventType.EVENT_SWEEP_BREAK_RETEST_LOW`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2899`, `planner/structure/liquidity_sweeps.py:310`
- `EVENT_SWEEP_WICK_HIGH` (`EventType.EVENT_SWEEP_WICK_HIGH`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2937`, `planner/structure/liquidity_sweeps.py:304`
- `EVENT_SWEEP_WICK_LOW` (`EventType.EVENT_SWEEP_WICK_LOW`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2938`, `planner/structure/liquidity_sweeps.py:306`
- `EVENT_VRVP_POC_SHIFT` (`EventType.EVENT_VRVP_POC_SHIFT`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2960`
- `STOP_BREAKOUT_CONFIRM_DN` (`StopReason.STOP_BREAKOUT_CONFIRM_DN`) -> `freqtrade/user_data/strategies/GridBrainV1.py:1662`
- `STOP_BREAKOUT_CONFIRM_UP` (`StopReason.STOP_BREAKOUT_CONFIRM_UP`) -> `freqtrade/user_data/strategies/GridBrainV1.py:1657`
- `STOP_CHANNEL_STRONG_BREAK` (`StopReason.STOP_CHANNEL_STRONG_BREAK`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2928`
- `STOP_DRAWDOWN_GUARD` (`StopReason.STOP_DRAWDOWN_GUARD`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2922`
- `STOP_EXEC_CONFIRM_EXIT_FAILSAFE` (`StopReason.STOP_EXEC_CONFIRM_EXIT_FAILSAFE`) -> `freqtrade/user_data/scripts/grid_executor_v1.py:2498`
- `STOP_FVG_VOID_CONFLUENCE` (`StopReason.STOP_FVG_VOID_CONFLUENCE`) -> `freqtrade/user_data/strategies/GridBrainV1.py:7689`
- `STOP_LIQUIDITY_SWEEP_BREAK_RETEST` (`StopReason.STOP_LIQUIDITY_SWEEP_BREAK_RETEST`) -> `freqtrade/user_data/strategies/GridBrainV1.py:2943`
- `STOP_META_DRIFT_HARD` (`StopReason.STOP_META_DRIFT_HARD`) -> `freqtrade/user_data/strategies/GridBrainV1.py:519`
- `WARN_COST_MODEL_STALE` (`WarningCode.WARN_COST_MODEL_STALE`) -> `freqtrade/user_data/strategies/GridBrainV1.py:5032`
- `WARN_EXEC_POST_ONLY_RETRY_HIGH` (`WarningCode.WARN_EXEC_POST_ONLY_RETRY_HIGH`) -> `freqtrade/user_data/scripts/grid_executor_v1.py:1121`
- `WARN_VRVP_UNAVAILABLE_FALLBACK_POC` (`WarningCode.WARN_VRVP_UNAVAILABLE_FALLBACK_POC`) -> `freqtrade/user_data/strategies/GridBrainV1.py:8083`

### 4.2 Registry-Only Codes (Defined, No Runtime Reference Detected)

- `BLOCK_BOX_DONCHIAN_WIDTH_SANITY` (`BlockReason.BLOCK_BOX_DONCHIAN_WIDTH_SANITY`)
- `BLOCK_BOX_STRADDLE_HTF_POC` (`BlockReason.BLOCK_BOX_STRADDLE_HTF_POC`)
- `BLOCK_BOX_WIDTH_TOO_NARROW` (`BlockReason.BLOCK_BOX_WIDTH_TOO_NARROW`)
- `BLOCK_BREAKOUT_RECLAIM_PENDING` (`BlockReason.BLOCK_BREAKOUT_RECLAIM_PENDING`)
- `BLOCK_DATA_DUPLICATE_TS` (`BlockReason.BLOCK_DATA_DUPLICATE_TS`)
- `BLOCK_DATA_NON_MONOTONIC_TS` (`BlockReason.BLOCK_DATA_NON_MONOTONIC_TS`)
- `BLOCK_EXEC_CONFIRM_REBUILD_FAILED` (`BlockReason.BLOCK_EXEC_CONFIRM_REBUILD_FAILED`)
- `BLOCK_EXEC_CONFIRM_START_FAILED` (`BlockReason.BLOCK_EXEC_CONFIRM_START_FAILED`)
- `BLOCK_FRESH_FVG_COOLOFF` (`BlockReason.BLOCK_FRESH_FVG_COOLOFF`)
- `BLOCK_INSIDE_SESSION_FVG` (`BlockReason.BLOCK_INSIDE_SESSION_FVG`)
- `BLOCK_MIN_RUNTIME_NOT_MET` (`BlockReason.BLOCK_MIN_RUNTIME_NOT_MET`)
- `BLOCK_MRVD_CONFLUENCE_FAIL` (`BlockReason.BLOCK_MRVD_CONFLUENCE_FAIL`)
- `BLOCK_MRVD_POC_DRIFT_GUARD` (`BlockReason.BLOCK_MRVD_POC_DRIFT_GUARD`)
- `BLOCK_N_LEVELS_INVALID` (`BlockReason.BLOCK_N_LEVELS_INVALID`)
- `BLOCK_SESSION_FVG_PAUSE` (`BlockReason.BLOCK_SESSION_FVG_PAUSE`)
- `BLOCK_START_CONFLUENCE_LOW` (`BlockReason.BLOCK_START_CONFLUENCE_LOW`)
- `EVENT_BBWP_EXTREME` (`EventType.EVENT_BBWP_EXTREME`)
- `EVENT_CVD_SPIKE_NEG` (`EventType.EVENT_CVD_SPIKE_NEG`)
- `EVENT_CVD_SPIKE_POS` (`EventType.EVENT_CVD_SPIKE_POS`)
- `EVENT_DRIFT_RETEST_DN` (`EventType.EVENT_DRIFT_RETEST_DN`)
- `EVENT_DRIFT_RETEST_UP` (`EventType.EVENT_DRIFT_RETEST_UP`)
- `EVENT_EXTREME_RETEST_BOTTOM` (`EventType.EVENT_EXTREME_RETEST_BOTTOM`)
- `EVENT_EXTREME_RETEST_TOP` (`EventType.EVENT_EXTREME_RETEST_TOP`)
- `EVENT_EXT_1386_RETEST_BOTTOM` (`EventType.EVENT_EXT_1386_RETEST_BOTTOM`)
- `EVENT_EXT_1386_RETEST_TOP` (`EventType.EVENT_EXT_1386_RETEST_TOP`)
- `EVENT_FVG_MITIGATED_BEAR` (`EventType.EVENT_FVG_MITIGATED_BEAR`)
- `EVENT_FVG_MITIGATED_BULL` (`EventType.EVENT_FVG_MITIGATED_BULL`)
- `EVENT_FVG_NEW_BEAR` (`EventType.EVENT_FVG_NEW_BEAR`)
- `EVENT_FVG_NEW_BULL` (`EventType.EVENT_FVG_NEW_BULL`)
- `EVENT_IMFVG_AVG_TAG_BEAR` (`EventType.EVENT_IMFVG_AVG_TAG_BEAR`)
- `EVENT_IMFVG_AVG_TAG_BULL` (`EventType.EVENT_IMFVG_AVG_TAG_BULL`)
- `EVENT_PASSIVE_ABSORPTION_DN` (`EventType.EVENT_PASSIVE_ABSORPTION_DN`)
- `EVENT_PASSIVE_ABSORPTION_UP` (`EventType.EVENT_PASSIVE_ABSORPTION_UP`)
- `EVENT_POC_ACCEPTANCE_CROSS` (`EventType.EVENT_POC_ACCEPTANCE_CROSS`)
- `EVENT_POC_TEST` (`EventType.EVENT_POC_TEST`)
- `EVENT_RANGE_HIT_BOTTOM` (`EventType.EVENT_RANGE_HIT_BOTTOM`)
- `EVENT_RANGE_HIT_TOP` (`EventType.EVENT_RANGE_HIT_TOP`)
- `EVENT_RECLAIM_CONFIRMED` (`EventType.EVENT_RECLAIM_CONFIRMED`)
- `EVENT_SESSION_FVG_MITIGATED` (`EventType.EVENT_SESSION_FVG_MITIGATED`)
- `EVENT_SESSION_FVG_NEW` (`EventType.EVENT_SESSION_FVG_NEW`)
- `EVENT_SQUEEZE_RELEASE_DN` (`EventType.EVENT_SQUEEZE_RELEASE_DN`)
- `EVENT_SQUEEZE_RELEASE_UP` (`EventType.EVENT_SQUEEZE_RELEASE_UP`)
- `STOP_BREAKOUT_2STRIKE_DN` (`StopReason.STOP_BREAKOUT_2STRIKE_DN`)
- `STOP_BREAKOUT_2STRIKE_UP` (`StopReason.STOP_BREAKOUT_2STRIKE_UP`)
- `STOP_DATA_QUARANTINE` (`StopReason.STOP_DATA_QUARANTINE`)
- `STOP_FAST_MOVE_DN` (`StopReason.STOP_FAST_MOVE_DN`)
- `STOP_FAST_MOVE_UP` (`StopReason.STOP_FAST_MOVE_UP`)
- `STOP_FRESH_STRUCTURE` (`StopReason.STOP_FRESH_STRUCTURE`)
- `STOP_LVN_VOID_EXIT_ACCEL` (`StopReason.STOP_LVN_VOID_EXIT_ACCEL`)
- `STOP_MRVD_AVG_BREAK` (`StopReason.STOP_MRVD_AVG_BREAK`)
- `STOP_OS_DEV_DIRECTIONAL_FLIP` (`StopReason.STOP_OS_DEV_DIRECTIONAL_FLIP`)
- `STOP_RANGE_SHIFT` (`StopReason.STOP_RANGE_SHIFT`)
- `STOP_SESSION_FVG_AGAINST_BIAS` (`StopReason.STOP_SESSION_FVG_AGAINST_BIAS`)
- `STOP_SQUEEZE_RELEASE_AGAINST` (`StopReason.STOP_SQUEEZE_RELEASE_AGAINST`)
- `WARN_CVD_DATA_QUALITY_LOW` (`WarningCode.WARN_CVD_DATA_QUALITY_LOW`)
- `WARN_EXEC_REPRICE_RATE_HIGH` (`WarningCode.WARN_EXEC_REPRICE_RATE_HIGH`)
- `WARN_FEATURE_FALLBACK_USED` (`WarningCode.WARN_FEATURE_FALLBACK_USED`)
- `WARN_PARTIAL_DATA_WINDOW` (`WarningCode.WARN_PARTIAL_DATA_WINDOW`)
- `WARN_PLAN_EXPIRES_SOON` (`WarningCode.WARN_PLAN_EXPIRES_SOON`)

## 5) Complete Symbol Inventory (All Custom Python Files)

### `analytics/__init__.py`

- Top-level functions: `0`
- Classes: `0`

### `analytics/execution_cost_calibrator.py`

- Top-level functions: `0`
- Classes: `1`
- `EmpiricalCostCalibrator` (`analytics/execution_cost_calibrator.py:9`) -> attrs `0`, methods `4`
  - methods: `__init__` (`analytics/execution_cost_calibrator.py:14`), `_samples` (`analytics/execution_cost_calibrator.py:20`), `observe` (`analytics/execution_cost_calibrator.py:27`), `snapshot` (`analytics/execution_cost_calibrator.py:79`)

### `core/atomic_json.py`

- Top-level functions: `3`
- `_fsync_parent_dir` (`core/atomic_json.py:12`), `write_json_atomic` (`core/atomic_json.py:32`), `read_json_object` (`core/atomic_json.py:50`)
- Classes: `0`

### `core/enums.py`

- Top-level functions: `5`
- `is_canonical_code` (`core/enums.py:474`), `all_canonical_codes` (`core/enums.py:479`), `parse_canonical_code` (`core/enums.py:484`), `category_of_code` (`core/enums.py:495`), `ensure_canonical_codes` (`core/enums.py:506`)
- Classes: `14`
- `StrEnum` (`core/enums.py:18`) -> attrs `0`, methods `3`
  - methods: `__str__` (`core/enums.py:21`), `values` (`core/enums.py:25`), `has_value` (`core/enums.py:29`)
- `Severity` (`core/enums.py:34`) -> attrs `4`, methods `0`
  - attrs: `HARD` (`core/enums.py:35`), `SOFT` (`core/enums.py:36`), `ADVISORY` (`core/enums.py:37`), `INFO` (`core/enums.py:38`)
- `ActionContext` (`core/enums.py:42`) -> attrs `5`, methods `0`
  - attrs: `START` (`core/enums.py:43`), `HOLD` (`core/enums.py:44`), `STOP` (`core/enums.py:45`), `REBUILD` (`core/enums.py:46`), `NOOP` (`core/enums.py:47`)
- `MaterialityClass` (`core/enums.py:51`) -> attrs `4`, methods `0`
  - attrs: `NOOP` (`core/enums.py:52`), `SOFT` (`core/enums.py:53`), `MATERIAL` (`core/enums.py:54`), `HARDSTOP` (`core/enums.py:55`)
- `PlannerHealthState` (`core/enums.py:59`) -> attrs `3`, methods `0`
  - attrs: `OK` (`core/enums.py:60`), `DEGRADED` (`core/enums.py:61`), `QUARANTINE` (`core/enums.py:62`)
- `ModuleName` (`core/enums.py:66`) -> attrs `57`, methods `0`
  - attrs: `DATA_LOADER` (`core/enums.py:68`), `DATA_QUALITY_MONITOR` (`core/enums.py:69`), `MTF_MERGE_INTEGRITY` (`core/enums.py:70`), `FEATURE_PIPELINE` (`core/enums.py:71`), `ADX_GATE` (`core/enums.py:74`), `BBW_QUIETNESS_GATE` (`core/enums.py:75`), `EMA_COMPRESSION_GATE` (`core/enums.py:76`), `RVOL_GATE` (`core/enums.py:77`), `CONTEXT_7D_GATE` (`core/enums.py:78`), `BREAKOUT_FRESH_BLOCK` (`core/enums.py:79`), `BREAKOUT_RECLAIM_TIMER` (`core/enums.py:80`), `RANGE_DI_OS_DEV` (`core/enums.py:81`), `BAND_SLOPE_VETO` (`core/enums.py:82`), `DRIFT_SLOPE_VETO` (`core/enums.py:83`), `EXCURSION_ASYMMETRY_VETO` (`core/enums.py:84`), `META_DRIFT_GUARD` (`core/enums.py:85`), `BBWP_MTF_GATE` (`core/enums.py:86`), `SQUEEZE_STATE_GATE` (`core/enums.py:87`), `VOLATILITY_POLICY_ADAPTER` (`core/enums.py:88`), `BOX_BUILDER` (`core/enums.py:91`), `BOX_STRADDLE_VETO` (`core/enums.py:92`), `VRVP` (`core/enums.py:93`), `MICRO_VAP` (`core/enums.py:94`), `MRVD` (`core/enums.py:95`), `BASIS_PIVOTS` (`core/enums.py:96`), `DONCHIAN` (`core/enums.py:97`), `CHANNEL_MODULE` (`core/enums.py:98`), `OB_MODULE` (`core/enums.py:101`), `FVG_MODULE` (`core/enums.py:102`), `IMFVG_MODULE` (`core/enums.py:103`), `SESSION_FVG` (`core/enums.py:104`), `FVG_POSITIONING_AVG` (`core/enums.py:105`), `FVG_VP` (`core/enums.py:106`), `LIQUIDITY_SWEEPS` (`core/enums.py:107`), `POC_ACCEPTANCE_GATE` (`core/enums.py:110`), `START_STABILITY` (`core/enums.py:111`), `CONFLUENCE_AGGREGATOR` (`core/enums.py:112`), `COST_MODEL` (`core/enums.py:113`), `EMPIRICAL_COST_CALIBRATOR` (`core/enums.py:114`), `N_LEVEL_SELECTION` (`core/enums.py:115`), `TARGET_SELECTOR` (`core/enums.py:116`), `SL_SELECTOR` (`core/enums.py:117`), `STOP_FRAMEWORK` (`core/enums.py:120`), `RECLAIM_DISCIPLINE` (`core/enums.py:121`), `PROTECTIONS` (`core/enums.py:122`), `REPLAN_POLICY` (`core/enums.py:123`), `PLAN_ATOMIC_HANDOFF` (`core/enums.py:124`), `EXECUTOR` (`core/enums.py:127`), `CAPACITY_GUARD` (`core/enums.py:128`), `CONFIRM_ENTRY_HOOK` (`core/enums.py:129`), `CONFIRM_REBUILD_HOOK` (`core/enums.py:130`), `CONFIRM_EXIT_HOOK` (`core/enums.py:131`), `MAKER_FIRST_EXECUTION` (`core/enums.py:132`), `RECONCILE_ENGINE` (`core/enums.py:133`), `FILL_DEDUPE_GUARD` (`core/enums.py:134`), `CVD_MODULE` (`core/enums.py:137`), `HVP_GATE` (`core/enums.py:138`)
- `BlockReason` (`core/enums.py:145`) -> attrs `70`, methods `0`
  - attrs: `BLOCK_ADX_HIGH` (`core/enums.py:147`), `BLOCK_BBW_EXPANDING` (`core/enums.py:148`), `BLOCK_EMA_DIST` (`core/enums.py:149`), `BLOCK_RVOL_SPIKE` (`core/enums.py:150`), `BLOCK_7D_EXTREME_CONTEXT` (`core/enums.py:151`), `BLOCK_FRESH_BREAKOUT` (`core/enums.py:154`), `BLOCK_BREAKOUT_RECLAIM_PENDING` (`core/enums.py:155`), `BLOCK_BREAKOUT_CONFIRM_UP` (`core/enums.py:156`), `BLOCK_BREAKOUT_CONFIRM_DN` (`core/enums.py:157`), `BLOCK_MIN_RANGE_LEN_NOT_MET` (`core/enums.py:158`), `BLOCK_OS_DEV_DIRECTIONAL` (`core/enums.py:159`), `BLOCK_OS_DEV_NEUTRAL_PERSISTENCE` (`core/enums.py:160`), `BLOCK_BAND_SLOPE_HIGH` (`core/enums.py:161`), `BLOCK_DRIFT_SLOPE_HIGH` (`core/enums.py:162`), `BLOCK_EXCURSION_ASYMMETRY` (`core/enums.py:163`), `BLOCK_META_DRIFT_SOFT` (`core/enums.py:164`), `BLOCK_BBWP_HIGH` (`core/enums.py:167`), `COOLOFF_BBWP_EXTREME` (`core/enums.py:168`), `BLOCK_FUNDING_FILTER` (`core/enums.py:169`), `BLOCK_SQUEEZE_RELEASE_AGAINST_BIAS` (`core/enums.py:170`), `BLOCK_VOL_BUCKET_UNSTABLE` (`core/enums.py:171`), `BLOCK_BOX_WIDTH_TOO_NARROW` (`core/enums.py:174`), `BLOCK_BOX_WIDTH_TOO_WIDE` (`core/enums.py:175`), `BLOCK_BOX_STRADDLE_BREAKOUT_LEVEL` (`core/enums.py:176`), `BLOCK_BOX_STRADDLE_OB_EDGE` (`core/enums.py:177`), `BLOCK_BOX_STRADDLE_FVG_EDGE` (`core/enums.py:178`), `BLOCK_BOX_STRADDLE_FVG_AVG` (`core/enums.py:179`), `BLOCK_BOX_STRADDLE_SESSION_FVG_AVG` (`core/enums.py:180`), `BLOCK_BOX_OVERLAP_HIGH` (`core/enums.py:181`), `BLOCK_BOX_ENVELOPE_RATIO_HIGH` (`core/enums.py:182`), `BLOCK_BOX_STRADDLE_HTF_POC` (`core/enums.py:183`), `BLOCK_BOX_STRADDLE_VWAP_DONCHIAN_MID` (`core/enums.py:184`), `BLOCK_BOX_VP_POC_MISPLACED` (`core/enums.py:185`), `BLOCK_BOX_CHANNEL_OVERLAP_LOW` (`core/enums.py:186`), `BLOCK_BOX_DONCHIAN_WIDTH_SANITY` (`core/enums.py:187`), `BLOCK_NO_POC_ACCEPTANCE` (`core/enums.py:190`), `BLOCK_POC_ALIGNMENT_FAIL` (`core/enums.py:191`), `BLOCK_START_BOX_POSITION` (`core/enums.py:192`), `BLOCK_START_RSI_BAND` (`core/enums.py:193`), `BLOCK_START_CONFLUENCE_LOW` (`core/enums.py:194`), `BLOCK_START_STABILITY_LOW` (`core/enums.py:195`), `BLOCK_START_PERSISTENCE_FAIL` (`core/enums.py:196`), `BLOCK_BASIS_CROSS_PENDING` (`core/enums.py:197`), `BLOCK_VAH_VAL_POC_PROXIMITY` (`core/enums.py:198`), `BLOCK_MRVD_CONFLUENCE_FAIL` (`core/enums.py:199`), `BLOCK_MRVD_POC_DRIFT_GUARD` (`core/enums.py:200`), `BLOCK_STEP_BELOW_COST` (`core/enums.py:203`), `BLOCK_STEP_BELOW_EMPIRICAL_COST` (`core/enums.py:204`), `BLOCK_N_LEVELS_INVALID` (`core/enums.py:205`), `BLOCK_CAPACITY_THIN` (`core/enums.py:206`), `BLOCK_EXEC_CONFIRM_START_FAILED` (`core/enums.py:207`), `BLOCK_EXEC_CONFIRM_REBUILD_FAILED` (`core/enums.py:208`), `BLOCK_RECLAIM_PENDING` (`core/enums.py:211`), `BLOCK_RECLAIM_NOT_CONFIRMED` (`core/enums.py:212`), `BLOCK_COOLDOWN_ACTIVE` (`core/enums.py:213`), `BLOCK_MIN_RUNTIME_NOT_MET` (`core/enums.py:214`), `BLOCK_DRAWDOWN_GUARD` (`core/enums.py:215`), `BLOCK_MAX_STOPS_WINDOW` (`core/enums.py:216`), `BLOCK_DATA_GAP` (`core/enums.py:219`), `BLOCK_DATA_DUPLICATE_TS` (`core/enums.py:220`), `BLOCK_DATA_NON_MONOTONIC_TS` (`core/enums.py:221`), `BLOCK_DATA_MISALIGN` (`core/enums.py:222`), `BLOCK_ZERO_VOL_ANOMALY` (`core/enums.py:223`), `BLOCK_STALE_FEATURES` (`core/enums.py:224`), `BLOCK_FRESH_OB_COOLOFF` (`core/enums.py:227`), `BLOCK_FRESH_FVG_COOLOFF` (`core/enums.py:228`), `BLOCK_SESSION_FVG_PAUSE` (`core/enums.py:229`), `BLOCK_INSIDE_SESSION_FVG` (`core/enums.py:230`), `BLOCK_HVP_EXPANDING` (`core/enums.py:231`), `BLOCK_LIQ_SWEEP_OPPOSITE_STRUCTURE` (`core/enums.py:232`)
- `StopReason` (`core/enums.py:239`) -> attrs `20`, methods `0`
  - attrs: `STOP_BREAKOUT_2STRIKE_UP` (`core/enums.py:241`), `STOP_BREAKOUT_2STRIKE_DN` (`core/enums.py:242`), `STOP_BREAKOUT_CONFIRM_UP` (`core/enums.py:243`), `STOP_BREAKOUT_CONFIRM_DN` (`core/enums.py:244`), `STOP_FAST_MOVE_UP` (`core/enums.py:245`), `STOP_FAST_MOVE_DN` (`core/enums.py:246`), `STOP_RANGE_SHIFT` (`core/enums.py:247`), `STOP_FRESH_STRUCTURE` (`core/enums.py:248`), `STOP_SQUEEZE_RELEASE_AGAINST` (`core/enums.py:251`), `STOP_CHANNEL_STRONG_BREAK` (`core/enums.py:252`), `STOP_OS_DEV_DIRECTIONAL_FLIP` (`core/enums.py:253`), `STOP_META_DRIFT_HARD` (`core/enums.py:254`), `STOP_LVN_VOID_EXIT_ACCEL` (`core/enums.py:257`), `STOP_FVG_VOID_CONFLUENCE` (`core/enums.py:258`), `STOP_LIQUIDITY_SWEEP_BREAK_RETEST` (`core/enums.py:259`), `STOP_SESSION_FVG_AGAINST_BIAS` (`core/enums.py:260`), `STOP_MRVD_AVG_BREAK` (`core/enums.py:261`), `STOP_DRAWDOWN_GUARD` (`core/enums.py:264`), `STOP_EXEC_CONFIRM_EXIT_FAILSAFE` (`core/enums.py:265`), `STOP_DATA_QUARANTINE` (`core/enums.py:266`)
- `ReplanReason` (`core/enums.py:273`) -> attrs `9`, methods `0`
  - attrs: `REPLAN_NOOP_MINOR_DELTA` (`core/enums.py:275`), `REPLAN_SOFT_ADJUST_ONLY` (`core/enums.py:276`), `REPLAN_MATERIAL_BOX_CHANGE` (`core/enums.py:277`), `REPLAN_MATERIAL_GRID_CHANGE` (`core/enums.py:278`), `REPLAN_MATERIAL_RISK_CHANGE` (`core/enums.py:279`), `REPLAN_HARD_STOP_OVERRIDE` (`core/enums.py:280`), `REPLAN_EPOCH_DEFERRED` (`core/enums.py:283`), `REPLAN_DEFERRED_ACTIVE_FILL_WINDOW` (`core/enums.py:284`), `REPLAN_DUPLICATE_PLAN_HASH` (`core/enums.py:285`)
- `PauseReason` (`core/enums.py:292`) -> attrs `6`, methods `0`
  - attrs: `PAUSE_DATA_QUARANTINE` (`core/enums.py:293`), `PAUSE_DATA_DEGRADED` (`core/enums.py:294`), `PAUSE_META_DRIFT_SOFT` (`core/enums.py:295`), `PAUSE_BBWP_COOLOFF` (`core/enums.py:296`), `PAUSE_SESSION_FVG` (`core/enums.py:297`), `PAUSE_EXECUTION_UNSAFE` (`core/enums.py:298`)
- `WarningCode` (`core/enums.py:305`) -> attrs `8`, methods `0`
  - attrs: `WARN_COST_MODEL_STALE` (`core/enums.py:306`), `WARN_CVD_DATA_QUALITY_LOW` (`core/enums.py:307`), `WARN_VRVP_UNAVAILABLE_FALLBACK_POC` (`core/enums.py:308`), `WARN_FEATURE_FALLBACK_USED` (`core/enums.py:309`), `WARN_EXEC_POST_ONLY_RETRY_HIGH` (`core/enums.py:310`), `WARN_EXEC_REPRICE_RATE_HIGH` (`core/enums.py:311`), `WARN_PLAN_EXPIRES_SOON` (`core/enums.py:312`), `WARN_PARTIAL_DATA_WINDOW` (`core/enums.py:313`)
- `ExecCode` (`core/enums.py:320`) -> attrs `21`, methods `0`
  - attrs: `EXEC_PLAN_SCHEMA_INVALID` (`core/enums.py:322`), `EXEC_PLAN_HASH_MISMATCH` (`core/enums.py:323`), `EXEC_PLAN_DUPLICATE_IGNORED` (`core/enums.py:324`), `EXEC_PLAN_STALE_SEQ_IGNORED` (`core/enums.py:325`), `EXEC_PLAN_EXPIRED_IGNORED` (`core/enums.py:326`), `EXEC_PLAN_APPLIED` (`core/enums.py:327`), `EXEC_RECONCILE_START_LADDER_CREATED` (`core/enums.py:330`), `EXEC_RECONCILE_HOLD_NO_MATERIAL_CHANGE` (`core/enums.py:331`), `EXEC_RECONCILE_MATERIAL_REBUILD` (`core/enums.py:332`), `EXEC_RECONCILE_STOP_CANCELLED_LADDER` (`core/enums.py:333`), `EXEC_CAPACITY_RUNG_CAP_APPLIED` (`core/enums.py:334`), `EXEC_CAPACITY_NOTIONAL_CAP_APPLIED` (`core/enums.py:335`), `EXEC_CONFIRM_START_FAILED` (`core/enums.py:336`), `EXEC_CONFIRM_REBUILD_FAILED` (`core/enums.py:337`), `EXEC_CONFIRM_EXIT_FAILSAFE` (`core/enums.py:338`), `EXEC_POST_ONLY_RETRY` (`core/enums.py:341`), `EXEC_POST_ONLY_FALLBACK_REPRICE` (`core/enums.py:342`), `EXEC_ORDER_TIMEOUT_REPRICE` (`core/enums.py:343`), `EXEC_ORDER_CANCEL_REPLACE_APPLIED` (`core/enums.py:344`), `EXEC_FILL_REPLACEMENT_PLACED` (`core/enums.py:345`), `EXEC_FILL_DUPLICATE_GUARD_HIT` (`core/enums.py:346`)
- `EventType` (`core/enums.py:353`) -> attrs `61`, methods `0`
  - attrs: `EVENT_POC_TEST` (`core/enums.py:355`), `EVENT_POC_ACCEPTANCE_CROSS` (`core/enums.py:356`), `EVENT_EXTREME_RETEST_TOP` (`core/enums.py:357`), `EVENT_EXTREME_RETEST_BOTTOM` (`core/enums.py:358`), `EVENT_EXT_1386_RETEST_TOP` (`core/enums.py:359`), `EVENT_EXT_1386_RETEST_BOTTOM` (`core/enums.py:360`), `EVENT_RANGE_HIT_TOP` (`core/enums.py:361`), `EVENT_RANGE_HIT_BOTTOM` (`core/enums.py:362`), `EVENT_BREAKOUT_BULL` (`core/enums.py:365`), `EVENT_BREAKOUT_BEAR` (`core/enums.py:366`), `EVENT_RECLAIM_CONFIRMED` (`core/enums.py:367`), `EVENT_CHANNEL_STRONG_BREAK_UP` (`core/enums.py:368`), `EVENT_CHANNEL_STRONG_BREAK_DN` (`core/enums.py:369`), `EVENT_CHANNEL_MIDLINE_TOUCH` (`core/enums.py:370`), `EVENT_DONCHIAN_STRONG_BREAK_UP` (`core/enums.py:371`), `EVENT_DONCHIAN_STRONG_BREAK_DN` (`core/enums.py:372`), `EVENT_DRIFT_RETEST_UP` (`core/enums.py:373`), `EVENT_DRIFT_RETEST_DN` (`core/enums.py:374`), `EVENT_SWEEP_WICK_HIGH` (`core/enums.py:377`), `EVENT_SWEEP_WICK_LOW` (`core/enums.py:378`), `EVENT_SWEEP_BREAK_RETEST_HIGH` (`core/enums.py:379`), `EVENT_SWEEP_BREAK_RETEST_LOW` (`core/enums.py:380`), `EVENT_SESSION_HIGH_SWEEP` (`core/enums.py:381`), `EVENT_SESSION_LOW_SWEEP` (`core/enums.py:382`), `EVENT_FVG_NEW_BULL` (`core/enums.py:385`), `EVENT_FVG_NEW_BEAR` (`core/enums.py:386`), `EVENT_FVG_MITIGATED_BULL` (`core/enums.py:387`), `EVENT_FVG_MITIGATED_BEAR` (`core/enums.py:388`), `EVENT_IMFVG_AVG_TAG_BULL` (`core/enums.py:389`), `EVENT_IMFVG_AVG_TAG_BEAR` (`core/enums.py:390`), `EVENT_SESSION_FVG_NEW` (`core/enums.py:391`), `EVENT_SESSION_FVG_MITIGATED` (`core/enums.py:392`), `EVENT_OB_NEW_BULL` (`core/enums.py:393`), `EVENT_OB_NEW_BEAR` (`core/enums.py:394`), `EVENT_OB_TAGGED_BULL` (`core/enums.py:395`), `EVENT_OB_TAGGED_BEAR` (`core/enums.py:396`), `EVENT_VRVP_POC_SHIFT` (`core/enums.py:399`), `EVENT_MICRO_POC_SHIFT` (`core/enums.py:400`), `EVENT_HVN_TOUCH` (`core/enums.py:401`), `EVENT_LVN_TOUCH` (`core/enums.py:402`), `EVENT_LVN_VOID_EXIT` (`core/enums.py:403`), `EVENT_FVG_POC_TAG` (`core/enums.py:404`), `EVENT_CVD_BULL_DIV` (`core/enums.py:407`), `EVENT_CVD_BEAR_DIV` (`core/enums.py:408`), `EVENT_CVD_BOS_UP` (`core/enums.py:409`), `EVENT_CVD_BOS_DN` (`core/enums.py:410`), `EVENT_CVD_SPIKE_POS` (`core/enums.py:411`), `EVENT_CVD_SPIKE_NEG` (`core/enums.py:412`), `EVENT_PASSIVE_ABSORPTION_UP` (`core/enums.py:413`), `EVENT_PASSIVE_ABSORPTION_DN` (`core/enums.py:414`), `EVENT_META_DRIFT_SOFT` (`core/enums.py:415`), `EVENT_META_DRIFT_HARD` (`core/enums.py:416`), `EVENT_BBWP_EXTREME` (`core/enums.py:417`), `EVENT_SQUEEZE_RELEASE_UP` (`core/enums.py:418`), `EVENT_SQUEEZE_RELEASE_DN` (`core/enums.py:419`), `EVENT_SPREAD_SPIKE` (`core/enums.py:422`), `EVENT_DEPTH_THIN` (`core/enums.py:423`), `EVENT_JUMP_DETECTED` (`core/enums.py:424`), `EVENT_POST_ONLY_REJECT_BURST` (`core/enums.py:425`), `EVENT_DATA_GAP_DETECTED` (`core/enums.py:426`), `EVENT_DATA_MISALIGN_DETECTED` (`core/enums.py:427`)
- `InfoCode` (`core/enums.py:434`) -> attrs `5`, methods `0`
  - attrs: `INFO_VOL_BUCKET_CHANGED` (`core/enums.py:435`), `INFO_BOX_SHIFT_APPLIED` (`core/enums.py:436`), `INFO_TARGET_SOURCE_SELECTED` (`core/enums.py:437`), `INFO_SL_SOURCE_SELECTED` (`core/enums.py:438`), `INFO_REPLAN_EPOCH_BOUNDARY` (`core/enums.py:439`)

### `core/plan_signature.py`

- Top-level functions: `14`
- `_canonical_json` (`core/plan_signature.py:51`), `stable_payload_hash` (`core/plan_signature.py:55`), `material_plan_payload` (`core/plan_signature.py:60`), `compute_plan_hash` (`core/plan_signature.py:64`), `_is_sequence` (`core/plan_signature.py:68`), `_material_diff_entries` (`core/plan_signature.py:72`), `material_plan_diff_entries` (`core/plan_signature.py:105`), `material_plan_changed_fields` (`core/plan_signature.py:116`), `material_plan_diff_snapshot` (`core/plan_signature.py:123`), `_parse_iso8601` (`core/plan_signature.py:143`), `_parse_optional_datetime` (`core/plan_signature.py:158`), `validate_signature_fields` (`core/plan_signature.py:169`), `plan_is_expired` (`core/plan_signature.py:220`), `plan_pair` (`core/plan_signature.py:235`)
- Classes: `0`

### `core/schema_validation.py`

- Top-level functions: `4`
- `_format_error` (`core/schema_validation.py:19`), `schema_path` (`core/schema_validation.py:25`), `_load_schema` (`core/schema_validation.py:30`), `validate_schema` (`core/schema_validation.py:38`)
- Classes: `0`

### `data/__init__.py`

- Top-level functions: `0`
- Classes: `0`

### `data/data_quality_assessor.py`

- Top-level functions: `1`
- `assess_data_quality` (`data/data_quality_assessor.py:12`)
- Classes: `0`

### `execution/__init__.py`

- Top-level functions: `0`
- Classes: `0`

### `execution/capacity_guard.py`

- Top-level functions: `4`
- `load_capacity_hint_state` (`execution/capacity_guard.py:9`), `_as_float` (`execution/capacity_guard.py:48`), `_as_int` (`execution/capacity_guard.py:57`), `compute_dynamic_capacity_state` (`execution/capacity_guard.py:66`)
- Classes: `0`

### `freqtrade/user_data/scripts/grid_executor_v1.py`

- Top-level functions: `22`
- `log_event` (`freqtrade/user_data/scripts/grid_executor_v1.py:26`), `_log_plan_marker` (`freqtrade/user_data/scripts/grid_executor_v1.py:40`), `_plan_context` (`freqtrade/user_data/scripts/grid_executor_v1.py:49`), `load_json` (`freqtrade/user_data/scripts/grid_executor_v1.py:130`), `write_json` (`freqtrade/user_data/scripts/grid_executor_v1.py:135`), `_round_to_tick` (`freqtrade/user_data/scripts/grid_executor_v1.py:143`), `build_levels` (`freqtrade/user_data/scripts/grid_executor_v1.py:149`), `plan_signature` (`freqtrade/user_data/scripts/grid_executor_v1.py:167`), `soft_adjust_ok` (`freqtrade/user_data/scripts/grid_executor_v1.py:201`), `_action_signature` (`freqtrade/user_data/scripts/grid_executor_v1.py:230`), `quantize_price` (`freqtrade/user_data/scripts/grid_executor_v1.py:237`), `quantize_amount` (`freqtrade/user_data/scripts/grid_executor_v1.py:243`), `market_limits` (`freqtrade/user_data/scripts/grid_executor_v1.py:249`), `passes_min_notional` (`freqtrade/user_data/scripts/grid_executor_v1.py:267`), `_key_for` (`freqtrade/user_data/scripts/grid_executor_v1.py:274`), `_safe_float` (`freqtrade/user_data/scripts/grid_executor_v1.py:281`), `_safe_int` (`freqtrade/user_data/scripts/grid_executor_v1.py:290`), `_safe_bool` (`freqtrade/user_data/scripts/grid_executor_v1.py:299`), `_pair_fs` (`freqtrade/user_data/scripts/grid_executor_v1.py:316`), `_extract_rung_weights` (`freqtrade/user_data/scripts/grid_executor_v1.py:320`), `_normalized_side_weights` (`freqtrade/user_data/scripts/grid_executor_v1.py:352`), `main` (`freqtrade/user_data/scripts/grid_executor_v1.py:2829`)
- Classes: `4`
- `RestingOrder` (`freqtrade/user_data/scripts/grid_executor_v1.py:81`) -> attrs `7`, methods `0`
  - attrs: `side` (`freqtrade/user_data/scripts/grid_executor_v1.py:82`), `price` (`freqtrade/user_data/scripts/grid_executor_v1.py:83`), `qty_base` (`freqtrade/user_data/scripts/grid_executor_v1.py:84`), `level_index` (`freqtrade/user_data/scripts/grid_executor_v1.py:85`), `order_id` (`freqtrade/user_data/scripts/grid_executor_v1.py:86`), `status` (`freqtrade/user_data/scripts/grid_executor_v1.py:87`), `filled_base` (`freqtrade/user_data/scripts/grid_executor_v1.py:90`)
- `ExecutorState` (`freqtrade/user_data/scripts/grid_executor_v1.py:94`) -> attrs `26`, methods `0`
  - attrs: `schema_version` (`freqtrade/user_data/scripts/grid_executor_v1.py:95`), `ts` (`freqtrade/user_data/scripts/grid_executor_v1.py:96`), `exchange` (`freqtrade/user_data/scripts/grid_executor_v1.py:97`), `pair` (`freqtrade/user_data/scripts/grid_executor_v1.py:98`), `symbol` (`freqtrade/user_data/scripts/grid_executor_v1.py:99`), `plan_ts` (`freqtrade/user_data/scripts/grid_executor_v1.py:100`), `mode` (`freqtrade/user_data/scripts/grid_executor_v1.py:101`), `last_applied_plan_id` (`freqtrade/user_data/scripts/grid_executor_v1.py:102`), `last_applied_seq` (`freqtrade/user_data/scripts/grid_executor_v1.py:103`), `last_applied_valid_for_candle_ts` (`freqtrade/user_data/scripts/grid_executor_v1.py:104`), `last_plan_hash` (`freqtrade/user_data/scripts/grid_executor_v1.py:105`), `executor_state_machine` (`freqtrade/user_data/scripts/grid_executor_v1.py:106`), `step` (`freqtrade/user_data/scripts/grid_executor_v1.py:108`), `n_levels` (`freqtrade/user_data/scripts/grid_executor_v1.py:109`), `box_low` (`freqtrade/user_data/scripts/grid_executor_v1.py:110`), `box_high` (`freqtrade/user_data/scripts/grid_executor_v1.py:111`), `quote_total` (`freqtrade/user_data/scripts/grid_executor_v1.py:113`), `base_total` (`freqtrade/user_data/scripts/grid_executor_v1.py:114`), `quote_free` (`freqtrade/user_data/scripts/grid_executor_v1.py:116`), `base_free` (`freqtrade/user_data/scripts/grid_executor_v1.py:117`), `quote_reserved` (`freqtrade/user_data/scripts/grid_executor_v1.py:118`), `base_reserved` (`freqtrade/user_data/scripts/grid_executor_v1.py:119`), `runtime` (`freqtrade/user_data/scripts/grid_executor_v1.py:121`), `orders` (`freqtrade/user_data/scripts/grid_executor_v1.py:122`), `applied_plan_ids` (`freqtrade/user_data/scripts/grid_executor_v1.py:123`), `applied_plan_hashes` (`freqtrade/user_data/scripts/grid_executor_v1.py:124`)
- `FillCooldownGuard` (`freqtrade/user_data/scripts/grid_executor_v1.py:365`) -> attrs `0`, methods `4`
  - methods: `__init__` (`freqtrade/user_data/scripts/grid_executor_v1.py:366`), `configure` (`freqtrade/user_data/scripts/grid_executor_v1.py:371`), `allow` (`freqtrade/user_data/scripts/grid_executor_v1.py:382`), `mark` (`freqtrade/user_data/scripts/grid_executor_v1.py:390`)
- `GridExecutorV1` (`freqtrade/user_data/scripts/grid_executor_v1.py:399`) -> attrs `0`, methods `48`
  - methods: `__init__` (`freqtrade/user_data/scripts/grid_executor_v1.py:411`), `_reserved_balances_intent` (`freqtrade/user_data/scripts/grid_executor_v1.py:577`), `_free_balances_intent` (`freqtrade/user_data/scripts/grid_executor_v1.py:594`), `_sync_balance_ccxt` (`freqtrade/user_data/scripts/grid_executor_v1.py:598`), `_recover_state_from_disk` (`freqtrade/user_data/scripts/grid_executor_v1.py:626`), `_reset_runtime_diagnostics` (`freqtrade/user_data/scripts/grid_executor_v1.py:721`), `_append_runtime_warning` (`freqtrade/user_data/scripts/grid_executor_v1.py:740`), `_append_runtime_exec_event` (`freqtrade/user_data/scripts/grid_executor_v1.py:745`), `_append_runtime_pause_reason` (`freqtrade/user_data/scripts/grid_executor_v1.py:750`), `_remember_applied_plan_id` (`freqtrade/user_data/scripts/grid_executor_v1.py:755`), `_remember_applied_plan_hash` (`freqtrade/user_data/scripts/grid_executor_v1.py:765`), `_record_applied_plan` (`freqtrade/user_data/scripts/grid_executor_v1.py:775`), `_reject_plan_intake` (`freqtrade/user_data/scripts/grid_executor_v1.py:798`), `_validate_plan_intake` (`freqtrade/user_data/scripts/grid_executor_v1.py:814`), `_write_rejected_plan_state` (`freqtrade/user_data/scripts/grid_executor_v1.py:912`), `_execution_cfg` (`freqtrade/user_data/scripts/grid_executor_v1.py:924`), `_apply_execution_hardening_config` (`freqtrade/user_data/scripts/grid_executor_v1.py:937`), `_prune_post_only_reject_window` (`freqtrade/user_data/scripts/grid_executor_v1.py:1107`), `_register_post_only_reject` (`freqtrade/user_data/scripts/grid_executor_v1.py:1112`), `_post_only_burst_status` (`freqtrade/user_data/scripts/grid_executor_v1.py:1137`), `_is_post_only_reject_error` (`freqtrade/user_data/scripts/grid_executor_v1.py:1157`), `_tick_for_price` (`freqtrade/user_data/scripts/grid_executor_v1.py:1172`), `_reprice_post_only_price` (`freqtrade/user_data/scripts/grid_executor_v1.py:1178`), `_confirm_metrics` (`freqtrade/user_data/scripts/grid_executor_v1.py:1187`), `_run_confirm_hook` (`freqtrade/user_data/scripts/grid_executor_v1.py:1213`), `_extract_capacity_inputs` (`freqtrade/user_data/scripts/grid_executor_v1.py:1277`), `_compute_capacity_state` (`freqtrade/user_data/scripts/grid_executor_v1.py:1357`), `_enforce_capacity_rung_cap` (`freqtrade/user_data/scripts/grid_executor_v1.py:1413`), `_execution_cost_paths` (`freqtrade/user_data/scripts/grid_executor_v1.py:1461`), `_append_jsonl` (`freqtrade/user_data/scripts/grid_executor_v1.py:1480`), `_record_order_lifecycle_event` (`freqtrade/user_data/scripts/grid_executor_v1.py:1486`), `_record_fill_lifecycle_event` (`freqtrade/user_data/scripts/grid_executor_v1.py:1529`), `_publish_execution_cost_artifact` (`freqtrade/user_data/scripts/grid_executor_v1.py:1579`), `_order_match_tolerant` (`freqtrade/user_data/scripts/grid_executor_v1.py:1691`), `_ccxt_call` (`freqtrade/user_data/scripts/grid_executor_v1.py:1719`), `_desired_initial_ladder` (`freqtrade/user_data/scripts/grid_executor_v1.py:1753`), `_ccxt_fetch_open_orders` (`freqtrade/user_data/scripts/grid_executor_v1.py:1820`), `_ccxt_cancel_order` (`freqtrade/user_data/scripts/grid_executor_v1.py:1828`), `_ccxt_place_limit` (`freqtrade/user_data/scripts/grid_executor_v1.py:1836`), `_ccxt_reconcile_set` (`freqtrade/user_data/scripts/grid_executor_v1.py:1952`), `_levels_for_index` (`freqtrade/user_data/scripts/grid_executor_v1.py:2092`), `_next_fill_bar_index` (`freqtrade/user_data/scripts/grid_executor_v1.py:2097`), `_extract_exit_levels` (`freqtrade/user_data/scripts/grid_executor_v1.py:2112`), `_find_order_by_id` (`freqtrade/user_data/scripts/grid_executor_v1.py:2138`), `_ingest_trades_and_replenish` (`freqtrade/user_data/scripts/grid_executor_v1.py:2144`), `step` (`freqtrade/user_data/scripts/grid_executor_v1.py:2328`), `_executor_state_machine` (`freqtrade/user_data/scripts/grid_executor_v1.py:2730`), `_write_state` (`freqtrade/user_data/scripts/grid_executor_v1.py:2741`)

### `freqtrade/user_data/scripts/grid_simulator_v1.py`

- Top-level functions: `40`
- `log_event` (`freqtrade/user_data/scripts/grid_simulator_v1.py:18`), `_log_plan_marker` (`freqtrade/user_data/scripts/grid_simulator_v1.py:32`), `_plan_context` (`freqtrade/user_data/scripts/grid_simulator_v1.py:41`), `find_ohlcv_file` (`freqtrade/user_data/scripts/grid_simulator_v1.py:61`), `load_ohlcv` (`freqtrade/user_data/scripts/grid_simulator_v1.py:88`), `filter_timerange` (`freqtrade/user_data/scripts/grid_simulator_v1.py:132`), `parse_start_at` (`freqtrade/user_data/scripts/grid_simulator_v1.py:147`), `_round_to_tick` (`freqtrade/user_data/scripts/grid_simulator_v1.py:254`), `build_levels` (`freqtrade/user_data/scripts/grid_simulator_v1.py:260`), `_normalize_fill_mode` (`freqtrade/user_data/scripts/grid_simulator_v1.py:279`), `_fill_trigger` (`freqtrade/user_data/scripts/grid_simulator_v1.py:288`), `_touched_index_bounds` (`freqtrade/user_data/scripts/grid_simulator_v1.py:299`), `_safe_float` (`freqtrade/user_data/scripts/grid_simulator_v1.py:370`), `_safe_int` (`freqtrade/user_data/scripts/grid_simulator_v1.py:379`), `_clamp_probability` (`freqtrade/user_data/scripts/grid_simulator_v1.py:388`), `_build_chaos_runtime_config` (`freqtrade/user_data/scripts/grid_simulator_v1.py:418`), `_uniform_int_inclusive` (`freqtrade/user_data/scripts/grid_simulator_v1.py:496`), `extract_rung_weights` (`freqtrade/user_data/scripts/grid_simulator_v1.py:502`), `normalized_side_weights` (`freqtrade/user_data/scripts/grid_simulator_v1.py:546`), `plan_signature` (`freqtrade/user_data/scripts/grid_simulator_v1.py:564`), `soft_adjust_ok` (`freqtrade/user_data/scripts/grid_simulator_v1.py:584`), `action_signature` (`freqtrade/user_data/scripts/grid_simulator_v1.py:607`), `extract_exit_levels` (`freqtrade/user_data/scripts/grid_simulator_v1.py:614`), `plan_effective_time` (`freqtrade/user_data/scripts/grid_simulator_v1.py:644`), `load_plan_sequence` (`freqtrade/user_data/scripts/grid_simulator_v1.py:669`), `_uniq_reasons` (`freqtrade/user_data/scripts/grid_simulator_v1.py:732`), `_increment_reason` (`freqtrade/user_data/scripts/grid_simulator_v1.py:744`), `_increment_reasons` (`freqtrade/user_data/scripts/grid_simulator_v1.py:753`), `_sorted_reason_counts` (`freqtrade/user_data/scripts/grid_simulator_v1.py:758`), `_normalize_router_mode` (`freqtrade/user_data/scripts/grid_simulator_v1.py:762`), `_normalize_replan_decision` (`freqtrade/user_data/scripts/grid_simulator_v1.py:769`), `_normalize_materiality_class` (`freqtrade/user_data/scripts/grid_simulator_v1.py:776`), `extract_start_block_reasons` (`freqtrade/user_data/scripts/grid_simulator_v1.py:783`), `extract_start_counterfactual` (`freqtrade/user_data/scripts/grid_simulator_v1.py:813`), `extract_stop_reason_flags` (`freqtrade/user_data/scripts/grid_simulator_v1.py:894`), `build_desired_ladder` (`freqtrade/user_data/scripts/grid_simulator_v1.py:914`), `simulate_grid` (`freqtrade/user_data/scripts/grid_simulator_v1.py:964`), `simulate_grid_replay` (`freqtrade/user_data/scripts/grid_simulator_v1.py:1229`), `load_plan` (`freqtrade/user_data/scripts/grid_simulator_v1.py:2175`), `main` (`freqtrade/user_data/scripts/grid_simulator_v1.py:2180`)
- Classes: `4`
- `OrderSim` (`freqtrade/user_data/scripts/grid_simulator_v1.py:236`) -> attrs `5`, methods `0`
  - attrs: `side` (`freqtrade/user_data/scripts/grid_simulator_v1.py:237`), `price` (`freqtrade/user_data/scripts/grid_simulator_v1.py:238`), `qty_base` (`freqtrade/user_data/scripts/grid_simulator_v1.py:239`), `level_index` (`freqtrade/user_data/scripts/grid_simulator_v1.py:240`), `status` (`freqtrade/user_data/scripts/grid_simulator_v1.py:241`)
- `FillSim` (`freqtrade/user_data/scripts/grid_simulator_v1.py:245`) -> attrs `6`, methods `0`
  - attrs: `ts_utc` (`freqtrade/user_data/scripts/grid_simulator_v1.py:246`), `side` (`freqtrade/user_data/scripts/grid_simulator_v1.py:247`), `price` (`freqtrade/user_data/scripts/grid_simulator_v1.py:248`), `qty_base` (`freqtrade/user_data/scripts/grid_simulator_v1.py:249`), `fee_quote` (`freqtrade/user_data/scripts/grid_simulator_v1.py:250`), `reason` (`freqtrade/user_data/scripts/grid_simulator_v1.py:251`)
- `FillCooldownGuard` (`freqtrade/user_data/scripts/grid_simulator_v1.py:339`) -> attrs `0`, methods `4`
  - methods: `__init__` (`freqtrade/user_data/scripts/grid_simulator_v1.py:340`), `configure` (`freqtrade/user_data/scripts/grid_simulator_v1.py:345`), `allow` (`freqtrade/user_data/scripts/grid_simulator_v1.py:356`), `mark` (`freqtrade/user_data/scripts/grid_simulator_v1.py:364`)
- `ChaosRuntimeConfig` (`freqtrade/user_data/scripts/grid_simulator_v1.py:396`) -> attrs `19`, methods `0`
  - attrs: `profile_id` (`freqtrade/user_data/scripts/grid_simulator_v1.py:397`), `name` (`freqtrade/user_data/scripts/grid_simulator_v1.py:398`), `enabled` (`freqtrade/user_data/scripts/grid_simulator_v1.py:399`), `seed` (`freqtrade/user_data/scripts/grid_simulator_v1.py:400`), `latency_mean_ms` (`freqtrade/user_data/scripts/grid_simulator_v1.py:401`), `latency_jitter_ms` (`freqtrade/user_data/scripts/grid_simulator_v1.py:402`), `latency_fill_window_ms` (`freqtrade/user_data/scripts/grid_simulator_v1.py:403`), `spread_base_bps` (`freqtrade/user_data/scripts/grid_simulator_v1.py:404`), `spread_burst_bps` (`freqtrade/user_data/scripts/grid_simulator_v1.py:405`), `spread_burst_probability` (`freqtrade/user_data/scripts/grid_simulator_v1.py:406`), `partial_fill_probability` (`freqtrade/user_data/scripts/grid_simulator_v1.py:407`), `partial_fill_min_ratio` (`freqtrade/user_data/scripts/grid_simulator_v1.py:408`), `partial_fill_max_ratio` (`freqtrade/user_data/scripts/grid_simulator_v1.py:409`), `reject_burst_probability` (`freqtrade/user_data/scripts/grid_simulator_v1.py:410`), `reject_burst_min_bars` (`freqtrade/user_data/scripts/grid_simulator_v1.py:411`), `reject_burst_max_bars` (`freqtrade/user_data/scripts/grid_simulator_v1.py:412`), `delayed_candle_probability` (`freqtrade/user_data/scripts/grid_simulator_v1.py:413`), `missing_candle_probability` (`freqtrade/user_data/scripts/grid_simulator_v1.py:414`), `data_gap_probability` (`freqtrade/user_data/scripts/grid_simulator_v1.py:415`)

### `freqtrade/user_data/scripts/regime_audit_v1.py`

- Top-level functions: `26`
- `find_ohlcv_file` (`freqtrade/user_data/scripts/regime_audit_v1.py:45`), `load_ohlcv` (`freqtrade/user_data/scripts/regime_audit_v1.py:60`), `filter_timerange` (`freqtrade/user_data/scripts/regime_audit_v1.py:92`), `bb_width` (`freqtrade/user_data/scripts/regime_audit_v1.py:103`), `atr_series` (`freqtrade/user_data/scripts/regime_audit_v1.py:111`), `efficiency_ratio_series` (`freqtrade/user_data/scripts/regime_audit_v1.py:119`), `choppiness_index_series` (`freqtrade/user_data/scripts/regime_audit_v1.py:136`), `adx_wilder` (`freqtrade/user_data/scripts/regime_audit_v1.py:164`), `rolling_percentile_last` (`freqtrade/user_data/scripts/regime_audit_v1.py:185`), `future_roll_max` (`freqtrade/user_data/scripts/regime_audit_v1.py:204`), `future_roll_min` (`freqtrade/user_data/scripts/regime_audit_v1.py:209`), `resample_ohlcv` (`freqtrade/user_data/scripts/regime_audit_v1.py:214`), `build_feature_frame` (`freqtrade/user_data/scripts/regime_audit_v1.py:233`), `add_labels` (`freqtrade/user_data/scripts/regime_audit_v1.py:303`), `qval` (`freqtrade/user_data/scripts/regime_audit_v1.py:340`), `assign_non_trend_mask` (`freqtrade/user_data/scripts/regime_audit_v1.py:347`), `percentile_stats` (`freqtrade/user_data/scripts/regime_audit_v1.py:369`), `normalize_series` (`freqtrade/user_data/scripts/regime_audit_v1.py:380`), `feature_quantiles` (`freqtrade/user_data/scripts/regime_audit_v1.py:392`), `recommend_mode_thresholds` (`freqtrade/user_data/scripts/regime_audit_v1.py:410`), `label_counts` (`freqtrade/user_data/scripts/regime_audit_v1.py:429`), `add_verbose_states` (`freqtrade/user_data/scripts/regime_audit_v1.py:444`), `extract_transition_events` (`freqtrade/user_data/scripts/regime_audit_v1.py:506`), `transition_counts` (`freqtrade/user_data/scripts/regime_audit_v1.py:552`), `median_state_run_length` (`freqtrade/user_data/scripts/regime_audit_v1.py:562`), `main` (`freqtrade/user_data/scripts/regime_audit_v1.py:577`)
- Classes: `0`

### `freqtrade/user_data/scripts/user_regression_suite.py`

- Top-level functions: `13`
- `_require` (`freqtrade/user_data/scripts/user_regression_suite.py:39`), `_plan_get` (`freqtrade/user_data/scripts/user_regression_suite.py:44`), `run_stress_replay_validation` (`freqtrade/user_data/scripts/user_regression_suite.py:53`), `check_plan_schema_and_feature_outputs` (`freqtrade/user_data/scripts/user_regression_suite.py:78`), `check_recent_plan_history` (`freqtrade/user_data/scripts/user_regression_suite.py:218`), `_base_paper_executor` (`freqtrade/user_data/scripts/user_regression_suite.py:258`), `_force_ref_inside_box` (`freqtrade/user_data/scripts/user_regression_suite.py:280`), `check_executor_action_semantics` (`freqtrade/user_data/scripts/user_regression_suite.py:290`), `check_weighted_ladder_and_simulator` (`freqtrade/user_data/scripts/user_regression_suite.py:342`), `check_ml_overlay_behavior` (`freqtrade/user_data/scripts/user_regression_suite.py:483`), `check_adx_hysteresis_behavior` (`freqtrade/user_data/scripts/user_regression_suite.py:547`), `check_mode_router_handoff_behavior` (`freqtrade/user_data/scripts/user_regression_suite.py:603`), `main` (`freqtrade/user_data/scripts/user_regression_suite.py:722`)
- Classes: `0`

### `freqtrade/user_data/strategies/GridBrainV1.py`

- Top-level functions: `1`
- `_normalize_runtime_value` (`freqtrade/user_data/strategies/GridBrainV1.py:82`)
- Classes: `6`
- `EmpiricalCostCalibrator` (`freqtrade/user_data/strategies/GridBrainV1.py:98`) -> attrs `0`, methods `4`
  - methods: `__init__` (`freqtrade/user_data/strategies/GridBrainV1.py:106`), `_samples` (`freqtrade/user_data/strategies/GridBrainV1.py:112`), `observe` (`freqtrade/user_data/strategies/GridBrainV1.py:119`), `snapshot` (`freqtrade/user_data/strategies/GridBrainV1.py:161`)
- `MetaDriftGuard` (`freqtrade/user_data/strategies/GridBrainV1.py:243`) -> attrs `0`, methods `4`
  - methods: `__init__` (`freqtrade/user_data/strategies/GridBrainV1.py:246`), `reset_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:251`), `_pair_state` (`freqtrade/user_data/strategies/GridBrainV1.py:254`), `observe` (`freqtrade/user_data/strategies/GridBrainV1.py:264`)
- `GridBrainRuntimeSnapshot` (`freqtrade/user_data/strategies/GridBrainV1.py:419`) -> attrs `3`, methods `2`
  - attrs: `timestamp` (`freqtrade/user_data/strategies/GridBrainV1.py:420`), `knobs` (`freqtrade/user_data/strategies/GridBrainV1.py:421`), `lookbacks` (`freqtrade/user_data/strategies/GridBrainV1.py:422`)
  - methods: `from_strategy` (`freqtrade/user_data/strategies/GridBrainV1.py:425`), `as_dict` (`freqtrade/user_data/strategies/GridBrainV1.py:445`)
- `GridBrainLookbackSummary` (`freqtrade/user_data/strategies/GridBrainV1.py:450`) -> attrs `2`, methods `2`
  - attrs: `lookbacks` (`freqtrade/user_data/strategies/GridBrainV1.py:451`), `buffer` (`freqtrade/user_data/strategies/GridBrainV1.py:452`)
  - methods: `from_strategy` (`freqtrade/user_data/strategies/GridBrainV1.py:455`), `required_candles` (`freqtrade/user_data/strategies/GridBrainV1.py:469`)
- `GridBrainV1Core` (`freqtrade/user_data/strategies/GridBrainV1.py:475`) -> attrs `487`, methods `138`
  - attrs: `INTERFACE_VERSION` (`freqtrade/user_data/strategies/GridBrainV1.py:515`), `STOP_REASON_TREND_ADX` (`freqtrade/user_data/strategies/GridBrainV1.py:516`), `STOP_REASON_VOL_EXPANSION` (`freqtrade/user_data/strategies/GridBrainV1.py:517`), `STOP_REASON_BOX_BREAK` (`freqtrade/user_data/strategies/GridBrainV1.py:518`), `STOP_REASON_META_DRIFT_HARD` (`freqtrade/user_data/strategies/GridBrainV1.py:519`), `timeframe` (`freqtrade/user_data/strategies/GridBrainV1.py:525`), `can_short` (`freqtrade/user_data/strategies/GridBrainV1.py:526`), `minimal_roi` (`freqtrade/user_data/strategies/GridBrainV1.py:528`), `stoploss` (`freqtrade/user_data/strategies/GridBrainV1.py:529`), `trailing_stop` (`freqtrade/user_data/strategies/GridBrainV1.py:530`), `process_only_new_candles` (`freqtrade/user_data/strategies/GridBrainV1.py:532`), `lookback_buffer` (`freqtrade/user_data/strategies/GridBrainV1.py:533`), `startup_candle_count` (`freqtrade/user_data/strategies/GridBrainV1.py:536`), `data_quality_expected_candle_seconds` (`freqtrade/user_data/strategies/GridBrainV1.py:539`), `data_quality_gap_multiplier` (`freqtrade/user_data/strategies/GridBrainV1.py:540`), `data_quality_max_stale_minutes` (`freqtrade/user_data/strategies/GridBrainV1.py:541`), `data_quality_zero_volume_streak_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:542`), `materiality_epoch_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:545`), `materiality_box_mid_shift_max_step_frac` (`freqtrade/user_data/strategies/GridBrainV1.py:546`), `materiality_box_width_change_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:547`), `materiality_tp_shift_max_step_frac` (`freqtrade/user_data/strategies/GridBrainV1.py:548`), `materiality_sl_shift_max_step_frac` (`freqtrade/user_data/strategies/GridBrainV1.py:549`), `poc_acceptance_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:551`), `poc_acceptance_lookback_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:552`), `poc_alignment_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:553`), `poc_alignment_strict_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:554`), `poc_alignment_lookback_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:555`), `poc_alignment_max_step_diff` (`freqtrade/user_data/strategies/GridBrainV1.py:556`), `poc_alignment_max_width_frac` (`freqtrade/user_data/strategies/GridBrainV1.py:557`), `box_lookback_24h_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:561`), `box_lookback_48h_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:562`), `box_lookback_18h_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:563`), `box_lookback_12h_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:564`), `extremes_7d_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:565`), `box_overlap_prune_threshold` (`freqtrade/user_data/strategies/GridBrainV1.py:566`), `box_overlap_history` (`freqtrade/user_data/strategies/GridBrainV1.py:567`), `box_band_overlap_required` (`freqtrade/user_data/strategies/GridBrainV1.py:568`), `box_band_adx_allow` (`freqtrade/user_data/strategies/GridBrainV1.py:569`), `box_band_rvol_allow` (`freqtrade/user_data/strategies/GridBrainV1.py:570`), `box_envelope_ratio_max` (`freqtrade/user_data/strategies/GridBrainV1.py:571`), `box_envelope_adx_threshold` (`freqtrade/user_data/strategies/GridBrainV1.py:572`), `box_envelope_rvol_threshold` (`freqtrade/user_data/strategies/GridBrainV1.py:573`), `session_box_pad_shrink_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:574`), `breakout_lookback_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:577`), `breakout_block_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:578`), `breakout_override_allowed` (`freqtrade/user_data/strategies/GridBrainV1.py:579`), `breakout_straddle_step_buffer_frac` (`freqtrade/user_data/strategies/GridBrainV1.py:580`), `breakout_reason_code` (`freqtrade/user_data/strategies/GridBrainV1.py:581`), `min_range_len_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:582`), `breakout_confirm_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:583`), `breakout_confirm_buffer_mode` (`freqtrade/user_data/strategies/GridBrainV1.py:584`), `breakout_confirm_buffer_value` (`freqtrade/user_data/strategies/GridBrainV1.py:585`), `atr_period_15m` (`freqtrade/user_data/strategies/GridBrainV1.py:587`), `atr_pad_mult` (`freqtrade/user_data/strategies/GridBrainV1.py:588`), `rsi_period_15m` (`freqtrade/user_data/strategies/GridBrainV1.py:590`), `rsi_min` (`freqtrade/user_data/strategies/GridBrainV1.py:591`), `rsi_max` (`freqtrade/user_data/strategies/GridBrainV1.py:592`), `adx_period` (`freqtrade/user_data/strategies/GridBrainV1.py:595`), `adx_4h_max` (`freqtrade/user_data/strategies/GridBrainV1.py:596`), `ema_fast` (`freqtrade/user_data/strategies/GridBrainV1.py:599`), `ema_slow` (`freqtrade/user_data/strategies/GridBrainV1.py:600`), `ema_dist_max_frac` (`freqtrade/user_data/strategies/GridBrainV1.py:601`), `bb_window` (`freqtrade/user_data/strategies/GridBrainV1.py:603`), `bb_stds` (`freqtrade/user_data/strategies/GridBrainV1.py:604`), `bbw_pct_lookback_1h` (`freqtrade/user_data/strategies/GridBrainV1.py:605`), `bbw_1h_pct_max` (`freqtrade/user_data/strategies/GridBrainV1.py:606`), `bbw_nonexp_lookback_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:607`), `bbw_nonexp_tolerance_frac` (`freqtrade/user_data/strategies/GridBrainV1.py:608`), `context_7d_hard_veto` (`freqtrade/user_data/strategies/GridBrainV1.py:609`), `vol_sma_window` (`freqtrade/user_data/strategies/GridBrainV1.py:611`), `vol_spike_mult` (`freqtrade/user_data/strategies/GridBrainV1.py:612`), `rvol_window_15m` (`freqtrade/user_data/strategies/GridBrainV1.py:613`), `rvol_15m_max` (`freqtrade/user_data/strategies/GridBrainV1.py:614`), `vrvp_lookback_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:617`), `vrvp_bins` (`freqtrade/user_data/strategies/GridBrainV1.py:618`), `vrvp_value_area_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:619`), `vrvp_poc_outside_box_max_frac` (`freqtrade/user_data/strategies/GridBrainV1.py:620`), `vrvp_max_box_shift_frac` (`freqtrade/user_data/strategies/GridBrainV1.py:621`), `vrvp_reject_if_still_outside` (`freqtrade/user_data/strategies/GridBrainV1.py:622`), `fallback_poc_estimator_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:623`), `fallback_poc_lookback_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:624`), `bbwp_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:627`), `bbwp_lookback_s` (`freqtrade/user_data/strategies/GridBrainV1.py:628`), `bbwp_lookback_m` (`freqtrade/user_data/strategies/GridBrainV1.py:629`), `bbwp_lookback_l` (`freqtrade/user_data/strategies/GridBrainV1.py:630`), `bbwp_s_max` (`freqtrade/user_data/strategies/GridBrainV1.py:631`), `bbwp_m_max` (`freqtrade/user_data/strategies/GridBrainV1.py:632`), `bbwp_l_max` (`freqtrade/user_data/strategies/GridBrainV1.py:633`), `bbwp_veto_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:634`), `bbwp_cooloff_trigger_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:635`), `bbwp_cooloff_release_s` (`freqtrade/user_data/strategies/GridBrainV1.py:636`), `bbwp_cooloff_release_m` (`freqtrade/user_data/strategies/GridBrainV1.py:637`), `bbwp_nonexp_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:638`), `squeeze_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:639`), `squeeze_require_on_1h` (`freqtrade/user_data/strategies/GridBrainV1.py:640`), `squeeze_momentum_block_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:641`), `squeeze_tp_nudge_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:642`), `squeeze_tp_nudge_step_multiple` (`freqtrade/user_data/strategies/GridBrainV1.py:643`), `kc_atr_mult` (`freqtrade/user_data/strategies/GridBrainV1.py:644`), `band_slope_veto_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:647`), `band_slope_veto_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:648`), `band_slope_veto_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:649`), `drift_slope_veto_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:650`), `excursion_asymmetry_veto_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:651`), `excursion_asymmetry_min_ratio` (`freqtrade/user_data/strategies/GridBrainV1.py:652`), `excursion_asymmetry_max_ratio` (`freqtrade/user_data/strategies/GridBrainV1.py:653`), `hvp_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:654`), `hvp_lookback_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:655`), `hvp_sma_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:656`), `funding_filter_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:657`), `funding_filter_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:658`), `instrumentation_er_lookback` (`freqtrade/user_data/strategies/GridBrainV1.py:661`), `instrumentation_chop_lookback` (`freqtrade/user_data/strategies/GridBrainV1.py:662`), `instrumentation_di_flip_lookback` (`freqtrade/user_data/strategies/GridBrainV1.py:663`), `instrumentation_wickiness_lookback` (`freqtrade/user_data/strategies/GridBrainV1.py:664`), `instrumentation_containment_lookback` (`freqtrade/user_data/strategies/GridBrainV1.py:665`), `instrumentation_atr_pct_percentile` (`freqtrade/user_data/strategies/GridBrainV1.py:666`), `instrumentation_atr_pct_lookback` (`freqtrade/user_data/strategies/GridBrainV1.py:667`), `os_dev_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:670`), `os_dev_n_strike` (`freqtrade/user_data/strategies/GridBrainV1.py:671`), `os_dev_range_band` (`freqtrade/user_data/strategies/GridBrainV1.py:672`), `os_dev_persist_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:673`), `os_dev_rvol_max` (`freqtrade/user_data/strategies/GridBrainV1.py:674`), `os_dev_history_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:675`), `micro_vap_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:678`), `micro_vap_lookback_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:679`), `micro_vap_bins` (`freqtrade/user_data/strategies/GridBrainV1.py:680`), `micro_hvn_quantile` (`freqtrade/user_data/strategies/GridBrainV1.py:681`), `micro_lvn_quantile` (`freqtrade/user_data/strategies/GridBrainV1.py:682`), `micro_extrema_count` (`freqtrade/user_data/strategies/GridBrainV1.py:683`), `micro_lvn_corridor_steps` (`freqtrade/user_data/strategies/GridBrainV1.py:684`), `micro_void_slope_threshold` (`freqtrade/user_data/strategies/GridBrainV1.py:685`), `fvg_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:688`), `fvg_lookback_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:689`), `fvg_min_gap_atr` (`freqtrade/user_data/strategies/GridBrainV1.py:690`), `fvg_straddle_veto_steps` (`freqtrade/user_data/strategies/GridBrainV1.py:691`), `fvg_position_avg_count` (`freqtrade/user_data/strategies/GridBrainV1.py:692`), `imfvg_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:694`), `imfvg_mitigated_relax` (`freqtrade/user_data/strategies/GridBrainV1.py:695`), `defensive_fvg_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:697`), `defensive_fvg_min_gap_atr` (`freqtrade/user_data/strategies/GridBrainV1.py:698`), `defensive_fvg_body_frac` (`freqtrade/user_data/strategies/GridBrainV1.py:699`), `defensive_fvg_fresh_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:700`), `session_fvg_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:702`), `session_fvg_inside_gate` (`freqtrade/user_data/strategies/GridBrainV1.py:703`), `session_fvg_pause_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:704`), `mrvd_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:707`), `mrvd_bins` (`freqtrade/user_data/strategies/GridBrainV1.py:708`), `mrvd_value_area_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:709`), `mrvd_day_lookback_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:710`), `mrvd_week_lookback_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:711`), `mrvd_month_lookback_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:712`), `mrvd_required_overlap_count` (`freqtrade/user_data/strategies/GridBrainV1.py:713`), `mrvd_va_overlap_min_frac` (`freqtrade/user_data/strategies/GridBrainV1.py:714`), `mrvd_near_poc_steps` (`freqtrade/user_data/strategies/GridBrainV1.py:715`), `mrvd_drift_guard_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:716`), `mrvd_drift_guard_steps` (`freqtrade/user_data/strategies/GridBrainV1.py:717`), `cvd_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:720`), `cvd_lookback_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:721`), `cvd_pivot_left` (`freqtrade/user_data/strategies/GridBrainV1.py:722`), `cvd_pivot_right` (`freqtrade/user_data/strategies/GridBrainV1.py:723`), `cvd_divergence_max_age_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:724`), `cvd_near_value_steps` (`freqtrade/user_data/strategies/GridBrainV1.py:725`), `cvd_bos_lookback` (`freqtrade/user_data/strategies/GridBrainV1.py:726`), `cvd_bos_freeze_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:727`), `cvd_rung_bias_strength` (`freqtrade/user_data/strategies/GridBrainV1.py:728`), `freqai_overlay_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:731`), `freqai_overlay_gate_mode` (`freqtrade/user_data/strategies/GridBrainV1.py:732`), `freqai_overlay_strict_predict` (`freqtrade/user_data/strategies/GridBrainV1.py:733`), `freqai_overlay_confidence_min` (`freqtrade/user_data/strategies/GridBrainV1.py:734`), `freqai_overlay_breakout_scale` (`freqtrade/user_data/strategies/GridBrainV1.py:735`), `freqai_overlay_breakout_quick_tp_thresh` (`freqtrade/user_data/strategies/GridBrainV1.py:736`), `freqai_overlay_rung_edge_cut_max` (`freqtrade/user_data/strategies/GridBrainV1.py:737`), `rung_weight_hvn_boost` (`freqtrade/user_data/strategies/GridBrainV1.py:740`), `rung_weight_lvn_penalty` (`freqtrade/user_data/strategies/GridBrainV1.py:741`), `rung_weight_min` (`freqtrade/user_data/strategies/GridBrainV1.py:742`), `rung_weight_max` (`freqtrade/user_data/strategies/GridBrainV1.py:743`), `target_net_step_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:747`), `est_fee_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:748`), `est_spread_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:749`), `majors_gross_step_floor_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:750`), `n_min` (`freqtrade/user_data/strategies/GridBrainV1.py:751`), `n_max` (`freqtrade/user_data/strategies/GridBrainV1.py:752`), `n_volatility_adapter_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:753`), `n_volatility_adapter_strength` (`freqtrade/user_data/strategies/GridBrainV1.py:754`), `volatility_min_step_buffer_bps` (`freqtrade/user_data/strategies/GridBrainV1.py:755`), `empirical_cost_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:758`), `empirical_cost_window` (`freqtrade/user_data/strategies/GridBrainV1.py:759`), `empirical_cost_min_samples` (`freqtrade/user_data/strategies/GridBrainV1.py:760`), `empirical_cost_stale_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:761`), `empirical_cost_percentile` (`freqtrade/user_data/strategies/GridBrainV1.py:762`), `empirical_cost_conservative_mode` (`freqtrade/user_data/strategies/GridBrainV1.py:763`), `empirical_cost_require_live_samples` (`freqtrade/user_data/strategies/GridBrainV1.py:764`), `empirical_cost_min_live_samples` (`freqtrade/user_data/strategies/GridBrainV1.py:765`), `empirical_spread_proxy_scale` (`freqtrade/user_data/strategies/GridBrainV1.py:766`), `empirical_adverse_selection_scale` (`freqtrade/user_data/strategies/GridBrainV1.py:767`), `empirical_retry_penalty_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:768`), `empirical_missed_fill_penalty_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:769`), `empirical_cost_floor_min_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:770`), `execution_cost_artifact_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:771`), `execution_cost_artifact_dir` (`freqtrade/user_data/strategies/GridBrainV1.py:772`), `execution_cost_artifact_filename` (`freqtrade/user_data/strategies/GridBrainV1.py:773`), `execution_cost_artifact_max_age_minutes` (`freqtrade/user_data/strategies/GridBrainV1.py:774`), `min_width_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:777`), `max_width_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:778`), `box_width_avg_veto_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:779`), `box_width_avg_veto_lookback` (`freqtrade/user_data/strategies/GridBrainV1.py:780`), `box_width_avg_veto_min_samples` (`freqtrade/user_data/strategies/GridBrainV1.py:781`), `box_width_avg_veto_max_ratio` (`freqtrade/user_data/strategies/GridBrainV1.py:782`), `stop_confirm_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:785`), `fast_stop_step_multiple` (`freqtrade/user_data/strategies/GridBrainV1.py:786`), `range_shift_stop_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:787`), `tp_step_multiple` (`freqtrade/user_data/strategies/GridBrainV1.py:788`), `sl_step_multiple` (`freqtrade/user_data/strategies/GridBrainV1.py:789`), `reclaim_hours` (`freqtrade/user_data/strategies/GridBrainV1.py:790`), `cooldown_minutes` (`freqtrade/user_data/strategies/GridBrainV1.py:791`), `min_runtime_hours` (`freqtrade/user_data/strategies/GridBrainV1.py:792`), `neutral_stop_adx_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:793`), `neutral_box_break_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:794`), `neutral_box_break_step_multiple` (`freqtrade/user_data/strategies/GridBrainV1.py:795`), `drawdown_guard_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:796`), `drawdown_guard_lookback_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:797`), `drawdown_guard_max_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:798`), `max_stops_window_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:799`), `max_stops_window_minutes` (`freqtrade/user_data/strategies/GridBrainV1.py:800`), `max_stops_window_count` (`freqtrade/user_data/strategies/GridBrainV1.py:801`), `gate_profile` (`freqtrade/user_data/strategies/GridBrainV1.py:804`), `start_min_gate_pass_ratio` (`freqtrade/user_data/strategies/GridBrainV1.py:805`), `start_stability_min_score` (`freqtrade/user_data/strategies/GridBrainV1.py:806`), `start_stability_k_fraction` (`freqtrade/user_data/strategies/GridBrainV1.py:807`), `start_box_position_guard_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:808`), `start_box_position_min_frac` (`freqtrade/user_data/strategies/GridBrainV1.py:809`), `start_box_position_max_frac` (`freqtrade/user_data/strategies/GridBrainV1.py:810`), `basis_cross_confirm_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:811`), `capacity_hint_path` (`freqtrade/user_data/strategies/GridBrainV1.py:812`), `capacity_hint_hard_block` (`freqtrade/user_data/strategies/GridBrainV1.py:813`), `planner_health_quarantine_on_gap` (`freqtrade/user_data/strategies/GridBrainV1.py:816`), `planner_health_quarantine_on_misalign` (`freqtrade/user_data/strategies/GridBrainV1.py:817`), `meta_drift_soft_block_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:818`), `meta_drift_soft_block_steps` (`freqtrade/user_data/strategies/GridBrainV1.py:819`), `meta_drift_guard_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:820`), `meta_drift_guard_window` (`freqtrade/user_data/strategies/GridBrainV1.py:821`), `meta_drift_guard_min_samples` (`freqtrade/user_data/strategies/GridBrainV1.py:822`), `meta_drift_guard_smoothing_alpha` (`freqtrade/user_data/strategies/GridBrainV1.py:823`), `meta_drift_guard_eps` (`freqtrade/user_data/strategies/GridBrainV1.py:824`), `meta_drift_guard_z_soft` (`freqtrade/user_data/strategies/GridBrainV1.py:825`), `meta_drift_guard_z_hard` (`freqtrade/user_data/strategies/GridBrainV1.py:826`), `meta_drift_guard_cusum_k_sigma` (`freqtrade/user_data/strategies/GridBrainV1.py:827`), `meta_drift_guard_cusum_soft` (`freqtrade/user_data/strategies/GridBrainV1.py:828`), `meta_drift_guard_cusum_hard` (`freqtrade/user_data/strategies/GridBrainV1.py:829`), `meta_drift_guard_ph_delta_sigma` (`freqtrade/user_data/strategies/GridBrainV1.py:830`), `meta_drift_guard_ph_soft` (`freqtrade/user_data/strategies/GridBrainV1.py:831`), `meta_drift_guard_ph_hard` (`freqtrade/user_data/strategies/GridBrainV1.py:832`), `meta_drift_guard_soft_min_channels` (`freqtrade/user_data/strategies/GridBrainV1.py:833`), `meta_drift_guard_hard_min_channels` (`freqtrade/user_data/strategies/GridBrainV1.py:834`), `meta_drift_guard_cooldown_extend_minutes` (`freqtrade/user_data/strategies/GridBrainV1.py:835`), `meta_drift_guard_spread_proxy_scale` (`freqtrade/user_data/strategies/GridBrainV1.py:836`), `breakout_idle_reclaim_on_fresh` (`freqtrade/user_data/strategies/GridBrainV1.py:837`), `hvp_quiet_exit_bias_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:838`), `hvp_quiet_exit_step_multiple` (`freqtrade/user_data/strategies/GridBrainV1.py:839`), `regime_router_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:842`), `regime_router_default_mode` (`freqtrade/user_data/strategies/GridBrainV1.py:843`), `regime_router_force_mode` (`freqtrade/user_data/strategies/GridBrainV1.py:844`), `regime_router_switch_persist_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:845`), `regime_router_switch_cooldown_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:846`), `regime_router_switch_margin` (`freqtrade/user_data/strategies/GridBrainV1.py:847`), `regime_router_allow_pause` (`freqtrade/user_data/strategies/GridBrainV1.py:848`), `regime_router_score_enter` (`freqtrade/user_data/strategies/GridBrainV1.py:849`), `regime_router_score_exit` (`freqtrade/user_data/strategies/GridBrainV1.py:850`), `regime_router_score_persistence_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:851`), `regime_router_score_artifact_run_id` (`freqtrade/user_data/strategies/GridBrainV1.py:852`), `regime_router_score_artifact_dir` (`freqtrade/user_data/strategies/GridBrainV1.py:853`), `regime_router_score_artifact_file` (`freqtrade/user_data/strategies/GridBrainV1.py:854`), `neutral_adx_enter_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:855`), `neutral_adx_exit_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:856`), `neutral_adx_veto_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:857`), `neutral_bbwp_enter_min_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:858`), `neutral_bbwp_enter_max_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:859`), `neutral_bbwp_veto_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:860`), `neutral_bbwp_dead_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:861`), `neutral_atr_pct_min` (`freqtrade/user_data/strategies/GridBrainV1.py:862`), `neutral_spread_bps_max` (`freqtrade/user_data/strategies/GridBrainV1.py:863`), `neutral_spread_step_frac` (`freqtrade/user_data/strategies/GridBrainV1.py:864`), `neutral_enter_persist_min` (`freqtrade/user_data/strategies/GridBrainV1.py:867`), `neutral_enter_persist_max` (`freqtrade/user_data/strategies/GridBrainV1.py:868`), `neutral_exit_persist_ratio` (`freqtrade/user_data/strategies/GridBrainV1.py:869`), `neutral_cooldown_multiplier` (`freqtrade/user_data/strategies/GridBrainV1.py:870`), `neutral_min_runtime_hours_offset` (`freqtrade/user_data/strategies/GridBrainV1.py:871`), `neutral_persistence_default_enter` (`freqtrade/user_data/strategies/GridBrainV1.py:872`), `neutral_grid_levels_ratio` (`freqtrade/user_data/strategies/GridBrainV1.py:873`), `neutral_grid_budget_ratio` (`freqtrade/user_data/strategies/GridBrainV1.py:874`), `neutral_rebuild_shift_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:875`), `neutral_rebuild_max_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:876`), `regime_threshold_profile` (`freqtrade/user_data/strategies/GridBrainV1.py:894`), `intraday_adx_enter_max` (`freqtrade/user_data/strategies/GridBrainV1.py:897`), `intraday_adx_exit_min` (`freqtrade/user_data/strategies/GridBrainV1.py:898`), `intraday_adx_rising_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:899`), `intraday_bbw_1h_pct_max` (`freqtrade/user_data/strategies/GridBrainV1.py:900`), `intraday_bbw_nonexp_lookback_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:901`), `intraday_bbw_nonexp_tolerance_frac` (`freqtrade/user_data/strategies/GridBrainV1.py:902`), `intraday_ema_dist_max_frac` (`freqtrade/user_data/strategies/GridBrainV1.py:903`), `intraday_vol_spike_mult` (`freqtrade/user_data/strategies/GridBrainV1.py:904`), `intraday_rvol_15m_max` (`freqtrade/user_data/strategies/GridBrainV1.py:905`), `intraday_bbwp_s_enter_low` (`freqtrade/user_data/strategies/GridBrainV1.py:906`), `intraday_bbwp_s_enter_high` (`freqtrade/user_data/strategies/GridBrainV1.py:907`), `intraday_bbwp_m_enter_low` (`freqtrade/user_data/strategies/GridBrainV1.py:908`), `intraday_bbwp_m_enter_high` (`freqtrade/user_data/strategies/GridBrainV1.py:909`), `intraday_bbwp_l_enter_low` (`freqtrade/user_data/strategies/GridBrainV1.py:910`), `intraday_bbwp_l_enter_high` (`freqtrade/user_data/strategies/GridBrainV1.py:911`), `intraday_bbwp_stop_high` (`freqtrade/user_data/strategies/GridBrainV1.py:912`), `intraday_atr_pct_max` (`freqtrade/user_data/strategies/GridBrainV1.py:913`), `intraday_os_dev_persist_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:914`), `intraday_os_dev_rvol_max` (`freqtrade/user_data/strategies/GridBrainV1.py:915`), `swing_adx_enter_max` (`freqtrade/user_data/strategies/GridBrainV1.py:918`), `swing_adx_exit_min` (`freqtrade/user_data/strategies/GridBrainV1.py:919`), `swing_adx_rising_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:920`), `swing_bbw_1h_pct_max` (`freqtrade/user_data/strategies/GridBrainV1.py:921`), `swing_bbw_nonexp_lookback_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:922`), `swing_bbw_nonexp_tolerance_frac` (`freqtrade/user_data/strategies/GridBrainV1.py:923`), `swing_ema_dist_max_frac` (`freqtrade/user_data/strategies/GridBrainV1.py:924`), `swing_vol_spike_mult` (`freqtrade/user_data/strategies/GridBrainV1.py:925`), `swing_rvol_15m_max` (`freqtrade/user_data/strategies/GridBrainV1.py:926`), `swing_bbwp_s_enter_low` (`freqtrade/user_data/strategies/GridBrainV1.py:927`), `swing_bbwp_s_enter_high` (`freqtrade/user_data/strategies/GridBrainV1.py:928`), `swing_bbwp_m_enter_low` (`freqtrade/user_data/strategies/GridBrainV1.py:929`), `swing_bbwp_m_enter_high` (`freqtrade/user_data/strategies/GridBrainV1.py:930`), `swing_bbwp_l_enter_low` (`freqtrade/user_data/strategies/GridBrainV1.py:931`), `swing_bbwp_l_enter_high` (`freqtrade/user_data/strategies/GridBrainV1.py:932`), `swing_bbwp_stop_high` (`freqtrade/user_data/strategies/GridBrainV1.py:933`), `swing_atr_pct_max` (`freqtrade/user_data/strategies/GridBrainV1.py:934`), `swing_os_dev_persist_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:935`), `swing_os_dev_rvol_max` (`freqtrade/user_data/strategies/GridBrainV1.py:936`), `emit_per_candle_history_backtest` (`freqtrade/user_data/strategies/GridBrainV1.py:939`), `soft_adjust_max_step_frac` (`freqtrade/user_data/strategies/GridBrainV1.py:942`), `inventory_mode` (`freqtrade/user_data/strategies/GridBrainV1.py:945`), `inventory_target_base_min_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:946`), `inventory_target_base_max_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:947`), `topup_policy` (`freqtrade/user_data/strategies/GridBrainV1.py:948`), `max_concurrent_rebuilds` (`freqtrade/user_data/strategies/GridBrainV1.py:949`), `preferred_rung_cap` (`freqtrade/user_data/strategies/GridBrainV1.py:950`), `grid_budget_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:951`), `reserve_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:952`), `donchian_lookback_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:955`), `basis_band_window` (`freqtrade/user_data/strategies/GridBrainV1.py:956`), `basis_band_stds` (`freqtrade/user_data/strategies/GridBrainV1.py:957`), `fvg_vp_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:958`), `fvg_vp_bins` (`freqtrade/user_data/strategies/GridBrainV1.py:959`), `fvg_vp_lookback_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:960`), `fvg_vp_poc_tag_step_frac` (`freqtrade/user_data/strategies/GridBrainV1.py:961`), `sl_lvn_avoid_steps` (`freqtrade/user_data/strategies/GridBrainV1.py:962`), `sl_fvg_buffer_steps` (`freqtrade/user_data/strategies/GridBrainV1.py:963`), `box_quality_log_space` (`freqtrade/user_data/strategies/GridBrainV1.py:964`), `box_quality_extension_factor` (`freqtrade/user_data/strategies/GridBrainV1.py:965`), `midline_bias_fallback_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:966`), `midline_bias_tp_candidate_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:967`), `midline_bias_poc_neutral_step_frac` (`freqtrade/user_data/strategies/GridBrainV1.py:968`), `midline_bias_poc_neutral_width_frac` (`freqtrade/user_data/strategies/GridBrainV1.py:969`), `midline_bias_source_buffer_steps` (`freqtrade/user_data/strategies/GridBrainV1.py:970`), `midline_bias_source_buffer_width_frac` (`freqtrade/user_data/strategies/GridBrainV1.py:971`), `midline_bias_deadband_steps` (`freqtrade/user_data/strategies/GridBrainV1.py:972`), `midline_bias_deadband_width_frac` (`freqtrade/user_data/strategies/GridBrainV1.py:973`), `fill_confirmation_mode` (`freqtrade/user_data/strategies/GridBrainV1.py:976`), `fill_no_repeat_lsi_guard` (`freqtrade/user_data/strategies/GridBrainV1.py:977`), `fill_no_repeat_cooldown_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:978`), `tick_size_step_frac` (`freqtrade/user_data/strategies/GridBrainV1.py:979`), `tick_size_floor` (`freqtrade/user_data/strategies/GridBrainV1.py:980`), `micro_reentry_pause_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:983`), `micro_reentry_require_poc_reclaim` (`freqtrade/user_data/strategies/GridBrainV1.py:984`), `micro_reentry_poc_buffer_steps` (`freqtrade/user_data/strategies/GridBrainV1.py:985`), `buy_ratio_bias_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:986`), `buy_ratio_midband_half_width` (`freqtrade/user_data/strategies/GridBrainV1.py:987`), `buy_ratio_bullish_threshold` (`freqtrade/user_data/strategies/GridBrainV1.py:988`), `buy_ratio_bearish_threshold` (`freqtrade/user_data/strategies/GridBrainV1.py:989`), `buy_ratio_rung_bias_strength` (`freqtrade/user_data/strategies/GridBrainV1.py:990`), `buy_ratio_bearish_tp_step_multiple` (`freqtrade/user_data/strategies/GridBrainV1.py:991`), `smart_channel_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:992`), `smart_channel_breakout_step_buffer` (`freqtrade/user_data/strategies/GridBrainV1.py:993`), `smart_channel_volume_confirm_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:994`), `smart_channel_volume_rvol_min` (`freqtrade/user_data/strategies/GridBrainV1.py:995`), `smart_channel_tp_nudge_step_multiple` (`freqtrade/user_data/strategies/GridBrainV1.py:996`), `ob_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:997`), `ob_tf` (`freqtrade/user_data/strategies/GridBrainV1.py:998`), `ob_use_wick_zone` (`freqtrade/user_data/strategies/GridBrainV1.py:999`), `ob_impulse_lookahead` (`freqtrade/user_data/strategies/GridBrainV1.py:1000`), `ob_impulse_atr_len` (`freqtrade/user_data/strategies/GridBrainV1.py:1001`), `ob_impulse_atr_mult` (`freqtrade/user_data/strategies/GridBrainV1.py:1002`), `ob_fresh_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:1003`), `ob_max_age_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:1004`), `ob_mitigation_mode` (`freqtrade/user_data/strategies/GridBrainV1.py:1005`), `ob_straddle_min_step_mult` (`freqtrade/user_data/strategies/GridBrainV1.py:1006`), `ob_tp_nudge_max_steps` (`freqtrade/user_data/strategies/GridBrainV1.py:1007`), `zigzag_contraction_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:1008`), `zigzag_contraction_lookback_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:1009`), `zigzag_contraction_ratio_max` (`freqtrade/user_data/strategies/GridBrainV1.py:1010`), `session_sweep_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:1011`), `session_sweep_retest_lookback_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:1012`), `sweeps_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:1013`), `sweep_pivot_len` (`freqtrade/user_data/strategies/GridBrainV1.py:1014`), `sweep_max_age_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:1015`), `sweep_break_buffer_mode` (`freqtrade/user_data/strategies/GridBrainV1.py:1016`), `sweep_break_buffer_value` (`freqtrade/user_data/strategies/GridBrainV1.py:1017`), `sweep_retest_window_bars` (`freqtrade/user_data/strategies/GridBrainV1.py:1018`), `sweep_retest_buffer_mode` (`freqtrade/user_data/strategies/GridBrainV1.py:1019`), `sweep_retest_buffer_value` (`freqtrade/user_data/strategies/GridBrainV1.py:1020`), `sweep_stop_if_through_box_edge` (`freqtrade/user_data/strategies/GridBrainV1.py:1021`), `sweep_retest_validation_mode` (`freqtrade/user_data/strategies/GridBrainV1.py:1022`), `sweep_min_level_separation_steps` (`freqtrade/user_data/strategies/GridBrainV1.py:1023`), `order_flow_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:1024`), `order_flow_spread_soft_max_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:1025`), `order_flow_depth_thin_soft_max` (`freqtrade/user_data/strategies/GridBrainV1.py:1026`), `order_flow_imbalance_extreme` (`freqtrade/user_data/strategies/GridBrainV1.py:1027`), `order_flow_jump_soft_max_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:1028`), `order_flow_soft_veto_min_flags` (`freqtrade/user_data/strategies/GridBrainV1.py:1029`), `order_flow_hard_block` (`freqtrade/user_data/strategies/GridBrainV1.py:1030`), `order_flow_confidence_penalty_per_flag` (`freqtrade/user_data/strategies/GridBrainV1.py:1031`), `plans_root_rel` (`freqtrade/user_data/strategies/GridBrainV1.py:1033`), `plan_schema_version` (`freqtrade/user_data/strategies/GridBrainV1.py:1034`), `planner_version` (`freqtrade/user_data/strategies/GridBrainV1.py:1035`), `plan_expiry_seconds` (`freqtrade/user_data/strategies/GridBrainV1.py:1036`), `decision_log_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:1037`), `event_log_enabled` (`freqtrade/user_data/strategies/GridBrainV1.py:1038`), `decision_log_filename` (`freqtrade/user_data/strategies/GridBrainV1.py:1039`), `event_log_filename` (`freqtrade/user_data/strategies/GridBrainV1.py:1040`), `decision_event_log_max_changed_fields` (`freqtrade/user_data/strategies/GridBrainV1.py:1041`), `_last_written_ts_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1044`), `_last_plan_hash_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1045`), `_last_plan_base_hash_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1046`), `_last_material_plan_payload_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1047`), `_last_plan_id_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1048`), `_last_decision_seq_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1049`), `_event_counter_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1050`), `_last_mid_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1051`), `_last_box_step_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1052`), `_reclaim_until_ts_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1053`), `_cooldown_until_ts_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1054`), `_micro_reentry_pause_until_ts_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1055`), `_stop_timestamps_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1056`), `_active_since_ts_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1057`), `_running_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1058`), `_bbwp_cooloff_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1059`), `_os_dev_state_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1060`), `_os_dev_candidate_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1061`), `_os_dev_candidate_count_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1062`), `_os_dev_zero_persist_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1063`), `_mrvd_day_poc_prev_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1064`), `_cvd_freeze_bars_left_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1065`), `_last_adx_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1066`), `_adx_rising_count_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1067`), `_mode_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1068`), `_mode_candidate_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1069`), `_mode_candidate_count_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1070`), `_mode_cooldown_until_ts_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1071`), `_running_mode_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1072`), `_mode_at_entry_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1073`), `_mode_at_exit_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1074`), `_history_emit_in_progress_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1075`), `_history_emit_end_ts_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1076`), `_box_state_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1077`), `_box_rebuild_bars_since_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1078`), `_neutral_box_break_bars_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1079`), `_breakout_levels_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1080`), `_breakout_bars_since_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1081`), `_box_signature_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1082`), `_data_quality_issues_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1083`), `_materiality_epoch_bar_count_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1084`), `_box_history_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1085`), `_box_width_history_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1086`), `_last_width_pct_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1087`), `_last_tp_price_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1088`), `_last_sl_price_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1089`), `_ob_state_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1090`), `_poc_acceptance_crossed_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1091`), `_poc_alignment_crossed_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1092`), `_plan_guard_decision_count_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1093`), `_mid_history_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1094`), `_hvp_cooloff_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1095`), `_box_quality_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1096`), `_mid_history_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1097`), `_hvp_cooloff_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1098`), `_meta_drift_prev_box_pos_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1099`), `_external_mode_thresholds_path_cache` (`freqtrade/user_data/strategies/GridBrainV1.py:1100`), `_external_mode_thresholds_mtime_cache` (`freqtrade/user_data/strategies/GridBrainV1.py:1101`), `_external_mode_thresholds_cache` (`freqtrade/user_data/strategies/GridBrainV1.py:1102`), `_neutral_persistence_state_by_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:1103`), `MODE_TRADING` (`freqtrade/user_data/strategies/GridBrainV1.py:2047`), `MODE_TRADING_WITH_PAUSE` (`freqtrade/user_data/strategies/GridBrainV1.py:2048`), `MODE_VALUES` (`freqtrade/user_data/strategies/GridBrainV1.py:2050`)
  - methods: `__init__` (`freqtrade/user_data/strategies/GridBrainV1.py:491`), `_determine_regime_bands_run_id` (`freqtrade/user_data/strategies/GridBrainV1.py:878`), `informative_pairs` (`freqtrade/user_data/strategies/GridBrainV1.py:1106`), `populate_indicators_4h` (`freqtrade/user_data/strategies/GridBrainV1.py:1117`), `populate_indicators_1h` (`freqtrade/user_data/strategies/GridBrainV1.py:1132`), `_safe_float` (`freqtrade/user_data/strategies/GridBrainV1.py:1164`), `_record_mid_history` (`freqtrade/user_data/strategies/GridBrainV1.py:1179`), `_compute_band_slope_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:1189`), `_excursion_asymmetry_ratio` (`freqtrade/user_data/strategies/GridBrainV1.py:1199`), `_funding_gate_ok` (`freqtrade/user_data/strategies/GridBrainV1.py:1209`), `_hvp_stats` (`freqtrade/user_data/strategies/GridBrainV1.py:1216`), `_box_signature` (`freqtrade/user_data/strategies/GridBrainV1.py:1233`), `_poc_cross_detected` (`freqtrade/user_data/strategies/GridBrainV1.py:1239`), `_derive_box_block_reasons` (`freqtrade/user_data/strategies/GridBrainV1.py:1256`), `_box_straddles_cached_breakout` (`freqtrade/user_data/strategies/GridBrainV1.py:1271`), `_box_straddles_level` (`freqtrade/user_data/strategies/GridBrainV1.py:1296`), `_box_level_straddle_reasons` (`freqtrade/user_data/strategies/GridBrainV1.py:1309`), `_squeeze_release_block_reason` (`freqtrade/user_data/strategies/GridBrainV1.py:1326`), `_append_reason` (`freqtrade/user_data/strategies/GridBrainV1.py:1329`), `_run_data_quality_checks` (`freqtrade/user_data/strategies/GridBrainV1.py:1333`), `_percentile` (`freqtrade/user_data/strategies/GridBrainV1.py:1346`), `_poc_acceptance_status` (`freqtrade/user_data/strategies/GridBrainV1.py:1357`), `_fallback_poc_estimate` (`freqtrade/user_data/strategies/GridBrainV1.py:1381`), `_box_width_history` (`freqtrade/user_data/strategies/GridBrainV1.py:1406`), `_box_width_avg_veto_state` (`freqtrade/user_data/strategies/GridBrainV1.py:1418`), `_record_accepted_box_width` (`freqtrade/user_data/strategies/GridBrainV1.py:1447`), `_poc_alignment_state` (`freqtrade/user_data/strategies/GridBrainV1.py:1451`), `_efficiency_ratio` (`freqtrade/user_data/strategies/GridBrainV1.py:1526`), `_detect_structural_breakout` (`freqtrade/user_data/strategies/GridBrainV1.py:1539`), `_breakout_confirm_buffer` (`freqtrade/user_data/strategies/GridBrainV1.py:1560`), `_breakout_confirm_state` (`freqtrade/user_data/strategies/GridBrainV1.py:1581`), `_range_len_gate_state` (`freqtrade/user_data/strategies/GridBrainV1.py:1622`), `_breakout_confirm_reason_state` (`freqtrade/user_data/strategies/GridBrainV1.py:1647`), `_bbw_nonexpanding` (`freqtrade/user_data/strategies/GridBrainV1.py:1679`), `_update_breakout_fresh_state` (`freqtrade/user_data/strategies/GridBrainV1.py:1696`), `_phase2_gate_failures_from_flags` (`freqtrade/user_data/strategies/GridBrainV1.py:1729`), `_planner_health_state` (`freqtrade/user_data/strategies/GridBrainV1.py:1750`), `_start_stability_state` (`freqtrade/user_data/strategies/GridBrainV1.py:1767`), `_atomic_write_json` (`freqtrade/user_data/strategies/GridBrainV1.py:1774`), `_evaluate_materiality` (`freqtrade/user_data/strategies/GridBrainV1.py:1777`), `_validate_feature_contract` (`freqtrade/user_data/strategies/GridBrainV1.py:1816`), `_log_feature_contract_violation` (`freqtrade/user_data/strategies/GridBrainV1.py:1839`), `_choppiness_index` (`freqtrade/user_data/strategies/GridBrainV1.py:1854`), `_di_flip_rate` (`freqtrade/user_data/strategies/GridBrainV1.py:1878`), `_wickiness` (`freqtrade/user_data/strategies/GridBrainV1.py:1903`), `_containment_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:1929`), `_adx_exit_hysteresis_trigger` (`freqtrade/user_data/strategies/GridBrainV1.py:1960`), `_adx_di_down_risk_trigger` (`freqtrade/user_data/strategies/GridBrainV1.py:1973`), `_gate_profile_values` (`freqtrade/user_data/strategies/GridBrainV1.py:1993`), `_normalize_mode_name` (`freqtrade/user_data/strategies/GridBrainV1.py:2053`), `_neutral_adx_pct` (`freqtrade/user_data/strategies/GridBrainV1.py:2063`), `_neutral_spread_bps` (`freqtrade/user_data/strategies/GridBrainV1.py:2072`), `_neutral_step_bps` (`freqtrade/user_data/strategies/GridBrainV1.py:2080`), `_neutral_spread_threshold` (`freqtrade/user_data/strategies/GridBrainV1.py:2086`), `_active_threshold_profile` (`freqtrade/user_data/strategies/GridBrainV1.py:2091`), `_external_mode_threshold_overrides` (`freqtrade/user_data/strategies/GridBrainV1.py:2097`), `_mode_threshold_overrides` (`freqtrade/user_data/strategies/GridBrainV1.py:2176`), `_mode_threshold_block` (`freqtrade/user_data/strategies/GridBrainV1.py:2242`), `_mode_router_score` (`freqtrade/user_data/strategies/GridBrainV1.py:2314`), `_regime_router_state` (`freqtrade/user_data/strategies/GridBrainV1.py:2373`), `_runmode_name` (`freqtrade/user_data/strategies/GridBrainV1.py:2649`), `_should_emit_per_candle_history` (`freqtrade/user_data/strategies/GridBrainV1.py:2668`), `_reset_pair_runtime_state` (`freqtrade/user_data/strategies/GridBrainV1.py:2674`), `_ts_to_iso` (`freqtrade/user_data/strategies/GridBrainV1.py:2721`), `_plan_dir` (`freqtrade/user_data/strategies/GridBrainV1.py:2729`), `_seed_plan_signature_state` (`freqtrade/user_data/strategies/GridBrainV1.py:2742`), `_next_plan_identity` (`freqtrade/user_data/strategies/GridBrainV1.py:2782`), `_write_plan` (`freqtrade/user_data/strategies/GridBrainV1.py:2789`), `_decision_log_path` (`freqtrade/user_data/strategies/GridBrainV1.py:2865`), `_event_log_path` (`freqtrade/user_data/strategies/GridBrainV1.py:2870`), `_append_jsonl` (`freqtrade/user_data/strategies/GridBrainV1.py:2876`), `_severity_for_code` (`freqtrade/user_data/strategies/GridBrainV1.py:2883`), `_source_module_for_code` (`freqtrade/user_data/strategies/GridBrainV1.py:2915`), `_next_event_id` (`freqtrade/user_data/strategies/GridBrainV1.py:2989`), `_emit_decision_and_event_logs` (`freqtrade/user_data/strategies/GridBrainV1.py:2994`), `_range_candidate` (`freqtrade/user_data/strategies/GridBrainV1.py:3099`), `_build_box_15m` (`freqtrade/user_data/strategies/GridBrainV1.py:3104`), `_latest_daily_vwap` (`freqtrade/user_data/strategies/GridBrainV1.py:3153`), `_is_level_near_box` (`freqtrade/user_data/strategies/GridBrainV1.py:3175`), `_box_quality_levels` (`freqtrade/user_data/strategies/GridBrainV1.py:3201`), `_midline_bias_fallback_state` (`freqtrade/user_data/strategies/GridBrainV1.py:3257`), `_update_box_quality` (`freqtrade/user_data/strategies/GridBrainV1.py:3350`), `_box_overlap_fraction` (`freqtrade/user_data/strategies/GridBrainV1.py:3380`), `_box_overlap_prune` (`freqtrade/user_data/strategies/GridBrainV1.py:3395`), `_record_box_history` (`freqtrade/user_data/strategies/GridBrainV1.py:3405`), `_bbw_percentile_ok` (`freqtrade/user_data/strategies/GridBrainV1.py:3413`), `_bbwp_percentile_last` (`freqtrade/user_data/strategies/GridBrainV1.py:3419`), `_user_data_dir` (`freqtrade/user_data/strategies/GridBrainV1.py:3430`), `_regime_bands_artifact_path` (`freqtrade/user_data/strategies/GridBrainV1.py:3435`), `_pair_fs` (`freqtrade/user_data/strategies/GridBrainV1.py:3443`), `_execution_cost_artifact_path` (`freqtrade/user_data/strategies/GridBrainV1.py:3446`), `_load_execution_cost_artifact` (`freqtrade/user_data/strategies/GridBrainV1.py:3451`), `_load_regime_bands_entries` (`freqtrade/user_data/strategies/GridBrainV1.py:3525`), `_neutral_band_entry` (`freqtrade/user_data/strategies/GridBrainV1.py:3547`), `_normalize_from_band` (`freqtrade/user_data/strategies/GridBrainV1.py:3552`), `_neutral_persistence_for_pair` (`freqtrade/user_data/strategies/GridBrainV1.py:3575`), `_compute_chop_score` (`freqtrade/user_data/strategies/GridBrainV1.py:3591`), `_vrvp_profile` (`freqtrade/user_data/strategies/GridBrainV1.py:3630`), `_interval_overlap_frac` (`freqtrade/user_data/strategies/GridBrainV1.py:3690`), `_mrvd_profile` (`freqtrade/user_data/strategies/GridBrainV1.py:3702`), `_pivot_indices` (`freqtrade/user_data/strategies/GridBrainV1.py:3803`), `_cvd_state` (`freqtrade/user_data/strategies/GridBrainV1.py:3831`), `_apply_cvd_rung_bias` (`freqtrade/user_data/strategies/GridBrainV1.py:3957`), `_find_numeric_row` (`freqtrade/user_data/strategies/GridBrainV1.py:3993`), `_freqai_overlay_state` (`freqtrade/user_data/strategies/GridBrainV1.py:4020`), `_apply_ml_rung_safety` (`freqtrade/user_data/strategies/GridBrainV1.py:4136`), `_os_dev_from_history` (`freqtrade/user_data/strategies/GridBrainV1.py:4170`), `_micro_vap_inside_box` (`freqtrade/user_data/strategies/GridBrainV1.py:4219`), `_rung_weights_from_micro_vap` (`freqtrade/user_data/strategies/GridBrainV1.py:4315`), `_fvg_stack_state` (`freqtrade/user_data/strategies/GridBrainV1.py:4358`), `_capacity_hint_state` (`freqtrade/user_data/strategies/GridBrainV1.py:4678`), `_empirical_cost_sample` (`freqtrade/user_data/strategies/GridBrainV1.py:4685`), `_meta_drift_channels` (`freqtrade/user_data/strategies/GridBrainV1.py:4756`), `_meta_drift_state` (`freqtrade/user_data/strategies/GridBrainV1.py:4791`), `_effective_cost_floor` (`freqtrade/user_data/strategies/GridBrainV1.py:4881`), `_n_level_bounds` (`freqtrade/user_data/strategies/GridBrainV1.py:5067`), `_grid_sizing` (`freqtrade/user_data/strategies/GridBrainV1.py:5083`), `_nearest_above` (`freqtrade/user_data/strategies/GridBrainV1.py:5144`), `_select_tp_price` (`freqtrade/user_data/strategies/GridBrainV1.py:5158`), `_select_sl_price` (`freqtrade/user_data/strategies/GridBrainV1.py:5175`), `_infer_tick_size` (`freqtrade/user_data/strategies/GridBrainV1.py:5202`), `_breakout_flags` (`freqtrade/user_data/strategies/GridBrainV1.py:5208`), `_micro_buy_ratio_state` (`freqtrade/user_data/strategies/GridBrainV1.py:5221`), `_apply_buy_ratio_rung_bias` (`freqtrade/user_data/strategies/GridBrainV1.py:5281`), `_fvg_vp_state` (`freqtrade/user_data/strategies/GridBrainV1.py:5311`), `_smart_channel_state` (`freqtrade/user_data/strategies/GridBrainV1.py:5394`), `_zigzag_contraction_state` (`freqtrade/user_data/strategies/GridBrainV1.py:5458`), `_informative_ohlc_frame` (`freqtrade/user_data/strategies/GridBrainV1.py:5497`), `_order_block_state` (`freqtrade/user_data/strategies/GridBrainV1.py:5526`), `_session_sweep_state` (`freqtrade/user_data/strategies/GridBrainV1.py:5704`), `_order_flow_state` (`freqtrade/user_data/strategies/GridBrainV1.py:5779`), `_drawdown_guard_state` (`freqtrade/user_data/strategies/GridBrainV1.py:5838`), `_max_stops_window_state` (`freqtrade/user_data/strategies/GridBrainV1.py:5869`), `_register_stop_timestamp` (`freqtrade/user_data/strategies/GridBrainV1.py:5893`), `_micro_reentry_state` (`freqtrade/user_data/strategies/GridBrainV1.py:5900`), `populate_indicators` (`freqtrade/user_data/strategies/GridBrainV1.py:5931`), `populate_entry_trend` (`freqtrade/user_data/strategies/GridBrainV1.py:9599`), `populate_exit_trend` (`freqtrade/user_data/strategies/GridBrainV1.py:9603`)
- `GridBrainV1` (`freqtrade/user_data/strategies/GridBrainV1.py:9608`) -> attrs `0`, methods `0`

### `freqtrade/user_data/strategies/GridBrainV1BaselineNoNeutral.py`

- Top-level functions: `0`
- Classes: `1`
- `GridBrainV1BaselineNoNeutral` (`freqtrade/user_data/strategies/GridBrainV1BaselineNoNeutral.py:4`) -> attrs `2`, methods `0`
  - attrs: `regime_router_enabled` (`freqtrade/user_data/strategies/GridBrainV1BaselineNoNeutral.py:5`), `regime_router_force_mode` (`freqtrade/user_data/strategies/GridBrainV1BaselineNoNeutral.py:6`)

### `freqtrade/user_data/strategies/GridBrainV1ExpRouterFast.py`

- Top-level functions: `0`
- Classes: `1`
- `GridBrainV1ExpRouterFast` (`freqtrade/user_data/strategies/GridBrainV1ExpRouterFast.py:4`) -> attrs `2`, methods `0`
  - attrs: `regime_router_switch_persist_bars` (`freqtrade/user_data/strategies/GridBrainV1ExpRouterFast.py:11`), `regime_router_switch_margin` (`freqtrade/user_data/strategies/GridBrainV1ExpRouterFast.py:12`)

### `freqtrade/user_data/strategies/GridBrainV1NeutralDiFilter.py`

- Top-level functions: `0`
- Classes: `1`
- `GridBrainV1NeutralDiFilter` (`freqtrade/user_data/strategies/GridBrainV1NeutralDiFilter.py:4`) -> attrs `1`, methods `1`
  - attrs: `neutral_di_flip_max` (`freqtrade/user_data/strategies/GridBrainV1NeutralDiFilter.py:5`)
  - methods: `_regime_router_state` (`freqtrade/user_data/strategies/GridBrainV1NeutralDiFilter.py:7`)

### `freqtrade/user_data/strategies/GridBrainV1NeutralEligibilityOnly.py`

- Top-level functions: `0`
- Classes: `1`
- `GridBrainV1NeutralEligibilityOnly` (`freqtrade/user_data/strategies/GridBrainV1NeutralEligibilityOnly.py:4`) -> attrs `6`, methods `0`
  - attrs: `neutral_grid_levels_ratio` (`freqtrade/user_data/strategies/GridBrainV1NeutralEligibilityOnly.py:5`), `neutral_grid_budget_ratio` (`freqtrade/user_data/strategies/GridBrainV1NeutralEligibilityOnly.py:6`), `neutral_enter_persist_min` (`freqtrade/user_data/strategies/GridBrainV1NeutralEligibilityOnly.py:7`), `neutral_enter_persist_max` (`freqtrade/user_data/strategies/GridBrainV1NeutralEligibilityOnly.py:8`), `neutral_persistence_default_enter` (`freqtrade/user_data/strategies/GridBrainV1NeutralEligibilityOnly.py:9`), `neutral_cooldown_multiplier` (`freqtrade/user_data/strategies/GridBrainV1NeutralEligibilityOnly.py:10`)

### `freqtrade/user_data/strategies/GridBrainV1NoFVG.py`

- Top-level functions: `0`
- Classes: `1`
- `GridBrainV1NoFVG` (`freqtrade/user_data/strategies/GridBrainV1NoFVG.py:4`) -> attrs `5`, methods `0`
  - attrs: `fvg_enabled` (`freqtrade/user_data/strategies/GridBrainV1NoFVG.py:7`), `defensive_fvg_enabled` (`freqtrade/user_data/strategies/GridBrainV1NoFVG.py:8`), `session_fvg_enabled` (`freqtrade/user_data/strategies/GridBrainV1NoFVG.py:9`), `session_fvg_inside_gate` (`freqtrade/user_data/strategies/GridBrainV1NoFVG.py:10`), `imfvg_enabled` (`freqtrade/user_data/strategies/GridBrainV1NoFVG.py:11`)

### `freqtrade/user_data/strategies/GridBrainV1NoPause.py`

- Top-level functions: `0`
- Classes: `1`
- `GridBrainV1NoPause` (`freqtrade/user_data/strategies/GridBrainV1NoPause.py:4`) -> attrs `2`, methods `0`
  - attrs: `regime_router_allow_pause` (`freqtrade/user_data/strategies/GridBrainV1NoPause.py:11`), `regime_router_default_mode` (`freqtrade/user_data/strategies/GridBrainV1NoPause.py:12`)

### `freqtrade/user_data/strategies/sample_strategy.py`

- Top-level functions: `0`
- Classes: `1`
- `SampleStrategy` (`freqtrade/user_data/strategies/sample_strategy.py:40`) -> attrs `18`, methods `4`
  - attrs: `INTERFACE_VERSION` (`freqtrade/user_data/strategies/sample_strategy.py:60`), `can_short` (`freqtrade/user_data/strategies/sample_strategy.py:63`), `minimal_roi` (`freqtrade/user_data/strategies/sample_strategy.py:67`), `stoploss` (`freqtrade/user_data/strategies/sample_strategy.py:76`), `trailing_stop` (`freqtrade/user_data/strategies/sample_strategy.py:79`), `timeframe` (`freqtrade/user_data/strategies/sample_strategy.py:85`), `process_only_new_candles` (`freqtrade/user_data/strategies/sample_strategy.py:88`), `use_exit_signal` (`freqtrade/user_data/strategies/sample_strategy.py:91`), `exit_profit_only` (`freqtrade/user_data/strategies/sample_strategy.py:92`), `ignore_roi_if_entry_signal` (`freqtrade/user_data/strategies/sample_strategy.py:93`), `buy_rsi` (`freqtrade/user_data/strategies/sample_strategy.py:96`), `sell_rsi` (`freqtrade/user_data/strategies/sample_strategy.py:97`), `short_rsi` (`freqtrade/user_data/strategies/sample_strategy.py:98`), `exit_short_rsi` (`freqtrade/user_data/strategies/sample_strategy.py:99`), `startup_candle_count` (`freqtrade/user_data/strategies/sample_strategy.py:104`), `order_types` (`freqtrade/user_data/strategies/sample_strategy.py:107`), `order_time_in_force` (`freqtrade/user_data/strategies/sample_strategy.py:115`), `plot_config` (`freqtrade/user_data/strategies/sample_strategy.py:117`)
  - methods: `informative_pairs` (`freqtrade/user_data/strategies/sample_strategy.py:133`), `populate_indicators` (`freqtrade/user_data/strategies/sample_strategy.py:146`), `populate_entry_trend` (`freqtrade/user_data/strategies/sample_strategy.py:366`), `populate_exit_trend` (`freqtrade/user_data/strategies/sample_strategy.py:397`)

### `freqtrade/user_data/tests/test_chaos_replay_harness.py`

- Top-level functions: `8`
- `_build_replay_df` (`freqtrade/user_data/tests/test_chaos_replay_harness.py:9`), `_plan_at` (`freqtrade/user_data/tests/test_chaos_replay_harness.py:22`), `_base_profile` (`freqtrade/user_data/tests/test_chaos_replay_harness.py:35`), `_simulate` (`freqtrade/user_data/tests/test_chaos_replay_harness.py:53`), `test_chaos_profile_is_deterministic_and_reports_delta` (`freqtrade/user_data/tests/test_chaos_replay_harness.py:66`), `test_chaos_partial_fill_profile_marks_partial_fills` (`freqtrade/user_data/tests/test_chaos_replay_harness.py:91`), `test_chaos_data_gap_profile_drops_candles` (`freqtrade/user_data/tests/test_chaos_replay_harness.py:104`), `test_chaos_fault_injection_profiles_trigger_expected_rails` (`freqtrade/user_data/tests/test_chaos_replay_harness.py:161`)
- Classes: `0`

### `freqtrade/user_data/tests/test_executor_hardening.py`

- Top-level functions: `12`
- `_base_plan` (`freqtrade/user_data/tests/test_executor_hardening.py:14`), `_executor` (`freqtrade/user_data/tests/test_executor_hardening.py:98`), `test_ccxt_place_limit_retries_post_only_with_backoff_and_reprice` (`freqtrade/user_data/tests/test_executor_hardening.py:111`), `test_reject_burst_blocks_start_and_downgrades_to_hold` (`freqtrade/user_data/tests/test_executor_hardening.py:131`), `test_stop_exit_confirm_uses_failsafe_reason` (`freqtrade/user_data/tests/test_executor_hardening.py:153`), `test_rebuild_confirm_failure_is_tracked_separately` (`freqtrade/user_data/tests/test_executor_hardening.py:176`), `test_reconcile_matches_live_orders_with_tolerance` (`freqtrade/user_data/tests/test_executor_hardening.py:201`), `test_reconcile_honors_action_cap` (`freqtrade/user_data/tests/test_executor_hardening.py:233`), `test_executor_recovers_state_file_on_startup` (`freqtrade/user_data/tests/test_executor_hardening.py:260`), `test_capacity_rung_cap_limits_seeded_orders_in_paper` (`freqtrade/user_data/tests/test_executor_hardening.py:306`), `test_capacity_hard_block_prevents_start` (`freqtrade/user_data/tests/test_executor_hardening.py:339`), `test_execution_cost_feedback_writes_artifact_and_lifecycle_logs` (`freqtrade/user_data/tests/test_executor_hardening.py:365`)
- Classes: `2`
- `_RetryThenAcceptExchange` (`freqtrade/user_data/tests/test_executor_hardening.py:71`) -> attrs `0`, methods `4`
  - methods: `__init__` (`freqtrade/user_data/tests/test_executor_hardening.py:72`), `price_to_precision` (`freqtrade/user_data/tests/test_executor_hardening.py:76`), `amount_to_precision` (`freqtrade/user_data/tests/test_executor_hardening.py:79`), `create_limit_buy_order` (`freqtrade/user_data/tests/test_executor_hardening.py:82`)
- `_ReconcileExchange` (`freqtrade/user_data/tests/test_executor_hardening.py:90`) -> attrs `0`, methods `2`
  - methods: `__init__` (`freqtrade/user_data/tests/test_executor_hardening.py:91`), `fetch_open_orders` (`freqtrade/user_data/tests/test_executor_hardening.py:94`)

### `freqtrade/user_data/tests/test_liquidity_sweeps.py`

- Top-level functions: `6`
- `_sweep_df` (`freqtrade/user_data/tests/test_liquidity_sweeps.py:8`), `_base_cfg` (`freqtrade/user_data/tests/test_liquidity_sweeps.py:21`), `test_pivot_confirmation_is_bar_confirmed` (`freqtrade/user_data/tests/test_liquidity_sweeps.py:37`), `test_wick_sweep_and_break_retest_stop_through_box_edge` (`freqtrade/user_data/tests/test_liquidity_sweeps.py:59`), `test_retest_validation_mode_toggle_affects_break_retest_only` (`freqtrade/user_data/tests/test_liquidity_sweeps.py:76`), `test_determinism_for_same_inputs` (`freqtrade/user_data/tests/test_liquidity_sweeps.py:101`)
- Classes: `0`

### `freqtrade/user_data/tests/test_meta_drift_replay.py`

- Top-level functions: `3`
- `_build_replay_df` (`freqtrade/user_data/tests/test_meta_drift_replay.py:8`), `_plan_at` (`freqtrade/user_data/tests/test_meta_drift_replay.py:21`), `test_replay_synthetic_regime_shift_tracks_meta_drift_soft_and_hard` (`freqtrade/user_data/tests/test_meta_drift_replay.py:53`)
- Classes: `0`

### `freqtrade/user_data/tests/test_min_range_and_breakout_confirm.py`

- Top-level functions: `10`
- `_strategy_for_breakout_buffer` (`freqtrade/user_data/tests/test_min_range_and_breakout_confirm.py:9`), `_close_df` (`freqtrade/user_data/tests/test_min_range_and_breakout_confirm.py:16`), `test_min_range_len_gate_blocks_before_threshold` (`freqtrade/user_data/tests/test_min_range_and_breakout_confirm.py:20`), `test_min_range_len_gate_passes_at_threshold` (`freqtrade/user_data/tests/test_min_range_and_breakout_confirm.py:34`), `test_min_range_len_gate_resets_on_new_box_generation` (`freqtrade/user_data/tests/test_min_range_and_breakout_confirm.py:46`), `test_breakout_confirm_single_close_outside_is_not_confirmed` (`freqtrade/user_data/tests/test_min_range_and_breakout_confirm.py:64`), `test_breakout_confirm_up_blocks_start_when_not_running` (`freqtrade/user_data/tests/test_min_range_and_breakout_confirm.py:79`), `test_breakout_confirm_dn_stops_when_running` (`freqtrade/user_data/tests/test_min_range_and_breakout_confirm.py:98`), `test_breakout_confirm_buffer_modes` (`freqtrade/user_data/tests/test_min_range_and_breakout_confirm.py:125`), `test_breakout_confirm_determinism_on_same_input` (`freqtrade/user_data/tests/test_min_range_and_breakout_confirm.py:138`)
- Classes: `0`

### `freqtrade/user_data/tests/test_ml_overlay_step14.py`

- Top-level functions: `7`
- `_window` (`freqtrade/user_data/tests/test_ml_overlay_step14.py:17`), `_write_summary` (`freqtrade/user_data/tests/test_ml_overlay_step14.py:34`), `_write_json` (`freqtrade/user_data/tests/test_ml_overlay_step14.py:69`), `_write_schema` (`freqtrade/user_data/tests/test_ml_overlay_step14.py:74`), `test_step14_ml_scripts_pipeline` (`freqtrade/user_data/tests/test_ml_overlay_step14.py:108`), `test_tuning_protocol_respects_required_ml_overlay_gate` (`freqtrade/user_data/tests/test_ml_overlay_step14.py:212`), `test_ml_overlay_defaults_are_advisory_and_off` (`freqtrade/user_data/tests/test_ml_overlay_step14.py:332`)
- Classes: `0`

### `freqtrade/user_data/tests/test_order_blocks.py`

- Top-level functions: `7`
- `_new_strategy` (`freqtrade/user_data/tests/test_order_blocks.py:9`), `_bull_ob_df` (`freqtrade/user_data/tests/test_order_blocks.py:13`), `_bear_ob_df` (`freqtrade/user_data/tests/test_order_blocks.py:26`), `_as_strategy_df` (`freqtrade/user_data/tests/test_order_blocks.py:39`), `test_order_block_detects_bull_and_mitigation` (`freqtrade/user_data/tests/test_order_blocks.py:48`), `test_order_block_detects_bear_and_freshness_window` (`freqtrade/user_data/tests/test_order_blocks.py:69`), `test_order_block_strategy_state_applies_fresh_gate_straddle_and_tp_nudges` (`freqtrade/user_data/tests/test_order_blocks.py:89`)
- Classes: `0`

### `freqtrade/user_data/tests/test_partial_module_completion.py`

- Top-level functions: `5`
- `_new_strategy` (`freqtrade/user_data/tests/test_partial_module_completion.py:14`), `test_protections_drawdown_and_stop_window_helpers` (`freqtrade/user_data/tests/test_partial_module_completion.py:18`), `test_micro_bias_order_flow_and_reentry_helpers` (`freqtrade/user_data/tests/test_partial_module_completion.py:46`), `test_fvg_vp_channel_and_session_sweep_helpers` (`freqtrade/user_data/tests/test_partial_module_completion.py:125`), `test_event_bus_emits_reason_and_taxonomy_events` (`freqtrade/user_data/tests/test_partial_module_completion.py:204`)
- Classes: `0`

### `freqtrade/user_data/tests/test_phase3_validation.py`

- Top-level functions: `48`
- `test_box_signature_is_repeatable` (`freqtrade/user_data/tests/test_phase3_validation.py:16`), `test_poc_cross_detected_when_open_close_bracket_value` (`freqtrade/user_data/tests/test_phase3_validation.py:22`), `test_derive_box_block_reasons_reflects_conflicts` (`freqtrade/user_data/tests/test_phase3_validation.py:33`), `test_poc_acceptance_status_persists_once_crossed` (`freqtrade/user_data/tests/test_phase3_validation.py:45`), `_fresh_phase3_strategy` (`freqtrade/user_data/tests/test_phase3_validation.py:64`), `test_data_quality_checks_flag_gap` (`freqtrade/user_data/tests/test_phase3_validation.py:75`), `test_data_quality_checks_flag_duplicates` (`freqtrade/user_data/tests/test_phase3_validation.py:91`), `test_data_quality_checks_zero_volume_streak` (`freqtrade/user_data/tests/test_phase3_validation.py:107`), `test_phase2_gate_failures_records_block_reasons` (`freqtrade/user_data/tests/test_phase3_validation.py:125`), `test_start_block_reasons_include_baseline_codes` (`freqtrade/user_data/tests/test_phase3_validation.py:144`), `test_start_block_reasons_include_breakout_block` (`freqtrade/user_data/tests/test_phase3_validation.py:157`), `test_materiality_waits_for_epoch_or_delta` (`freqtrade/user_data/tests/test_phase3_validation.py:168`), `test_compute_band_slope_pct_respects_window` (`freqtrade/user_data/tests/test_phase3_validation.py:186`), `test_excursion_asymmetry_ratio_handles_invalid_devs` (`freqtrade/user_data/tests/test_phase3_validation.py:197`), `test_funding_gate_honors_threshold` (`freqtrade/user_data/tests/test_phase3_validation.py:203`), `test_box_straddle_breakout_detection_adds_blocker` (`freqtrade/user_data/tests/test_phase3_validation.py:213`), `test_squeeze_release_block_reason_is_consumed` (`freqtrade/user_data/tests/test_phase3_validation.py:223`), `test_bbw_nonexpanding_gate_requires_flat_or_contracting_window` (`freqtrade/user_data/tests/test_phase3_validation.py:231`), `test_breakout_fresh_state_blocks_until_reclaimed` (`freqtrade/user_data/tests/test_phase3_validation.py:238`), `test_detect_structural_breakout_uses_close_vs_prior_extremes` (`freqtrade/user_data/tests/test_phase3_validation.py:255`), `test_hvp_stats_returns_current_and_sma` (`freqtrade/user_data/tests/test_phase3_validation.py:271`), `test_planner_health_state_transitions` (`freqtrade/user_data/tests/test_phase3_validation.py:283`), `test_start_stability_state_supports_k_of_n_and_score` (`freqtrade/user_data/tests/test_phase3_validation.py:292`), `test_box_quality_metrics_and_straddle_helpers` (`freqtrade/user_data/tests/test_phase3_validation.py:305`), `test_box_quality_levels_linear_fallback_when_nonpositive_bounds` (`freqtrade/user_data/tests/test_phase3_validation.py:320`), `test_midline_bias_fallback_activates_when_vrvp_poc_is_neutral` (`freqtrade/user_data/tests/test_phase3_validation.py:333`), `test_midline_bias_fallback_stays_inactive_when_vrvp_poc_not_neutral` (`freqtrade/user_data/tests/test_phase3_validation.py:364`), `test_fallback_poc_estimate_uses_volume_weighted_typical_price` (`freqtrade/user_data/tests/test_phase3_validation.py:393`), `test_box_width_avg_veto_triggers_when_width_exceeds_rolling_ratio` (`freqtrade/user_data/tests/test_phase3_validation.py:410`), `test_poc_alignment_strict_requires_cross_when_misaligned` (`freqtrade/user_data/tests/test_phase3_validation.py:424`), `test_poc_acceptance_handles_multiple_candidates` (`freqtrade/user_data/tests/test_phase3_validation.py:463`), `test_box_overlap_prune_detects_high_overlap` (`freqtrade/user_data/tests/test_phase3_validation.py:476`), `test_latest_daily_vwap_computation` (`freqtrade/user_data/tests/test_phase3_validation.py:484`), `_cost_strategy` (`freqtrade/user_data/tests/test_phase3_validation.py:510`), `test_grid_sizing_reduces_n_to_meet_cost_floor` (`freqtrade/user_data/tests/test_phase3_validation.py:542`), `test_effective_cost_floor_uses_empirical_and_emits_stale_warning` (`freqtrade/user_data/tests/test_phase3_validation.py:557`), `test_effective_cost_floor_switches_to_empirical_when_higher` (`freqtrade/user_data/tests/test_phase3_validation.py:565`), `test_effective_cost_floor_proxy_only_samples_do_not_promote_empirical` (`freqtrade/user_data/tests/test_phase3_validation.py:586`), `test_effective_cost_floor_promotes_with_empirical_artifact` (`freqtrade/user_data/tests/test_phase3_validation.py:609`), `test_tp_selection_prefers_nearest_conservative` (`freqtrade/user_data/tests/test_phase3_validation.py:659`), `test_sl_selection_avoids_lvn_and_fvg_gap` (`freqtrade/user_data/tests/test_phase3_validation.py:675`), `test_simulator_fill_guard_respects_no_repeat_toggle` (`freqtrade/user_data/tests/test_phase3_validation.py:690`), `test_executor_fill_guard_respects_no_repeat_toggle` (`freqtrade/user_data/tests/test_phase3_validation.py:703`), `test_executor_fill_bar_index_tracks_plan_clock` (`freqtrade/user_data/tests/test_phase3_validation.py:715`), `test_meta_drift_guard_detects_hard_shift` (`freqtrade/user_data/tests/test_phase3_validation.py:734`), `test_meta_drift_state_maps_to_actions` (`freqtrade/user_data/tests/test_phase3_validation.py:778`), `test_empirical_cost_sample_uses_execution_cost_artifact` (`freqtrade/user_data/tests/test_phase3_validation.py:852`), `test_decision_and_event_logs_are_emitted_with_schema` (`freqtrade/user_data/tests/test_phase3_validation.py:896`)
- Classes: `0`

### `freqtrade/user_data/tests/test_replay_golden_consistency.py`

- Top-level functions: `4`
- `_build_df` (`freqtrade/user_data/tests/test_replay_golden_consistency.py:8`), `_plan` (`freqtrade/user_data/tests/test_replay_golden_consistency.py:21`), `test_replay_golden_summary_contract_is_strict` (`freqtrade/user_data/tests/test_replay_golden_consistency.py:63`), `test_replay_brain_simulator_consistency_trace_matches_plans` (`freqtrade/user_data/tests/test_replay_golden_consistency.py:126`)
- Classes: `0`

### `freqtrade/user_data/tests/test_stress_replay_standard_validation.py`

- Top-level functions: `3`
- `_replay_df` (`freqtrade/user_data/tests/test_stress_replay_standard_validation.py:17`), `_plan` (`freqtrade/user_data/tests/test_stress_replay_standard_validation.py:31`), `test_stress_replay_standard_validation_summary_contract` (`freqtrade/user_data/tests/test_stress_replay_standard_validation.py:44`)
- Classes: `0`

### `freqtrade/user_data/tests/test_tuning_protocol.py`

- Top-level functions: `8`
- `_write_summary` (`freqtrade/user_data/tests/test_tuning_protocol.py:12`), `_write_manifest` (`freqtrade/user_data/tests/test_tuning_protocol.py:85`), `_write_registry` (`freqtrade/user_data/tests/test_tuning_protocol.py:90`), `_write_schema` (`freqtrade/user_data/tests/test_tuning_protocol.py:95`), `_run_protocol` (`freqtrade/user_data/tests/test_tuning_protocol.py:136`), `test_tuning_protocol_promotes_candidate_with_passed_gates` (`freqtrade/user_data/tests/test_tuning_protocol.py:164`), `test_tuning_protocol_strict_fails_when_chaos_gate_fails` (`freqtrade/user_data/tests/test_tuning_protocol.py:325`), `test_tuning_protocol_strict_fails_when_required_ablation_missing` (`freqtrade/user_data/tests/test_tuning_protocol.py:456`)
- Classes: `0`

### `freqtrade_cli.py`

- Top-level functions: `3`
- `_is_repo_module` (`freqtrade_cli.py:10`), `_prime_repo_package` (`freqtrade_cli.py:23`), `main` (`freqtrade_cli.py:51`)
- Classes: `0`

### `io/__init__.py`

- Top-level functions: `0`
- Classes: `0`

### `io/atomic_json.py`

- Top-level functions: `0`
- Classes: `0`

### `planner/__init__.py`

- Top-level functions: `0`
- Classes: `0`

### `planner/replan_policy.py`

- Top-level functions: `1`
- `evaluate_replan_materiality` (`planner/replan_policy.py:18`)
- Classes: `1`
- `ReplanThresholds` (`planner/replan_policy.py:10`) -> attrs `5`, methods `0`
  - attrs: `epoch_bars` (`planner/replan_policy.py:11`), `box_mid_shift_max_step_frac` (`planner/replan_policy.py:12`), `box_width_change_pct` (`planner/replan_policy.py:13`), `tp_shift_max_step_frac` (`planner/replan_policy.py:14`), `sl_shift_max_step_frac` (`planner/replan_policy.py:15`)

### `planner/start_stability.py`

- Top-level functions: `1`
- `evaluate_start_stability` (`planner/start_stability.py:9`)
- Classes: `0`

### `planner/structure/__init__.py`

- Top-level functions: `0`
- Classes: `0`

### `planner/structure/liquidity_sweeps.py`

- Top-level functions: `4`
- `_atr` (`planner/structure/liquidity_sweeps.py:26`), `_buffer_value` (`planner/structure/liquidity_sweeps.py:43`), `_confirmed_pivot_indices` (`planner/structure/liquidity_sweeps.py:64`), `analyze_liquidity_sweeps` (`planner/structure/liquidity_sweeps.py:90`)
- Classes: `1`
- `LiquiditySweepConfig` (`planner/structure/liquidity_sweeps.py:12`) -> attrs `11`, methods `0`
  - attrs: `enabled` (`planner/structure/liquidity_sweeps.py:13`), `pivot_len` (`planner/structure/liquidity_sweeps.py:14`), `max_age_bars` (`planner/structure/liquidity_sweeps.py:15`), `break_buffer_mode` (`planner/structure/liquidity_sweeps.py:16`), `break_buffer_value` (`planner/structure/liquidity_sweeps.py:17`), `retest_window_bars` (`planner/structure/liquidity_sweeps.py:18`), `retest_buffer_mode` (`planner/structure/liquidity_sweeps.py:19`), `retest_buffer_value` (`planner/structure/liquidity_sweeps.py:20`), `stop_if_through_box_edge` (`planner/structure/liquidity_sweeps.py:21`), `retest_validation_mode` (`planner/structure/liquidity_sweeps.py:22`), `min_level_separation_steps` (`planner/structure/liquidity_sweeps.py:23`)

### `planner/structure/order_blocks.py`

- Top-level functions: `8`
- `_atr` (`planner/structure/order_blocks.py:81`), `_row_ts_seconds` (`planner/structure/order_blocks.py:95`), `_extract_ts_series` (`planner/structure/order_blocks.py:109`), `_zone_bounds` (`planner/structure/order_blocks.py:115`), `_is_impulse_match` (`planner/structure/order_blocks.py:129`), `_detect_latest_block_for_side` (`planner/structure/order_blocks.py:145`), `_age_gated_block` (`planner/structure/order_blocks.py:245`), `build_order_block_snapshot` (`planner/structure/order_blocks.py:263`)
- Classes: `3`
- `OrderBlock` (`planner/structure/order_blocks.py:15`) -> attrs `8`, methods `0`
  - attrs: `side` (`planner/structure/order_blocks.py:16`), `tf` (`planner/structure/order_blocks.py:17`), `created_ts` (`planner/structure/order_blocks.py:18`), `top` (`planner/structure/order_blocks.py:19`), `bottom` (`planner/structure/order_blocks.py:20`), `mid` (`planner/structure/order_blocks.py:21`), `mitigated` (`planner/structure/order_blocks.py:22`), `last_mitigated_ts` (`planner/structure/order_blocks.py:23`)
- `OrderBlockConfig` (`planner/structure/order_blocks.py:27`) -> attrs `9`, methods `0`
  - attrs: `enabled` (`planner/structure/order_blocks.py:28`), `tf` (`planner/structure/order_blocks.py:29`), `use_wick_zone` (`planner/structure/order_blocks.py:30`), `impulse_lookahead` (`planner/structure/order_blocks.py:31`), `impulse_atr_len` (`planner/structure/order_blocks.py:32`), `impulse_atr_mult` (`planner/structure/order_blocks.py:33`), `fresh_bars` (`planner/structure/order_blocks.py:34`), `max_age_bars` (`planner/structure/order_blocks.py:35`), `mitigation_mode` (`planner/structure/order_blocks.py:36`)
- `OrderBlockSnapshot` (`planner/structure/order_blocks.py:40`) -> attrs `8`, methods `1`
  - attrs: `bull` (`planner/structure/order_blocks.py:41`), `bear` (`planner/structure/order_blocks.py:42`), `bull_age_bars` (`planner/structure/order_blocks.py:43`), `bear_age_bars` (`planner/structure/order_blocks.py:44`), `bull_fresh` (`planner/structure/order_blocks.py:45`), `bear_fresh` (`planner/structure/order_blocks.py:46`), `bull_valid` (`planner/structure/order_blocks.py:47`), `bear_valid` (`planner/structure/order_blocks.py:48`)
  - methods: `as_dict` (`planner/structure/order_blocks.py:50`)

### `planner/volatility_policy_adapter.py`

- Top-level functions: `6`
- `_clip` (`planner/volatility_policy_adapter.py:11`), `_safe_float` (`planner/volatility_policy_adapter.py:15`), `_atr_bucket` (`planner/volatility_policy_adapter.py:27`), `_bbwp_bucket` (`planner/volatility_policy_adapter.py:43`), `compute_volatility_policy_view` (`planner/volatility_policy_adapter.py:64`), `compute_n_level_bounds` (`planner/volatility_policy_adapter.py:258`)
- Classes: `0`

### `risk/__init__.py`

- Top-level functions: `0`
- Classes: `0`

### `risk/meta_drift_guard.py`

- Top-level functions: `1`
- `_safe_float` (`risk/meta_drift_guard.py:9`)
- Classes: `1`
- `MetaDriftGuard` (`risk/meta_drift_guard.py:25`) -> attrs `0`, methods `4`
  - methods: `__init__` (`risk/meta_drift_guard.py:28`), `reset_pair` (`risk/meta_drift_guard.py:33`), `_pair_state` (`risk/meta_drift_guard.py:36`), `observe` (`risk/meta_drift_guard.py:46`)

### `sim/__init__.py`

- Top-level functions: `0`
- Classes: `0`

### `sim/chaos_profiles.py`

- Top-level functions: `3`
- `default_chaos_profile` (`sim/chaos_profiles.py:10`), `validate_chaos_profile` (`sim/chaos_profiles.py:30`), `load_chaos_profile` (`sim/chaos_profiles.py:34`)
- Classes: `0`

