# 🎓 PredictGrade: Student Performance Analytics & Prediction Portal

PredictGrade is a production-grade, modern SaaS-style web application designed to predict student exam performance, identify academic vulnerabilities, and generate personalized, week-by-week learning roadmaps.

It replaces the legacy Streamlit/Flask architecture with a robust, scalable **FastAPI** backend and a responsive, high-fidelity **React + TypeScript + Vite** dashboard.

---

## ✨ Features

- 🔮 **ML Predictions**: Forecasts exam scores (0–100%) using scaled sklearn regressors.
- 🎯 **Confidence Scores**: Calculates estimation confidence based on Z-score distance from training feature density:
  $$Confidence = R^2 \times e^{-0.15 \times z} \times 100$$
- 🚨 **Risk Assessment**: Classifies students into **High**, **Medium**, or **Low** academic risk based on predicted scores and attendance.
- 🗓️ **AI Learning Roadmap**: Generates a milestone-based, week-by-week 4-week study checklist tailored to individual habit weaknesses.
- 📊 **Dynamic Dashboard**: Responsive metrics, category breakdowns, and data correlations (Attendance vs. Grade, Study Hours vs. Grade) rendered in **Recharts**.
- 🔒 **Role-Based Access Control**: Secure JWT authentication isolating dashboard privileges between **Admin**, **Teacher**, and **Student** accounts.
- 📥 **Document Exports**: Streams formatted PDF student report cards and complete Excel prediction histories.

---

## 🗂️ Project Structure

```text
Student_Performance_Prediction/
 ├── backend/
 │    ├── Dockerfile
 │    ├── requirements.txt
 │    └── app/
 │         ├── api/            # API endpoints (auth, predict, analytics, model)
 │         ├── core/           # Config, database setup, JWT security
 │         ├── database/       # DB models, database seeder
 │         ├── schemas/        # Pydantic schemas (requests, responses)
 │         ├── services/       # Exporters (PDF/Excel), AI roadmaps
 │         └── ml/             # Regressor pipelines and inference cache
 ├── frontend/
 │    ├── Dockerfile
 │    ├── package.json
 │    ├── tailwind.config.js
 │    └── src/
 │         ├── components/     # UI elements (charts, tables, sliders)
 │         ├── context/        # Auth, theme, toast state containers
 │         ├── hooks/          # useAuth, useTheme, useToast
 │         ├── layouts/        # Dashboard layout, Auth shell
 │         ├── pages/          # Home, predict, results, analytics, insights, profile
 │         └── services/       # Axios API client wrappers
 ├── docker-compose.yml
 ├── .env.example
 └── README.md
```

---

## 🚀 Quick Start (Local Run)

Ensure you have **Python 3.10+** and **Node.js 18+** installed.

### 1. Backend Setup

```bash
# Navigate to project root
cd Student_Performance_Prediction

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Start backend locally (runs on port 8000)
python -m uvicorn backend.app.main:app --reload
```
On first start, the backend will auto-create the SQLite database, seed default accounts, and pre-train the model.

### 2. Frontend Setup

```bash
# Open a new terminal
cd Student_Performance_Prediction/frontend

# Install node dependencies
npm install

# Start Vite dev server (runs on port 3000)
npm run dev
```
Open **[http://localhost:3000](http://localhost:3000)** in your browser.

---

## 🔑 Default Credentials

- **Admin Account**: `admin@example.com` / `admin123`
- **Teacher Account**: `teacher@example.com` / `teacher123`
- **Student Account**: `student@example.com` / `student123`

---

## 🐳 Running with Docker

Orchestrate the entire platform in a single command using Docker Compose:

```bash
# Build and run containers
docker-compose up --build
```
- **Frontend Panel**: [http://localhost](http://localhost) (Served via Nginx)
- **API Swagger documentation**: [http://localhost:8000/docs](http://localhost:8000/docs) (Served via FastAPI)
