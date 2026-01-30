# Email Open Notifier - Final Architecture

## Dual Storage System

The email notifier now uses a **dual storage approach** for optimal performance and analytics:

### 1. **In-Memory Cache** (24-hour retention)
**Purpose:** Duplicate prevention
**Technology:** Python dictionary in memory
**Retention:** 24 hours
**Use case:** Prevents sending duplicate Discord notifications

### 2. **SQLite Database** (Permanent storage)
**Purpose:** Analytics and historical tracking
**Technology:** SQLite with async support
**Retention:** Permanent (all records kept)
**Use case:** Analytics, reporting, historical queries

## Why Both?

### Cache for Performance
- **Fast lookups** - No disk I/O for duplicate checks
- **Automatic cleanup** - Entries expire after 24 hours
- **Simple** - No complex queries needed
- **Sufficient** - 24 hours is enough to prevent duplicate notifications

### Database for Analytics
- **Historical data** - Keep all email opens forever
- **Rich queries** - Search by date, lead, recipient
- **Export capability** - CSV export for external analysis
- **Metrics** - Track engagement over time

## Data Flow

```
Email Opened in Close.io
        ↓
Webhook/Polling detects event
        ↓
Check cache: Already notified?
        ↓ No
Send Discord notification
        ↓
Log to database (analytics)
        ↓
Mark in cache (prevent duplicates)
```

## Database Schema

### `email_open_log` Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| email_id | STRING | Close.io email ID |
| lead_id | STRING | Close.io lead ID |
| lead_name | STRING | Company/lead name |
| subject | STRING | Email subject |
| recipient | STRING | Email recipient |
| opens_count | INTEGER | Times opened |
| opened_at | DATETIME | When email was opened |
| notified_at | DATETIME | When Discord notification sent |
| date_opened | STRING | Date in YYYY-MM-DD format |

**Indexes:**
- `email_id` - Fast lookup by email
- `lead_id` - Fast lookup by lead
- `recipient` - Fast lookup by recipient
- `opened_at` - Fast date queries
- `date_opened` - Fast date range queries

## Analytics Endpoints

### 1. Summary Analytics
```bash
GET /analytics/summary
```

Returns:
```json
{
  "total_opens": 1247,
  "unique_emails": 423,
  "unique_leads": 156
}
```

### 2. Recent Opens
```bash
GET /analytics/recent?limit=50
```

Returns last N email opens with full details.

### 3. Opens by Date Range
```bash
GET /analytics/by-date?start_date=2025-01-01&end_date=2025-01-31
```

Returns all opens within date range.

### 4. Opens by Lead
```bash
GET /analytics/by-lead/lead_abc123
```

Returns all opens for a specific company/lead.

### 5. CSV Export
```bash
GET /analytics/export
```

Downloads CSV file with all email open data.

## Usage Examples

### Query Recent Opens
```bash
curl http://localhost:8000/analytics/recent?limit=10
```

### Get Opens for January 2025
```bash
curl "http://localhost:8000/analytics/by-date?start_date=2025-01-01&end_date=2025-01-31"
```

### Get All Opens for a Lead
```bash
curl http://localhost:8000/analytics/by-lead/lead_xyz789
```

### Export Everything
```bash
curl http://localhost:8000/analytics/export > email_opens.csv
```

### Get Summary Stats
```bash
curl http://localhost:8000/analytics/summary
```

## Docker Setup

### Volumes
```yaml
volumes:
  - ./data:/app/data  # SQLite database persists here
  - ./discord_config.json:/app/discord_config.json:ro
```

### Data Directory
Create before running:
```bash
mkdir -p data
```

Database will be created automatically at `./data/email_opens.db`

## Performance Characteristics

### Duplicate Check (Cache)
- **Speed:** < 1ms (in-memory lookup)
- **Memory:** ~100 bytes per entry
- **Capacity:** 10,000+ entries easily

### Analytics Query (Database)
- **Small queries:** < 10ms
- **Large queries:** < 100ms (10k records)
- **Export:** < 1s (10k records)

### Storage
- **Cache:** ~1 MB for 10k entries
- **Database:** ~1 MB per 10k records
- **Growth:** ~100 MB per million opens

## Maintenance

### Backup Database
```bash
# Copy database file
cp data/email_opens.db data/email_opens_backup_$(date +%Y%m%d).db

# Or use SQLite backup command
sqlite3 data/email_opens.db ".backup data/backup.db"
```

### Query Database Directly
```bash
sqlite3 data/email_opens.db

# Get total count
SELECT COUNT(*) FROM email_open_log;

# Get opens today
SELECT * FROM email_open_log WHERE date_opened = date('now');

# Get top leads by opens
SELECT lead_name, COUNT(*) as opens 
FROM email_open_log 
GROUP BY lead_name 
ORDER BY opens DESC 
LIMIT 10;
```

### Clear Old Data (Optional)
```sql
-- Delete opens older than 1 year
DELETE FROM email_open_log 
WHERE opened_at < datetime('now', '-1 year');

-- Vacuum to reclaim space
VACUUM;
```

## Configuration

### Environment Variables
```env
# Database location
DATABASE_URL=sqlite+aiosqlite:///./data/email_opens.db

# Cache retention (duplicate prevention)
CACHE_RETENTION_HOURS=24
```

### Custom Database Location
```env
# Use absolute path
DATABASE_URL=sqlite+aiosqlite:////var/lib/email-notifier/opens.db

# Or relative path
DATABASE_URL=sqlite+aiosqlite:///./custom_location/db.sqlite
```

## Monitoring

### Check Database Size
```bash
ls -lh data/email_opens.db
```

### Check Record Count
```bash
curl http://localhost:8000/analytics/summary
```

### Check Cache Status
```bash
curl http://localhost:8000/stats
```

## Integration Examples

### Power BI / Tableau
1. Export CSV: `GET /analytics/export`
2. Import into BI tool
3. Create dashboards

### Python Analysis
```python
import requests
import pandas as pd

# Get data
response = requests.get('http://localhost:8000/analytics/recent?limit=1000')
data = response.json()

# Convert to DataFrame
df = pd.DataFrame(data['opens'])
df['opened_at'] = pd.to_datetime(df['opened_at'])

# Analysis
print(df.groupby('lead_name')['opens_count'].sum().sort_values(ascending=False))
```

### Direct SQLite Access
```python
import sqlite3

conn = sqlite3.connect('data/email_opens.db')
df = pd.read_sql_query("SELECT * FROM email_open_log WHERE date_opened >= '2025-01-01'", conn)
conn.close()
```

## Benefits of This Architecture

✅ **Fast** - In-memory cache for duplicate prevention
✅ **Reliable** - Database ensures no data loss
✅ **Analytical** - Rich querying capabilities
✅ **Scalable** - Can handle millions of records
✅ **Simple** - Single SQLite file, no external database
✅ **Exportable** - CSV export for external tools
✅ **Queryable** - REST API + direct SQL access

## When to Upgrade

Consider PostgreSQL/MySQL when:
- More than 10 million records
- Multiple services accessing same data
- Need advanced analytics (window functions, etc.)
- Require replication/backups

For most use cases, SQLite is perfect and significantly simpler.
