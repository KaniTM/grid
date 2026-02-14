# Walkforward Tuning Shortlist

- Generated: `2026-02-14T10:43:32.326555+00:00`
- Run A: `wf_step6_long_B_audit_20200101_20260213_fresh_20260214T032806Z`
- Run B: `wf_exp_osdev_persist_20200101_20260213_v1`
- Delta B-A (`sum_pnl_quote`): `-905.3783178543019`

## Top Blockers (B)

- `gate_fail:mode_active_ok`: `117399` (12.51%)
- `router_pause_mode`: `117399` (12.51%)
- `gate_fail:bbwp_gate_ok`: `110714` (11.80%)
- `gate_fail:fvg_gate_ok`: `106441` (11.35%)
- `reclaim_active`: `83523` (8.90%)
- `cooldown_active`: `68786` (7.33%)
- `stop_rule_active`: `60270` (6.42%)
- `gate_fail:os_dev_build_ok`: `45866` (4.89%)

## Top Stops (B)

- `event:PLAN_STOP`: `60270` (44.49%)
- `bbwp_expansion_stop`: `53520` (39.51%)
- `os_dev_trend_stop`: `8657` (6.39%)
- `adx_hysteresis_stop`: `6598` (4.87%)
- `adx_di_down_risk_stop`: `4519` (3.34%)
- `range_shift_stop`: `1773` (1.31%)
- `router_pause_stop`: `36` (0.03%)
- `mode_handoff_required_stop`: `28` (0.02%)

## Shortlist

- **#1 gate_fail:mode_active_ok** (B=117399, A=199647, Δ=-82248)
  - Test faster router switching: `regime_router_switch_persist_bars` 4 -> 3.
  - Test lower switch margin: `regime_router_switch_margin` 1.0 -> 0.5.
  - A/B keep `router_eligible=true` in both modes while tuning entry gates.
- **#2 gate_fail:bbwp_gate_ok** (B=110714, A=187704, Δ=-76990)
  - Raise BBWP caps in overrides: `bbwp_s_max`, `bbwp_m_max`, `bbwp_l_max` by +3 then +5 points.
  - Re-test with unchanged stop logic first to isolate entry-gate impact.
- **#3 gate_fail:fvg_gate_ok** (B=106441, A=175907, Δ=-69466)
  - Relax FVG veto aggressiveness in `GridBrainV1` (fvg gate constants) by one notch.
  - Measure STOP churn impact before and after to ensure no adverse breakouts.
- **#4 gate_fail:os_dev_build_ok** (B=45866, A=80982, Δ=-35116)
  - Reduce `os_dev_persist_bars` one step (24 -> 18 intraday, 12 -> 9 swing).
  - Keep `os_dev_rvol_max` fixed in pass-1; tune only if needed in pass-2.
- **#5 bbwp_expansion_stop** (B=53520, A=0, Δ=53520)
  - Add 1-step hysteresis to BBWP expansion stop trigger.
  - Test +2/+4 BBWP stop margin ladders to reduce premature exits.
