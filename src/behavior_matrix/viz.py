"""Visualization utilities for Behavior Matrix."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Sequence

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import plotly.graph_objects as go

from .generator import generate_candidates


def _ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _transition_graphs(matrix: Sequence[dict], output_dir: Path) -> None:
    grouped = defaultdict(list)
    for row in matrix:
        grouped[row["component_id"]].append(row)

    for component, rows in grouped.items():
        graph = nx.MultiDiGraph()
        for row in rows:
            start = row["context"]["start_state"]
            end = row["expect"]["end_state"]
            label = f"{row['fault_id']}\n{row['expect']['transition_name']}"
            graph.add_edge(start, end, label=label)

        plt.figure(figsize=(8, 6))
        pos = nx.spring_layout(graph, seed=42)
        nx.draw_networkx_nodes(graph, pos, node_color="#1f77b4", node_size=1500)
        nx.draw_networkx_labels(graph, pos, font_color="white")
        nx.draw_networkx_edges(graph, pos, arrowstyle="->", arrowsize=20, edge_color="#333333")
        edge_labels = {(u, v, k): d["label"] for u, v, k, d in graph.edges(keys=True, data=True)}
        nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_color="#444444")
        plt.axis("off")
        output_path = output_dir / f"transitions_{component}.png"
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()


def _heatmap(matrix: Sequence[dict], output_dir: Path) -> None:
    df = pd.DataFrame(
        [
            {
                "fault_id": row["fault_id"],
                "component_id": row["component_id"],
                "priority": row["priority"],
                "transition_name": row["expect"]["transition_name"],
            }
            for row in matrix
        ]
    )
    counts = df.groupby(["fault_id", "component_id"]).size().unstack(fill_value=0)

    fig, ax = plt.subplots(figsize=(8, 6))
    cax = ax.imshow(counts.values, cmap="viridis")
    ax.set_xticks(range(len(counts.columns)))
    ax.set_xticklabels(counts.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(counts.index)))
    ax.set_yticklabels(counts.index)
    ax.set_title("Heatmap pokrycia (liczba wierszy)")
    fig.colorbar(cax, ax=ax, label="Liczba wierszy")

    for i in range(counts.shape[0]):
        for j in range(counts.shape[1]):
            value = counts.iat[i, j]
            ax.text(j, i, str(value), ha="center", va="center", color="white")

    output_path = output_dir / "heatmap.png"
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)


def _timing_pivot(matrix: Sequence[dict], output_dir: Path) -> None:
    df = pd.DataFrame(
        [
            {
                "fault_id": row["fault_id"],
                "component_id": row["component_id"],
                "max_time_ms": row["timing"]["max_time_ms"],
                "tolerance_ms": row["timing"]["tolerance_ms"],
            }
            for row in matrix
        ]
    )
    summary = (
        df.groupby(["fault_id", "component_id"])
        .agg(
            max_time_min=("max_time_ms", "min"),
            max_time_mean=("max_time_ms", "mean"),
            max_time_max=("max_time_ms", "max"),
            tol_min=("tolerance_ms", "min"),
            tol_mean=("tolerance_ms", "mean"),
            tol_max=("tolerance_ms", "max"),
        )
        .reset_index()
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axis("off")
    col_labels = [
        "max_time_min",
        "max_time_mean",
        "max_time_max",
        "tol_min",
        "tol_mean",
        "tol_max",
    ]
    cell_values = []
    row_labels = []
    for _, row in summary.iterrows():
        row_labels.append(f"{row['fault_id']} | {row['component_id']}")
        cell_values.append(
            [
                int(row["max_time_min"]),
                f"{row['max_time_mean']:.1f}",
                int(row["max_time_max"]),
                int(row["tol_min"]),
                f"{row['tol_mean']:.1f}",
                int(row["tol_max"]),
            ]
        )

    table = ax.table(
        cellText=cell_values,
        colLabels=col_labels,
        rowLabels=row_labels,
        loc="center",
    )
    table.scale(1, 1.5)
    ax.set_title("Pivot czasów")
    output_path = output_dir / "timing_pivot.png"
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)


def _candidate_table(matrix: Sequence[dict], output_dir: Path) -> None:
    candidates = generate_candidates(matrix, seed=1337)
    fig = go.Figure(
        data=[
            go.Table(
                header=dict(
                    values=[
                        "tc_id",
                        "phase",
                        "fault_id",
                        "component_id",
                        "start_state",
                        "end_state",
                        "priority",
                    ],
                    fill_color="#4b9cd3",
                    font=dict(color="white"),
                ),
                cells=dict(
                    values=[
                        [c["tc_id"] for c in candidates],
                        [c["phase"] for c in candidates],
                        [c["fault_id"] for c in candidates],
                        [c["component_id"] for c in candidates],
                        [c["start_state"] for c in candidates],
                        [c["end_state"] for c in candidates],
                        [c["priority"] for c in candidates],
                    ],
                ),
            )
        ]
    )
    fig.update_layout(title="Kandydaci TC")
    output_path = output_dir / "tc_table.html"
    fig.write_html(output_path)


def generate_visualisations(matrix: Sequence[dict], output_dir: str | Path) -> None:
    output_path = Path(output_dir)
    _ensure_output_dir(output_path)
    _transition_graphs(matrix, output_path)
    _heatmap(matrix, output_path)
    _timing_pivot(matrix, output_path)
    _candidate_table(matrix, output_path)


__all__ = ["generate_visualisations"]
