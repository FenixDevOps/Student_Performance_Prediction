from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="student", nullable=False)  # "admin", "teacher", "student"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    predictions_created = relationship(
        "PredictionRecord", 
        back_populates="created_by", 
        foreign_keys="PredictionRecord.created_by_id"
    )
    student_predictions = relationship(
        "PredictionRecord", 
        back_populates="student", 
        foreign_keys="PredictionRecord.student_id"
    )

class PredictionRecord(Base):
    __tablename__ = "prediction_records"

    id = Column(Integer, primary_key=True, index=True)
    student_name = Column(String, nullable=False)
    
    # Input Features
    attendance = Column(Float, nullable=False)
    previous_gpa = Column(Float, nullable=False)
    study_hours = Column(Float, nullable=False)
    assignment_completion = Column(Float, nullable=False)
    participation_score = Column(Float, nullable=False)
    sleep_hours = Column(Float, nullable=False)
    practice_test_score = Column(Float, nullable=False)
    practice_problems = Column(Integer, nullable=False)
    
    # Outputs / Results
    predicted_score = Column(Float, nullable=False)
    performance_level = Column(String, nullable=False)  # "Excellent", "Good", "Average", "At Risk"
    confidence_score = Column(Float, nullable=False)    # 0.0 to 100.0
    risk_level = Column(String, nullable=False)          # "Low", "Medium", "High"
    
    # AI recommendations and summary details
    summary = Column(String, nullable=True)
    strengths = Column(JSON, nullable=True)              # List[str]
    weaknesses = Column(JSON, nullable=True)             # List[str]
    recommendations = Column(JSON, nullable=True)        # List[str]
    learning_roadmap = Column(JSON, nullable=True)       # List[dict]
    
    # Auditing / Tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    created_by = relationship(
        "User", 
        back_populates="predictions_created", 
        foreign_keys=[created_by_id]
    )
    student = relationship(
        "User", 
        back_populates="student_predictions", 
        foreign_keys=[student_id]
    )
