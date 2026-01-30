"""Event cache for preventing duplicate notifications.

For 24/7 operation: Cache entries expire after 24 hours.
No database persistence needed since service runs continuously.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional

from .config import settings


class EventCache:
    """
    In-memory cache to track notified emails and prevent duplicates.
    
    Designed for 24/7 operation:
    - Entries expire after 24 hours
    - No persistence needed (service runs continuously)
    - Automatic cleanup of old entries
    """
    
    def __init__(self):
        self._cache: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()
        # 24 hours for 24/7 operation
        self._retention_hours = settings.CACHE_RETENTION_HOURS
    
    def is_notified(self, email_id: str) -> bool:
        """Check if email has already been notified within last 24 hours."""
        # Clean old entries first
        self._cleanup_old_entries()
        
        return email_id in self._cache
    
    async def mark_notified(self, email_id: str):
        """Mark email as notified."""
        async with self._lock:
            self._cache[email_id] = datetime.now()
    
    def _cleanup_old_entries(self):
        """Remove entries older than retention period (24 hours)."""
        cutoff = datetime.now() - timedelta(hours=self._retention_hours)
        
        # Remove old entries
        to_remove = [
            email_id 
            for email_id, timestamp in self._cache.items()
            if timestamp < cutoff
        ]
        
        for email_id in to_remove:
            del self._cache[email_id]
    
    async def get_stats(self) -> Dict[str, any]:
        """Get cache statistics."""
        async with self._lock:
            oldest_entry = min(self._cache.values()) if self._cache else None
            
            return {
                "cache_size": len(self._cache),
                "total_count": len(self._cache),
                "oldest_entry": oldest_entry.isoformat() if oldest_entry else None,
                "retention_hours": self._retention_hours
            }
    
    async def clear(self):
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
