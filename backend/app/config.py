"""StayNest application configuration.

All settings loaded from environment variables (12-factor compliant).
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_ENV: str = "development"
    DEBUG: bool = False
    APP_TITLE: str = "StayNest API"
    APP_VERSION: str = "0.1.0"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://staynest:staynest_secret@localhost:5432/staynest"
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "CHANGE-ME-use-openssl-rand-hex-64"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # S3-Compatible Storage
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_PUBLIC_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY_ID: str = "minioadmin"
    S3_SECRET_ACCESS_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "staynest-images"
    S3_REGION: str = "us-east-1"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"

    # Webhook
    WEBHOOK_SECRET: str = "CHANGE-ME-webhook-secret"

    # BetterAuth (validated in non-dev environments)
    BETTER_AUTH_SECRET: str = "change-me-generate-with-openssl-rand-base64-32"

    # Email
    EMAIL_BACKEND: str = "console"  # "console" or "smtp"
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_TLS: bool = True
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@staynest.com"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Sentry (leave empty to disable)
    SENTRY_DSN: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": True}

    def validate_secrets(self) -> None:
        """Raise at startup if critical secrets still have placeholder values."""
        default_jwt = "CHANGE-ME-use-openssl-rand-hex-64"
        default_webhook = "CHANGE-ME-webhook-secret"
        default_betterauth = "change-me-generate-with-openssl-rand-base64-32"
        if self.APP_ENV != "development":
            if self.JWT_SECRET_KEY == default_jwt:
                msg = (
                    "JWT_SECRET_KEY must be set via environment variable "
                    "in non-development environments"
                )
                raise ValueError(msg)
            if self.WEBHOOK_SECRET == default_webhook:
                msg = (
                    "WEBHOOK_SECRET must be set via environment variable "
                    "in non-development environments"
                )
                raise ValueError(msg)
            if self.BETTER_AUTH_SECRET == default_betterauth:
                msg = (
                    "BETTER_AUTH_SECRET must be set via environment variable "
                    "in non-development environments"
                )
                raise ValueError(msg)


settings = Settings()
settings.validate_secrets()
