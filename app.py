import os
import sys

# ── LOGGING & ERROR CATCHING (TOP OF FILE) ──────────────────────────
try:
    print(">>> APP STARTING: INITIALIZING PATHS...")
    # Now that we are in root, ROOT is just the current directory
    ROOT = os.path.abspath(os.path.dirname(__file__))
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    print(f">>> ROOT PATH SET TO: {ROOT}")
except Exception as e:
    print(f">>> PATH INITIALIZATION FAILED: {str(e)}")

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

# --- DATABASE & ML LOGIC ---
from src.db_manager import init_db, insert_prediction, get_summary_stats, search_records
from src.predict import load_meta, predict_single, FEATURE_COLS, MODEL_PATH
from src.train_model import train
from src.recommendations import analyse

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
application = app  # For Gunicorn alias
CORS(app)

# Global metadata and Initialization
model_meta = {}
try:
    print("Pre-initialization: Checking database...")
    init_db()
    print("Database initialized successfully.")

    model_meta = load_meta()
    if not model_meta and not os.path.exists(MODEL_PATH):
        print("Model not found. Training model locally...")
        model_meta = train()
    print("Model loaded/trained successfully.")
except Exception as e:
    print("-" * 30)
    print("CRITICAL STARTUP ERROR:")
    print(str(e))
    import traceback
    traceback.print_exc()
    print("-" * 30)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        student_name = data.get('student_name', 'Unknown Student')
        features = {col: data.get(col) for col in FEATURE_COLS}
        
        # Validate features
        if any(v is None for v in features.values()):
            return jsonify({'error': 'Missing required features'}), 400
            
        result = predict_single(features)
        score = result['predicted_score']
        level = result['performance_level']
        
        # Save to database
        insert_prediction(student_name, features, score, level)
        
        # Get recommendations
        analysis = analyse(features, score)
        
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
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        stats = get_summary_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    try:
        query = request.args.get('query', '')
        level = request.args.get('level', 'All')
        records = search_records(name_query=query, level_filter=level)
        return jsonify(records)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/model-info', methods=['GET'])
def get_model_info():
    return jsonify(model_meta)

if __name__ == '__main__':
    # Ensure directories exist
    os.makedirs(os.path.join(app.root_path, 'static', 'css'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'static', 'js'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'templates'), exist_ok=True)
    
    app.run(debug=True, port=5000)
