from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional


def load_capacity_hint_state(
    pair: str,
    *,
    capacity_hint_path: str,
    capacity_hint_hard_block: bool,
) -> Dict[str, object]:
    out = {
        "available": False,
        "allow_start": True,
        "reason": None,
        "preferred_rung_cap": None,
        "max_concurrent_rebuilds": None,
        "advisory_only": bool(not capacity_hint_hard_block),
    }
    path = str(capacity_hint_path or "").strip()
    if not path:
        return out
    p = Path(path).expanduser()
    if not p.is_file():
        return out

    try:
        with p.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        raw: Optional[dict]
        raw = payload.get(pair) if isinstance(payload, dict) and pair in payload else payload
        if not isinstance(raw, dict):
            return out
        out["available"] = True
        out["allow_start"] = bool(raw.get("allow_start", True))
        out["reason"] = raw.get("reason")
        out["preferred_rung_cap"] = raw.get("preferred_rung_cap")
        out["max_concurrent_rebuilds"] = raw.get("max_concurrent_rebuilds")
        out["advisory_only"] = bool(raw.get("advisory_only", not capacity_hint_hard_block))
        return out
    except Exception:
        return out

