"""Command line interface for the Behavior Matrix toolkit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .generator import generate_candidates
from .io import UnsupportedMatrixFormatError, load_matrix, save_json
from .validator import (
    DuplicateMatrixRowError,
    SchemaValidationError,
    validate_matrix,
)
from .viz import generate_visualisations

EXIT_OK = 0
EXIT_SCHEMA_ERROR = 2
EXIT_DUPLICATES = 3
EXIT_UNEXPECTED = 1


def _load_policy(path: str | None) -> dict[str, Any] | None:
    if not path:
        return None
    with Path(path).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def cmd_validate(args: argparse.Namespace) -> int:
    try:
        document = load_matrix(args.input)
        validate_matrix(document)
    except SchemaValidationError as exc:
        for message in exc.errors:
            print(message, file=sys.stderr)
        return EXIT_SCHEMA_ERROR
    except DuplicateMatrixRowError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_DUPLICATES
    return EXIT_OK


def cmd_gen(args: argparse.Namespace) -> int:
    try:
        document = load_matrix(args.input)
        validated = validate_matrix(document)
    except SchemaValidationError as exc:
        for message in exc.errors:
            print(message, file=sys.stderr)
        return EXIT_SCHEMA_ERROR
    except DuplicateMatrixRowError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_DUPLICATES

    try:
        policy = _load_policy(args.policy)
    except FileNotFoundError:
        print(f"Policy file not found: {args.policy}", file=sys.stderr)
        return EXIT_SCHEMA_ERROR
    except json.JSONDecodeError as exc:
        print(f"Invalid policy JSON: {exc}", file=sys.stderr)
        return EXIT_SCHEMA_ERROR
    candidates = generate_candidates(validated.matrix, seed=args.seed, policy_data=policy)
    save_json(args.output, candidates)
    print(f"Generated {len(candidates)} candidates → {args.output}")
    return EXIT_OK


def cmd_viz(args: argparse.Namespace) -> int:
    try:
        document = load_matrix(args.input)
        validated = validate_matrix(document)
    except SchemaValidationError as exc:
        for message in exc.errors:
            print(message, file=sys.stderr)
        return EXIT_SCHEMA_ERROR
    except DuplicateMatrixRowError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_DUPLICATES

    generate_visualisations(validated.matrix, args.output)
    print(f"Visualisations written to {args.output}")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bm", description="Behavior Matrix toolkit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_cmd = subparsers.add_parser("validate", help="Validate a matrix file")
    validate_cmd.add_argument("--in", dest="input", required=True, help="Input matrix file")
    validate_cmd.set_defaults(func=cmd_validate)

    gen_cmd = subparsers.add_parser("gen", help="Generate TC candidates")
    gen_cmd.add_argument("--in", dest="input", required=True, help="Input matrix file")
    gen_cmd.add_argument("--out", dest="output", required=True, help="Output JSON file")
    gen_cmd.add_argument("--seed", dest="seed", type=int, default=1337)
    gen_cmd.add_argument("--policy", dest="policy")
    gen_cmd.set_defaults(func=cmd_gen)

    viz_cmd = subparsers.add_parser("viz", help="Create visualisations")
    viz_cmd.add_argument("--in", dest="input", required=True, help="Input matrix file")
    viz_cmd.add_argument("--out", dest="output", required=True, help="Output directory")
    viz_cmd.set_defaults(func=cmd_viz)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except UnsupportedMatrixFormatError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_SCHEMA_ERROR
    except Exception as exc:  # pragma: no cover
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return EXIT_UNEXPECTED


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
