import os
import secrets
import warnings
from pydantic import ConfigDict, field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")

    # App Settings
    APP_NAME: str = "HealthSenseAI"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:8000,http://127.0.0.1:8000,http://localhost:3000,http://127.0.0.1:3000"
    
    # Database Settings
    # SQLite fallback for easy local setup, PostgreSQL supported out of the box
    DATABASE_URL: str = "sqlite:///./healthmate.db"
    
    # JWT Settings
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Gemini API Settings
    GEMINI_API_KEY: str = ""

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "prod", "production", "false", "0", "no", "off"}:
                return False
            if normalized in {"debug", "dev", "development", "true", "1", "yes", "on"}:
                return True
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]
    
settings = Settings()

if not settings.JWT_SECRET_KEY:
    if settings.ENVIRONMENT.lower() in {"production", "prod"}:
        raise RuntimeError("JWT_SECRET_KEY must be set in production.")
    settings.JWT_SECRET_KEY = secrets.token_urlsafe(48)
    warnings.warn(
        "JWT_SECRET_KEY is not set. Using a generated development-only secret; "
        "sessions will reset when the process restarts.",
        RuntimeWarning,
    )
