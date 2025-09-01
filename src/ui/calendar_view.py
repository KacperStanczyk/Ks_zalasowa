"""Placeholder Calendar view."""
from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QWidget, QLabel


class CalendarView(QWidget):
    def __init__(self, conn):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Kalendarz nawyków"))
        self.setLayout(layout)
