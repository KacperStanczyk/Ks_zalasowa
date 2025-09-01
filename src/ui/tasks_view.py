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
        layout = QHBoxLayout()
        for name in ["TODO", "IN_PROGRESS", "DONE"]:
            lst = QListWidget()
            lst.setObjectName(name)
            lst.setDragDropMode(QListWidget.InternalMove)
            layout.addWidget(lst)
        self.setLayout(layout)
