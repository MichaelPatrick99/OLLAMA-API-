"""Configuration settings for the Ollama API wrapper."""

from pydantic_settings import BaseSettings
from typing import Optional


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
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"


# Create settings instance
settings = Settings()