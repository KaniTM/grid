from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping, Union


PathLike = Union[str, os.PathLike[str], Path]


def write_json_atomic(path: PathLike, payload: Mapping[str, Any]) -> None:
    """
    Atomically write a JSON object (tmp + fsync + rename).
    """
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_name(f"{out_path.name}.tmp")

    data = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
    with tmp_path.open("w", encoding="utf-8") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())

    os.replace(str(tmp_path), str(out_path))


def read_json_object(path: PathLike) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return payload

