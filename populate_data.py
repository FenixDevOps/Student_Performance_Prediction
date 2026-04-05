import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime, timezone

# Add current directory to path so we can import our modules
ROOT = os.path.abspath(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.db_manager import insert_prediction, init_db
from src.recommendations import analyse
from app import _train_model, predict_single, FEATURE_COLS

def populate():
    print("Initializing...")
    init_db()
    
    # We need a model to predict scores
    print("Training temporary model for data population...")
    model, meta = _train_model()
    
    # Patch the global model in app.py if we were running inside it, 
    # but here we just use it locally.
    
    students = [
        # EXCELLENT (Target > 85)
        {"name": "Aarav Sharma", "att": 98, "gpa": 9.8, "study": 38, "asn": 99, "part": 10, "slp": 8.0, "ptest": 98, "prob": 190},
        {"name": "Ananya Iyer", "att": 95, "gpa": 9.5, "study": 35, "asn": 97, "part": 9, "slp": 7.5, "ptest": 95, "prob": 180},
        {"name": "Vihaan Reddy", "att": 92, "gpa": 9.2, "study": 32, "asn": 95, "part": 9, "slp": 7.0, "ptest": 92, "prob": 170},
        {"name": "Saanvi Gupta", "att": 96, "gpa": 9.6, "study": 36, "asn": 98, "part": 10, "slp": 8.5, "ptest": 96, "prob": 195},
        {"name": "Ishaan Nair", "att": 94, "gpa": 9.4, "study": 34, "asn": 96, "part": 9, "slp": 7.8, "ptest": 94, "prob": 185},
        
        # GOOD (Target 70-85)
        {"name": "Aditya Verma", "att": 85, "gpa": 8.0, "study": 25, "asn": 85, "part": 8, "slp": 7.0, "ptest": 80, "prob": 120},
        {"name": "Diya Malhotra", "att": 82, "gpa": 7.8, "study": 22, "asn": 82, "part": 7, "slp": 6.5, "ptest": 78, "prob": 110},
        {"name": "Kavya Singh", "att": 88, "gpa": 8.2, "study": 28, "asn": 88, "part": 8, "slp": 7.2, "ptest": 82, "prob": 130},
        {"name": "Rohan Joshi", "att": 80, "gpa": 7.5, "study": 20, "asn": 80, "part": 7, "slp": 6.0, "ptest": 75, "prob": 100},
        {"name": "Kyra Kapoor", "att": 84, "gpa": 7.9, "study": 24, "asn": 84, "part": 8, "slp": 6.8, "ptest": 79, "prob": 115},
        
        # AVERAGE (Target 50-70)
        {"name": "Arjun Das", "att": 70, "gpa": 6.0, "study": 12, "asn": 65, "part": 5, "slp": 6.0, "ptest": 60, "prob": 60},
        {"name": "Meera Pillai", "att": 68, "gpa": 5.8, "study": 10, "asn": 62, "part": 5, "slp": 5.5, "ptest": 58, "prob": 55},
        {"name": "Siddharth Rao", "att": 72, "gpa": 6.2, "study": 14, "asn": 68, "part": 6, "slp": 6.2, "ptest": 62, "prob": 70},
        {"name": "Zara Khan", "att": 65, "gpa": 5.5, "study": 8, "asn": 60, "part": 4, "slp": 5.0, "ptest": 55, "prob": 45},
        {"name": "Kabir Bose", "att": 74, "gpa": 6.4, "study": 16, "asn": 70, "part": 6, "slp": 6.5, "ptest": 64, "prob": 80},
        
        # AT RISK (Target < 50)
        {"name": "Aryan Saxena", "att": 45, "gpa": 3.0, "study": 4, "asn": 40, "part": 2, "slp": 4.5, "ptest": 35, "prob": 15},
        {"name": "Tanya Bajaj", "att": 40, "gpa": 2.5, "study": 2, "asn": 35, "part": 2, "slp": 4.0, "ptest": 30, "prob": 10},
        {"name": "Yash Mehra", "att": 35, "gpa": 2.0, "study": 1, "asn": 30, "part": 1, "slp": 4.0, "ptest": 25, "prob": 5},
        {"name": "Sanya Goel", "att": 48, "gpa": 3.2, "study": 5, "asn": 45, "part": 3, "slp": 5.0, "ptest": 40, "prob": 20},
        {"name": "Reyansh Jain", "att": 30, "gpa": 1.5, "study": 0.5, "asn": 25, "part": 1, "slp": 3.5, "ptest": 20, "prob": 0},
    ]

    print(f"Starting population of {len(students)} records...")

    for s in students:
        features = {
            "attendance": s["att"],
            "previous_gpa": s["gpa"],
            "study_hours": s["study"],
            "assignment_completion": s["asn"],
            "participation_score": s["part"],
            "sleep_hours": s["slp"],
            "practice_test_score": s["ptest"],
            "practice_problems": s["prob"]
        }
        
        # Predict using the trained pipeline
        X = pd.DataFrame([features])[FEATURE_COLS]
        score = float(np.clip(model.predict(X)[0], 0, 100))
        
        # Performance Level Logic (sync with app.py)
        if score >= 85: level, emoji = "Excellent", "🏆"
        elif score >= 70: level, emoji = "Good", "✅"
        elif score >= 50: level, emoji = "Average", "⚠️"
        else: level, emoji = "At Risk", "🚨"
        
        analysis = analyse(features, score)
        
        insert_prediction(
            student_name=s["name"],
            features=features,
            predicted_score=round(score, 2),
            performance_level=level,
            strengths=analysis.strengths,
            weaknesses=analysis.weaknesses,
            recommendations=analysis.recommendations,
            summary=analysis.summary
        )
        print(f"Added: {s['name']} -> {score:.2f} ({level})")

    print("\nData population complete! 🚀")

if __name__ == "__main__":
    populate()
