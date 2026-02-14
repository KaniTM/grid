#!/usr/bin/env python3
"""
Helpers for publishing stable "latest" pointers for user artifacts.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_json_atomic(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _rel(base: Path, maybe_path: Optional[Path]) -> str:
    if maybe_path is None:
        return ""
    try:
        return str(maybe_path.resolve().relative_to(base.resolve()))
    except Exception:
        return str(maybe_path)


def publish_latest_ref(user_data_dir: Path, category: str, payload: Dict[str, Any]) -> Path:
    """
    Write:
    - user_data/latest_refs/<category>.json
    - user_data/latest_refs/index.json
    """
    user_data = Path(user_data_dir).resolve()
    refs_dir = user_data / "latest_refs"
    refs_dir.mkdir(parents=True, exist_ok=True)

    cat = str(category).strip().lower()
    if not cat:
        raise ValueError("category must be non-empty")

    ts = _utc_now_iso()
    cat_payload = dict(payload)
    cat_payload["category"] = cat
    cat_payload["updated_utc"] = ts

    cat_file = refs_dir / f"{cat}.json"
    _write_json_atomic(cat_file, cat_payload)

    index_file = refs_dir / "index.json"
    index = _load_json(index_file)
    refs = index.get("refs", {})
    if not isinstance(refs, dict):
        refs = {}
    refs[cat] = {
        "ref_file": cat_file.name,
        "updated_utc": ts,
        "run_id": str(cat_payload.get("run_id") or ""),
        "out_dir": str(cat_payload.get("out_dir") or ""),
    }
    index["refs"] = refs
    index["updated_utc"] = ts
    _write_json_atomic(index_file, index)
    return cat_file


def load_latest_ref(user_data_dir: Path, category: str) -> Dict[str, Any]:
    user_data = Path(user_data_dir).resolve()
    refs_dir = user_data / "latest_refs"
    cat = str(category).strip().lower()
    if not cat:
        return {}
    return _load_json(refs_dir / f"{cat}.json")


def collect_latest_run_pins(user_data_dir: Path) -> Tuple[Set[str], Set[str]]:
    """
    Return pinned run-ids inferred from latest refs:
    - walkforward runs
    - regime_audit runs
    """
    user_data = Path(user_data_dir).resolve()
    wf: Set[str] = set()
    rg: Set[str] = set()

    walkforward_ref = load_latest_ref(user_data, "walkforward")
    walkforward_run = str(walkforward_ref.get("run_id") or "").strip()
    if walkforward_run:
        wf.add(walkforward_run)

    compare_ref = load_latest_ref(user_data, "ab_compare")
    a_run = str(compare_ref.get("A_run_id") or "").strip()
    b_run = str(compare_ref.get("B_run_id") or "").strip()
    if a_run:
        wf.add(a_run)
    if b_run:
        wf.add(b_run)

    regime_ref = load_latest_ref(user_data, "regime_audit")
    regime_run = str(regime_ref.get("run_id") or "").strip()
    if regime_run:
        rg.add(regime_run)

    return wf, rg


def rel_payload_path(user_data_dir: Path, path: Optional[Path]) -> str:
    return _rel(Path(user_data_dir).resolve(), path)
