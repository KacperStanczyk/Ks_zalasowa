"""Task-related helpers."""
from __future__ import annotations

import sqlite3
from typing import Optional


def add_task(
    conn: sqlite3.Connection,
    project_id: int,
    title: str,
    priority: int = 3,
    estimate: Optional[int] = None,
    notes: Optional[str] = None,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO tasks(project_id, title, priority, estimate, notes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (project_id, title, priority, estimate, notes),
    )
    conn.commit()
    return cur.lastrowid


def assign_to_week(
    conn: sqlite3.Connection, task_id: int, iso_week: str, rolled_over: bool = False
) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO weekly_assignments(task_id, iso_week, planned, rolled_over) VALUES (?, ?, 1, ?)",
        (task_id, iso_week, 1 if rolled_over else 0),
    )
    conn.commit()


def update_status(conn: sqlite3.Connection, task_id: int, status: str) -> None:
    conn.execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))
    conn.commit()
