"""
========================================
Application Configuration
========================================
Centralized settings management using Pydantic
"""

from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    
    # ==================== API KEYS ====================
    GEMINI_API_KEY: str = ""
    
    # ==================== DATABASE ====================
    DATABASE_URL: str = "sqlite:///./data/app.db"
    
    # ==================== VECTOR STORE ====================
    VECTOR_STORE_PATH: str = "./data/vectorstore"
    
    # ==================== SECURITY ====================
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # ==================== APPLICATION ====================
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # ==================== CORS ====================
    FRONTEND_URL: str = "http://localhost:5173"
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173"
    ]
    
    # ==================== FILE UPLOAD ====================
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".txt", ".csv", ".json", ".docx"]
    UPLOAD_DIR: str = "./data/uploads"
    
    # ==================== LLM SETTINGS ====================
    LLM_MODEL: str = "gemini-pro"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2048
    
    # ==================== RAG SETTINGS ====================
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RESULTS: int = 5
    
    # ==================== AGENT SETTINGS ====================
    AGENT_MAX_ITERATIONS: int = 10
    AGENT_TIMEOUT: int = 60  # seconds
    
    # ==================== OPTIONAL INTEGRATIONS ====================
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SLACK_WEBHOOK_URL: str = ""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    Uses lru_cache for performance
    """
    return Settings()


# Global settings instance
settings = get_settings()


# ==================== Validation ====================
def validate_settings():
    """Validate critical settings on startup"""
    errors = []
    
    if not settings.GEMINI_API_KEY:
        errors.append("GEMINI_API_KEY is required")
    
    if settings.SECRET_KEY == "your-secret-key-change-in-production":
        if settings.ENVIRONMENT == "production":
            errors.append("SECRET_KEY must be changed in production")
    
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")


# ==================== Directory Setup ====================
def ensure_directories():
    """Create necessary directories"""
    directories = [
        settings.VECTOR_STORE_PATH,
        settings.UPLOAD_DIR,
        "./data",
        "./logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
