"""Simple website scraper using BeautifulSoup."""

from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from .config import settings
from .models import WebsiteData


class SimpleScraper:
    """
    Free alternative to Firecrawl using BeautifulSoup.
    Scrapes main content primarily from the provided URL.
    """

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def scrape_website(self, url: str, max_pages: int = 1) -> WebsiteData:
        """
        Scrape a single page (since we can't easily crawl sitemaps without more logic).
        
        Args:
            url: Website URL
            max_pages: Ignored in this simple version (scrapes only 1 page)
            
        Returns:
            WebsiteData object
        """
        try:
            with httpx.Client(timeout=settings.REQUEST_TIMEOUT, follow_redirects=True) as client:
                response = client.get(url, headers=self.headers)
                response.raise_for_status()
                html = response.text
                
            soup = BeautifulSoup(html, "lxml")
            
            # Remove scripts and styles
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extract title and description
            title = soup.title.string if soup.title else ""
            meta_desc = soup.find("meta", attrs={"name": "description"})
            description = meta_desc["content"] if meta_desc else ""
            
            # Extract text content
            # Get text and separate with newlines
            lines = (line.strip() for line in soup.get_text().splitlines())
            # Drop blank lines
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text_content = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Format as simple markdown
            content = f"# {title}\n\n{text_content}"
            
            return WebsiteData(
                url=url,
                title=title,
                description=description,
                content=content,
                key_points=[],  # No automatic key point extraction yet (could use simple NLP/LLM later)
                pages_scraped=[url],
                metadata={"generator": "SimpleScraper"},
                scraped_at=datetime.now()
            )
            
        except Exception as e:
            print(f"SimpleScraper failed for {url}: {e}")
            # Return empty/error data
            return WebsiteData(
                url=url,
                title="Error Scraping",
                description=str(e),
                content=f"Error scraping {url}: {e}",
                key_points=[],
                pages_scraped=[],
                metadata={"error": str(e)},
                scraped_at=datetime.now()
            )
