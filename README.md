# 🎓 Student Performance Analytics & Prediction System

An end-to-end machine learning application that predicts student exam performance,
identifies academic strengths and weaknesses, and provides personalised improvement
recommendations — all through an interactive Streamlit dashboard.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔮 **AI Prediction** | Predicts exam score (0–100) from 8 academic features |
| 🏷️ **Performance Levels** | Excellent / Good / Average / At Risk |
| 📊 **Analytics Dashboard** | Score distribution, feature importance, scatter plots, heatmap |
| 🚀 **Recommendations** | Up to 10 personalised improvement tips |
| 🕸️ **Radar Chart** | Visual feature profile for the student |
| 📁 **Student History** | SQLite-backed database with search, filter, trend analysis |
| 🤖 **Best Model Selection** | Trains 3 models, auto-selects the best by RMSE |

---

## 🗂️ Project Structure

```
student-performance-analytics/
├── app/
│   └── streamlit_app.py        # Main Streamlit application (3 pages)
├── src/
│   ├── data_generator.py       # Synthetic dataset generation (1600 rows)
│   ├── train_model.py          # Model training pipeline
│   ├── predict.py              # Prediction helpers
│   ├── recommendations.py      # Personalised recommendation engine
│   └── db_manager.py           # SQLite student history database
├── data/
│   └── dataset.csv             # Generated on first run
├── models/
│   ├── model.pkl               # Saved best model (joblib)
│   └── model_meta.json         # Metrics & feature importances
├── database/
│   └── student_history.db      # SQLite database (auto-created)
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### 1 — Clone / download the project

```bash
git clone https://github.com/yourname/student-performance-analytics.git
cd student-performance-analytics
```

### 2 — Create a virtual environment (recommended)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### 4 — Launch the app

```bash
streamlit run app/streamlit_app.py
```

The app will open automatically at **http://localhost:8501**.

> **First launch**: The app automatically generates the dataset and trains the model —
> this takes ~30 seconds and only happens once.

---

## 🧠 Models Trained

| Model | Notes |
|---|---|
| Linear Regression | Baseline; fast, interpretable |
| Random Forest | 200 trees, good for non-linear patterns |
| Gradient Boosting | 200 estimators, usually best accuracy |

The best model is selected by **lowest RMSE** on a held-out 20 % test set and saved
to `models/model.pkl`.

---

## 📋 Input Features

| Feature | Range | Description |
|---|---|---|
| Attendance | 0–100 % | Percentage of classes attended |
| Previous GPA | 0.0–4.0 | GPA from last semester |
| Study Hours | 0–40 hrs/wk | Average weekly study time |
| Assignment Completion | 0–100 % | Assignments submitted on time |
| Class Participation | 1–10 | Self-assessed participation level |
| Sleep Hours | 3–12 hrs/day | Average nightly sleep |
| Practice Test Score | 0–100 | Average recent practice exam score |
| Practice Problems | 0–500 | Total problems completed |

**Target:** `exam_score` (0–100)

---

## 🏷️ Performance Levels

| Level | Score Range | Colour |
|---|---|---|
| 🏆 Excellent | 85–100 | Green |
| ✅ Good | 70–84 | Blue |
| ⚠️ Average | 50–69 | Amber |
| 🚨 At Risk | < 50 | Red |

---

## 🛠️ Run Individual Scripts

```bash
# Generate dataset only
python src/data_generator.py

# Train models only
python src/train_model.py

# Run a single prediction (smoke test)
python src/predict.py

# Test recommendation engine
python src/recommendations.py

# Test database
python src/db_manager.py
```

---

## 📦 Tech Stack

- **Python 3.10+**
- **Streamlit** — web dashboard
- **scikit-learn** — ML models
- **pandas / NumPy** — data processing
- **matplotlib / seaborn** — visualisations
- **joblib** — model persistence
- **SQLite** — student history database

---

## 📄 License

MIT — free to use, modify, and distribute.
