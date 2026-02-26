# Code Implementation Snapshot (Generated from Source)

- Generated: `2026-02-26T21:52:01.159504+00:00`
- Purpose: Code-only implementation reference to compare old/new plans and prevent accidental removals.
- Scope: Custom project code and user modules; excludes upstream `freqtrade/freqtrade/**` framework internals.

## 1) Files Scanned

- Python files: `48`
- Schema/config files: `10`
- Docs files: `10`
- Shell helper files: `2`

### 1.1 Python Source Manifest

- `analytics/__init__.py` (lines: 2)
- `analytics/execution_cost_calibrator.py` (lines: 200)
- `core/atomic_json.py` (lines: 54)
- `core/enums.py` (lines: 549)
- `core/plan_signature.py` (lines: 242)
- `core/schema_validation.py` (lines: 50)
- `data/__init__.py` (lines: 2)
- `data/data_quality_assessor.py` (lines: 78)
- `execution/__init__.py` (lines: 2)
- `execution/capacity_guard.py` (lines: 141)
- `freqtrade/user_data/scripts/grid_executor_v1.py` (lines: 2902)
- `freqtrade/user_data/scripts/grid_simulator_v1.py` (lines: 2354)
- `freqtrade/user_data/scripts/regime_audit_v1.py` (lines: 1070)
- `freqtrade/user_data/scripts/user_regression_suite.py` (lines: 749)
- `freqtrade/user_data/strategies/GridBrainV1.py` (lines: 9610)
- `freqtrade/user_data/strategies/GridBrainV1BaselineNoNeutral.py` (lines: 6)
- `freqtrade/user_data/strategies/GridBrainV1ExpRouterFast.py` (lines: 12)
- `freqtrade/user_data/strategies/GridBrainV1NeutralDiFilter.py` (lines: 17)
- `freqtrade/user_data/strategies/GridBrainV1NeutralEligibilityOnly.py` (lines: 11)
- `freqtrade/user_data/strategies/GridBrainV1NoFVG.py` (lines: 11)
- `freqtrade/user_data/strategies/GridBrainV1NoPause.py` (lines: 12)
- `freqtrade/user_data/strategies/sample_strategy.py` (lines: 428)
- `freqtrade/user_data/tests/test_chaos_replay_harness.py` (lines: 192)
- `freqtrade/user_data/tests/test_executor_hardening.py` (lines: 398)
- `freqtrade/user_data/tests/test_liquidity_sweeps.py` (lines: 118)
- `freqtrade/user_data/tests/test_meta_drift_replay.py` (lines: 77)
- `freqtrade/user_data/tests/test_min_range_and_breakout_confirm.py` (lines: 154)
- `freqtrade/user_data/tests/test_ml_overlay_step14.py` (lines: 334)
- `freqtrade/user_data/tests/test_order_blocks.py` (lines: 118)
- `freqtrade/user_data/tests/test_partial_module_completion.py` (lines: 266)
- `freqtrade/user_data/tests/test_phase3_validation.py` (lines: 960)
- `freqtrade/user_data/tests/test_replay_golden_consistency.py` (lines: 188)
- `freqtrade/user_data/tests/test_stress_replay_standard_validation.py` (lines: 61)
- `freqtrade/user_data/tests/test_tuning_protocol.py` (lines: 573)
- `freqtrade_cli.py` (lines: 52)
- `io/__init__.py` (lines: 2)
- `io/atomic_json.py` (lines: 6)
- `planner/__init__.py` (lines: 2)
- `planner/replan_policy.py` (lines: 90)
- `planner/start_stability.py` (lines: 29)
- `planner/structure/__init__.py` (lines: 21)
- `planner/structure/liquidity_sweeps.py` (lines: 333)
- `planner/structure/order_blocks.py` (lines: 319)
- `planner/volatility_policy_adapter.py` (lines: 287)
- `risk/__init__.py` (lines: 2)
- `risk/meta_drift_guard.py` (lines: 198)
- `sim/__init__.py` (lines: 2)
- `sim/chaos_profiles.py` (lines: 41)

### 1.2 Schema/Config Manifest

- `experiments/champions.json` (lines: 64)
- `experiments/manifest.yaml` (lines: 89)
- `experiments/metrics_schema.json` (lines: 40)
- `schemas/__init__.py` (lines: 2)
- `schemas/chaos_profile.schema.json` (lines: 176)
- `schemas/decision_log.schema.json` (lines: 105)
- `schemas/event_log.schema.json` (lines: 58)
- `schemas/execution_cost_calibration.schema.json` (lines: 83)
- `schemas/grid_plan.schema.json` (lines: 228)
- `schemas/plan_signature.py` (lines: 35)

### 1.3 Docs Manifest

- `README.md` (lines: 22)
- `docs/ATOMIC_PLAN_HANDOFF.md` (lines: 48)
- `docs/CODING_RULES.md` (lines: 197)
- `docs/DECISION_REASON_CODES.md` (lines: 1340)
- `docs/GRID_MASTER_PLAN.md` (lines: 2535)
- `docs/REPLAN_POLICY_AND_MATERIALITY.md` (lines: 40)
- `docs/STRESS_REPLAY_PROFILES.md` (lines: 44)
- `docs/TUNING_PROTOCOL_WALKFORWARD_PBO.md` (lines: 29)
- `docs/codex_resume_workflow.md` (lines: 35)
- `docs/storage_cleanup_workflow.md` (lines: 146)

## 2) Canonical Reason/Event Registry (from `core/enums.py`)

### BlockReason (70)

- `BLOCK_ADX_HIGH` (`BlockReason.BLOCK_ADX_HIGH` at `core/enums.py:147`)
- `BLOCK_BBW_EXPANDING` (`BlockReason.BLOCK_BBW_EXPANDING` at `core/enums.py:148`)
- `BLOCK_EMA_DIST` (`BlockReason.BLOCK_EMA_DIST` at `core/enums.py:149`)
- `BLOCK_RVOL_SPIKE` (`BlockReason.BLOCK_RVOL_SPIKE` at `core/enums.py:150`)
- `BLOCK_7D_EXTREME_CONTEXT` (`BlockReason.BLOCK_7D_EXTREME_CONTEXT` at `core/enums.py:151`)
- `BLOCK_FRESH_BREAKOUT` (`BlockReason.BLOCK_FRESH_BREAKOUT` at `core/enums.py:154`)
- `BLOCK_BREAKOUT_RECLAIM_PENDING` (`BlockReason.BLOCK_BREAKOUT_RECLAIM_PENDING` at `core/enums.py:155`)
- `BLOCK_BREAKOUT_CONFIRM_UP` (`BlockReason.BLOCK_BREAKOUT_CONFIRM_UP` at `core/enums.py:156`)
- `BLOCK_BREAKOUT_CONFIRM_DN` (`BlockReason.BLOCK_BREAKOUT_CONFIRM_DN` at `core/enums.py:157`)
- `BLOCK_MIN_RANGE_LEN_NOT_MET` (`BlockReason.BLOCK_MIN_RANGE_LEN_NOT_MET` at `core/enums.py:158`)
- `BLOCK_OS_DEV_DIRECTIONAL` (`BlockReason.BLOCK_OS_DEV_DIRECTIONAL` at `core/enums.py:159`)
- `BLOCK_OS_DEV_NEUTRAL_PERSISTENCE` (`BlockReason.BLOCK_OS_DEV_NEUTRAL_PERSISTENCE` at `core/enums.py:160`)
- `BLOCK_BAND_SLOPE_HIGH` (`BlockReason.BLOCK_BAND_SLOPE_HIGH` at `core/enums.py:161`)
- `BLOCK_DRIFT_SLOPE_HIGH` (`BlockReason.BLOCK_DRIFT_SLOPE_HIGH` at `core/enums.py:162`)
- `BLOCK_EXCURSION_ASYMMETRY` (`BlockReason.BLOCK_EXCURSION_ASYMMETRY` at `core/enums.py:163`)
- `BLOCK_META_DRIFT_SOFT` (`BlockReason.BLOCK_META_DRIFT_SOFT` at `core/enums.py:164`)
- `BLOCK_BBWP_HIGH` (`BlockReason.BLOCK_BBWP_HIGH` at `core/enums.py:167`)
- `COOLOFF_BBWP_EXTREME` (`BlockReason.COOLOFF_BBWP_EXTREME` at `core/enums.py:168`)
- `BLOCK_FUNDING_FILTER` (`BlockReason.BLOCK_FUNDING_FILTER` at `core/enums.py:169`)
- `BLOCK_SQUEEZE_RELEASE_AGAINST_BIAS` (`BlockReason.BLOCK_SQUEEZE_RELEASE_AGAINST_BIAS` at `core/enums.py:170`)
- `BLOCK_VOL_BUCKET_UNSTABLE` (`BlockReason.BLOCK_VOL_BUCKET_UNSTABLE` at `core/enums.py:171`)
- `BLOCK_BOX_WIDTH_TOO_NARROW` (`BlockReason.BLOCK_BOX_WIDTH_TOO_NARROW` at `core/enums.py:174`)
- `BLOCK_BOX_WIDTH_TOO_WIDE` (`BlockReason.BLOCK_BOX_WIDTH_TOO_WIDE` at `core/enums.py:175`)
- `BLOCK_BOX_STRADDLE_BREAKOUT_LEVEL` (`BlockReason.BLOCK_BOX_STRADDLE_BREAKOUT_LEVEL` at `core/enums.py:176`)
- `BLOCK_BOX_STRADDLE_OB_EDGE` (`BlockReason.BLOCK_BOX_STRADDLE_OB_EDGE` at `core/enums.py:177`)
- `BLOCK_BOX_STRADDLE_FVG_EDGE` (`BlockReason.BLOCK_BOX_STRADDLE_FVG_EDGE` at `core/enums.py:178`)
- `BLOCK_BOX_STRADDLE_FVG_AVG` (`BlockReason.BLOCK_BOX_STRADDLE_FVG_AVG` at `core/enums.py:179`)
- `BLOCK_BOX_STRADDLE_SESSION_FVG_AVG` (`BlockReason.BLOCK_BOX_STRADDLE_SESSION_FVG_AVG` at `core/enums.py:180`)
- `BLOCK_BOX_OVERLAP_HIGH` (`BlockReason.BLOCK_BOX_OVERLAP_HIGH` at `core/enums.py:181`)
- `BLOCK_BOX_ENVELOPE_RATIO_HIGH` (`BlockReason.BLOCK_BOX_ENVELOPE_RATIO_HIGH` at `core/enums.py:182`)
- `BLOCK_BOX_STRADDLE_HTF_POC` (`BlockReason.BLOCK_BOX_STRADDLE_HTF_POC` at `core/enums.py:183`)
- `BLOCK_BOX_STRADDLE_VWAP_DONCHIAN_MID` (`BlockReason.BLOCK_BOX_STRADDLE_VWAP_DONCHIAN_MID` at `core/enums.py:184`)
- `BLOCK_BOX_VP_POC_MISPLACED` (`BlockReason.BLOCK_BOX_VP_POC_MISPLACED` at `core/enums.py:185`)
- `BLOCK_BOX_CHANNEL_OVERLAP_LOW` (`BlockReason.BLOCK_BOX_CHANNEL_OVERLAP_LOW` at `core/enums.py:186`)
- `BLOCK_BOX_DONCHIAN_WIDTH_SANITY` (`BlockReason.BLOCK_BOX_DONCHIAN_WIDTH_SANITY` at `core/enums.py:187`)
- `BLOCK_NO_POC_ACCEPTANCE` (`BlockReason.BLOCK_NO_POC_ACCEPTANCE` at `core/enums.py:190`)
- `BLOCK_POC_ALIGNMENT_FAIL` (`BlockReason.BLOCK_POC_ALIGNMENT_FAIL` at `core/enums.py:191`)
- `BLOCK_START_BOX_POSITION` (`BlockReason.BLOCK_START_BOX_POSITION` at `core/enums.py:192`)
- `BLOCK_START_RSI_BAND` (`BlockReason.BLOCK_START_RSI_BAND` at `core/enums.py:193`)
- `BLOCK_START_CONFLUENCE_LOW` (`BlockReason.BLOCK_START_CONFLUENCE_LOW` at `core/enums.py:194`)
- `BLOCK_START_STABILITY_LOW` (`BlockReason.BLOCK_START_STABILITY_LOW` at `core/enums.py:195`)
- `BLOCK_START_PERSISTENCE_FAIL` (`BlockReason.BLOCK_START_PERSISTENCE_FAIL` at `core/enums.py:196`)
- `BLOCK_BASIS_CROSS_PENDING` (`BlockReason.BLOCK_BASIS_CROSS_PENDING` at `core/enums.py:197`)
- `BLOCK_VAH_VAL_POC_PROXIMITY` (`BlockReason.BLOCK_VAH_VAL_POC_PROXIMITY` at `core/enums.py:198`)
- `BLOCK_MRVD_CONFLUENCE_FAIL` (`BlockReason.BLOCK_MRVD_CONFLUENCE_FAIL` at `core/enums.py:199`)
- `BLOCK_MRVD_POC_DRIFT_GUARD` (`BlockReason.BLOCK_MRVD_POC_DRIFT_GUARD` at `core/enums.py:200`)
- `BLOCK_STEP_BELOW_COST` (`BlockReason.BLOCK_STEP_BELOW_COST` at `core/enums.py:203`)
- `BLOCK_STEP_BELOW_EMPIRICAL_COST` (`BlockReason.BLOCK_STEP_BELOW_EMPIRICAL_COST` at `core/enums.py:204`)
- `BLOCK_N_LEVELS_INVALID` (`BlockReason.BLOCK_N_LEVELS_INVALID` at `core/enums.py:205`)
- `BLOCK_CAPACITY_THIN` (`BlockReason.BLOCK_CAPACITY_THIN` at `core/enums.py:206`)
- `BLOCK_EXEC_CONFIRM_START_FAILED` (`BlockReason.BLOCK_EXEC_CONFIRM_START_FAILED` at `core/enums.py:207`)
- `BLOCK_EXEC_CONFIRM_REBUILD_FAILED` (`BlockReason.BLOCK_EXEC_CONFIRM_REBUILD_FAILED` at `core/enums.py:208`)
- `BLOCK_RECLAIM_PENDING` (`BlockReason.BLOCK_RECLAIM_PENDING` at `core/enums.py:211`)
- `BLOCK_RECLAIM_NOT_CONFIRMED` (`BlockReason.BLOCK_RECLAIM_NOT_CONFIRMED` at `core/enums.py:212`)
- `BLOCK_COOLDOWN_ACTIVE` (`BlockReason.BLOCK_COOLDOWN_ACTIVE` at `core/enums.py:213`)
- `BLOCK_MIN_RUNTIME_NOT_MET` (`BlockReason.BLOCK_MIN_RUNTIME_NOT_MET` at `core/enums.py:214`)
- `BLOCK_DRAWDOWN_GUARD` (`BlockReason.BLOCK_DRAWDOWN_GUARD` at `core/enums.py:215`)
- `BLOCK_MAX_STOPS_WINDOW` (`BlockReason.BLOCK_MAX_STOPS_WINDOW` at `core/enums.py:216`)
- `BLOCK_DATA_GAP` (`BlockReason.BLOCK_DATA_GAP` at `core/enums.py:219`)
- `BLOCK_DATA_DUPLICATE_TS` (`BlockReason.BLOCK_DATA_DUPLICATE_TS` at `core/enums.py:220`)
- `BLOCK_DATA_NON_MONOTONIC_TS` (`BlockReason.BLOCK_DATA_NON_MONOTONIC_TS` at `core/enums.py:221`)
- `BLOCK_DATA_MISALIGN` (`BlockReason.BLOCK_DATA_MISALIGN` at `core/enums.py:222`)
- `BLOCK_ZERO_VOL_ANOMALY` (`BlockReason.BLOCK_ZERO_VOL_ANOMALY` at `core/enums.py:223`)
- `BLOCK_STALE_FEATURES` (`BlockReason.BLOCK_STALE_FEATURES` at `core/enums.py:224`)
- `BLOCK_FRESH_OB_COOLOFF` (`BlockReason.BLOCK_FRESH_OB_COOLOFF` at `core/enums.py:227`)
- `BLOCK_FRESH_FVG_COOLOFF` (`BlockReason.BLOCK_FRESH_FVG_COOLOFF` at `core/enums.py:228`)
- `BLOCK_SESSION_FVG_PAUSE` (`BlockReason.BLOCK_SESSION_FVG_PAUSE` at `core/enums.py:229`)
- `BLOCK_INSIDE_SESSION_FVG` (`BlockReason.BLOCK_INSIDE_SESSION_FVG` at `core/enums.py:230`)
- `BLOCK_HVP_EXPANDING` (`BlockReason.BLOCK_HVP_EXPANDING` at `core/enums.py:231`)
- `BLOCK_LIQ_SWEEP_OPPOSITE_STRUCTURE` (`BlockReason.BLOCK_LIQ_SWEEP_OPPOSITE_STRUCTURE` at `core/enums.py:232`)

### StopReason (20)

- `STOP_BREAKOUT_2STRIKE_UP` (`StopReason.STOP_BREAKOUT_2STRIKE_UP` at `core/enums.py:241`)
- `STOP_BREAKOUT_2STRIKE_DN` (`StopReason.STOP_BREAKOUT_2STRIKE_DN` at `core/enums.py:242`)
- `STOP_BREAKOUT_CONFIRM_UP` (`StopReason.STOP_BREAKOUT_CONFIRM_UP` at `core/enums.py:243`)
- `STOP_BREAKOUT_CONFIRM_DN` (`StopReason.STOP_BREAKOUT_CONFIRM_DN` at `core/enums.py:244`)
- `STOP_FAST_MOVE_UP` (`StopReason.STOP_FAST_MOVE_UP` at `core/enums.py:245`)
- `STOP_FAST_MOVE_DN` (`StopReason.STOP_FAST_MOVE_DN` at `core/enums.py:246`)
- `STOP_RANGE_SHIFT` (`StopReason.STOP_RANGE_SHIFT` at `core/enums.py:247`)
- `STOP_FRESH_STRUCTURE` (`StopReason.STOP_FRESH_STRUCTURE` at `core/enums.py:248`)
- `STOP_SQUEEZE_RELEASE_AGAINST` (`StopReason.STOP_SQUEEZE_RELEASE_AGAINST` at `core/enums.py:251`)
- `STOP_CHANNEL_STRONG_BREAK` (`StopReason.STOP_CHANNEL_STRONG_BREAK` at `core/enums.py:252`)
- `STOP_OS_DEV_DIRECTIONAL_FLIP` (`StopReason.STOP_OS_DEV_DIRECTIONAL_FLIP` at `core/enums.py:253`)
- `STOP_META_DRIFT_HARD` (`StopReason.STOP_META_DRIFT_HARD` at `core/enums.py:254`)
- `STOP_LVN_VOID_EXIT_ACCEL` (`StopReason.STOP_LVN_VOID_EXIT_ACCEL` at `core/enums.py:257`)
- `STOP_FVG_VOID_CONFLUENCE` (`StopReason.STOP_FVG_VOID_CONFLUENCE` at `core/enums.py:258`)
- `STOP_LIQUIDITY_SWEEP_BREAK_RETEST` (`StopReason.STOP_LIQUIDITY_SWEEP_BREAK_RETEST` at `core/enums.py:259`)
- `STOP_SESSION_FVG_AGAINST_BIAS` (`StopReason.STOP_SESSION_FVG_AGAINST_BIAS` at `core/enums.py:260`)
- `STOP_MRVD_AVG_BREAK` (`StopReason.STOP_MRVD_AVG_BREAK` at `core/enums.py:261`)
- `STOP_DRAWDOWN_GUARD` (`StopReason.STOP_DRAWDOWN_GUARD` at `core/enums.py:264`)
- `STOP_EXEC_CONFIRM_EXIT_FAILSAFE` (`StopReason.STOP_EXEC_CONFIRM_EXIT_FAILSAFE` at `core/enums.py:265`)
- `STOP_DATA_QUARANTINE` (`StopReason.STOP_DATA_QUARANTINE` at `core/enums.py:266`)

### WarningCode (8)

- `WARN_COST_MODEL_STALE` (`WarningCode.WARN_COST_MODEL_STALE` at `core/enums.py:306`)
- `WARN_CVD_DATA_QUALITY_LOW` (`WarningCode.WARN_CVD_DATA_QUALITY_LOW` at `core/enums.py:307`)
- `WARN_VRVP_UNAVAILABLE_FALLBACK_POC` (`WarningCode.WARN_VRVP_UNAVAILABLE_FALLBACK_POC` at `core/enums.py:308`)
- `WARN_FEATURE_FALLBACK_USED` (`WarningCode.WARN_FEATURE_FALLBACK_USED` at `core/enums.py:309`)
- `WARN_EXEC_POST_ONLY_RETRY_HIGH` (`WarningCode.WARN_EXEC_POST_ONLY_RETRY_HIGH` at `core/enums.py:310`)
- `WARN_EXEC_REPRICE_RATE_HIGH` (`WarningCode.WARN_EXEC_REPRICE_RATE_HIGH` at `core/enums.py:311`)
- `WARN_PLAN_EXPIRES_SOON` (`WarningCode.WARN_PLAN_EXPIRES_SOON` at `core/enums.py:312`)
- `WARN_PARTIAL_DATA_WINDOW` (`WarningCode.WARN_PARTIAL_DATA_WINDOW` at `core/enums.py:313`)

### EventType (61)

- `EVENT_POC_TEST` (`EventType.EVENT_POC_TEST` at `core/enums.py:355`)
- `EVENT_POC_ACCEPTANCE_CROSS` (`EventType.EVENT_POC_ACCEPTANCE_CROSS` at `core/enums.py:356`)
- `EVENT_EXTREME_RETEST_TOP` (`EventType.EVENT_EXTREME_RETEST_TOP` at `core/enums.py:357`)
- `EVENT_EXTREME_RETEST_BOTTOM` (`EventType.EVENT_EXTREME_RETEST_BOTTOM` at `core/enums.py:358`)
- `EVENT_EXT_1386_RETEST_TOP` (`EventType.EVENT_EXT_1386_RETEST_TOP` at `core/enums.py:359`)
- `EVENT_EXT_1386_RETEST_BOTTOM` (`EventType.EVENT_EXT_1386_RETEST_BOTTOM` at `core/enums.py:360`)
- `EVENT_RANGE_HIT_TOP` (`EventType.EVENT_RANGE_HIT_TOP` at `core/enums.py:361`)
- `EVENT_RANGE_HIT_BOTTOM` (`EventType.EVENT_RANGE_HIT_BOTTOM` at `core/enums.py:362`)
- `EVENT_BREAKOUT_BULL` (`EventType.EVENT_BREAKOUT_BULL` at `core/enums.py:365`)
- `EVENT_BREAKOUT_BEAR` (`EventType.EVENT_BREAKOUT_BEAR` at `core/enums.py:366`)
- `EVENT_RECLAIM_CONFIRMED` (`EventType.EVENT_RECLAIM_CONFIRMED` at `core/enums.py:367`)
- `EVENT_CHANNEL_STRONG_BREAK_UP` (`EventType.EVENT_CHANNEL_STRONG_BREAK_UP` at `core/enums.py:368`)
- `EVENT_CHANNEL_STRONG_BREAK_DN` (`EventType.EVENT_CHANNEL_STRONG_BREAK_DN` at `core/enums.py:369`)
- `EVENT_CHANNEL_MIDLINE_TOUCH` (`EventType.EVENT_CHANNEL_MIDLINE_TOUCH` at `core/enums.py:370`)
- `EVENT_DONCHIAN_STRONG_BREAK_UP` (`EventType.EVENT_DONCHIAN_STRONG_BREAK_UP` at `core/enums.py:371`)
- `EVENT_DONCHIAN_STRONG_BREAK_DN` (`EventType.EVENT_DONCHIAN_STRONG_BREAK_DN` at `core/enums.py:372`)
- `EVENT_DRIFT_RETEST_UP` (`EventType.EVENT_DRIFT_RETEST_UP` at `core/enums.py:373`)
- `EVENT_DRIFT_RETEST_DN` (`EventType.EVENT_DRIFT_RETEST_DN` at `core/enums.py:374`)
- `EVENT_SWEEP_WICK_HIGH` (`EventType.EVENT_SWEEP_WICK_HIGH` at `core/enums.py:377`)
- `EVENT_SWEEP_WICK_LOW` (`EventType.EVENT_SWEEP_WICK_LOW` at `core/enums.py:378`)
- `EVENT_SWEEP_BREAK_RETEST_HIGH` (`EventType.EVENT_SWEEP_BREAK_RETEST_HIGH` at `core/enums.py:379`)
- `EVENT_SWEEP_BREAK_RETEST_LOW` (`EventType.EVENT_SWEEP_BREAK_RETEST_LOW` at `core/enums.py:380`)
- `EVENT_SESSION_HIGH_SWEEP` (`EventType.EVENT_SESSION_HIGH_SWEEP` at `core/enums.py:381`)
- `EVENT_SESSION_LOW_SWEEP` (`EventType.EVENT_SESSION_LOW_SWEEP` at `core/enums.py:382`)
- `EVENT_FVG_NEW_BULL` (`EventType.EVENT_FVG_NEW_BULL` at `core/enums.py:385`)
- `EVENT_FVG_NEW_BEAR` (`EventType.EVENT_FVG_NEW_BEAR` at `core/enums.py:386`)
- `EVENT_FVG_MITIGATED_BULL` (`EventType.EVENT_FVG_MITIGATED_BULL` at `core/enums.py:387`)
- `EVENT_FVG_MITIGATED_BEAR` (`EventType.EVENT_FVG_MITIGATED_BEAR` at `core/enums.py:388`)
- `EVENT_IMFVG_AVG_TAG_BULL` (`EventType.EVENT_IMFVG_AVG_TAG_BULL` at `core/enums.py:389`)
- `EVENT_IMFVG_AVG_TAG_BEAR` (`EventType.EVENT_IMFVG_AVG_TAG_BEAR` at `core/enums.py:390`)
- `EVENT_SESSION_FVG_NEW` (`EventType.EVENT_SESSION_FVG_NEW` at `core/enums.py:391`)
- `EVENT_SESSION_FVG_MITIGATED` (`EventType.EVENT_SESSION_FVG_MITIGATED` at `core/enums.py:392`)
- `EVENT_OB_NEW_BULL` (`EventType.EVENT_OB_NEW_BULL` at `core/enums.py:393`)
- `EVENT_OB_NEW_BEAR` (`EventType.EVENT_OB_NEW_BEAR` at `core/enums.py:394`)
- `EVENT_OB_TAGGED_BULL` (`EventType.EVENT_OB_TAGGED_BULL` at `core/enums.py:395`)
- `EVENT_OB_TAGGED_BEAR` (`EventType.EVENT_OB_TAGGED_BEAR` at `core/enums.py:396`)
- `EVENT_VRVP_POC_SHIFT` (`EventType.EVENT_VRVP_POC_SHIFT` at `core/enums.py:399`)
- `EVENT_MICRO_POC_SHIFT` (`EventType.EVENT_MICRO_POC_SHIFT` at `core/enums.py:400`)
- `EVENT_HVN_TOUCH` (`EventType.EVENT_HVN_TOUCH` at `core/enums.py:401`)
- `EVENT_LVN_TOUCH` (`EventType.EVENT_LVN_TOUCH` at `core/enums.py:402`)
- `EVENT_LVN_VOID_EXIT` (`EventType.EVENT_LVN_VOID_EXIT` at `core/enums.py:403`)
- `EVENT_FVG_POC_TAG` (`EventType.EVENT_FVG_POC_TAG` at `core/enums.py:404`)
- `EVENT_CVD_BULL_DIV` (`EventType.EVENT_CVD_BULL_DIV` at `core/enums.py:407`)
- `EVENT_CVD_BEAR_DIV` (`EventType.EVENT_CVD_BEAR_DIV` at `core/enums.py:408`)
- `EVENT_CVD_BOS_UP` (`EventType.EVENT_CVD_BOS_UP` at `core/enums.py:409`)
- `EVENT_CVD_BOS_DN` (`EventType.EVENT_CVD_BOS_DN` at `core/enums.py:410`)
- `EVENT_CVD_SPIKE_POS` (`EventType.EVENT_CVD_SPIKE_POS` at `core/enums.py:411`)
- `EVENT_CVD_SPIKE_NEG` (`EventType.EVENT_CVD_SPIKE_NEG` at `core/enums.py:412`)
- `EVENT_PASSIVE_ABSORPTION_UP` (`EventType.EVENT_PASSIVE_ABSORPTION_UP` at `core/enums.py:413`)
- `EVENT_PASSIVE_ABSORPTION_DN` (`EventType.EVENT_PASSIVE_ABSORPTION_DN` at `core/enums.py:414`)
- `EVENT_META_DRIFT_SOFT` (`EventType.EVENT_META_DRIFT_SOFT` at `core/enums.py:415`)
- `EVENT_META_DRIFT_HARD` (`EventType.EVENT_META_DRIFT_HARD` at `core/enums.py:416`)
- `EVENT_BBWP_EXTREME` (`EventType.EVENT_BBWP_EXTREME` at `core/enums.py:417`)
- `EVENT_SQUEEZE_RELEASE_UP` (`EventType.EVENT_SQUEEZE_RELEASE_UP` at `core/enums.py:418`)
- `EVENT_SQUEEZE_RELEASE_DN` (`EventType.EVENT_SQUEEZE_RELEASE_DN` at `core/enums.py:419`)
- `EVENT_SPREAD_SPIKE` (`EventType.EVENT_SPREAD_SPIKE` at `core/enums.py:422`)
- `EVENT_DEPTH_THIN` (`EventType.EVENT_DEPTH_THIN` at `core/enums.py:423`)
- `EVENT_JUMP_DETECTED` (`EventType.EVENT_JUMP_DETECTED` at `core/enums.py:424`)
- `EVENT_POST_ONLY_REJECT_BURST` (`EventType.EVENT_POST_ONLY_REJECT_BURST` at `core/enums.py:425`)
- `EVENT_DATA_GAP_DETECTED` (`EventType.EVENT_DATA_GAP_DETECTED` at `core/enums.py:426`)
- `EVENT_DATA_MISALIGN_DETECTED` (`EventType.EVENT_DATA_MISALIGN_DETECTED` at `core/enums.py:427`)

### ModuleName (57)

- `data_loader` (`ModuleName.DATA_LOADER` at `core/enums.py:68`)
- `data_quality_monitor` (`ModuleName.DATA_QUALITY_MONITOR` at `core/enums.py:69`)
- `mtf_merge_integrity` (`ModuleName.MTF_MERGE_INTEGRITY` at `core/enums.py:70`)
- `feature_pipeline` (`ModuleName.FEATURE_PIPELINE` at `core/enums.py:71`)
- `adx_gate` (`ModuleName.ADX_GATE` at `core/enums.py:74`)
- `bbw_quietness_gate` (`ModuleName.BBW_QUIETNESS_GATE` at `core/enums.py:75`)
- `ema_compression_gate` (`ModuleName.EMA_COMPRESSION_GATE` at `core/enums.py:76`)
- `rvol_gate` (`ModuleName.RVOL_GATE` at `core/enums.py:77`)
- `context_7d_gate` (`ModuleName.CONTEXT_7D_GATE` at `core/enums.py:78`)
- `breakout_fresh_block` (`ModuleName.BREAKOUT_FRESH_BLOCK` at `core/enums.py:79`)
- `breakout_reclaim_timer` (`ModuleName.BREAKOUT_RECLAIM_TIMER` at `core/enums.py:80`)
- `range_di_os_dev` (`ModuleName.RANGE_DI_OS_DEV` at `core/enums.py:81`)
- `band_slope_veto` (`ModuleName.BAND_SLOPE_VETO` at `core/enums.py:82`)
- `drift_slope_veto` (`ModuleName.DRIFT_SLOPE_VETO` at `core/enums.py:83`)
- `excursion_asymmetry_veto` (`ModuleName.EXCURSION_ASYMMETRY_VETO` at `core/enums.py:84`)
- `meta_drift_guard` (`ModuleName.META_DRIFT_GUARD` at `core/enums.py:85`)
- `bbwp_mtf_gate` (`ModuleName.BBWP_MTF_GATE` at `core/enums.py:86`)
- `squeeze_state_gate` (`ModuleName.SQUEEZE_STATE_GATE` at `core/enums.py:87`)
- `volatility_policy_adapter` (`ModuleName.VOLATILITY_POLICY_ADAPTER` at `core/enums.py:88`)
- `box_builder` (`ModuleName.BOX_BUILDER` at `core/enums.py:91`)
- `box_straddle_veto` (`ModuleName.BOX_STRADDLE_VETO` at `core/enums.py:92`)
- `vrvp` (`ModuleName.VRVP` at `core/enums.py:93`)
- `micro_vap` (`ModuleName.MICRO_VAP` at `core/enums.py:94`)
- `mrvd` (`ModuleName.MRVD` at `core/enums.py:95`)
- `basis_pivots` (`ModuleName.BASIS_PIVOTS` at `core/enums.py:96`)
- `donchian` (`ModuleName.DONCHIAN` at `core/enums.py:97`)
- `channel_module` (`ModuleName.CHANNEL_MODULE` at `core/enums.py:98`)
- `ob_module` (`ModuleName.OB_MODULE` at `core/enums.py:101`)
- `fvg_module` (`ModuleName.FVG_MODULE` at `core/enums.py:102`)
- `imfvg_module` (`ModuleName.IMFVG_MODULE` at `core/enums.py:103`)
- `session_fvg` (`ModuleName.SESSION_FVG` at `core/enums.py:104`)
- `fvg_positioning_avg` (`ModuleName.FVG_POSITIONING_AVG` at `core/enums.py:105`)
- `fvg_vp` (`ModuleName.FVG_VP` at `core/enums.py:106`)
- `liquidity_sweeps` (`ModuleName.LIQUIDITY_SWEEPS` at `core/enums.py:107`)
- `poc_acceptance_gate` (`ModuleName.POC_ACCEPTANCE_GATE` at `core/enums.py:110`)
- `start_stability` (`ModuleName.START_STABILITY` at `core/enums.py:111`)
- `confluence_aggregator` (`ModuleName.CONFLUENCE_AGGREGATOR` at `core/enums.py:112`)
- `cost_model` (`ModuleName.COST_MODEL` at `core/enums.py:113`)
- `empirical_cost_calibrator` (`ModuleName.EMPIRICAL_COST_CALIBRATOR` at `core/enums.py:114`)
- `n_level_selection` (`ModuleName.N_LEVEL_SELECTION` at `core/enums.py:115`)
- `target_selector` (`ModuleName.TARGET_SELECTOR` at `core/enums.py:116`)
- `sl_selector` (`ModuleName.SL_SELECTOR` at `core/enums.py:117`)
- `stop_framework` (`ModuleName.STOP_FRAMEWORK` at `core/enums.py:120`)
- `reclaim_discipline` (`ModuleName.RECLAIM_DISCIPLINE` at `core/enums.py:121`)
- `protections` (`ModuleName.PROTECTIONS` at `core/enums.py:122`)
- `replan_policy` (`ModuleName.REPLAN_POLICY` at `core/enums.py:123`)
- `plan_atomic_handoff` (`ModuleName.PLAN_ATOMIC_HANDOFF` at `core/enums.py:124`)
- `executor` (`ModuleName.EXECUTOR` at `core/enums.py:127`)
- `capacity_guard` (`ModuleName.CAPACITY_GUARD` at `core/enums.py:128`)
- `confirm_entry_hook` (`ModuleName.CONFIRM_ENTRY_HOOK` at `core/enums.py:129`)
- `confirm_rebuild_hook` (`ModuleName.CONFIRM_REBUILD_HOOK` at `core/enums.py:130`)
- `confirm_exit_hook` (`ModuleName.CONFIRM_EXIT_HOOK` at `core/enums.py:131`)
- `maker_first_execution` (`ModuleName.MAKER_FIRST_EXECUTION` at `core/enums.py:132`)
- `reconcile_engine` (`ModuleName.RECONCILE_ENGINE` at `core/enums.py:133`)
- `fill_dedupe_guard` (`ModuleName.FILL_DEDUPE_GUARD` at `core/enums.py:134`)
- `cvd_module` (`ModuleName.CVD_MODULE` at `core/enums.py:137`)
- `hvp_gate` (`ModuleName.HVP_GATE` at `core/enums.py:138`)

### Severity (4)

- `hard` (`Severity.HARD` at `core/enums.py:35`)
- `soft` (`Severity.SOFT` at `core/enums.py:36`)
- `advisory` (`Severity.ADVISORY` at `core/enums.py:37`)
- `info` (`Severity.INFO` at `core/enums.py:38`)

### MaterialityClass (4)

- `noop` (`MaterialityClass.NOOP` at `core/enums.py:52`)
- `soft` (`MaterialityClass.SOFT` at `core/enums.py:53`)
- `material` (`MaterialityClass.MATERIAL` at `core/enums.py:54`)
- `hardstop` (`MaterialityClass.HARDSTOP` at `core/enums.py:55`)

## 3) Runtime Wiring Map for Canonical Codes

- Criterion: A code is considered wired when referenced in runtime source under strategy/helpers/scripts.
- Runtime files scanned for wiring: `34`

### BlockReason

- `BLOCK_ADX_HIGH` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:1739`)
- `BLOCK_BBW_EXPANDING` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:1741`)
- `BLOCK_EMA_DIST` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:1743`)
- `BLOCK_RVOL_SPIKE` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:1745`)
- `BLOCK_7D_EXTREME_CONTEXT` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:1747`)
- `BLOCK_FRESH_BREAKOUT` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:581`)
- `BLOCK_BREAKOUT_RECLAIM_PENDING` -> REGISTRY_ONLY
- `BLOCK_BREAKOUT_CONFIRM_UP` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:1659`)
- `BLOCK_BREAKOUT_CONFIRM_DN` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:1664`)
- `BLOCK_MIN_RANGE_LEN_NOT_MET` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:1640`)
- `BLOCK_OS_DEV_DIRECTIONAL` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:7770`)
- `BLOCK_OS_DEV_NEUTRAL_PERSISTENCE` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:7772`)
- `BLOCK_BAND_SLOPE_HIGH` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:7732`)
- `BLOCK_DRIFT_SLOPE_HIGH` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:7736`)
- `BLOCK_EXCURSION_ASYMMETRY` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:7734`)
- `BLOCK_META_DRIFT_SOFT` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:7765`)
- `BLOCK_BBWP_HIGH` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:7741`)
- `COOLOFF_BBWP_EXTREME` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:7745`)
- `BLOCK_FUNDING_FILTER` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:7755`)
- `BLOCK_SQUEEZE_RELEASE_AGAINST_BIAS` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:1327`)
- `BLOCK_VOL_BUCKET_UNSTABLE` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:8028`)
- `BLOCK_BOX_WIDTH_TOO_NARROW` -> REGISTRY_ONLY
- `BLOCK_BOX_WIDTH_TOO_WIDE` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:6617`)
- `BLOCK_BOX_STRADDLE_BREAKOUT_LEVEL` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:7174`)
- `BLOCK_BOX_STRADDLE_OB_EDGE` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2948`)
- `BLOCK_BOX_STRADDLE_FVG_EDGE` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:1261`)
- `BLOCK_BOX_STRADDLE_FVG_AVG` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:1263`)
- `BLOCK_BOX_STRADDLE_SESSION_FVG_AVG` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:1268`)
- `BLOCK_BOX_OVERLAP_HIGH` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:6620`)
- `BLOCK_BOX_ENVELOPE_RATIO_HIGH` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:6737`)
- `BLOCK_BOX_STRADDLE_HTF_POC` -> REGISTRY_ONLY
- `BLOCK_BOX_STRADDLE_VWAP_DONCHIAN_MID` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:7185`)
- `BLOCK_BOX_VP_POC_MISPLACED` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:7178`)
- `BLOCK_BOX_CHANNEL_OVERLAP_LOW` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:6723`)
- `BLOCK_BOX_DONCHIAN_WIDTH_SANITY` -> REGISTRY_ONLY
- `BLOCK_NO_POC_ACCEPTANCE` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:7787`)
- `BLOCK_POC_ALIGNMENT_FAIL` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:1511`)
- `BLOCK_START_BOX_POSITION` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:7783`)
- `BLOCK_START_RSI_BAND` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:7785`)
- `BLOCK_START_CONFLUENCE_LOW` -> REGISTRY_ONLY
- `BLOCK_START_STABILITY_LOW` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:8030`)
- `BLOCK_START_PERSISTENCE_FAIL` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:7738`)
- `BLOCK_BASIS_CROSS_PENDING` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:7793`)
- `BLOCK_VAH_VAL_POC_PROXIMITY` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:7791`)
- `BLOCK_MRVD_CONFLUENCE_FAIL` -> REGISTRY_ONLY
- `BLOCK_MRVD_POC_DRIFT_GUARD` -> REGISTRY_ONLY
- `BLOCK_STEP_BELOW_COST` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:6844`)
- `BLOCK_STEP_BELOW_EMPIRICAL_COST` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:6842`)
- `BLOCK_N_LEVELS_INVALID` -> REGISTRY_ONLY
- `BLOCK_CAPACITY_THIN` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:7763`, `execution/capacity_guard.py:122`, `freqtrade/user_data/scripts/grid_executor_v1.py:1341`)
- `BLOCK_EXEC_CONFIRM_START_FAILED` -> REGISTRY_ONLY
- `BLOCK_EXEC_CONFIRM_REBUILD_FAILED` -> REGISTRY_ONLY
- `BLOCK_RECLAIM_PENDING` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:8055`)
- `BLOCK_RECLAIM_NOT_CONFIRMED` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:5926`)
- `BLOCK_COOLDOWN_ACTIVE` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:8057`)
- `BLOCK_MIN_RUNTIME_NOT_MET` -> REGISTRY_ONLY
- `BLOCK_DRAWDOWN_GUARD` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2920`)
- `BLOCK_MAX_STOPS_WINDOW` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2921`)
- `BLOCK_DATA_GAP` -> WIRED (`data/data_quality_assessor.py:47`, `freqtrade/user_data/strategies/GridBrainV1.py:1756`)
- `BLOCK_DATA_DUPLICATE_TS` -> REGISTRY_ONLY
- `BLOCK_DATA_NON_MONOTONIC_TS` -> REGISTRY_ONLY
- `BLOCK_DATA_MISALIGN` -> WIRED (`data/data_quality_assessor.py:34`, `freqtrade/user_data/strategies/GridBrainV1.py:1761`)
- `BLOCK_ZERO_VOL_ANOMALY` -> WIRED (`data/data_quality_assessor.py:63`)
- `BLOCK_STALE_FEATURES` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:7767`)
- `BLOCK_FRESH_OB_COOLOFF` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2947`)
- `BLOCK_FRESH_FVG_COOLOFF` -> REGISTRY_ONLY
- `BLOCK_SESSION_FVG_PAUSE` -> REGISTRY_ONLY
- `BLOCK_INSIDE_SESSION_FVG` -> REGISTRY_ONLY
- `BLOCK_HVP_EXPANDING` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:7757`)
- `BLOCK_LIQ_SWEEP_OPPOSITE_STRUCTURE` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:7761`)

### StopReason

- `STOP_BREAKOUT_2STRIKE_UP` -> REGISTRY_ONLY
- `STOP_BREAKOUT_2STRIKE_DN` -> REGISTRY_ONLY
- `STOP_BREAKOUT_CONFIRM_UP` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:1657`)
- `STOP_BREAKOUT_CONFIRM_DN` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:1662`)
- `STOP_FAST_MOVE_UP` -> REGISTRY_ONLY
- `STOP_FAST_MOVE_DN` -> REGISTRY_ONLY
- `STOP_RANGE_SHIFT` -> REGISTRY_ONLY
- `STOP_FRESH_STRUCTURE` -> REGISTRY_ONLY
- `STOP_SQUEEZE_RELEASE_AGAINST` -> REGISTRY_ONLY
- `STOP_CHANNEL_STRONG_BREAK` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2928`)
- `STOP_OS_DEV_DIRECTIONAL_FLIP` -> REGISTRY_ONLY
- `STOP_META_DRIFT_HARD` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:519`)
- `STOP_LVN_VOID_EXIT_ACCEL` -> REGISTRY_ONLY
- `STOP_FVG_VOID_CONFLUENCE` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:7689`)
- `STOP_LIQUIDITY_SWEEP_BREAK_RETEST` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2943`)
- `STOP_SESSION_FVG_AGAINST_BIAS` -> REGISTRY_ONLY
- `STOP_MRVD_AVG_BREAK` -> REGISTRY_ONLY
- `STOP_DRAWDOWN_GUARD` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2922`)
- `STOP_EXEC_CONFIRM_EXIT_FAILSAFE` -> WIRED (`freqtrade/user_data/scripts/grid_executor_v1.py:2498`)
- `STOP_DATA_QUARANTINE` -> REGISTRY_ONLY

### WarningCode

- `WARN_COST_MODEL_STALE` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:5032`)
- `WARN_CVD_DATA_QUALITY_LOW` -> REGISTRY_ONLY
- `WARN_VRVP_UNAVAILABLE_FALLBACK_POC` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:8083`)
- `WARN_FEATURE_FALLBACK_USED` -> REGISTRY_ONLY
- `WARN_EXEC_POST_ONLY_RETRY_HIGH` -> WIRED (`freqtrade/user_data/scripts/grid_executor_v1.py:1121`)
- `WARN_EXEC_REPRICE_RATE_HIGH` -> REGISTRY_ONLY
- `WARN_PLAN_EXPIRES_SOON` -> REGISTRY_ONLY
- `WARN_PARTIAL_DATA_WINDOW` -> REGISTRY_ONLY

### EventType

- `EVENT_POC_TEST` -> REGISTRY_ONLY
- `EVENT_POC_ACCEPTANCE_CROSS` -> REGISTRY_ONLY
- `EVENT_EXTREME_RETEST_TOP` -> REGISTRY_ONLY
- `EVENT_EXTREME_RETEST_BOTTOM` -> REGISTRY_ONLY
- `EVENT_EXT_1386_RETEST_TOP` -> REGISTRY_ONLY
- `EVENT_EXT_1386_RETEST_BOTTOM` -> REGISTRY_ONLY
- `EVENT_RANGE_HIT_TOP` -> REGISTRY_ONLY
- `EVENT_RANGE_HIT_BOTTOM` -> REGISTRY_ONLY
- `EVENT_BREAKOUT_BULL` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:8203`)
- `EVENT_BREAKOUT_BEAR` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:8205`)
- `EVENT_RECLAIM_CONFIRMED` -> REGISTRY_ONLY
- `EVENT_CHANNEL_STRONG_BREAK_UP` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2894`)
- `EVENT_CHANNEL_STRONG_BREAK_DN` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2895`)
- `EVENT_CHANNEL_MIDLINE_TOUCH` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2931`)
- `EVENT_DONCHIAN_STRONG_BREAK_UP` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2896`)
- `EVENT_DONCHIAN_STRONG_BREAK_DN` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2897`)
- `EVENT_DRIFT_RETEST_UP` -> REGISTRY_ONLY
- `EVENT_DRIFT_RETEST_DN` -> REGISTRY_ONLY
- `EVENT_SWEEP_WICK_HIGH` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2937`, `planner/structure/liquidity_sweeps.py:304`)
- `EVENT_SWEEP_WICK_LOW` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2938`, `planner/structure/liquidity_sweeps.py:306`)
- `EVENT_SWEEP_BREAK_RETEST_HIGH` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2898`, `planner/structure/liquidity_sweeps.py:308`)
- `EVENT_SWEEP_BREAK_RETEST_LOW` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2899`, `planner/structure/liquidity_sweeps.py:310`)
- `EVENT_SESSION_HIGH_SWEEP` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2941`)
- `EVENT_SESSION_LOW_SWEEP` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2942`)
- `EVENT_FVG_NEW_BULL` -> REGISTRY_ONLY
- `EVENT_FVG_NEW_BEAR` -> REGISTRY_ONLY
- `EVENT_FVG_MITIGATED_BULL` -> REGISTRY_ONLY
- `EVENT_FVG_MITIGATED_BEAR` -> REGISTRY_ONLY
- `EVENT_IMFVG_AVG_TAG_BULL` -> REGISTRY_ONLY
- `EVENT_IMFVG_AVG_TAG_BEAR` -> REGISTRY_ONLY
- `EVENT_SESSION_FVG_NEW` -> REGISTRY_ONLY
- `EVENT_SESSION_FVG_MITIGATED` -> REGISTRY_ONLY
- `EVENT_OB_NEW_BULL` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2949`)
- `EVENT_OB_NEW_BEAR` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2950`)
- `EVENT_OB_TAGGED_BULL` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2951`)
- `EVENT_OB_TAGGED_BEAR` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2952`)
- `EVENT_VRVP_POC_SHIFT` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2960`)
- `EVENT_MICRO_POC_SHIFT` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2961`)
- `EVENT_HVN_TOUCH` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2962`)
- `EVENT_LVN_TOUCH` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2963`)
- `EVENT_LVN_VOID_EXIT` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2964`)
- `EVENT_FVG_POC_TAG` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2956`)
- `EVENT_CVD_BULL_DIV` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:8243`)
- `EVENT_CVD_BEAR_DIV` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:8245`)
- `EVENT_CVD_BOS_UP` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:8247`)
- `EVENT_CVD_BOS_DN` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:8249`)
- `EVENT_CVD_SPIKE_POS` -> REGISTRY_ONLY
- `EVENT_CVD_SPIKE_NEG` -> REGISTRY_ONLY
- `EVENT_PASSIVE_ABSORPTION_UP` -> REGISTRY_ONLY
- `EVENT_PASSIVE_ABSORPTION_DN` -> REGISTRY_ONLY
- `EVENT_META_DRIFT_SOFT` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2905`)
- `EVENT_META_DRIFT_HARD` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2893`)
- `EVENT_BBWP_EXTREME` -> REGISTRY_ONLY
- `EVENT_SQUEEZE_RELEASE_UP` -> REGISTRY_ONLY
- `EVENT_SQUEEZE_RELEASE_DN` -> REGISTRY_ONLY
- `EVENT_SPREAD_SPIKE` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2906`, `freqtrade/user_data/scripts/grid_executor_v1.py:1250`)
- `EVENT_DEPTH_THIN` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2907`, `freqtrade/user_data/scripts/grid_executor_v1.py:1256`)
- `EVENT_JUMP_DETECTED` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2908`, `freqtrade/user_data/scripts/grid_executor_v1.py:1262`)
- `EVENT_POST_ONLY_REJECT_BURST` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2909`, `freqtrade/user_data/scripts/grid_executor_v1.py:1124`)
- `EVENT_DATA_GAP_DETECTED` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2900`)
- `EVENT_DATA_MISALIGN_DETECTED` -> WIRED (`freqtrade/user_data/strategies/GridBrainV1.py:2901`)

## 4) Python API Inventory (Classes, Methods, Functions)

### `analytics/__init__.py`

- Top-level functions: 0
- Classes: 0

### `analytics/execution_cost_calibrator.py`

- Top-level functions: 0
- Classes: 1
  - `EmpiricalCostCalibrator` (L9): attrs=0, methods=4
    - methods: `__init__` (L14), `_samples` (L20), `observe` (L27), `snapshot` (L79)

### `core/atomic_json.py`

- Top-level functions: 3
  - `_fsync_parent_dir` (L12), `write_json_atomic` (L32), `read_json_object` (L50)
- Classes: 0

### `core/enums.py`

- Top-level functions: 5
  - `is_canonical_code` (L474), `all_canonical_codes` (L479), `parse_canonical_code` (L484), `category_of_code` (L495), `ensure_canonical_codes` (L506)
- Classes: 14
  - `StrEnum` (L18): attrs=0, methods=3
    - methods: `__str__` (L21), `values` (L25), `has_value` (L29)
  - `Severity` (L34): attrs=4, methods=0
    - attrs: `HARD` (L35), `SOFT` (L36), `ADVISORY` (L37), `INFO` (L38)
  - `ActionContext` (L42): attrs=5, methods=0
    - attrs: `START` (L43), `HOLD` (L44), `STOP` (L45), `REBUILD` (L46), `NOOP` (L47)
  - `MaterialityClass` (L51): attrs=4, methods=0
    - attrs: `NOOP` (L52), `SOFT` (L53), `MATERIAL` (L54), `HARDSTOP` (L55)
  - `PlannerHealthState` (L59): attrs=3, methods=0
    - attrs: `OK` (L60), `DEGRADED` (L61), `QUARANTINE` (L62)
  - `ModuleName` (L66): attrs=57, methods=0
    - attrs: `DATA_LOADER` (L68), `DATA_QUALITY_MONITOR` (L69), `MTF_MERGE_INTEGRITY` (L70), `FEATURE_PIPELINE` (L71), `ADX_GATE` (L74), `BBW_QUIETNESS_GATE` (L75), `EMA_COMPRESSION_GATE` (L76), `RVOL_GATE` (L77), `CONTEXT_7D_GATE` (L78), `BREAKOUT_FRESH_BLOCK` (L79), `BREAKOUT_RECLAIM_TIMER` (L80), `RANGE_DI_OS_DEV` (L81), `BAND_SLOPE_VETO` (L82), `DRIFT_SLOPE_VETO` (L83), `EXCURSION_ASYMMETRY_VETO` (L84), `META_DRIFT_GUARD` (L85), `BBWP_MTF_GATE` (L86), `SQUEEZE_STATE_GATE` (L87), `VOLATILITY_POLICY_ADAPTER` (L88), `BOX_BUILDER` (L91), `BOX_STRADDLE_VETO` (L92), `VRVP` (L93), `MICRO_VAP` (L94), `MRVD` (L95), `BASIS_PIVOTS` (L96), `DONCHIAN` (L97), `CHANNEL_MODULE` (L98), `OB_MODULE` (L101), `FVG_MODULE` (L102), `IMFVG_MODULE` (L103), `SESSION_FVG` (L104), `FVG_POSITIONING_AVG` (L105), `FVG_VP` (L106), `LIQUIDITY_SWEEPS` (L107), `POC_ACCEPTANCE_GATE` (L110), `START_STABILITY` (L111), `CONFLUENCE_AGGREGATOR` (L112), `COST_MODEL` (L113), `EMPIRICAL_COST_CALIBRATOR` (L114), `N_LEVEL_SELECTION` (L115), `TARGET_SELECTOR` (L116), `SL_SELECTOR` (L117), `STOP_FRAMEWORK` (L120), `RECLAIM_DISCIPLINE` (L121), `PROTECTIONS` (L122), `REPLAN_POLICY` (L123), `PLAN_ATOMIC_HANDOFF` (L124), `EXECUTOR` (L127), `CAPACITY_GUARD` (L128), `CONFIRM_ENTRY_HOOK` (L129), `CONFIRM_REBUILD_HOOK` (L130), `CONFIRM_EXIT_HOOK` (L131), `MAKER_FIRST_EXECUTION` (L132), `RECONCILE_ENGINE` (L133), `FILL_DEDUPE_GUARD` (L134), `CVD_MODULE` (L137), `HVP_GATE` (L138)
  - `BlockReason` (L145): attrs=70, methods=0
    - attrs: `BLOCK_ADX_HIGH` (L147), `BLOCK_BBW_EXPANDING` (L148), `BLOCK_EMA_DIST` (L149), `BLOCK_RVOL_SPIKE` (L150), `BLOCK_7D_EXTREME_CONTEXT` (L151), `BLOCK_FRESH_BREAKOUT` (L154), `BLOCK_BREAKOUT_RECLAIM_PENDING` (L155), `BLOCK_BREAKOUT_CONFIRM_UP` (L156), `BLOCK_BREAKOUT_CONFIRM_DN` (L157), `BLOCK_MIN_RANGE_LEN_NOT_MET` (L158), `BLOCK_OS_DEV_DIRECTIONAL` (L159), `BLOCK_OS_DEV_NEUTRAL_PERSISTENCE` (L160), `BLOCK_BAND_SLOPE_HIGH` (L161), `BLOCK_DRIFT_SLOPE_HIGH` (L162), `BLOCK_EXCURSION_ASYMMETRY` (L163), `BLOCK_META_DRIFT_SOFT` (L164), `BLOCK_BBWP_HIGH` (L167), `COOLOFF_BBWP_EXTREME` (L168), `BLOCK_FUNDING_FILTER` (L169), `BLOCK_SQUEEZE_RELEASE_AGAINST_BIAS` (L170), `BLOCK_VOL_BUCKET_UNSTABLE` (L171), `BLOCK_BOX_WIDTH_TOO_NARROW` (L174), `BLOCK_BOX_WIDTH_TOO_WIDE` (L175), `BLOCK_BOX_STRADDLE_BREAKOUT_LEVEL` (L176), `BLOCK_BOX_STRADDLE_OB_EDGE` (L177), `BLOCK_BOX_STRADDLE_FVG_EDGE` (L178), `BLOCK_BOX_STRADDLE_FVG_AVG` (L179), `BLOCK_BOX_STRADDLE_SESSION_FVG_AVG` (L180), `BLOCK_BOX_OVERLAP_HIGH` (L181), `BLOCK_BOX_ENVELOPE_RATIO_HIGH` (L182), `BLOCK_BOX_STRADDLE_HTF_POC` (L183), `BLOCK_BOX_STRADDLE_VWAP_DONCHIAN_MID` (L184), `BLOCK_BOX_VP_POC_MISPLACED` (L185), `BLOCK_BOX_CHANNEL_OVERLAP_LOW` (L186), `BLOCK_BOX_DONCHIAN_WIDTH_SANITY` (L187), `BLOCK_NO_POC_ACCEPTANCE` (L190), `BLOCK_POC_ALIGNMENT_FAIL` (L191), `BLOCK_START_BOX_POSITION` (L192), `BLOCK_START_RSI_BAND` (L193), `BLOCK_START_CONFLUENCE_LOW` (L194), `BLOCK_START_STABILITY_LOW` (L195), `BLOCK_START_PERSISTENCE_FAIL` (L196), `BLOCK_BASIS_CROSS_PENDING` (L197), `BLOCK_VAH_VAL_POC_PROXIMITY` (L198), `BLOCK_MRVD_CONFLUENCE_FAIL` (L199), `BLOCK_MRVD_POC_DRIFT_GUARD` (L200), `BLOCK_STEP_BELOW_COST` (L203), `BLOCK_STEP_BELOW_EMPIRICAL_COST` (L204), `BLOCK_N_LEVELS_INVALID` (L205), `BLOCK_CAPACITY_THIN` (L206), `BLOCK_EXEC_CONFIRM_START_FAILED` (L207), `BLOCK_EXEC_CONFIRM_REBUILD_FAILED` (L208), `BLOCK_RECLAIM_PENDING` (L211), `BLOCK_RECLAIM_NOT_CONFIRMED` (L212), `BLOCK_COOLDOWN_ACTIVE` (L213), `BLOCK_MIN_RUNTIME_NOT_MET` (L214), `BLOCK_DRAWDOWN_GUARD` (L215), `BLOCK_MAX_STOPS_WINDOW` (L216), `BLOCK_DATA_GAP` (L219), `BLOCK_DATA_DUPLICATE_TS` (L220), `BLOCK_DATA_NON_MONOTONIC_TS` (L221), `BLOCK_DATA_MISALIGN` (L222), `BLOCK_ZERO_VOL_ANOMALY` (L223), `BLOCK_STALE_FEATURES` (L224), `BLOCK_FRESH_OB_COOLOFF` (L227), `BLOCK_FRESH_FVG_COOLOFF` (L228), `BLOCK_SESSION_FVG_PAUSE` (L229), `BLOCK_INSIDE_SESSION_FVG` (L230), `BLOCK_HVP_EXPANDING` (L231), `BLOCK_LIQ_SWEEP_OPPOSITE_STRUCTURE` (L232)
  - `StopReason` (L239): attrs=20, methods=0
    - attrs: `STOP_BREAKOUT_2STRIKE_UP` (L241), `STOP_BREAKOUT_2STRIKE_DN` (L242), `STOP_BREAKOUT_CONFIRM_UP` (L243), `STOP_BREAKOUT_CONFIRM_DN` (L244), `STOP_FAST_MOVE_UP` (L245), `STOP_FAST_MOVE_DN` (L246), `STOP_RANGE_SHIFT` (L247), `STOP_FRESH_STRUCTURE` (L248), `STOP_SQUEEZE_RELEASE_AGAINST` (L251), `STOP_CHANNEL_STRONG_BREAK` (L252), `STOP_OS_DEV_DIRECTIONAL_FLIP` (L253), `STOP_META_DRIFT_HARD` (L254), `STOP_LVN_VOID_EXIT_ACCEL` (L257), `STOP_FVG_VOID_CONFLUENCE` (L258), `STOP_LIQUIDITY_SWEEP_BREAK_RETEST` (L259), `STOP_SESSION_FVG_AGAINST_BIAS` (L260), `STOP_MRVD_AVG_BREAK` (L261), `STOP_DRAWDOWN_GUARD` (L264), `STOP_EXEC_CONFIRM_EXIT_FAILSAFE` (L265), `STOP_DATA_QUARANTINE` (L266)
  - `ReplanReason` (L273): attrs=9, methods=0
    - attrs: `REPLAN_NOOP_MINOR_DELTA` (L275), `REPLAN_SOFT_ADJUST_ONLY` (L276), `REPLAN_MATERIAL_BOX_CHANGE` (L277), `REPLAN_MATERIAL_GRID_CHANGE` (L278), `REPLAN_MATERIAL_RISK_CHANGE` (L279), `REPLAN_HARD_STOP_OVERRIDE` (L280), `REPLAN_EPOCH_DEFERRED` (L283), `REPLAN_DEFERRED_ACTIVE_FILL_WINDOW` (L284), `REPLAN_DUPLICATE_PLAN_HASH` (L285)
  - `PauseReason` (L292): attrs=6, methods=0
    - attrs: `PAUSE_DATA_QUARANTINE` (L293), `PAUSE_DATA_DEGRADED` (L294), `PAUSE_META_DRIFT_SOFT` (L295), `PAUSE_BBWP_COOLOFF` (L296), `PAUSE_SESSION_FVG` (L297), `PAUSE_EXECUTION_UNSAFE` (L298)
  - `WarningCode` (L305): attrs=8, methods=0
    - attrs: `WARN_COST_MODEL_STALE` (L306), `WARN_CVD_DATA_QUALITY_LOW` (L307), `WARN_VRVP_UNAVAILABLE_FALLBACK_POC` (L308), `WARN_FEATURE_FALLBACK_USED` (L309), `WARN_EXEC_POST_ONLY_RETRY_HIGH` (L310), `WARN_EXEC_REPRICE_RATE_HIGH` (L311), `WARN_PLAN_EXPIRES_SOON` (L312), `WARN_PARTIAL_DATA_WINDOW` (L313)
  - `ExecCode` (L320): attrs=21, methods=0
    - attrs: `EXEC_PLAN_SCHEMA_INVALID` (L322), `EXEC_PLAN_HASH_MISMATCH` (L323), `EXEC_PLAN_DUPLICATE_IGNORED` (L324), `EXEC_PLAN_STALE_SEQ_IGNORED` (L325), `EXEC_PLAN_EXPIRED_IGNORED` (L326), `EXEC_PLAN_APPLIED` (L327), `EXEC_RECONCILE_START_LADDER_CREATED` (L330), `EXEC_RECONCILE_HOLD_NO_MATERIAL_CHANGE` (L331), `EXEC_RECONCILE_MATERIAL_REBUILD` (L332), `EXEC_RECONCILE_STOP_CANCELLED_LADDER` (L333), `EXEC_CAPACITY_RUNG_CAP_APPLIED` (L334), `EXEC_CAPACITY_NOTIONAL_CAP_APPLIED` (L335), `EXEC_CONFIRM_START_FAILED` (L336), `EXEC_CONFIRM_REBUILD_FAILED` (L337), `EXEC_CONFIRM_EXIT_FAILSAFE` (L338), `EXEC_POST_ONLY_RETRY` (L341), `EXEC_POST_ONLY_FALLBACK_REPRICE` (L342), `EXEC_ORDER_TIMEOUT_REPRICE` (L343), `EXEC_ORDER_CANCEL_REPLACE_APPLIED` (L344), `EXEC_FILL_REPLACEMENT_PLACED` (L345), `EXEC_FILL_DUPLICATE_GUARD_HIT` (L346)
  - `EventType` (L353): attrs=61, methods=0
    - attrs: `EVENT_POC_TEST` (L355), `EVENT_POC_ACCEPTANCE_CROSS` (L356), `EVENT_EXTREME_RETEST_TOP` (L357), `EVENT_EXTREME_RETEST_BOTTOM` (L358), `EVENT_EXT_1386_RETEST_TOP` (L359), `EVENT_EXT_1386_RETEST_BOTTOM` (L360), `EVENT_RANGE_HIT_TOP` (L361), `EVENT_RANGE_HIT_BOTTOM` (L362), `EVENT_BREAKOUT_BULL` (L365), `EVENT_BREAKOUT_BEAR` (L366), `EVENT_RECLAIM_CONFIRMED` (L367), `EVENT_CHANNEL_STRONG_BREAK_UP` (L368), `EVENT_CHANNEL_STRONG_BREAK_DN` (L369), `EVENT_CHANNEL_MIDLINE_TOUCH` (L370), `EVENT_DONCHIAN_STRONG_BREAK_UP` (L371), `EVENT_DONCHIAN_STRONG_BREAK_DN` (L372), `EVENT_DRIFT_RETEST_UP` (L373), `EVENT_DRIFT_RETEST_DN` (L374), `EVENT_SWEEP_WICK_HIGH` (L377), `EVENT_SWEEP_WICK_LOW` (L378), `EVENT_SWEEP_BREAK_RETEST_HIGH` (L379), `EVENT_SWEEP_BREAK_RETEST_LOW` (L380), `EVENT_SESSION_HIGH_SWEEP` (L381), `EVENT_SESSION_LOW_SWEEP` (L382), `EVENT_FVG_NEW_BULL` (L385), `EVENT_FVG_NEW_BEAR` (L386), `EVENT_FVG_MITIGATED_BULL` (L387), `EVENT_FVG_MITIGATED_BEAR` (L388), `EVENT_IMFVG_AVG_TAG_BULL` (L389), `EVENT_IMFVG_AVG_TAG_BEAR` (L390), `EVENT_SESSION_FVG_NEW` (L391), `EVENT_SESSION_FVG_MITIGATED` (L392), `EVENT_OB_NEW_BULL` (L393), `EVENT_OB_NEW_BEAR` (L394), `EVENT_OB_TAGGED_BULL` (L395), `EVENT_OB_TAGGED_BEAR` (L396), `EVENT_VRVP_POC_SHIFT` (L399), `EVENT_MICRO_POC_SHIFT` (L400), `EVENT_HVN_TOUCH` (L401), `EVENT_LVN_TOUCH` (L402), `EVENT_LVN_VOID_EXIT` (L403), `EVENT_FVG_POC_TAG` (L404), `EVENT_CVD_BULL_DIV` (L407), `EVENT_CVD_BEAR_DIV` (L408), `EVENT_CVD_BOS_UP` (L409), `EVENT_CVD_BOS_DN` (L410), `EVENT_CVD_SPIKE_POS` (L411), `EVENT_CVD_SPIKE_NEG` (L412), `EVENT_PASSIVE_ABSORPTION_UP` (L413), `EVENT_PASSIVE_ABSORPTION_DN` (L414), `EVENT_META_DRIFT_SOFT` (L415), `EVENT_META_DRIFT_HARD` (L416), `EVENT_BBWP_EXTREME` (L417), `EVENT_SQUEEZE_RELEASE_UP` (L418), `EVENT_SQUEEZE_RELEASE_DN` (L419), `EVENT_SPREAD_SPIKE` (L422), `EVENT_DEPTH_THIN` (L423), `EVENT_JUMP_DETECTED` (L424), `EVENT_POST_ONLY_REJECT_BURST` (L425), `EVENT_DATA_GAP_DETECTED` (L426), `EVENT_DATA_MISALIGN_DETECTED` (L427)
  - `InfoCode` (L434): attrs=5, methods=0
    - attrs: `INFO_VOL_BUCKET_CHANGED` (L435), `INFO_BOX_SHIFT_APPLIED` (L436), `INFO_TARGET_SOURCE_SELECTED` (L437), `INFO_SL_SOURCE_SELECTED` (L438), `INFO_REPLAN_EPOCH_BOUNDARY` (L439)

### `core/plan_signature.py`

- Top-level functions: 14
  - `_canonical_json` (L51), `stable_payload_hash` (L55), `material_plan_payload` (L60), `compute_plan_hash` (L64), `_is_sequence` (L68), `_material_diff_entries` (L72), `material_plan_diff_entries` (L105), `material_plan_changed_fields` (L116), `material_plan_diff_snapshot` (L123), `_parse_iso8601` (L143), `_parse_optional_datetime` (L158), `validate_signature_fields` (L169), `plan_is_expired` (L220), `plan_pair` (L235)
- Classes: 0

### `core/schema_validation.py`

- Top-level functions: 4
  - `_format_error` (L19), `schema_path` (L25), `_load_schema` (L30), `validate_schema` (L38)
- Classes: 0

### `data/__init__.py`

- Top-level functions: 0
- Classes: 0

### `data/data_quality_assessor.py`

- Top-level functions: 1
  - `assess_data_quality` (L12)
- Classes: 0

### `execution/__init__.py`

- Top-level functions: 0
- Classes: 0

### `execution/capacity_guard.py`

- Top-level functions: 4
  - `load_capacity_hint_state` (L9), `_as_float` (L48), `_as_int` (L57), `compute_dynamic_capacity_state` (L66)
- Classes: 0

### `freqtrade/user_data/scripts/grid_executor_v1.py`

- Top-level functions: 22
  - `log_event` (L26), `_log_plan_marker` (L40), `_plan_context` (L49), `load_json` (L130), `write_json` (L135), `_round_to_tick` (L143), `build_levels` (L149), `plan_signature` (L167), `soft_adjust_ok` (L201), `_action_signature` (L230), `quantize_price` (L237), `quantize_amount` (L243), `market_limits` (L249), `passes_min_notional` (L267), `_key_for` (L274), `_safe_float` (L281), `_safe_int` (L290), `_safe_bool` (L299), `_pair_fs` (L316), `_extract_rung_weights` (L320), `_normalized_side_weights` (L352), `main` (L2829)
- Classes: 4
  - `RestingOrder` (L81): attrs=7, methods=0
    - attrs: `side` (L82), `price` (L83), `qty_base` (L84), `level_index` (L85), `order_id` (L86), `status` (L87), `filled_base` (L90)
  - `ExecutorState` (L94): attrs=26, methods=0
    - attrs: `schema_version` (L95), `ts` (L96), `exchange` (L97), `pair` (L98), `symbol` (L99), `plan_ts` (L100), `mode` (L101), `last_applied_plan_id` (L102), `last_applied_seq` (L103), `last_applied_valid_for_candle_ts` (L104), `last_plan_hash` (L105), `executor_state_machine` (L106), `step` (L108), `n_levels` (L109), `box_low` (L110), `box_high` (L111), `quote_total` (L113), `base_total` (L114), `quote_free` (L116), `base_free` (L117), `quote_reserved` (L118), `base_reserved` (L119), `runtime` (L121), `orders` (L122), `applied_plan_ids` (L123), `applied_plan_hashes` (L124)
  - `FillCooldownGuard` (L365): attrs=0, methods=4
    - methods: `__init__` (L366), `configure` (L371), `allow` (L382), `mark` (L390)
  - `GridExecutorV1` (L399): attrs=0, methods=48
    - methods: `__init__` (L411), `_reserved_balances_intent` (L577), `_free_balances_intent` (L594), `_sync_balance_ccxt` (L598), `_recover_state_from_disk` (L626), `_reset_runtime_diagnostics` (L721), `_append_runtime_warning` (L740), `_append_runtime_exec_event` (L745), `_append_runtime_pause_reason` (L750), `_remember_applied_plan_id` (L755), `_remember_applied_plan_hash` (L765), `_record_applied_plan` (L775), `_reject_plan_intake` (L798), `_validate_plan_intake` (L814), `_write_rejected_plan_state` (L912), `_execution_cfg` (L924), `_apply_execution_hardening_config` (L937), `_prune_post_only_reject_window` (L1107), `_register_post_only_reject` (L1112), `_post_only_burst_status` (L1137), `_is_post_only_reject_error` (L1157), `_tick_for_price` (L1172), `_reprice_post_only_price` (L1178), `_confirm_metrics` (L1187), `_run_confirm_hook` (L1213), `_extract_capacity_inputs` (L1277), `_compute_capacity_state` (L1357), `_enforce_capacity_rung_cap` (L1413), `_execution_cost_paths` (L1461), `_append_jsonl` (L1480), `_record_order_lifecycle_event` (L1486), `_record_fill_lifecycle_event` (L1529), `_publish_execution_cost_artifact` (L1579), `_order_match_tolerant` (L1691), `_ccxt_call` (L1719), `_desired_initial_ladder` (L1753), `_ccxt_fetch_open_orders` (L1820), `_ccxt_cancel_order` (L1828), `_ccxt_place_limit` (L1836), `_ccxt_reconcile_set` (L1952), `_levels_for_index` (L2092), `_next_fill_bar_index` (L2097), `_extract_exit_levels` (L2112), `_find_order_by_id` (L2138), `_ingest_trades_and_replenish` (L2144), `step` (L2328), `_executor_state_machine` (L2730), `_write_state` (L2741)

### `freqtrade/user_data/scripts/grid_simulator_v1.py`

- Top-level functions: 40
  - `log_event` (L18), `_log_plan_marker` (L32), `_plan_context` (L41), `find_ohlcv_file` (L61), `load_ohlcv` (L88), `filter_timerange` (L132), `parse_start_at` (L147), `_round_to_tick` (L254), `build_levels` (L260), `_normalize_fill_mode` (L279), `_fill_trigger` (L288), `_touched_index_bounds` (L299), `_safe_float` (L370), `_safe_int` (L379), `_clamp_probability` (L388), `_build_chaos_runtime_config` (L418), `_uniform_int_inclusive` (L496), `extract_rung_weights` (L502), `normalized_side_weights` (L546), `plan_signature` (L564), `soft_adjust_ok` (L584), `action_signature` (L607), `extract_exit_levels` (L614), `plan_effective_time` (L644), `load_plan_sequence` (L669), `_uniq_reasons` (L732), `_increment_reason` (L744), `_increment_reasons` (L753), `_sorted_reason_counts` (L758), `_normalize_router_mode` (L762), `_normalize_replan_decision` (L769), `_normalize_materiality_class` (L776), `extract_start_block_reasons` (L783), `extract_start_counterfactual` (L813), `extract_stop_reason_flags` (L894), `build_desired_ladder` (L914), `simulate_grid` (L964), `simulate_grid_replay` (L1229), `load_plan` (L2175), `main` (L2180)
- Classes: 4
  - `OrderSim` (L236): attrs=5, methods=0
    - attrs: `side` (L237), `price` (L238), `qty_base` (L239), `level_index` (L240), `status` (L241)
  - `FillSim` (L245): attrs=6, methods=0
    - attrs: `ts_utc` (L246), `side` (L247), `price` (L248), `qty_base` (L249), `fee_quote` (L250), `reason` (L251)
  - `FillCooldownGuard` (L339): attrs=0, methods=4
    - methods: `__init__` (L340), `configure` (L345), `allow` (L356), `mark` (L364)
  - `ChaosRuntimeConfig` (L396): attrs=19, methods=0
    - attrs: `profile_id` (L397), `name` (L398), `enabled` (L399), `seed` (L400), `latency_mean_ms` (L401), `latency_jitter_ms` (L402), `latency_fill_window_ms` (L403), `spread_base_bps` (L404), `spread_burst_bps` (L405), `spread_burst_probability` (L406), `partial_fill_probability` (L407), `partial_fill_min_ratio` (L408), `partial_fill_max_ratio` (L409), `reject_burst_probability` (L410), `reject_burst_min_bars` (L411), `reject_burst_max_bars` (L412), `delayed_candle_probability` (L413), `missing_candle_probability` (L414), `data_gap_probability` (L415)

### `freqtrade/user_data/scripts/regime_audit_v1.py`

- Top-level functions: 26
  - `find_ohlcv_file` (L45), `load_ohlcv` (L60), `filter_timerange` (L92), `bb_width` (L103), `atr_series` (L111), `efficiency_ratio_series` (L119), `choppiness_index_series` (L136), `adx_wilder` (L164), `rolling_percentile_last` (L185), `future_roll_max` (L204), `future_roll_min` (L209), `resample_ohlcv` (L214), `build_feature_frame` (L233), `add_labels` (L303), `qval` (L340), `assign_non_trend_mask` (L347), `percentile_stats` (L369), `normalize_series` (L380), `feature_quantiles` (L392), `recommend_mode_thresholds` (L410), `label_counts` (L429), `add_verbose_states` (L444), `extract_transition_events` (L506), `transition_counts` (L552), `median_state_run_length` (L562), `main` (L577)
- Classes: 0

### `freqtrade/user_data/scripts/user_regression_suite.py`

- Top-level functions: 13
  - `_require` (L39), `_plan_get` (L44), `run_stress_replay_validation` (L53), `check_plan_schema_and_feature_outputs` (L78), `check_recent_plan_history` (L218), `_base_paper_executor` (L258), `_force_ref_inside_box` (L280), `check_executor_action_semantics` (L290), `check_weighted_ladder_and_simulator` (L342), `check_ml_overlay_behavior` (L483), `check_adx_hysteresis_behavior` (L547), `check_mode_router_handoff_behavior` (L603), `main` (L722)
- Classes: 0

### `freqtrade/user_data/strategies/GridBrainV1.py`

- Top-level functions: 1
  - `_normalize_runtime_value` (L82)
- Classes: 6
  - `EmpiricalCostCalibrator` (L98): attrs=0, methods=4
    - methods: `__init__` (L106), `_samples` (L112), `observe` (L119), `snapshot` (L161)
  - `MetaDriftGuard` (L243): attrs=0, methods=4
    - methods: `__init__` (L246), `reset_pair` (L251), `_pair_state` (L254), `observe` (L264)
  - `GridBrainRuntimeSnapshot` (L419): attrs=3, methods=2
    - attrs: `timestamp` (L420), `knobs` (L421), `lookbacks` (L422)
    - methods: `from_strategy` (L425), `as_dict` (L445)
  - `GridBrainLookbackSummary` (L450): attrs=2, methods=2
    - attrs: `lookbacks` (L451), `buffer` (L452)
    - methods: `from_strategy` (L455), `required_candles` (L469)
  - `GridBrainV1Core` (L475): attrs=487, methods=138
    - attrs: `INTERFACE_VERSION` (L515), `STOP_REASON_TREND_ADX` (L516), `STOP_REASON_VOL_EXPANSION` (L517), `STOP_REASON_BOX_BREAK` (L518), `STOP_REASON_META_DRIFT_HARD` (L519), `timeframe` (L525), `can_short` (L526), `minimal_roi` (L528), `stoploss` (L529), `trailing_stop` (L530), `process_only_new_candles` (L532), `lookback_buffer` (L533), `startup_candle_count` (L536), `data_quality_expected_candle_seconds` (L539), `data_quality_gap_multiplier` (L540), `data_quality_max_stale_minutes` (L541), `data_quality_zero_volume_streak_bars` (L542), `materiality_epoch_bars` (L545), `materiality_box_mid_shift_max_step_frac` (L546), `materiality_box_width_change_pct` (L547), `materiality_tp_shift_max_step_frac` (L548), `materiality_sl_shift_max_step_frac` (L549), `poc_acceptance_enabled` (L551), `poc_acceptance_lookback_bars` (L552), `poc_alignment_enabled` (L553), `poc_alignment_strict_enabled` (L554), `poc_alignment_lookback_bars` (L555), `poc_alignment_max_step_diff` (L556), `poc_alignment_max_width_frac` (L557), `box_lookback_24h_bars` (L561), `box_lookback_48h_bars` (L562), `box_lookback_18h_bars` (L563), `box_lookback_12h_bars` (L564), `extremes_7d_bars` (L565), `box_overlap_prune_threshold` (L566), `box_overlap_history` (L567), `box_band_overlap_required` (L568), `box_band_adx_allow` (L569), `box_band_rvol_allow` (L570), `box_envelope_ratio_max` (L571), `box_envelope_adx_threshold` (L572), `box_envelope_rvol_threshold` (L573), `session_box_pad_shrink_pct` (L574), `breakout_lookback_bars` (L577), `breakout_block_bars` (L578), `breakout_override_allowed` (L579), `breakout_straddle_step_buffer_frac` (L580), `breakout_reason_code` (L581), `min_range_len_bars` (L582), `breakout_confirm_bars` (L583), `breakout_confirm_buffer_mode` (L584), `breakout_confirm_buffer_value` (L585), `atr_period_15m` (L587), `atr_pad_mult` (L588), `rsi_period_15m` (L590), `rsi_min` (L591), `rsi_max` (L592), `adx_period` (L595), `adx_4h_max` (L596), `ema_fast` (L599), `ema_slow` (L600), `ema_dist_max_frac` (L601), `bb_window` (L603), `bb_stds` (L604), `bbw_pct_lookback_1h` (L605), `bbw_1h_pct_max` (L606), `bbw_nonexp_lookback_bars` (L607), `bbw_nonexp_tolerance_frac` (L608), `context_7d_hard_veto` (L609), `vol_sma_window` (L611), `vol_spike_mult` (L612), `rvol_window_15m` (L613), `rvol_15m_max` (L614), `vrvp_lookback_bars` (L617), `vrvp_bins` (L618), `vrvp_value_area_pct` (L619), `vrvp_poc_outside_box_max_frac` (L620), `vrvp_max_box_shift_frac` (L621), `vrvp_reject_if_still_outside` (L622), `fallback_poc_estimator_enabled` (L623), `fallback_poc_lookback_bars` (L624), `bbwp_enabled` (L627), `bbwp_lookback_s` (L628), `bbwp_lookback_m` (L629), `bbwp_lookback_l` (L630), `bbwp_s_max` (L631), `bbwp_m_max` (L632), `bbwp_l_max` (L633), `bbwp_veto_pct` (L634), `bbwp_cooloff_trigger_pct` (L635), `bbwp_cooloff_release_s` (L636), `bbwp_cooloff_release_m` (L637), `bbwp_nonexp_bars` (L638), `squeeze_enabled` (L639), `squeeze_require_on_1h` (L640), `squeeze_momentum_block_enabled` (L641), `squeeze_tp_nudge_enabled` (L642), `squeeze_tp_nudge_step_multiple` (L643), `kc_atr_mult` (L644), `band_slope_veto_enabled` (L647), `band_slope_veto_bars` (L648), `band_slope_veto_pct` (L649), `drift_slope_veto_enabled` (L650), `excursion_asymmetry_veto_enabled` (L651), `excursion_asymmetry_min_ratio` (L652), `excursion_asymmetry_max_ratio` (L653), `hvp_enabled` (L654), `hvp_lookback_bars` (L655), `hvp_sma_bars` (L656), `funding_filter_enabled` (L657), `funding_filter_pct` (L658), `instrumentation_er_lookback` (L661), `instrumentation_chop_lookback` (L662), `instrumentation_di_flip_lookback` (L663), `instrumentation_wickiness_lookback` (L664), `instrumentation_containment_lookback` (L665), `instrumentation_atr_pct_percentile` (L666), `instrumentation_atr_pct_lookback` (L667), `os_dev_enabled` (L670), `os_dev_n_strike` (L671), `os_dev_range_band` (L672), `os_dev_persist_bars` (L673), `os_dev_rvol_max` (L674), `os_dev_history_bars` (L675), `micro_vap_enabled` (L678), `micro_vap_lookback_bars` (L679), `micro_vap_bins` (L680), `micro_hvn_quantile` (L681), `micro_lvn_quantile` (L682), `micro_extrema_count` (L683), `micro_lvn_corridor_steps` (L684), `micro_void_slope_threshold` (L685), `fvg_enabled` (L688), `fvg_lookback_bars` (L689), `fvg_min_gap_atr` (L690), `fvg_straddle_veto_steps` (L691), `fvg_position_avg_count` (L692), `imfvg_enabled` (L694), `imfvg_mitigated_relax` (L695), `defensive_fvg_enabled` (L697), `defensive_fvg_min_gap_atr` (L698), `defensive_fvg_body_frac` (L699), `defensive_fvg_fresh_bars` (L700), `session_fvg_enabled` (L702), `session_fvg_inside_gate` (L703), `session_fvg_pause_bars` (L704), `mrvd_enabled` (L707), `mrvd_bins` (L708), `mrvd_value_area_pct` (L709), `mrvd_day_lookback_bars` (L710), `mrvd_week_lookback_bars` (L711), `mrvd_month_lookback_bars` (L712), `mrvd_required_overlap_count` (L713), `mrvd_va_overlap_min_frac` (L714), `mrvd_near_poc_steps` (L715), `mrvd_drift_guard_enabled` (L716), `mrvd_drift_guard_steps` (L717), `cvd_enabled` (L720), `cvd_lookback_bars` (L721), `cvd_pivot_left` (L722), `cvd_pivot_right` (L723), `cvd_divergence_max_age_bars` (L724), `cvd_near_value_steps` (L725), `cvd_bos_lookback` (L726), `cvd_bos_freeze_bars` (L727), `cvd_rung_bias_strength` (L728), `freqai_overlay_enabled` (L731), `freqai_overlay_gate_mode` (L732), `freqai_overlay_strict_predict` (L733), `freqai_overlay_confidence_min` (L734), `freqai_overlay_breakout_scale` (L735), `freqai_overlay_breakout_quick_tp_thresh` (L736), `freqai_overlay_rung_edge_cut_max` (L737), `rung_weight_hvn_boost` (L740), `rung_weight_lvn_penalty` (L741), `rung_weight_min` (L742), `rung_weight_max` (L743), `target_net_step_pct` (L747), `est_fee_pct` (L748), `est_spread_pct` (L749), `majors_gross_step_floor_pct` (L750), `n_min` (L751), `n_max` (L752), `n_volatility_adapter_enabled` (L753), `n_volatility_adapter_strength` (L754), `volatility_min_step_buffer_bps` (L755), `empirical_cost_enabled` (L758), `empirical_cost_window` (L759), `empirical_cost_min_samples` (L760), `empirical_cost_stale_bars` (L761), `empirical_cost_percentile` (L762), `empirical_cost_conservative_mode` (L763), `empirical_cost_require_live_samples` (L764), `empirical_cost_min_live_samples` (L765), `empirical_spread_proxy_scale` (L766), `empirical_adverse_selection_scale` (L767), `empirical_retry_penalty_pct` (L768), `empirical_missed_fill_penalty_pct` (L769), `empirical_cost_floor_min_pct` (L770), `execution_cost_artifact_enabled` (L771), `execution_cost_artifact_dir` (L772), `execution_cost_artifact_filename` (L773), `execution_cost_artifact_max_age_minutes` (L774), `min_width_pct` (L777), `max_width_pct` (L778), `box_width_avg_veto_enabled` (L779), `box_width_avg_veto_lookback` (L780), `box_width_avg_veto_min_samples` (L781), `box_width_avg_veto_max_ratio` (L782), `stop_confirm_bars` (L785), `fast_stop_step_multiple` (L786), `range_shift_stop_pct` (L787), `tp_step_multiple` (L788), `sl_step_multiple` (L789), `reclaim_hours` (L790), `cooldown_minutes` (L791), `min_runtime_hours` (L792), `neutral_stop_adx_bars` (L793), `neutral_box_break_bars` (L794), `neutral_box_break_step_multiple` (L795), `drawdown_guard_enabled` (L796), `drawdown_guard_lookback_bars` (L797), `drawdown_guard_max_pct` (L798), `max_stops_window_enabled` (L799), `max_stops_window_minutes` (L800), `max_stops_window_count` (L801), `gate_profile` (L804), `start_min_gate_pass_ratio` (L805), `start_stability_min_score` (L806), `start_stability_k_fraction` (L807), `start_box_position_guard_enabled` (L808), `start_box_position_min_frac` (L809), `start_box_position_max_frac` (L810), `basis_cross_confirm_enabled` (L811), `capacity_hint_path` (L812), `capacity_hint_hard_block` (L813), `planner_health_quarantine_on_gap` (L816), `planner_health_quarantine_on_misalign` (L817), `meta_drift_soft_block_enabled` (L818), `meta_drift_soft_block_steps` (L819), `meta_drift_guard_enabled` (L820), `meta_drift_guard_window` (L821), `meta_drift_guard_min_samples` (L822), `meta_drift_guard_smoothing_alpha` (L823), `meta_drift_guard_eps` (L824), `meta_drift_guard_z_soft` (L825), `meta_drift_guard_z_hard` (L826), `meta_drift_guard_cusum_k_sigma` (L827), `meta_drift_guard_cusum_soft` (L828), `meta_drift_guard_cusum_hard` (L829), `meta_drift_guard_ph_delta_sigma` (L830), `meta_drift_guard_ph_soft` (L831), `meta_drift_guard_ph_hard` (L832), `meta_drift_guard_soft_min_channels` (L833), `meta_drift_guard_hard_min_channels` (L834), `meta_drift_guard_cooldown_extend_minutes` (L835), `meta_drift_guard_spread_proxy_scale` (L836), `breakout_idle_reclaim_on_fresh` (L837), `hvp_quiet_exit_bias_enabled` (L838), `hvp_quiet_exit_step_multiple` (L839), `regime_router_enabled` (L842), `regime_router_default_mode` (L843), `regime_router_force_mode` (L844), `regime_router_switch_persist_bars` (L845), `regime_router_switch_cooldown_bars` (L846), `regime_router_switch_margin` (L847), `regime_router_allow_pause` (L848), `regime_router_score_enter` (L849), `regime_router_score_exit` (L850), `regime_router_score_persistence_bars` (L851), `regime_router_score_artifact_run_id` (L852), `regime_router_score_artifact_dir` (L853), `regime_router_score_artifact_file` (L854), `neutral_adx_enter_pct` (L855), `neutral_adx_exit_pct` (L856), `neutral_adx_veto_pct` (L857), `neutral_bbwp_enter_min_pct` (L858), `neutral_bbwp_enter_max_pct` (L859), `neutral_bbwp_veto_pct` (L860), `neutral_bbwp_dead_pct` (L861), `neutral_atr_pct_min` (L862), `neutral_spread_bps_max` (L863), `neutral_spread_step_frac` (L864), `neutral_enter_persist_min` (L867), `neutral_enter_persist_max` (L868), `neutral_exit_persist_ratio` (L869), `neutral_cooldown_multiplier` (L870), `neutral_min_runtime_hours_offset` (L871), `neutral_persistence_default_enter` (L872), `neutral_grid_levels_ratio` (L873), `neutral_grid_budget_ratio` (L874), `neutral_rebuild_shift_pct` (L875), `neutral_rebuild_max_bars` (L876), `regime_threshold_profile` (L894), `intraday_adx_enter_max` (L897), `intraday_adx_exit_min` (L898), `intraday_adx_rising_bars` (L899), `intraday_bbw_1h_pct_max` (L900), `intraday_bbw_nonexp_lookback_bars` (L901), `intraday_bbw_nonexp_tolerance_frac` (L902), `intraday_ema_dist_max_frac` (L903), `intraday_vol_spike_mult` (L904), `intraday_rvol_15m_max` (L905), `intraday_bbwp_s_enter_low` (L906), `intraday_bbwp_s_enter_high` (L907), `intraday_bbwp_m_enter_low` (L908), `intraday_bbwp_m_enter_high` (L909), `intraday_bbwp_l_enter_low` (L910), `intraday_bbwp_l_enter_high` (L911), `intraday_bbwp_stop_high` (L912), `intraday_atr_pct_max` (L913), `intraday_os_dev_persist_bars` (L914), `intraday_os_dev_rvol_max` (L915), `swing_adx_enter_max` (L918), `swing_adx_exit_min` (L919), `swing_adx_rising_bars` (L920), `swing_bbw_1h_pct_max` (L921), `swing_bbw_nonexp_lookback_bars` (L922), `swing_bbw_nonexp_tolerance_frac` (L923), `swing_ema_dist_max_frac` (L924), `swing_vol_spike_mult` (L925), `swing_rvol_15m_max` (L926), `swing_bbwp_s_enter_low` (L927), `swing_bbwp_s_enter_high` (L928), `swing_bbwp_m_enter_low` (L929), `swing_bbwp_m_enter_high` (L930), `swing_bbwp_l_enter_low` (L931), `swing_bbwp_l_enter_high` (L932), `swing_bbwp_stop_high` (L933), `swing_atr_pct_max` (L934), `swing_os_dev_persist_bars` (L935), `swing_os_dev_rvol_max` (L936), `emit_per_candle_history_backtest` (L939), `soft_adjust_max_step_frac` (L942), `inventory_mode` (L945), `inventory_target_base_min_pct` (L946), `inventory_target_base_max_pct` (L947), `topup_policy` (L948), `max_concurrent_rebuilds` (L949), `preferred_rung_cap` (L950), `grid_budget_pct` (L951), `reserve_pct` (L952), `donchian_lookback_bars` (L955), `basis_band_window` (L956), `basis_band_stds` (L957), `fvg_vp_enabled` (L958), `fvg_vp_bins` (L959), `fvg_vp_lookback_bars` (L960), `fvg_vp_poc_tag_step_frac` (L961), `sl_lvn_avoid_steps` (L962), `sl_fvg_buffer_steps` (L963), `box_quality_log_space` (L964), `box_quality_extension_factor` (L965), `midline_bias_fallback_enabled` (L966), `midline_bias_tp_candidate_enabled` (L967), `midline_bias_poc_neutral_step_frac` (L968), `midline_bias_poc_neutral_width_frac` (L969), `midline_bias_source_buffer_steps` (L970), `midline_bias_source_buffer_width_frac` (L971), `midline_bias_deadband_steps` (L972), `midline_bias_deadband_width_frac` (L973), `fill_confirmation_mode` (L976), `fill_no_repeat_lsi_guard` (L977), `fill_no_repeat_cooldown_bars` (L978), `tick_size_step_frac` (L979), `tick_size_floor` (L980), `micro_reentry_pause_bars` (L983), `micro_reentry_require_poc_reclaim` (L984), `micro_reentry_poc_buffer_steps` (L985), `buy_ratio_bias_enabled` (L986), `buy_ratio_midband_half_width` (L987), `buy_ratio_bullish_threshold` (L988), `buy_ratio_bearish_threshold` (L989), `buy_ratio_rung_bias_strength` (L990), `buy_ratio_bearish_tp_step_multiple` (L991), `smart_channel_enabled` (L992), `smart_channel_breakout_step_buffer` (L993), `smart_channel_volume_confirm_enabled` (L994), `smart_channel_volume_rvol_min` (L995), `smart_channel_tp_nudge_step_multiple` (L996), `ob_enabled` (L997), `ob_tf` (L998), `ob_use_wick_zone` (L999), `ob_impulse_lookahead` (L1000), `ob_impulse_atr_len` (L1001), `ob_impulse_atr_mult` (L1002), `ob_fresh_bars` (L1003), `ob_max_age_bars` (L1004), `ob_mitigation_mode` (L1005), `ob_straddle_min_step_mult` (L1006), `ob_tp_nudge_max_steps` (L1007), `zigzag_contraction_enabled` (L1008), `zigzag_contraction_lookback_bars` (L1009), `zigzag_contraction_ratio_max` (L1010), `session_sweep_enabled` (L1011), `session_sweep_retest_lookback_bars` (L1012), `sweeps_enabled` (L1013), `sweep_pivot_len` (L1014), `sweep_max_age_bars` (L1015), `sweep_break_buffer_mode` (L1016), `sweep_break_buffer_value` (L1017), `sweep_retest_window_bars` (L1018), `sweep_retest_buffer_mode` (L1019), `sweep_retest_buffer_value` (L1020), `sweep_stop_if_through_box_edge` (L1021), `sweep_retest_validation_mode` (L1022), `sweep_min_level_separation_steps` (L1023), `order_flow_enabled` (L1024), `order_flow_spread_soft_max_pct` (L1025), `order_flow_depth_thin_soft_max` (L1026), `order_flow_imbalance_extreme` (L1027), `order_flow_jump_soft_max_pct` (L1028), `order_flow_soft_veto_min_flags` (L1029), `order_flow_hard_block` (L1030), `order_flow_confidence_penalty_per_flag` (L1031), `plans_root_rel` (L1033), `plan_schema_version` (L1034), `planner_version` (L1035), `plan_expiry_seconds` (L1036), `decision_log_enabled` (L1037), `event_log_enabled` (L1038), `decision_log_filename` (L1039), `event_log_filename` (L1040), `decision_event_log_max_changed_fields` (L1041), `_last_written_ts_by_pair` (L1044), `_last_plan_hash_by_pair` (L1045), `_last_plan_base_hash_by_pair` (L1046), `_last_material_plan_payload_by_pair` (L1047), `_last_plan_id_by_pair` (L1048), `_last_decision_seq_by_pair` (L1049), `_event_counter_by_pair` (L1050), `_last_mid_by_pair` (L1051), `_last_box_step_by_pair` (L1052), `_reclaim_until_ts_by_pair` (L1053), `_cooldown_until_ts_by_pair` (L1054), `_micro_reentry_pause_until_ts_by_pair` (L1055), `_stop_timestamps_by_pair` (L1056), `_active_since_ts_by_pair` (L1057), `_running_by_pair` (L1058), `_bbwp_cooloff_by_pair` (L1059), `_os_dev_state_by_pair` (L1060), `_os_dev_candidate_by_pair` (L1061), `_os_dev_candidate_count_by_pair` (L1062), `_os_dev_zero_persist_by_pair` (L1063), `_mrvd_day_poc_prev_by_pair` (L1064), `_cvd_freeze_bars_left_by_pair` (L1065), `_last_adx_by_pair` (L1066), `_adx_rising_count_by_pair` (L1067), `_mode_by_pair` (L1068), `_mode_candidate_by_pair` (L1069), `_mode_candidate_count_by_pair` (L1070), `_mode_cooldown_until_ts_by_pair` (L1071), `_running_mode_by_pair` (L1072), `_mode_at_entry_by_pair` (L1073), `_mode_at_exit_by_pair` (L1074), `_history_emit_in_progress_by_pair` (L1075), `_history_emit_end_ts_by_pair` (L1076), `_box_state_by_pair` (L1077), `_box_rebuild_bars_since_by_pair` (L1078), `_neutral_box_break_bars_by_pair` (L1079), `_breakout_levels_by_pair` (L1080), `_breakout_bars_since_by_pair` (L1081), `_box_signature_by_pair` (L1082), `_data_quality_issues_by_pair` (L1083), `_materiality_epoch_bar_count_by_pair` (L1084), `_box_history_by_pair` (L1085), `_box_width_history_by_pair` (L1086), `_last_width_pct_by_pair` (L1087), `_last_tp_price_by_pair` (L1088), `_last_sl_price_by_pair` (L1089), `_ob_state_by_pair` (L1090), `_poc_acceptance_crossed_by_pair` (L1091), `_poc_alignment_crossed_by_pair` (L1092), `_plan_guard_decision_count_by_pair` (L1093), `_mid_history_by_pair` (L1094), `_hvp_cooloff_by_pair` (L1095), `_box_quality_by_pair` (L1096), `_mid_history_by_pair` (L1097), `_hvp_cooloff_by_pair` (L1098), `_meta_drift_prev_box_pos_by_pair` (L1099), `_external_mode_thresholds_path_cache` (L1100), `_external_mode_thresholds_mtime_cache` (L1101), `_external_mode_thresholds_cache` (L1102), `_neutral_persistence_state_by_pair` (L1103), `MODE_TRADING` (L2047), `MODE_TRADING_WITH_PAUSE` (L2048), `MODE_VALUES` (L2050)
    - methods: `__init__` (L491), `_determine_regime_bands_run_id` (L878), `informative_pairs` (L1106), `populate_indicators_4h` (L1117), `populate_indicators_1h` (L1132), `_safe_float` (L1164), `_record_mid_history` (L1179), `_compute_band_slope_pct` (L1189), `_excursion_asymmetry_ratio` (L1199), `_funding_gate_ok` (L1209), `_hvp_stats` (L1216), `_box_signature` (L1233), `_poc_cross_detected` (L1239), `_derive_box_block_reasons` (L1256), `_box_straddles_cached_breakout` (L1271), `_box_straddles_level` (L1296), `_box_level_straddle_reasons` (L1309), `_squeeze_release_block_reason` (L1326), `_append_reason` (L1329), `_run_data_quality_checks` (L1333), `_percentile` (L1346), `_poc_acceptance_status` (L1357), `_fallback_poc_estimate` (L1381), `_box_width_history` (L1406), `_box_width_avg_veto_state` (L1418), `_record_accepted_box_width` (L1447), `_poc_alignment_state` (L1451), `_efficiency_ratio` (L1526), `_detect_structural_breakout` (L1539), `_breakout_confirm_buffer` (L1560), `_breakout_confirm_state` (L1581), `_range_len_gate_state` (L1622), `_breakout_confirm_reason_state` (L1647), `_bbw_nonexpanding` (L1679), `_update_breakout_fresh_state` (L1696), `_phase2_gate_failures_from_flags` (L1729), `_planner_health_state` (L1750), `_start_stability_state` (L1767), `_atomic_write_json` (L1774), `_evaluate_materiality` (L1777), `_validate_feature_contract` (L1816), `_log_feature_contract_violation` (L1839), `_choppiness_index` (L1854), `_di_flip_rate` (L1878), `_wickiness` (L1903), `_containment_pct` (L1929), `_adx_exit_hysteresis_trigger` (L1960), `_adx_di_down_risk_trigger` (L1973), `_gate_profile_values` (L1993), `_normalize_mode_name` (L2053), `_neutral_adx_pct` (L2063), `_neutral_spread_bps` (L2072), `_neutral_step_bps` (L2080), `_neutral_spread_threshold` (L2086), `_active_threshold_profile` (L2091), `_external_mode_threshold_overrides` (L2097), `_mode_threshold_overrides` (L2176), `_mode_threshold_block` (L2242), `_mode_router_score` (L2314), `_regime_router_state` (L2373), `_runmode_name` (L2649), `_should_emit_per_candle_history` (L2668), `_reset_pair_runtime_state` (L2674), `_ts_to_iso` (L2721), `_plan_dir` (L2729), `_seed_plan_signature_state` (L2742), `_next_plan_identity` (L2782), `_write_plan` (L2789), `_decision_log_path` (L2865), `_event_log_path` (L2870), `_append_jsonl` (L2876), `_severity_for_code` (L2883), `_source_module_for_code` (L2915), `_next_event_id` (L2989), `_emit_decision_and_event_logs` (L2994), `_range_candidate` (L3099), `_build_box_15m` (L3104), `_latest_daily_vwap` (L3153), `_is_level_near_box` (L3175), `_box_quality_levels` (L3201), `_midline_bias_fallback_state` (L3257), `_update_box_quality` (L3350), `_box_overlap_fraction` (L3380), `_box_overlap_prune` (L3395), `_record_box_history` (L3405), `_bbw_percentile_ok` (L3413), `_bbwp_percentile_last` (L3419), `_user_data_dir` (L3430), `_regime_bands_artifact_path` (L3435), `_pair_fs` (L3443), `_execution_cost_artifact_path` (L3446), `_load_execution_cost_artifact` (L3451), `_load_regime_bands_entries` (L3525), `_neutral_band_entry` (L3547), `_normalize_from_band` (L3552), `_neutral_persistence_for_pair` (L3575), `_compute_chop_score` (L3591), `_vrvp_profile` (L3630), `_interval_overlap_frac` (L3690), `_mrvd_profile` (L3702), `_pivot_indices` (L3803), `_cvd_state` (L3831), `_apply_cvd_rung_bias` (L3957), `_find_numeric_row` (L3993), `_freqai_overlay_state` (L4020), `_apply_ml_rung_safety` (L4136), `_os_dev_from_history` (L4170), `_micro_vap_inside_box` (L4219), `_rung_weights_from_micro_vap` (L4315), `_fvg_stack_state` (L4358), `_capacity_hint_state` (L4678), `_empirical_cost_sample` (L4685), `_meta_drift_channels` (L4756), `_meta_drift_state` (L4791), `_effective_cost_floor` (L4881), `_n_level_bounds` (L5067), `_grid_sizing` (L5083), `_nearest_above` (L5144), `_select_tp_price` (L5158), `_select_sl_price` (L5175), `_infer_tick_size` (L5202), `_breakout_flags` (L5208), `_micro_buy_ratio_state` (L5221), `_apply_buy_ratio_rung_bias` (L5281), `_fvg_vp_state` (L5311), `_smart_channel_state` (L5394), `_zigzag_contraction_state` (L5458), `_informative_ohlc_frame` (L5497), `_order_block_state` (L5526), `_session_sweep_state` (L5704), `_order_flow_state` (L5779), `_drawdown_guard_state` (L5838), `_max_stops_window_state` (L5869), `_register_stop_timestamp` (L5893), `_micro_reentry_state` (L5900), `populate_indicators` (L5931), `populate_entry_trend` (L9599), `populate_exit_trend` (L9603)
  - `GridBrainV1` (L9608): attrs=0, methods=0

### `freqtrade/user_data/strategies/GridBrainV1BaselineNoNeutral.py`

- Top-level functions: 0
- Classes: 1
  - `GridBrainV1BaselineNoNeutral` (L4): attrs=2, methods=0
    - attrs: `regime_router_enabled` (L5), `regime_router_force_mode` (L6)

### `freqtrade/user_data/strategies/GridBrainV1ExpRouterFast.py`

- Top-level functions: 0
- Classes: 1
  - `GridBrainV1ExpRouterFast` (L4): attrs=2, methods=0
    - attrs: `regime_router_switch_persist_bars` (L11), `regime_router_switch_margin` (L12)

### `freqtrade/user_data/strategies/GridBrainV1NeutralDiFilter.py`

- Top-level functions: 0
- Classes: 1
  - `GridBrainV1NeutralDiFilter` (L4): attrs=1, methods=1
    - attrs: `neutral_di_flip_max` (L5)
    - methods: `_regime_router_state` (L7)

### `freqtrade/user_data/strategies/GridBrainV1NeutralEligibilityOnly.py`

- Top-level functions: 0
- Classes: 1
  - `GridBrainV1NeutralEligibilityOnly` (L4): attrs=6, methods=0
    - attrs: `neutral_grid_levels_ratio` (L5), `neutral_grid_budget_ratio` (L6), `neutral_enter_persist_min` (L7), `neutral_enter_persist_max` (L8), `neutral_persistence_default_enter` (L9), `neutral_cooldown_multiplier` (L10)

### `freqtrade/user_data/strategies/GridBrainV1NoFVG.py`

- Top-level functions: 0
- Classes: 1
  - `GridBrainV1NoFVG` (L4): attrs=5, methods=0
    - attrs: `fvg_enabled` (L7), `defensive_fvg_enabled` (L8), `session_fvg_enabled` (L9), `session_fvg_inside_gate` (L10), `imfvg_enabled` (L11)

### `freqtrade/user_data/strategies/GridBrainV1NoPause.py`

- Top-level functions: 0
- Classes: 1
  - `GridBrainV1NoPause` (L4): attrs=2, methods=0
    - attrs: `regime_router_allow_pause` (L11), `regime_router_default_mode` (L12)

### `freqtrade/user_data/strategies/sample_strategy.py`

- Top-level functions: 0
- Classes: 1
  - `SampleStrategy` (L40): attrs=18, methods=4
    - attrs: `INTERFACE_VERSION` (L60), `can_short` (L63), `minimal_roi` (L67), `stoploss` (L76), `trailing_stop` (L79), `timeframe` (L85), `process_only_new_candles` (L88), `use_exit_signal` (L91), `exit_profit_only` (L92), `ignore_roi_if_entry_signal` (L93), `buy_rsi` (L96), `sell_rsi` (L97), `short_rsi` (L98), `exit_short_rsi` (L99), `startup_candle_count` (L104), `order_types` (L107), `order_time_in_force` (L115), `plot_config` (L117)
    - methods: `informative_pairs` (L133), `populate_indicators` (L146), `populate_entry_trend` (L366), `populate_exit_trend` (L397)

### `freqtrade/user_data/tests/test_chaos_replay_harness.py`

- Top-level functions: 8
  - `_build_replay_df` (L9), `_plan_at` (L22), `_base_profile` (L35), `_simulate` (L53), `test_chaos_profile_is_deterministic_and_reports_delta` (L66), `test_chaos_partial_fill_profile_marks_partial_fills` (L91), `test_chaos_data_gap_profile_drops_candles` (L104), `test_chaos_fault_injection_profiles_trigger_expected_rails` (L161)
- Classes: 0

### `freqtrade/user_data/tests/test_executor_hardening.py`

- Top-level functions: 12
  - `_base_plan` (L14), `_executor` (L98), `test_ccxt_place_limit_retries_post_only_with_backoff_and_reprice` (L111), `test_reject_burst_blocks_start_and_downgrades_to_hold` (L131), `test_stop_exit_confirm_uses_failsafe_reason` (L153), `test_rebuild_confirm_failure_is_tracked_separately` (L176), `test_reconcile_matches_live_orders_with_tolerance` (L201), `test_reconcile_honors_action_cap` (L233), `test_executor_recovers_state_file_on_startup` (L260), `test_capacity_rung_cap_limits_seeded_orders_in_paper` (L306), `test_capacity_hard_block_prevents_start` (L339), `test_execution_cost_feedback_writes_artifact_and_lifecycle_logs` (L365)
- Classes: 2
  - `_RetryThenAcceptExchange` (L71): attrs=0, methods=4
    - methods: `__init__` (L72), `price_to_precision` (L76), `amount_to_precision` (L79), `create_limit_buy_order` (L82)
  - `_ReconcileExchange` (L90): attrs=0, methods=2
    - methods: `__init__` (L91), `fetch_open_orders` (L94)

### `freqtrade/user_data/tests/test_liquidity_sweeps.py`

- Top-level functions: 6
  - `_sweep_df` (L8), `_base_cfg` (L21), `test_pivot_confirmation_is_bar_confirmed` (L37), `test_wick_sweep_and_break_retest_stop_through_box_edge` (L59), `test_retest_validation_mode_toggle_affects_break_retest_only` (L76), `test_determinism_for_same_inputs` (L101)
- Classes: 0

### `freqtrade/user_data/tests/test_meta_drift_replay.py`

- Top-level functions: 3
  - `_build_replay_df` (L8), `_plan_at` (L21), `test_replay_synthetic_regime_shift_tracks_meta_drift_soft_and_hard` (L53)
- Classes: 0

### `freqtrade/user_data/tests/test_min_range_and_breakout_confirm.py`

- Top-level functions: 10
  - `_strategy_for_breakout_buffer` (L9), `_close_df` (L16), `test_min_range_len_gate_blocks_before_threshold` (L20), `test_min_range_len_gate_passes_at_threshold` (L34), `test_min_range_len_gate_resets_on_new_box_generation` (L46), `test_breakout_confirm_single_close_outside_is_not_confirmed` (L64), `test_breakout_confirm_up_blocks_start_when_not_running` (L79), `test_breakout_confirm_dn_stops_when_running` (L98), `test_breakout_confirm_buffer_modes` (L125), `test_breakout_confirm_determinism_on_same_input` (L138)
- Classes: 0

### `freqtrade/user_data/tests/test_ml_overlay_step14.py`

- Top-level functions: 7
  - `_window` (L17), `_write_summary` (L34), `_write_json` (L69), `_write_schema` (L74), `test_step14_ml_scripts_pipeline` (L108), `test_tuning_protocol_respects_required_ml_overlay_gate` (L212), `test_ml_overlay_defaults_are_advisory_and_off` (L332)
- Classes: 0

### `freqtrade/user_data/tests/test_order_blocks.py`

- Top-level functions: 7
  - `_new_strategy` (L9), `_bull_ob_df` (L13), `_bear_ob_df` (L26), `_as_strategy_df` (L39), `test_order_block_detects_bull_and_mitigation` (L48), `test_order_block_detects_bear_and_freshness_window` (L69), `test_order_block_strategy_state_applies_fresh_gate_straddle_and_tp_nudges` (L89)
- Classes: 0

### `freqtrade/user_data/tests/test_partial_module_completion.py`

- Top-level functions: 5
  - `_new_strategy` (L14), `test_protections_drawdown_and_stop_window_helpers` (L18), `test_micro_bias_order_flow_and_reentry_helpers` (L46), `test_fvg_vp_channel_and_session_sweep_helpers` (L125), `test_event_bus_emits_reason_and_taxonomy_events` (L204)
- Classes: 0

### `freqtrade/user_data/tests/test_phase3_validation.py`

- Top-level functions: 48
  - `test_box_signature_is_repeatable` (L16), `test_poc_cross_detected_when_open_close_bracket_value` (L22), `test_derive_box_block_reasons_reflects_conflicts` (L33), `test_poc_acceptance_status_persists_once_crossed` (L45), `_fresh_phase3_strategy` (L64), `test_data_quality_checks_flag_gap` (L75), `test_data_quality_checks_flag_duplicates` (L91), `test_data_quality_checks_zero_volume_streak` (L107), `test_phase2_gate_failures_records_block_reasons` (L125), `test_start_block_reasons_include_baseline_codes` (L144), `test_start_block_reasons_include_breakout_block` (L157), `test_materiality_waits_for_epoch_or_delta` (L168), `test_compute_band_slope_pct_respects_window` (L186), `test_excursion_asymmetry_ratio_handles_invalid_devs` (L197), `test_funding_gate_honors_threshold` (L203), `test_box_straddle_breakout_detection_adds_blocker` (L213), `test_squeeze_release_block_reason_is_consumed` (L223), `test_bbw_nonexpanding_gate_requires_flat_or_contracting_window` (L231), `test_breakout_fresh_state_blocks_until_reclaimed` (L238), `test_detect_structural_breakout_uses_close_vs_prior_extremes` (L255), `test_hvp_stats_returns_current_and_sma` (L271), `test_planner_health_state_transitions` (L283), `test_start_stability_state_supports_k_of_n_and_score` (L292), `test_box_quality_metrics_and_straddle_helpers` (L305), `test_box_quality_levels_linear_fallback_when_nonpositive_bounds` (L320), `test_midline_bias_fallback_activates_when_vrvp_poc_is_neutral` (L333), `test_midline_bias_fallback_stays_inactive_when_vrvp_poc_not_neutral` (L364), `test_fallback_poc_estimate_uses_volume_weighted_typical_price` (L393), `test_box_width_avg_veto_triggers_when_width_exceeds_rolling_ratio` (L410), `test_poc_alignment_strict_requires_cross_when_misaligned` (L424), `test_poc_acceptance_handles_multiple_candidates` (L463), `test_box_overlap_prune_detects_high_overlap` (L476), `test_latest_daily_vwap_computation` (L484), `_cost_strategy` (L510), `test_grid_sizing_reduces_n_to_meet_cost_floor` (L542), `test_effective_cost_floor_uses_empirical_and_emits_stale_warning` (L557), `test_effective_cost_floor_switches_to_empirical_when_higher` (L565), `test_effective_cost_floor_proxy_only_samples_do_not_promote_empirical` (L586), `test_effective_cost_floor_promotes_with_empirical_artifact` (L609), `test_tp_selection_prefers_nearest_conservative` (L659), `test_sl_selection_avoids_lvn_and_fvg_gap` (L675), `test_simulator_fill_guard_respects_no_repeat_toggle` (L690), `test_executor_fill_guard_respects_no_repeat_toggle` (L703), `test_executor_fill_bar_index_tracks_plan_clock` (L715), `test_meta_drift_guard_detects_hard_shift` (L734), `test_meta_drift_state_maps_to_actions` (L778), `test_empirical_cost_sample_uses_execution_cost_artifact` (L852), `test_decision_and_event_logs_are_emitted_with_schema` (L896)
- Classes: 0

### `freqtrade/user_data/tests/test_replay_golden_consistency.py`

- Top-level functions: 4
  - `_build_df` (L8), `_plan` (L21), `test_replay_golden_summary_contract_is_strict` (L63), `test_replay_brain_simulator_consistency_trace_matches_plans` (L126)
- Classes: 0

### `freqtrade/user_data/tests/test_stress_replay_standard_validation.py`

- Top-level functions: 3
  - `_replay_df` (L17), `_plan` (L31), `test_stress_replay_standard_validation_summary_contract` (L44)
- Classes: 0

### `freqtrade/user_data/tests/test_tuning_protocol.py`

- Top-level functions: 8
  - `_write_summary` (L12), `_write_manifest` (L85), `_write_registry` (L90), `_write_schema` (L95), `_run_protocol` (L136), `test_tuning_protocol_promotes_candidate_with_passed_gates` (L164), `test_tuning_protocol_strict_fails_when_chaos_gate_fails` (L325), `test_tuning_protocol_strict_fails_when_required_ablation_missing` (L456)
- Classes: 0

### `freqtrade_cli.py`

- Top-level functions: 3
  - `_is_repo_module` (L10), `_prime_repo_package` (L23), `main` (L51)
- Classes: 0

### `io/__init__.py`

- Top-level functions: 0
- Classes: 0

### `io/atomic_json.py`

- Top-level functions: 0
- Classes: 0

### `planner/__init__.py`

- Top-level functions: 0
- Classes: 0

### `planner/replan_policy.py`

- Top-level functions: 1
  - `evaluate_replan_materiality` (L18)
- Classes: 1
  - `ReplanThresholds` (L10): attrs=5, methods=0
    - attrs: `epoch_bars` (L11), `box_mid_shift_max_step_frac` (L12), `box_width_change_pct` (L13), `tp_shift_max_step_frac` (L14), `sl_shift_max_step_frac` (L15)

### `planner/start_stability.py`

- Top-level functions: 1
  - `evaluate_start_stability` (L9)
- Classes: 0

### `planner/structure/__init__.py`

- Top-level functions: 0
- Classes: 0

### `planner/structure/liquidity_sweeps.py`

- Top-level functions: 4
  - `_atr` (L26), `_buffer_value` (L43), `_confirmed_pivot_indices` (L64), `analyze_liquidity_sweeps` (L90)
- Classes: 1
  - `LiquiditySweepConfig` (L12): attrs=11, methods=0
    - attrs: `enabled` (L13), `pivot_len` (L14), `max_age_bars` (L15), `break_buffer_mode` (L16), `break_buffer_value` (L17), `retest_window_bars` (L18), `retest_buffer_mode` (L19), `retest_buffer_value` (L20), `stop_if_through_box_edge` (L21), `retest_validation_mode` (L22), `min_level_separation_steps` (L23)

### `planner/structure/order_blocks.py`

- Top-level functions: 8
  - `_atr` (L81), `_row_ts_seconds` (L95), `_extract_ts_series` (L109), `_zone_bounds` (L115), `_is_impulse_match` (L129), `_detect_latest_block_for_side` (L145), `_age_gated_block` (L245), `build_order_block_snapshot` (L263)
- Classes: 3
  - `OrderBlock` (L15): attrs=8, methods=0
    - attrs: `side` (L16), `tf` (L17), `created_ts` (L18), `top` (L19), `bottom` (L20), `mid` (L21), `mitigated` (L22), `last_mitigated_ts` (L23)
  - `OrderBlockConfig` (L27): attrs=9, methods=0
    - attrs: `enabled` (L28), `tf` (L29), `use_wick_zone` (L30), `impulse_lookahead` (L31), `impulse_atr_len` (L32), `impulse_atr_mult` (L33), `fresh_bars` (L34), `max_age_bars` (L35), `mitigation_mode` (L36)
  - `OrderBlockSnapshot` (L40): attrs=8, methods=1
    - attrs: `bull` (L41), `bear` (L42), `bull_age_bars` (L43), `bear_age_bars` (L44), `bull_fresh` (L45), `bear_fresh` (L46), `bull_valid` (L47), `bear_valid` (L48)
    - methods: `as_dict` (L50)

### `planner/volatility_policy_adapter.py`

- Top-level functions: 6
  - `_clip` (L11), `_safe_float` (L15), `_atr_bucket` (L27), `_bbwp_bucket` (L43), `compute_volatility_policy_view` (L64), `compute_n_level_bounds` (L258)
- Classes: 0

### `risk/__init__.py`

- Top-level functions: 0
- Classes: 0

### `risk/meta_drift_guard.py`

- Top-level functions: 1
  - `_safe_float` (L9)
- Classes: 1
  - `MetaDriftGuard` (L25): attrs=0, methods=4
    - methods: `__init__` (L28), `reset_pair` (L33), `_pair_state` (L36), `observe` (L46)

### `sim/__init__.py`

- Top-level functions: 0
- Classes: 0

### `sim/chaos_profiles.py`

- Top-level functions: 3
  - `default_chaos_profile` (L10), `validate_chaos_profile` (L30), `load_chaos_profile` (L34)
- Classes: 0

## 5) Schema Contract Inventory

- `schemas/chaos_profile.schema.json`: title=`Chaos Replay Profile`, type=`object`, required=10, properties=16
- `schemas/decision_log.schema.json`: title=`Planner Decision Log Row`, type=`object`, required=17, properties=17
- `schemas/event_log.schema.json`: title=`Event Log Row`, type=`object`, required=9, properties=9
- `schemas/execution_cost_calibration.schema.json`: title=`Execution Cost Calibration Artifact`, type=`object`, required=12, properties=14
- `schemas/grid_plan.schema.json`: title=`Grid Plan`, type=`object`, required=29, properties=31

## 6) Unit Test Inventory (`freqtrade/user_data/tests`)

- `freqtrade/user_data/tests/test_chaos_replay_harness.py`: 4 tests
  - `test_chaos_profile_is_deterministic_and_reports_delta`, `test_chaos_partial_fill_profile_marks_partial_fills`, `test_chaos_data_gap_profile_drops_candles`, `test_chaos_fault_injection_profiles_trigger_expected_rails`
- `freqtrade/user_data/tests/test_executor_hardening.py`: 10 tests
  - `test_ccxt_place_limit_retries_post_only_with_backoff_and_reprice`, `test_reject_burst_blocks_start_and_downgrades_to_hold`, `test_stop_exit_confirm_uses_failsafe_reason`, `test_rebuild_confirm_failure_is_tracked_separately`, `test_reconcile_matches_live_orders_with_tolerance`, `test_reconcile_honors_action_cap`, `test_executor_recovers_state_file_on_startup`, `test_capacity_rung_cap_limits_seeded_orders_in_paper`, `test_capacity_hard_block_prevents_start`, `test_execution_cost_feedback_writes_artifact_and_lifecycle_logs`
- `freqtrade/user_data/tests/test_liquidity_sweeps.py`: 4 tests
  - `test_pivot_confirmation_is_bar_confirmed`, `test_wick_sweep_and_break_retest_stop_through_box_edge`, `test_retest_validation_mode_toggle_affects_break_retest_only`, `test_determinism_for_same_inputs`
- `freqtrade/user_data/tests/test_meta_drift_replay.py`: 1 tests
  - `test_replay_synthetic_regime_shift_tracks_meta_drift_soft_and_hard`
- `freqtrade/user_data/tests/test_min_range_and_breakout_confirm.py`: 8 tests
  - `test_min_range_len_gate_blocks_before_threshold`, `test_min_range_len_gate_passes_at_threshold`, `test_min_range_len_gate_resets_on_new_box_generation`, `test_breakout_confirm_single_close_outside_is_not_confirmed`, `test_breakout_confirm_up_blocks_start_when_not_running`, `test_breakout_confirm_dn_stops_when_running`, `test_breakout_confirm_buffer_modes`, `test_breakout_confirm_determinism_on_same_input`
- `freqtrade/user_data/tests/test_ml_overlay_step14.py`: 3 tests
  - `test_step14_ml_scripts_pipeline`, `test_tuning_protocol_respects_required_ml_overlay_gate`, `test_ml_overlay_defaults_are_advisory_and_off`
- `freqtrade/user_data/tests/test_order_blocks.py`: 3 tests
  - `test_order_block_detects_bull_and_mitigation`, `test_order_block_detects_bear_and_freshness_window`, `test_order_block_strategy_state_applies_fresh_gate_straddle_and_tp_nudges`
- `freqtrade/user_data/tests/test_partial_module_completion.py`: 4 tests
  - `test_protections_drawdown_and_stop_window_helpers`, `test_micro_bias_order_flow_and_reentry_helpers`, `test_fvg_vp_channel_and_session_sweep_helpers`, `test_event_bus_emits_reason_and_taxonomy_events`
- `freqtrade/user_data/tests/test_phase3_validation.py`: 46 tests
  - `test_box_signature_is_repeatable`, `test_poc_cross_detected_when_open_close_bracket_value`, `test_derive_box_block_reasons_reflects_conflicts`, `test_poc_acceptance_status_persists_once_crossed`, `test_data_quality_checks_flag_gap`, `test_data_quality_checks_flag_duplicates`, `test_data_quality_checks_zero_volume_streak`, `test_phase2_gate_failures_records_block_reasons`, `test_start_block_reasons_include_baseline_codes`, `test_start_block_reasons_include_breakout_block`, `test_materiality_waits_for_epoch_or_delta`, `test_compute_band_slope_pct_respects_window`, `test_excursion_asymmetry_ratio_handles_invalid_devs`, `test_funding_gate_honors_threshold`, `test_box_straddle_breakout_detection_adds_blocker`, `test_squeeze_release_block_reason_is_consumed`, `test_bbw_nonexpanding_gate_requires_flat_or_contracting_window`, `test_breakout_fresh_state_blocks_until_reclaimed`, `test_detect_structural_breakout_uses_close_vs_prior_extremes`, `test_hvp_stats_returns_current_and_sma`, `test_planner_health_state_transitions`, `test_start_stability_state_supports_k_of_n_and_score`, `test_box_quality_metrics_and_straddle_helpers`, `test_box_quality_levels_linear_fallback_when_nonpositive_bounds`, `test_midline_bias_fallback_activates_when_vrvp_poc_is_neutral`, `test_midline_bias_fallback_stays_inactive_when_vrvp_poc_not_neutral`, `test_fallback_poc_estimate_uses_volume_weighted_typical_price`, `test_box_width_avg_veto_triggers_when_width_exceeds_rolling_ratio`, `test_poc_alignment_strict_requires_cross_when_misaligned`, `test_poc_acceptance_handles_multiple_candidates`, `test_box_overlap_prune_detects_high_overlap`, `test_latest_daily_vwap_computation`, `test_grid_sizing_reduces_n_to_meet_cost_floor`, `test_effective_cost_floor_uses_empirical_and_emits_stale_warning`, `test_effective_cost_floor_switches_to_empirical_when_higher`, `test_effective_cost_floor_proxy_only_samples_do_not_promote_empirical`, `test_effective_cost_floor_promotes_with_empirical_artifact`, `test_tp_selection_prefers_nearest_conservative`, `test_sl_selection_avoids_lvn_and_fvg_gap`, `test_simulator_fill_guard_respects_no_repeat_toggle`, `test_executor_fill_guard_respects_no_repeat_toggle`, `test_executor_fill_bar_index_tracks_plan_clock`, `test_meta_drift_guard_detects_hard_shift`, `test_meta_drift_state_maps_to_actions`, `test_empirical_cost_sample_uses_execution_cost_artifact`, `test_decision_and_event_logs_are_emitted_with_schema`
- `freqtrade/user_data/tests/test_replay_golden_consistency.py`: 2 tests
  - `test_replay_golden_summary_contract_is_strict`, `test_replay_brain_simulator_consistency_trace_matches_plans`
- `freqtrade/user_data/tests/test_stress_replay_standard_validation.py`: 1 tests
  - `test_stress_replay_standard_validation_summary_contract`
- `freqtrade/user_data/tests/test_tuning_protocol.py`: 3 tests
  - `test_tuning_protocol_promotes_candidate_with_passed_gates`, `test_tuning_protocol_strict_fails_when_chaos_gate_fails`, `test_tuning_protocol_strict_fails_when_required_ablation_missing`

## 7) Registry-Only Canonical Codes (No Runtime Reference Detected)

- These are defined in enums but not referenced in runtime source scan. Keep/remove should be decided explicitly.

- `BLOCK_BOX_DONCHIAN_WIDTH_SANITY` (BlockReason.BLOCK_BOX_DONCHIAN_WIDTH_SANITY)
- `BLOCK_BOX_STRADDLE_HTF_POC` (BlockReason.BLOCK_BOX_STRADDLE_HTF_POC)
- `BLOCK_BOX_WIDTH_TOO_NARROW` (BlockReason.BLOCK_BOX_WIDTH_TOO_NARROW)
- `BLOCK_BREAKOUT_RECLAIM_PENDING` (BlockReason.BLOCK_BREAKOUT_RECLAIM_PENDING)
- `BLOCK_DATA_DUPLICATE_TS` (BlockReason.BLOCK_DATA_DUPLICATE_TS)
- `BLOCK_DATA_NON_MONOTONIC_TS` (BlockReason.BLOCK_DATA_NON_MONOTONIC_TS)
- `BLOCK_EXEC_CONFIRM_REBUILD_FAILED` (BlockReason.BLOCK_EXEC_CONFIRM_REBUILD_FAILED)
- `BLOCK_EXEC_CONFIRM_START_FAILED` (BlockReason.BLOCK_EXEC_CONFIRM_START_FAILED)
- `BLOCK_FRESH_FVG_COOLOFF` (BlockReason.BLOCK_FRESH_FVG_COOLOFF)
- `BLOCK_INSIDE_SESSION_FVG` (BlockReason.BLOCK_INSIDE_SESSION_FVG)
- `BLOCK_MIN_RUNTIME_NOT_MET` (BlockReason.BLOCK_MIN_RUNTIME_NOT_MET)
- `BLOCK_MRVD_CONFLUENCE_FAIL` (BlockReason.BLOCK_MRVD_CONFLUENCE_FAIL)
- `BLOCK_MRVD_POC_DRIFT_GUARD` (BlockReason.BLOCK_MRVD_POC_DRIFT_GUARD)
- `BLOCK_N_LEVELS_INVALID` (BlockReason.BLOCK_N_LEVELS_INVALID)
- `BLOCK_SESSION_FVG_PAUSE` (BlockReason.BLOCK_SESSION_FVG_PAUSE)
- `BLOCK_START_CONFLUENCE_LOW` (BlockReason.BLOCK_START_CONFLUENCE_LOW)
- `EVENT_BBWP_EXTREME` (EventType.EVENT_BBWP_EXTREME)
- `EVENT_CVD_SPIKE_NEG` (EventType.EVENT_CVD_SPIKE_NEG)
- `EVENT_CVD_SPIKE_POS` (EventType.EVENT_CVD_SPIKE_POS)
- `EVENT_DRIFT_RETEST_DN` (EventType.EVENT_DRIFT_RETEST_DN)
- `EVENT_DRIFT_RETEST_UP` (EventType.EVENT_DRIFT_RETEST_UP)
- `EVENT_EXTREME_RETEST_BOTTOM` (EventType.EVENT_EXTREME_RETEST_BOTTOM)
- `EVENT_EXTREME_RETEST_TOP` (EventType.EVENT_EXTREME_RETEST_TOP)
- `EVENT_EXT_1386_RETEST_BOTTOM` (EventType.EVENT_EXT_1386_RETEST_BOTTOM)
- `EVENT_EXT_1386_RETEST_TOP` (EventType.EVENT_EXT_1386_RETEST_TOP)
- `EVENT_FVG_MITIGATED_BEAR` (EventType.EVENT_FVG_MITIGATED_BEAR)
- `EVENT_FVG_MITIGATED_BULL` (EventType.EVENT_FVG_MITIGATED_BULL)
- `EVENT_FVG_NEW_BEAR` (EventType.EVENT_FVG_NEW_BEAR)
- `EVENT_FVG_NEW_BULL` (EventType.EVENT_FVG_NEW_BULL)
- `EVENT_IMFVG_AVG_TAG_BEAR` (EventType.EVENT_IMFVG_AVG_TAG_BEAR)
- `EVENT_IMFVG_AVG_TAG_BULL` (EventType.EVENT_IMFVG_AVG_TAG_BULL)
- `EVENT_PASSIVE_ABSORPTION_DN` (EventType.EVENT_PASSIVE_ABSORPTION_DN)
- `EVENT_PASSIVE_ABSORPTION_UP` (EventType.EVENT_PASSIVE_ABSORPTION_UP)
- `EVENT_POC_ACCEPTANCE_CROSS` (EventType.EVENT_POC_ACCEPTANCE_CROSS)
- `EVENT_POC_TEST` (EventType.EVENT_POC_TEST)
- `EVENT_RANGE_HIT_BOTTOM` (EventType.EVENT_RANGE_HIT_BOTTOM)
- `EVENT_RANGE_HIT_TOP` (EventType.EVENT_RANGE_HIT_TOP)
- `EVENT_RECLAIM_CONFIRMED` (EventType.EVENT_RECLAIM_CONFIRMED)
- `EVENT_SESSION_FVG_MITIGATED` (EventType.EVENT_SESSION_FVG_MITIGATED)
- `EVENT_SESSION_FVG_NEW` (EventType.EVENT_SESSION_FVG_NEW)
- `EVENT_SQUEEZE_RELEASE_DN` (EventType.EVENT_SQUEEZE_RELEASE_DN)
- `EVENT_SQUEEZE_RELEASE_UP` (EventType.EVENT_SQUEEZE_RELEASE_UP)
- `STOP_BREAKOUT_2STRIKE_DN` (StopReason.STOP_BREAKOUT_2STRIKE_DN)
- `STOP_BREAKOUT_2STRIKE_UP` (StopReason.STOP_BREAKOUT_2STRIKE_UP)
- `STOP_DATA_QUARANTINE` (StopReason.STOP_DATA_QUARANTINE)
- `STOP_FAST_MOVE_DN` (StopReason.STOP_FAST_MOVE_DN)
- `STOP_FAST_MOVE_UP` (StopReason.STOP_FAST_MOVE_UP)
- `STOP_FRESH_STRUCTURE` (StopReason.STOP_FRESH_STRUCTURE)
- `STOP_LVN_VOID_EXIT_ACCEL` (StopReason.STOP_LVN_VOID_EXIT_ACCEL)
- `STOP_MRVD_AVG_BREAK` (StopReason.STOP_MRVD_AVG_BREAK)
- `STOP_OS_DEV_DIRECTIONAL_FLIP` (StopReason.STOP_OS_DEV_DIRECTIONAL_FLIP)
- `STOP_RANGE_SHIFT` (StopReason.STOP_RANGE_SHIFT)
- `STOP_SESSION_FVG_AGAINST_BIAS` (StopReason.STOP_SESSION_FVG_AGAINST_BIAS)
- `STOP_SQUEEZE_RELEASE_AGAINST` (StopReason.STOP_SQUEEZE_RELEASE_AGAINST)
- `WARN_CVD_DATA_QUALITY_LOW` (WarningCode.WARN_CVD_DATA_QUALITY_LOW)
- `WARN_EXEC_REPRICE_RATE_HIGH` (WarningCode.WARN_EXEC_REPRICE_RATE_HIGH)
- `WARN_FEATURE_FALLBACK_USED` (WarningCode.WARN_FEATURE_FALLBACK_USED)
- `WARN_PARTIAL_DATA_WINDOW` (WarningCode.WARN_PARTIAL_DATA_WINDOW)
- `WARN_PLAN_EXPIRES_SOON` (WarningCode.WARN_PLAN_EXPIRES_SOON)

## 8) Notes for Plan Merge in Browser ChatGPT

- Use this file as code-ground truth, then diff it against old and current plan versions.
- Treat `REGISTRY_ONLY` as “not implemented in runtime unless separate evidence exists”.
- Prioritize features that have both runtime wiring and unit/replay tests.
