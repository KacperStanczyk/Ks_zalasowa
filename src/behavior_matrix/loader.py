"""Utilities for loading behavior matrix YAML files."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml

from .model import (
    BehaviorContext,
    BehaviorRow,
    ExpectedBehavior,
    MonitorSpec,
)


def _ensure_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def load_behavior_matrix(path: str | Path) -> Dict[str, Any]:
    """Load a YAML behavior matrix file and normalise the structure.

    Returns a dictionary containing component metadata, monitor registry data,
    and parsed :class:`BehaviorRow` instances.
    """

    raw = _load_yaml(path)
    components = raw.get("components", [])
    monitor_registry = raw.get("monitors", [])
    rows = [_parse_row(entry) for entry in raw.get("behavior_matrix", [])]

    return {
        "components": components,
        "monitors": monitor_registry,
        "rows": rows,
    }


def _load_yaml(path: str | Path) -> Dict[str, Any]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):  # pragma: no cover - defensive
        raise ValueError("Behavior matrix YAML must contain a top-level mapping")
    return data


def _parse_row(entry: Dict[str, Any]) -> BehaviorRow:
    context_raw = entry.get("context", {})
    expect_raw = entry.get("expect", {})
    monitors_raw = entry.get("monitors", [])

    context = BehaviorContext(
        start_state=context_raw["start_state"],
        warm_from_fault_id=context_raw.get("warm_from_fault_id"),
    )
    expect = ExpectedBehavior(
        end_state=expect_raw["end_state"],
        notes=expect_raw.get("notes"),
    )
    monitors = [
        MonitorSpec(
            id=monitor_entry["id"],
            plugin=monitor_entry["plugin"],
            params=monitor_entry.get("params", {}),
        )
        for monitor_entry in monitors_raw
    ]

    return BehaviorRow(
        fault_id=entry["fault_id"],
        component_id=entry["component_id"],
        asil=entry["asil"],
        context=context,
        phase=entry["phase"],
        expect=expect,
        monitors=monitors,
        priority=float(entry["priority"]),
        enabled=bool(entry.get("enabled", True)),
        event_type=entry.get("event_type"),
        event_family=entry.get("event_family"),
        iso_environments=_ensure_list(entry.get("iso", {}).get("environments")),
        iso_methods_test=_ensure_list(entry.get("iso", {}).get("methods", {}).get("test")),
        trace_req_ids=_ensure_list(entry.get("trace", {}).get("req_ids")),
    )


__all__ = ["load_behavior_matrix"]
