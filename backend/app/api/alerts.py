from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import os

from backend.app.core.database import get_db
from backend.app.core.security import require_teacher_or_admin
from backend.app.database.models import User, SystemAlert, PredictionRecord

router = APIRouter()

@router.get("")
def get_unresolved_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    """List all unresolved high-risk alerts. Teacher/Admin only."""
    return db.query(SystemAlert).filter(SystemAlert.resolved == False).order_by(SystemAlert.created_at.desc()).all()
    
@router.post("/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    """Mark an alert as resolved. Teacher/Admin only."""
    alert = db.query(SystemAlert).filter(SystemAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
        
    alert.resolved = True
    db.commit()
    return {"success": True, "message": f"Alert {alert_id} resolved successfully."}
    
@router.post("/email")
def email_parent_report(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    """Dispatches performance report PDF to parent's email. Mocks or sends email."""
    rec_id = payload.get("record_id")
    parent_email = payload.get("parent_email", "").strip()
    
    if not rec_id or not parent_email:
        raise HTTPException(status_code=400, detail="Missing record_id or parent_email.")
        
    rec = db.query(PredictionRecord).filter(PredictionRecord.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Prediction record not found.")
        
    # Dispatch email (Mock/Console print for demonstration)
    subject = f"Academic Risk Notification: Student {rec.student_name} Performance Review"
    body = f"""
    Dear Parent/Advisor,
    
    We are writing to notify you regarding the academic evaluation report for {rec.student_name}.
    Based on the classroom metrics, their projected final exam grade is currently {rec.predicted_score}% ({rec.performance_level} Performance), with a risk assessment of: {rec.risk_level}.
    
    We have attached the comprehensive PDF report containing personalized strengths, weaknesses, and a 4-week study roadmap to help them correct these patterns.
    
    Sincerely,
    School Portal Administration
    """
    
    print("="*60)
    print(f"[MAIL DISPATCH] TO: {parent_email}")
    print(f"[MAIL DISPATCH] SUBJECT: {subject}")
    print(f"[MAIL DISPATCH] BODY:\n{body}")
    print(f"[MAIL DISPATCH] ATTACHMENT: report_{rec.student_name.replace(' ', '_')}_{rec.id}.pdf")
    print("="*60)
    
    return {
        "success": True,
        "message": f"Report successfully dispatched to {parent_email} via mock mailer.",
        "details": {
            "to": parent_email,
            "subject": subject
        }
    }
