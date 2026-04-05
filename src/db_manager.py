"""
db_manager.py
--------------
Storage layer with four tiers:
  1. MongoDB Atlas  (when MONGO_URI env var is set)  → fully persistent
  2. JSON File      (fallback for local persistence)  → database/records.json
  3. In-memory list (last resort fallback)           → persists for session lifetime
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Optional, List, Union

log = logging.getLogger(__name__)

# Paths
DB_DIR = "database"
JSON_DB_PATH = os.path.join(DB_DIR, "records.json")
MONGO_URI = os.environ.get("MONGO_URI", "").strip()

# ── IN-MEMORY FALLBACK ─────────────────────────────────────────────────────────
_mem_store: List[dict] = []
_mem_next_id: int = 1

# ── MONGODB CLIENT (lazy-loaded, singleton) ────────────────────────────────────
_mongo_col = None

def _get_col():
    """Return MongoDB collection, or None if not configured / unreachable."""
    global _mongo_col
    if _mongo_col is not None:
        return _mongo_col
    if not MONGO_URI:
        return None
    try:
        from pymongo import MongoClient
        from pymongo.server_api import ServerApi
        client = MongoClient(
            MONGO_URI,
            server_api=ServerApi('1'),
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        client.admin.command('ping')           # verify connection
        _mongo_col = client['student_analytics']['prediction_history']
        # performance indices
        _mongo_col.create_index([("created_at", -1)])
        _mongo_col.create_index([("student_name", 1)])
        log.info("MongoDB Atlas connected ✓")
        return _mongo_col
    except Exception as exc:
        log.warning(f"MongoDB unavailable ({exc}) — using file/memory storage")
        return None

# ── JSON FILE HELPERS ─────────────────────────────────────────────────────────
def _load_json() -> List[dict]:
    if not os.path.exists(JSON_DB_PATH):
        return []
    try:
        with open(JSON_DB_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        log.error(f"Error loading JSON DB: {e}")
        return []

def _save_json(data: List[dict]):
    try:
        os.makedirs(DB_DIR, exist_ok=True)
        with open(JSON_DB_PATH, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        log.error(f"Error saving JSON DB: {e}")

# ── PUBLIC API ─────────────────────────────────────────────────────────────────

def init_db() -> None:
    """Initialize storage and perform auto-seeding if empty."""
    try:
        col = _get_col()
        if col is not None:
            log.info("Storage: MongoDB Atlas")
            # Auto-seed MongoDB if empty
            if col.count_documents({}) == 0:
                log.info("MongoDB is empty. Auto-seeding...")
                seed_db()
        else:
            if os.path.exists(JSON_DB_PATH) or os.access(DB_DIR if os.path.exists(DB_DIR) else '.', os.W_OK):
                log.info(f"Storage: JSON File ({JSON_DB_PATH})")
                # Auto-seed JSON if empty
                if len(_load_json()) == 0:
                    log.info("JSON DB is empty. Auto-seeding...")
                    seed_db()
            else:
                log.info("Storage: In-memory (Filesystem not writable and no MONGO_URI)")
                if len(_mem_store) == 0:
                    log.info("Memory store is empty. Auto-seeding...")
                    seed_db()
    except Exception as e:
        log.warning(f"init_db warning: {e}")


def insert_prediction(
    student_name: str,
    features: dict,
    predicted_score: float,
    performance_level: str,
    strengths: list = None,
    weaknesses: list = None,
    recommendations: list = None,
    summary: str = "",
    created_at: str = None
) -> str:
    """Insert a full prediction record. Returns the record id."""
    global _mem_next_id

    now = created_at or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    doc = {
        "student_name":          student_name,
        "attendance":            float(features.get("attendance") or 0),
        "gpa":                   float(features.get("previous_gpa") or 0),
        "study_hours":           float(features.get("study_hours") or 0),
        "assignment_completion": float(features.get("assignment_completion") or 0),
        "participation":         float(features.get("participation_score") or 0),
        "sleep_hours":           float(features.get("sleep_hours") or 0),
        "practice_test_score":   float(features.get("practice_test_score") or 0),
        "practice_problems":     int(features.get("practice_problems") or 0),
        "predicted_score":       float(predicted_score),
        "performance_level":     performance_level,
        "strengths":             strengths or [],
        "weaknesses":            weaknesses or [],
        "recommendations":       recommendations or [],
        "summary":               summary,
        "created_at":            now,
        "timestamp":             now,
    }

    col = _get_col()
    if col is not None:
        result = col.insert_one({**doc})
        record_id = str(result.inserted_id)
        log.info(f"[MongoDB] Saved → {student_name}: {predicted_score}")
    else:
        # Try JSON Tier
        try:
            data = _load_json()
            record_id = str(len(data) + 1 + int(datetime.now().timestamp()))
            doc["id"] = record_id
            data.append(doc)
            _save_json(data)
            log.info(f"[JSON] Saved → {student_name}: {predicted_score} (total={len(data)})")
        except Exception:
            # Fallback to Memory
            record_id = str(_mem_next_id)
            _mem_next_id += 1
            doc["id"] = record_id
            _mem_store.append(doc)
            log.info(f"[Memory] Saved → {student_name}: {predicted_score} (total={len(_mem_store)})")

    return record_id


def get_analytics() -> dict:
    """Return aggregate statistics + recent 20 records for charts."""
    col = _get_col()

    if col is not None:
        # MongoDB Logic
        pipeline = [{
            "$group": {
                "_id":       None,
                "total":     {"$sum": 1},
                "avg_score": {"$avg": "$predicted_score"},
                "max_score": {"$max": "$predicted_score"},
                "min_score": {"$min": "$predicted_score"},
                "excellent": {"$sum": {"$cond": [{"$eq": ["$performance_level", "Excellent"]}, 1, 0]}},
                "good":      {"$sum": {"$cond": [{"$eq": ["$performance_level", "Good"]},      1, 0]}},
                "average":   {"$sum": {"$cond": [{"$eq": ["$performance_level", "Average"]},   1, 0]}},
                "at_risk":   {"$sum": {"$cond": [{"$eq": ["$performance_level", "At Risk"]},   1, 0]}},
            }
        }]
        agg = list(col.aggregate(pipeline))
        if agg:
            s = agg[0]
            s.pop("_id", None)
            s["avg_score"] = round(s.get("avg_score") or 0, 2)
            s["max_score"] = round(s.get("max_score") or 0, 2)
            s["min_score"] = round(s.get("min_score") or 0, 2)
        else:
            s = _empty_analytics()

        recent_cur = col.find({}, {"student_name": 1, "predicted_score": 1, "created_at": 1}) \
                        .sort("created_at", 1).limit(20)
        recent = []
        for doc in recent_cur:
            recent.append({
                "name":  doc.get("student_name", "?"),
                "score": doc.get("predicted_score", 0),
                "date":  str(doc.get("created_at", ""))[:10],
            })
        s["recent_scores"] = recent
        return s

    else:
        # JSON / Memory Logic
        data = _load_json() or _mem_store
        if not data:
            s = _empty_analytics()
            s["recent_scores"] = []
            return s
        
        scores = [r["predicted_score"] for r in data]
        s = {
            "total":     len(data),
            "avg_score": round(sum(scores) / len(data), 2),
            "max_score": round(max(scores), 2),
            "min_score": round(min(scores), 2),
            "excellent": sum(1 for r in data if r["performance_level"] == "Excellent"),
            "good":      sum(1 for r in data if r["performance_level"] == "Good"),
            "average":   sum(1 for r in data if r["performance_level"] == "Average"),
            "at_risk":   sum(1 for r in data if r["performance_level"] == "At Risk"),
        }
        recent = [
            {"name": r["student_name"], "score": r["predicted_score"], "date": str(r.get("created_at", ""))[:10]}
            for r in data[-20:]
        ]
        s["recent_scores"] = recent
        return s


def search_records(name_query: str = "", level_filter: str = "All", sort_by: str = "latest") -> list:
    col = _get_col()
    if col is not None:
        query = {}
        if name_query:
            query["student_name"] = {"$regex": name_query, "$options": "i"}
        if level_filter and level_filter != "All":
            query["performance_level"] = level_filter
        sort_field = "created_at" if sort_by in ("latest", "date") else "predicted_score"
        cursor = col.find(query).sort(sort_field, -1).limit(200)
        results = []
        for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            results.append(doc)
        return results
    else:
        data = (_load_json() or _mem_store).copy()
        if name_query:
            data = [r for r in data if name_query.lower() in r.get("student_name", "").lower()]
        if level_filter and level_filter != "All":
            data = [r for r in data if r.get("performance_level") == level_filter]
        
        if sort_by == "score":
            data = sorted(data, key=lambda x: x.get("predicted_score", 0), reverse=True)
        else:  # latest
            data = sorted(data, key=lambda x: x.get("created_at", ""), reverse=True)
        return data[:200]


def delete_record(record_id: str) -> None:
    col = _get_col()
    if col is not None:
        from bson.objectid import ObjectId
        col.delete_one({"_id": ObjectId(record_id)})
    else:
        # JSON
        data = _load_json()
        if data:
            new_data = [r for r in data if r.get("id") != record_id]
            if len(new_data) < len(data):
                _save_json(new_data)
                return
        # Memory
        global _mem_store
        _mem_store = [r for r in _mem_store if r.get("id") != record_id]


def clear_db() -> int:
    """Wipe all records from current storage. Returns number of deleted items."""
    col = _get_col()
    count = 0
    if col is not None:
        res = col.delete_many({})
        count = res.deleted_count
        log.info(f"MongoDB cleared: {count} records removed.")
    else:
        # JSON
        data = _load_json()
        count = len(data)
        _save_json([])
        # Memory
        global _mem_store
        count += len(_mem_store)
        _mem_store = []
        log.info(f"Local storage cleared: {count} records removed.")
    return count


def seed_db(force=False) -> int:
    """Seeds the DB with 23 sample records if empty/forced. Returns count added."""
    col = _get_col()
    
    # Check if we should skip
    if not force:
        if col is not None:
            if col.count_documents({}) > 0: return 0
        else:
            if len(_load_json() or _mem_store) > 0: return 0

    seed_records = [
        # EXCELLENT (6)
        {"name": "Rahul Sharma", "att": 95, "gpa": 9.1, "study": 30, "asn": 92, "part": 9, "slp": 7.5, "ptest": 90, "prob": 180, "score": 91, "level": "Excellent", "date": "2026-04-01 10:00:00"},
        {"name": "Priya Patel", "att": 98, "gpa": 9.5, "study": 35, "asn": 98, "part": 10, "slp": 8.0, "ptest": 95, "prob": 200, "score": 97, "level": "Excellent", "date": "2026-04-01 11:30:00"},
        {"name": "Siddharth Malhotra", "att": 92, "gpa": 8.8, "study": 28, "asn": 90, "part": 8, "slp": 7.0, "ptest": 88, "prob": 150, "score": 89, "level": "Excellent", "date": "2026-04-02 09:15:00"},
        {"name": "Ananya Iyer", "att": 96, "gpa": 9.2, "study": 32, "asn": 95, "part": 9, "slp": 7.8, "ptest": 92, "prob": 190, "score": 94, "level": "Excellent", "date": "2026-04-02 14:00:00"},
        {"name": "Arjun Reddy", "att": 94, "gpa": 9.0, "study": 30, "asn": 94, "part": 9, "slp": 7.5, "ptest": 91, "prob": 175, "score": 92, "level": "Excellent", "date": "2026-04-03 10:45:00"},
        {"name": "Ishani Bose", "att": 97, "gpa": 9.4, "study": 34, "asn": 96, "part": 10, "slp": 8.2, "ptest": 94, "prob": 195, "score": 96, "level": "Excellent", "date": "2026-04-03 16:20:00"},
        
        # GOOD (6)
        {"name": "Aditya Verma", "att": 85, "gpa": 7.8, "study": 20, "asn": 82, "part": 7, "slp": 7.0, "ptest": 78, "prob": 100, "score": 79, "level": "Good", "date": "2026-04-01 12:00:00"},
        {"name": "Diya Sen", "att": 88, "gpa": 8.0, "study": 22, "asn": 85, "part": 8, "slp": 6.5, "ptest": 82, "prob": 120, "score": 83, "level": "Good", "date": "2026-04-01 15:45:00"},
        {"name": "Manish Gupta", "att": 82, "gpa": 7.5, "study": 18, "asn": 80, "part": 7, "slp": 6.0, "ptest": 75, "prob": 90, "score": 76, "level": "Good", "date": "2026-04-02 11:20:00"},
        {"name": "Neha Kapoor", "att": 86, "gpa": 7.9, "study": 21, "asn": 84, "part": 8, "slp": 7.2, "ptest": 80, "prob": 110, "score": 81, "level": "Good", "date": "2026-04-02 17:30:00"},
        {"name": "Rohan Nair", "att": 84, "gpa": 7.6, "study": 19, "asn": 81, "part": 7, "slp": 6.8, "ptest": 76, "prob": 95, "score": 77, "level": "Good", "date": "2026-04-03 12:15:00"},
        {"name": "Sanya Das", "att": 87, "gpa": 7.7, "study": 20, "asn": 83, "part": 8, "slp": 7.0, "ptest": 79, "prob": 105, "score": 80, "level": "Good", "date": "2026-04-04 09:40:00"},

        # AVERAGE (6)
        {"name": "Kabir Singh", "att": 75, "gpa": 6.5, "study": 12, "asn": 70, "part": 5, "slp": 6.0, "ptest": 65, "prob": 50, "score": 64, "level": "Average", "date": "2026-04-01 14:10:00"},
        {"name": "Zoya Khan", "att": 72, "gpa": 6.2, "study": 10, "asn": 65, "part": 5, "slp": 5.5, "ptest": 60, "prob": 40, "score": 60, "level": "Average", "date": "2026-04-02 10:30:00"},
        {"name": "Vikram Rao", "att": 78, "gpa": 6.8, "study": 14, "asn": 72, "part": 6, "slp": 6.5, "ptest": 68, "prob": 60, "score": 67, "level": "Average", "date": "2026-04-02 16:00:00"},
        {"name": "Meera Pillai", "att": 70, "gpa": 6.0, "study": 11, "asn": 68, "part": 5, "slp": 5.0, "ptest": 62, "prob": 45, "score": 61, "level": "Average", "date": "2026-04-03 13:20:00"},
        {"name": "Aryan Joshi", "att": 74, "gpa": 6.4, "study": 13, "asn": 71, "part": 6, "slp": 6.2, "ptest": 64, "prob": 55, "score": 65, "level": "Average", "date": "2026-04-04 11:10:00"},
        {"name": "Kyra Shah", "att": 71, "gpa": 6.1, "study": 10, "asn": 66, "part": 5, "slp": 5.2, "ptest": 61, "prob": 42, "score": 59, "level": "Average", "date": "2026-04-04 15:30:00"},

        # AT RISK (5)
        {"name": "Yash Mehra", "att": 55, "gpa": 4.5, "study": 5, "asn": 50, "part": 3, "slp": 5.0, "ptest": 45, "prob": 20, "score": 46, "level": "At Risk", "date": "2026-04-01 16:50:00"},
        {"name": "Tanya Bajaj", "att": 50, "gpa": 4.0, "study": 4, "asn": 45, "part": 2, "slp": 4.5, "ptest": 40, "prob": 15, "score": 42, "level": "At Risk", "date": "2026-04-02 12:40:00"},
        {"name": "Rajesh Pal", "att": 45, "gpa": 3.5, "study": 3, "asn": 40, "part": 2, "slp": 4.0, "ptest": 35, "prob": 10, "score": 38, "level": "At Risk", "date": "2026-04-03 15:10:00"},
        {"name": "Simran Kaur", "att": 40, "gpa": 3.0, "study": 2, "asn": 35, "part": 1, "slp": 4.0, "ptest": 30, "prob": 5, "score": 33, "level": "At Risk", "date": "2026-04-04 12:50:00"},
        {"name": "Amit Trivedi", "att": 35, "gpa": 2.5, "study": 1, "asn": 30, "part": 1, "slp": 3.5, "ptest": 25, "prob": 2, "score": 28, "level": "At Risk", "date": "2026-04-04 17:00:00"},
    ]

    from src.recommendations import analyse
    
    count = 0
    for r in seed_records:
        feats = {
            "attendance": r["att"], "previous_gpa": r["gpa"], 
            "study_hours": r["study"], "assignment_completion": r["asn"],
            "participation_score": r["part"], "sleep_hours": r["slp"],
            "practice_test_score": r["ptest"], "practice_problems": r["prob"]
        }
        res = analyse(feats, r["score"])
        insert_prediction(
            student_name=r["name"], features=feats, predicted_score=r["score"],
            performance_level=r["level"], strengths=res.strengths,
            weaknesses=res.weaknesses, recommendations=res.recommendations,
            summary=res.summary, created_at=r["date"]
        )
        count += 1
    
    log.info(f"Seeded {count} records.")
    return count


def _empty_analytics() -> dict:
    return {
        "total": 0, "avg_score": 0, "max_score": 0, "min_score": 0,
        "excellent": 0, "good": 0, "average": 0, "at_risk": 0,
    }
