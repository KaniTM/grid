# ruff: noqa: S101

import json
import os
from pathlib import Path

import pytest

from freqtrade.user_data.scripts import user_regression_suite


def _write_plan(path: Path, candle_ts: int) -> None:
    path.write_text(json.dumps({"candle_ts": int(candle_ts)}), encoding="utf-8")


def test_resolve_recent_plan_seconds_defaults_to_600(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("REGRESSION_RECENT_PLAN_SECONDS", raising=False)
    assert user_regression_suite.resolve_recent_plan_seconds(None) == 600


def test_resolve_recent_plan_seconds_prefers_cli_over_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REGRESSION_RECENT_PLAN_SECONDS", "3600")
    assert user_regression_suite.resolve_recent_plan_seconds(900) == 900


def test_check_recent_plan_history_respects_custom_window(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    now = 1_700_000_000.0
    plan_dir = tmp_path / "plans"
    plan_dir.mkdir(parents=True, exist_ok=True)

    latest = plan_dir / "grid_plan.latest.json"
    snap1 = plan_dir / "grid_plan.20260209T234500+0000.json"
    snap2 = plan_dir / "grid_plan.20260210T000000+0000.json"

    _write_plan(latest, 1700000000)
    _write_plan(snap1, 1700000000)
    _write_plan(snap2, 1700000900)

    # Simulate "stale for 600s" but valid for a wider custom window.
    old_mtime = now - 1200.0
    for p in (latest, snap1, snap2):
        p.touch()
        p.chmod(0o644)
        os.utime(p, (old_mtime, old_mtime))

    monkeypatch.setattr(user_regression_suite.time, "time", lambda: now)

    with pytest.raises(AssertionError, match="no recent plan snapshots"):
        user_regression_suite.check_recent_plan_history(latest, recent_seconds=600)

    user_regression_suite.check_recent_plan_history(latest, recent_seconds=3600)
