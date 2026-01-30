"""
Email Open Discord Notifier
Real-time Discord notifications for email opens in Close.io CRM

ARCHITECTURE:
- In-memory cache (24-hour expiry) → Duplicate prevention
- SQLite database → Analytics & historical tracking
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse

from src.config import settings
from src.models import EmailOpenEvent
from src.closeio import CloseIOClient
from src.discord_notifier import DiscordNotifier
from src.cache import EventCache
from src.database import (
    init_db,
    log_email_open,
    get_recent_opens,
    get_opens_by_date,
    get_analytics_summary,
    get_top_leads,
    get_opens_by_time_of_day,
    get_opens_by_day_of_week,
    get_engagement_metrics
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    # Initialize database for analytics
    await init_db()
    
    # Initialize cache (in-memory, 24-hour retention for duplicate prevention)
    app.state.cache = EventCache()
    
    # Initialize Close.io client
    app.state.closeio = CloseIOClient()
    
    # Initialize Discord notifier (supports multi-webhook config)
    app.state.discord = DiscordNotifier()
    
    # Start background polling task if webhooks not available
    if settings.POLLING_ENABLED:
        app.state.polling_task = asyncio.create_task(poll_email_opens(app))
    
    print("=" * 70)
    print("Email Open Discord Notifier - RUNNING 24/7")
    print("=" * 70)
    print(f"Cache: In-memory, {settings.CACHE_RETENTION_HOURS}h retention (duplicate prevention)")
    print(f"Database: SQLite analytics storage (all opens logged)")
    print(f"Polling: {'Enabled' if settings.POLLING_ENABLED else 'Disabled'}")
    if settings.POLLING_ENABLED:
        print(f"Polling interval: {settings.POLLING_INTERVAL_SECONDS}s")
    print("=" * 70)
    
    yield
    
    # Cleanup
    if settings.POLLING_ENABLED and hasattr(app.state, 'polling_task'):
        app.state.polling_task.cancel()


app = FastAPI(
    title="Email Open Discord Notifier",
    description="Real-time Discord notifications for Close.io email opens (24/7 operation)",
    version="2.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Email Open Discord Notifier",
        "status": "running",
        "webhook_enabled": not settings.POLLING_ENABLED,
        "polling_enabled": settings.POLLING_ENABLED
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "config": {
            "closeio_configured": bool(settings.CLOSEIO_API_KEY),
            "discord_configured": bool(settings.DISCORD_WEBHOOK_URL),
            "polling_interval": settings.POLLING_INTERVAL_SECONDS,
        }
    }


@app.post("/webhook/closeio")
async def closeio_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Receive Close.io webhook events.
    
    Close.io will POST events to this endpoint when configured.
    We filter for email open events and send Discord notifications.
    """
    # Verify signature if configured
    if settings.CLOSEIO_WEBHOOK_SECRET:
        signature = request.headers.get("close-sig-hash")
        timestamp = request.headers.get("close-sig-timestamp")
        
        if not signature or not timestamp:
            raise HTTPException(status_code=401, detail="Missing signature headers")
        
        # Verify webhook signature
        body = await request.body()
        if not app.state.closeio.verify_webhook_signature(body, timestamp, signature):
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse webhook payload
    payload = await request.json()
    
    # Process event in background
    background_tasks.add_task(process_webhook_event, app, payload)
    
    return {"status": "received"}


async def process_webhook_event(app: FastAPI, payload: dict):
    """Process a webhook event from Close.io."""
    try:
        event = payload.get("event", {})
        
        # Check if this is an email activity update
        object_type = event.get("object_type")
        action = event.get("action")
        
        if object_type != "activity.email" or action != "updated":
            return
        
        # Check if email was opened
        data = event.get("data", {})
        changed_fields = event.get("changed_fields", [])
        
        # Close.io tracks opens in the 'opens' field
        if "opens" not in changed_fields:
            return
        
        # Extract email details
        email_id = data.get("id")
        lead_id = data.get("lead_id")
        subject = data.get("subject", "")
        recipient = data.get("to", [{}])[0].get("email", "") if data.get("to") else ""
        opens_count = len(data.get("opens", []))
        
        # Check cache to prevent duplicate notifications
        if app.state.cache.is_notified(email_id):
            return
        
        # Get lead details
        lead_info = await app.state.closeio.get_lead(lead_id)
        lead_name = lead_info.get("display_name", "Unknown")
        
        # Create event
        email_event = EmailOpenEvent(
            email_id=email_id,
            lead_id=lead_id,
            lead_name=lead_name,
            subject=subject,
            recipient=recipient,
            opens_count=opens_count,
            opened_at=datetime.now()
        )
        
        # Send Discord notification
        await app.state.discord.send_email_open_notification(email_event)
        
        # Log to database for analytics
        await log_email_open(
            email_id=email_id,
            lead_id=lead_id,
            lead_name=lead_name,
            subject=subject,
            recipient=recipient,
            opens_count=opens_count,
            opened_at=email_event.opened_at
        )
        
        # Mark as notified in cache (prevents duplicate notifications)
        await app.state.cache.mark_notified(email_id)
        
    except Exception as e:
        # Log error but don't fail the webhook
        print(f"Error processing webhook event: {e}")


async def poll_email_opens(app: FastAPI):
    """
    Background task to poll Close.io for email opens.
    
    Used as fallback if webhooks are not configured or not working.
    """
    print(f"Starting polling task (interval: {settings.POLLING_INTERVAL_SECONDS}s)")
    
    while True:
        try:
            await asyncio.sleep(settings.POLLING_INTERVAL_SECONDS)
            
            # Get recent email activities from event log
            events = await app.state.closeio.get_recent_email_opens(
                minutes=settings.POLLING_LOOKBACK_MINUTES
            )
            
            for event in events:
                email_id = event.get("email_id")
                
                # Check if already notified
                if app.state.cache.is_notified(email_id):
                    continue
                
                # Create email event
                email_event = EmailOpenEvent(
                    email_id=email_id,
                    lead_id=event.get("lead_id"),
                    lead_name=event.get("lead_name", "Unknown"),
                    subject=event.get("subject", ""),
                    recipient=event.get("recipient", ""),
                    opens_count=event.get("opens_count", 1),
                    opened_at=datetime.fromisoformat(event.get("opened_at"))
                )
                
                # Send notification
                await app.state.discord.send_email_open_notification(email_event)
                
                # Log to database for analytics
                await log_email_open(
                    email_id=email_id,
                    lead_id=email_event.lead_id,
                    lead_name=email_event.lead_name,
                    subject=email_event.subject,
                    recipient=email_event.recipient,
                    opens_count=email_event.opens_count,
                    opened_at=email_event.opened_at
                )
                
                # Mark as notified (prevents duplicate notifications)
                await app.state.cache.mark_notified(email_id)
                
        except asyncio.CancelledError:
            print("Polling task cancelled")
            break
        except Exception as e:
            print(f"Error in polling task: {e}")
            # Continue polling even on error


@app.get("/stats")
async def get_stats(request: Request):
    """Get notification statistics."""
    cache_stats = await request.app.state.cache.get_stats()
    
    return {
        "total_notifications": cache_stats["total_count"],
        "cache_size": cache_stats["cache_size"],
        "oldest_entry": cache_stats["oldest_entry"],
    }


@app.post("/test/notification")
async def test_notification(request: Request):
    """Send a test Discord notification."""
    test_event = EmailOpenEvent(
        email_id="test_123",
        lead_id="lead_test",
        lead_name="Test Company",
        subject="Test Email Subject",
        recipient="test@example.com",
        opens_count=1,
        opened_at=datetime.now()
    )
    
    await request.app.state.discord.send_email_open_notification(test_event)
    
    return {"status": "Test notification sent"}


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/analytics/summary")
async def get_analytics_summary_endpoint():
    """
    Get summary analytics of all email opens.
    
    Returns:
        - total_opens: Total number of email open events
        - unique_emails: Number of unique emails opened
        - unique_leads: Number of unique leads/companies
    """
    summary = await get_analytics_summary()
    return summary


@app.get("/analytics/recent")
async def get_recent_opens_endpoint(limit: int = 50):
    """
    Get recent email opens.
    
    Args:
        limit: Number of recent opens to return (default: 50, max: 500)
    """
    limit = min(limit, 500)  # Cap at 500
    opens = await get_recent_opens(limit=limit)
    
    return {
        "count": len(opens),
        "opens": [
            {
                "email_id": open.email_id,
                "lead_id": open.lead_id,
                "lead_name": open.lead_name,
                "subject": open.subject,
                "recipient": open.recipient,
                "opens_count": open.opens_count,
                "opened_at": open.opened_at.isoformat(),
                "notified_at": open.notified_at.isoformat()
            }
            for open in opens
        ]
    }


@app.get("/analytics/by-date")
async def get_opens_by_date_endpoint(
    start_date: str,
    end_date: str
):
    """
    Get email opens within a date range.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Example:
        /analytics/by-date?start_date=2025-01-01&end_date=2025-01-31
    """
    opens = await get_opens_by_date(start_date, end_date)
    
    return {
        "start_date": start_date,
        "end_date": end_date,
        "count": len(opens),
        "opens": [
            {
                "email_id": open.email_id,
                "lead_id": open.lead_id,
                "lead_name": open.lead_name,
                "subject": open.subject,
                "recipient": open.recipient,
                "opens_count": open.opens_count,
                "opened_at": open.opened_at.isoformat(),
                "date_opened": open.date_opened
            }
            for open in opens
        ]
    }


@app.get("/analytics/by-lead/{lead_id}")
async def get_opens_by_lead_endpoint(lead_id: str):
    """
    Get all email opens for a specific lead/company.
    
    Args:
        lead_id: Close.io lead ID
        
    Example:
        /analytics/by-lead/lead_abc123
    """
    opens = await get_opens_by_lead(lead_id)
    
    if not opens:
        raise HTTPException(status_code=404, detail="No email opens found for this lead")
    
    return {
        "lead_id": lead_id,
        "lead_name": opens[0].lead_name if opens else None,
        "total_opens": len(opens),
        "opens": [
            {
                "email_id": open.email_id,
                "subject": open.subject,
                "recipient": open.recipient,
                "opens_count": open.opens_count,
                "opened_at": open.opened_at.isoformat()
            }
            for open in opens
        ]
    }


@app.get("/analytics/export")
async def export_analytics():
    """
    Export all email open data as CSV.
    
    Returns CSV file with all email open records.
    """
    from fastapi.responses import StreamingResponse
    import io
    import csv
    
    # Get all data
    opens = await get_recent_opens(limit=10000)  # Get up to 10k records
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "Email ID", "Lead ID", "Lead Name", "Subject", 
        "Recipient", "Opens Count", "Opened At", "Notified At", "Date"
    ])
    
    # Write data
    for open in opens:
        writer.writerow([
            open.email_id,
            open.lead_id,
            open.lead_name,
            open.subject,
            open.recipient,
            open.opens_count,
            open.opened_at.isoformat(),
            open.notified_at.isoformat(),
            open.date_opened
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=email_opens.csv"}
    )


@app.get("/analytics/top-leads")
async def get_top_leads_endpoint(limit: int = 10):
    """
    Get top leads by email open count.
    
    Args:
        limit: Number of top leads to return (default: 10, max: 100)
        
    Returns:
        - lead_id
        - lead_name
        - total_opens
        - unique_emails
        - first_open
        - last_open
    """
    limit = min(limit, 100)  # Cap at 100
    leads = await get_top_leads(limit=limit)
    
    return {
        "count": len(leads),
        "leads": leads
    }


@app.get("/analytics/time-of-day")
async def get_opens_by_time_endpoint():
    """
    Get email opens by hour of day (0-23).
    
    Useful for finding optimal send times.
    
    Returns:
        Array of {hour, opens_count, unique_leads}
    """
    data = await get_opens_by_time_of_day()
    
    return {
        "time_analysis": data,
        "best_hour": max(data, key=lambda x: x["opens_count"])["hour"] if data else None
    }


@app.get("/analytics/day-of-week")
async def get_opens_by_day_endpoint():
    """
    Get email opens by day of week.
    
    0=Monday, 6=Sunday
    
    Returns:
        Array of {day_of_week, day_name, opens_count, unique_leads}
    """
    data = await get_opens_by_day_of_week()
    
    return {
        "day_analysis": data,
        "best_day": max(data, key=lambda x: x["opens_count"])["day_name"] if data else None
    }


@app.get("/analytics/engagement")
async def get_engagement_metrics_endpoint(days: int = 30):
    """
    Get engagement metrics for last N days.
    
    Args:
        days: Number of days to analyze (default: 30, max: 365)
        
    Returns:
        - period_days
        - total_opens
        - unique_emails
        - unique_leads
        - avg_opens_per_email
        - max_opens_per_email
    """
    days = min(days, 365)  # Cap at 1 year
    metrics = await get_engagement_metrics(days=days)
    
    return metrics


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
