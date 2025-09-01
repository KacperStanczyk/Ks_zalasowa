"""Placeholder Today view."""
from __future__ import annotations

from datetime import date
from PySide6.QtWidgets import QVBoxLayout, QWidget, QLabel


class TodayView(QWidget):
    def __init__(self, conn):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Dzisiejsze nawyki"))
        self.setLayout(layout)
