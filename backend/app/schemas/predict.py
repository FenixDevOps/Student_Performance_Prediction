from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class StudentFeatureInput(BaseModel):
    student_name: str = Field(..., min_length=2, max_length=100, description="Name of the student")
    attendance: float = Field(..., ge=0.0, le=100.0, description="Attendance rate in percentage")
    previous_gpa: float = Field(..., ge=0.0, le=10.0, description="Previous GPA (out of 10.0)")
    study_hours: float = Field(..., ge=0.0, le=168.0, description="Weekly study hours")
    assignment_completion: float = Field(..., ge=0.0, le=100.0, description="Assignment completion rate in percentage")
    participation_score: float = Field(..., ge=0.0, le=10.0, description="Class participation score (out of 10.0)")
    sleep_hours: float = Field(..., ge=0.0, le=24.0, description="Daily sleep hours")
    practice_test_score: float = Field(..., ge=0.0, le=100.0, description="Practice test score in percentage")
    practice_problems: int = Field(..., ge=0, le=1000, description="Number of practice problems solved")

class RoadmapWeek(BaseModel):
    week: int
    title: str
    focus: str
    tasks: List[str]

class PredictionResultResponse(BaseModel):
    id: int
    student_name: str
    attendance: float
    previous_gpa: float
    study_hours: float
    assignment_completion: float
    participation_score: float
    sleep_hours: float
    practice_test_score: float
    practice_problems: int
    
    predicted_score: float
    performance_level: str
    confidence_score: float
    risk_level: str
    
    summary: Optional[str] = None
    strengths: List[str] = []
    weaknesses: List[str] = []
    recommendations: List[str] = []
    learning_roadmap: List[RoadmapWeek] = []
    
    created_at: datetime
    created_by_id: Optional[int] = None
    student_id: Optional[int] = None

    class Config:
        from_attributes = True
