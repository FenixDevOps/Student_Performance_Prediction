from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
import os

from backend.app.core.database import get_db
from backend.app.core.security import require_admin
from backend.app.database.models import User, PredictionRecord, ModelRetrainHistory, ModelSettings
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

@router.get("/history")
def get_retrain_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Fetch logs of past model retraining metrics. Admin only."""
    return db.query(ModelRetrainHistory).order_by(ModelRetrainHistory.trained_at.desc()).all()

@router.post("/active")
def change_active_algorithm(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Change the active ML model algorithm in the backend. Admin only."""
    algorithm = payload.get("active_algorithm")
    valid_algos = ["Linear Regression", "Random Forest", "Gradient Boosting", "Neural Network", "Ridge Regression"]
    
    if not algorithm or algorithm not in valid_algos:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid algorithm choice. Must be one of: {', '.join(valid_algos)}"
        )
        
    setting = db.query(ModelSettings).first()
    if not setting:
        setting = ModelSettings(active_algorithm=algorithm)
        db.add(setting)
    else:
        setting.active_algorithm = algorithm
        
    db.commit()
    reset_ml_cache() # Clear cache so next request loads the new algorithm pkl!
    
    return {
        "success": True, 
        "active_algorithm": algorithm,
        "message": f"Active ML algorithm successfully changed to {algorithm}."
    }

