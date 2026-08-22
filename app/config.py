from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables and .env file."""

    # App metadata
    app_name: str = Field(default="Invoice Automation POC", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")

    # Environment
    debug: bool = Field(default=False, description="Debug mode flag")
    environment: str = Field(default="development", description="Environment (development/production)")

    # API Configuration
    openai_api_key: str = Field(default="", description="OpenAI API key for AI extraction")
    openai_model: str = Field(default="", description="OpenAI model for invoice extraction")

    # File paths
    upload_dir: str = Field(
        default="data/uploads",
        description="Directory for uploaded invoice files",
    )
    database_url: str = Field(
        default="sqlite:///data/invoice.db",
        description="SQLite database URL",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def __init__(self, **kwargs):
        """Initialize settings and ensure required directories exist."""
        super().__init__(**kwargs)
        # Create upload directory if it doesn't exist
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Uses @lru_cache to ensure a single Settings instance is created and reused.
    
    Returns:
        Settings: Cached application configuration.
    """
    return Settings()
