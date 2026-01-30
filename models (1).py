"""Data models for research agent."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, HttpUrl


class WebsiteData(BaseModel):
    """Scraped website data."""
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    key_points: List[str] = []
    pages_scraped: List[str] = []
    metadata: Dict[str, Any] = {}
    scraped_at: datetime


class LinkedInCompanyData(BaseModel):
    """LinkedIn company profile data."""
    name: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    headquarters: Optional[str] = None
    founded: Optional[str] = None
    specialties: List[str] = []
    description: Optional[str] = None
    website: Optional[str] = None
    employee_count: Optional[int] = None
    source: str = "bright_data"  # bright_data, apify, or joeyism


class LinkedInPost(BaseModel):
    """LinkedIn post data."""
    post_url: Optional[str] = None
    author: Optional[str] = None
    content: Optional[str] = None
    engagement: Dict[str, int] = {}
    published_at: Optional[datetime] = None
    source: str = "bright_data"  # bright_data or apify


class ProspectResearch(BaseModel):
    """Complete research data for a prospect."""
    company_name: str
    website_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    website_data: Optional[WebsiteData] = None
    linkedin_company_data: Optional[LinkedInCompanyData] = None
    linkedin_posts: List[LinkedInPost] = []
    timestamp: datetime
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.model_dump()
