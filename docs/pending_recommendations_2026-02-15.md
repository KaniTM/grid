# Pending Recommendations (As Of 2026-02-15)

## User Input Needed
- Define what `neutral/choppy` means operationally (volatility band, trend-strength cap, allowed drift, acceptable spread/liquidity).
- Confirm desired mode priority: `intraday`, `neutral/choppy`, and `range` at equal priority; `swing` as fallback.

## Not Implemented Yet
- Add a dedicated `neutral_choppy` mode with separate sizing, spacing, and stop/de-risk rules.
- Update router transitions to treat `swing` as fallback only when non-trend opportunities are unavailable.
- Add reverse handoff: if running `swing` and non-trend conditions improve, switch back to `intraday` or `neutral_choppy`.
- Run strict walkforward for the new routing policy and compare against baseline with mode/fill attribution.
- Keep strict train/validation/test separation (rolling walkforward) when calibrating neutral/choppy thresholds.
- Add a short neutral/choppy research brief to justify threshold design and feature set before final tuning.
