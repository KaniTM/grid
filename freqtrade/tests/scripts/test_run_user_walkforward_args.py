import argparse

from freqtrade.scripts.run_user_walkforward import _collect_resume_mismatches


def _dummy_args(**kwargs):
    return argparse.Namespace(**kwargs)


def test_collect_resume_mismatches_ignores_optional_changes():
    existing_args = {
        "window_days": 7,
        "step_days": 7,
        "min_window_days": 7,
        "pair": "BTC/USDT",
        "exchange": "binance",
        "timeframe": "15m",
        "strategy": "GridBrainV1",
        "strategy_path": "/freqtrade/user_data/strategies",
        "data_dir": "/freqtrade/user_data/data/binance",
        "config_path": "/freqtrade/user_data/config.json",
        "mode_thresholds_path": "",
        "backtesting_extra": "",
        "sim_extra": "",
    }
    current_args = _dummy_args(
        **{**existing_args, "backtesting_extra": "tune-me"}
    )
    fatal, optional = _collect_resume_mismatches(existing_args, current_args)
    assert not fatal
    assert any(entry[0] == "backtesting_extra" for entry in optional)


def test_collect_resume_mismatches_detects_core_mismatch():
    existing_args = {
        "window_days": 7,
        "step_days": 7,
        "min_window_days": 7,
        "pair": "BTC/USDT",
        "exchange": "binance",
        "timeframe": "15m",
        "strategy": "GridBrainV1",
        "strategy_path": "/freqtrade/user_data/strategies",
        "data_dir": "/freqtrade/user_data/data/binance",
        "config_path": "/freqtrade/user_data/config.json",
    }
    current_args = _dummy_args(**{**existing_args, "pair": "ETH/USDT"})
    fatal, optional = _collect_resume_mismatches(existing_args, current_args)
    assert fatal
    assert fatal[0][0] == "pair"
    assert not optional
