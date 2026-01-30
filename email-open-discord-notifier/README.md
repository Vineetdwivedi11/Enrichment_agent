# Research Agent - Prospect Intelligence Tool

Automated prospect research tool that combines website scraping (Firecrawl) and LinkedIn data (Bright Data) to generate comprehensive company/prospect intelligence reports.

## Features

- 🌐 **Website Scraping**: Extract company information from websites using Firecrawl
- 💼 **LinkedIn Data**: Fetch company profiles, posts, and employee data via Bright Data API
- 📊 **Google Sheets Export**: Automatically create formatted spreadsheets with research data
- 💾 **JSON Output**: Save structured research data for further processing
- 🐳 **Docker Support**: Run locally or deploy to AWS with Docker containers
- 🎨 **Rich CLI**: Beautiful command-line interface with progress indicators

## Installation

### Local Setup

```bash
# Clone repository
git clone <repository-url>
cd research-agent

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Docker Setup

```bash
# Build image
docker build -t research-agent .

# Or use docker-compose
docker-compose build
```

## Configuration

### Required API Keys

1. **Firecrawl API Key** - For website scraping
   - Get it from: https://firecrawl.dev
   
2. **Bright Data API Key** - For LinkedIn data
   - Get it from: https://brightdata.com

3. **Google Service Account** (Optional, for Sheets export)
   - Create service account in Google Cloud Console
   - Download credentials JSON file
   - Save as `credentials.json` in project root

### Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```env
FIRECRAWL_API_KEY=your_key_here
BRIGHTDATA_API_KEY=your_key_here
GOOGLE_CREDENTIALS_PATH=credentials.json
```

## Usage

### Command Line

```bash
# Basic research with website
python cli.py research "Acme Corp" --website https://acme.com

# Include LinkedIn data
python cli.py research "Acme Corp" \
  --website https://acme.com \
  --linkedin https://linkedin.com/company/acme

# Export to Google Sheets
python cli.py research "Acme Corp" \
  --website https://acme.com \
  --sheet \
  --sheet-name "Q1 2025 Prospects"

# Research LinkedIn profile
python cli.py linkedin-profile "https://linkedin.com/in/john-doe"

# Check configuration
python cli.py config-check
```

### Docker

```bash
# Using docker run
docker run -v $(pwd)/output:/app/output \
  --env-file .env \
  research-agent research "Acme Corp" --website https://acme.com

# Using docker-compose
docker-compose run research-agent research "Acme Corp" --website https://acme.com
```

### AWS Deployment

```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

docker tag research-agent:latest <account>.dkr.ecr.us-east-1.amazonaws.com/research-agent:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/research-agent:latest

# Deploy to ECS/Fargate or run as Lambda
```

## Output

### JSON Output

Research data is saved as structured JSON:

```json
{
  "company_name": "Acme Corp",
  "website_url": "https://acme.com",
  "website_data": {
    "title": "Acme Corp - Leading Solutions",
    "description": "...",
    "content": "..."
  },
  "linkedin_company_data": {
    "name": "Acme Corp",
    "industry": "Technology",
    "company_size": "201-500 employees",
    "headquarters": "San Francisco, CA"
  },
  "linkedin_posts": [...]
}
```

### Google Sheets

Creates a formatted spreadsheet with:
- Overview tab with company information
- LinkedIn Posts tab with recent company posts
- Automatic formatting and column sizing

## Integration with Open Source Tools

While this tool uses commercial APIs (Firecrawl, Bright Data), you can integrate open-source alternatives:

### LinkedIn Scraping Alternatives

1. **linkedin_scraper** (Python)
   ```bash
   pip install linkedin-scraper
   ```

2. **linkedin-api** (Python)
   ```bash
   pip install linkedin-api
   ```

See `docs/open-source-alternatives.md` for integration examples.

## Architecture

```
research-agent/
├── cli.py              # Main CLI application
├── src/
│   ├── config.py       # Configuration management
│   ├── models.py       # Data models
│   ├── firecrawl_scraper.py
│   ├── linkedin_scraper.py
│   └── google_sheets.py
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Development

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run tests (if available)
pytest

# Format code
black .
```

## Troubleshooting

### Common Issues

1. **Google Sheets Export Fails**
   - Ensure service account has correct permissions
   - Check that credentials.json is in correct location
   - Verify Google Sheets API is enabled in Google Cloud Console

2. **API Rate Limits**
   - Bright Data: Check your plan limits
   - Firecrawl: Monitor usage on dashboard
   - Add delays between requests if needed

3. **Docker Permissions**
   - Ensure output directory is writable
   - Mount credentials file as read-only

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
- Open an issue on GitHub
- Check API documentation:
  - Firecrawl: https://docs.firecrawl.dev
  - Bright Data: https://docs.brightdata.com
