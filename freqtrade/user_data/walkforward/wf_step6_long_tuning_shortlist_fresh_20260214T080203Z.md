# Walkforward Tuning Shortlist

- Generated: `2026-02-14T08:02:03.563997+00:00`
- Run A: `wf_step6_long_A_manual_20200101_20260213_fresh_20260214T012147Z`
- Run B: `wf_step6_long_B_audit_20200101_20260213_fresh_20260214T032806Z`
- Delta B-A (`sum_pnl_quote`): `515.3736384476507`

## Top Blockers (B)

- `gate_fail:mode_active_ok`: `199647` (12.49%)
- `router_pause_mode`: `199647` (12.49%)
- `gate_fail:bbwp_gate_ok`: `187704` (11.74%)
- `gate_fail:fvg_gate_ok`: `175907` (11.00%)
- `reclaim_active`: `141482` (8.85%)
- `cooldown_active`: `115741` (7.24%)
- `stop_rule_active`: `100869` (6.31%)
- `gate_fail:os_dev_build_ok`: `80982` (5.06%)

## Top Stops (B)

- `event:PLAN_STOP`: `100869` (44.91%)
- `bbwp_expansion_stop`: `89760` (39.97%)
- `os_dev_trend_stop`: `13980` (6.22%)
- `adx_hysteresis_stop`: `10554` (4.70%)
- `adx_di_down_risk_stop`: `6042` (2.69%)
- `range_shift_stop`: `3129` (1.39%)
- `router_pause_stop`: `87` (0.04%)
- `mode_handoff_required_stop`: `48` (0.02%)

## Shortlist

- **#1 gate_fail:mode_active_ok** (B=199647, A=208229, Δ=-8582)
  - Test faster router switching: `regime_router_switch_persist_bars` 4 -> 3.
  - Test lower switch margin: `regime_router_switch_margin` 1.0 -> 0.5.
  - A/B keep `router_eligible=true` in both modes while tuning entry gates.
- **#2 gate_fail:bbwp_gate_ok** (B=187704, A=202060, Δ=-14356)
  - Raise BBWP caps in overrides: `bbwp_s_max`, `bbwp_m_max`, `bbwp_l_max` by +3 then +5 points.
  - Re-test with unchanged stop logic first to isolate entry-gate impact.
- **#3 gate_fail:fvg_gate_ok** (B=175907, A=175907, Δ=0)
  - Relax FVG veto aggressiveness in `GridBrainV1` (fvg gate constants) by one notch.
  - Measure STOP churn impact before and after to ensure no adverse breakouts.
- **#4 gate_fail:os_dev_build_ok** (B=80982, A=87179, Δ=-6197)
  - Reduce `os_dev_persist_bars` one step (24 -> 18 intraday, 12 -> 9 swing).
  - Keep `os_dev_rvol_max` fixed in pass-1; tune only if needed in pass-2.
- **#5 bbwp_expansion_stop** (B=89760, A=0, Δ=89760)
  - Add 1-step hysteresis to BBWP expansion stop trigger.
  - Test +2/+4 BBWP stop margin ladders to reduce premature exits.
- **#6 gate_fail:cvd_gate_ok** (B=65632, A=65632, Δ=0)
  - Run a one-variable-at-a-time pass to measure this reason’s isolated effect.
