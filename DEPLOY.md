# Deployment Guide - Student Performance Analytics (MongoDB Edition)

Your project now uses **MongoDB Atlas** for data storage, offering a robust and scalable solution for your analytics!

## 1. Sync Your Code
Ensure all local changes are pushed to your GitHub!

## 2. Updated Render Settings
Go to your **Web Service** on Render and ensure these fields match exactly:

| Field | Value |
| :--- | :--- |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app` |

## 3. Environment Variable (Crucial)
You must switch from `DATABASE_URL` to `MONGO_URI`.

1. Go to the **Environment** tab on Render.
2. DELETE the old `DATABASE_URL`.
3. ADD a new Environment Variable:
   - **Key**: `MONGO_URI`
   - **Value**: `mongodb+srv://<username>:<password>@cluster0.hoeochj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0`
   *(Replace `<username>` and `<password>` with your MongoDB Atlas credentials).*

---

### **Why this fixes your deployment:**
- **Flexible Schema**: MongoDB handles the student prediction data more gracefully than SQL, especially for nested analytics.
- **Stable Connection**: The `pymongo[srv]` driver is specifically optimized for cloud connections (Atlas).
- **Reduced Latency**: MongoDB Atlas naturally pairs well with Render's hosting regions.

**You are ready to launch! Just update the environment variables on Render and it will work.**
