from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://pricetrackr:testpassword@localhost:5432/pricetrackr"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:5000,http://localhost:3000"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_SECRET: str = "your-jwt-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    
    # --- ADD VAPID KEYS ---
    VAPID_PUBLIC_KEY: str = "BPF_f-g2b3-lJj8-O0-lJj8-O0-lJj8-O0-lJj8-O0-lJj8-O0-lJj8-O0-lJj8-O0-lJj8-O0-lJj8-O0-lJj8-O0"
    VAPID_PRIVATE_KEY: str = "your-private-vapid-key-goes-here"
    VAPID_CLAIMS_EMAIL: str = "mailto:admin@yourdomain.com"
    # --- END VAPID KEYS ---
    
    # Scraper
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    SCRAPER_DELAY_MIN: int = 2
    SCRAPER_DELAY_MAX: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
