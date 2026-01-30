"""Discord notification sender with multi-webhook support."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

import httpx

from .config import settings
from .models import EmailOpenEvent


class DiscordNotifier:
    """
    Send notifications to Discord via webhook(s).
    
    Supports:
    - Single webhook (via DISCORD_WEBHOOK_URL env var)
    - Multiple webhooks (via discord_config.json file)
    """
    
    def __init__(self):
        self.webhooks = self._load_webhooks()
        
        if not self.webhooks:
            raise ValueError("No Discord webhooks configured. Set DISCORD_WEBHOOK_URL or create discord_config.json")
        
        self.client = httpx.AsyncClient(timeout=10.0)
    
    def _load_webhooks(self) -> List[Dict[str, str]]:
        """
        Load webhook configurations.
        
        Priority:
        1. discord_config.json file (multiple webhooks)
        2. DISCORD_WEBHOOK_URL env var (single webhook)
        
        Returns:
            List of webhook configs: [{"url": "...", "name": "..."}, ...]
        """
        webhooks = []
        
        # Try loading from config file first
        config_file = Path(settings.DISCORD_CONFIG_FILE)
        if config_file.exists():
            try:
                with open(config_file) as f:
                    config = json.load(f)
                    
                # Support two formats:
                # 1. {"webhooks": [{"url": "...", "name": "..."}]}
                # 2. {"default": "url", "sales": "url"}
                
                if "webhooks" in config:
                    webhooks = config["webhooks"]
                else:
                    # Convert dict format to list format
                    webhooks = [
                        {"url": url, "name": name}
                        for name, url in config.items()
                    ]
                
                print(f"Loaded {len(webhooks)} Discord webhooks from {config_file}")
                return webhooks
            except Exception as e:
                print(f"Failed to load Discord config file: {e}")
        
        # Fallback to single webhook from env var
        if settings.DISCORD_WEBHOOK_URL:
            webhooks = [{
                "url": settings.DISCORD_WEBHOOK_URL,
                "name": "default"
            }]
            print(f"Using Discord webhook from environment variable")
        
        return webhooks
    
    async def send_email_open_notification(self, event: EmailOpenEvent, webhook_name: Optional[str] = None):
        """
        Send Discord notification for email open event.
        
        Args:
            event: Email open event
            webhook_name: Specific webhook to use (optional, sends to all if None)
        """
        # Create Discord embed
        embed = {
            "title": "📧 Email Opened",
            "color": 3066993,  # Green color
            "fields": [
                {
                    "name": "Lead",
                    "value": event.lead_name,
                    "inline": True
                },
                {
                    "name": "Recipient",
                    "value": event.recipient,
                    "inline": True
                },
                {
                    "name": "Subject",
                    "value": event.subject[:100] + ("..." if len(event.subject) > 100 else ""),
                    "inline": False
                },
                {
                    "name": "Opens Count",
                    "value": str(event.opens_count),
                    "inline": True
                },
                {
                    "name": "Opened At",
                    "value": event.opened_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "inline": True
                }
            ],
            "footer": {
                "text": f"Email ID: {event.email_id}"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Add link to Close.io if we have lead ID
        if event.lead_id:
            embed["url"] = f"https://app.close.com/lead/{event.lead_id}/"
        
        payload = {
            "embeds": [embed]
        }
        
        # Send to specified webhook or all webhooks
        webhooks_to_use = self.webhooks
        if webhook_name:
            webhooks_to_use = [w for w in self.webhooks if w["name"] == webhook_name]
        
        # Send to all matching webhooks
        for webhook in webhooks_to_use:
            try:
                response = await self.client.post(webhook["url"], json=payload)
                response.raise_for_status()
            except Exception as e:
                print(f"Failed to send to webhook '{webhook['name']}': {e}")
    
    async def send_text_notification(self, message: str, webhook_name: Optional[str] = None):
        """Send a simple text notification."""
        payload = {
            "content": message
        }
        
        webhooks_to_use = self.webhooks
        if webhook_name:
            webhooks_to_use = [w for w in self.webhooks if w["name"] == webhook_name]
        
        for webhook in webhooks_to_use:
            try:
                response = await self.client.post(webhook["url"], json=payload)
                response.raise_for_status()
            except Exception as e:
                print(f"Failed to send to webhook '{webhook['name']}': {e}")
    
    async def send_error_notification(self, error: str, webhook_name: Optional[str] = None):
        """Send error notification to Discord."""
        embed = {
            "title": "⚠️ Error in Email Notifier",
            "description": error,
            "color": 15158332,  # Red color
            "timestamp": datetime.now().isoformat()
        }
        
        payload = {
            "embeds": [embed]
        }
        
        webhooks_to_use = self.webhooks
        if webhook_name:
            webhooks_to_use = [w for w in self.webhooks if w["name"] == webhook_name]
        
        for webhook in webhooks_to_use:
            try:
                response = await self.client.post(webhook["url"], json=payload)
                response.raise_for_status()
            except:
                pass  # Don't fail on error notifications
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
