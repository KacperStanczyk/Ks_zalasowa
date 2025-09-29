import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from behavior_matrix import (
    build_coverage_heatmap,
    build_iso_compliance_summary,
    build_state_transition_graph,
    build_traceability_matrix,
    generate_test_cases,
    load_behavior_matrix,
)
from behavior_matrix.plugins.mock_monitors import build_mock_registry


@pytest.fixture(scope="module")
def matrix_data() -> dict:
    path = Path(__file__).parent / "data" / "behavior_matrix_sample.yaml"
    return load_behavior_matrix(path)


@pytest.fixture(scope="module")
def rows(matrix_data):
    return matrix_data["rows"]


@pytest.fixture(scope="module")
def generated_cases(rows):
    return generate_test_cases(rows)


def test_test_case_ids_are_stable(generated_cases):
    ids = [case.tc_id for case in generated_cases]
    assert ids == [
        "TC_001_COMP_BMS_FI_BMS_OVERVOLT_TRA_E1",
        "TC_002_COMP_BMS_FI_BMS_OVERVOLT_REC_E1",
        "TC_004_COMP_MCU_FI_MCU_RECOVER_REC_E3",
    ]


def test_visualization_data_shapes(rows):
    transition_graph = build_state_transition_graph(rows, component_id="COMP.BMS")
    assert "NORMAL" in transition_graph

    heatmap = build_coverage_heatmap(rows)
    assert heatmap["COMP.BMS"][1] == "covered"
    assert heatmap["COMP.MCU"][3] == "covered"

    trace_matrix = build_traceability_matrix(rows)
    assert trace_matrix["REQ-005"].count("FI.BMS.OVERVOLT") == 2

    iso_summary = build_iso_compliance_summary(rows)
    assert iso_summary["asil"]["D"] == 2
    assert iso_summary["asil"]["C"] == 2


def test_generated_cases_are_callable(generated_cases):
    registry = build_mock_registry()
    for case in generated_cases:
        result = case.execute(registry=registry)
        assert result.passed is True
