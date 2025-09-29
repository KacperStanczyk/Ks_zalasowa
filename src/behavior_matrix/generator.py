"""Test case generator for the Behavior Matrix MVP."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence

from .model import BehaviorRow, MonitorPlugin, MonitorRegistry, TestCase
from .plugins.mock_monitors import build_mock_registry


@dataclass(frozen=True)
class GenerationSettings:
    """Settings controlling deterministic TC ID construction."""

    prefix: str = "TC"


def generate_test_cases(
    rows: Sequence[BehaviorRow],
    settings: GenerationSettings | None = None,
    registry: MonitorRegistry | None = None,
) -> List[TestCase]:
    """Create executable test cases for the provided matrix rows."""

    if settings is None:
        settings = GenerationSettings()
    if registry is None:
        registry = build_mock_registry()

    cases: List[TestCase] = []
    for index, row in enumerate(rows, start=1):
        if not row.enabled:
            continue
        tc_id = _build_tc_id(settings.prefix, index, row)
        cases.append(TestCase(tc_id=tc_id, row=row))
    _attach_registry(registry)
    return cases


def _build_tc_id(prefix: str, index: int, row: BehaviorRow) -> str:
    event_fragment = f"E{row.event_type}" if row.event_type is not None else "Ena"
    normalized_fault = row.fault_id.replace(".", "_")
    normalized_component = row.component_id.replace(".", "_")
    phase_fragment = row.phase[0:3].upper()
    return f"{prefix}_{index:03d}_{normalized_component}_{normalized_fault}_{phase_fragment}_{event_fragment}"


def _attach_registry(registry: MonitorRegistry) -> None:
    """Attach the registry globally for quick access during pytest runs."""

    GLOBAL_REGISTRY.clear()
    for plugin in registry.all_plugins().values():
        GLOBAL_REGISTRY[plugin.name] = plugin


def get_global_plugin(name: str) -> MonitorPlugin:
    return GLOBAL_REGISTRY[name]


GLOBAL_REGISTRY: Dict[str, MonitorPlugin] = {}


__all__ = ["GenerationSettings", "generate_test_cases", "get_global_plugin"]
