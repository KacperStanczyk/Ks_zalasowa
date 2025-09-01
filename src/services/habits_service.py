"""Habit management helpers."""
from __future__ import annotations

import sqlite3
from datetime import date



def add_habit(
    conn: sqlite3.Connection,
    name: str,
    type_: str,
    goal_type: str,
    goal_value: int,
) -> int:
    """Insert a new habit and return its id."""
    cur = conn.execute(
        """
        INSERT INTO habits(name, type, goal_type, goal_value)
        VALUES (?, ?, ?, ?)
        """,
        (name, type_, goal_type, goal_value),
    )
    conn.commit()
    return cur.lastrowid


def get_active_habits(conn: sqlite3.Connection):
    """Return all active habits."""
    cur = conn.execute(
        "SELECT id, name FROM habits WHERE is_active=1 ORDER BY id"
    )
    return cur.fetchall()



def toggle_binary_habit(conn: sqlite3.Connection, habit_id: int, day: date) -> None:
    cur = conn.execute(
        "SELECT id FROM habit_logs WHERE habit_id=? AND date=?", (habit_id, day)
    )
    row = cur.fetchone()
    if row:
        conn.execute("DELETE FROM habit_logs WHERE id=?", (row["id"],))
    else:
        conn.execute(
            "INSERT INTO habit_logs(habit_id, date, value) VALUES(?, ?, 1)",
            (habit_id, day),
        )
    conn.commit()


def increment_quantity_habit(
    conn: sqlite3.Connection, habit_id: int, day: date, delta: int
) -> None:
    cur = conn.execute(
        "SELECT id, value FROM habit_logs WHERE habit_id=? AND date=?", (habit_id, day)
    )
    row = cur.fetchone()
    if row:
        new_val = max(0, row["value"] + delta)
        if new_val == 0:
            conn.execute("DELETE FROM habit_logs WHERE id=?", (row["id"],))
        else:
            conn.execute("UPDATE habit_logs SET value=? WHERE id=?", (new_val, row["id"]))
    elif delta > 0:
        conn.execute(
            "INSERT INTO habit_logs(habit_id, date, value) VALUES(?, ?, ?)",
            (habit_id, day, delta),
        )
    conn.commit()
