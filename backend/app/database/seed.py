import datetime
from sqlalchemy.orm import Session
from backend.app.core.security import get_password_hash
from backend.app.database.models import User, PredictionRecord
from backend.app.services.ai_engine import generate_ai_analysis

def seed_database(db: Session) -> int:
    """
    Seeds database with initial users (admin, teacher, student) and
    23 structured prediction history records. Returns count of predictions added.
    """
    # 1. Create Default Users if they don't exist
    users = [
        {"email": "admin@example.com", "name": "System Administrator", "pass": "admin123", "role": "admin"},
        {"email": "teacher@example.com", "name": "Professor Sarah Jenkins", "pass": "teacher123", "role": "teacher"},
        {"email": "student@example.com", "name": "Rahul Sharma", "pass": "student123", "role": "student"},
    ]
    
    seeded_users = {}
    for u in users:
        existing = db.query(User).filter(User.email == u["email"]).first()
        if not existing:
            new_user = User(
                email=u["email"],
                full_name=u["name"],
                hashed_password=get_password_hash(u["pass"]),
                role=u["role"]
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            seeded_users[u["role"]] = new_user
        else:
            seeded_users[u["role"]] = existing
            
    # Check if predictions already seeded
    if db.query(PredictionRecord).count() > 0:
        return 0
        
    # 2. Add Mock Predictions
    seed_records = [
        # EXCELLENT (6)
        {"name": "Rahul Sharma", "att": 95.0, "gpa": 9.1, "study": 30.0, "asn": 92.0, "part": 9.0, "slp": 7.5, "ptest": 90.0, "prob": 180, "score": 91.0, "level": "Excellent", "date": "2026-04-01 10:00:00", "student_role": "student"},
        {"name": "Priya Patel", "att": 98.0, "gpa": 9.5, "study": 35.0, "asn": 98.0, "part": 10.0, "slp": 8.0, "ptest": 95.0, "prob": 200, "score": 97.0, "level": "Excellent", "date": "2026-04-01 11:30:00"},
        {"name": "Siddharth Malhotra", "att": 92.0, "gpa": 8.8, "study": 28.0, "asn": 90.0, "part": 8.0, "slp": 7.0, "ptest": 88.0, "prob": 150, "score": 89.0, "level": "Excellent", "date": "2026-04-02 09:15:00"},
        {"name": "Ananya Iyer", "att": 96.0, "gpa": 9.2, "study": 32.0, "asn": 95.0, "part": 9.0, "slp": 7.8, "ptest": 92.0, "prob": 190, "score": 94.0, "level": "Excellent", "date": "2026-04-02 14:00:00"},
        {"name": "Arjun Reddy", "att": 94.0, "gpa": 9.0, "study": 30.0, "asn": 94.0, "part": 9.0, "slp": 7.5, "ptest": 91.0, "prob": 175, "score": 92.0, "level": "Excellent", "date": "2026-04-03 10:45:00"},
        {"name": "Ishani Bose", "att": 97.0, "gpa": 9.4, "study": 34.0, "asn": 96.0, "part": 10.0, "slp": 8.2, "ptest": 94.0, "prob": 195, "score": 96.0, "level": "Excellent", "date": "2026-04-03 16:20:00"},
        
        # GOOD (6)
        {"name": "Aditya Verma", "att": 85.0, "gpa": 7.8, "study": 20.0, "asn": 82.0, "part": 7.0, "slp": 7.0, "ptest": 78.0, "prob": 100, "score": 79.0, "level": "Good", "date": "2026-04-01 12:00:00"},
        {"name": "Diya Sen", "att": 88.0, "gpa": 8.0, "study": 22.0, "asn": 85.0, "part": 8.0, "slp": 6.5, "ptest": 82.0, "prob": 120, "score": 83.0, "level": "Good", "date": "2026-04-01 15:45:00"},
        {"name": "Manish Gupta", "att": 82.0, "gpa": 7.5, "study": 18.0, "asn": 80.0, "part": 7.0, "slp": 6.0, "ptest": 75.0, "prob": 90, "score": 76.0, "level": "Good", "date": "2026-04-02 11:20:00"},
        {"name": "Neha Kapoor", "att": 86.0, "gpa": 7.9, "study": 21.0, "asn": 84.0, "part": 8.0, "slp": 7.2, "ptest": 80.0, "prob": 110, "score": 81.0, "level": "Good", "date": "2026-04-02 17:30:00"},
        {"name": "Rohan Nair", "att": 84.0, "gpa": 7.6, "study": 19.0, "asn": 81.0, "part": 7.0, "slp": 6.8, "ptest": 76.0, "prob": 95, "score": 77.0, "level": "Good", "date": "2026-04-03 12:15:00"},
        {"name": "Sanya Das", "att": 87.0, "gpa": 7.7, "study": 20.0, "asn": 83.0, "part": 8.0, "slp": 7.0, "ptest": 79.0, "prob": 105, "score": 80.0, "level": "Good", "date": "2026-04-04 09:40:00"},

        # AVERAGE (6)
        {"name": "Kabir Singh", "att": 75.0, "gpa": 6.5, "study": 12.0, "asn": 70.0, "part": 5.0, "slp": 6.0, "ptest": 65.0, "prob": 50, "score": 64.0, "level": "Average", "date": "2026-04-01 14:10:00"},
        {"name": "Zoya Khan", "att": 72.0, "gpa": 6.2, "study": 10.0, "asn": 65.0, "part": 5.0, "slp": 5.5, "ptest": 60.0, "prob": 40, "score": 60.0, "level": "Average", "date": "2026-04-02 10:30:00"},
        {"name": "Vikram Rao", "att": 78.0, "gpa": 6.8, "study": 14.0, "asn": 72.0, "part": 6.0, "slp": 6.5, "ptest": 68.0, "prob": 60, "score": 67.0, "level": "Average", "date": "2026-04-02 16:00:00"},
        {"name": "Meera Pillai", "att": 70.0, "gpa": 6.0, "study": 11.0, "asn": 68.0, "part": 5.0, "slp": 5.0, "ptest": 62.0, "prob": 45, "score": 61.0, "level": "Average", "date": "2026-04-03 13:20:00"},
        {"name": "Aryan Joshi", "att": 74.0, "gpa": 6.4, "study": 13.0, "asn": 71.0, "part": 6.0, "slp": 6.2, "ptest": 64.0, "prob": 55, "score": 65.0, "level": "Average", "date": "2026-04-04 11:10:00"},
        {"name": "Kyra Shah", "att": 71.0, "gpa": 6.1, "study": 10.0, "asn": 66.0, "part": 5.0, "slp": 5.2, "ptest": 61.0, "prob": 42, "score": 59.0, "level": "Average", "date": "2026-04-04 15:30:00"},

        # AT RISK (5)
        {"name": "Yash Mehra", "att": 55.0, "gpa": 4.5, "study": 5.0, "asn": 50.0, "part": 3.0, "slp": 5.0, "ptest": 45.0, "prob": 20, "score": 46.0, "level": "At Risk", "date": "2026-04-01 16:50:00"},
        {"name": "Tanya Bajaj", "att": 50.0, "gpa": 4.0, "study": 4.0, "asn": 45.0, "part": 2.0, "slp": 4.5, "ptest": 40.0, "prob": 15, "score": 42.0, "level": "At Risk", "date": "2026-04-02 12:40:00"},
        {"name": "Rajesh Pal", "att": 45.0, "gpa": 3.5, "study": 3.0, "asn": 40.0, "part": 2.0, "slp": 4.0, "ptest": 35.0, "prob": 10, "score": 38.0, "level": "At Risk", "date": "2026-04-03 15:10:00"},
        {"name": "Simran Kaur", "att": 40.0, "gpa": 3.0, "study": 2.0, "asn": 35.0, "part": 1.0, "slp": 4.0, "ptest": 30.0, "prob": 5, "score": 33.0, "level": "At Risk", "date": "2026-04-04 12:50:00"},
        {"name": "Amit Trivedi", "att": 35.0, "gpa": 2.5, "study": 1.0, "asn": 30.0, "part": 1.0, "slp": 3.5, "ptest": 25.0, "prob": 2, "score": 28.0, "level": "At Risk", "date": "2026-04-04 17:00:00"},
    ]
    
    teacher_id = seeded_users["teacher"].id
    count = 0
    
    for r in seed_records:
        feats = {
            "attendance": r["att"],
            "previous_gpa": r["gpa"],
            "study_hours": r["study"],
            "assignment_completion": r["asn"],
            "participation_score": r["part"],
            "sleep_hours": r["slp"],
            "practice_test_score": r["ptest"],
            "practice_problems": r["prob"]
        }
        
        ai_res = generate_ai_analysis(feats, r["score"])
        
        # Determine risk level
        risk_level = ai_res["risk_level"]
        
        student_id = seeded_users["student"].id if r.get("student_role") == "student" else None
        
        created_at_dt = datetime.datetime.strptime(r["date"], "%Y-%m-%d %H:%M:%S")
        
        rec = PredictionRecord(
            student_name=r["name"],
            attendance=feats["attendance"],
            previous_gpa=feats["previous_gpa"],
            study_hours=feats["study_hours"],
            assignment_completion=feats["assignment_completion"],
            participation_score=feats["participation_score"],
            sleep_hours=feats["sleep_hours"],
            practice_test_score=feats["practice_test_score"],
            practice_problems=feats["practice_problems"],
            predicted_score=r["score"],
            performance_level=r["level"],
            confidence_score=78.5,  # static seed confidence score
            risk_level=risk_level,
            summary=ai_res["summary"],
            strengths=ai_res["strengths"],
            weaknesses=ai_res["weaknesses"],
            recommendations=ai_res["recommendations"],
            learning_roadmap=ai_res["learning_roadmap"],
            created_by_id=teacher_id,
            student_id=student_id,
            created_at=created_at_dt
        )
        
        db.add(rec)
        count += 1
        
    db.commit()
    return count
