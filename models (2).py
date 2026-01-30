"""Data models for Email Open Discord Notifier."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


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
