# Deployment Guide - Student Performance Analytics (Final Edition)

Your project has been simplified to a **flat structure** (no subfolders for the main app) to ensure 100% compatibility with Render's Free tier.

## 1. Sync Your Code
I have already pushed these changes to your GitHub! 

## 2. Updated Render Settings
Go to your **Web Service** on Render and ensure these fields match exactly:

| Field | Value |
| :--- | :--- |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app` |

## 3. Environment Variable (Crucial)
Ensure you have added your Supabase URL in the **Environment** section:
- **Key**: `DATABASE_URL`
- **Value**: `postgresql://postgres:Soumya%401820@db.hoeochjdnluzymbdnsza.supabase.co:5432/postgres`
  *(Note: I encoded the `@` in your password as `%40` to prevent connection errors).*

---

### **Why this fixes the "Status 1" error:**
-   **No more folder path issues**: By moving `app.py` to the main folder, Render can find it instantly.
-   **Stable Python**: I added a `runtime.txt` file to force Render to use Python 3.11.
-   **Diagnostic Logs**: If it still fails, the logs will now show a very clear message starting with **`>>>`** explaining the exact line that failed.

**You are ready to launch! Just update the Start Command on Render and it should work.**
