# Walkforward Tuning Shortlist

- Generated: `2026-02-14T10:43:32.261875+00:00`
- Run A: `wf_step6_long_B_audit_20200101_20260213_fresh_20260214T032806Z`
- Run B: `wf_exp_bbwp_plus3_20200101_20260213_v1`
- Delta B-A (`sum_pnl_quote`): `-432.24789893681407`

## Top Blockers (B)

- `gate_fail:mode_active_ok`: `151264` (12.42%)
- `router_pause_mode`: `151264` (12.42%)
- `gate_fail:bbwp_gate_ok`: `140933` (11.57%)
- `gate_fail:fvg_gate_ok`: `135679` (11.14%)
- `reclaim_active`: `108113` (8.88%)
- `cooldown_active`: `88485` (7.27%)
- `stop_rule_active`: `77130` (6.33%)
- `gate_fail:os_dev_build_ok`: `62926` (5.17%)

## Top Stops (B)

- `event:PLAN_STOP`: `77130` (44.79%)
- `bbwp_expansion_stop`: `68593` (39.83%)
- `os_dev_trend_stop`: `11172` (6.49%)
- `adx_hysteresis_stop`: `8135` (4.72%)
- `adx_di_down_risk_stop`: `4664` (2.71%)
- `range_shift_stop`: `2329` (1.35%)
- `router_pause_stop`: `58` (0.03%)
- `mode_handoff_required_stop`: `39` (0.02%)

## Shortlist

- **#1 gate_fail:mode_active_ok** (B=151264, A=199647, Δ=-48383)
  - Test faster router switching: `regime_router_switch_persist_bars` 4 -> 3.
  - Test lower switch margin: `regime_router_switch_margin` 1.0 -> 0.5.
  - A/B keep `router_eligible=true` in both modes while tuning entry gates.
- **#2 gate_fail:bbwp_gate_ok** (B=140933, A=187704, Δ=-46771)
  - Raise BBWP caps in overrides: `bbwp_s_max`, `bbwp_m_max`, `bbwp_l_max` by +3 then +5 points.
  - Re-test with unchanged stop logic first to isolate entry-gate impact.
- **#3 gate_fail:fvg_gate_ok** (B=135679, A=175907, Δ=-40228)
  - Relax FVG veto aggressiveness in `GridBrainV1` (fvg gate constants) by one notch.
  - Measure STOP churn impact before and after to ensure no adverse breakouts.
- **#4 gate_fail:os_dev_build_ok** (B=62926, A=80982, Δ=-18056)
  - Reduce `os_dev_persist_bars` one step (24 -> 18 intraday, 12 -> 9 swing).
  - Keep `os_dev_rvol_max` fixed in pass-1; tune only if needed in pass-2.
- **#5 bbwp_expansion_stop** (B=68593, A=0, Δ=68593)
  - Add 1-step hysteresis to BBWP expansion stop trigger.
  - Test +2/+4 BBWP stop margin ladders to reduce premature exits.
