import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "user_data" / "scripts" / "grid_executor_v1.py"


def _load_grid_executor_module() -> Any:
    spec = importlib.util.spec_from_file_location("grid_executor_v1", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    if spec.name not in sys.modules:
        sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_plan_signature_logs_on_invalid_plan(capsys, tmp_path) -> None:
    module = _load_grid_executor_module()
    plan = {"range": {"low": 1, "high": 2}}
    plan_path = tmp_path / "test_plan.json"
    plan["_plan_path"] = str(plan_path)
    with pytest.raises(KeyError):
        module.plan_signature(plan)
    captured = capsys.readouterr()
    assert "plan_signature_failed" in captured.out
    assert str(plan_path) in captured.out
