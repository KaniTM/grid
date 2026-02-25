import json
import subprocess
import sys
from pathlib import Path


def _run_manage(user_data: Path) -> dict:
    cmd = [
        sys.executable,
        "-m",
        "freqtrade.scripts.manage_user_artifacts",
        "--json",
        "--user-data",
        str(user_data),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(res.stdout)


def test_blocked_walkforward_candidate_in_summary(tmp_path: Path) -> None:
    user_data = tmp_path / "user_data"
    run_dir = user_data / "walkforward" / "wf_blocked"
    run_dir.mkdir(parents=True)
    summary = run_dir / "summary.json"
    window = {
        "index": 0,
        "status": "ok",
        "timerange": "20250101-20250102",
        "result_file": "window_000.result.json",
    }
    summary.write_text(json.dumps({"windows": [window]}), encoding="utf-8")
    result_file = run_dir / "window_000.result.json"
    result_file.write_text(json.dumps({"summary": {"end_quote": None, "end_base": None}}), encoding="utf-8")

    payload = _run_manage(user_data)
    blocked_candidates = payload.get("blocked_candidates") or []
    assert blocked_candidates, "Expected at least one blocked candidate"
    assert blocked_candidates[0]["run_id"] == "wf_blocked"
    assert payload.get("walkforward_blocked_run_stats")
    assert payload["walkforward_blocked_run_stats"][0]["run_id"] == "wf_blocked"
