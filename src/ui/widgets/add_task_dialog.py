"""Dialog window for creating a new task."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QTextEdit,
)


class AddTaskDialog(QDialog):
    """Collect all information required to create a task."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nowe zadanie")

        layout = QFormLayout()

        self.title_edit = QLineEdit()
        layout.addRow("Tytuł", self.title_edit)

        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(1, 5)
        self.priority_spin.setValue(3)
        layout.addRow("Priorytet", self.priority_spin)

        self.estimate_spin = QSpinBox()
        self.estimate_spin.setRange(0, 100)
        self.estimate_spin.setSpecialValueText("")
        layout.addRow("Szac. czas", self.estimate_spin)

        self.notes_edit = QTextEdit()
        layout.addRow("Notatki", self.notes_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_data(self) -> dict:
        """Return the data entered by the user."""
        return {
            "title": self.title_edit.text().strip(),
            "priority": self.priority_spin.value(),
            "estimate": self.estimate_spin.value() or None,
            "notes": self.notes_edit.toPlainText().strip() or None,
        }

