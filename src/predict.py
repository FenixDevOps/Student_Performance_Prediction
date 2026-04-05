"""
predict.py
----------
Loads the saved model and generates predictions along with performance
level labels for a given set of student features.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
MODEL_PATH = "models/model.pkl"
META_PATH  = "models/model_meta.json"

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

# ── Performance-level thresholds ─────────────────────────────────────────────
PERFORMANCE_LEVELS = [
    (85, 101, "Excellent",  "🏆"),
    (70,  85, "Good",       "✅"),
    (50,  70, "Average",    "⚠️"),
    ( 0,  50, "At Risk",    "🚨"),
]


def get_performance_level(score: float) -> tuple[str, str]:
    """
    Map a predicted exam score to a performance category.

    Returns
    -------
    (label, emoji)  e.g. ("Good", "✅")
    """
    for low, high, label, emoji in PERFORMANCE_LEVELS:
        if low <= score < high:
            return label, emoji
    return "At Risk", "🚨"


_cached_model = None

def load_model():
    """Load the saved model pipeline from disk. Cached in memory after first load."""
    global _cached_model
    if _cached_model is not None:
        return _cached_model
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model not found at '{MODEL_PATH}'. "
            "Run `python src/train_model.py` first."
        )
    _cached_model = joblib.load(MODEL_PATH)
    return _cached_model


def load_meta() -> dict:
    """Load model metadata (metrics, feature importances, etc.)."""
    if not os.path.exists(META_PATH):
        return {}
    with open(META_PATH) as f:
        return json.load(f)


def predict_single(features: dict) -> dict:
    """
    Predict exam score for a single student.

    Parameters
    ----------
    features : dict
        Keys must match FEATURE_COLS.

    Returns
    -------
    dict
        {
            "predicted_score": float,
            "performance_level": str,
            "performance_emoji": str,
            "features": dict          # input features, normalised
        }
    """
    model = load_model()

    # Build a 1-row DataFrame in the correct column order
    X = pd.DataFrame([features])[FEATURE_COLS]

    score = float(np.clip(model.predict(X)[0], 0, 100))
    level, emoji = get_performance_level(score)

    return {
        "predicted_score":   round(score, 2),
        "performance_level": level,
        "performance_emoji": emoji,
        "features":          features,
    }


def predict_batch(df: pd.DataFrame) -> pd.DataFrame:
    """
    Predict exam scores for a DataFrame of students.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain all columns in FEATURE_COLS.

    Returns
    -------
    pd.DataFrame
        Input DataFrame with appended columns:
        predicted_score, performance_level, performance_emoji.
    """
    model  = load_model()
    scores = np.clip(model.predict(df[FEATURE_COLS]), 0, 100)
    df = df.copy()
    df["predicted_score"]   = scores.round(2)
    levels_emojis           = [get_performance_level(s) for s in scores]
    df["performance_level"] = [le[0] for le in levels_emojis]
    df["performance_emoji"] = [le[1] for le in levels_emojis]
    return df


# ── Standalone smoke test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    sample = {
        "attendance":            85.0,
        "previous_gpa":          3.2,
        "study_hours":           18.0,
        "assignment_completion": 80.0,
        "participation_score":   7.0,
        "sleep_hours":           7.0,
        "practice_test_score":   72.0,
        "practice_problems":     90,
    }
    result = predict_single(sample)
    print(f"\nPredicted score : {result['predicted_score']}")
    print(f"Performance     : {result['performance_emoji']} {result['performance_level']}")
