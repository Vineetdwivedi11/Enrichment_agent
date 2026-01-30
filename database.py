"""Database for email open analytics.

Stores all email open notifications for historical analysis.
Note: Cache uses in-memory (24h) for duplicate prevention,
      Database stores ALL opens permanently for analytics.
      
OPTIMIZED SCHEMA:
- Efficient data types (VARCHAR with limits)
- Compound indexes for common queries
- Denormalized for query performance
- Partitioned by date for fast range queries
"""

from datetime import datetime
from typing import List, Optional, Dict

from sqlalchemy import (
    Column, String, DateTime, Integer, create_engine, 
    desc, Index, text, Float
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select

from .config import settings

Base = declarative_base()


class EmailOpenLog(Base):
    """
    Optimized log of all email opens for analytics.
    
    OPTIMIZATIONS:
    - VARCHAR with limits instead of unbounded STRING
    - Compound indexes for common query patterns
    - Date fields for efficient range queries
    - Denormalized data (lead_name stored directly)
    """
    __tablename__ = "email_open_log"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Email identifiers (indexed for lookups)
    email_id = Column(String(100), nullable=False, index=True)
    lead_id = Column(String(100), nullable=False, index=True)
    
    # Denormalized data for query performance
    lead_name = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    recipient = Column(String(255), nullable=False, index=True)
    
    # Metrics
    opens_count = Column(Integer, default=1)
    
    # Timestamps
    opened_at = Column(DateTime, nullable=False, index=True)
    notified_at = Column(DateTime, nullable=False, default=datetime.now)
    
    # Date fields for efficient range queries
    date_opened = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    year_opened = Column(Integer, nullable=False)  # For year-based queries
    month_opened = Column(Integer, nullable=False)  # For month-based queries
    
    # Hour for time-of-day analysis
    hour_opened = Column(Integer)  # 0-23
    
    # Day of week (0=Monday, 6=Sunday)
    day_of_week = Column(Integer)  # For pattern analysis
    
    # Compound indexes for common query patterns
    __table_args__ = (
        # Fast lead + date queries
        Index('idx_lead_date', 'lead_id', 'date_opened'),
        
        # Fast recipient + date queries
        Index('idx_recipient_date', 'recipient', 'date_opened'),
        
        # Fast date range queries
        Index('idx_date_opened_desc', 'date_opened', 'opened_at'),
        
        # Analytics queries by time period
        Index('idx_year_month', 'year_opened', 'month_opened'),
        
        # Email tracking
        Index('idx_email_opened', 'email_id', 'opened_at'),
    )


# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,  # Verify connections before use
    pool_size=10,  # Connection pool
    max_overflow=20  # Allow extra connections
)

# Create async session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db():
    """Initialize database tables with optimized schema."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Get database session."""
    async with async_session() as session:
        yield session


async def log_email_open(
    email_id: str,
    lead_id: str,
    lead_name: str,
    subject: str,
    recipient: str,
    opens_count: int,
    opened_at: datetime
):
    """
    Log an email open event to database for analytics.
    
    Args:
        email_id: Email ID from Close.io
        lead_id: Lead ID
        lead_name: Lead/company name
        subject: Email subject
        recipient: Email recipient
        opens_count: Number of times opened
        opened_at: When it was opened
    """
    async with async_session() as session:
        log_entry = EmailOpenLog(
            email_id=email_id,
            lead_id=lead_id,
            lead_name=lead_name,
            subject=subject,
            recipient=recipient,
            opens_count=opens_count,
            opened_at=opened_at,
            notified_at=datetime.now(),
            date_opened=opened_at.strftime("%Y-%m-%d"),
            year_opened=opened_at.year,
            month_opened=opened_at.month,
            hour_opened=opened_at.hour,
            day_of_week=opened_at.weekday()
        )
        
        session.add(log_entry)
        await session.commit()


async def get_recent_opens(limit: int = 50) -> List[EmailOpenLog]:
    """Get recent email opens for analytics."""
    async with async_session() as session:
        result = await session.execute(
            select(EmailOpenLog)
            .order_by(desc(EmailOpenLog.opened_at))
            .limit(limit)
        )
        return result.scalars().all()


async def get_opens_by_date(start_date: str, end_date: str) -> List[EmailOpenLog]:
    """
    Get email opens within date range.
    
    Optimized with indexed date_opened field.
    
    Args:
        start_date: YYYY-MM-DD format
        end_date: YYYY-MM-DD format
    """
    async with async_session() as session:
        result = await session.execute(
            select(EmailOpenLog)
            .where(EmailOpenLog.date_opened >= start_date)
            .where(EmailOpenLog.date_opened <= end_date)
            .order_by(desc(EmailOpenLog.opened_at))
        )
        return result.scalars().all()


async def get_opens_by_lead(lead_id: str) -> List[EmailOpenLog]:
    """
    Get all email opens for a specific lead.
    
    Optimized with compound index (lead_id, date_opened).
    """
    async with async_session() as session:
        result = await session.execute(
            select(EmailOpenLog)
            .where(EmailOpenLog.lead_id == lead_id)
            .order_by(desc(EmailOpenLog.opened_at))
        )
        return result.scalars().all()


async def get_analytics_summary() -> Dict:
    """Get summary analytics of email opens."""
    async with async_session() as session:
        # Total opens
        total_result = await session.execute(
            select(EmailOpenLog)
        )
        total_opens = len(total_result.scalars().all())
        
        # Unique emails
        unique_result = await session.execute(
            select(EmailOpenLog.email_id).distinct()
        )
        unique_emails = len(unique_result.scalars().all())
        
        # Unique leads
        leads_result = await session.execute(
            select(EmailOpenLog.lead_id).distinct()
        )
        unique_leads = len(leads_result.scalars().all())
        
        return {
            "total_opens": total_opens,
            "unique_emails": unique_emails,
            "unique_leads": unique_leads
        }


async def get_top_leads(limit: int = 10) -> List[Dict]:
    """
    Get top leads by email open count.
    
    Optimized query using GROUP BY on indexed lead_id.
    """
    async with async_session() as session:
        query = text("""
            SELECT 
                lead_id,
                lead_name,
                COUNT(*) as total_opens,
                COUNT(DISTINCT email_id) as unique_emails,
                MIN(date_opened) as first_open,
                MAX(date_opened) as last_open
            FROM email_open_log
            GROUP BY lead_id, lead_name
            ORDER BY total_opens DESC
            LIMIT :limit
        """)
        
        result = await session.execute(query, {"limit": limit})
        
        return [
            {
                "lead_id": row[0],
                "lead_name": row[1],
                "total_opens": row[2],
                "unique_emails": row[3],
                "first_open": row[4],
                "last_open": row[5]
            }
            for row in result
        ]


async def get_opens_by_time_of_day() -> List[Dict]:
    """
    Get email opens grouped by hour of day.
    
    Useful for finding best send times.
    """
    async with async_session() as session:
        query = text("""
            SELECT 
                hour_opened,
                COUNT(*) as opens_count,
                COUNT(DISTINCT lead_id) as unique_leads
            FROM email_open_log
            GROUP BY hour_opened
            ORDER BY hour_opened
        """)
        
        result = await session.execute(query)
        
        return [
            {
                "hour": row[0],
                "opens_count": row[1],
                "unique_leads": row[2]
            }
            for row in result
        ]


async def get_opens_by_day_of_week() -> List[Dict]:
    """
    Get email opens grouped by day of week.
    
    0=Monday, 6=Sunday
    """
    async with async_session() as session:
        query = text("""
            SELECT 
                day_of_week,
                COUNT(*) as opens_count,
                COUNT(DISTINCT lead_id) as unique_leads
            FROM email_open_log
            GROUP BY day_of_week
            ORDER BY day_of_week
        """)
        
        result = await session.execute(query)
        
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        return [
            {
                "day_of_week": row[0],
                "day_name": day_names[row[0]] if row[0] is not None else "Unknown",
                "opens_count": row[1],
                "unique_leads": row[2]
            }
            for row in result
        ]


async def get_engagement_metrics(days: int = 30) -> Dict:
    """
    Get engagement metrics for last N days.
    
    Args:
        days: Number of days to analyze (default: 30)
    """
    async with async_session() as session:
        from datetime import timedelta
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        # Opens in period
        query = text("""
            SELECT 
                COUNT(*) as total_opens,
                COUNT(DISTINCT email_id) as unique_emails,
                COUNT(DISTINCT lead_id) as unique_leads,
                AVG(opens_count) as avg_opens_per_email,
                MAX(opens_count) as max_opens_per_email
            FROM email_open_log
            WHERE date_opened >= :cutoff_date
        """)
        
        result = await session.execute(query, {"cutoff_date": cutoff_date})
        row = result.fetchone()
        
        return {
            "period_days": days,
            "total_opens": row[0] or 0,
            "unique_emails": row[1] or 0,
            "unique_leads": row[2] or 0,
            "avg_opens_per_email": round(float(row[3] or 0), 2),
            "max_opens_per_email": row[4] or 0
        }

