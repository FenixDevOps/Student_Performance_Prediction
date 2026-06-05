from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import io

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user, require_teacher_or_admin, require_any_user
from backend.app.database.models import User, PredictionRecord
from backend.app.schemas.predict import StudentFeatureInput, PredictionResultResponse
from backend.app.ml.inference import predict_single
from backend.app.services.ai_engine import generate_ai_analysis
from backend.app.services.exporter import generate_pdf_report, generate_excel_report

router = APIRouter()

@router.post("/predict", response_model=PredictionResultResponse)
def create_prediction(
    student_in: StudentFeatureInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    """
    Run prediction for a student, run AI analytics, and store the record.
    Accessible only to Teachers and Admins.
    """
    features = {
        "attendance": student_in.attendance,
        "previous_gpa": student_in.previous_gpa,
        "study_hours": student_in.study_hours,
        "assignment_completion": student_in.assignment_completion,
        "participation_score": student_in.participation_score,
        "sleep_hours": student_in.sleep_hours,
        "practice_test_score": student_in.practice_test_score,
        "practice_problems": student_in.practice_problems
    }
    
    # Run ML Model
    ml_res = predict_single(features)
    predicted_score = ml_res["predicted_score"]
    performance_level = ml_res["performance_level"]
    confidence_score = ml_res["confidence_score"]
    risk_level = ml_res["risk_level"]
    
    # Run AI Analysis
    ai_res = generate_ai_analysis(features, predicted_score)
    
    # Check if a student user matches by email/name to link student account
    # For now, search user table by full_name or email prefix
    linked_student = db.query(User).filter(
        (User.full_name == student_in.student_name) & (User.role == "student")
    ).first()
    
    student_id = linked_student.id if linked_student else None
    
    db_record = PredictionRecord(
        student_name=student_in.student_name,
        attendance=student_in.attendance,
        previous_gpa=student_in.previous_gpa,
        study_hours=student_in.study_hours,
        assignment_completion=student_in.assignment_completion,
        participation_score=student_in.participation_score,
        sleep_hours=student_in.sleep_hours,
        practice_test_score=student_in.practice_test_score,
        practice_problems=student_in.practice_problems,
        predicted_score=predicted_score,
        performance_level=performance_level,
        confidence_score=confidence_score,
        risk_level=risk_level,
        summary=ai_res["summary"],
        strengths=ai_res["strengths"],
        weaknesses=ai_res["weaknesses"],
        recommendations=ai_res["recommendations"],
        learning_roadmap=ai_res["learning_roadmap"],
        created_by_id=current_user.id,
        student_id=student_id
    )
    
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

@router.get("/history", response_model=List[PredictionResultResponse])
def get_prediction_history(
    query: Optional[str] = Query(None, description="Search by student name"),
    level: str = Query("All", description="Filter by Performance Level"),
    sort: str = Query("latest", description="Sort by 'latest' or 'score'"),
    current_user: User = Depends(require_any_user),
    db: Session = Depends(get_db)
):
    """
    Search historical predictions.
    Students see only their own reports. Teachers & Admins see all.
    """
    db_query = db.query(PredictionRecord)
    
    # Role isolation
    if current_user.role == "student":
        # Match student email or user ID
        db_query = db_query.filter(
            (PredictionRecord.student_id == current_user.id) | 
            (PredictionRecord.student_name == current_user.full_name)
        )
    else:
        # Teacher/Admin filtering
        if query:
            db_query = db_query.filter(PredictionRecord.student_name.ilike(f"%{query}%"))
        if level != "All":
            db_query = db_query.filter(PredictionRecord.performance_level == level)
            
    # Sorting
    if sort == "score":
        db_query = db_query.order_by(PredictionRecord.predicted_score.desc())
    else:  # default latest
        db_query = db_query.order_by(PredictionRecord.created_at.desc())
        
    return db_query.limit(200).all()

@router.get("/record/{record_id}", response_model=PredictionResultResponse)
def get_single_record(
    record_id: int,
    current_user: User = Depends(require_any_user),
    db: Session = Depends(get_db)
):
    """Fetch details of a single prediction report."""
    rec = db.query(PredictionRecord).filter(PredictionRecord.id == record_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Prediction record not found.")
        
    # Security check for Student Role
    if current_user.role == "student" and rec.student_id != current_user.id and rec.student_name != current_user.full_name:
        raise HTTPException(status_code=403, detail="You do not have permission to view this report.")
        
    return rec

@router.delete("/record/{record_id}")
def delete_prediction_record(
    record_id: int,
    current_user: User = Depends(require_teacher_or_admin),
    db: Session = Depends(get_db)
):
    """Delete a prediction record. Admin and Teacher only."""
    rec = db.query(PredictionRecord).filter(PredictionRecord.id == record_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Record not found.")
    db.delete(rec)
    db.commit()
    return {"success": True, "message": f"Record {record_id} deleted successfully."}

@router.get("/export/pdf/{record_id}")
def export_pdf(
    record_id: int,
    current_user: User = Depends(require_any_user),
    db: Session = Depends(get_db)
):
    """Stream PDF format for a prediction report."""
    rec = db.query(PredictionRecord).filter(PredictionRecord.id == record_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Record not found.")
        
    # Role isolation
    if current_user.role == "student" and rec.student_id != current_user.id and rec.student_name != current_user.full_name:
        raise HTTPException(status_code=403, detail="Unauthorized access to this PDF.")
        
    # Serialize to dictionary for reportlab helper
    record_dict = {
        "student_name": rec.student_name,
        "attendance": rec.attendance,
        "previous_gpa": rec.previous_gpa,
        "study_hours": rec.study_hours,
        "assignment_completion": rec.assignment_completion,
        "participation_score": rec.participation_score,
        "sleep_hours": rec.sleep_hours,
        "practice_test_score": rec.practice_test_score,
        "practice_problems": rec.practice_problems,
        "predicted_score": rec.predicted_score,
        "performance_level": rec.performance_level,
        "confidence_score": rec.confidence_score,
        "risk_level": rec.risk_level,
        "summary": rec.summary,
        "strengths": rec.strengths,
        "weaknesses": rec.weaknesses,
        "recommendations": rec.recommendations,
        "learning_roadmap": rec.learning_roadmap,
        "created_at": rec.created_at
    }
    
    pdf_buffer = generate_pdf_report(record_dict)
    filename = f"report_{rec.student_name.replace(' ', '_')}_{rec.id}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/export/excel")
def export_excel(
    current_user: User = Depends(require_teacher_or_admin),
    db: Session = Depends(get_db)
):
    """Streams predictions history spreadsheet. Admin/Teacher only."""
    records = db.query(PredictionRecord).order_by(PredictionRecord.created_at.desc()).all()
    
    # Serialize records list
    records_list = []
    for rec in records:
        records_list.append({
            "id": rec.id,
            "student_name": rec.student_name,
            "predicted_score": rec.predicted_score,
            "performance_level": rec.performance_level,
            "confidence_score": rec.confidence_score,
            "risk_level": rec.risk_level,
            "attendance": rec.attendance,
            "previous_gpa": rec.previous_gpa,
            "study_hours": rec.study_hours,
            "assignment_completion": rec.assignment_completion,
            "participation_score": rec.participation_score,
            "sleep_hours": rec.sleep_hours,
            "practice_test_score": rec.practice_test_score,
            "practice_problems": rec.practice_problems,
            "created_at": rec.created_at
        })
        
    excel_buffer = generate_excel_report(records_list)
    filename = f"predictions_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return StreamingResponse(
        excel_buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
