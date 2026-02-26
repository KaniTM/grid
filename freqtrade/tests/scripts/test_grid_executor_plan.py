from freqtrade.user_data.scripts.grid_executor_v1 import plan_signature


def test_plan_signature_returns_expected_tuple_and_logs(capsys):
    plan = {
        "range": {"low": 1.0, "high": 5.0},
        "grid": {"n_levels": 4, "step_price": 1.0},
    }
    sig = plan_signature(plan)
    assert sig == (1.0, 5.0, 4, 1.0)
    out = capsys.readouterr().out
    assert '"message": "plan_signature"' in out
