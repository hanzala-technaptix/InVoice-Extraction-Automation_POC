from functools import lru_cache

from pydantic import AliasChoices, Field
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

    # Gmail IMAP (app password — no OAuth client ID required for POC)
    gmail_email: str = Field(default="", description="Gmail address for IMAP")
    gmail_app_password: str = Field(
        default="",
        validation_alias=AliasChoices("GMAIL_APP_PASSWORD", "GMAIL_PASSWORD"),
        description="Gmail 16-character app password",
    )
    gmail_query: str = Field(
        default="has:attachment filename:pdf",
        description="Gmail search query for invoice PDF messages",
    )
    gmail_poll_enabled: bool = Field(
        default=True,
        description="Enable background Gmail polling on server startup",
    )
    gmail_poll_interval_seconds: int = Field(
        default=120,
        ge=30,
        description="Seconds between Gmail inbox polls",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )



@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Uses @lru_cache to ensure a single Settings instance is created and reused.
    
    Returns:
        Settings: Cached application configuration.
    """
    return Settings()
