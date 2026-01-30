"""Close.io API client."""

import hashlib
import hmac
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import httpx

from .config import settings


class CloseIOClient:
    """Client for Close.io API."""
    
    def __init__(self):
        self.api_key = settings.CLOSEIO_API_KEY
        self.base_url = settings.CLOSEIO_API_URL
        
        if not self.api_key:
            raise ValueError("CLOSEIO_API_KEY not set")
        
        self.client = httpx.AsyncClient(
            auth=(self.api_key, ""),
            timeout=30.0
        )
    
    async def get_lead(self, lead_id: str) -> Dict[str, Any]:
        """Get lead details."""
        response = await self.client.get(f"{self.base_url}/lead/{lead_id}/")
        response.raise_for_status()
        return response.json()
    
    async def get_email_activity(self, email_id: str) -> Dict[str, Any]:
        """Get email activity details."""
        response = await self.client.get(f"{self.base_url}/activity/email/{email_id}/")
        response.raise_for_status()
        return response.json()
    
    async def get_recent_email_opens(self, minutes: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent email open events from event log.
        
        This is used for polling mode as a fallback.
        """
        # Calculate time range
        now = datetime.now()
        lookback = now - timedelta(minutes=minutes)
        
        # Query event log for email activity updates
        params = {
            "object_type": "activity.email",
            "action": "updated",
            "date_created__gt": lookback.isoformat(),
            "_limit": 100
        }
        
        response = await self.client.get(
            f"{self.base_url}/event/",
            params=params
        )
        response.raise_for_status()
        events = response.json().get("data", [])
        
        # Filter for email opens and extract relevant data
        email_opens = []
        for event in events:
            changed_fields = event.get("changed_fields", [])
            
            # Check if 'opens' field was updated
            if "opens" not in changed_fields:
                continue
            
            data = event.get("data", {})
            
            # Skip if no opens recorded
            opens = data.get("opens", [])
            if not opens:
                continue
            
            # Get latest open time
            latest_open = opens[-1] if opens else {}
            
            email_opens.append({
                "email_id": data.get("id"),
                "lead_id": data.get("lead_id"),
                "subject": data.get("subject", ""),
                "recipient": data.get("to", [{}])[0].get("email", "") if data.get("to") else "",
                "opens_count": len(opens),
                "opened_at": latest_open.get("opened_at", datetime.now().isoformat())
            })
        
        # Get lead names for each event
        for event in email_opens:
            try:
                lead = await self.get_lead(event["lead_id"])
                event["lead_name"] = lead.get("display_name", "Unknown")
            except:
                event["lead_name"] = "Unknown"
        
        return email_opens
    
    async def create_webhook_subscription(
        self, 
        webhook_url: str,
        events: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a webhook subscription in Close.io.
        
        Args:
            webhook_url: URL to receive webhooks
            events: List of events to subscribe to
        """
        if events is None:
            # Subscribe to email activity updates
            events = [
                {
                    "object_type": "activity.email",
                    "action": "updated"
                }
            ]
        
        payload = {
            "url": webhook_url,
            "events": events,
            "verify_ssl": True
        }
        
        response = await self.client.post(
            f"{self.base_url}/webhook_subscription/",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def list_webhook_subscriptions(self) -> List[Dict[str, Any]]:
        """List all webhook subscriptions."""
        response = await self.client.get(f"{self.base_url}/webhook_subscription/")
        response.raise_for_status()
        return response.json().get("data", [])
    
    def verify_webhook_signature(
        self, 
        payload: bytes, 
        timestamp: str, 
        signature: str
    ) -> bool:
        """
        Verify Close.io webhook signature.
        
        Close.io signs webhooks with HMAC SHA256.
        """
        if not settings.CLOSEIO_WEBHOOK_SECRET:
            return True  # Skip verification if no secret configured
        
        # Concatenate timestamp and payload
        message = timestamp.encode() + payload
        
        # Calculate HMAC
        expected_signature = hmac.new(
            settings.CLOSEIO_WEBHOOK_SECRET.encode(),
            message,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
