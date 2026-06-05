# 🎓 PredictGrade: Student Performance Analytics & Prediction Portal

PredictGrade is a production-grade, high-fidelity SaaS-style web application designed to forecast student exam performance, isolate study habits weaknesses, and deploy interactive gamified study plans. 

The application utilizes a robust **FastAPI** REST backend paired with a modern, responsive **React + TypeScript + Vite + Tailwind CSS** dashboard.

---

## 🌟 Core Modules

### 🎒 1. Gamification & Study Engagement (For Students)
* **Interactive Kanban Checklist**: Replaces static recommendations with a weekly study milestone list (Weeks 1-4). Checkmark states sync dynamically.
* **XP & Streak Metrics**: Awards `10 XP` per completed task, and a `50 XP` bonus for completing an entire week. Tracks daily streaks with flame indicators.
* **AI Study Assistant**: A floating chat widget enabling students to query study tips, Pomodoro setup instructions, or personalized advice regarding their strengths/weaknesses.

### 🍎 2. Academic Risk Alerts & Communication (For Teachers)
* **Automated Risk Notifications**: Instantly creates a system alert if a student's predicted exam grade falls into the "At Risk" (High Risk) category.
* **Bell Dropdown Alerts**: Displays unresolved risk alerts globally in the header.
* **Parent PDF Dispatcher**: Features a quick-action email dispatch modal that sends the student evaluation PDF report card directly to parents/advisors and resolves the alert.

### ⚙️ 3. ML Pipeline Analytics & Seeding (For Admins)
* **Algorithm Selector**: Switch the active prediction model dynamically on the fly between **Linear Regression**, **Random Forest**, **Gradient Boosting**, **MLP Neural Network**, and **Ridge Regression**.
* **Model Retraining Controls**: Synchronously retrains all regressors on live database records and logs results.
* **Seeder & Data Utilities**: Offers buttons to wipe evaluation history or reset db seeder data.
* **Retraining Audit History Logs**: Keeps an active table log of past retraining runs.

---

## 🗂️ Project Structure

```text
Student_Performance_Prediction/
 ├── backend/
 │    ├── Dockerfile
 │    ├── requirements.txt
 │    └── app/
 │         ├── api/            # API routers (auth, predict, analytics, model, alerts)
 │         ├── core/           # Security middlewares, database setup, environment settings
 │         ├── database/       # SQLAlchemy models, SQLite/PostgreSQL seeder
 │         ├── schemas/        # Request/Response validation schemas (Pydantic)
 │         ├── services/       # Report builders (PDF & Excel generators), AI analytics engine
 │         └── ml/             # Regressor candidates, pipeline trainer, dynamic inference
 ├── frontend/
 │    ├── Dockerfile
 │    ├── package.json
 │    ├── tailwind.config.js
 │    └── src/
 │         ├── components/     # Reusable layout fragments, slider fields
 │         ├── context/        # React state contexts (Auth, Theme, Toast)
 │         ├── hooks/          # Custom hooks wrappers (useAuth, useTheme, useToast)
 │         ├── layouts/        # App route layout panels (Sidebar, Headers, Bell Alerts)
 │         ├── pages/          # Home Dashboard, Predict, Analytics, ModelInsights, Profile
 │         └── services/       # Axios client connection instances (api.ts)
 ├── docker-compose.yml
 ├──render.yaml
 ├──student_evaluations_100.csv  # 100 sample records for bulk prediction testing
 └── README.md
```

---

## 🔑 Default Credentials

The seeder initializes default accounts for testing the role-based views:

| Role | Username | Password | Access Privileges |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@example.com` | `admin123` | Active ML controls, pipeline retraining, database seeder, teacher features |
| **Teacher** | `teacher@example.com` | `teacher123` | Manual & bulk predictions, analytics graphs, alerts dropdown, parent dispatch |
| **Student** | `student@example.com` | `student123` | Gamified stats (Level/XP/Streaks), Kanban checklist, AI study chat companion |

---

## 🚀 Local Quick Start

Ensure you have **Python 3.10+** and **Node.js 18+** installed.

### 1. Run Backend REST API
```bash
cd Student_Performance_Prediction

# Activate virtual environment (Windows)
.\venv\Scripts\activate
# Activate virtual environment (macOS/Linux)
source venv/bin/activate

# Install requirements
pip install -r backend/requirements.txt

# Start local server (runs on port 8000)
python -m uvicorn backend.app.main:app --reload
```
> [!NOTE]
> During startup, FastAPI will automatically generate database tables, apply schema migrations (adding gamification fields if missing), and cache model regressors.

### 2. Run React Frontend
```bash
cd Student_Performance_Prediction/frontend

# Install dependencies
npm install

# Start Vite dev server (runs on port 3000)
npm run dev
```
Open **[http://localhost:3000](http://localhost:3000)** to browse the interface.

---

## 🐳 Running with Docker

Orchestrate the entire platform in a single command using Docker Compose:

```bash
# In the project root, run:
docker-compose up --build
```
* **Frontend Panel**: [http://localhost](http://localhost) (Served via Nginx)
* **API Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs) (Served via FastAPI)
