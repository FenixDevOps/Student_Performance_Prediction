# Deployment Guide - Student Performance Analytics (PostgreSQL Edition)

Follow these steps to deploy your application to the cloud using **Render** with permanent storage.

## 1. Prepare Your Repository
Ensure your project is on GitHub:
```bash
git add .
git commit -m "Migrate to PostgreSQL for persistent cloud storage"
git push origin main
```

## 2. Create a Free PostgreSQL Database on Render
1.  **New PostgreSQL**: On the [Render Dashboard](https://dashboard.render.com/), click **New +** -> **PostgreSQL**.
2.  **Config**:
    *   **Name**: `student-db`
    *   **Database**: `student_history`
    *   **Tier**: `Free`
3.  **Click Create**. Wait for it to become **"Available"**.
4.  **Copy URL**: Look for the **Internal Database URL** (e.g., `postgres://user:pass@host/db`).

## 3. Deploy the Web Service
1.  **New Web Service**: Click **New +** -> **Web Service**.
2.  **Choose Repository**: Select `Student_Performance_Prediction`.
3.  **Config Settings**:
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `gunicorn --chdir app app:app`
4.  **Environment Variables**:
    *   Click **Advanced** -> **Add Environment Variable**.
    *   **Key**: `DATABASE_URL`
    *   **Value**: Paste your **Internal Database URL** from Step 2.
5.  **Submit**: Click **Create Web Service**.

## 4. Why This is Better
- **Persistent Data**: Unlike SQLite on the free tier, PostgreSQL stores your student records in a separate, dedicated database. Even if the web server restarts, your data stays safe.
- **Dual Mode**: The app still works with your local `student_history.db` for offline testing!

---

> [!NOTE]
> Render's free PostgreSQL databases expire after **90 days**. If you want a forever-free database, consider using **Supabase** or another external provider, but Render is the easiest for now.
