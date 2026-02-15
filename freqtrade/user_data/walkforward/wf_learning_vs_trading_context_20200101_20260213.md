# Learning vs Trading Context (2020-01-01 to 2026-02-13)

- Generated UTC: `2026-02-15T13:05:05.322410+00:00`
- Baseline run: `wf_step6_long_B_audit_20200101_20260213_fresh_20260214T032806Z`

## Learning Context
- Walkforward baseline is fixed-threshold evaluation (no in-run fitting).
- Calibration source: `freqtrade/user_data/regime_audit/regime_calib_long_20200101_20251101_v1/report.json`
- Calibration period: `2020-01-01` to `2025-10-31`

## Execution Activity (Baseline)
- Total action bars: `213601` (~`2225.01` days)
- Starts: `644`
- Holds: `112088`
- Stops: `100869`
- Fills: `338`
- Approx mode-paused bars (`gate_fail:mode_active_ok`): `199647` (`93.47%`)
- Approx active/eligible bars: `13954` (`6.53%`, ~`145.35` days)

## Independent Market Regime Share (Strategy-Agnostic)
- Intraday non-trend (`range + neutral`): `84.27%`
  - Range: `39.28%`
  - Neutral: `44.99%`
  - Trend: `15.72%`
- Swing non-trend (`range + neutral`): `80.94%`
  - Range: `35.98%`
  - Neutral: `44.96%`
  - Trend: `19.01%`
