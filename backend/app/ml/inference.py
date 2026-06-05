import os
import json
import joblib
import numpy as np
import pandas as pd
from backend.app.core.config import settings

FEATURE_COLS = [
    "attendance",
    "previous_gpa",
    "study_hours",
    "assignment_completion",
    "participation_score",
    "sleep_hours",
    "practice_test_score",
    "practice_problems",
]

PERFORMANCE_LEVELS = [
    (85, 101, "Excellent", "🏆"),
    (70,  85, "Good",      "✅"),
    (50,  70, "Average",   "⚠️"),
    ( 0,  50, "At Risk",   "🚨"),
]

_cached_model = None
_cached_meta = None

def get_performance_level(score: float) -> tuple[str, str]:
    """Map exam score to category label and emoji."""
    for low, high, label, emoji in PERFORMANCE_LEVELS:
        if low <= score < high:
            return label, emoji
    return "At Risk", "🚨"

def get_risk_level(score: float, features: dict) -> str:
    """Assess risk level: High, Medium, or Low based on score and attributes."""
    attendance = features.get("attendance", 100.0)
    study_hours = features.get("study_hours", 20.0)
    
    if score < 50 or attendance < 65:
        return "High"
    elif score < 70 or attendance < 78 or study_hours < 8.0:
        return "Medium"
    else:
        return "Low"

def load_model():
    """Load model pipeline from disk and cache it."""
    global _cached_model
    if _cached_model is not None:
        return _cached_model
        
    if not os.path.exists(settings.MODEL_PATH):
        # Auto-train if model doesn't exist
        from backend.app.ml.pipeline import train_and_save_model
        train_and_save_model()
        
    _cached_model = joblib.load(settings.MODEL_PATH)
    return _cached_model

def load_meta() -> dict:
    """Load model training metadata and cache it."""
    global _cached_meta
    if _cached_meta is not None:
        return _cached_meta
        
    if not os.path.exists(settings.META_PATH):
        from backend.app.ml.pipeline import train_and_save_model
        _cached_meta = train_and_save_model()
    else:
        with open(settings.META_PATH) as f:
            _cached_meta = json.load(f)
            
    return _cached_meta

def reset_ml_cache():
    """Clears cached model and metadata. Called after retraining."""
    global _cached_model, _cached_meta
    _cached_model = None
    _cached_meta = None

def calculate_confidence_score(features: dict, meta: dict) -> float:
    """
    Computes a prediction confidence score based on the Z-score distance
    from the training distribution, scaled by model R^2.
    """
    r2 = meta.get("r2", 0.85)
    # Ensure R^2 is sane
    if r2 <= 0:
        r2 = 0.80
        
    stats = meta.get("feature_stats", {})
    if not stats:
        return round(float(r2 * 100), 2)
        
    # Calculate Z-score distance for each feature
    z_squared_sum = 0.0
    valid_features_count = 0
    
    for col in FEATURE_COLS:
        val = features.get(col)
        if val is None:
            continue
            
        col_stats = stats.get(col, {})
        mean = col_stats.get("mean", 0.0)
        std = col_stats.get("std", 1.0)
        
        z = (val - mean) / std
        z_squared_sum += z ** 2
        valid_features_count += 1
        
    if valid_features_count == 0:
        return round(float(r2 * 100), 2)
        
    avg_z = np.sqrt(z_squared_sum / valid_features_count)
    
    # Exponential decay based on distance from training data mean
    decay = np.exp(-0.12 * avg_z)
    
    # Scale confidence score
    confidence = r2 * decay * 100
    
    # Clip between 40% and 99%
    confidence = np.clip(confidence, 40.0, 99.0)
    return round(float(confidence), 2)

def predict_single(features: dict) -> dict:
    """
    Generate student exam score prediction and associated analytics.
    """
    model = load_model()
    meta = load_meta()
    
    # Re-order features into correct columns
    input_data = {}
    for col in FEATURE_COLS:
        input_data[col] = float(features[col])
        
    df = pd.DataFrame([input_data])[FEATURE_COLS]
    
    # Predict score
    predicted_score = float(model.predict(df)[0])
    predicted_score = float(np.clip(predicted_score, 0.0, 100.0))
    
    # Map analytics categories
    level, emoji = get_performance_level(predicted_score)
    risk = get_risk_level(predicted_score, input_data)
    confidence = calculate_confidence_score(input_data, meta)
    
    return {
        "predicted_score": round(predicted_score, 2),
        "performance_level": level,
        "performance_emoji": emoji,
        "confidence_score": confidence,
        "risk_level": risk,
        "features": input_data
    }
