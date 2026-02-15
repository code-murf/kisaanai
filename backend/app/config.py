"""
Application configuration using Pydantic Settings.
Handles environment variables and provides type-safe configuration.
"""
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application
    APP_NAME: str = "Agri-Analytics API"
    PROJECT_NAME: str = "Agri-Analytics API"  # Alias for compatibility
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True  # Enable debug mode by default for development
    ENVIRONMENT: str = "development"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/agri_analytics"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_EXPIRY_SECONDS: int = 300  # 5 minutes
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # External APIs
    AGMARKNET_BASE_URL: str = "https://agmarknet.gov.in"
    IMD_WEATHER_API_URL: str = "https://api.imd.gov.in"
    
    # Bhashini Voice API
    BHASHINI_API_URL: str = "https://bhashini.gov.in/api"
    BHASHINI_API_KEY: Optional[str] = None
    
    # Twilio WhatsApp
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_WHATSAPP_NUMBER: Optional[str] = None
    
    # ML Models
    MODEL_PATH: str = "models"
    XGB_MODEL_PATH: str = "models/xgb_forecast.onnx"
    TFT_MODEL_PATH: str = "models/tft_forecast.pt"
    
    # MinIO / S3
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "agri-data"
    MINIO_BUCKET: str = "agri-data"
    MINIO_SECURE: bool = False

    # Supabase (Optional)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    
    # Hugging Face
    HF_TOKEN: Optional[str] = None
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD_SECONDS: int = 60
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000", 
        "http://localhost:5173", 
        "http://localhost:3003",
        "https://kisaanai.vercel.app",
        "https://*.vercel.app"
    ]
    
    # AI/ML Settings
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"  # Alternative: mixtral-8x7b-32768
    
    # Voice API Settings
    SARVAM_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_AGENT_ID: str = ""
    VOICE_STT_TIMEOUT: int = 5  # Speech-to-text timeout (seconds)
    VOICE_LLM_TIMEOUT: int = 10  # LLM inference timeout (seconds)
    VOICE_TTS_TIMEOUT: int = 5  # Text-to-speech timeout (seconds)
    VOICE_SESSION_TIMEOUT: int = 300  # Session timeout (seconds)
    VOICE_MAX_CONCURRENT: int = 50  # Max concurrent voice requests


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
