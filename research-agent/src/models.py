"""Data models for Email Open Discord Notifier and Enrichment Agent."""

from datetime import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field, ConfigDict
import json



class ExtractionSchema(BaseModel):
    """Schema definition for data extraction."""
    name: str
    description: str
    fields: Dict[str, Dict[str, Any]]
    
    @classmethod
    def from_file(cls, filepath: str) -> "ExtractionSchema":
        """Load schema from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(**data)


class PromptTemplate(BaseModel):
    """Prompt template with variables."""
    name: str
    content: str
    variables: List[str] = []
    
    @classmethod
    def from_file(cls, filepath: str) -> "PromptTemplate":
        """Load prompt from file."""
        import re
        from pathlib import Path
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        variables = re.findall(r'\{\{\s*(\w+)\s*\}\}', content)
        
        return cls(
            name=Path(filepath).stem,
            content=content,
            variables=list(set(variables))
        )
    
    def render(self, **kwargs) -> str:
        """Render template with variables."""
        from jinja2 import Template
        template = Template(self.content)
        return template.render(**kwargs)


class EnrichmentResult(BaseModel):
    """Result of enrichment process."""
    model_config = ConfigDict(protected_namespaces=())
    
    company_name: str
    url: str
    schema_used: str
    prompt_used: str
    extracted_data: Dict[str, Any]
    raw_content: Optional[str] = None
    enriched_at: datetime = Field(default_factory=datetime.now)
    model_used: str = Field(description="The AI model used for extraction")
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "company_name": self.company_name,
            "url": self.url,
            "schema_used": self.schema_used,
            "prompt_used": self.prompt_used,
            "extracted_data": self.extracted_data,
            "enriched_at": self.enriched_at.isoformat(),
            "model_used": self.model_used
        }


class WebsiteData(BaseModel):
    """Scraped website data."""
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    key_points: List[str] = []
    pages_scraped: List[str] = []
    metadata: Dict[str, Any] = {}
    scraped_at: datetime = Field(default_factory=datetime.now)


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
