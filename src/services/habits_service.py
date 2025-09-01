"""Habit management helpers."""
from __future__ import annotations

import sqlite3
from datetime import date


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
