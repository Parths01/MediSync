"""
backend/app/config.py
Centralised settings loaded from environment / .env file.
"""
from functools import lru_cache

from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # App
    app_env: str = "development"

    # Database
    database_url: str
    database_ssl_mode: Literal["prefer", "require", "verify-ca", "verify-full"] = "prefer"
    pgsslrootcert: str | None = None
    cleanup_database_url: str | None = None

    # CORS
    frontend_url: str = "http://localhost:3000"
    vercel_env: str | None = None
    vercel_url: str | None = None
    cron_secret: str | None = None

    @property
    def allowed_frontend_origins(self) -> list[str]:
        origins = [self.frontend_url.rstrip("/")]
        # Vercel gives each preview deployment its own host. Accept only that
        # deployment's HTTPS origin; never allow a broad *.vercel.app pattern.
        if self.vercel_env == "preview" and self.vercel_url:
            origins.append(f"https://{self.vercel_url.removeprefix('https://').rstrip('/')}")
        return list(dict.fromkeys(origins))

    # Authentication cookies
    session_cookie_name: str = "medisync_session"
    csrf_cookie_name: str = "medisync_csrf"
    session_ttl_hours: int = 12
    session_cookie_secure: bool = False

    # AI is deliberately local-only until MediSync verifies its privacy gate.
    ai_patient_data_enabled: bool = False
    ai_provider: Literal["local_rules"] = "local_rules"
    ai_external_calls_enabled: bool = False
    ai_timeout_seconds: float = Field(default=12.0, ge=1.0, le=60.0)
    ai_max_retries: int = Field(default=1, ge=0, le=3)
    ai_max_output_tokens: int = Field(default=512, ge=32, le=2048)
    ai_context_max_messages: int = Field(default=12, ge=1, le=30)
    ai_context_max_chars: int = Field(default=6000, ge=256, le=16000)
    ai_conversation_retention_days: int = Field(default=90, ge=1, le=3650)
    ai_analytics_retention_days: int = Field(default=365, ge=1, le=3650)
    operator_audit_retention_days: int = Field(default=365, ge=180, le=3650)

    @model_validator(mode="after")
    def validate_production_cookies(self) -> "Settings":
        if self.app_env.lower() in {"production", "prod"} and not self.session_cookie_secure:
            raise ValueError("SESSION_COOKIE_SECURE must be enabled in production")
        if self.app_env.lower() in {"production", "prod"} and self.database_ssl_mode != "verify-full":
            raise ValueError("DATABASE_SSL_MODE=verify-full is required in production")
        if self.session_ttl_hours < 1 or self.session_ttl_hours > 168:
            raise ValueError("SESSION_TTL_HOURS must be between 1 and 168")
        if self.ai_external_calls_enabled:
            raise ValueError("External AI calls cannot be enabled until the privacy gate is approved")
        if self.app_env.lower() in {"production", "prod"} and self.ai_patient_data_enabled:
            raise ValueError("AI patient-data processing is disabled in production pending privacy and security approval")
        if self.cron_secret and len(self.cron_secret) < 16:
            raise ValueError("CRON_SECRET must contain at least 16 characters")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
