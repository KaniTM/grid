from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from run_state import RunStateTracker


class StallDetected(RuntimeError):
    pass


@dataclass
class MonitorConfig:
    run_id: str
    run_type: str
    total_steps: Optional[int] = None
    enabled: bool = False
    state_dir: Optional[Path] = None
    stall_threshold_sec: int = 0


class LongRunMonitor:
    def __init__(self, config: MonitorConfig, run_state: Optional[RunStateTracker] = None) -> None:
        self.config = config
        self.run_state = run_state
        self._last_progress_ts: Optional[float] = None
        self._started = False
        if config.enabled and run_state is None and config.state_dir:
            state_path = config.state_dir / "state.json"
            events_path = config.state_dir / "events.jsonl"
            self.run_state = RunStateTracker(state_path, events_path)

    def _print(self, payload: Dict[str, Any]) -> None:
        print("[liveness]" + " ".join(f"{k}={json.dumps(v)}" for k, v in payload.items()), flush=True)

    def start(self, message: str = "", total_steps: Optional[int] = None) -> None:
        if not self.config.enabled or self._started:
            return
        self._started = True
        if total_steps is not None:
            self.config.total_steps = total_steps
        payload: Dict[str, Any] = {
            "run": self.config.run_id,
            "run_type": self.config.run_type,
            "event": "RUN_START",
            "pct": "0.00%",
            "message": message,
        }
        self._print(payload)
        self._tick()
        if self.run_state is not None:
            self.run_state.update(
                status="running",
                step_word="RUN_START",
                pct_complete="0.00%",
            )
            self.run_state.event("RUN_START", message=message)

    def progress(self, done: int, stage: str, total: Optional[int] = None, message: str = "") -> None:
        if not self.config.enabled:
            return
        total_val = total if total is not None else self.config.total_steps
        pct = self._format_pct(done, total_val)
        payload = {
            "run": self.config.run_id,
            "stage": stage,
            "done": done,
            "total": total_val,
            "pct": pct,
            "message": message,
        }
        self._print(payload)
        self._tick()
        if self.run_state is not None:
            self.run_state.update(
                status="running",
                step_word=stage,
                pct_complete=pct,
                windows_completed=done if stage.startswith("WINDOW") else done,
            )

    def event(self, word: str, **fields: Any) -> None:
        if not self.config.enabled:
            return
        payload = {
            "run": self.config.run_id,
            "event": word,
            **fields,
        }
        self._print(payload)
        self._tick()
        if self.run_state is not None:
            self.run_state.event(word, **fields)

    def complete(self, word: str, message: str = "", return_code: int = 0) -> None:
        if not self.config.enabled:
            return
        pct = "100.00%"
        payload = {
            "run": self.config.run_id,
            "event": word,
            "pct": pct,
            "message": message,
            "return_code": return_code,
        }
        self._print(payload)
        self._tick()
        if self.run_state is not None:
            self.run_state.update(
                status=("completed" if return_code == 0 else "failed"),
                step_word=word,
                pct_complete=pct,
                return_code=return_code,
            )
            self.run_state.event(word, return_code=return_code)

    def check_stall(self, label: str = "") -> None:
        thresh = int(self.config.stall_threshold_sec or 0)
        if thresh <= 0:
            return
        if self._last_progress_ts is None:
            return
        if (time.time() - self._last_progress_ts) > thresh:
            msg = f"Stall detected for run={self.config.run_id} label={label} threshold={thresh}s"
            self.event("STALL", label=label, message=msg)
            raise StallDetected(msg)

    def poke(self) -> None:
        if not self.config.enabled:
            return
        self._tick()

    def _tick(self) -> None:
        self._last_progress_ts = time.time()

    @staticmethod
    def _format_pct(done: int, total: Optional[int]) -> str:
        if not total or total <= 0:
            return "0.00%"
        return f"{(100.0 * float(done) / float(total)):.2f}%"
