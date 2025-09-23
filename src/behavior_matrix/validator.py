"""Validation utilities for Behavior Matrix data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List

from jsonschema import Draft202012Validator

from .schema import SCHEMA


class SchemaValidationError(Exception):
    """Raised when schema validation fails."""

    def __init__(self, errors: List[str]):
        super().__init__("\n".join(errors))
        self.errors = errors


class DuplicateMatrixRowError(Exception):
    """Raised when duplicate matrix rows are detected."""

    def __init__(self, duplicates: list[tuple[int, int]]):
        msg = "Duplicate rows detected: " + ", ".join(
            f"rows {first + 1} and {second + 1}" for first, second in duplicates
        )
        super().__init__(msg)
        self.duplicates = duplicates


_validator = Draft202012Validator(SCHEMA)


@dataclass(slots=True)
class ValidatedMatrix:
    matrix: List[dict[str, Any]]


def validate_matrix(document: dict[str, Any]) -> ValidatedMatrix:
    """Validate the raw document according to schema and business rules."""

    schema_errors = []
    for error in sorted(_validator.iter_errors(document), key=lambda e: e.path):
        pointer = "/" + "/".join(str(part) for part in error.absolute_path)
        pointer = pointer if pointer != "/" else ""
        schema_errors.append(f"{pointer or '/'}: {error.message}")
    if schema_errors:
        raise SchemaValidationError(schema_errors)

    matrix = document.get("matrix", [])
    business_errors: List[str] = []
    seen: dict[tuple[Any, ...], int] = {}
    duplicates: list[tuple[int, int]] = []

    for idx, row in enumerate(matrix):
        key = (
            row["fault_id"],
            row["component_id"],
            row["context"]["start_state"],
            row["context"].get("warm_from_fault_id"),
        )
        if key in seen:
            duplicates.append((seen[key], idx))
        else:
            seen[key] = idx

        monitors = row.get("monitors", [])
        if len(monitors) != len(set(monitors)):
            business_errors.append(
                f"/matrix/{idx}/monitors: duplicate monitor_id entries are not allowed"
            )

    if business_errors:
        raise SchemaValidationError(business_errors)

    if duplicates:
        raise DuplicateMatrixRowError(duplicates)

    return ValidatedMatrix(matrix=list(matrix))


__all__ = ["validate_matrix", "SchemaValidationError", "DuplicateMatrixRowError", "ValidatedMatrix"]
