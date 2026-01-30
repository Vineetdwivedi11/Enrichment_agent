"""Data models for Email Open Discord Notifier and Enrichment Agent."""

from datetime import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field, ConfigDict
import json


class WebhookEvent(BaseModel):
    """Close.io webhook event."""
    event: dict
    organization_id: str


class EmailOpenEvent(BaseModel):
    """Email open event details."""
    email_id: str
    lead_id: str
    lead_name: str
    subject: str
    recipient: str
    opens_count: int
    opened_at: datetime
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "email_id": self.email_id,
            "lead_id": self.lead_id,
            "lead_name": self.lead_name,
            "subject": self.subject,
            "recipient": self.recipient,
            "opens_count": self.opens_count,
            "opened_at": self.opened_at.isoformat()
        }


class NotificationRecord(BaseModel):
    """Record of sent notification."""
    email_id: str
    notified_at: datetime
    lead_name: str
    subject: str


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


class WebsiteContent(BaseModel):
    """Scraped website content."""
    url: str
    title: Optional[str] = None
    markdown: str
    metadata: Dict[str, Any] = {}
    scraped_at: datetime = Field(default_factory=datetime.now)
