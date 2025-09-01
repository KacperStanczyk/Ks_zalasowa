"""Simple Kanban board with ability to add tasks."""
from __future__ import annotations

from datetime import date
from typing import Callable, Dict

from PySide6.QtCore import Qt, QEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
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
    get_backlog_tasks,  # <-- upewnij się, że istnieje; w razie czego podmień na właściwą
    bulk_update,
    update_status,
)
from services.week_service import iso_week

from .widgets.add_task_dialog import AddTaskDialog
from .widgets.bulk_update_dialog import BulkUpdateDialog


KANBAN_STATUSES = ("TODO", "IN_PROGRESS", "DONE")


class StatusList(QListWidget):
    """List widget representing a task status column with cross-list DnD."""

    def __init__(self, status: str, on_change: Callable[[int, str], None]):
        super().__init__()
        self.status = status
        self.on_change = on_change

        self.setObjectName(status)

        # DnD setup — umożliwia przeciąganie między listami:
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QListWidget.SingleSelection)
        # Pozwala na przenoszenie elementów między widgetami:
        self.setDragDropMode(QListWidget.DragDrop)

    # Qt override
    def dropEvent(self, event):  # noqa: N802
        """Po udanym dropie aktualizujemy status w DB."""
        source = event.source()
        if not isinstance(source, QListWidget):
            return super().dropEvent(event)

        # Zachowujemy referencję do przenoszonego itemu PRZED super().dropEvent,
        # bo po przeniesieniu currentItem na źródle może się zmienić.
        item: QListWidgetItem | None = source.currentItem()
        super().dropEvent(event)

        if item is None:
            return
        task_id = item.data(Qt.UserRole)
        if task_id is None:
            return
        try:
            self.on_change(int(task_id), self.status)
        except Exception:
            # w razie błędu operacyjnego – twardo ignorujemy żeby nie crashować UI
            pass

    # Opcjonalnie: wygładzenie UX – podświetlenie kolumny przy drag enter/leave
    def dragEnterEvent(self, event):  # noqa: N802
        if event.source() and isinstance(event.source(), QListWidget):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):  # noqa: N802
        if event.source() and isinstance(event.source(), QListWidget):
            event.acceptProposedAction()
        else:
            event.ignore()


class TasksView(QWidget):
    """Kanban board view with an option to add tasks."""

    def __init__(self, conn):
        super().__init__()

        self.conn = conn
        self.curr_week = iso_week(date.today())
        self.project_id = get_or_create_default_project(conn)

        main = QVBoxLayout()

        # --- Content (Backlog + Board) ---
        content = QHBoxLayout()

        # Left: Backlog
        left = QVBoxLayout()
        left.addWidget(QLabel("Backlog"))
        self.backlog = QListWidget()
        self.backlog.setSelectionMode(QListWidget.SingleSelection)
        self.backlog.itemDoubleClicked.connect(self._plan_backlog_task)
        left.addWidget(self.backlog)
        content.addLayout(left)

        # Right: Kanban board
        board = QHBoxLayout()
        self.lists: Dict[str, StatusList] = {}
        for name in KANBAN_STATUSES:
            column = QVBoxLayout()
            column.addWidget(QLabel(name))
            lst = StatusList(name, self._status_changed)
            column.addWidget(lst)
            board.addLayout(column)
            self.lists[name] = lst
        content.addLayout(board)
        main.addLayout(content)

        # --- Actions ---
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

    # --- Data loading ---
    def _load_tasks(self) -> None:
        for lst in self.lists.values():
            lst.clear()
        self.backlog.clear()

        # Backlog
        for row in get_backlog_tasks(self.conn) or []:
            item = QListWidgetItem(row.get("title", "<no title>"))
            item.setData(Qt.UserRole, row.get("id"))
            self.backlog.addItem(item)

        # Planned tasks (current week)
        for row in get_tasks_for_week(self.conn, self.curr_week) or []:
            title = row.get("title", "<no title>")
            status = row.get("status", "TODO")
            status = status if status in self.lists else "TODO"
            item = QListWidgetItem(title)
            item.setData(Qt.UserRole, row.get("id"))
            self.lists[status].addItem(item)

    # --- Actions handlers ---
    def _add_task(self) -> None:
        dlg = AddTaskDialog(self)
        if dlg.exec() != dlg.Accepted:
            return
        data = dlg.get_data()
        title = (data.get("title") or "").strip()
        if not title:
            return

        task_id = add_task(
            self.conn,
            self.project_id,
            title,
            data.get("priority"),
            data.get("estimate"),
            data.get("notes"),
        )
        assign_to_week(self.conn, task_id, self.curr_week)

        item = QListWidgetItem(title)
        item.setData(Qt.UserRole, task_id)
        self.lists["TODO"].addItem(item)

    def _status_changed(self, task_id: int, status: str) -> None:
        update_status(self.conn, task_id, status)

    def _plan_backlog_task(self, item: QListWidgetItem) -> None:
        task_id = item.data(Qt.UserRole)
        if task_id is None:
            return
        assign_to_week(self.conn, int(task_id), self.curr_week)

        row = self.backlog.row(item)
        self.backlog.takeItem(row)

        new_item = QListWidgetItem(item.text())
        new_item.setData(Qt.UserRole, task_id)
        self.lists["TODO"].addItem(new_item)

    def _bulk_update(self) -> None:
        dlg = BulkUpdateDialog(self)
        if dlg.exec() != dlg.Accepted:
            return
        tasks = dlg.get_tasks()
        if not tasks:
            return
        bulk_update(self.conn, tasks)
        self._load_tasks()
