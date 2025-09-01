import sqlite3
from datetime import date

from services.db import init_db
from services.tasks_service import (
    add_task,
    assign_to_week,
    get_backlog_tasks,
    get_or_create_default_project,
    get_tasks_for_week,
    bulk_update,
)
from services.week_service import iso_week


def setup_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn


def test_backlog_and_assignment():
    conn = setup_conn()
    project = get_or_create_default_project(conn)
    task_id = add_task(conn, project, "Zadanie")
    backlog = get_backlog_tasks(conn)
    assert [row["id"] for row in backlog] == [task_id]

    week = iso_week(date(2024, 1, 1))
    assign_to_week(conn, task_id, week)

    backlog = get_backlog_tasks(conn)
    assert backlog == []
    rows = get_tasks_for_week(conn, week)
    assert [row["id"] for row in rows] == [task_id]
    conn.close()


def test_bulk_update_creates_and_updates_tasks():
    conn = setup_conn()
    bulk_update(
        conn,
        [
            {"title": "A", "week": "2024-W01"},
            {"title": "B"},
        ],
    )
    rows = get_tasks_for_week(conn, "2024-W01")
    assert [row["title"] for row in rows] == ["A"]
    backlog = get_backlog_tasks(conn)
    assert [row["title"] for row in backlog] == ["B"]

    task_id = backlog[0]["id"]
    bulk_update(conn, [{"id": task_id, "title": "B2", "week": "2024-W02"}])
    assert get_backlog_tasks(conn) == []
    rows = get_tasks_for_week(conn, "2024-W02")
    assert [row["title"] for row in rows] == ["B2"]
    conn.close()
