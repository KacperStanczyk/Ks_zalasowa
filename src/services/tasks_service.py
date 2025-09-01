"""Task-related helpers."""
from __future__ import annotations

import sqlite3
from typing import Optional


def get_or_create_default_project(conn: sqlite3.Connection) -> int:
    """Ensure a default project exists and return its id."""
    cur = conn.execute("SELECT id FROM projects WHERE name='General'")
    row = cur.fetchone()
    if row:
        return row["id"]
    cur = conn.execute(
        "INSERT INTO projects(name, status) VALUES ('General', 'ACTIVE')"
    )
    conn.commit()
    return cur.lastrowid


def get_tasks_for_week(conn: sqlite3.Connection, iso_week: str):
    """Return tasks assigned to the given ISO week."""
    cur = conn.execute(
        """
        SELECT t.id, t.title, t.status
        FROM tasks t
        JOIN weekly_assignments w ON w.task_id=t.id
        WHERE w.iso_week=?
        ORDER BY t.id
        """,
        (iso_week,),
    )
    return cur.fetchall()



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


def bulk_update(conn: sqlite3.Connection, tasks: list[dict]) -> None:
    """Create or update tasks in bulk based on a JSON-friendly structure."""
    default_project = get_or_create_default_project(conn)
    for item in tasks:
        task_id = item.get("id")
        if task_id:
            fields = []
            values = []
            for col in ["title", "priority", "estimate", "notes", "status"]:
                if col in item:
                    fields.append(f"{col}=?")
                    values.append(item[col])
            if fields:
                conn.execute(
                    f"UPDATE tasks SET {', '.join(fields)} WHERE id=?",
                    (*values, task_id),
                )
        else:
            cur = conn.execute(
                """
                INSERT INTO tasks(project_id, title, priority, estimate, notes, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    item.get("project_id", default_project),
                    item["title"],
                    item.get("priority", 3),
                    item.get("estimate"),
                    item.get("notes"),
                    item.get("status", "TODO"),
                ),
            )
            task_id = cur.lastrowid
            item["id"] = task_id
        if "week" in item:
            assign_to_week(conn, task_id, item["week"])
    conn.commit()
