import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.database import Base, engine, SessionLocal
from backend.app.database.seed import seed_database
from backend.app.ml.inference import load_model, load_meta

from backend.app.api import auth, predict, analytics, model

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="2.0.0",
    description="Production-grade ML prediction engine for student exam scores and AI roadmap recommendations.",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configurations
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local development flexibility, support all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_db_and_ml():
    """Initializes tables, seeds mock users/predictions, and pre-caches the ML model."""
    print("[Startup] Initializing SQLite tables...")
    Base.metadata.create_all(bind=engine)
    
    # Auto-seeding
    db = SessionLocal()
    try:
        print("[Startup] Running DB seed check...")
        seed_count = seed_database(db)
        if seed_count > 0:
            print(f"[Startup] [SUCCESS] Seeded {seed_count} prediction records.")
        else:
            print("[Startup] DB seed check clean (records already present or seeded).")
    except Exception as e:
        print(f"[Startup] DB seeding error: {str(e)}")
    finally:
        db.close()
        
    # Pre-load ML Model
    print("[Startup] Pre-loading ML inference model...")
    try:
        model = load_model()
        meta = load_meta()
        print(f"[Startup] [SUCCESS] Model loaded: {meta.get('model_name', 'Unknown')} (R^2={meta.get('r2')})")
    except Exception as e:
        print(f"[Startup] Model preloading failed: {str(e)}")

@app.get("/")
@app.get("/api/health")
def health_check():
    """Service status monitor."""
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": "2.0.0"
    }

# Include API Routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(predict.router, prefix=f"{settings.API_V1_STR}/predict", tags=["Predictions"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_STR}/analytics", tags=["Analytics"])
app.include_router(model.router, prefix=f"{settings.API_V1_STR}/model", tags=["Model Controls"])

if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
