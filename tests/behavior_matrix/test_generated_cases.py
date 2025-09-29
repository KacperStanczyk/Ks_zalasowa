import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from behavior_matrix import generate_test_cases, load_behavior_matrix
from behavior_matrix.plugins.mock_monitors import build_mock_registry


@pytest.fixture(scope="module")
def sample_cases():
    matrix_path = Path(__file__).parent.parent / "data" / "behavior_matrix_sample.yaml"
    matrix = load_behavior_matrix(matrix_path)
    return generate_test_cases(matrix["rows"])


@pytest.fixture(scope="module")
def registry():
    return build_mock_registry()


@pytest.mark.parametrize("case_index", [0, 1, 2])
def test_generated_case_execution(sample_cases, registry, case_index):
    case = sample_cases[case_index]
    result = case.execute(registry)
    assert result.passed is True, f"Generated test case {case.tc_id} failed"
