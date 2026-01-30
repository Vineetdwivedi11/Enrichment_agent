# Email Open Discord Notifier

Real-time Discord notifications for email opens in Close.io CRM. Get instant alerts when prospects open your emails.

## Features

- 🔔 **Real-time Notifications**: Instant Discord alerts when emails are opened
- 🔄 **Dual Mode**: Works with webhooks OR polling (fallback)
- 🚫 **No Duplicates**: Smart caching prevents repeat notifications
- 💾 **Persistent Storage**: SQLite database tracks notification history
- 🐳 **Docker Ready**: Easy deployment with Docker/Docker Compose
- ☁️ **AWS Compatible**: Deploy to ECS, Fargate, or Lambda
- 🔒 **Webhook Verification**: Validates Close.io webhook signatures

## How It Works

### Webhook Mode (Recommended)
1. Close.io sends webhook events to this service when emails are opened
2. Service validates the event and checks for duplicates
3. Sends formatted notification to Discord channel

### Polling Mode (Fallback)
1. Service periodically polls Close.io Event Log API
2. Identifies new email open events
3. Sends notifications for new opens only

## Installation

### Local Setup

```bash
# Clone repository
cd email-open-discord-notifier

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### Docker Setup

```bash
# Build image
docker build -t email-open-notifier .

# Or use docker-compose
docker-compose up -d
```

## Configuration

### Required Credentials

1. **Close.io API Key**
   - Go to Close.io Settings → API Keys
   - Generate new API key
   - Add to `.env` as `CLOSEIO_API_KEY`

2. **Discord Webhook URL**
   - Go to Discord Server Settings → Integrations → Webhooks
   - Create new webhook
   - Copy webhook URL
   - Add to `.env` as `DISCORD_WEBHOOK_URL`

3. **Close.io Webhook Setup** (Optional but recommended)
   - Option A: Use the service's API endpoint:
     ```bash
     # Create webhook subscription via API
     curl -X POST https://your-domain.com/webhook/closeio
     ```
   - Option B: Contact Close.io support to configure webhook manually
   - Set webhook URL to: `https://your-domain.com/webhook/closeio`

### Environment Variables

```env
# Server
PORT=8000
DEBUG=false

# Close.io
CLOSEIO_API_KEY=your_api_key_here
CLOSEIO_WEBHOOK_SECRET=optional_secret_for_signature_verification

# Discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Polling (if webhooks not available)
POLLING_ENABLED=true
POLLING_INTERVAL_SECONDS=300  # Check every 5 minutes
POLLING_LOOKBACK_MINUTES=10   # Look back 10 minutes each check
```

## Usage

### Running Locally

```bash
# Direct Python
python main.py

# Or with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000

# Access at http://localhost:8000
```

### Running with Docker

```bash
# Using docker-compose (recommended)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop service
docker-compose down
```

### Testing

```bash
# Check service health
curl http://localhost:8000/health

# Send test notification
curl -X POST http://localhost:8000/test/notification

# View stats
curl http://localhost:8000/stats
```

## Close.io Webhook Configuration

### Automated Setup (via API)

The service includes a helper endpoint to create webhook subscriptions:

```python
import httpx

# Your service URL
SERVICE_URL = "https://your-domain.com"

# Create webhook subscription
response = httpx.post(
    f"{SERVICE_URL}/setup/webhook",
    headers={"Authorization": "Bearer your-closeio-api-key"}
)
```

### Manual Setup

If automatic webhook setup doesn't work:

1. **Email Close.io Support**: support@close.io
2. **Provide Webhook URL**: `https://your-domain.com/webhook/closeio`
3. **Request Events**: `activity.email` with action `updated`

### Verifying Webhooks Work

Check the service logs:
```bash
docker-compose logs -f email-notifier
```

You should see:
- `✓ Webhook received` when emails are opened
- `✓ Discord notification sent`

## Discord Notification Format

Notifications include:
- 📧 Lead name and email address
- 📋 Email subject line
- 🔢 Number of opens
- ⏰ Timestamp of open
- 🔗 Link to lead in Close.io

Example:
```
📧 Email Opened
Lead: Acme Corp
Recipient: john@acme.com
Subject: Following up on our demo
Opens Count: 2
Opened At: 2025-01-12 14:30:00
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service status |
| `/health` | GET | Health check |
| `/webhook/closeio` | POST | Receive Close.io webhooks |
| `/stats` | GET | Notification statistics |
| `/test/notification` | POST | Send test notification |

## Deployment

### AWS ECS/Fargate

```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

docker tag email-open-notifier:latest <account>.dkr.ecr.us-east-1.amazonaws.com/email-notifier:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/email-notifier:latest

# Deploy to ECS (use task definition)
# Set environment variables in task definition
# Expose port 8000
# Mount volume for SQLite database
```

### AWS Lambda

For serverless deployment:
1. Use AWS Lambda adapter
2. Set up API Gateway for webhook endpoint
3. Use DynamoDB instead of SQLite for cache

## Monitoring

### Logs

```bash
# Docker logs
docker-compose logs -f

# Check for errors
docker-compose logs | grep ERROR
```

### Metrics

Access `/stats` endpoint:
```json
{
  "total_notifications": 42,
  "cache_size": 42,
  "oldest_entry": "2025-01-10T10:00:00"
}
```

## Troubleshooting

### No Notifications Received

1. **Check Close.io API key**:
   ```bash
   curl -u your_api_key: https://api.close.com/api/v1/me/
   ```

2. **Check Discord webhook**:
   ```bash
   curl -X POST http://localhost:8000/test/notification
   ```

3. **Verify webhook setup**:
   - Check Close.io webhook subscriptions
   - Ensure webhook URL is publicly accessible

4. **Check logs** for errors:
   ```bash
   docker-compose logs -f | grep ERROR
   ```

### Duplicate Notifications

The service uses caching to prevent duplicates, but if you're still getting them:
- Check cache retention days in config
- Clear cache database: `rm data/email_opens.db`
- Restart service

### Polling Mode Not Working

1. Verify `POLLING_ENABLED=true`
2. Check `POLLING_INTERVAL_SECONDS` (don't set too low)
3. Ensure Close.io API key has permissions

## Development

```bash
# Install dev dependencies
pip install -r requirements.txt pytest black flake8

# Run tests
pytest

# Format code
black .

# Lint
flake8 .
```

## Architecture

```
email-open-discord-notifier/
├── main.py                 # FastAPI application
├── src/
│   ├── config.py          # Configuration
│   ├── models.py          # Data models
│   ├── closeio.py         # Close.io API client
│   ├── discord_notifier.py # Discord webhook sender
│   ├── cache.py           # Duplicate prevention
│   └── database.py        # SQLite persistence
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Security Notes

- Store API keys in environment variables, never in code
- Use HTTPS for webhook endpoint in production
- Enable webhook signature verification
- Regularly rotate API keys
- Monitor for unusual activity

## Close.io Webhook Support

⚠️ **Important**: Close.io webhook support for email opens depends on their current API capabilities:

- **Confirmed**: Event Log API tracks email opens (polling works)
- **Uncertain**: Whether webhooks fire specifically for email opens
- **Solution**: Service supports both webhook AND polling modes

If webhooks don't work, polling mode provides reliable fallback.

## License

MIT License - See LICENSE file

## Support

Issues or questions? Open an issue on GitHub or check:
- Close.io API Docs: https://developer.close.com
- Discord Webhook Guide: https://discord.com/developers/docs/resources/webhook
