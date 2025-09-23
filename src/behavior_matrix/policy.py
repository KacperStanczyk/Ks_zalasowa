"""Policy options for candidate generation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Policy:
    """Filtering options used during candidate generation."""

    include_transition: bool = True
    include_recovery: bool = True
    min_priority: float = 0.0
    max_candidates: int | None = 1000
    seed: int = 1337

    @classmethod
    def from_dict(cls, data: dict[str, object] | None, default_seed: int) -> "Policy":
        if data is None:
            return cls(seed=default_seed)
        kwargs = {
            "include_transition": bool(data.get("include_transition", True)),
            "include_recovery": bool(data.get("include_recovery", True)),
            "min_priority": float(data.get("min_priority", 0.0)),
            "max_candidates": data.get("max_candidates"),
            "seed": int(data.get("seed", default_seed)),
        }
        max_candidates = kwargs["max_candidates"]
        if max_candidates is not None:
            kwargs["max_candidates"] = int(max_candidates)
        return cls(**kwargs)
