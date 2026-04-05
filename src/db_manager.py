"""
db_manager.py
--------------
Storage layer with three tiers:
  1. MongoDB Atlas  (when MONGO_URI env var is set)  → fully persistent
  2. In-memory list (no MONGO_URI)                   → persists for session lifetime
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional, List

log = logging.getLogger(__name__)

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
        log.warning(f"MongoDB unavailable ({exc}) — using in-memory storage")
        return None

# ── PUBLIC API ─────────────────────────────────────────────────────────────────

def init_db() -> None:
    """Initialize storage. Fails silently so it never crashes the app."""
    try:
        col = _get_col()
        if col is not None:
            log.info("Storage: MongoDB Atlas")
        else:
            log.info("Storage: In-memory (set MONGO_URI env var for persistence)")
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
) -> str:
    """Insert a full prediction record. Returns the record id."""
    global _mem_next_id

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
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
        # kept for backward-compat with old frontend references
        "timestamp":             now,
    }

    col = _get_col()
    if col is not None:
        result = col.insert_one({**doc})
        record_id = str(result.inserted_id)
        log.info(f"[MongoDB] Saved → {student_name}: {predicted_score}")
    else:
        record_id = str(_mem_next_id)
        _mem_next_id += 1
        doc["id"] = record_id
        _mem_store.append(doc)
        log.info(f"[Memory] Saved → {student_name}: {predicted_score}  (total={len(_mem_store)})")

    return record_id


def get_analytics() -> dict:
    """Return aggregate statistics + recent 20 records for charts."""
    col = _get_col()

    if col is not None:
        # ── MongoDB aggregation ───────────────────────────────────────────────
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

        # recent 20 for trend chart
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
        # ── In-memory computation ─────────────────────────────────────────────
        if not _mem_store:
            s = _empty_analytics()
            s["recent_scores"] = []
            return s
        scores = [r["predicted_score"] for r in _mem_store]
        s = {
            "total":     len(_mem_store),
            "avg_score": round(sum(scores) / len(scores), 2),
            "max_score": round(max(scores), 2),
            "min_score": round(min(scores), 2),
            "excellent": sum(1 for r in _mem_store if r["performance_level"] == "Excellent"),
            "good":      sum(1 for r in _mem_store if r["performance_level"] == "Good"),
            "average":   sum(1 for r in _mem_store if r["performance_level"] == "Average"),
            "at_risk":   sum(1 for r in _mem_store if r["performance_level"] == "At Risk"),
        }
        recent = [
            {"name": r["student_name"], "score": r["predicted_score"], "date": str(r.get("created_at", ""))[:10]}
            for r in _mem_store[-20:]
        ]
        s["recent_scores"] = recent
        return s


# ── kept for backwards-compat (app.py /api/stats) ─────────────────────────────
def get_summary_stats() -> dict:
    return get_analytics()


def search_records(
    name_query: str = "",
    level_filter: str = "All",
    sort_by: str = "latest",
) -> list:
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
        data = list(_mem_store)
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
        log.info(f"[MongoDB] Deleted id={record_id}")
    else:
        global _mem_store
        before = len(_mem_store)
        _mem_store = [r for r in _mem_store if r.get("id") != record_id]
        log.info(f"[Memory] Deleted id={record_id}  (removed {before - len(_mem_store)} records)")


def _empty_analytics() -> dict:
    return {
        "total": 0, "avg_score": 0, "max_score": 0, "min_score": 0,
        "excellent": 0, "good": 0, "average": 0, "at_risk": 0,
    }
