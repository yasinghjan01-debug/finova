import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "FINOVA"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment & Security
    SECRET_KEY: str = "finova-secret-super-key-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Razorpay Test Mode Configuration
    RAZORPAY_KEY_ID: str = "rzp_test_finovaMockKey123"
    RAZORPAY_KEY_SECRET: str = "finovaMockSecretKey456"
    RAZORPAY_WEBHOOK_SECRET: str = "finovaWebhookSecret789"
    
    # Database
    DATABASE_URL: str = "sqlite:///./finova.db"
    
    # Policy Thresholds
    AUTO_RECONCILE_CONFIDENCE_THRESHOLD: float = 0.95
    HIGH_RISK_THRESHOLD: float = 70.0
    CRITICAL_RISK_THRESHOLD: float = 85.0
    AUTO_REMINDER_MAX_AMOUNT: float = 50000.0  # Max amount for autonomous nudge without human sign-off
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
