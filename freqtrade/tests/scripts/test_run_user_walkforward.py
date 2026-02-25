import importlib.util
import sys
from argparse import Namespace
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "run-user-walkforward.py"


def _load_module() -> Any:
    spec = importlib.util.spec_from_file_location("run_user_walkforward", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    script_dir = SCRIPT_PATH.parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    if spec.name not in sys.modules:
        sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _make_args(**overrides: Any) -> Namespace:
    base = {
        "window_days": 7,
        "step_days": 7,
        "min_window_days": 2,
        "pair": "ETH/USDT",
        "exchange": "binance",
        "timeframe": "15m",
        "strategy": "GridBrainV1",
        "strategy_path": "/freqtrade/user_data/strategies",
        "data_dir": "/freqtrade/user_data/data/binance",
        "config_path": "/freqtrade/user_data/config.json",
        "start_quote": 1000.0,
        "start_base": 0.0,
        "carry_capital": False,
        "fee_pct": 0.1,
        "max_orders_per_side": 40,
        "close_on_stop": False,
        "reverse_fill": False,
        "regime_threshold_profile": None,
        "mode_thresholds_path": "/freqtrade/user_data/regime_audit/prev.json",
        "backtesting_extra": "",
        "sim_extra": "",
    }
    base.update(overrides)
    return Namespace(**base)


def test_resume_core_mismatch_detected() -> None:
    module = _load_module()
    existing_args = _make_args()
    args = _make_args(window_days=14)
    fatal, optional = module._collect_resume_mismatches(existing_args.__dict__, args)
    assert fatal == [("window_days", 14, 7)]
    assert optional == []


def test_resume_optional_mismatch_warning() -> None:
    module = _load_module()
    existing_args = _make_args()
    args = _make_args(
        fee_pct=0.2,
        mode_thresholds_path="/freqtrade/user_data/regime_audit/new.json",
    )
    fatal, optional = module._collect_resume_mismatches(existing_args.__dict__, args)
    assert not fatal
    keys = {entry[0] for entry in optional}
    assert "fee_pct" in keys
    assert "mode_thresholds_path" in keys
