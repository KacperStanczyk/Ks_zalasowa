
"""Simple Kanban board with ability to add tasks."""
from __future__ import annotations

from datetime import date
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
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
    update_status,
)
from services.week_service import iso_week


class StatusList(QListWidget):
    def __init__(self, status: str, on_change):
        super().__init__()
        self.status = status
        self.on_change = on_change
        self.setObjectName(status)
        self.setDragDropMode(QListWidget.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QListWidget.SingleSelection)

    def dropEvent(self, event):
        item = self.currentItem()
        super().dropEvent(event)
        if item:
            task_id = item.data(Qt.UserRole)
            self.on_change(task_id, self.status)

=======
"""Simple Kanban placeholder."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QWidget,
)


class TasksView(QWidget):
    def __init__(self, conn):
        super().__init__()

        self.conn = conn
        self.curr_week = iso_week(date.today())
        self.project_id = get_or_create_default_project(conn)

        main = QVBoxLayout()
        board = QHBoxLayout()
        self.lists = {}
        for name in ["TODO", "IN_PROGRESS", "DONE"]:
            lst = StatusList(name, self._status_changed)
            board.addWidget(lst)
            self.lists[name] = lst
        main.addLayout(board)

        form = QHBoxLayout()
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Nowe zadanie")
        add_btn = QPushButton("Dodaj")
        add_btn.clicked.connect(self._add_task)
        form.addWidget(self.title_edit)
        form.addWidget(add_btn)
        main.addLayout(form)

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
        title = self.title_edit.text().strip()
        if not title:
            return
        task_id = add_task(self.conn, self.project_id, title)
        assign_to_week(self.conn, task_id, self.curr_week)
        item = QListWidgetItem(title)
        item.setData(Qt.UserRole, task_id)
        self.lists["TODO"].addItem(item)
        self.title_edit.clear()

    def _status_changed(self, task_id: int, status: str) -> None:
        update_status(self.conn, task_id, status)

        layout = QHBoxLayout()
        for name in ["TODO", "IN_PROGRESS", "DONE"]:
            lst = QListWidget()
            lst.setObjectName(name)
            lst.setDragDropMode(QListWidget.InternalMove)
            layout.addWidget(lst)
        self.setLayout(layout)
