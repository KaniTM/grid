from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping as AbcMapping, Sequence
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional
from uuid import UUID


PLAN_SCHEMA_VERSION = "1.0.0"
PLANNER_VERSION_DEFAULT = "gridbrain_v1"


SIGNATURE_REQUIRED_FIELDS = (
    "schema_version",
    "planner_version",
    "pair",
    "exchange",
    "plan_id",
    "decision_seq",
    "plan_hash",
    "generated_at",
    "valid_for_candle_ts",
    "materiality_class",
)


MATERIALITY_ALLOWED = {"noop", "soft", "material", "hardstop"}


MATERIAL_HASH_TOP_LEVEL_FIELDS = (
    "schema_version",
    "planner_version",
    "pair",
    "exchange",
    "action",
    "mode",
    "valid_for_candle_ts",
    "materiality_class",
    "replan_decision",
    "replan_reasons",
    "box",
    "grid",
    "risk",
    "capital_policy",
    "update_policy",
)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def stable_payload_hash(value: Any) -> str:
    payload = _canonical_json(value).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def material_plan_payload(plan: Mapping[str, Any]) -> Dict[str, Any]:
    return {k: plan.get(k) for k in MATERIAL_HASH_TOP_LEVEL_FIELDS if k in plan}


def compute_plan_hash(plan: Mapping[str, Any]) -> str:
    return stable_payload_hash(material_plan_payload(plan))


def _is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _material_diff_entries(
    prev: Any,
    new: Any,
    *,
    prefix: str,
    out: list[tuple[str, Any, Any]],
) -> None:
    if isinstance(prev, AbcMapping) and isinstance(new, AbcMapping):
        keys = sorted(set(prev.keys()) | set(new.keys()))
        for key in keys:
            path = f"{prefix}.{key}" if prefix else str(key)
            if key not in prev:
                out.append((path, None, new.get(key)))
                continue
            if key not in new:
                out.append((path, prev.get(key), None))
                continue
            _material_diff_entries(prev.get(key), new.get(key), prefix=path, out=out)
        return

    if _is_sequence(prev) and _is_sequence(new):
        if len(prev) != len(new):
            out.append((prefix or "<root>", list(prev), list(new)))
            return
        for idx, (pv, nv) in enumerate(zip(prev, new)):
            path = f"{prefix}[{idx}]" if prefix else f"[{idx}]"
            _material_diff_entries(pv, nv, prefix=path, out=out)
        return

    if _canonical_json(prev) != _canonical_json(new):
        out.append((prefix or "<root>", prev, new))


def material_plan_diff_entries(
    prev_plan: Optional[Mapping[str, Any]],
    new_plan: Mapping[str, Any],
) -> list[tuple[str, Any, Any]]:
    prev_payload = material_plan_payload(prev_plan or {})
    new_payload = material_plan_payload(new_plan)
    entries: list[tuple[str, Any, Any]] = []
    _material_diff_entries(prev_payload, new_payload, prefix="", out=entries)
    return entries


def material_plan_changed_fields(
    prev_plan: Optional[Mapping[str, Any]],
    new_plan: Mapping[str, Any],
) -> list[str]:
    return [path for path, _, _ in material_plan_diff_entries(prev_plan, new_plan)]


def material_plan_diff_snapshot(
    prev_plan: Optional[Mapping[str, Any]],
    new_plan: Mapping[str, Any],
    *,
    max_fields: int = 24,
) -> Dict[str, Dict[str, Any]]:
    entries = material_plan_diff_entries(prev_plan, new_plan)
    if max_fields <= 0:
        max_fields = 1
    out: Dict[str, Dict[str, Any]] = {}
    for path, prev_val, new_val in entries[:max_fields]:
        out[path] = {"prev": prev_val, "new": new_val}
    if len(entries) > max_fields:
        out["_truncated_fields"] = {
            "prev": len(entries) - max_fields,
            "new": "truncated",
        }
    return out


def _parse_iso8601(ts: str) -> Optional[datetime]:
    text = str(ts or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _parse_optional_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except Exception:
            return None
    return _parse_iso8601(str(value))


def validate_signature_fields(plan: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in SIGNATURE_REQUIRED_FIELDS:
        if field not in plan:
            errors.append(f"missing:{field}")

    if errors:
        return errors

    try:
        UUID(str(plan.get("plan_id")))
    except Exception:
        errors.append("invalid:plan_id")

    try:
        if int(plan.get("decision_seq")) <= 0:
            errors.append("invalid:decision_seq")
    except Exception:
        errors.append("invalid:decision_seq")

    plan_hash = str(plan.get("plan_hash") or "").strip()
    if len(plan_hash) < 32:
        errors.append("invalid:plan_hash")

    if _parse_optional_datetime(plan.get("generated_at")) is None:
        errors.append("invalid:generated_at")

    try:
        if int(plan.get("valid_for_candle_ts")) <= 0:
            errors.append("invalid:valid_for_candle_ts")
    except Exception:
        errors.append("invalid:valid_for_candle_ts")

    materiality = str(plan.get("materiality_class") or "").strip().lower()
    if materiality not in MATERIALITY_ALLOWED:
        errors.append("invalid:materiality_class")

    supersedes = plan.get("supersedes_plan_id")
    if supersedes not in (None, ""):
        try:
            UUID(str(supersedes))
        except Exception:
            errors.append("invalid:supersedes_plan_id")

    expires_at = plan.get("expires_at")
    if expires_at not in (None, "") and _parse_optional_datetime(expires_at) is None:
        errors.append("invalid:expires_at")

    return errors


def plan_is_expired(plan: Mapping[str, Any], *, now_ts: Optional[int] = None) -> bool:
    expires_at = plan.get("expires_at")
    if expires_at in (None, ""):
        return False
    expires_dt = _parse_optional_datetime(expires_at)
    if expires_dt is None:
        return False
    now_dt = (
        datetime.fromtimestamp(int(now_ts), tz=timezone.utc)
        if now_ts is not None
        else datetime.now(timezone.utc)
    )
    return bool(expires_dt <= now_dt)


def plan_pair(plan: Mapping[str, Any]) -> str:
    pair = plan.get("pair")
    if pair is not None and str(pair).strip():
        return str(pair)
    symbol = plan.get("symbol")
    if symbol is not None and str(symbol).strip():
        return str(symbol)
    return ""
