# Sales Automation Microservices

Two independent microservices for sales prospecting and email tracking automation.

## Services Overview

### 1. Research Agent
**Purpose**: Automated prospect research combining website scraping and LinkedIn intelligence

**Features**:
- 🌐 Website scraping via Firecrawl API
- 💼 LinkedIn data via Bright Data API (company profiles, posts, people search)
- 📊 Google Sheets export
- 💾 JSON output
- 🐳 Docker containerized
- 🎯 CLI interface

**Tech Stack**: Python, Typer, httpx, gspread

### 2. Email Open Discord Notifier
**Purpose**: Real-time Discord notifications when emails are opened in Close.io CRM

**Features**:
- 🔔 Instant email open alerts
- 🔄 Dual mode: Webhooks + Polling fallback
- 🚫 Duplicate notification prevention
- 💾 SQLite persistence
- 🐳 Docker containerized
- ☁️ AWS-ready

**Tech Stack**: Python, FastAPI, httpx, SQLAlchemy, Discord webhooks

## Repository Structure

```
.
├── research-agent/              # Service 1: Prospect Research
│   ├── cli.py                   # CLI application
│   ├── src/                     # Source code
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── README.md
│
└── email-open-discord-notifier/ # Service 2: Email Tracking
    ├── main.py                  # FastAPI application
    ├── src/                     # Source code
    ├── Dockerfile
    ├── docker-compose.yml
    └── README.md
```

## Quick Start

### Research Agent

```bash
cd research-agent

# Configure
cp .env.example .env
# Add API keys: FIRECRAWL_API_KEY, BRIGHTDATA_API_KEY

# Run locally
pip install -r requirements.txt
python cli.py research "Acme Corp" --website https://acme.com

# Or with Docker
docker-compose build
docker-compose run research-agent research "Acme Corp" --website https://acme.com
```

### Email Open Notifier

```bash
cd email-open-discord-notifier

# Configure
cp .env.example .env
# Add: CLOSEIO_API_KEY, DISCORD_WEBHOOK_URL

# Run locally
pip install -r requirements.txt
python main.py

# Or with Docker
docker-compose up -d

# Test
curl -X POST http://localhost:8000/test/notification
```

## API Keys Required

### Research Agent
- **Firecrawl API** - Website scraping
  - Get at: https://firecrawl.dev
- **Bright Data API** - LinkedIn data
  - Get at: https://brightdata.com
- **Google Service Account** (optional) - Sheets export
  - Create at: https://console.cloud.google.com

### Email Open Notifier
- **Close.io API** - CRM integration
  - Get at: Close.io Settings → API Keys
- **Discord Webhook** - Notifications
  - Create at: Discord Server → Integrations → Webhooks

## Deployment Options

### Local Development
Both services can run locally with Python:
```bash
# Research Agent
python cli.py research "Company" --website https://example.com

# Email Notifier
uvicorn main:app --reload
```

### Docker (Recommended)
Each service has its own docker-compose.yml:
```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### AWS Deployment

#### Option 1: ECS/Fargate
```bash
# Push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker tag <service>:latest <account>.dkr.ecr.us-east-1.amazonaws.com/<service>:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/<service>:latest

# Deploy with task definitions
```

#### Option 2: Lambda (Email Notifier only)
- Use AWS Lambda Web Adapter
- Set up API Gateway for webhook endpoint
- Store environment variables in Secrets Manager

## Integration Guide

### Research Agent → Google Sheets
1. Create Google service account
2. Download credentials.json
3. Share target spreadsheet with service account email
4. Run: `python cli.py research "Company" --sheet --sheet-name "Prospects"`

### Email Notifier → Close.io
1. Get Close.io API key
2. **Webhook Mode** (recommended):
   - Set up public endpoint (AWS/ngrok)
   - Configure webhook in Close.io
3. **Polling Mode** (fallback):
   - Set `POLLING_ENABLED=true`
   - Service checks every 5 minutes

### Email Notifier → Discord
1. Create Discord webhook in target channel
2. Copy webhook URL
3. Add to .env as `DISCORD_WEBHOOK_URL`
4. Test: `curl -X POST http://localhost:8000/test/notification`

## Open Source Alternatives

### For LinkedIn Scraping
If you want to avoid Bright Data costs:

**joeyism/linkedin_scraper** (Python):
```bash
pip install linkedin-scraper
```

**linkedin-api** (Python):
```bash
pip install linkedin-api
```

See research-agent/README.md for integration examples.

## Close.io Webhook Support

⚠️ **Important Note**: Close.io webhook support for email opens needs verification:

- **Confirmed**: Event Log API tracks email opens ✓
- **Webhook Support**: May require contacting Close.io support
- **Solution**: Service supports both webhook AND polling modes

The email notifier works reliably in **polling mode** if webhooks aren't available.

## Monitoring & Logs

### Research Agent
```bash
# View output
ls -la output/

# Check Google Sheets
# Open URL from command output
```

### Email Notifier
```bash
# View logs
docker-compose logs -f

# Check stats
curl http://localhost:8000/stats

# Database
sqlite3 data/email_opens.db "SELECT * FROM notification_log;"
```

## Development

### Running Tests
```bash
# Install dev dependencies
pip install pytest black flake8

# Run tests
pytest

# Format code
black .
```

### Adding Features

Each service is independently developed:

**Research Agent**:
- Add new scrapers in `src/`
- New output formats in `src/google_sheets.py`
- CLI commands in `cli.py`

**Email Notifier**:
- New endpoints in `main.py`
- CRM integrations in `src/closeio.py`
- Notification formats in `src/discord_notifier.py`

## Security Best Practices

1. **Never commit API keys**
   - Use .env files (in .gitignore)
   - Use AWS Secrets Manager in production

2. **Webhook Security**
   - Enable signature verification
   - Use HTTPS endpoints only
   - Rotate webhook secrets regularly

3. **Database Security**
   - Mount SQLite volume with appropriate permissions
   - Use managed databases (RDS) in production
   - Regular backups

4. **Network Security**
   - Use VPC for AWS deployments
   - Restrict inbound traffic to necessary ports
   - Use security groups

## Troubleshooting

### Research Agent

**Issue**: Google Sheets export fails
```bash
# Solution:
1. Check credentials.json exists
2. Verify service account has access to sheets
3. Enable Google Sheets API in Cloud Console
```

**Issue**: Firecrawl rate limits
```bash
# Solution:
1. Check Firecrawl dashboard for usage
2. Upgrade plan if needed
3. Add delays between requests
```

### Email Notifier

**Issue**: No Discord notifications
```bash
# Solution:
1. Test Discord webhook: curl -X POST http://localhost:8000/test/notification
2. Check logs: docker-compose logs -f
3. Verify DISCORD_WEBHOOK_URL is correct
```

**Issue**: Duplicate notifications
```bash
# Solution:
1. Check cache: curl http://localhost:8000/stats
2. Clear database: rm data/email_opens.db
3. Restart service: docker-compose restart
```

## Production Checklist

### Before Deploying

- [ ] All API keys configured in environment
- [ ] Docker images built and tested
- [ ] Webhook endpoints publicly accessible (if using webhooks)
- [ ] Database volumes mounted with persistence
- [ ] Logging configured
- [ ] Health checks enabled
- [ ] Monitoring set up (CloudWatch, etc.)
- [ ] Backup strategy for databases
- [ ] Error notifications configured

### AWS Deployment

- [ ] ECR repositories created
- [ ] IAM roles configured
- [ ] Security groups set up
- [ ] Load balancer configured (if needed)
- [ ] Auto-scaling policies set
- [ ] CloudWatch alarms created
- [ ] Secrets Manager configured

## Cost Optimization

### Research Agent
- Firecrawl: ~$0.001 per page
- Bright Data: Pay-as-you-go LinkedIn API
- AWS: t3.micro sufficient ($8/month)

### Email Notifier
- Close.io: Included in subscription
- Discord: Free
- AWS: t3.nano sufficient ($4/month)

**Tip**: Use spot instances or Lambda for further savings

## Future Enhancements

### Research Agent
- [ ] Automated enrichment workflows
- [ ] Integration with CRM systems
- [ ] Scheduled batch processing
- [ ] Custom data sources
- [ ] AI-powered insights

### Email Notifier
- [ ] Slack integration
- [ ] Email reply tracking
- [ ] Custom notification rules
- [ ] Analytics dashboard
- [ ] Multi-CRM support

## Support

Each service has detailed README with:
- Installation instructions
- Configuration guides
- API documentation
- Troubleshooting tips

See individual README files:
- `research-agent/README.md`
- `email-open-discord-notifier/README.md`

## License

MIT License - See LICENSE file for details

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open pull request

Both services welcome contributions!
# Enrichment_agent
# Enrichment_agent
