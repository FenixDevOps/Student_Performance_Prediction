# Deployment Guide - PredictGrade Portal

PredictGrade is designed to run in containerized environments (Docker) and can scale from a local SQLite database to a production-ready cloud database like PostgreSQL with zero code changes.

---

## 1. Local Containerized Run

To spin up the entire application locally using Docker:

```bash
# In the project root, run:
docker-compose up --build
```
This builds two containers:
1. `student-prediction-backend` hosting the FastAPI REST server (port 8000).
2. `student-prediction-frontend` hosting the compiled React static files served via Nginx (port 80).

**Persistent Volumes**:
- `backend-db-volume` stores the SQLite database file (`student_performance.db`).
- `backend-model-volume` caches the serialized joblib model pipeline and metadata JSON.

---

## 2. Production Scaling: SQLite to PostgreSQL

To switch from SQLite to PostgreSQL in production:
1. Spin up a PostgreSQL cluster (e.g. on AWS RDS, Supabase, or Render PostgreSQL).
2. Override the `DATABASE_URL` environment variable on the backend container:

```env
DATABASE_URL=postgresql://db_user:db_password@db_host:5432/db_name
```
FastAPI will automatically detect the driver and instantiate the database tables on the PostgreSQL cluster during startup.

---

## 3. Deploying to Render (Free Cloud Tier)

To deploy both components to Render:

### A. Database (PostgreSQL)
1. In Render Dashboard, click **New > PostgreSQL**.
2. Copy the **Internal Database URL** for other services to connect.

### B. Backend Web Service
1. Click **New > Web Service**.
2. Connect your GitHub repository.
3. Configure the settings:
   - **Runtime**: `Docker`
   - **Docker Context**: `.`
   - **Dockerfile Path**: `backend/Dockerfile`
4. Add the following **Environment Variables**:
   - `DATABASE_URL`: *Your Render PostgreSQL Database URL*
   - `SECRET_KEY`: *A secure random JWT signing key*
   - `PYTHONPATH`: `/workspace`

### C. Frontend Web Service
1. Click **New > Web Service** (or Static Site if built separately).
2. Configure settings:
   - **Runtime**: `Docker`
   - **Docker Context**: `.`
   - **Dockerfile Path**: `frontend/Dockerfile`
3. Link the frontend to the backend service. Render's Nginx proxy inside `frontend/nginx.conf` routes `/api` traffic directly to `http://backend:8000` inside Render's private network.

---

## 4. Production Security Hardening

Before deploying to live user cohorts:
- [ ] Change `SECRET_KEY` in the environment variables to a random 64-character hex string:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- [ ] Ensure the frontend Nginx is configured to enforce SSL (HTTPS) redirections.
- [ ] Restrict CORS origins on `backend/app/main.py` to specify your official domain rather than allowing all (`*`).
