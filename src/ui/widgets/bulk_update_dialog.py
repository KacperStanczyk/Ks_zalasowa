"""Dialog window allowing mass task updates via JSON."""
from __future__ import annotations

import json
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QTextEdit,
    QVBoxLayout,
)


class BulkUpdateDialog(QDialog):
    """Prompt user for JSON describing tasks to add or update."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Masowa aktualizacja")

        layout = QVBoxLayout()

        fmt = (
            "Format:\n{\n  \"tasks\": [\n    {\"title\": \"Nowe\", \"week\": \"2024-W30\"},\n"
            "    {\"id\": 1, \"status\": \"DONE\"}\n  ]\n}"
        )
        info = QLabel(fmt)
        info.setWordWrap(True)
        layout.addWidget(info)

        self.text = QTextEdit()
        layout.addWidget(self.text)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_tasks(self) -> list[dict]:
        """Return parsed task data or an empty list on failure."""
        try:
            data = json.loads(self.text.toPlainText() or "{}")
        except json.JSONDecodeError:
            return []
        if isinstance(data, dict):
            tasks = data.get("tasks", [])
            if isinstance(tasks, list):
                return [t for t in tasks if isinstance(t, dict)]
        return []
