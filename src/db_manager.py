"""
db_manager.py
-------------
SQLite-backed student history database.

Handles:
  - Creating the database schema
  - Inserting new prediction records
  - Querying, searching, and filtering past records
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional

DB_PATH = "database/student_history.db"


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Open (or create) the SQLite database and return a connection."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row          # rows behave like dicts
    conn.execute("PRAGMA journal_mode=WAL") # safer concurrent writes
    return conn


def init_db(db_path: str = DB_PATH) -> None:
    """Create the predictions table if it does not already exist."""
    conn = get_connection(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name          TEXT    NOT NULL,
            attendance            REAL,
            previous_gpa          REAL,
            study_hours           REAL,
            assignment_completion REAL,
            participation_score   REAL,
            sleep_hours           REAL,
            practice_test_score   REAL,
            practice_problems     INTEGER,
            predicted_score       REAL,
            performance_level     TEXT,
            timestamp             TEXT
        )
    """)
    conn.commit()
    conn.close()


def insert_prediction(
    student_name: str,
    features: dict,
    predicted_score: float,
    performance_level: str,
    db_path: str = DB_PATH,
) -> int:
    """
    Save a new prediction record.

    Returns
    -------
    int
        The row ID of the inserted record.
    """
    init_db(db_path)
    conn = get_connection(db_path)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.execute(
        """
        INSERT INTO predictions (
            student_name, attendance, previous_gpa, study_hours,
            assignment_completion, participation_score, sleep_hours,
            practice_test_score, practice_problems,
            predicted_score, performance_level, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            student_name,
            features.get("attendance"),
            features.get("previous_gpa"),
            features.get("study_hours"),
            features.get("assignment_completion"),
            features.get("participation_score"),
            features.get("sleep_hours"),
            features.get("practice_test_score"),
            features.get("practice_problems"),
            predicted_score,
            performance_level,
            timestamp,
        ),
    )
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return row_id


def get_all_records(db_path: str = DB_PATH) -> list[dict]:
    """Return all prediction records, newest first."""
    init_db(db_path)
    conn = get_connection(db_path)
    rows = conn.execute(
        "SELECT * FROM predictions ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_records(
    name_query: str = "",
    level_filter: Optional[str] = None,
    db_path: str = DB_PATH,
) -> list[dict]:
    """
    Search and filter student records.

    Parameters
    ----------
    name_query : str
        Substring search on student_name (case-insensitive).
    level_filter : str | None
        If provided, only return records matching this performance_level.

    Returns
    -------
    list[dict]
        Matching records, newest first.
    """
    init_db(db_path)
    conn = get_connection(db_path)

    sql    = "SELECT * FROM predictions WHERE 1=1"
    params: list = []

    if name_query:
        sql += " AND LOWER(student_name) LIKE ?"
        params.append(f"%{name_query.lower()}%")

    if level_filter and level_filter != "All":
        sql += " AND performance_level = ?"
        params.append(level_filter)

    sql += " ORDER BY id DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_student_trend(student_name: str, db_path: str = DB_PATH) -> list[dict]:
    """
    Return all records for a specific student, ordered chronologically.
    Useful for plotting a performance trend over time.
    """
    init_db(db_path)
    conn = get_connection(db_path)
    rows = conn.execute(
        """
        SELECT id, timestamp, predicted_score, performance_level
        FROM predictions
        WHERE LOWER(student_name) = ?
        ORDER BY id ASC
        """,
        (student_name.lower(),),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_record(record_id: int, db_path: str = DB_PATH) -> None:
    """Delete a single record by its ID."""
    conn = get_connection(db_path)
    conn.execute("DELETE FROM predictions WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()


def get_summary_stats(db_path: str = DB_PATH) -> dict:
    """
    Return aggregate statistics across all records.
    Used to populate the dashboard summary widgets.
    """
    init_db(db_path)
    conn = get_connection(db_path)
    row = conn.execute(
        """
        SELECT
            COUNT(*)                                                AS total,
            ROUND(AVG(predicted_score), 2)                         AS avg_score,
            ROUND(MAX(predicted_score), 2)                         AS max_score,
            ROUND(MIN(predicted_score), 2)                         AS min_score,
            SUM(CASE WHEN performance_level='Excellent' THEN 1 ELSE 0 END) AS excellent,
            SUM(CASE WHEN performance_level='Good'      THEN 1 ELSE 0 END) AS good,
            SUM(CASE WHEN performance_level='Average'   THEN 1 ELSE 0 END) AS average,
            SUM(CASE WHEN performance_level='At Risk'   THEN 1 ELSE 0 END) AS at_risk
        FROM predictions
        """
    ).fetchone()
    conn.close()
    return dict(row) if row else {}


# ── Standalone smoke test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    rid = insert_prediction(
        "Alice",
        {"attendance": 90, "previous_gpa": 3.5, "study_hours": 22,
         "assignment_completion": 88, "participation_score": 8,
         "sleep_hours": 7.5, "practice_test_score": 78, "practice_problems": 100},
        predicted_score=82.4,
        performance_level="Good",
    )
    print(f"Inserted record id={rid}")
    stats = get_summary_stats()
    print("Stats:", stats)
