"""Configuration settings for Research Agent."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Firecrawl API
    FIRECRAWL_API_KEY: str = os.getenv("FIRECRAWL_API_KEY", "")
    FIRECRAWL_API_URL: str = "https://api.firecrawl.dev/v1"
    
    # Bright Data LinkedIn API (primary)
    BRIGHTDATA_API_KEY: str = os.getenv("BRIGHTDATA_API_KEY", "")
    BRIGHTDATA_API_URL: str = "https://api.brightdata.com/datasets/v3"
    
    # Apify API (secondary)
    APIFY_API_KEY: str = os.getenv("APIFY_API_KEY", "")
    
    # joeyism scraper fallback
    USE_JOEYISM_FALLBACK: bool = os.getenv("USE_JOEYISM_FALLBACK", "false").lower() == "true"
    
    # Google Sheets
    GOOGLE_CREDENTIALS_PATH: Optional[Path] = Path(os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json"))
    
    # Request settings
    REQUEST_TIMEOUT: int = 60
    MAX_RETRIES: int = 3
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
