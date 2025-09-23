"""Input/output helpers for Behavior Matrix data."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List

import yaml

MatrixType = Dict[str, Any]


class UnsupportedMatrixFormatError(ValueError):
    """Raised when the matrix file extension is unsupported."""


def _load_yaml(path: Path) -> MatrixType:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _parse_semicolon_list(value: str | None) -> List[str]:
    if value is None or value == "":
        return []
    return [item.strip() for item in value.split(";") if item.strip()]


def _load_csv(path: Path) -> MatrixType:
    with path.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows: List[Dict[str, Any]] = []
        for raw_row in reader:
            row = {
                "fault_id": raw_row["fault_id"],
                "component_id": raw_row["component_id"],
                "context": {
                    "start_state": raw_row["context.start_state"],
                    "warm_from_fault_id": raw_row["context.warm_from_fault_id"] or None,
                },
                "expect": {
                    "end_state": raw_row["expect.end_state"],
                    "transition_name": raw_row["expect.transition_name"],
                },
                "monitors": _parse_semicolon_list(raw_row["monitors"]),
                "timing": {
                    "max_time_ms": int(raw_row["timing.max_time_ms"]),
                    "tolerance_ms": int(raw_row["timing.tolerance_ms"]),
                    "measurement_uncertainty": int(
                        raw_row["timing.measurement_uncertainty"]
                    ),
                },
                "priority": float(raw_row["priority"]),
                "trace": {
                    "req_ids": _parse_semicolon_list(raw_row["trace.req_ids"]),
                },
                "version": raw_row["version"],
            }
            tags = _parse_semicolon_list(raw_row.get("tags"))
            if tags:
                row["tags"] = tags
            rows.append(row)
    return {"matrix": rows}


def load_matrix(path: str | Path) -> MatrixType:
    """Load a matrix document from YAML or CSV."""

    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml", ".json"}:
        return _load_yaml(path)
    if suffix == ".csv":
        return _load_csv(path)
    raise UnsupportedMatrixFormatError(f"Unsupported matrix format: {path.suffix}")


def save_json(path: str | Path, data: Any) -> None:
    path = Path(path)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


__all__ = ["load_matrix", "save_json", "UnsupportedMatrixFormatError"]
