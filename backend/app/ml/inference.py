import os
import json
import joblib
import numpy as np
import pandas as pd
from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.database.models import ModelSettings

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

def get_active_model_path_and_name() -> tuple[str, str]:
    db = SessionLocal()
    try:
        setting = db.query(ModelSettings).first()
        if setting:
            algorithm = setting.active_algorithm
            filename = f"model_{algorithm.lower().replace(' ', '_')}.pkl"
            path = os.path.join(settings.MODEL_DIR, filename)
            if os.path.exists(path):
                return path, algorithm
    except Exception as e:
        print(f"Failed to query ModelSettings: {str(e)}")
    finally:
        db.close()
    return settings.MODEL_PATH, "Best Model"

def get_feature_importances(pipeline) -> dict:
    inner_model = pipeline.named_steps["model"]
    if hasattr(inner_model, "feature_importances_"):
        return dict(zip(FEATURE_COLS, inner_model.feature_importances_.tolist()))
    elif hasattr(inner_model, "coef_"):
        coefs = np.abs(inner_model.coef_)
        return dict(zip(FEATURE_COLS, (coefs / coefs.sum()).tolist()))
    else:
        return {col: 1.0 / len(FEATURE_COLS) for col in FEATURE_COLS}

def load_model():
    """Load active model pipeline from disk and cache it."""
    global _cached_model
    if _cached_model is not None:
        return _cached_model
        
    path, name = get_active_model_path_and_name()
    if not os.path.exists(path):
        # Auto-train if model doesn't exist
        from backend.app.ml.pipeline import train_and_save_model
        train_and_save_model()
        
    _cached_model = joblib.load(path)
    return _cached_model

def load_meta() -> dict:
    """Load model training metadata and cache it, adjusting for active algorithm."""
    global _cached_meta
    if _cached_meta is not None:
        return _cached_meta
        
    if not os.path.exists(settings.META_PATH):
        from backend.app.ml.pipeline import train_and_save_model
        base_meta = train_and_save_model()
    else:
        with open(settings.META_PATH) as f:
            base_meta = json.load(f)
            
    # Adjust metadata for the active algorithm
    path, active_name = get_active_model_path_and_name()
    
    # Find metrics for active name in all_results
    active_result = None
    for res in base_meta.get("all_results", []):
        if res["name"] == active_name:
            active_result = res
            break
            
    if active_result:
        base_meta["model_name"] = active_result["name"]
        base_meta["rmse"] = active_result["rmse"]
        base_meta["mae"] = active_result["mae"]
        base_meta["r2"] = active_result["r2"]
        
        # Load model to get its feature importances
        try:
            model = load_model()
            base_meta["feature_importances"] = get_feature_importances(model)
        except Exception:
            pass
            
    _cached_meta = base_meta
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
