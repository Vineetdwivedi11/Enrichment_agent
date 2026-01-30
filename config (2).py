"""Configuration settings for Email Open Discord Notifier."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings."""
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Close.io API
    CLOSEIO_API_KEY: str = os.getenv("CLOSEIO_API_KEY", "")
    CLOSEIO_API_URL: str = "https://api.close.com/api/v1"
    CLOSEIO_WEBHOOK_SECRET: Optional[str] = os.getenv("CLOSEIO_WEBHOOK_SECRET")
    
    # Discord configuration file (for multiple webhooks/channels)
    DISCORD_CONFIG_FILE: str = os.getenv("DISCORD_CONFIG_FILE", "discord_config.json")
    # Legacy: Single webhook URL (backwards compatible)
    DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL", "")
    
    # Polling settings (fallback if webhooks not available)
    POLLING_ENABLED: bool = os.getenv("POLLING_ENABLED", "true").lower() == "true"
    POLLING_INTERVAL_SECONDS: int = int(os.getenv("POLLING_INTERVAL_SECONDS", "300"))  # 5 minutes
    POLLING_LOOKBACK_MINUTES: int = int(os.getenv("POLLING_LOOKBACK_MINUTES", "10"))
    
    # Database for analytics
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/email_opens.db")
    
    # Cache settings (24/7 operation: 24-hour retention for duplicate prevention)
    CACHE_RETENTION_HOURS: int = int(os.getenv("CACHE_RETENTION_HOURS", "24"))
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
