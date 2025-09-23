import json
import os
import subprocess
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from behavior_matrix.generator import generate_candidates
from behavior_matrix.io import load_matrix
from behavior_matrix.validator import DuplicateMatrixRowError, validate_matrix

EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "behavior_matrix"


def test_validation_passes_for_sample_matrix():
    document = load_matrix(EXAMPLES / "matrix.yaml")
    validated = validate_matrix(document)
    assert len(validated.matrix) == 3


def test_duplicate_detection(tmp_path):
    document = load_matrix(EXAMPLES / "matrix.yaml")
    duplicate_row = document["matrix"][0].copy()
    document["matrix"].append(duplicate_row)
    with pytest.raises(DuplicateMatrixRowError):
        validate_matrix(document)


def test_generate_candidates_deterministic():
    document = load_matrix(EXAMPLES / "matrix.yaml")
    validated = validate_matrix(document)
    first = generate_candidates(validated.matrix, seed=42)
    second = generate_candidates(validated.matrix, seed=42)
    assert first == second
    assert all("tc_id" in candidate for candidate in first)


def test_cli_validate(tmp_path):
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")}
    cmd = [
        "python",
        "-m",
        "behavior_matrix.cli",
        "validate",
        "--in",
        str(EXAMPLES / "matrix.yaml"),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False, env=env)
    assert result.returncode == 0, result.stderr


def test_cli_gen_creates_output(tmp_path):
    output = tmp_path / "candidates.json"
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")}
    cmd = [
        "python",
        "-m",
        "behavior_matrix.cli",
        "gen",
        "--in",
        str(EXAMPLES / "matrix.yaml"),
        "--out",
        str(output),
        "--seed",
        "99",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False, env=env)
    assert result.returncode == 0, result.stderr
    data = json.loads(output.read_text())
    assert isinstance(data, list)
    assert data, "Expected at least one candidate"


def test_cli_viz_creates_outputs(tmp_path):
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")}
    cmd = [
        "python",
        "-m",
        "behavior_matrix.cli",
        "viz",
        "--in",
        str(EXAMPLES / "matrix.yaml"),
        "--out",
        str(tmp_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False, env=env)
    assert result.returncode == 0, result.stderr
    expected = {
        f"transitions_COMP.BCM.png",
        f"transitions_COMP.ADAS.png",
        "heatmap.png",
        "timing_pivot.png",
        "tc_table.html",
    }
    produced = {path.name for path in tmp_path.iterdir()}
    assert expected.issubset(produced)
