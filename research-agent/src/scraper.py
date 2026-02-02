"""Firecrawl website scraper."""

from typing import Optional
import httpx
from .config import settings
from .models import WebsiteData


class FirecrawlScraper:
    """Scrape website content using Firecrawl API."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.FIRECRAWL_API_KEY
        self.base_url = settings.FIRECRAWL_API_URL
        
        if not self.api_key:
            raise ValueError("FIRECRAWL_API_KEY not set")
    
    def scrape_website(self, url: str) -> WebsiteData:
        """Scrape a single URL."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "url": url,
            "formats": ["markdown"],
            "onlyMainContent": True
        }
        
        with httpx.Client(timeout=settings.REQUEST_TIMEOUT) as client:
            response = client.post(
                f"{self.base_url}/scrape",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
        
        page_data = data.get("data", {})
        
        return WebsiteData(
            url=url,
            title=page_data.get("metadata", {}).get("title"),
            content=page_data.get("markdown", ""),
            metadata=page_data.get("metadata", {})
        )
