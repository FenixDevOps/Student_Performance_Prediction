# Deployment Guide - Student Performance Analytics

Follow these steps to deploy your application to the cloud using **Render**.

## 1. Prepare Your Repository
Ensure your project is on GitHub. If not, initialize a git repository and push it:
```bash
git init
git add .
git commit -m "Initial commit for deployment"
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

## 2. Deploy to Render
1.  **Sign up/Log in**: Go to [Render](https://render.com/) and connect your GitHub account.
2.  **Create a New Web Service**: Click **New +** and select **Web Service**.
3.  **Choose Repository**: Select your `Student_Performance_Prediction` repository.
4.  **Configure Settings**:
    *   **Name**: `student-performance-analytics` (or any name you like)
    *   **Runtime**: `Python 3`
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `gunicorn --chdir app app:app`
5.  **Environment Variables**:
    *   Click **Advanced** -> **Add Environment Variable**.
    *   Add `PYTHON_VERSION` = `3.10` (or your local version).
6.  **Persistent Disk (Crucial for SQLite)**:
    *   Scroll down to **Disks**.
    *   Click **Add Disk**.
    *   **Name**: `student-db`
    *   **Mount Path**: `/opt/render/project/src/database`
    *   **Size**: `1 GB` (Free tier)
    *   *This ensures your student records stay saved even after the server restarts.*

## 3. Verify Deployment
Once Render finishes building, you will get a URL (e.g., `https://student-performance-analytics.onrender.com`).
- Navigate to the URL.
- Test a prediction.
- Verify that the data is saved in the **Student History** tab.

---

> [!IMPORTANT]
> Since this is a Python app with a SQLite database, using a **Persistent Disk** on Render is highly recommended. Otherwise, your data will be reset every time the app redeploys.
