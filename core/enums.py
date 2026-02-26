"""
Canonical enums for planner / simulator / executor reason and event codes.

This file mirrors `docs/DECISION_REASON_CODES.md`.

Rules:
- Do not invent ad-hoc strings in code.
- If you add a new code here, also update the docs file.
- Keep semantics stable; prefer adding new codes over changing existing meaning.
"""

from __future__ import annotations

from enum import Enum, unique
from typing import Iterable, Optional, Union


class StrEnum(str, Enum):
    """Py3.10+ compatible string enum base (without requiring enum.StrEnum)."""

    def __str__(self) -> str:
        return self.value

    @classmethod
    def values(cls) -> list[str]:
        return [m.value for m in cls]

    @classmethod
    def has_value(cls, value: str) -> bool:
        return value in cls._value2member_map_  # type: ignore[attr-defined]


@unique
class Severity(StrEnum):
    HARD = "hard"
    SOFT = "soft"
    ADVISORY = "advisory"
    INFO = "info"


@unique
class ActionContext(StrEnum):
    START = "START"
    HOLD = "HOLD"
    STOP = "STOP"
    REBUILD = "REBUILD"
    NOOP = "NOOP"


@unique
class MaterialityClass(StrEnum):
    NOOP = "noop"
    SOFT = "soft"
    MATERIAL = "material"
    HARDSTOP = "hardstop"


@unique
class PlannerHealthState(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    QUARANTINE = "quarantine"


@unique
class ModuleName(StrEnum):
    # Core/data/pipeline
    DATA_LOADER = "data_loader"
    DATA_QUALITY_MONITOR = "data_quality_monitor"
    MTF_MERGE_INTEGRITY = "mtf_merge_integrity"
    FEATURE_PIPELINE = "feature_pipeline"

    # Phase-2 / regime gates
    ADX_GATE = "adx_gate"
    BBW_QUIETNESS_GATE = "bbw_quietness_gate"
    EMA_COMPRESSION_GATE = "ema_compression_gate"
    RVOL_GATE = "rvol_gate"
    CONTEXT_7D_GATE = "context_7d_gate"
    BREAKOUT_FRESH_BLOCK = "breakout_fresh_block"
    BREAKOUT_RECLAIM_TIMER = "breakout_reclaim_timer"
    RANGE_DI_OS_DEV = "range_di_os_dev"
    BAND_SLOPE_VETO = "band_slope_veto"
    DRIFT_SLOPE_VETO = "drift_slope_veto"
    EXCURSION_ASYMMETRY_VETO = "excursion_asymmetry_veto"
    META_DRIFT_GUARD = "meta_drift_guard"
    BBWP_MTF_GATE = "bbwp_mtf_gate"
    SQUEEZE_STATE_GATE = "squeeze_state_gate"
    VOLATILITY_POLICY_ADAPTER = "volatility_policy_adapter"

    # Phase-3 / box / profiles
    BOX_BUILDER = "box_builder"
    BOX_STRADDLE_VETO = "box_straddle_veto"
    VRVP = "vrvp"
    MICRO_VAP = "micro_vap"
    MRVD = "mrvd"
    BASIS_PIVOTS = "basis_pivots"
    DONCHIAN = "donchian"
    CHANNEL_MODULE = "channel_module"

    # Structure modules
    OB_MODULE = "ob_module"
    FVG_MODULE = "fvg_module"
    IMFVG_MODULE = "imfvg_module"
    SESSION_FVG = "session_fvg"
    FVG_POSITIONING_AVG = "fvg_positioning_avg"
    FVG_VP = "fvg_vp"
    LIQUIDITY_SWEEPS = "liquidity_sweeps"

    # Phase-4 / sizing/risk
    POC_ACCEPTANCE_GATE = "poc_acceptance_gate"
    START_STABILITY = "start_stability"
    CONFLUENCE_AGGREGATOR = "confluence_aggregator"
    COST_MODEL = "cost_model"
    EMPIRICAL_COST_CALIBRATOR = "empirical_cost_calibrator"
    N_LEVEL_SELECTION = "n_level_selection"
    TARGET_SELECTOR = "target_selector"
    SL_SELECTOR = "sl_selector"

    # Phase-5 / protections / replan
    STOP_FRAMEWORK = "stop_framework"
    RECLAIM_DISCIPLINE = "reclaim_discipline"
    PROTECTIONS = "protections"
    REPLAN_POLICY = "replan_policy"
    PLAN_ATOMIC_HANDOFF = "plan_atomic_handoff"

    # Executor/runtime
    EXECUTOR = "executor"
    CAPACITY_GUARD = "capacity_guard"
    CONFIRM_ENTRY_HOOK = "confirm_entry_hook"
    CONFIRM_REBUILD_HOOK = "confirm_rebuild_hook"
    CONFIRM_EXIT_HOOK = "confirm_exit_hook"
    MAKER_FIRST_EXECUTION = "maker_first_execution"
    RECONCILE_ENGINE = "reconcile_engine"
    FILL_DEDUPE_GUARD = "fill_dedupe_guard"

    # Flow / optional signals
    CVD_MODULE = "cvd_module"
    HVP_GATE = "hvp_gate"


# =========================
# A) BLOCK_* (start/rebuild blockers)
# =========================
@unique
class BlockReason(StrEnum):
    # A.1 Core Regime / Quietness Gates
    BLOCK_ADX_HIGH = "BLOCK_ADX_HIGH"
    BLOCK_BBW_EXPANDING = "BLOCK_BBW_EXPANDING"
    BLOCK_EMA_DIST = "BLOCK_EMA_DIST"
    BLOCK_RVOL_SPIKE = "BLOCK_RVOL_SPIKE"
    BLOCK_7D_EXTREME_CONTEXT = "BLOCK_7D_EXTREME_CONTEXT"

    # A.2 Structural Breakout / Drift / Regime State
    BLOCK_FRESH_BREAKOUT = "BLOCK_FRESH_BREAKOUT"
    BLOCK_BREAKOUT_RECLAIM_PENDING = "BLOCK_BREAKOUT_RECLAIM_PENDING"
    BLOCK_BREAKOUT_CONFIRM_UP = "BLOCK_BREAKOUT_CONFIRM_UP"
    BLOCK_BREAKOUT_CONFIRM_DN = "BLOCK_BREAKOUT_CONFIRM_DN"
    BLOCK_MIN_RANGE_LEN_NOT_MET = "BLOCK_MIN_RANGE_LEN_NOT_MET"
    BLOCK_OS_DEV_DIRECTIONAL = "BLOCK_OS_DEV_DIRECTIONAL"
    BLOCK_OS_DEV_NEUTRAL_PERSISTENCE = "BLOCK_OS_DEV_NEUTRAL_PERSISTENCE"
    BLOCK_BAND_SLOPE_HIGH = "BLOCK_BAND_SLOPE_HIGH"
    BLOCK_DRIFT_SLOPE_HIGH = "BLOCK_DRIFT_SLOPE_HIGH"
    BLOCK_EXCURSION_ASYMMETRY = "BLOCK_EXCURSION_ASYMMETRY"
    BLOCK_META_DRIFT_SOFT = "BLOCK_META_DRIFT_SOFT"

    # A.3 Volatility Regime / BBWP / Squeeze
    BLOCK_BBWP_HIGH = "BLOCK_BBWP_HIGH"
    COOLOFF_BBWP_EXTREME = "COOLOFF_BBWP_EXTREME"
    BLOCK_FUNDING_FILTER = "BLOCK_FUNDING_FILTER"
    BLOCK_SQUEEZE_RELEASE_AGAINST_BIAS = "BLOCK_SQUEEZE_RELEASE_AGAINST_BIAS"
    BLOCK_VOL_BUCKET_UNSTABLE = "BLOCK_VOL_BUCKET_UNSTABLE"

    # A.4 Box Builder Integrity / Width / Straddle
    BLOCK_BOX_WIDTH_TOO_NARROW = "BLOCK_BOX_WIDTH_TOO_NARROW"
    BLOCK_BOX_WIDTH_TOO_WIDE = "BLOCK_BOX_WIDTH_TOO_WIDE"
    BLOCK_BOX_STRADDLE_BREAKOUT_LEVEL = "BLOCK_BOX_STRADDLE_BREAKOUT_LEVEL"
    BLOCK_BOX_STRADDLE_OB_EDGE = "BLOCK_BOX_STRADDLE_OB_EDGE"
    BLOCK_BOX_STRADDLE_FVG_EDGE = "BLOCK_BOX_STRADDLE_FVG_EDGE"
    BLOCK_BOX_STRADDLE_FVG_AVG = "BLOCK_BOX_STRADDLE_FVG_AVG"
    BLOCK_BOX_STRADDLE_SESSION_FVG_AVG = "BLOCK_BOX_STRADDLE_SESSION_FVG_AVG"
    BLOCK_BOX_OVERLAP_HIGH = "BLOCK_BOX_OVERLAP_HIGH"
    BLOCK_BOX_ENVELOPE_RATIO_HIGH = "BLOCK_BOX_ENVELOPE_RATIO_HIGH"
    BLOCK_BOX_STRADDLE_HTF_POC = "BLOCK_BOX_STRADDLE_HTF_POC"
    BLOCK_BOX_STRADDLE_VWAP_DONCHIAN_MID = "BLOCK_BOX_STRADDLE_VWAP_DONCHIAN_MID"
    BLOCK_BOX_VP_POC_MISPLACED = "BLOCK_BOX_VP_POC_MISPLACED"
    BLOCK_BOX_CHANNEL_OVERLAP_LOW = "BLOCK_BOX_CHANNEL_OVERLAP_LOW"
    BLOCK_BOX_DONCHIAN_WIDTH_SANITY = "BLOCK_BOX_DONCHIAN_WIDTH_SANITY"

    # A.5 Acceptance / Confluence / Start Eligibility
    BLOCK_NO_POC_ACCEPTANCE = "BLOCK_NO_POC_ACCEPTANCE"
    BLOCK_POC_ALIGNMENT_FAIL = "BLOCK_POC_ALIGNMENT_FAIL"
    BLOCK_START_BOX_POSITION = "BLOCK_START_BOX_POSITION"
    BLOCK_START_RSI_BAND = "BLOCK_START_RSI_BAND"
    BLOCK_START_CONFLUENCE_LOW = "BLOCK_START_CONFLUENCE_LOW"
    BLOCK_START_STABILITY_LOW = "BLOCK_START_STABILITY_LOW"
    BLOCK_START_PERSISTENCE_FAIL = "BLOCK_START_PERSISTENCE_FAIL"
    BLOCK_BASIS_CROSS_PENDING = "BLOCK_BASIS_CROSS_PENDING"
    BLOCK_VAH_VAL_POC_PROXIMITY = "BLOCK_VAH_VAL_POC_PROXIMITY"
    BLOCK_MRVD_CONFLUENCE_FAIL = "BLOCK_MRVD_CONFLUENCE_FAIL"
    BLOCK_MRVD_POC_DRIFT_GUARD = "BLOCK_MRVD_POC_DRIFT_GUARD"

    # A.6 Cost / Sizing / Capacity / Execution-Aware Start Blocks
    BLOCK_STEP_BELOW_COST = "BLOCK_STEP_BELOW_COST"
    BLOCK_STEP_BELOW_EMPIRICAL_COST = "BLOCK_STEP_BELOW_EMPIRICAL_COST"
    BLOCK_N_LEVELS_INVALID = "BLOCK_N_LEVELS_INVALID"
    BLOCK_CAPACITY_THIN = "BLOCK_CAPACITY_THIN"
    BLOCK_EXEC_CONFIRM_START_FAILED = "BLOCK_EXEC_CONFIRM_START_FAILED"
    BLOCK_EXEC_CONFIRM_REBUILD_FAILED = "BLOCK_EXEC_CONFIRM_REBUILD_FAILED"

    # A.7 Cooldown / Reclaim / Runtime Rails
    BLOCK_RECLAIM_PENDING = "BLOCK_RECLAIM_PENDING"
    BLOCK_RECLAIM_NOT_CONFIRMED = "BLOCK_RECLAIM_NOT_CONFIRMED"
    BLOCK_COOLDOWN_ACTIVE = "BLOCK_COOLDOWN_ACTIVE"
    BLOCK_MIN_RUNTIME_NOT_MET = "BLOCK_MIN_RUNTIME_NOT_MET"
    BLOCK_DRAWDOWN_GUARD = "BLOCK_DRAWDOWN_GUARD"
    BLOCK_MAX_STOPS_WINDOW = "BLOCK_MAX_STOPS_WINDOW"

    # A.8 Data Quality / Health State Blocks
    BLOCK_DATA_GAP = "BLOCK_DATA_GAP"
    BLOCK_DATA_DUPLICATE_TS = "BLOCK_DATA_DUPLICATE_TS"
    BLOCK_DATA_NON_MONOTONIC_TS = "BLOCK_DATA_NON_MONOTONIC_TS"
    BLOCK_DATA_MISALIGN = "BLOCK_DATA_MISALIGN"
    BLOCK_ZERO_VOL_ANOMALY = "BLOCK_ZERO_VOL_ANOMALY"
    BLOCK_STALE_FEATURES = "BLOCK_STALE_FEATURES"

    # A.9 Module-Specific / Optional Advisory-to-Hard Blocks
    BLOCK_FRESH_OB_COOLOFF = "BLOCK_FRESH_OB_COOLOFF"
    BLOCK_FRESH_FVG_COOLOFF = "BLOCK_FRESH_FVG_COOLOFF"
    BLOCK_SESSION_FVG_PAUSE = "BLOCK_SESSION_FVG_PAUSE"
    BLOCK_INSIDE_SESSION_FVG = "BLOCK_INSIDE_SESSION_FVG"
    BLOCK_HVP_EXPANDING = "BLOCK_HVP_EXPANDING"
    BLOCK_LIQ_SWEEP_OPPOSITE_STRUCTURE = "BLOCK_LIQ_SWEEP_OPPOSITE_STRUCTURE"


# =========================
# B) STOP_*
# =========================
@unique
class StopReason(StrEnum):
    # B.1 Core Breakout / Fast Move / Range Shift
    STOP_BREAKOUT_2STRIKE_UP = "STOP_BREAKOUT_2STRIKE_UP"
    STOP_BREAKOUT_2STRIKE_DN = "STOP_BREAKOUT_2STRIKE_DN"
    STOP_BREAKOUT_CONFIRM_UP = "STOP_BREAKOUT_CONFIRM_UP"
    STOP_BREAKOUT_CONFIRM_DN = "STOP_BREAKOUT_CONFIRM_DN"
    STOP_FAST_MOVE_UP = "STOP_FAST_MOVE_UP"
    STOP_FAST_MOVE_DN = "STOP_FAST_MOVE_DN"
    STOP_RANGE_SHIFT = "STOP_RANGE_SHIFT"
    STOP_FRESH_STRUCTURE = "STOP_FRESH_STRUCTURE"

    # B.2 Squeeze / Channel / Regime-Driven Overrides
    STOP_SQUEEZE_RELEASE_AGAINST = "STOP_SQUEEZE_RELEASE_AGAINST"
    STOP_CHANNEL_STRONG_BREAK = "STOP_CHANNEL_STRONG_BREAK"
    STOP_OS_DEV_DIRECTIONAL_FLIP = "STOP_OS_DEV_DIRECTIONAL_FLIP"
    STOP_META_DRIFT_HARD = "STOP_META_DRIFT_HARD"

    # B.3 Structure / VAP / Void / Liquidity-Based Stops
    STOP_LVN_VOID_EXIT_ACCEL = "STOP_LVN_VOID_EXIT_ACCEL"
    STOP_FVG_VOID_CONFLUENCE = "STOP_FVG_VOID_CONFLUENCE"
    STOP_LIQUIDITY_SWEEP_BREAK_RETEST = "STOP_LIQUIDITY_SWEEP_BREAK_RETEST"
    STOP_SESSION_FVG_AGAINST_BIAS = "STOP_SESSION_FVG_AGAINST_BIAS"
    STOP_MRVD_AVG_BREAK = "STOP_MRVD_AVG_BREAK"

    # B.4 Protections / Risk / Execution Stops
    STOP_DRAWDOWN_GUARD = "STOP_DRAWDOWN_GUARD"
    STOP_EXEC_CONFIRM_EXIT_FAILSAFE = "STOP_EXEC_CONFIRM_EXIT_FAILSAFE"
    STOP_DATA_QUARANTINE = "STOP_DATA_QUARANTINE"


# =========================
# C) REPLAN_*
# =========================
@unique
class ReplanReason(StrEnum):
    # C.1 Primary Replan Outcomes
    REPLAN_NOOP_MINOR_DELTA = "REPLAN_NOOP_MINOR_DELTA"
    REPLAN_SOFT_ADJUST_ONLY = "REPLAN_SOFT_ADJUST_ONLY"
    REPLAN_MATERIAL_BOX_CHANGE = "REPLAN_MATERIAL_BOX_CHANGE"
    REPLAN_MATERIAL_GRID_CHANGE = "REPLAN_MATERIAL_GRID_CHANGE"
    REPLAN_MATERIAL_RISK_CHANGE = "REPLAN_MATERIAL_RISK_CHANGE"
    REPLAN_HARD_STOP_OVERRIDE = "REPLAN_HARD_STOP_OVERRIDE"

    # C.2 Replan Timing / Epoch / Idempotency Context
    REPLAN_EPOCH_DEFERRED = "REPLAN_EPOCH_DEFERRED"
    REPLAN_DEFERRED_ACTIVE_FILL_WINDOW = "REPLAN_DEFERRED_ACTIVE_FILL_WINDOW"
    REPLAN_DUPLICATE_PLAN_HASH = "REPLAN_DUPLICATE_PLAN_HASH"


# =========================
# D) PAUSE_*
# =========================
@unique
class PauseReason(StrEnum):
    PAUSE_DATA_QUARANTINE = "PAUSE_DATA_QUARANTINE"
    PAUSE_DATA_DEGRADED = "PAUSE_DATA_DEGRADED"
    PAUSE_META_DRIFT_SOFT = "PAUSE_META_DRIFT_SOFT"
    PAUSE_BBWP_COOLOFF = "PAUSE_BBWP_COOLOFF"
    PAUSE_SESSION_FVG = "PAUSE_SESSION_FVG"
    PAUSE_EXECUTION_UNSAFE = "PAUSE_EXECUTION_UNSAFE"


# =========================
# E) WARN_*
# =========================
@unique
class WarningCode(StrEnum):
    WARN_COST_MODEL_STALE = "WARN_COST_MODEL_STALE"
    WARN_CVD_DATA_QUALITY_LOW = "WARN_CVD_DATA_QUALITY_LOW"
    WARN_VRVP_UNAVAILABLE_FALLBACK_POC = "WARN_VRVP_UNAVAILABLE_FALLBACK_POC"
    WARN_FEATURE_FALLBACK_USED = "WARN_FEATURE_FALLBACK_USED"
    WARN_EXEC_POST_ONLY_RETRY_HIGH = "WARN_EXEC_POST_ONLY_RETRY_HIGH"
    WARN_EXEC_REPRICE_RATE_HIGH = "WARN_EXEC_REPRICE_RATE_HIGH"
    WARN_PLAN_EXPIRES_SOON = "WARN_PLAN_EXPIRES_SOON"
    WARN_PARTIAL_DATA_WINDOW = "WARN_PARTIAL_DATA_WINDOW"


# =========================
# F) EXEC_*
# =========================
@unique
class ExecCode(StrEnum):
    # F.1 Plan Intake / Idempotency / Schema
    EXEC_PLAN_SCHEMA_INVALID = "EXEC_PLAN_SCHEMA_INVALID"
    EXEC_PLAN_HASH_MISMATCH = "EXEC_PLAN_HASH_MISMATCH"
    EXEC_PLAN_DUPLICATE_IGNORED = "EXEC_PLAN_DUPLICATE_IGNORED"
    EXEC_PLAN_STALE_SEQ_IGNORED = "EXEC_PLAN_STALE_SEQ_IGNORED"
    EXEC_PLAN_EXPIRED_IGNORED = "EXEC_PLAN_EXPIRED_IGNORED"
    EXEC_PLAN_APPLIED = "EXEC_PLAN_APPLIED"

    # F.2 Ladder / Reconcile / Capacity Controls
    EXEC_RECONCILE_START_LADDER_CREATED = "EXEC_RECONCILE_START_LADDER_CREATED"
    EXEC_RECONCILE_HOLD_NO_MATERIAL_CHANGE = "EXEC_RECONCILE_HOLD_NO_MATERIAL_CHANGE"
    EXEC_RECONCILE_MATERIAL_REBUILD = "EXEC_RECONCILE_MATERIAL_REBUILD"
    EXEC_RECONCILE_STOP_CANCELLED_LADDER = "EXEC_RECONCILE_STOP_CANCELLED_LADDER"
    EXEC_CAPACITY_RUNG_CAP_APPLIED = "EXEC_CAPACITY_RUNG_CAP_APPLIED"
    EXEC_CAPACITY_NOTIONAL_CAP_APPLIED = "EXEC_CAPACITY_NOTIONAL_CAP_APPLIED"
    EXEC_CONFIRM_START_FAILED = "EXEC_CONFIRM_START_FAILED"
    EXEC_CONFIRM_REBUILD_FAILED = "EXEC_CONFIRM_REBUILD_FAILED"
    EXEC_CONFIRM_EXIT_FAILSAFE = "EXEC_CONFIRM_EXIT_FAILSAFE"

    # F.3 Maker-First / Placement / Lifecycle
    EXEC_POST_ONLY_RETRY = "EXEC_POST_ONLY_RETRY"
    EXEC_POST_ONLY_FALLBACK_REPRICE = "EXEC_POST_ONLY_FALLBACK_REPRICE"
    EXEC_ORDER_TIMEOUT_REPRICE = "EXEC_ORDER_TIMEOUT_REPRICE"
    EXEC_ORDER_CANCEL_REPLACE_APPLIED = "EXEC_ORDER_CANCEL_REPLACE_APPLIED"
    EXEC_FILL_REPLACEMENT_PLACED = "EXEC_FILL_REPLACEMENT_PLACED"
    EXEC_FILL_DUPLICATE_GUARD_HIT = "EXEC_FILL_DUPLICATE_GUARD_HIT"


# =========================
# G) EVENT_*
# =========================
@unique
class EventType(StrEnum):
    # G.1 Acceptance / Retests / Range Events
    EVENT_POC_TEST = "EVENT_POC_TEST"
    EVENT_POC_ACCEPTANCE_CROSS = "EVENT_POC_ACCEPTANCE_CROSS"
    EVENT_EXTREME_RETEST_TOP = "EVENT_EXTREME_RETEST_TOP"
    EVENT_EXTREME_RETEST_BOTTOM = "EVENT_EXTREME_RETEST_BOTTOM"
    EVENT_EXT_1386_RETEST_TOP = "EVENT_EXT_1386_RETEST_TOP"
    EVENT_EXT_1386_RETEST_BOTTOM = "EVENT_EXT_1386_RETEST_BOTTOM"
    EVENT_RANGE_HIT_TOP = "EVENT_RANGE_HIT_TOP"
    EVENT_RANGE_HIT_BOTTOM = "EVENT_RANGE_HIT_BOTTOM"

    # G.2 Structure Breakouts / Reclaims / Channels
    EVENT_BREAKOUT_BULL = "EVENT_BREAKOUT_BULL"
    EVENT_BREAKOUT_BEAR = "EVENT_BREAKOUT_BEAR"
    EVENT_RECLAIM_CONFIRMED = "EVENT_RECLAIM_CONFIRMED"
    EVENT_CHANNEL_STRONG_BREAK_UP = "EVENT_CHANNEL_STRONG_BREAK_UP"
    EVENT_CHANNEL_STRONG_BREAK_DN = "EVENT_CHANNEL_STRONG_BREAK_DN"
    EVENT_CHANNEL_MIDLINE_TOUCH = "EVENT_CHANNEL_MIDLINE_TOUCH"
    EVENT_DONCHIAN_STRONG_BREAK_UP = "EVENT_DONCHIAN_STRONG_BREAK_UP"
    EVENT_DONCHIAN_STRONG_BREAK_DN = "EVENT_DONCHIAN_STRONG_BREAK_DN"
    EVENT_DRIFT_RETEST_UP = "EVENT_DRIFT_RETEST_UP"
    EVENT_DRIFT_RETEST_DN = "EVENT_DRIFT_RETEST_DN"

    # G.3 Liquidity Sweeps / Session High-Low
    EVENT_SWEEP_WICK_HIGH = "EVENT_SWEEP_WICK_HIGH"
    EVENT_SWEEP_WICK_LOW = "EVENT_SWEEP_WICK_LOW"
    EVENT_SWEEP_BREAK_RETEST_HIGH = "EVENT_SWEEP_BREAK_RETEST_HIGH"
    EVENT_SWEEP_BREAK_RETEST_LOW = "EVENT_SWEEP_BREAK_RETEST_LOW"
    EVENT_SESSION_HIGH_SWEEP = "EVENT_SESSION_HIGH_SWEEP"
    EVENT_SESSION_LOW_SWEEP = "EVENT_SESSION_LOW_SWEEP"

    # G.4 FVG / OB / Session FVG / Mitigation
    EVENT_FVG_NEW_BULL = "EVENT_FVG_NEW_BULL"
    EVENT_FVG_NEW_BEAR = "EVENT_FVG_NEW_BEAR"
    EVENT_FVG_MITIGATED_BULL = "EVENT_FVG_MITIGATED_BULL"
    EVENT_FVG_MITIGATED_BEAR = "EVENT_FVG_MITIGATED_BEAR"
    EVENT_IMFVG_AVG_TAG_BULL = "EVENT_IMFVG_AVG_TAG_BULL"
    EVENT_IMFVG_AVG_TAG_BEAR = "EVENT_IMFVG_AVG_TAG_BEAR"
    EVENT_SESSION_FVG_NEW = "EVENT_SESSION_FVG_NEW"
    EVENT_SESSION_FVG_MITIGATED = "EVENT_SESSION_FVG_MITIGATED"
    EVENT_OB_NEW_BULL = "EVENT_OB_NEW_BULL"
    EVENT_OB_NEW_BEAR = "EVENT_OB_NEW_BEAR"
    EVENT_OB_TAGGED_BULL = "EVENT_OB_TAGGED_BULL"
    EVENT_OB_TAGGED_BEAR = "EVENT_OB_TAGGED_BEAR"

    # G.5 VAP / VP / HVN-LVN / Volume Structure
    EVENT_VRVP_POC_SHIFT = "EVENT_VRVP_POC_SHIFT"
    EVENT_MICRO_POC_SHIFT = "EVENT_MICRO_POC_SHIFT"
    EVENT_HVN_TOUCH = "EVENT_HVN_TOUCH"
    EVENT_LVN_TOUCH = "EVENT_LVN_TOUCH"
    EVENT_LVN_VOID_EXIT = "EVENT_LVN_VOID_EXIT"
    EVENT_FVG_POC_TAG = "EVENT_FVG_POC_TAG"

    # G.6 CVD / Flow / Volatility / Drift
    EVENT_CVD_BULL_DIV = "EVENT_CVD_BULL_DIV"
    EVENT_CVD_BEAR_DIV = "EVENT_CVD_BEAR_DIV"
    EVENT_CVD_BOS_UP = "EVENT_CVD_BOS_UP"
    EVENT_CVD_BOS_DN = "EVENT_CVD_BOS_DN"
    EVENT_CVD_SPIKE_POS = "EVENT_CVD_SPIKE_POS"
    EVENT_CVD_SPIKE_NEG = "EVENT_CVD_SPIKE_NEG"
    EVENT_PASSIVE_ABSORPTION_UP = "EVENT_PASSIVE_ABSORPTION_UP"
    EVENT_PASSIVE_ABSORPTION_DN = "EVENT_PASSIVE_ABSORPTION_DN"
    EVENT_META_DRIFT_SOFT = "EVENT_META_DRIFT_SOFT"
    EVENT_META_DRIFT_HARD = "EVENT_META_DRIFT_HARD"
    EVENT_BBWP_EXTREME = "EVENT_BBWP_EXTREME"
    EVENT_SQUEEZE_RELEASE_UP = "EVENT_SQUEEZE_RELEASE_UP"
    EVENT_SQUEEZE_RELEASE_DN = "EVENT_SQUEEZE_RELEASE_DN"

    # G.7 Execution Safety / Runtime Events
    EVENT_SPREAD_SPIKE = "EVENT_SPREAD_SPIKE"
    EVENT_DEPTH_THIN = "EVENT_DEPTH_THIN"
    EVENT_JUMP_DETECTED = "EVENT_JUMP_DETECTED"
    EVENT_POST_ONLY_REJECT_BURST = "EVENT_POST_ONLY_REJECT_BURST"
    EVENT_DATA_GAP_DETECTED = "EVENT_DATA_GAP_DETECTED"
    EVENT_DATA_MISALIGN_DETECTED = "EVENT_DATA_MISALIGN_DETECTED"


# =========================
# H) INFO_*
# =========================
@unique
class InfoCode(StrEnum):
    INFO_VOL_BUCKET_CHANGED = "INFO_VOL_BUCKET_CHANGED"
    INFO_BOX_SHIFT_APPLIED = "INFO_BOX_SHIFT_APPLIED"
    INFO_TARGET_SOURCE_SELECTED = "INFO_TARGET_SOURCE_SELECTED"
    INFO_SL_SOURCE_SELECTED = "INFO_SL_SOURCE_SELECTED"
    INFO_REPLAN_EPOCH_BOUNDARY = "INFO_REPLAN_EPOCH_BOUNDARY"


# =========================
# Aggregates / helpers
# =========================
ReasonCode = Union[
    BlockReason,
    StopReason,
    ReplanReason,
    PauseReason,
    WarningCode,
    ExecCode,
    EventType,
    InfoCode,
]

ENUM_GROUPS: tuple[type[StrEnum], ...] = (
    BlockReason,
    StopReason,
    ReplanReason,
    PauseReason,
    WarningCode,
    ExecCode,
    EventType,
    InfoCode,
)

ALL_CODE_VALUES: frozenset[str] = frozenset(
    value
    for enum_cls in ENUM_GROUPS
    for value in enum_cls.values()
)


def is_canonical_code(value: str) -> bool:
    """Return True if `value` is a known canonical code."""
    return value in ALL_CODE_VALUES


def all_canonical_codes() -> list[str]:
    """Return all canonical codes sorted alphabetically."""
    return sorted(ALL_CODE_VALUES)


def parse_canonical_code(value: str) -> Optional[ReasonCode]:
    """
    Parse a canonical code string into its enum member.
    Returns None if unknown.
    """
    for enum_cls in ENUM_GROUPS:
        if enum_cls.has_value(value):
            return enum_cls(value)  # type: ignore[return-value]
    return None


def category_of_code(value: Union[str, ReasonCode]) -> Optional[str]:
    """
    Return the category prefix for a code (e.g., BLOCK, STOP, EVENT),
    or None if unknown.
    """
    raw = value.value if isinstance(value, Enum) else value
    if raw in ALL_CODE_VALUES:
        return raw.split("_", 1)[0]
    return None


def ensure_canonical_codes(values: Iterable[Union[str, ReasonCode]]) -> list[str]:
    """
    Normalize/validate a list of code values.
    Raises ValueError if any code is non-canonical.
    """
    out: list[str] = []
    unknown: list[str] = []
    for v in values:
        code = v.value if isinstance(v, Enum) else str(v)
        out.append(code)
        if code not in ALL_CODE_VALUES:
            unknown.append(code)
    if unknown:
        raise ValueError(f"Non-canonical codes detected: {unknown}")
    return out


__all__ = [
    # base/meta
    "StrEnum",
    "Severity",
    "ActionContext",
    "MaterialityClass",
    "PlannerHealthState",
    "ModuleName",
    # code enums
    "BlockReason",
    "StopReason",
    "ReplanReason",
    "PauseReason",
    "WarningCode",
    "ExecCode",
    "EventType",
    "InfoCode",
    "ReasonCode",
    # helpers
    "ENUM_GROUPS",
    "ALL_CODE_VALUES",
    "is_canonical_code",
    "all_canonical_codes",
    "parse_canonical_code",
    "category_of_code",
    "ensure_canonical_codes",
]
