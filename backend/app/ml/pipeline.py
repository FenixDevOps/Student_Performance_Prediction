import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.database.models import ModelRetrainHistory

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
TARGET_COL = "exam_score"

def generate_synthetic_data(n_samples: int = 1600, random_state: int = 42) -> pd.DataFrame:
    """Generate realistic synthetic student dataset."""
    rng = np.random.default_rng(random_state)
    
    attendance = rng.uniform(40, 100, n_samples)
    previous_gpa = rng.uniform(1.5, 10.0, n_samples)
    study_hours = rng.uniform(2, 40, n_samples)
    assignment_completion = rng.uniform(30, 100, n_samples)
    participation_score = rng.uniform(1, 10, n_samples)
    sleep_hours = rng.uniform(4, 10, n_samples)
    practice_test_score = rng.uniform(20, 100, n_samples)
    practice_problems = rng.integers(0, 201, n_samples).astype(float)
    
    sleep_penalty = -np.abs(sleep_hours - 7.5) * 1.5
    
    raw_score = (
        0.28 * practice_test_score
        + 0.22 * (previous_gpa / 10.0 * 100)
        + 0.18 * (study_hours / 40.0 * 100)
        + 0.10 * attendance
        + 0.10 * assignment_completion
        + 0.05 * (participation_score / 10.0 * 100)
        + 0.05 * (practice_problems / 200.0 * 100)
        + sleep_penalty
        + rng.normal(0, 5, n_samples)
    )
    
    exam_score = np.clip(raw_score, 0, 100).round(2)
    
    df = pd.DataFrame({
        "attendance": attendance.round(2),
        "previous_gpa": previous_gpa.round(2),
        "study_hours": study_hours.round(2),
        "assignment_completion": assignment_completion.round(2),
        "participation_score": participation_score.round(2),
        "sleep_hours": sleep_hours.round(2),
        "practice_test_score": practice_test_score.round(2),
        "practice_problems": practice_problems.astype(int),
        "exam_score": exam_score,
    })
    
    return df

def train_and_save_model() -> dict:
    """Runs full pipeline training, compares multiple models, and persists them."""
    df = generate_synthetic_data()
    X = df[FEATURE_COLS]
    y = df[TARGET_COL]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Store feature stats for distance-based confidence calculations
    feature_stats = {}
    for col in FEATURE_COLS:
        feature_stats[col] = {
            "mean": float(X_train[col].mean()),
            "std": float(X_train[col].std()) if X_train[col].std() > 0 else 1.0
        }
    
    candidates = {
        "Linear Regression": Pipeline([
            ("scaler", StandardScaler()),
            ("model", LinearRegression()),
        ]),
        "Random Forest": Pipeline([
            ("scaler", StandardScaler()),
            ("model", RandomForestRegressor(
                n_estimators=200,
                max_depth=10,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1,
            )),
        ]),
        "Gradient Boosting": Pipeline([
            ("scaler", StandardScaler()),
            ("model", GradientBoostingRegressor(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.08,
                subsample=0.85,
                random_state=42,
            )),
        ]),
        "Neural Network": Pipeline([
            ("scaler", StandardScaler()),
            ("model", MLPRegressor(
                hidden_layer_sizes=(64, 32),
                max_iter=500,
                random_state=42,
            )),
        ]),
        "Ridge Regression": Pipeline([
            ("scaler", StandardScaler()),
            ("model", Ridge(alpha=1.0)),
        ]),
    }
    
    results = []
    for name, pipeline in candidates.items():
        pipeline.fit(X_train, y_train)
        preds = pipeline.predict(X_test)
        rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
        mae = float(mean_absolute_error(y_test, preds))
        r2 = float(r2_score(y_test, preds))
        
        results.append({
            "name": name,
            "rmse": rmse,
            "mae": mae,
            "r2": r2,
            "pipeline": pipeline
        })
        
        # Save each model file separately
        filename = f"model_{name.lower().replace(' ', '_')}.pkl"
        path = os.path.join(settings.MODEL_DIR, filename)
        joblib.dump(pipeline, path)
        
    # Log retraining runs to database
    db = SessionLocal()
    try:
        for r in results:
            log_entry = ModelRetrainHistory(
                algorithm_name=r["name"],
                rmse=r["rmse"],
                mae=r["mae"],
                r2=r["r2"],
                samples_count=len(df)
            )
            db.add(log_entry)
        db.commit()
    except Exception as db_err:
        print(f"Failed to log retraining history: {str(db_err)}")
        db.rollback()
    finally:
        db.close()
    
    # Select best model by lowest RMSE
    best = min(results, key=lambda r: r["rmse"])
    best_pipeline = best["pipeline"]
    
    # Calculate feature importances
    inner_model = best_pipeline.named_steps["model"]
    if hasattr(inner_model, "feature_importances_"):
        importances = dict(zip(FEATURE_COLS, inner_model.feature_importances_.tolist()))
    elif hasattr(inner_model, "coef_"):
        coefs = np.abs(inner_model.coef_)
        importances = dict(zip(FEATURE_COLS, (coefs / coefs.sum()).tolist()))
    else:
        importances = {col: 1.0 / len(FEATURE_COLS) for col in FEATURE_COLS}
        
    # Save the selected pipeline as the default active model
    joblib.dump(best_pipeline, settings.MODEL_PATH)
    
    # Save training meta details
    meta = {
        "model_name": best["name"],
        "rmse": round(best["rmse"], 4),
        "mae": round(best["mae"], 4),
        "r2": round(best["r2"], 4),
        "feature_cols": FEATURE_COLS,
        "feature_importances": importances,
        "feature_stats": feature_stats,
        "all_results": [
            {
                "name": r["name"],
                "rmse": round(r["rmse"], 4),
                "mae": round(r["mae"], 4),
                "r2": round(r["r2"], 4)
            } for r in results
        ],
        "trained_at": pd.Timestamp.now().isoformat()
    }
    
    with open(settings.META_PATH, "w") as f:
        json.dump(meta, f, indent=2)
        
    return meta

