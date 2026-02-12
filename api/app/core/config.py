"""
LoadMoveGH — Application Configuration
Loads settings from environment variables with sensible defaults.
"""

from __future__ import annotations

import json
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration sourced from .env / environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────
    APP_NAME: str = "LoadMoveGH"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # ── Database ─────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/loadmovegh"

    # ── JWT ──────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "CHANGE_ME_super_secret_key_64_chars"
    JWT_REFRESH_SECRET_KEY: str = "CHANGE_ME_another_secret_key_64_chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Email / SMTP ─────────────────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@loadmovegh.com"
    EMAIL_FROM_NAME: str = "LoadMoveGH"

    # ── OTP ──────────────────────────────────────────────────
    OTP_EXPIRE_MINUTES: int = 10
    OTP_LENGTH: int = 6

    # ── Mobile Money (MTN MoMo API) ──────────────────────────
    MOMO_BASE_URL: str = "https://sandbox.momodeveloper.mtn.com"
    MOMO_COLLECTION_API_KEY: str = ""
    MOMO_COLLECTION_API_USER: str = ""
    MOMO_COLLECTION_SUBSCRIPTION_KEY: str = ""
    MOMO_DISBURSEMENT_API_KEY: str = ""
    MOMO_DISBURSEMENT_API_USER: str = ""
    MOMO_DISBURSEMENT_SUBSCRIPTION_KEY: str = ""
    MOMO_CALLBACK_HOST: str = "https://api.loadmovegh.com"
    MOMO_ENVIRONMENT: str = "sandbox"  # sandbox or production

    # ── Platform Fees ──────────────────────────────────────────
    PLATFORM_COMMISSION_RATE: float = 0.05    # 5%
    WITHDRAWAL_FEE_RATE: float = 0.01         # 1%
    WITHDRAWAL_FEE_MIN: float = 0.50          # GHS
    WITHDRAWAL_FEE_MAX: float = 10.00         # GHS
    MIN_DEPOSIT_AMOUNT: float = 1.00          # GHS
    MIN_WITHDRAWAL_AMOUNT: float = 5.00       # GHS
    MAX_TRANSACTION_AMOUNT: float = 50000.00  # GHS

    # ── AI Pricing Engine ───────────────────────────────────────
    PRICING_MODEL_DIR: str = "ml_models"
    PRICING_DEFAULT_DIESEL_PRICE: float = 15.50  # GHS per litre
    PRICING_CONFIDENCE_THRESHOLD: float = 0.50   # Below this → add disclaimer
    PRICING_MAX_TRAINING_SAMPLES: int = 100000

    # ── Fraud Detection ──────────────────────────────────────────
    FRAUD_ALERT_THRESHOLD_MEDIUM: float = 40.0   # Composite ≥ this → alert
    FRAUD_ALERT_THRESHOLD_HIGH: float = 65.0     # ≥ this → auto-restrict
    FRAUD_ALERT_THRESHOLD_CRITICAL: float = 85.0 # ≥ this → auto-freeze
    FRAUD_AUTO_SCAN_ON_TRANSACTION: bool = True   # Scan on every payment event
    FRAUD_MAX_SIGNALS_PER_SCAN: int = 50          # Cap to prevent log flood

    # ── AI Assistant (OpenAI) ─────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_MAX_TOKENS: int = 2048
    OPENAI_TEMPERATURE: float = 0.4
    OPENAI_MAX_SESSIONS_PER_USER: int = 50
    OPENAI_MAX_MESSAGES_PER_SESSION: int = 100

    # ── Frontend ─────────────────────────────────────────────
    FRONTEND_URL: str = "https://www.loadmovegh.com"

    # ── Admin ──────────────────────────────────────────────
    ADMIN_URL: str = "https://admin.loadmovegh.com"

    # ── CORS ─────────────────────────────────────────────────
    CORS_ORIGINS: str = '["https://www.loadmovegh.com","https://loadmovegh.com","https://admin.loadmovegh.com","http://localhost:3000","http://localhost:3001"]'

    @property
    def cors_origins_list(self) -> List[str]:
        try:
            return json.loads(self.CORS_ORIGINS)
        except (json.JSONDecodeError, TypeError):
            return ["https://www.loadmovegh.com", "http://localhost:3000"]


settings = Settings()
