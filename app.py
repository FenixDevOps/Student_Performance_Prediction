import os
import sys
import json
import logging
import numpy as np
import pandas as pd
import joblib

# ── LOGGING ────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

# ── PATH SETUP ────────────────────────────────────────────────────────────────
log.info("APP STARTING: Initializing paths...")
ROOT = os.path.abspath(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
log.info(f"ROOT PATH: {ROOT}")

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from src.db_manager import init_db, insert_prediction, get_summary_stats, search_records, delete_record
from src.recommendations import analyse

# ── FEATURE CONFIG ────────────────────────────────────────────────────────────
FEATURE_COLS = [
    "attendance", "previous_gpa", "study_hours", "assignment_completion",
    "participation_score", "sleep_hours", "practice_test_score", "practice_problems",
]

PERFORMANCE_LEVELS = [
    (85, 101, "Excellent", "🏆"),
    (70,  85, "Good",      "✅"),
    (50,  70, "Average",   "⚠️"),
    ( 0,  50, "At Risk",   "🚨"),
]

# ── MODEL SINGLETONS ──────────────────────────────────────────────────────────
_model = None
_model_meta = {}

def _train_model():
    """Train a Linear Regression model in-memory with synthetic data."""
    log.info("[startup] Generating synthetic training data...")
    rng = np.random.default_rng(42)
    n = 1600
    attendance            = rng.uniform(40, 100, n)
    previous_gpa          = rng.uniform(1.5, 10.0, n)
    study_hours           = rng.uniform(2, 40, n)
    assignment_completion = rng.uniform(30, 100, n)
    participation_score   = rng.uniform(1, 10, n)
    sleep_hours           = rng.uniform(4, 10, n)
    practice_test_score   = rng.uniform(20, 100, n)
    practice_problems     = rng.integers(0, 201, n).astype(float)
    sleep_penalty = -np.abs(sleep_hours - 7.5) * 1.5
    raw_score = (
        0.28 * practice_test_score
        + 0.22 * (previous_gpa / 10.0 * 100)
        + 0.18 * (study_hours / 40.0 * 100)
        + 0.10 * attendance
        + 0.10 * assignment_completion
        + 0.05 * (participation_score / 10.0 * 100)
        + 0.05 * (practice_problems / 200.0 * 100)
        + sleep_penalty + rng.normal(0, 5, n)
    )
    exam_score = np.clip(raw_score, 0, 100).round(2)
    X = pd.DataFrame({
        "attendance": attendance, "previous_gpa": previous_gpa,
        "study_hours": study_hours, "assignment_completion": assignment_completion,
        "participation_score": participation_score, "sleep_hours": sleep_hours,
        "practice_test_score": practice_test_score, "practice_problems": practice_problems,
    })[FEATURE_COLS]
    log.info("[startup] Training model...")
    pipeline = Pipeline([("scaler", StandardScaler()), ("model", LinearRegression())])
    pipeline.fit(X, exam_score)
    from sklearn.metrics import mean_squared_error, r2_score
    preds = pipeline.predict(X)
    rmse = float(np.sqrt(mean_squared_error(exam_score, preds)))
    r2   = float(r2_score(exam_score, preds))
    meta = {
        "model_name": "Linear Regression",
        "rmse": round(rmse, 4),
        "mae":  round(float(np.mean(np.abs(exam_score - preds))), 4),
        "r2":   round(r2, 4),
        "feature_cols": FEATURE_COLS,
    }
    log.info(f"[startup] Model trained ✓  R²={r2:.4f}  RMSE={rmse:.4f}")
    return pipeline, meta

def get_performance_level(score: float):
    for low, high, label, emoji in PERFORMANCE_LEVELS:
        if low <= score < high:
            return label, emoji
    return "At Risk", "🚨"

def predict_single(features: dict):
    global _model
    if _model is None:
        raise RuntimeError("Model not loaded yet. Please wait a moment and retry.")
    X = pd.DataFrame([features])[FEATURE_COLS]
    score = float(np.clip(_model.predict(X)[0], 0, 100))
    level, emoji = get_performance_level(score)
    return {"predicted_score": round(score, 2), "performance_level": level, "performance_emoji": emoji, "features": features}

# ── FLASK APP ─────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder='static', template_folder='templates')
application = app  # Gunicorn alias
CORS(app)

# ── STARTUP ───────────────────────────────────────────────────────────────────
log.info("Initializing database...")
try:
    init_db()
    log.info("Database initialized.")
except Exception as e:
    log.warning(f"DB init failed (continuing): {e}")

MODEL_FILE = os.path.join(ROOT, 'models', 'model.pkl')
META_FILE  = os.path.join(ROOT, 'models', 'model_meta.json')

log.info("Loading model...")
try:
    if os.path.exists(MODEL_FILE):
        _model = joblib.load(MODEL_FILE)
        if os.path.exists(META_FILE):
            with open(META_FILE) as f:
                _model_meta = json.load(f)
        log.info(f"Model loaded from disk ✓  R²={_model_meta.get('r2','?')}")
    else:
        log.info("No pre-trained model found — training now...")
        _model, _model_meta = _train_model()
except Exception as e:
    log.error(f"Model load/train FAILED: {e}")
    import traceback; traceback.print_exc()

# ── ROUTES ────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/ping')
def ping():
    return jsonify({"status": "ok", "model_loaded": _model is not None})

@app.route('/api/model-info', methods=['GET'])
def get_model_info():
    return jsonify(_model_meta)

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({'error': 'No JSON body received.'}), 400

        student_name = str(data.get('student_name', 'Unknown Student')).strip() or 'Unknown Student'
        features = {col: data.get(col) for col in FEATURE_COLS}
        missing = [k for k, v in features.items() if v is None]
        if missing:
            return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400

        # Type-coerce features
        features = {k: float(v) if k != 'practice_problems' else int(v) for k, v in features.items()}

        result = predict_single(features)
        score  = result['predicted_score']
        level  = result['performance_level']

        try:
            insert_prediction(student_name, features, score, level)
        except Exception as db_err:
            log.warning(f"DB save failed (result still returned): {db_err}")

        analysis = analyse(features, score)
        log.info(f"Predicted for '{student_name}': score={score}, level={level}")

        return jsonify({
            'score': score,
            'level': level,
            'emoji': result['performance_emoji'],
            'summary': analysis.summary,
            'strengths': analysis.strengths,
            'weaknesses': analysis.weaknesses,
            'recommendations': analysis.recommendations,
            'features': features
        })
    except Exception as e:
        log.error(f"Predict error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        stats = get_summary_stats()
        return jsonify(stats)
    except Exception as e:
        log.warning(f"Stats error: {e}")
        return jsonify({'total': 0, 'avg_score': 0, 'max_score': 0, 'min_score': 0,
                        'excellent': 0, 'good': 0, 'average': 0, 'at_risk': 0})

@app.route('/api/history', methods=['GET'])
def get_history():
    try:
        query = request.args.get('query', '')
        level = request.args.get('level', 'All')
        records = search_records(name_query=query, level_filter=level)
        return jsonify(records)
    except Exception as e:
        log.warning(f"History error: {e}")
        return jsonify([])

@app.route('/api/history/<record_id>', methods=['DELETE'])
def delete_history_record(record_id):
    try:
        delete_record(record_id)
        return jsonify({'success': True, 'deleted_id': record_id})
    except Exception as e:
        log.warning(f"Delete error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
