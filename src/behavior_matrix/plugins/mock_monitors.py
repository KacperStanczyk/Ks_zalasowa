"""Mock monitor plugins used by the MVP."""

from __future__ import annotations

import random
from ..model import MonitorPlugin, MonitorRegistry, MonitorResult, TestCase


class RangeMonitor(MonitorPlugin):
    name = "range"

    def evaluate(self, test_case: TestCase, monitor) -> MonitorResult:  # type: ignore[override]
        params = monitor.params
        value = params.get("expected", 0)
        lower = params.get("min", value)
        upper = params.get("max", value)
        passed = lower <= value <= upper
        details = {
            "value": value,
            "range": (lower, upper),
            "component": test_case.row.component_id,
            "fault_id": test_case.row.fault_id,
        }
        return MonitorResult(monitor_id=monitor.id, passed=passed, details=details)


class StateMonitor(MonitorPlugin):
    name = "state"

    def evaluate(self, test_case: TestCase, monitor) -> MonitorResult:  # type: ignore[override]
        expected_state = test_case.row.expect.end_state
        passed = expected_state in {test_case.row.expect.end_state, test_case.row.context.start_state}
        details = {
            "expected": expected_state,
            "start": test_case.row.context.start_state,
            "phase": test_case.row.phase,
        }
        return MonitorResult(monitor_id=monitor.id, passed=passed, details=details)


class TimingMonitor(MonitorPlugin):
    name = "timing"

    def evaluate(self, test_case: TestCase, monitor) -> MonitorResult:  # type: ignore[override]
        budget_ms = monitor.params.get("budget_ms", 100)
        simulated = random.randint(budget_ms // 2, budget_ms)  # deterministic enough for demo
        passed = simulated <= budget_ms
        details = {
            "budget_ms": budget_ms,
            "observed_ms": simulated,
        }
        return MonitorResult(monitor_id=monitor.id, passed=passed, details=details)


def build_mock_registry() -> MonitorRegistry:
    registry = MonitorRegistry()
    for plugin in (RangeMonitor(), StateMonitor(), TimingMonitor()):
        registry.register(plugin)
    return registry


__all__ = ["build_mock_registry", "RangeMonitor", "StateMonitor", "TimingMonitor"]
