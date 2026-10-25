# backend/fastapi_app/config.py (add more settings)
from pydantic_settings import BaseSettings
from typing import List, Optional
from dotenv import load_dotenv
import os

env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(env_path)

class Settings(BaseSettings):
    # API Settings
    APIFY_API_TOKEN: str = os.getenv("APIFY_API_TOKEN", "")
    API_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Database
    DATABASE_URL: str = os.getenv("Database_URL")

    # Redis
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
   
    
    # Celery
    CELERY_BROKER_URL: str = "redis://127.0.0.1:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://127.0.0.1:6379/0"
    
    # Supabase/S3 (for resume storage)
    SUPABASE_URL: str = os.getenv("supabase_url_service_role_key")
    SUPABASE_KEY: str = os.getenv("supabase_key_service_role_key")
    
    # Playwright
    PLAYWRIGHT_HEADLESS: bool = True
    AUTO_APPLY_INTERNAL_TOKEN: str = os.getenv("AUTO_APPLY_INTERNAL_TOKEN", "")
    
    # Scraping
    SCRAPE_DELAY_MIN: float = 1.0
    SCRAPE_DELAY_MAX: float = 3.0
    SCRAPE_TIMEOUT: int = 30000  # milliseconds
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Security
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 120

    
    

    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()
