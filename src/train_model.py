"""
train_model.py
--------------
Trains three regression models on the student performance dataset,
evaluates each one, selects the best by RMSE, and saves it with joblib.

Models trained:
  1. Linear Regression
  2. Random Forest Regressor
  3. Gradient Boosting Regressor

Evaluation metrics:
  - RMSE  (root mean squared error)
  - MAE   (mean absolute error)
  - R²    (coefficient of determination)
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# Allow running from project root or src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.data_generator import save_dataset

# ── Constants ─────────────────────────────────────────────────────────────────
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
DATA_PATH  = "data/dataset.csv"
MODEL_PATH = "models/model.pkl"
META_PATH  = "models/model_meta.json"


# ── Helper: evaluate a fitted model ──────────────────────────────────────────
def evaluate(model, X_test, y_test, name: str) -> dict:
    """Return a dict of evaluation metrics for a fitted model."""
    preds = model.predict(X_test)
    rmse  = np.sqrt(mean_squared_error(y_test, preds))
    mae   = mean_absolute_error(y_test, preds)
    r2    = r2_score(y_test, preds)
    print(f"  [{name}]  RMSE={rmse:.3f}  MAE={mae:.3f}  R²={r2:.4f}")
    return {"name": name, "rmse": rmse, "mae": mae, "r2": r2, "model": model}


# ── Main training pipeline ────────────────────────────────────────────────────
def train(data_path: str = DATA_PATH,
          model_path: str = MODEL_PATH) -> dict:
    """
    Full training pipeline.

    1. Load (or generate) dataset.
    2. Split into train / test sets (80/20).
    3. Train three models.
    4. Select the best model by RMSE.
    5. Save the best model + metadata.

    Returns
    -------
    dict
        Metadata about the selected best model.
    """
    # ── 1. Load data ──────────────────────────────────────────────────────────
    if not os.path.exists(data_path):
        print("[train_model] Dataset not found — generating…")
        save_dataset(data_path)

    df = pd.read_csv(data_path)
    print(f"[train_model] Loaded {len(df)} rows from {data_path}")

    X = df[FEATURE_COLS]
    y = df[TARGET_COL]

    # ── 2. Train / test split ─────────────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # ── 3. Define candidate models ────────────────────────────────────────────
    candidates = {
        "Linear Regression": Pipeline([
            ("scaler", StandardScaler()),
            ("model",  LinearRegression()),
        ]),
        "Random Forest": Pipeline([
            ("scaler", StandardScaler()),
            ("model",  RandomForestRegressor(
                n_estimators=200,
                max_depth=10,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1,
            )),
        ]),
        "Gradient Boosting": Pipeline([
            ("scaler", StandardScaler()),
            ("model",  GradientBoostingRegressor(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.08,
                subsample=0.85,
                random_state=42,
            )),
        ]),
    }

    # ── 4. Train and evaluate ─────────────────────────────────────────────────
    print("\n[train_model] Training models…")
    results = []
    for name, pipeline in candidates.items():
        pipeline.fit(X_train, y_train)
        metrics = evaluate(pipeline, X_test, y_test, name)
        results.append(metrics)

    # ── 5. Select best by RMSE (lower is better) ──────────────────────────────
    best = min(results, key=lambda r: r["rmse"])
    print(f"\n[train_model] ✓ Best model: {best['name']}  (RMSE={best['rmse']:.3f})")

    # ── 6. Extract feature importances ───────────────────────────────────────
    inner_model = best["model"].named_steps["model"]
    if hasattr(inner_model, "feature_importances_"):
        importances = dict(zip(FEATURE_COLS, inner_model.feature_importances_.tolist()))
    else:
        # Linear regression → use absolute coefficients as proxy
        coefs = np.abs(inner_model.coef_)
        importances = dict(zip(FEATURE_COLS, (coefs / coefs.sum()).tolist()))

    # ── 7. Save model + metadata ──────────────────────────────────────────────
    os.makedirs(os.path.dirname(model_path), exist_ok=True)

    joblib.dump(best["model"], model_path)
    print(f"[train_model] Model saved → {model_path}")

    meta = {
        "model_name":          best["name"],
        "rmse":                round(best["rmse"], 4),
        "mae":                 round(best["mae"],  4),
        "r2":                  round(best["r2"],   4),
        "feature_cols":        FEATURE_COLS,
        "feature_importances": importances,
        "all_results": [
            {"name": r["name"], "rmse": round(r["rmse"], 4),
             "mae": round(r["mae"], 4), "r2": round(r["r2"], 4)}
            for r in results
        ],
    }
    with open(META_PATH, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"[train_model] Metadata saved → {META_PATH}")

    return meta


# ── Standalone execution ──────────────────────────────────────────────────────
if __name__ == "__main__":
    train()
