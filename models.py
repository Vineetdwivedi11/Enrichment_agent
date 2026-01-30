"""Data models for Enrichment Agent."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
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
    company_name: str
    url: str
    schema_used: str
    prompt_used: str
    extracted_data: Dict[str, Any]
    raw_content: Optional[str] = None
    enriched_at: datetime = Field(default_factory=datetime.now)
    model_used: str
    
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


class WebsiteContent(BaseModel):
    """Scraped website content."""
    url: str
    title: Optional[str] = None
    markdown: str
    metadata: Dict[str, Any] = {}
    scraped_at: datetime = Field(default_factory=datetime.now)
