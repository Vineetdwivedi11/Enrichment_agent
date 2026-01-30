"""LinkedIn scraper with multiple fallback options.

Priority order:
1. Bright Data API (paid, most reliable)
2. Apify Harvest Data API (subscription-based)
3. joeyism/linkedin_scraper (open source fallback)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

import httpx

from .config import settings
from .models import LinkedInCompanyData, LinkedInPost


class LinkedInScraper:
    """Scrape LinkedIn data using multiple sources with fallback."""
    
    def __init__(self):
        # Bright Data (primary)
        self.brightdata_key = settings.BRIGHTDATA_API_KEY
        self.brightdata_url = settings.BRIGHTDATA_API_URL
        
        # Apify (secondary)
        self.apify_key = settings.APIFY_API_KEY
        self.apify_url = "https://api.apify.com/v2"
        
        # joeyism scraper (tertiary/fallback)
        self.use_joeyism = settings.USE_JOEYISM_FALLBACK
    
    async def scrape_company(self, linkedin_url: str) -> LinkedInCompanyData:
        """
        Scrape LinkedIn company profile with fallback.
        
        Tries in order: Bright Data -> Apify -> joeyism
        
        Args:
            linkedin_url: LinkedIn company URL
            
        Returns:
            LinkedInCompanyData object
        """
        # Try Bright Data first
        if self.brightdata_key:
            try:
                return await self._scrape_company_brightdata(linkedin_url)
            except Exception as e:
                print(f"Bright Data failed: {e}, trying Apify...")
        
        # Try Apify second
        if self.apify_key:
            try:
                return await self._scrape_company_apify(linkedin_url)
            except Exception as e:
                print(f"Apify failed: {e}, trying joeyism...")
        
        # Try joeyism as last resort
        if self.use_joeyism:
            try:
                return await self._scrape_company_joeyism(linkedin_url)
            except Exception as e:
                print(f"joeyism scraper failed: {e}")
                raise ValueError("All LinkedIn scraping methods failed")
        
        raise ValueError("No LinkedIn scraping method available")
    
    async def _scrape_company_brightdata(self, linkedin_url: str) -> LinkedInCompanyData:
        """Scrape using Bright Data API."""
        headers = {
            "Authorization": f"Bearer {self.brightdata_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "url": linkedin_url,
            "include_employees": False
        }
        
        async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{self.brightdata_url}/linkedin/company",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
        
        company_data = data.get("data", [{}])[0] if data.get("data") else {}
        
        return LinkedInCompanyData(
            name=company_data.get("name"),
            industry=company_data.get("industry"),
            company_size=company_data.get("company_size"),
            headquarters=company_data.get("headquarters"),
            founded=company_data.get("founded"),
            specialties=company_data.get("specialties", []),
            description=company_data.get("description"),
            website=company_data.get("website"),
            employee_count=company_data.get("employee_count"),
            source="bright_data"
        )
    
    async def _scrape_company_apify(self, linkedin_url: str) -> LinkedInCompanyData:
        """Scrape using Apify Harvest Data API."""
        headers = {
            "Authorization": f"Bearer {self.apify_key}",
            "Content-Type": "application/json"
        }
        
        # Start actor run
        payload = {
            "startUrls": [{"url": linkedin_url}],
            "proxyConfiguration": {"useApifyProxy": True}
        }
        
        async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT * 2) as client:
            # Start the run
            response = await client.post(
                f"{self.apify_url}/acts/apify~linkedin-company-scraper/runs",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            run_data = response.json()
            run_id = run_data.get("data", {}).get("id")
            
            # Wait for completion (poll for status)
            max_attempts = 30
            for _ in range(max_attempts):
                await asyncio.sleep(2)
                status_response = await client.get(
                    f"{self.apify_url}/acts/apify~linkedin-company-scraper/runs/{run_id}",
                    headers=headers
                )
                status_response.raise_for_status()
                status_data = status_response.json()
                
                status = status_data.get("data", {}).get("status")
                if status == "SUCCEEDED":
                    break
            
            # Get results
            results_response = await client.get(
                f"{self.apify_url}/acts/apify~linkedin-company-scraper/runs/{run_id}/dataset/items",
                headers=headers
            )
            results_response.raise_for_status()
            results = results_response.json()
        
        company_data = results[0] if results else {}
        
        return LinkedInCompanyData(
            name=company_data.get("name"),
            industry=company_data.get("industry"),
            company_size=company_data.get("companySize"),
            headquarters=company_data.get("headquarters"),
            founded=company_data.get("founded"),
            specialties=company_data.get("specialties", []),
            description=company_data.get("description"),
            website=company_data.get("website"),
            employee_count=self._parse_employee_count(company_data.get("companySize")),
            source="apify"
        )
    
    async def _scrape_company_joeyism(self, linkedin_url: str) -> LinkedInCompanyData:
        """Scrape using joeyism/linkedin_scraper library."""
        try:
            from linkedin_scraper import CompanyScraper, BrowserManager
            
            async with BrowserManager(headless=True) as browser:
                # Load session if available
                try:
                    await browser.load_session("linkedin_session.json")
                except:
                    pass  # No session available
                
                scraper = CompanyScraper(browser.page)
                company = await scraper.scrape(linkedin_url)
                
                return LinkedInCompanyData(
                    name=company.name,
                    industry=company.industry,
                    company_size=company.company_size,
                    headquarters=company.headquarters,
                    founded=company.founded_year,
                    specialties=company.specialties if hasattr(company, 'specialties') else [],
                    description=company.about,
                    website=company.website,
                    employee_count=None,
                    source="joeyism"
                )
        except ImportError:
            raise ValueError("joeyism linkedin_scraper not installed. Run: pip install linkedin-scraper")
    
    async def get_company_posts(
        self, 
        linkedin_url: str, 
        limit: int = 10
    ) -> List[LinkedInPost]:
        """
        Get recent posts from LinkedIn company.
        
        Tries Bright Data -> Apify Harvest Data
        
        Args:
            linkedin_url: LinkedIn company URL
            limit: Maximum number of posts
            
        Returns:
            List of LinkedInPost objects
        """
        # Try Bright Data first
        if self.brightdata_key:
            try:
                return await self._get_posts_brightdata(linkedin_url, limit)
            except Exception as e:
                print(f"Bright Data posts failed: {e}, trying Apify...")
        
        # Try Apify Harvest Data
        if self.apify_key:
            try:
                return await self._get_posts_apify(linkedin_url, limit)
            except Exception as e:
                print(f"Apify posts failed: {e}")
                return []
        
        return []
    
    async def _get_posts_brightdata(
        self, 
        linkedin_url: str, 
        limit: int
    ) -> List[LinkedInPost]:
        """Get posts using Bright Data API."""
        headers = {
            "Authorization": f"Bearer {self.brightdata_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "url": linkedin_url,
            "limit": limit
        }
        
        async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{self.brightdata_url}/linkedin/posts",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
        
        posts = []
        for post_data in data.get("data", []):
            posts.append(LinkedInPost(
                post_url=post_data.get("post_url"),
                author=post_data.get("author"),
                content=post_data.get("content"),
                engagement={
                    "likes": post_data.get("likes", 0),
                    "comments": post_data.get("comments", 0),
                    "shares": post_data.get("shares", 0)
                },
                published_at=self._parse_date(post_data.get("published_at")),
                source="bright_data"
            ))
        
        return posts
    
    async def _get_posts_apify(
        self, 
        linkedin_url: str, 
        limit: int
    ) -> List[LinkedInPost]:
        """Get posts using Apify Harvest Data API."""
        headers = {
            "Authorization": f"Bearer {self.apify_key}",
            "Content-Type": "application/json"
        }
        
        # Use the LinkedIn posts scraper
        payload = {
            "startUrls": [{"url": linkedin_url + "/posts"}],
            "maxPosts": limit,
            "proxyConfiguration": {"useApifyProxy": True}
        }
        
        async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT * 2) as client:
            # Start the run
            response = await client.post(
                f"{self.apify_url}/acts/apify~linkedin-posts-scraper/runs",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            run_data = response.json()
            run_id = run_data.get("data", {}).get("id")
            
            # Wait for completion
            max_attempts = 30
            for _ in range(max_attempts):
                await asyncio.sleep(2)
                status_response = await client.get(
                    f"{self.apify_url}/acts/apify~linkedin-posts-scraper/runs/{run_id}",
                    headers=headers
                )
                status_response.raise_for_status()
                status_data = status_response.json()
                
                if status_data.get("data", {}).get("status") == "SUCCEEDED":
                    break
            
            # Get results
            results_response = await client.get(
                f"{self.apify_url}/acts/apify~linkedin-posts-scraper/runs/{run_id}/dataset/items",
                headers=headers
            )
            results_response.raise_for_status()
            results = results_response.json()
        
        posts = []
        for post_data in results[:limit]:
            posts.append(LinkedInPost(
                post_url=post_data.get("url"),
                author=post_data.get("author"),
                content=post_data.get("text"),
                engagement={
                    "likes": post_data.get("likes", 0),
                    "comments": post_data.get("comments", 0),
                    "shares": post_data.get("shares", 0)
                },
                published_at=self._parse_date(post_data.get("publishedAt")),
                source="apify"
            ))
        
        return posts
    
    async def scrape_profile(self, profile_url: str) -> Dict[str, Any]:
        """
        Scrape LinkedIn personal profile.
        
        Args:
            profile_url: LinkedIn profile URL
            
        Returns:
            Profile data dictionary
        """
        # Try Bright Data first
        if self.brightdata_key:
            try:
                return await self._scrape_profile_brightdata(profile_url)
            except Exception as e:
                print(f"Bright Data profile failed: {e}")
        
        return {}
    
    async def _scrape_profile_brightdata(self, profile_url: str) -> Dict[str, Any]:
        """Scrape profile using Bright Data."""
        headers = {
            "Authorization": f"Bearer {self.brightdata_key}",
            "Content-Type": "application/json"
        }
        
        payload = {"url": profile_url}
        
        async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{self.brightdata_url}/linkedin/profile",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
        
        return data.get("data", [{}])[0] if data.get("data") else {}
    
    @staticmethod
    def _parse_date(date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return None
    
    @staticmethod
    def _parse_employee_count(size_str: str) -> Optional[int]:
        """Parse employee count from size string like '201-500 employees'."""
        if not size_str:
            return None
        try:
            # Extract first number from string
            import re
            numbers = re.findall(r'\d+', size_str)
            if numbers:
                return int(numbers[0])
        except:
            pass
        return None
