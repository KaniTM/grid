# Stress Replay Profiles

This document defines canonical stress/chaos profile fields for replay.

## Profile goals

Replay profiles model execution and market perturbations used to validate safety behavior:

- latency shocks
- spread shocks
- partial fill bursts
- reject bursts
- data gap windows

## Canonical profile fields

`schemas/chaos_profile.schema.json` defines the machine-readable contract.

Core fields:

- `profile_id`
- `name`
- `enabled`
- `seed`
- `latency_ms`
- `spread_shock_bps`
- `partial_fill_probability`
- `reject_burst_probability`
- `data_gap_probability`

Additional supported knobs:

- `latency_ms.fill_window_ms`
- `spread_shock_bps.burst_probability`
- `partial_fill_min_ratio` / `partial_fill_max_ratio`
- `reject_burst_bars.min` / `reject_burst_bars.max`
- `delayed_candle_probability`
- `missing_candle_probability`

## Validation expectations

- Profile JSON must validate before replay starts.
- Replays must log active `profile_id`.
- Results should include deterministic seed and perturbation counters.
