import os
import sys
from pathlib import Path
import sqlite3
from datetime import date

import pytest

qtwidgets = pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 with libGL is required for GUI tests",
    exc_type=ImportError,
)
from PySide6.QtWidgets import QApplication, QLabel

# Ensure Qt uses offscreen rendering
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Make application code importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from services.db import init_db
from services.tasks_service import (
    add_task,
    assign_to_week,
    get_or_create_default_project,
    update_status,
)
from services.week_service import iso_week
from ui.widgets.add_task_dialog import AddTaskDialog
from ui.reports_view import ReportsView


@pytest.fixture(scope="module")
def qapp():
    """Provide a QApplication instance for widget tests."""
    return QApplication.instance() or QApplication([])


def test_add_task_dialog_collects_data(qapp):
    dlg = AddTaskDialog()
    dlg.title_edit.setText("  Example ")
    dlg.priority_spin.setValue(2)
    dlg.estimate_spin.setValue(5)
    dlg.notes_edit.setPlainText(" note ")
    assert dlg.get_data() == {
        "title": "Example",
        "priority": 2,
        "estimate": 5,
        "notes": "note",
    }


def test_reports_view_shows_weekly_completion(qapp):
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    project = get_or_create_default_project(conn)
    week = iso_week(date.today())

    t1 = add_task(conn, project, "A")
    assign_to_week(conn, t1, week)
    update_status(conn, t1, "DONE")

    t2 = add_task(conn, project, "B")
    assign_to_week(conn, t2, week)

    view = ReportsView(conn)
    label = view.findChild(QLabel)
    assert label is not None
    assert label.text() == "Zadania: 1/2 ukończone w tym tygodniu"
    conn.close()
