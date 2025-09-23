"""Candidate generation for Behavior Matrix rows."""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

from .policy import Policy


@dataclass(slots=True)
class Candidate:
    tc_id: str
    phase: str
    fault_id: str
    component_id: str
    start_state: str
    warm_from_fault_id: str | None
    end_state: str
    transition_name: str
    monitors: List[str]
    max_time_ms: int
    tolerance_ms: int
    priority: float
    batch_key: tuple[str, str]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "tc_id": self.tc_id,
            "phase": self.phase,
            "fault_id": self.fault_id,
            "component_id": self.component_id,
            "start_state": self.start_state,
            "warm_from_fault_id": self.warm_from_fault_id,
            "end_state": self.end_state,
            "transition_name": self.transition_name,
            "monitors": list(self.monitors),
            "max_time_ms": self.max_time_ms,
            "tolerance_ms": self.tolerance_ms,
            "priority": self.priority,
        }


def _strip_empty(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _strip_empty(v) for k, v in value.items() if v not in (None, [], {})}
    if isinstance(value, list):
        return [
            _strip_empty(v)
            for v in value
            if v not in (None, [], {})
        ]
    return value


def _canonical_json(data: Dict[str, Any]) -> str:
    cleaned = _strip_empty(data)
    return json.dumps(cleaned, sort_keys=True, separators=(",", ":"))


def _tc_hash(data: Dict[str, Any]) -> str:
    canonical = _canonical_json(data)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _transition_candidate(row: dict[str, Any], seed: int) -> Candidate:
    base = {
        "fault_id": row["fault_id"],
        "component_id": row["component_id"],
        "context": row["context"],
        "expect": row["expect"],
        "timing": row["timing"],
        "paramset": {},
        "phase": "transition",
        "seed": seed,
    }
    tc_id = _tc_hash(base)
    return Candidate(
        tc_id=tc_id,
        phase="transition",
        fault_id=row["fault_id"],
        component_id=row["component_id"],
        start_state=row["context"]["start_state"],
        warm_from_fault_id=row["context"].get("warm_from_fault_id"),
        end_state=row["expect"]["end_state"],
        transition_name=row["expect"]["transition_name"],
        monitors=list(row["monitors"]),
        max_time_ms=row["timing"]["max_time_ms"],
        tolerance_ms=row["timing"]["tolerance_ms"],
        priority=row["priority"],
        batch_key=(row["fault_id"], row["component_id"]),
    )


def _recovery_candidate(row: dict[str, Any], seed: int) -> Candidate:
    context = {
        "start_state": row["expect"]["end_state"],
        "warm_from_fault_id": row["fault_id"],
    }
    base = {
        "fault_id": row["fault_id"],
        "component_id": row["component_id"],
        "context": context,
        "expect": row["expect"],
        "timing": row["timing"],
        "paramset": {},
        "phase": "recovery",
        "seed": seed,
    }
    tc_id = _tc_hash(base)
    return Candidate(
        tc_id=tc_id,
        phase="recovery",
        fault_id=row["fault_id"],
        component_id=row["component_id"],
        start_state=context["start_state"],
        warm_from_fault_id=context["warm_from_fault_id"],
        end_state=row["expect"]["end_state"],
        transition_name=row["expect"]["transition_name"],
        monitors=list(row["monitors"]),
        max_time_ms=row["timing"]["max_time_ms"],
        tolerance_ms=row["timing"]["tolerance_ms"],
        priority=row["priority"],
        batch_key=(row["fault_id"], row["component_id"]),
    )


def generate_candidates(
    matrix: Iterable[dict[str, Any]],
    seed: int,
    policy_data: dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """Generate deterministic candidates from the matrix rows."""

    policy = Policy.from_dict(policy_data, default_seed=seed)

    rng = random.Random(policy.seed)
    candidates: List[Candidate] = []
    for row in matrix:
        if row["priority"] < policy.min_priority:
            continue
        if policy.include_transition:
            candidates.append(_transition_candidate(row, policy.seed))
        if policy.include_recovery:
            candidates.append(_recovery_candidate(row, policy.seed))

    # Deterministic ordering with pseudo-random tie breaking.
    ordering = [(candidate, rng.random()) for candidate in candidates]
    ordering.sort(
        key=lambda item: (
            -item[0].priority,
            item[1],
            item[0].tc_id,
        )
    )
    candidates = [item[0] for item in ordering]

    if policy.max_candidates is not None:
        candidates = candidates[: policy.max_candidates]

    return [candidate.as_dict() for candidate in candidates]


__all__ = ["generate_candidates", "Candidate"]
