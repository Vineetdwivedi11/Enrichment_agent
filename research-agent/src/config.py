"""Configuration for Enrichment Agent."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """Application settings."""
    
    # Enrichment Agent settings
    FIRECRAWL_API_KEY: str = os.getenv("FIRECRAWL_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "") 
    FIRECRAWL_API_URL: str = "https://api.firecrawl.dev/v1"
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    
    PROMPTS_DIR: Path = Path("prompts")
    SCHEMAS_DIR: Path = Path("schemas")
    OUTPUT_DIR: Path = Path("output")
    
    REQUEST_TIMEOUT: int = 60
    MAX_RETRIES: int = 3
    
    # Minimal Cost / Open Source Settings
    USE_JOEYISM_FALLBACK: bool = os.getenv("USE_JOEYISM_FALLBACK", "true").lower() == "true"
    USE_FREE_SCRAPER: bool = os.getenv("USE_FREE_SCRAPER", "true").lower() == "true"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
