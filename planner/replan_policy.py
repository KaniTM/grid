from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from core.enums import MaterialityClass


@dataclass(frozen=True)
class ReplanThresholds:
    epoch_bars: int
    box_mid_shift_max_step_frac: float
    box_width_change_pct: float
    tp_shift_max_step_frac: float
    sl_shift_max_step_frac: float


def evaluate_replan_materiality(
    *,
    prev_mid: Optional[float],
    prev_width_pct: Optional[float],
    prev_tp: Optional[float],
    prev_sl: Optional[float],
    epoch_counter: int,
    thresholds: ReplanThresholds,
    mid: float,
    width_pct: float,
    step_price: float,
    tp_price: float,
    sl_price: float,
    hard_stop: bool,
    action: str,
) -> Dict[str, object]:
    epoch_counter = int(max(epoch_counter, 1))
    allow_epoch = epoch_counter >= max(1, int(thresholds.epoch_bars))

    delta_mid_steps = 0.0
    delta_width_pct = 0.0
    delta_tp_steps = 0.0
    delta_sl_steps = 0.0

    if prev_mid is not None and step_price > 0:
        delta_mid_steps = abs(float(mid) - float(prev_mid)) / float(step_price)
    if prev_width_pct is not None:
        delta_width_pct = abs(float(width_pct) - float(prev_width_pct))
    if prev_tp is not None and step_price > 0:
        delta_tp_steps = abs(float(tp_price) - float(prev_tp)) / float(step_price)
    if prev_sl is not None and step_price > 0:
        delta_sl_steps = abs(float(sl_price) - float(prev_sl)) / float(step_price)

    material_delta = bool(
        delta_mid_steps >= float(thresholds.box_mid_shift_max_step_frac)
        or delta_width_pct >= float(thresholds.box_width_change_pct)
        or delta_tp_steps >= float(thresholds.tp_shift_max_step_frac)
        or delta_sl_steps >= float(thresholds.sl_shift_max_step_frac)
    )

    reasons: List[str] = []
    mat_class = MaterialityClass.NOOP
    publish = False
    if hard_stop or str(action).upper() == "STOP":
        mat_class = MaterialityClass.HARDSTOP
        reasons.append("REPLAN_HARD_STOP_OVERRIDE")
        publish = True
    elif material_delta:
        mat_class = MaterialityClass.MATERIAL
        reasons.append("REPLAN_MATERIAL_BOX_CHANGE")
        publish = True
    elif allow_epoch or prev_mid is None:
        mat_class = MaterialityClass.SOFT
        reasons.append("REPLAN_NOOP_MINOR_DELTA")
        publish = True
    else:
        mat_class = MaterialityClass.NOOP
        reasons.append("REPLAN_NOOP_MINOR_DELTA")
        publish = False

    next_epoch_counter = 0 if publish else int(epoch_counter)
    return {
        "class": mat_class,
        "reasons": reasons,
        "publish": bool(publish),
        "epoch_counter": int(epoch_counter),
        "delta_mid_steps": float(delta_mid_steps),
        "delta_width_pct": float(delta_width_pct),
        "delta_tp_steps": float(delta_tp_steps),
        "delta_sl_steps": float(delta_sl_steps),
        "next_epoch_counter": int(next_epoch_counter),
    }

