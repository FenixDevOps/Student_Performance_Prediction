from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user, require_any_user
from backend.app.database.models import User, PredictionRecord

router = APIRouter()

@router.get("")
def get_dashboard_analytics(
    current_user: User = Depends(require_any_user),
    db: Session = Depends(get_db)
):
    """
    Get dashboard KPI cards and chart datasets.
    Isolates data by user roles: students view personal, teachers/admins view aggregate.
    """
    base_query = db.query(PredictionRecord)
    
    if current_user.role == "student":
        # Student specific analytics
        base_query = base_query.filter(
            (PredictionRecord.student_id == current_user.id) |
            (PredictionRecord.student_name == current_user.full_name)
        )
        
        records = base_query.order_by(PredictionRecord.created_at.asc()).all()
        
        if not records:
            return {
                "role": "student",
                "total": 0,
                "avg_score": 0.0,
                "max_score": 0.0,
                "min_score": 0.0,
                "latest_score": 0.0,
                "performance_level": "Average",
                "risk_level": "Low",
                "confidence_score": 0.0,
                "history": [],
                "current_metrics": {
                    "attendance": 0,
                    "study_hours": 0,
                    "sleep_hours": 0,
                    "assignment_completion": 0,
                    "practice_test_score": 0,
                    "practice_problems": 0,
                    "previous_gpa": 0.0,
                    "participation_score": 0
                }
            }
            
        scores = [r.predicted_score for r in records]
        latest = records[-1]
        
        # Format a chronological progression history
        history_points = []
        for r in records:
            history_points.append({
                "date": r.created_at.strftime("%Y-%m-%d"),
                "score": r.predicted_score,
                "attendance": r.attendance,
                "study_hours": r.study_hours
            })
            
        return {
            "role": "student",
            "total": len(records),
            "avg_score": round(sum(scores) / len(records), 2),
            "max_score": max(scores),
            "min_score": min(scores),
            "latest_score": latest.predicted_score,
            "performance_level": latest.performance_level,
            "risk_level": latest.risk_level,
            "confidence_score": latest.confidence_score,
            "history": history_points,
            # Current values compared to benchmarks
            "current_metrics": {
                "attendance": latest.attendance,
                "study_hours": latest.study_hours,
                "sleep_hours": latest.sleep_hours,
                "assignment_completion": latest.assignment_completion,
                "practice_test_score": latest.practice_test_score,
                "practice_problems": latest.practice_problems,
                "previous_gpa": latest.previous_gpa,
                "participation_score": latest.participation_score
            }
        }
        
    else:
        # Teacher and Admin school-wide aggregate analytics
        total = base_query.count()
        if total == 0:
            return {
                "role": current_user.role,
                "total": 0,
                "avg_score": 0.0,
                "max_score": 0.0,
                "min_score": 0.0,
                "performance_dist": {"Excellent": 0, "Good": 0, "Average": 0, "At Risk": 0},
                "risk_dist": {"High": 0, "Medium": 0, "Low": 0},
                "scatter_data": [],
                "recent_history": []
            }
            
        # Overall aggregates
        stats = db.query(
            func.avg(PredictionRecord.predicted_score).label("avg_score"),
            func.max(PredictionRecord.predicted_score).label("max_score"),
            func.min(PredictionRecord.predicted_score).label("min_score")
        ).first()
        
        # Performance categories distribution
        perf_dist = {"Excellent": 0, "Good": 0, "Average": 0, "At Risk": 0}
        perf_query = db.query(
            PredictionRecord.performance_level, 
            func.count(PredictionRecord.id)
        ).group_by(PredictionRecord.performance_level).all()
        for level, count in perf_query:
            if level in perf_dist:
                perf_dist[level] = count
                
        # Risk categories distribution
        risk_dist = {"High": 0, "Medium": 0, "Low": 0}
        risk_query = db.query(
            PredictionRecord.risk_level, 
            func.count(PredictionRecord.id)
        ).group_by(PredictionRecord.risk_level).all()
        for r_level, count in risk_query:
            if r_level in risk_dist:
                risk_dist[r_level] = count
                
        # Correlation coordinate sets for charts (scatter plots)
        all_records = base_query.order_by(PredictionRecord.created_at.desc()).limit(100).all()
        scatter_data = []
        for r in all_records:
            scatter_data.append({
                "name": r.student_name,
                "attendance": r.attendance,
                "study_hours": r.study_hours,
                "previous_gpa": r.previous_gpa,
                "practice_test_score": r.practice_test_score,
                "score": r.predicted_score,
                "risk": r.risk_level,
                "level": r.performance_level
            })
            
        # Recent prediction logs
        recent_scores = []
        recent_records = base_query.order_by(PredictionRecord.created_at.desc()).limit(10).all()
        for r in recent_records:
            recent_scores.append({
                "id": r.id,
                "name": r.student_name,
                "score": r.predicted_score,
                "level": r.performance_level,
                "risk": r.risk_level,
                "date": r.created_at.strftime("%Y-%m-%d %H:%M")
            })
            
        return {
            "role": current_user.role,
            "total": total,
            "avg_score": round(float(stats.avg_score or 0.0), 2),
            "max_score": round(float(stats.max_score or 0.0), 2),
            "min_score": round(float(stats.min_score or 0.0), 2),
            "performance_dist": perf_dist,
            "risk_dist": risk_dist,
            "scatter_data": scatter_data,
            "recent_history": recent_scores
        }
