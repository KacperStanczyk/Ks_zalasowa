"""Data models for the Behavior Matrix MVP."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class MonitorSpec:
    """Specification for a monitor entry within the matrix."""

    id: str
    plugin: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BehaviorContext:
    """Execution context for a test case."""

    start_state: str
    warm_from_fault_id: Optional[str] = None


@dataclass(frozen=True)
class ExpectedBehavior:
    """Expected outcome of a behavior matrix entry."""

    end_state: str
    notes: Optional[str] = None


@dataclass(frozen=True)
class BehaviorRow:
    """A single row in the behavior matrix source data."""

    fault_id: str
    component_id: str
    asil: str
    context: BehaviorContext
    phase: str
    expect: ExpectedBehavior
    monitors: List[MonitorSpec]
    priority: float
    enabled: bool
    event_type: Optional[int] = None
    event_family: Optional[str] = None
    iso_environments: Optional[List[str]] = None
    iso_methods_test: Optional[List[str]] = None
    trace_req_ids: Optional[List[str]] = None


@dataclass(frozen=True)
class TestCase:
    """Representation of an executable test case generated from the matrix."""

    tc_id: str
    row: BehaviorRow

    def execute(self, registry: "MonitorRegistry") -> "TestResult":
        """Execute the test case using the provided registry."""
        monitor_results: List[MonitorResult] = []
        for monitor in self.row.monitors:
            plugin = registry.get_plugin(monitor.plugin)
            monitor_results.append(plugin.evaluate(self, monitor))
        passed = all(result.passed for result in monitor_results)
        return TestResult(test_case=self, monitor_results=monitor_results, passed=passed)


@dataclass(frozen=True)
class MonitorResult:
    """Outcome of an individual monitor evaluation."""

    monitor_id: str
    passed: bool
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TestResult:
    """Container that aggregates results from all monitors."""

    test_case: TestCase
    monitor_results: List[MonitorResult]
    passed: bool


class MonitorPlugin:
    """Base class for monitor plugins used by the registry."""

    name: str

    def evaluate(self, test_case: TestCase, monitor: MonitorSpec) -> MonitorResult:  # pragma: no cover - interface
        raise NotImplementedError


class MonitorRegistry:
    """Simple registry that resolves monitor plugin names."""

    def __init__(self) -> None:
        self._plugins: Dict[str, MonitorPlugin] = {}

    def register(self, plugin: MonitorPlugin) -> None:
        self._plugins[plugin.name] = plugin

    def get_plugin(self, name: str) -> MonitorPlugin:
        try:
            return self._plugins[name]
        except KeyError as exc:  # pragma: no cover - defensive
            raise LookupError(f"Unknown monitor plugin: {name}") from exc

    def all_plugins(self) -> Dict[str, MonitorPlugin]:
        """Expose registered plugins for inspection or export."""

        return dict(self._plugins)


__all__ = [
    "MonitorSpec",
    "BehaviorContext",
    "ExpectedBehavior",
    "BehaviorRow",
    "TestCase",
    "MonitorResult",
    "TestResult",
    "MonitorPlugin",
    "MonitorRegistry",
]
