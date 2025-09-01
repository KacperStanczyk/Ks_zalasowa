from __future__ import annotations

"""Simple Today view with ability to add habits."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from services.habits_service import add_habit, get_active_habits


class TodayView(QWidget):
    """Minimal view showing today's habits and allowing new ones."""

    def __init__(self, conn):
        super().__init__()
        self.conn = conn

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Dzisiejsze nawyki"))

        self.list = QListWidget()
        layout.addWidget(self.list)
        self._refresh()

        form = QHBoxLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nazwa")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["binary", "quantity"])
        self.goal_type_combo = QComboBox()
        self.goal_type_combo.addItems(["daily", "weekly", "monthly"])
        self.goal_spin = QSpinBox()
        self.goal_spin.setRange(1, 100)
        add_btn = QPushButton("Dodaj")
        add_btn.clicked.connect(self._add_clicked)
        for w in [
            self.name_edit,
            self.type_combo,
            self.goal_type_combo,
            self.goal_spin,
            add_btn,
        ]:
            form.addWidget(w)
        layout.addLayout(form)

        self.setLayout(layout)

    def _refresh(self) -> None:
        self.list.clear()
        for row in get_active_habits(self.conn):
            item = QListWidgetItem(row["name"])
            item.setData(Qt.UserRole, row["id"])
            self.list.addItem(item)

    def _add_clicked(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            return
        habit_id = add_habit(
            self.conn,
            name,
            self.type_combo.currentText(),
            self.goal_type_combo.currentText(),
            self.goal_spin.value(),
        )
        item = QListWidgetItem(name)
        item.setData(Qt.UserRole, habit_id)
        self.list.addItem(item)
        self.name_edit.clear()

