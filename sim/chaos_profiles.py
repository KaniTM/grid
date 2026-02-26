from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from core.schema_validation import validate_schema


def default_chaos_profile() -> Dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "profile_id": "baseline-chaos-v1",
        "name": "baseline",
        "enabled": True,
        "seed": 42,
        "latency_ms": {"mean": 120, "jitter": 40},
        "spread_shock_bps": {"base": 3, "burst": 12},
        "partial_fill_probability": 0.2,
        "reject_burst_probability": 0.1,
        "data_gap_probability": 0.03,
    }


def validate_chaos_profile(profile: Dict[str, object]) -> list[str]:
    return validate_schema(profile, "chaos_profile.schema.json")


def load_chaos_profile(path: str) -> Dict[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("chaos profile must be a JSON object")
    errors = validate_chaos_profile(payload)
    if errors:
        raise ValueError("; ".join(errors[:3]))
    return payload

