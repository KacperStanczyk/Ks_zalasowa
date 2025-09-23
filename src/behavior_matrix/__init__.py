"""Behavior Matrix toolkit for validation, generation, and visualization."""

from .io import load_matrix
from .validator import validate_matrix
from .generator import generate_candidates
from .policy import Policy

__all__ = [
    "load_matrix",
    "validate_matrix",
    "generate_candidates",
    "Policy",
]
