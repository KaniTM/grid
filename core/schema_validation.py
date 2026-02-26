from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

try:
    from jsonschema import Draft202012Validator, FormatChecker
except Exception:  # pragma: no cover
    Draft202012Validator = None  # type: ignore[assignment]
    FormatChecker = None  # type: ignore[assignment]


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = REPO_ROOT / "schemas"


def _format_error(err: Any) -> str:
    path_items = list(err.path) if hasattr(err, "path") else []
    path = "$" if not path_items else "$." + ".".join(str(x) for x in path_items)
    return f"{path}: {err.message}"


def schema_path(schema_name: str) -> Path:
    return SCHEMAS_DIR / str(schema_name)


@lru_cache(maxsize=32)
def _load_schema(schema_name: str) -> dict:
    path = schema_path(schema_name)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Schema must be a JSON object: {path}")
    return payload


def validate_schema(payload: Mapping[str, Any], schema_name: str) -> list[str]:
    if Draft202012Validator is None:
        return ["schema_validator_unavailable"]

    path = schema_path(schema_name)
    if not path.is_file():
        return [f"schema_not_found:{schema_name}"]

    schema = _load_schema(schema_name)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(payload), key=lambda e: (list(e.path), e.message))
    return [_format_error(err) for err in errors]

