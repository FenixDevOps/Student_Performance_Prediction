"""
db_manager.py
-------------
Database manager for MongoDB Atlas (production) and SQLite (local fallback).
"""

import os
import sqlite3
from datetime import datetime
from typing import Optional, Union
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# Configuration
SQLITE_DB_PATH = "database/student_history.db"
# MONGO_URI is provided by Render environment
MONGO_URI = os.environ.get("MONGO_URI")

def get_mongo_client():
    """Returns a MongoDB client if MONGO_URI is set."""
    if MONGO_URI:
        return MongoClient(MONGO_URI, server_api=ServerApi('1'))
    return None

def get_connection():
    """
    Returns a connection to either MongoDB (collection) or SQLite.
    Prioritizes MongoDB if MONGO_URI exists.
    """
    if MONGO_URI:
        client = get_mongo_client()
        db = client['student_prediction_db']
        return db['predictions']
    else:
        # Development: SQLite
        os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
        conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

def init_db() -> None:
    """Initialize the predictions collection/table on either platform."""
    if MONGO_URI:
        # MongoDB creates collections automatically on first insert
        pass
    else:
        # SQLite syntax - wrapped in try-except in case filesystem is read-only (Render)
        try:
            conn = get_connection()
            cur = conn.cursor()
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
        except Exception as e:
            print(f"[WARN] SQLite init failed (no MONGO_URI set, running without persistence): {e}")

def insert_prediction(student_name: str, features: dict, predicted_score: float, performance_level: str) -> str:
    init_db()
    conn = get_connection()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    data = {
        "student_name":          student_name,
        "attendance":            features.get("attendance"),
        "previous_gpa":          features.get("previous_gpa"),
        "study_hours":           features.get("study_hours"),
        "assignment_completion": features.get("assignment_completion"),
        "participation_score":   features.get("participation_score"),
        "sleep_hours":           features.get("sleep_hours"),
        "practice_test_score":   features.get("practice_test_score"),
        "practice_problems":     features.get("practice_problems"),
        "predicted_score":       predicted_score,
        "performance_level":     performance_level,
        "timestamp":             timestamp
    }
    
    if MONGO_URI:
        # MongoDB insert
        result = conn.insert_one(data)
        return str(result.inserted_id)
    else:
        # SQLite insert
        cur = conn.cursor()
        sql = """
            INSERT INTO predictions (
                student_name, attendance, previous_gpa, study_hours,
                assignment_completion, participation_score, sleep_hours,
                practice_test_score, practice_problems,
                predicted_score, performance_level, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        vals = (
            student_name, data["attendance"], data["previous_gpa"], 
            data["study_hours"], data["assignment_completion"], 
            data["participation_score"], data["sleep_hours"], 
            data["practice_test_score"], data["practice_problems"], 
            predicted_score, performance_level, timestamp
        )
        cur.execute(sql, vals)
        conn.commit()
        row_id = cur.lastrowid
        cur.close()
        conn.close()
        return str(row_id)

def search_records(name_query: str = "", level_filter: Optional[str] = None) -> list[dict]:
    init_db()
    conn = get_connection()
    
    if MONGO_URI:
        # MongoDB search
        query = {}
        if name_query:
            query["student_name"] = {"$regex": name_query, "$options": "i"}
        if level_filter and level_filter != "All":
            query["performance_level"] = level_filter
            
        # MongoDB results are already dicts
        cursor = conn.find(query).sort("timestamp", -1)
        results = []
        for doc in cursor:
            doc["id"] = str(doc.pop("_id")) # Convert ObjectId to string
            results.append(doc)
        return results
    else:
        # SQLite search
        cur = conn.cursor()
        sql = "SELECT * FROM predictions WHERE 1=1"
        params = []

        if name_query:
            sql += " AND LOWER(student_name) LIKE ?"
            params.append(f"%{name_query.lower()}%")

        if level_filter and level_filter != "All":
            sql += " AND performance_level = ?"
            params.append(level_filter)

        sql += " ORDER BY id DESC"
        cur.execute(sql, params)
        rows = cur.fetchall()
        results = [dict(r) for r in rows]
        cur.close()
        conn.close()
        return results

def get_summary_stats() -> dict:
    init_db()
    conn = get_connection()
    
    if MONGO_URI:
        # MongoDB aggregation pipeline
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total":      {"$sum": 1},
                    "avg_score":  {"$avg": "$predicted_score"},
                    "max_score":  {"$max": "$predicted_score"},
                    "min_score":  {"$min": "$predicted_score"},
                    "excellent":  {"$sum": {"$cond": [{"$eq": ["$performance_level", "Excellent"]}, 1, 0]}},
                    "good":       {"$sum": {"$cond": [{"$eq": ["$performance_level", "Good"]}, 1, 0]}},
                    "average":    {"$sum": {"$cond": [{"$eq": ["$performance_level", "Average"]}, 1, 0]}},
                    "at_risk":    {"$sum": {"$cond": [{"$eq": ["$performance_level", "At Risk"]}, 1, 0]}}
                }
            }
        ]
        results = list(conn.aggregate(pipeline))
        if results:
            stats = results[0]
            stats.pop("_id")
            stats["avg_score"] = round(stats.get("avg_score", 0), 2)
            return stats
        return {"total": 0, "avg_score": 0, "max_score": 0, "min_score": 0, "excellent": 0, "good": 0, "average": 0, "at_risk": 0}
    else:
        # SQLite stats
        cur = conn.cursor()
        cur.execute("""
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

def delete_record(record_id: Union[int, str]) -> None:
    conn = get_connection()
    if MONGO_URI:
        from bson.objectid import ObjectId
        conn.delete_one({"_id": ObjectId(record_id)})
    else:
        cur = conn.cursor()
        cur.execute("DELETE FROM predictions WHERE id = ?", (int(record_id),))
        conn.commit()
        cur.close()
        conn.close()

def get_student_trend() -> list[dict]:
    """Returns the last 10 predictions for trend analysis."""
    init_db()
    conn = get_connection()
    
    if MONGO_URI:
        # MongoDB trend
        cursor = conn.find({}, {"timestamp": 1, "predicted_score": 1}).sort("timestamp", 1).limit(10)
        results = []
        for doc in cursor:
            doc.pop("_id")
            results.append(doc)
        return results
    else:
        # SQLite trend
        cur = conn.cursor()
        cur.execute("SELECT timestamp, predicted_score FROM predictions ORDER BY id ASC LIMIT 10")
        rows = cur.fetchall()
        results = [dict(r) for r in rows]
        cur.close()
        conn.close()
        return results
