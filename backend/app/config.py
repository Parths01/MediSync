"""
backend/app/config.py
Centralised settings loaded from environment / .env file.
"""
from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # App
    app_env: str = "development"

    # Database
    database_url: str

    # CORS
    frontend_url: str = "http://localhost:3000"

    # Authentication cookies
    session_cookie_name: str = "medisync_session"
    csrf_cookie_name: str = "medisync_csrf"
    session_ttl_hours: int = 12
    session_cookie_secure: bool = False

    @model_validator(mode="after")
    def validate_production_cookies(self) -> "Settings":
        if self.app_env.lower() in {"production", "prod"} and not self.session_cookie_secure:
            raise ValueError("SESSION_COOKIE_SECURE must be enabled in production")
        if self.session_ttl_hours < 1 or self.session_ttl_hours > 168:
            raise ValueError("SESSION_TTL_HOURS must be between 1 and 168")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
