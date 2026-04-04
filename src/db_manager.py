"""
db_manager.py
-------------
Hybrid database manager supporting both SQLite (local) and PostgreSQL (production).
"""

import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Optional, Union

# Configuration
SQLITE_DB_PATH = "database/student_history.db"
# DATABASE_URL is provided by Render/Heroku environment
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    """
    Returns a connection to either PostgreSQL or SQLite.
    Prioritizes PostgreSQL if DATABASE_URL exists.
    """
    if DATABASE_URL:
        # Production: PostgreSQL
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        # Development: SQLite
        os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
        conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

def init_db() -> None:
    """Initialize the predictions table on either platform."""
    conn = get_connection()
    cur = conn.cursor()
    
    # Use SERIAL for PG, AUTOINCREMENT for SQLite
    if DATABASE_URL:
        # PostgreSQL syntax
        cur.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id                    SERIAL PRIMARY KEY,
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
    else:
        # SQLite syntax
        cur.execute("""
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
    cur.close()
    conn.close()

def insert_prediction(student_name: str, features: dict, predicted_score: float, performance_level: str) -> int:
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    sql = """
        INSERT INTO predictions (
            student_name, attendance, previous_gpa, study_hours,
            assignment_completion, participation_score, sleep_hours,
            practice_test_score, practice_problems,
            predicted_score, performance_level, timestamp
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """ if DATABASE_URL else """
        INSERT INTO predictions (
            student_name, attendance, previous_gpa, study_hours,
            assignment_completion, participation_score, sleep_hours,
            practice_test_score, practice_problems,
            predicted_score, performance_level, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    vals = (
        student_name, features.get("attendance"), features.get("previous_gpa"), 
        features.get("study_hours"), features.get("assignment_completion"), 
        features.get("participation_score"), features.get("sleep_hours"), 
        features.get("practice_test_score"), features.get("practice_problems"), 
        predicted_score, performance_level, timestamp
    )
    
    cur.execute(sql, vals)
    conn.commit()
    
    row_id = -1
    if DATABASE_URL:
        # PostgreSQL doesn't have lastrowid, but it's okay for now
        pass
    else:
        row_id = cur.lastrowid
        
    cur.close()
    conn.close()
    return row_id

def search_records(name_query: str = "", level_filter: Optional[str] = None) -> list[dict]:
    init_db()
    conn = get_connection()
    
    # PG needs RealDictCursor to match SQLite's Row
    cur = conn.cursor(cursor_factory=RealDictCursor) if DATABASE_URL else conn.cursor()
    
    placeholder = "%s" if DATABASE_URL else "?"
    sql = "SELECT * FROM predictions WHERE 1=1"
    params = []

    if name_query:
        sql += " AND LOWER(student_name) LIKE " + placeholder
        params.append(f"%{name_query.lower()}%")

    if level_filter and level_filter != "All":
        sql += " AND performance_level = " + placeholder
        params.append(level_filter)

    sql += " ORDER BY id DESC"
    cur.execute(sql, params)
    rows = cur.fetchall()
    
    # Format as list of dicts
    results = [dict(r) for r in rows]
    
    cur.close()
    conn.close()
    return results

def get_summary_stats() -> dict:
    init_db()
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor) if DATABASE_URL else conn.cursor()
    
    cur.execute("""
        SELECT
            COUNT(*)::INTEGER                                      AS total,
            ROUND(AVG(predicted_score)::NUMERIC, 2)                AS avg_score,
            ROUND(MAX(predicted_score)::NUMERIC, 2)                AS max_score,
            ROUND(MIN(predicted_score)::NUMERIC, 2)                AS min_score,
            SUM(CASE WHEN performance_level='Excellent' THEN 1 ELSE 0 END)::INTEGER AS excellent,
            SUM(CASE WHEN performance_level='Good'      THEN 1 ELSE 0 END)::INTEGER AS good,
            SUM(CASE WHEN performance_level='Average'   THEN 1 ELSE 0 END)::INTEGER AS average,
            SUM(CASE WHEN performance_level='At Risk'   THEN 1 ELSE 0 END)::INTEGER AS at_risk
        FROM predictions
    """) if DATABASE_URL else cur.execute("""
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
    """)
    
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else {}

def delete_record(record_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    placeholder = "%s" if DATABASE_URL else "?"
    cur.execute(f"DELETE FROM predictions WHERE id = {placeholder}", (record_id,))
    conn.commit()
    cur.close()
    conn.close()
