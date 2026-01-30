"""Firecrawl website scraper."""

from datetime import datetime
from typing import Dict, Any, List
from urllib.parse import urlparse

import httpx

from .config import settings
from .models import WebsiteData


class FirecrawlScraper:
    """Scrape website data using Firecrawl API."""
    
    # Important page patterns (in priority order)
    PRIORITY_PATTERNS = [
        'about', 'team', 'company', 'who-we-are',
        'products', 'services', 'solutions', 'what-we-do',
        'contact', 'careers', 'jobs',
        'customers', 'case-studies', 'testimonials',
        'blog', 'news', 'press'
    ]
    
    def __init__(self):
        self.api_key = settings.FIRECRAWL_API_KEY
        self.base_url = settings.FIRECRAWL_API_URL
        
        if not self.api_key:
            raise ValueError("FIRECRAWL_API_KEY not set in environment")
    
    def get_sitemap(self, url: str) -> List[str]:
        """
        Get sitemap/page list from website.
        
        Args:
            url: Website URL
            
        Returns:
            List of page URLs
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "url": url,
            "mode": "sitemap"
        }
        
        with httpx.Client(timeout=settings.REQUEST_TIMEOUT) as client:
            response = client.post(
                f"{self.base_url}/map",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
        
        return data.get("links", [])
    
    def rank_pages_by_importance(self, urls: List[str]) -> List[str]:
        """
        Rank pages by importance based on URL patterns.
        
        Args:
            urls: List of page URLs
            
        Returns:
            Sorted list of URLs by importance
        """
        def get_score(url: str) -> int:
            """Score a URL based on importance patterns."""
            url_lower = url.lower()
            path = urlparse(url).path.lower()
            
            # Homepage gets highest score
            if path in ['/', '']:
                return 1000
            
            # Check priority patterns
            for idx, pattern in enumerate(self.PRIORITY_PATTERNS):
                if pattern in path or pattern in url_lower:
                    return 900 - (idx * 10)  # Higher score for earlier patterns
            
            # Shorter paths are generally more important
            path_depth = len([p for p in path.split('/') if p])
            return max(0, 500 - (path_depth * 50))
        
        # Sort by score (descending)
        return sorted(urls, key=get_score, reverse=True)
    
    def extract_key_points(self, content: str, max_points: int = 5) -> List[str]:
        """
        Extract key points from content.
        
        Simple extraction based on:
        - Sentences with important keywords
        - Headings and bold text
        - Short, informative sentences
        
        Args:
            content: Page content (markdown)
            max_points: Maximum number of key points
            
        Returns:
            List of key points
        """
        if not content:
            return []
        
        key_points = []
        
        # Split into lines
        lines = content.split('\n')
        
        # Extract headings (markdown format)
        for line in lines:
            line = line.strip()
            
            # Main headings (##, ###)
            if line.startswith('##') and not line.startswith('####'):
                point = line.lstrip('#').strip()
                if len(point) > 10 and len(point) < 200:
                    key_points.append(point)
            
            # Bold text with content
            elif '**' in line:
                # Extract text between ** markers
                parts = line.split('**')
                for i in range(1, len(parts), 2):
                    if len(parts[i]) > 10 and len(parts[i]) < 200:
                        key_points.append(parts[i].strip())
        
        # Keywords for important content
        important_keywords = [
            'specialize', 'focus', 'provide', 'offer', 'solution',
            'mission', 'vision', 'goal', 'value', 'founded',
            'serve', 'help', 'enable', 'deliver', 'leading'
        ]
        
        # Extract sentences with important keywords
        sentences = []
        current_sentence = ''
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('*'):
                current_sentence += ' ' + line
                if line.endswith('.') or line.endswith('!'):
                    sentences.append(current_sentence.strip())
                    current_sentence = ''
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in important_keywords):
                if len(sentence) > 20 and len(sentence) < 300:
                    key_points.append(sentence)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_points = []
        for point in key_points:
            point_normalized = point.lower().strip()
            if point_normalized not in seen:
                seen.add(point_normalized)
                unique_points.append(point)
        
        return unique_points[:max_points]
    
    def scrape_website(self, url: str, max_pages: int = 5) -> WebsiteData:
        """
        Scrape a website intelligently:
        1. Get sitemap
        2. Rank pages by importance
        3. Scrape top N pages
        4. Extract key points
        
        Args:
            url: Website URL to scrape
            max_pages: Maximum number of pages to scrape (default: 5)
            
        Returns:
            WebsiteData object with scraped content and key points
        """
        # Step 1: Get sitemap
        try:
            all_pages = self.get_sitemap(url)
            if all_pages:
                # Rank pages by importance
                ranked_pages = self.rank_pages_by_importance(all_pages)
                # Get top N pages
                pages_to_scrape = [url] + ranked_pages[1:max_pages]  # Include homepage + top pages
            else:
                pages_to_scrape = [url]  # Fallback to just homepage
        except:
            pages_to_scrape = [url]  # Fallback to just homepage
        
        # Step 2: Scrape each page
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        all_content = []
        combined_metadata = {}
        
        for page_url in pages_to_scrape[:max_pages]:
            try:
                payload = {
                    "url": page_url,
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
                content = page_data.get("markdown", "")
                
                if content:
                    all_content.append(f"## {page_url}\n\n{content}\n\n")
                
                # Collect metadata from homepage
                if page_url == url:
                    combined_metadata = page_data.get("metadata", {})
                    
            except Exception as e:
                print(f"Failed to scrape {page_url}: {e}")
                continue
        
        # Step 3: Combine content
        combined_content = "\n".join(all_content)
        
        # Step 4: Extract key points
        key_points = self.extract_key_points(combined_content, max_points=10)
        
        return WebsiteData(
            url=url,
            title=combined_metadata.get("title"),
            description=combined_metadata.get("description"),
            content=combined_content,
            key_points=key_points,
            pages_scraped=pages_to_scrape[:max_pages],
            metadata=combined_metadata,
            scraped_at=datetime.now()
        )
    
    def crawl_website(self, url: str, max_pages: int = 5) -> list[WebsiteData]:
        """
        Crawl multiple pages of a website.
        
        Args:
            url: Starting URL
            max_pages: Maximum number of pages to crawl
            
        Returns:
            List of WebsiteData objects
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "url": url,
            "limit": max_pages,
            "scrapeOptions": {
                "formats": ["markdown"],
                "onlyMainContent": True
            }
        }
        
        with httpx.Client(timeout=settings.REQUEST_TIMEOUT * 2) as client:
            response = client.post(
                f"{self.base_url}/crawl",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
        
        # Parse crawl results
        results = []
        for page in data.get("data", []):
            results.append(WebsiteData(
                url=page.get("url", url),
                title=page.get("metadata", {}).get("title"),
                description=page.get("metadata", {}).get("description"),
                content=page.get("markdown", ""),
                metadata=page.get("metadata", {}),
                scraped_at=datetime.now()
            ))
        
        return results
