# Walkforward Tuning Shortlist

- Generated: `2026-02-14T10:43:32.196317+00:00`
- Run A: `wf_step6_long_B_audit_20200101_20260213_fresh_20260214T032806Z`
- Run B: `wf_exp_router_fast_20200101_20260213_v1`
- Delta B-A (`sum_pnl_quote`): `-102.6872477866442`

## Top Blockers (B)

- `gate_fail:mode_active_ok`: `151185` (12.45%)
- `router_pause_mode`: `151185` (12.45%)
- `gate_fail:bbwp_gate_ok`: `142875` (11.77%)
- `gate_fail:fvg_gate_ok`: `133869` (11.02%)
- `reclaim_active`: `108079` (8.90%)
- `cooldown_active`: `88482` (7.29%)
- `stop_rule_active`: `77086` (6.35%)
- `gate_fail:os_dev_build_ok`: `62197` (5.12%)

## Top Stops (B)

- `event:PLAN_STOP`: `77086` (44.86%)
- `bbwp_expansion_stop`: `68455` (39.84%)
- `os_dev_trend_stop`: `10879` (6.33%)
- `adx_hysteresis_stop`: `7994` (4.65%)
- `adx_di_down_risk_stop`: `4841` (2.82%)
- `range_shift_stop`: `2370` (1.38%)
- `router_pause_stop`: `68` (0.04%)
- `mode_handoff_required_stop`: `38` (0.02%)

## Shortlist

- **#1 gate_fail:mode_active_ok** (B=151185, A=199647, Δ=-48462)
  - Test faster router switching: `regime_router_switch_persist_bars` 4 -> 3.
  - Test lower switch margin: `regime_router_switch_margin` 1.0 -> 0.5.
  - A/B keep `router_eligible=true` in both modes while tuning entry gates.
- **#2 gate_fail:bbwp_gate_ok** (B=142875, A=187704, Δ=-44829)
  - Raise BBWP caps in overrides: `bbwp_s_max`, `bbwp_m_max`, `bbwp_l_max` by +3 then +5 points.
  - Re-test with unchanged stop logic first to isolate entry-gate impact.
- **#3 gate_fail:fvg_gate_ok** (B=133869, A=175907, Δ=-42038)
  - Relax FVG veto aggressiveness in `GridBrainV1` (fvg gate constants) by one notch.
  - Measure STOP churn impact before and after to ensure no adverse breakouts.
- **#4 gate_fail:os_dev_build_ok** (B=62197, A=80982, Δ=-18785)
  - Reduce `os_dev_persist_bars` one step (24 -> 18 intraday, 12 -> 9 swing).
  - Keep `os_dev_rvol_max` fixed in pass-1; tune only if needed in pass-2.
- **#5 bbwp_expansion_stop** (B=68455, A=0, Δ=68455)
  - Add 1-step hysteresis to BBWP expansion stop trigger.
  - Test +2/+4 BBWP stop margin ladders to reduce premature exits.
