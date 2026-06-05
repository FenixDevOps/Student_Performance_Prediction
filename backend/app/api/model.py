from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
import os

from backend.app.core.database import get_db
from backend.app.core.security import require_admin
from backend.app.database.models import User, PredictionRecord
from backend.app.database.seed import seed_database
from backend.app.ml.inference import load_meta, reset_ml_cache
from backend.app.ml.pipeline import train_and_save_model

router = APIRouter()

@router.get("/info")
def get_model_details():
    """Retrieve details on the active ML model (algorithm, R^2, RMSE, importances)."""
    try:
        meta = load_meta()
        return meta
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model metadata is currently unavailable: {str(e)}"
        )

@router.post("/retrain")
def retrain_model(
    current_user: User = Depends(require_admin)
):
    """
    Triggers synchronous model retraining on the current dataset.
    Accessible only by Admins.
    """
    try:
        new_meta = train_and_save_model()
        reset_ml_cache()  # Clear cached singleton instances
        return {
            "success": True, 
            "message": "Model retrained successfully.", 
            "metadata": new_meta
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model retraining failed: {str(e)}"
        )

@router.post("/clear-data")
def clear_prediction_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Deletes all prediction records in the database. Admin only."""
    try:
        count = db.query(PredictionRecord).delete()
        db.commit()
        return {"success": True, "count": count, "message": f"Successfully deleted {count} records."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to clear records: {str(e)}")

@router.post("/seed-data")
def seed_prediction_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Seeds prediction records. Admin only."""
    try:
        count = seed_database(db)
        return {"success": True, "count": count, "message": f"Seeded {count} records."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to seed records: {str(e)}")
