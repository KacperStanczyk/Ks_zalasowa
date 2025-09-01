"""Application bootstrap."""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import date

import yaml
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget

from services.db import get_connection, init_db
from services.week_service import rollover_tasks
from services.security_service import decrypt_file, encrypt_file, secure_delete
from services.backup_service import local_backup

DEFAULT_CONFIG = {
    "db_plain_path": "./data/app.db",
    "db_encrypted_path": "./data/app.db.enc",
    "backup_path": "./backup/",
    "auto_lock_minutes": 10,
    "default_view": "minimal",
}


def load_config() -> dict:
    path = Path("config.yaml")
    if path.exists():
        return yaml.safe_load(path.read_text())
    return DEFAULT_CONFIG.copy()


class MainWindow(QMainWindow):
    def __init__(self, conn):
        super().__init__()
        self.setWindowTitle("Habits + To-Do")
        tabs = QTabWidget()
        from ui.today_view import TodayView
        from ui.calendar_view import CalendarView
        from ui.tasks_view import TasksView
        from ui.reports_view import ReportsView

        tabs.addTab(TodayView(conn), "Dziś")
        tabs.addTab(CalendarView(conn), "Kalendarz")
        tabs.addTab(TasksView(conn), "Zadania")
        tabs.addTab(ReportsView(conn), "Raporty")
        self.setCentralWidget(tabs)


def main() -> int:
    config = load_config()
    plain = Path(config["db_plain_path"])
    enc = Path(config["db_encrypted_path"])
    plain.parent.mkdir(parents=True, exist_ok=True)
    backup_dir = Path(config["backup_path"])

    if enc.exists():
        decrypt_file(enc, plain, "password")  # TODO: prompt for password

    conn = get_connection(str(plain))
    init_db(conn)
    rollover_tasks(conn)

    app = QApplication(sys.argv)
    win = MainWindow(conn)
    win.show()
    code = app.exec()

    conn.close()
    encrypt_file(plain, enc, "password")
    secure_delete(plain)
    local_backup(enc, backup_dir)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
