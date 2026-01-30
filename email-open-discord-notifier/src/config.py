"""Configuration for Enrichment Agent."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """Application settings."""
    
    # Email Open Discord Notifier settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    CLOSEIO_API_KEY: str = os.getenv("CLOSEIO_API_KEY", "")
    CLOSEIO_API_URL: str = "https://api.close.com/api/v1"
    CLOSEIO_WEBHOOK_SECRET: Optional[str] = os.getenv("CLOSEIO_WEBHOOK_SECRET")
    
    DISCORD_CONFIG_FILE: str = os.getenv("DISCORD_CONFIG_FILE", "discord_config.json")
    DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL", "")
    
    POLLING_ENABLED: bool = os.getenv("POLLING_ENABLED", "true").lower() == "true"
    POLLING_INTERVAL_SECONDS: int = int(os.getenv("POLLING_INTERVAL_SECONDS", "300"))
    POLLING_LOOKBACK_MINUTES: int = int(os.getenv("POLLING_LOOKBACK_MINUTES", "10"))
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/email_opens.db")
    
    CACHE_RETENTION_HOURS: int = int(os.getenv("CACHE_RETENTION_HOURS", "24"))
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
