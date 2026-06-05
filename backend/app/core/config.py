import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Student Performance Prediction Portal"
    API_V1_STR: str = "/api"
    
    # Security
    # In production, change this to a random 32-character string
    SECRET_KEY: str = "SUPER_SECRET_STUDENT_PERFORMANCE_PREDICTION_KEY_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str = "sqlite:///./student_performance.db"
    
    # ML Models Paths
    # We will store models in a persistent directory
    MODEL_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ml", "model_cache"))
    
    @property
    def MODEL_PATH(self) -> str:
        return os.path.join(self.MODEL_DIR, "model.pkl")
        
    @property
    def META_PATH(self) -> str:
        return os.path.join(self.MODEL_DIR, "model_meta.json")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()

# Ensure model directory exists
os.makedirs(settings.MODEL_DIR, exist_ok=True)
