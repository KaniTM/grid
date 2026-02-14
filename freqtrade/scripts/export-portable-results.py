#!/usr/bin/env python3
"""Export lightweight, git-friendly result artifacts for cross-machine handoff.

Copies the latest walkforward summaries, AB compare report, and latest threshold
override file into user_data/portable_results/latest.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from latest_refs import publish_latest_ref, rel_payload_path


def pick_latest_walkforward_runs(wf_dir: Path, limit: int) -> list[Path]:
    runs: list[tuple[float, Path]] = []
    for d in wf_dir.iterdir():
        if not d.is_dir():
            continue
        summary = d / "summary.json"
        windows = d / "windows.csv"
        if summary.exists() and windows.exists():
            runs.append((summary.stat().st_mtime, d))
    runs.sort(key=lambda x: x[0], reverse=True)
    return [d for _, d in runs[:limit]]


def copy_if_exists(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user-data", default="user_data")
    ap.add_argument("--latest-runs", type=int, default=3)
    args = ap.parse_args()

    user_data = Path(args.user_data)
    wf_dir = user_data / "walkforward"
    regime_dir = user_data / "regime_audit"
    out_dir = user_data / "portable_results" / "latest"
    out_dir.mkdir(parents=True, exist_ok=True)

    copied: dict[str, list[str] | str] = {
        "walkforward_runs": [],
        "ab_compare": "",
        "mode_threshold_overrides": "",
    }

    for run_dir in pick_latest_walkforward_runs(wf_dir, args.latest_runs):
        run_name = run_dir.name
        target_dir = out_dir / "walkforward" / run_name
        copy_if_exists(run_dir / "summary.json", target_dir / "summary.json")
        copy_if_exists(run_dir / "windows.csv", target_dir / "windows.csv")
        copied["walkforward_runs"].append(run_name)

    ab_files = sorted(wf_dir.glob("*AB_compare*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if ab_files:
        src = ab_files[0]
        copy_if_exists(src, out_dir / "walkforward" / src.name)
        copied["ab_compare"] = src.name

    override_files = sorted(
        regime_dir.glob("**/mode_threshold_overrides.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if override_files:
        src = override_files[0]
        copy_if_exists(src, out_dir / "regime_audit" / src.parent.name / src.name)
        copied["mode_threshold_overrides"] = str(src.relative_to(user_data))

    manifest = {
        "portable_results_dir": str(out_dir),
        "copied": copied,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    latest_payload = {
        "run_type": "portable_export",
        "out_dir": rel_payload_path(user_data, out_dir),
        "manifest_path": rel_payload_path(user_data, out_dir / "manifest.json"),
        "walkforward_runs": copied.get("walkforward_runs", []),
        "ab_compare": str(copied.get("ab_compare") or ""),
        "mode_threshold_overrides": str(copied.get("mode_threshold_overrides") or ""),
    }
    ref = publish_latest_ref(user_data, "portable_results", latest_payload)
    manifest["latest_ref"] = str(ref)

    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
