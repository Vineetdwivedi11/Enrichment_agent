"""Email Open Discord Notifier package."""

from .config import settings
from .models import EmailOpenEvent, WebhookEvent, NotificationRecord
from .closeio import CloseIOClient
from .discord_notifier import DiscordNotifier
from .cache import EventCache
from .database import (
    init_db, 
    log_email_open, 
    get_recent_opens,
    get_opens_by_date,
    get_opens_by_lead,
    get_analytics_summary,
    get_top_leads,
    get_opens_by_time_of_day,
    get_opens_by_day_of_week,
    get_engagement_metrics
)

__all__ = [
    "settings",
    "EmailOpenEvent",
    "WebhookEvent",
    "NotificationRecord",
    "CloseIOClient",
    "DiscordNotifier",
    "EventCache",
    "init_db",
    "log_email_open",
    "get_recent_opens",
    "get_opens_by_date",
    "get_opens_by_lead",
    "get_analytics_summary",
    "get_top_leads",
    "get_opens_by_time_of_day",
    "get_opens_by_day_of_week",
    "get_engagement_metrics",
]
