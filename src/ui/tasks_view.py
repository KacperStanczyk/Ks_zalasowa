"""Simple Kanban board with ability to add tasks."""
from __future__ import annotations

from datetime import date
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from services.tasks_service import (
    add_task,
    assign_to_week,
    get_or_create_default_project,
    get_tasks_for_week,
    bulk_update,
    update_status,
)
from services.week_service import iso_week

from .widgets.add_task_dialog import AddTaskDialog
from .widgets.bulk_update_dialog import BulkUpdateDialog


class StatusList(QListWidget):
    """List widget representing a task status column."""

    def __init__(self, status: str, on_change):
        super().__init__()
        self.status = status
        self.on_change = on_change
        self.setObjectName(status)
        self.setDragDropMode(QListWidget.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QListWidget.SingleSelection)

    def dropEvent(self, event):  # noqa: N802 - Qt override
        item = self.currentItem()
        super().dropEvent(event)
        if item:
            task_id = item.data(Qt.UserRole)
            self.on_change(task_id, self.status)


class TasksView(QWidget):
    """Kanban board view with an option to add tasks."""

    def __init__(self, conn):
        super().__init__()

        self.conn = conn
        self.curr_week = iso_week(date.today())
        self.project_id = get_or_create_default_project(conn)

        main = QVBoxLayout()

        board = QHBoxLayout()
        self.lists: dict[str, StatusList] = {}
        for name in ["TODO", "IN_PROGRESS", "DONE"]:
            lst = StatusList(name, self._status_changed)
            board.addWidget(lst)
            self.lists[name] = lst
        main.addLayout(board)

        actions = QHBoxLayout()

        add_btn = QPushButton("Dodaj zadanie")
        add_btn.clicked.connect(self._add_task)
        actions.addWidget(add_btn)

        bulk_btn = QPushButton("Masowa aktualizacja")
        bulk_btn.clicked.connect(self._bulk_update)
        actions.addWidget(bulk_btn)

        main.addLayout(actions)

        self.setLayout(main)
        self._load_tasks()

    def _load_tasks(self) -> None:
        for lst in self.lists.values():
            lst.clear()
        for row in get_tasks_for_week(self.conn, self.curr_week):
            item = QListWidgetItem(row["title"])
            item.setData(Qt.UserRole, row["id"])
            self.lists[row["status"]].addItem(item)

    def _add_task(self) -> None:
        dlg = AddTaskDialog(self)
        if dlg.exec() != dlg.Accepted:
            return
        data = dlg.get_data()
        if not data["title"]:
            return
        task_id = add_task(
            self.conn,
            self.project_id,
            data["title"],
            data["priority"],
            data["estimate"],
            data["notes"],
        )
        assign_to_week(self.conn, task_id, self.curr_week)
        item = QListWidgetItem(data["title"])
        item.setData(Qt.UserRole, task_id)
        self.lists["TODO"].addItem(item)

    def _status_changed(self, task_id: int, status: str) -> None:
        update_status(self.conn, task_id, status)

    def _bulk_update(self) -> None:
        dlg = BulkUpdateDialog(self)
        if dlg.exec() != dlg.Accepted:
            return
        tasks = dlg.get_tasks()
        if not tasks:
            return
        bulk_update(self.conn, tasks)
        self._load_tasks()

