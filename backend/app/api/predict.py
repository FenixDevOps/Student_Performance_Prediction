from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import io
import os
import json
import csv
from datetime import datetime

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user, require_teacher_or_admin, require_any_user
from backend.app.database.models import User, PredictionRecord, RoadmapTaskState, SystemAlert
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
    
    # Trigger automated risk alert
    if risk_level == "High":
        alert = SystemAlert(
            student_name=student_in.student_name,
            predicted_score=predicted_score,
            attendance=student_in.attendance
        )
        db.add(alert)
        
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

@router.get("/roadmap/tasks")
def get_roadmap_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_user)
):
    """Retrieve all study roadmap tasks and their checkmark states for the current student."""
    latest = db.query(PredictionRecord).filter(
        (PredictionRecord.student_id == current_user.id) |
        (PredictionRecord.student_name == current_user.full_name)
    ).order_by(PredictionRecord.created_at.desc()).first()
    
    if not latest:
        return {"tasks": []}
        
    states = db.query(RoadmapTaskState).filter(
        RoadmapTaskState.prediction_record_id == latest.id,
        RoadmapTaskState.user_id == current_user.id
    ).all()
    
    state_map = {(s.week_number, s.task_index): s.completed for s in states}
    
    flat_tasks = []
    roadmap = latest.learning_roadmap or []
    for week_data in roadmap:
        week = week_data.get("week")
        title = week_data.get("title")
        focus = week_data.get("focus")
        for idx, task in enumerate(week_data.get("tasks", [])):
            completed = state_map.get((week, idx), False)
            flat_tasks.append({
                "week": week,
                "title": title,
                "focus": focus,
                "task_index": idx,
                "task": task,
                "completed": completed
            })
            
    return {"prediction_id": latest.id, "tasks": flat_tasks}

@router.put("/roadmap/tasks")
def toggle_roadmap_task(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_user)
):
    """Toggle a roadmap task checkmark. Awards XP and updates streaks."""
    pred_id = payload.get("prediction_id")
    week = payload.get("week")
    idx = payload.get("task_index")
    completed = payload.get("completed", False)
    
    if pred_id is None or week is None or idx is None:
        raise HTTPException(status_code=400, detail="Missing required parameters.")
        
    pred = db.query(PredictionRecord).filter(PredictionRecord.id == pred_id).first()
    if not pred:
        raise HTTPException(status_code=404, detail="Prediction record not found.")
        
    if current_user.role == "student" and pred.student_id != current_user.id and pred.student_name != current_user.full_name:
        raise HTTPException(status_code=403, detail="Not authorized to update this roadmap.")
        
    state = db.query(RoadmapTaskState).filter(
        RoadmapTaskState.user_id == current_user.id,
        RoadmapTaskState.prediction_record_id == pred_id,
        RoadmapTaskState.week_number == week,
        RoadmapTaskState.task_index == idx
    ).first()
    
    xp_gained = 0
    
    if not state:
        state = RoadmapTaskState(
            user_id=current_user.id,
            prediction_record_id=pred_id,
            week_number=week,
            task_index=idx,
            completed=completed
        )
        db.add(state)
    else:
        prev_completed = state.completed
        state.completed = completed
        if completed and not prev_completed:
            state.completed_at = datetime.utcnow()
            
    if completed:
        xp_gained += 10
        
        # Check if entire week is completed
        roadmap_week = next((w for w in (pred.learning_roadmap or []) if w.get("week") == week), None)
        if roadmap_week:
            total_tasks = len(roadmap_week.get("tasks", []))
            completed_states = db.query(RoadmapTaskState).filter(
                RoadmapTaskState.user_id == current_user.id,
                RoadmapTaskState.prediction_record_id == pred_id,
                RoadmapTaskState.week_number == week,
                RoadmapTaskState.completed == True
            ).all()
            
            completed_indices = {s.task_index for s in completed_states}
            completed_indices.add(idx)
            
            if len(completed_indices) >= total_tasks:
                xp_gained += 50
                
        # Update streak
        now = datetime.utcnow()
        last_completed = current_user.last_task_completed_at
        if last_completed:
            delta_days = (now.date() - last_completed.date()).days
            if delta_days == 1:
                current_user.current_streak += 1
            elif delta_days > 1:
                current_user.current_streak = 1
        else:
            current_user.current_streak = 1
            
        current_user.last_task_completed_at = now
        current_user.xp_points += xp_gained
        
    db.commit()
    db.refresh(current_user)
    
    return {
        "success": True,
        "completed": completed,
        "xp_gained": xp_gained,
        "total_xp": current_user.xp_points,
        "streak": current_user.current_streak
    }

@router.post("/chat")
def chat_about_roadmap(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_user)
):
    """Answer questions about the student's study roadmap using local heuristics or Gemini API."""
    pred_id = payload.get("prediction_id")
    message = payload.get("message", "").strip()
    
    if not pred_id or not message:
        raise HTTPException(status_code=400, detail="Missing prediction_id or message.")
        
    pred = db.query(PredictionRecord).filter(PredictionRecord.id == pred_id).first()
    if not pred:
        raise HTTPException(status_code=404, detail="Prediction record not found.")
        
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        response_text = ""
        msg_lower = message.lower()
        
        weaknesses = [w.split(":")[0].strip() for w in (pred.weaknesses or [])]
        strengths = [s.split(":")[0].strip() for w in (pred.strengths or [])]
        
        if "roadmap" in msg_lower or "week" in msg_lower:
            response_text = f"Your study roadmap focuses on correcting weaknesses in {', '.join(weaknesses) if weaknesses else 'general study areas'}. For week 1, you should prioritize stabilizing your routine. Let me know if you want detailed steps for any specific task!"
        elif "sleep" in msg_lower and "Sleep" in weaknesses:
            response_text = "I notice that your sleep schedule is below the healthy benchmark of 7-8 hours. Sleep is crucial for memory consolidation. Try setting a screen curfew 30 minutes before bed."
        elif "study" in msg_lower and "Study Hours" in weaknesses:
            response_text = "To build up your study habits, try using the Pomodoro technique (25 minutes studying, 5 minutes break). Block out specific slots in your calendar just like you do for classes."
        elif "attendance" in msg_lower and "Attendance" in weaknesses:
            response_text = "Your attendance is currently a risk factor. Showing up consistently to lectures is the easiest way to catch key instructions and stay on track. Try finding a buddy to keep you accountable."
        else:
            response_text = f"Hello {current_user.full_name}! As your AI study assistant, I see you are working to hit a predicted score of {pred.predicted_score}%. Your biggest strength is {strengths[0] if strengths else 'consistency'}, and we are working to improve {weaknesses[0] if weaknesses else 'study habits'}. What specific questions do you have about your roadmap?"
            
        return {"response": response_text}
        
    else:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            context = f"""
            You are a helpful educational chatbot assistant for a student named {current_user.full_name}.
            The student has the following prediction metrics:
            - Predicted Exam Score: {pred.predicted_score}%
            - Performance Category: {pred.performance_level}
            - Risk Status: {pred.risk_level}
            - Strengths: {', '.join(pred.strengths or [])}
            - Weaknesses: {', '.join(pred.weaknesses or [])}
            - Learning Roadmap: {json.dumps(pred.learning_roadmap or [])}
            
            Answer the student's query concisely and directly, giving practical, encouraging advice to help them succeed.
            """
            
            response = model.generate_content([context, message])
            return {"response": response.text}
        except Exception as e:
            return {"response": f"AI Assistant is currently offline (API error: {str(e)}). Focus on your roadmap tasks to stay ahead!"}

@router.post("/bulk")
def upload_bulk_evaluations(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    """Upload a CSV of student feature inputs, predict all scores, save reports, and trigger alerts."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
        
    try:
        content = file.file.read().decode('utf-8')
        csv_file = io.StringIO(content)
        reader = csv.DictReader(csv_file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV file: {str(e)}")
        
    results = []
    errors = []
    success_count = 0
    
    key_map = {
        "name": "student_name",
        "student_name": "student_name",
        "attendance": "attendance",
        "previous_gpa": "previous_gpa",
        "study_hours": "study_hours",
        "assignment_completion": "assignment_completion",
        "participation_score": "participation_score",
        "sleep_hours": "sleep_hours",
        "practice_test_score": "practice_test_score",
        "practice_problems": "practice_problems"
    }
    
    for row_idx, row in enumerate(reader):
        try:
            normalized = {}
            for k, v in row.items():
                if k:
                    norm_key = key_map.get(k.strip().lower())
                    if norm_key:
                        normalized[norm_key] = v.strip() if v else ""
                        
            name = normalized.get("student_name", "").strip()
            if not name:
                name = f"Student {row_idx + 1}"
                
            feats = {
                "attendance": float(normalized.get("attendance", 0.0)),
                "previous_gpa": float(normalized.get("previous_gpa", 0.0)),
                "study_hours": float(normalized.get("study_hours", 0.0)),
                "assignment_completion": float(normalized.get("assignment_completion", 0.0)),
                "participation_score": float(normalized.get("participation_score", 0.0)),
                "sleep_hours": float(normalized.get("sleep_hours", 0.0)),
                "practice_test_score": float(normalized.get("practice_test_score", 0.0)),
                "practice_problems": int(float(normalized.get("practice_problems", 0.0)))
            }
            
            pred_res = predict_single(feats)
            ai_res = generate_ai_analysis(feats, pred_res["predicted_score"])
            
            student = db.query(User).filter(
                (User.full_name == name) & (User.role == "student")
            ).first()
            student_id = student.id if student else None
            
            rec = PredictionRecord(
                student_name=name,
                attendance=feats["attendance"],
                previous_gpa=feats["previous_gpa"],
                study_hours=feats["study_hours"],
                assignment_completion=feats["assignment_completion"],
                participation_score=feats["participation_score"],
                sleep_hours=feats["sleep_hours"],
                practice_test_score=feats["practice_test_score"],
                practice_problems=feats["practice_problems"],
                predicted_score=pred_res["predicted_score"],
                performance_level=pred_res["performance_level"],
                confidence_score=pred_res["confidence_score"],
                risk_level=pred_res["risk_level"],
                summary=ai_res["summary"],
                strengths=ai_res["strengths"],
                weaknesses=ai_res["weaknesses"],
                recommendations=ai_res["recommendations"],
                learning_roadmap=ai_res["learning_roadmap"],
                created_by_id=current_user.id,
                student_id=student_id
            )
            db.add(rec)
            
            if pred_res["risk_level"] == "High":
                alert = SystemAlert(
                    student_name=name,
                    predicted_score=pred_res["predicted_score"],
                    attendance=feats["attendance"]
                )
                db.add(alert)
                
            success_count += 1
            results.append({
                "name": name,
                "score": pred_res["predicted_score"],
                "level": pred_res["performance_level"],
                "risk": pred_res["risk_level"]
            })
        except Exception as row_err:
            errors.append(f"Row {row_idx + 1} ({row.get('name') or row.get('student_name')}): {str(row_err)}")
            
    if success_count > 0:
        db.commit()
        
    return {
        "success": True,
        "total_processed": success_count + len(errors),
        "success_count": success_count,
        "error_count": len(errors),
        "errors": errors,
        "results": results
    }

