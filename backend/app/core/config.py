import os
from typing import List

class Settings:
    APP_NAME: str = "The Exam Timetable from Hell"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "hell_exam_timetable_jwt_secret_key_2026_super_secure")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./exam_timetable.db")
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://localhost:80",
    ]
    
    # Optimization Weights (Soft Constraints S1-S8)
    DEFAULT_SOLVER_TIME_LIMIT_SECONDS: int = int(os.getenv("DEFAULT_SOLVER_TIME_LIMIT_SECONDS", "30"))
    WEIGHT_STUDENT_BURDEN: int = int(os.getenv("DEFAULT_WEIGHT_BURDEN", "100"))            # S1: Multiple exams on same day
    WEIGHT_EXAM_SPACING: int = int(os.getenv("DEFAULT_WEIGHT_SPACING", "50"))               # S2: Back-to-back / insufficient rest
    WEIGHT_DAILY_IMBALANCE: int = int(os.getenv("DEFAULT_WEIGHT_IMBALANCE", "30"))          # S3/S8: Daily load skew
    WEIGHT_PREFERENCE_VIOLATION: int = int(os.getenv("DEFAULT_WEIGHT_PREFERENCE", "20"))    # S4: Missing preferred slots
    WEIGHT_ROOM_UTILIZATION: int = int(os.getenv("DEFAULT_WEIGHT_ROOM_UTILIZATION", "10"))  # S5: Excess room capacity waste
    WEIGHT_UNNECESSARY_CHANGES: int = int(os.getenv("DEFAULT_WEIGHT_UNNECESSARY_CHANGES", "80")) # S6: Movement from existing schedule
    WEIGHT_UNDESIRABLE_SESSION: int = int(os.getenv("DEFAULT_WEIGHT_UNDESIRABLE_SESSION", "40")) # S7: Early morning / late evening

settings = Settings()
