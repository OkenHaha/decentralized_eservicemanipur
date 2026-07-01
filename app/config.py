import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Anti-Corruption e-Services Manipur"
    API_V1_STR: str = "/api/v1"
    
    # SQLite Database configuration
    DB_FILE: str = "eseba.db"
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DB_FILE}"
    
    # Security config
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Files Upload Directory
    UPLOAD_DIR: Path = Path("uploads")
    
    # Development Flag
    DEV_MODE: bool = True

    # External Blockchain Node URL
    BLOCKCHAIN_NODE_URL: str = os.getenv("BLOCKCHAIN_NODE_URL", "http://127.0.0.1:8000")

    class Config:
        case_sensitive = True

settings = Settings()

# Ensure uploads directory exists
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
