"""
Application configuration using Pydantic Settings.
Loads configuration from environment variables.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, ValidationInfo
from typing import Optional
import sys


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Nexus Analyzer"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # S3 / MinIO
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET_NAME: str = "nexus-analyzer"
    S3_REGION: str = "us-east-1"

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 100
    ALLOWED_FILE_TYPES: str = "csv,xlsx"

    # Feature Flags
    ENABLE_REGISTRATION: bool = True
    ENABLE_EMAIL_VERIFICATION: bool = False
    ENABLE_AUDIT_LOG: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Celery
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    # Email (Optional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_FROM_NAME: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @field_validator('SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v: str, info: ValidationInfo) -> str:
        """Validate SECRET_KEY has sufficient strength."""
        if not v:
            raise ValueError("SECRET_KEY cannot be empty")

        # Check minimum length (32 chars = 256 bits)
        if len(v) < 32:
            raise ValueError(
                f"SECRET_KEY must be at least 32 characters (got {len(v)}). "
                "Generate a secure key with: python backend/scripts/generate_secret_key.py"
            )

        # Check for common weak/example keys
        weak_keys = [
            "your-secret-key",
            "change-me",
            "secret",
            "password",
            "example",
            "test",
            "demo",
            "dev",
            "your-secret-key-min-32-chars-change-in-production",
        ]

        v_lower = v.lower()
        for weak in weak_keys:
            if weak in v_lower:
                print(
                    f"\n{'='*70}\n"
                    f"WARNING: SECRET_KEY appears to contain weak/example text: '{weak}'\n"
                    f"This is a SECURITY RISK in production!\n"
                    f"Generate a secure key with:\n"
                    f"  python backend/scripts/generate_secret_key.py\n"
                    f"{'='*70}\n",
                    file=sys.stderr
                )
                # In production, fail hard
                environment = info.data.get('ENVIRONMENT', 'development')
                if environment == 'production':
                    raise ValueError(
                        f"SECRET_KEY contains weak/example text in production environment. "
                        f"Generate a secure key with: python backend/scripts/generate_secret_key.py"
                    )

        # Check entropy (should have variety of characters)
        unique_chars = len(set(v))
        if unique_chars < 16:
            print(
                f"\n{'='*70}\n"
                f"WARNING: SECRET_KEY has low entropy (only {unique_chars} unique characters)\n"
                f"Recommended: Use a cryptographically random key with high entropy.\n"
                f"Generate one with: python backend/scripts/generate_secret_key.py\n"
                f"{'='*70}\n",
                file=sys.stderr
            )

        return v

    @property
    def cors_origins_list(self) -> list[str]:
        """Convert CORS_ORIGINS string to list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def allowed_file_types_list(self) -> list[str]:
        """Convert ALLOWED_FILE_TYPES string to list."""
        return [ft.strip() for ft in self.ALLOWED_FILE_TYPES.split(",")]


# Create global settings instance
settings = Settings()
