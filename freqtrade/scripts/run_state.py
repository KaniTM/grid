#!/usr/bin/env python3
"""
Lightweight run-state tracker for long-running user scripts.

Writes:
- `state.json` (latest snapshot, atomically updated)
- `events.jsonl` (append-only event log with status words)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RunStateTracker:
    def __init__(self, state_file: Path, events_file: Optional[Path] = None) -> None:
        self.state_file = Path(state_file).resolve()
        self.events_file = Path(events_file).resolve() if events_file else None
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        if self.events_file:
            self.events_file.parent.mkdir(parents=True, exist_ok=True)
        self._state: Dict[str, Any] = {}

    @property
    def state(self) -> Dict[str, Any]:
        return dict(self._state)

    def update(self, **fields: Any) -> Dict[str, Any]:
        payload = dict(self._state)
        payload.update(fields)
        payload["updated_utc"] = _utc_now_iso()
        tmp = self.state_file.with_suffix(self.state_file.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self.state_file)
        self._state = payload
        return dict(self._state)

    def event(self, word: str, **fields: Any) -> Dict[str, Any]:
        rec: Dict[str, Any] = {"ts_utc": _utc_now_iso(), "word": str(word)}
        rec.update(fields)
        if self.events_file:
            with self.events_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, sort_keys=True) + "\n")
        return rec

