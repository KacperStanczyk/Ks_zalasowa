"""JSON schema definition for Behavior Matrix."""

from __future__ import annotations

SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.com/behavior-matrix.schema.json",
    "type": "object",
    "required": ["matrix"],
    "properties": {
        "matrix": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": [
                    "fault_id",
                    "component_id",
                    "context",
                    "expect",
                    "monitors",
                    "timing",
                    "priority",
                    "trace",
                    "version",
                ],
                "properties": {
                    "fault_id": {"type": "string", "minLength": 1},
                    "component_id": {"type": "string", "minLength": 1},
                    "context": {
                        "type": "object",
                        "required": ["start_state", "warm_from_fault_id"],
                        "properties": {
                            "start_state": {"type": "string", "minLength": 1},
                            "warm_from_fault_id": {"type": ["string", "null"]},
                        },
                        "additionalProperties": False,
                    },
                    "expect": {
                        "type": "object",
                        "required": ["end_state", "transition_name"],
                        "properties": {
                            "end_state": {"type": "string", "minLength": 1},
                            "transition_name": {"type": "string", "minLength": 1},
                        },
                        "additionalProperties": False,
                    },
                    "monitors": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"type": "string", "minLength": 1},
                    },
                    "timing": {
                        "type": "object",
                        "required": [
                            "max_time_ms",
                            "tolerance_ms",
                            "measurement_uncertainty",
                        ],
                        "properties": {
                            "max_time_ms": {"type": "integer", "minimum": 1},
                            "tolerance_ms": {"type": "integer", "minimum": 0},
                            "measurement_uncertainty": {
                                "type": "integer",
                                "minimum": 0,
                            },
                        },
                        "additionalProperties": False,
                    },
                    "priority": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "trace": {
                        "type": "object",
                        "required": ["req_ids"],
                        "properties": {
                            "req_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "uniqueItems": True,
                            }
                        },
                        "additionalProperties": False,
                    },
                    "version": {
                        "type": "string",
                        "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$",
                    },
                    "notes": {"type": "string"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "uniqueItems": True,
                    },
                },
                "additionalProperties": False,
            },
        }
    },
    "additionalProperties": False,
}
