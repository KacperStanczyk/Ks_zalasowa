"""Quick visualisation prototypes for the Behavior Matrix MVP."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

try:  # pragma: no cover - optional dependency
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover - optional dependency
    plt = None

from .model import BehaviorRow


def build_state_transition_graph(
    rows: Iterable[BehaviorRow], component_id: Optional[str] = None, output_path: Optional[str | Path] = None
) -> Dict[str, List[Tuple[str, str]]]:
    """Construct a simplified state transition graph."""

    transitions: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
    for row in rows:
        if component_id and row.component_id != component_id:
            continue
        transitions[row.context.start_state].append((row.expect.end_state, row.phase))
    if output_path and plt:
        _plot_state_graph(transitions, output_path)
    return transitions


def build_coverage_heatmap(
    rows: Iterable[BehaviorRow], output_path: Optional[str | Path] = None
) -> Dict[str, Dict[int, str]]:
    """Generate coverage data grouped by component and event type."""

    coverage: Dict[str, Dict[int, str]] = defaultdict(dict)
    for row in rows:
        if row.event_type is None:
            continue
        status = "covered" if row.enabled else "disabled"
        coverage[row.component_id][row.event_type] = status
    if output_path and plt:
        _plot_heatmap(coverage, output_path)
    return coverage


def build_traceability_matrix(rows: Iterable[BehaviorRow]) -> Dict[str, List[str]]:
    matrix: Dict[str, List[str]] = defaultdict(list)
    for row in rows:
        for req_id in row.trace_req_ids or ["UNSPECIFIED"]:
            matrix[req_id].append(row.fault_id)
    return matrix


def build_iso_compliance_summary(rows: Iterable[BehaviorRow]) -> Dict[str, Counter]:
    asil_counter: Counter = Counter()
    env_counter: Counter = Counter()
    method_counter: Counter = Counter()
    for row in rows:
        asil_counter[row.asil] += 1
        env_counter.update(row.iso_environments or [])
        method_counter.update(row.iso_methods_test or [])
    return {
        "asil": asil_counter,
        "environments": env_counter,
        "methods": method_counter,
    }


def _plot_state_graph(transitions: Dict[str, List[Tuple[str, str]]], output_path: str | Path) -> None:
    positions = {}
    fig, ax = plt.subplots(figsize=(6, 4))  # type: ignore[union-attr]
    ax.set_title("State Transition Graph (Prototype)")
    y = 0
    for idx, (state, edges) in enumerate(transitions.items()):
        positions[state] = (idx, y)
        ax.scatter(idx, y, color="tab:blue")
        ax.text(idx, y + 0.1, state, ha="center")
        for target_state, phase in edges:
            target_idx = idx + 0.5
            target_y = y - 0.5
            ax.annotate(
                "",
                xy=(target_idx, target_y),
                xytext=(idx, y),
                arrowprops=dict(arrowstyle="->", color="tab:red" if phase == "transition" else "tab:green"),
            )
            ax.text(target_idx, target_y - 0.1, f"{phase}\n→ {target_state}", ha="center")
    ax.axis("off")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def _plot_heatmap(coverage: Dict[str, Dict[int, str]], output_path: str | Path) -> None:
    components = list(coverage.keys())
    events = sorted({event for statuses in coverage.values() for event in statuses})
    status_to_value = {"covered": 1, "disabled": 0, "missing": -1}
    matrix = []
    for component in components:
        row = []
        for event in events:
            status = coverage[component].get(event, "missing")
            row.append(status_to_value[status])
        matrix.append(row)
    fig, ax = plt.subplots(figsize=(0.8 * len(events) + 1, 0.6 * len(components) + 1))  # type: ignore[union-attr]
    heatmap = ax.imshow(matrix, cmap="RdYlGn", vmin=-1, vmax=1)
    ax.set_xticks(range(len(events)))
    ax.set_xticklabels(events)
    ax.set_yticks(range(len(components)))
    ax.set_yticklabels(components)
    ax.set_title("Coverage Heatmap (Prototype)")
    for i, component in enumerate(components):
        for j, event in enumerate(events):
            status = coverage[component].get(event, "missing")
            ax.text(j, i, status[0].upper(), ha="center", va="center", color="black")
    fig.colorbar(heatmap, ax=ax, fraction=0.046, pad=0.04)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


__all__ = [
    "build_state_transition_graph",
    "build_coverage_heatmap",
    "build_traceability_matrix",
    "build_iso_compliance_summary",
]
