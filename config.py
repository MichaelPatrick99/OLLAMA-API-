"""Configuration settings for the Ollama API wrapper with authentication."""

from pydantic_settings import BaseSettings
from typing import Optional
import secrets


class Settings(BaseSettings):
    """Application settings."""
    
    # Ollama API settings
    OLLAMA_API_BASE_URL: str = "http://localhost:11434"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 3000
    DEBUG: bool = False
    
    # Default model settings
    DEFAULT_MODEL: str = "llama3:8b"
    DEFAULT_CONTEXT_SIZE: int = 4096
    REQUEST_TIMEOUT: float = 60.0
    
    # Database settings
    DATABASE_URL: Optional[str] = None  # Primary database URL - PRIORITIZED
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "ollama_api"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "password"
    
    # Authentication settings
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # API Key settings
    API_KEY_DEFAULT_EXPIRE_DAYS: int = 365
    API_KEY_MAX_EXPIRE_DAYS: int = 1825  # 5 years
    
    # Rate limiting settings
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Redis settings (for session management and rate limiting)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: Optional[str] = None
    
    # Security settings
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGITS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = False
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None
    LOG_USAGE: bool = True  # Log API usage for analytics
    
    # CORS settings
    CORS_ORIGINS: list = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]
    
    # Admin settings
    ADMIN_USERNAME: str = "admin"
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: str = "admin123"  # Will be hashed on first run
    CREATE_DEFAULT_ADMIN: bool = True
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"


# Create settings instance
settings = Settings()


def get_database_url() -> str:
    """Get the complete database URL.
    
    Returns:
        Database connection URL (prioritizes DATABASE_URL from .env)
    """
    # ALWAYS prioritize DATABASE_URL from environment
    if settings.DATABASE_URL:
        return settings.DATABASE_URL
    
    # Fallback to individual settings (PostgreSQL)
    return (
        f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )


def get_redis_url() -> str:
    """Get the complete Redis URL.
    
    Returns:
        Redis connection URL
    """
    if settings.REDIS_URL:
        return settings.REDIS_URL
    
    auth_part = f":{settings.REDIS_PASSWORD}@" if settings.REDIS_PASSWORD else ""
    return f"redis://{auth_part}{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
