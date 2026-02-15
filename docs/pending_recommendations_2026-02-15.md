# Pending Recommendations (As Of 2026-02-15)

## User Input Needed
- Define what `neutral/choppy` means operationally (volatility band, trend-strength cap, allowed drift, acceptable spread/liquidity).
- Confirm desired mode priority: `intraday`, `neutral/choppy`, and `range` at equal priority; `swing` as fallback.

## Not Implemented Yet
- Resume the interrupted strict baseline run and let it finish cleanly:
  - Run id: `wf_step6B_attr_debug_20260215T124506Z`
  - Resume entrypoint: `freqtrade/scripts/run-user-walkforward-supervisor.py` with `--resume --fail-on-window-error --heartbeat-sec --stalled-heartbeats-max`.
- Add a dedicated `neutral_choppy` mode with separate sizing, spacing, and stop/de-risk rules.
- Update router transitions to treat `swing` as fallback only when non-trend opportunities are unavailable.
- Add reverse handoff: if running `swing` and non-trend conditions improve, switch back to `intraday` or `neutral_choppy`.
- Run strict walkforward for the new routing policy and compare against baseline with mode/fill attribution.
- Keep strict train/validation/test separation (rolling walkforward) when calibrating neutral/choppy thresholds.
- Add a short neutral/choppy research brief to justify threshold design and feature set before final tuning.
- Enforce a global workflow standard for all long-running commands:
  - Always show live liveness + `% complete` on screen (no silent/background-only progress).
  - Auto-emit state markers (`RUN_START`, `WINDOW_DONE`, `RUN_COMPLETE` or equivalent).
  - Include stall detection and auto-retry/resume hooks in the command framework by default.
  - Apply this consistently across all data pulls, simulations, walkforwards, and comparisons.
