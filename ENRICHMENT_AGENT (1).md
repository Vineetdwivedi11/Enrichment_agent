# Enrichment Agent - Quick Start

**NEW:** Configurable website data extraction with prompts and schemas stored as files!

## What Is It?

A flexible enrichment tool that extracts structured data from websites using:
- **Prompts** (Jinja2 templates in `.txt` files)
- **Schemas** (JSON definitions of data structure)  
- **Firecrawl** (website scraping)
- **Claude** (LLM extraction)

## Key Features

✅ **Prompt-driven** - Define extraction logic as text files
✅ **Schema-based** - Define data structure as JSON  
✅ **Variable support** - Pass custom variables to prompts
✅ **Batch processing** - Process CSV/JSON lists
✅ **4 built-in templates** - Company, tech stack, contact, pricing
✅ **Fully customizable** - Add your own prompts and schemas

## Quick Start

```bash
cd enrichment-agent

# Install
pip install -r requirements.txt
cp .env.example .env
# Add API keys to .env

# Extract company info
python cli.py enrich https://stripe.com \
  --schema company_profile \
  --prompt extract_company \
  --company "Stripe"

# Extract tech stack
python cli.py enrich https://vercel.com \
  --schema tech_stack \
  --prompt extract_tech_stack \
  --company "Vercel"

# Batch process
python cli.py batch examples/companies.csv \
  --schema company_profile \
  --prompt extract_company
```

## How It Works

```
1. Read prompt template from prompts/extract_company.txt
   ↓
2. Read schema from schemas/company_profile.json
   ↓
3. Scrape website with Firecrawl
   ↓
4. Render prompt with scraped content + variables
   ↓
5. Send to Claude for extraction
   ↓
6. Validate against schema
   ↓
7. Save to output/Company_Name_timestamp.json
```

## Directory Structure

```
enrichment-agent/
├── cli.py                       # Main CLI
├── prompts/                     # Prompt templates (Jinja2)
│   ├── extract_company.txt
│   ├── extract_tech_stack.txt
│   ├── extract_contact.txt
│   └── extract_pricing.txt
├── schemas/                     # JSON schemas
│   ├── company_profile.json
│   ├── tech_stack.json
│   ├── contact_info.json
│   └── pricing_info.json
├── output/                      # Generated data
└── examples/                    # Sample CSV files
```

## Built-in Prompts & Schemas

### 1. Company Profile
**Extract:** Name, industry, size, funding, products, customers
```bash
python cli.py enrich URL --schema company_profile --prompt extract_company
```

### 2. Tech Stack
**Extract:** Languages, frameworks, databases, cloud, infrastructure
```bash
python cli.py enrich URL --schema tech_stack --prompt extract_tech_stack
```

### 3. Contact Information
**Extract:** Emails, phones, addresses, social media
```bash
python cli.py enrich URL --schema contact_info --prompt extract_contact
```

### 4. Pricing
**Extract:** Pricing model, tiers, trials, payment methods
```bash
python cli.py enrich URL --schema pricing_info --prompt extract_pricing
```

## Example: Company Profile

**Prompt** (`prompts/extract_company.txt`):
```
You are an expert at extracting company information.

COMPANY: {{ company_name }}
URL: {{ url }}

Content:
{{ content }}

Extract company profile based on schema.
```

**Schema** (`schemas/company_profile.json`):
```json
{
  "name": "company_profile",
  "fields": {
    "company_name": {
      "type": "string",
      "required": true
    },
    "industry": {
      "type": "string",
      "required": true
    },
    "founded_year": {
      "type": "integer",
      "required": false
    }
  }
}
```

**Output** (`output/Stripe_20250112.json`):
```json
{
  "company_name": "Stripe",
  "url": "https://stripe.com",
  "schema_used": "company_profile",
  "prompt_used": "extract_company",
  "extracted_data": {
    "company_name": "Stripe",
    "industry": "FinTech",
    "founded_year": 2010,
    "description": "Payment processing platform",
    "headquarters": "San Francisco, CA",
    "employee_count": "8000+"
  },
  "enriched_at": "2025-01-12T15:30:00"
}
```

## Custom Prompts & Schemas

### Create Custom Prompt

**1. Create file:**
```bash
touch prompts/extract_features.txt
```

**2. Write prompt:**
```
Extract product features from {{ company_name }}.

Content: {{ content }}

Focus on {{ focus_area }}.
```

**3. Use it:**
```bash
python cli.py enrich URL \
  --prompt extract_features \
  --schema your_schema \
  --var focus_area="security"
```

### Create Custom Schema

**1. Create file:**
```bash
touch schemas/features.json
```

**2. Define schema:**
```json
{
  "name": "features",
  "description": "Product features",
  "fields": {
    "core_features": {
      "type": "array",
      "description": "Main features",
      "required": true
    }
  }
}
```

**3. Use it:**
```bash
python cli.py enrich URL \
  --schema features \
  --prompt extract_features
```

## Batch Processing

**CSV file** (`companies.csv`):
```csv
name,url
Stripe,https://stripe.com
Shopify,https://shopify.com
```

**Process:**
```bash
python cli.py batch companies.csv \
  --schema company_profile \
  --prompt extract_company
```

**Output:** `output/batch_20250112.json` with all results.

## CLI Commands

```bash
# List resources
python cli.py list-prompts
python cli.py list-schemas
python cli.py show-schema company_profile

# Single enrichment
python cli.py enrich URL \
  --schema SCHEMA \
  --prompt PROMPT \
  --company "Name" \
  --var key=value

# Batch processing
python cli.py batch FILE \
  --schema SCHEMA \
  --prompt PROMPT
```

## Variables

All prompts have access to:
- `{{ content }}` - Scraped markdown
- `{{ url }}` - Website URL
- `{{ title }}` - Page title
- Custom variables via `--var key=value`

## Docker

```bash
# Build
docker build -t enrichment-agent .

# Run
docker-compose run enrichment-agent \
  enrich URL --schema X --prompt Y
```

## Configuration

**`.env` file:**
```bash
FIRECRAWL_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

## Use Cases

- **Sales Intelligence** - Enrich prospect data
- **Competitive Analysis** - Compare competitors
- **Market Research** - Analyze market segments
- **Lead Enrichment** - Add data to CRM
- **Tech Stack Analysis** - Identify technologies

## Documentation

- **README.md** - Complete user guide
- **EXAMPLES.md** - Detailed usage examples
- **ARCHITECTURE.md** - Technical architecture
- **schemas/*.json** - Schema definitions
- **prompts/*.txt** - Prompt templates

## Performance

- **Single URL:** ~5-8 seconds
- **Batch (100):** ~10-15 minutes
- **Cost:** ~$0.004 per URL

## Next Steps

1. Configure API keys in `.env`
2. Try built-in examples
3. Create custom prompts
4. Build custom schemas
5. Process batches

🚀 **Start enriching!**
