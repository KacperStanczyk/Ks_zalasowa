"""Simple Reports view showing weekly task stats."""
from __future__ import annotations

from datetime import date
from PySide6.QtWidgets import QVBoxLayout, QWidget, QLabel

from services.tasks_service import get_tasks_for_week
from services.week_service import iso_week


class ReportsView(QWidget):
    """Display basic statistics about tasks for the current week."""

    def __init__(self, conn):
        super().__init__()

        self.conn = conn
        layout = QVBoxLayout()

        curr_week = iso_week(date.today())
        rows = get_tasks_for_week(conn, curr_week)
        total = len(rows)
        done = sum(1 for r in rows if r["status"] == "DONE")
        text = f"Zadania: {done}/{total} ukończone w tym tygodniu"
        layout.addWidget(QLabel(text))

        self.setLayout(layout)
