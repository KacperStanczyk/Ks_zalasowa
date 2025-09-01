"""ISO week helpers and rollover logic."""
from __future__ import annotations

from datetime import date, timedelta
import sqlite3

from .settings_service import get_setting, set_setting


def iso_week(d: date) -> str:
    year, week, _ = d.isocalendar()
    return f"{year}-W{week:02d}"


def rollover_tasks(conn: sqlite3.Connection, today: date | None = None) -> int:
    today = today or date.today()
    curr = iso_week(today)
    prev = iso_week(today - timedelta(days=7))
    last_seen = get_setting(conn, "last_seen_iso_week")
    if last_seen == curr:
        return 0

    rows = conn.execute(
        """
        SELECT t.id FROM tasks t
        JOIN weekly_assignments w ON w.task_id = t.id
        WHERE w.iso_week = ? AND t.status NOT IN ('DONE','CANCELED')
        """,
        (prev,),
    ).fetchall()
    for row in rows:
        conn.execute(
            "INSERT OR IGNORE INTO weekly_assignments(task_id, iso_week, planned, rolled_over) VALUES (?, ?, 1, 1)",
            (row["id"], curr),
        )
    set_setting(conn, "last_seen_iso_week", curr)
    conn.commit()
    return len(rows)
