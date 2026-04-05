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
ROOT = os.path.abspath(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
log.info(f"ROOT: {ROOT}")

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from src.db_manager import (
    init_db, insert_prediction, get_analytics,
    search_records, delete_record, seed_db, clear_db
)
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
_model_meta: dict = {}

# ── TRAINING ──────────────────────────────────────────────────────────────────
def _train_model():
    log.info("Generating training data...")
    rng = np.random.default_rng(42)
    n = 1600
    att  = rng.uniform(40, 100, n);   gpa  = rng.uniform(1.5, 10.0, n)
    stud = rng.uniform(2, 40, n);     asn  = rng.uniform(30, 100, n)
    part = rng.uniform(1, 10, n);     slp  = rng.uniform(4, 10, n)
    ptest= rng.uniform(20, 100, n);   prob = rng.integers(0, 201, n).astype(float)
    raw  = (0.28*ptest + 0.22*(gpa/10*100) + 0.18*(stud/40*100)
            + 0.10*att + 0.10*asn + 0.05*(part/10*100)
            + 0.05*(prob/200*100) - np.abs(slp-7.5)*1.5 + rng.normal(0,5,n))
    y = np.clip(raw, 0, 100).round(2)
    X = pd.DataFrame({"attendance":att,"previous_gpa":gpa,"study_hours":stud,
                       "assignment_completion":asn,"participation_score":part,
                       "sleep_hours":slp,"practice_test_score":ptest,
                       "practice_problems":prob})[FEATURE_COLS]
    pipe = Pipeline([("scaler", StandardScaler()), ("model", LinearRegression())])
    pipe.fit(X, y)
    from sklearn.metrics import mean_squared_error, r2_score
    preds = pipe.predict(X)
    rmse = float(np.sqrt(mean_squared_error(y, preds)))
    r2   = float(r2_score(y, preds))
    meta = {"model_name":"Linear Regression","algorithm":"Linear Regression",
            "r2":round(r2,4),"rmse":round(rmse,4),
            "mae":round(float(np.mean(np.abs(y-preds))),4),
            "version":"v2.0","feature_cols":FEATURE_COLS}
    log.info(f"Model trained ✓  R²={r2:.4f}  RMSE={rmse:.4f}")
    return pipe, meta

def get_performance_level(score: float):
    for lo, hi, label, emoji in PERFORMANCE_LEVELS:
        if lo <= score < hi:
            return label, emoji
    return "At Risk", "🚨"

def predict_single(features: dict) -> dict:
    if _model is None:
        raise RuntimeError("Model not loaded. Server is still starting.")
    X = pd.DataFrame([features])[FEATURE_COLS]
    score = float(np.clip(_model.predict(X)[0], 0, 100))
    level, emoji = get_performance_level(score)
    return {"predicted_score": round(score, 2), "performance_level": level,
            "performance_emoji": emoji, "features": features}

# ── FLASK APP ─────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder='static', template_folder='templates')
application = app   # gunicorn alias
CORS(app)

# ── STARTUP ───────────────────────────────────────────────────────────────────
log.info("=== STARTUP ===")
try:
    init_db()  # This now handles auto-seeding
except Exception as e:
    log.warning(f"DB init warning: {e}")

MODEL_FILE = os.path.join(ROOT, 'models', 'model.pkl')
META_FILE  = os.path.join(ROOT, 'models', 'model_meta.json')
try:
    if os.path.exists(MODEL_FILE):
        _model = joblib.load(MODEL_FILE)
        if os.path.exists(META_FILE):
            with open(META_FILE) as f:
                _model_meta = json.load(f)
        _model_meta.setdefault("algorithm", _model_meta.get("model_name", "Linear Regression"))
        _model_meta.setdefault("version", "v2.0")
        log.info(f"Model loaded from disk ✓")
    else:
        _model, _model_meta = _train_model()
except Exception as e:
    log.error(f"Model load failed: {e}")

# ── ROUTES ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health')
@app.route('/api/ping')
def health():
    return jsonify({"status": "OK", "model_loaded": _model is not None})

@app.route('/api/model-info')
def model_info():
    return jsonify(_model_meta)

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json(force=True, silent=True)
        if not data: return jsonify({'error': 'No JSON body received.'}), 400

        student_name = str(data.get('student_name', 'Unknown')).strip() or 'Unknown'
        features = {col: data.get(col) for col in FEATURE_COLS}
        features = {k: float(v) if k != 'practice_problems' else int(v) for k, v in features.items()}

        result   = predict_single(features)
        score    = result['predicted_score']
        level    = result['performance_level']
        analysis = analyse(features, score)

        try:
            insert_prediction(
                student_name     = student_name,
                features         = features,
                predicted_score  = score,
                performance_level= level,
                strengths        = analysis.strengths,
                weaknesses       = analysis.weaknesses,
                recommendations  = analysis.recommendations,
                summary          = analysis.summary,
            )
        except Exception as db_err:
            log.warning(f"DB save warning: {db_err}")

        return jsonify({
            'score': score, 'level': level, 'emoji': result['performance_emoji'],
            'summary': analysis.summary, 'strengths': analysis.strengths,
            'weaknesses': analysis.weaknesses, 'recommendations': analysis.recommendations,
            'features': features,
        })
    except Exception as e:
        log.error(f"Predict error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics')
def analytics():
    try:
        return jsonify(get_analytics())
    except Exception as e:
        log.warning(f"Analytics error: {e}")
        return jsonify({'total':0,'avg_score':0,'max_score':0,'min_score':0,'recent_scores':[]})

@app.route('/api/history')
def history():
    try:
        query    = request.args.get('query', '')
        level    = request.args.get('level', 'All')
        sort_by  = request.args.get('sort', 'latest')
        records  = search_records(name_query=query, level_filter=level, sort_by=sort_by)
        return jsonify(records)
    except Exception as e:
        log.warning(f"History error: {e}")
        return jsonify([])

@app.route('/api/history/<record_id>', methods=['DELETE'])
def delete_history(record_id):
    try:
        delete_record(record_id)
        return jsonify({'success': True, 'deleted_id': record_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/seed-data', methods=['POST'])
def seed_data():
    try:
        count = seed_db(force=True)
        return jsonify({'success': True, 'count': count, 'message': f'Seeded {count} records.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear-data', methods=['DELETE'])
def clear_data():
    try:
        count = clear_db()
        return jsonify({'success': True, 'count': count, 'message': f'Removed {count} records.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
