# Enrichment Agent

**Extract structured data from websites using AI-powered prompts and schemas.**

Extract comprehensive company intelligence using 34 specialized prompts and Firecrawl + Claude.

## Features

✅ **34 Production-Ready Prompts** - Cover all aspects of a company  
✅ **30 Matching Schemas** - Structured data extraction  
✅ **Firecrawl Integration** - High-quality website scraping  
✅ **Claude AI Extraction** - LLM-powered data extraction  
✅ **Batch Processing** - Process multiple companies at once  
✅ **Flexible Variables** - Pass custom data to prompts  

## Quick Start

```bash
cd enrichment-agent

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your API keys

# Extract company profile
python cli.py enrich https://stripe.com \
  --schema company_profile \
  --prompt extract_company \
  --company "Stripe"

# List all available prompts
python cli.py list-prompts

# List all available schemas
python cli.py list-schemas
```

## 34 Available Prompts

### Core Business (10)
- `extract_company` - Company profile and basics
- `extract_leadership` - Leadership team and executives
- `extract_hiring` - Job openings and growth signals
- `extract_customers` - Testimonials and case studies
- `extract_funding` - Investment and financial data
- `extract_geography` - Geographic presence
- `extract_icp` - Ideal customer profile
- `extract_competitors` - Competitive landscape
- `extract_press` - Media coverage and PR
- `extract_acquisitions` - M&A activity

### Product & Technology (8)
- `extract_product_features` - Features and capabilities
- `extract_tech_stack` - Technology and infrastructure
- `extract_api` - API and developer resources
- `extract_integrations` - Integrations and partnerships
- `extract_mobile` - Mobile app presence
- `extract_innovation` - R&D and innovation
- `extract_roadmap` - Product vision and roadmap
- `extract_data_strategy` - Data and analytics

### Go-to-Market (4)
- `extract_sales_strategy` - Sales and GTM approach
- `extract_marketing_strategy` - Marketing and brand
- `extract_pricing` - Pricing information
- `extract_pricing_psychology` - Pricing tactics

### Customer & Support (6)
- `extract_onboarding` - Customer success and onboarding
- `extract_support` - Support channels and help
- `extract_reviews` - Customer reviews and ratings
- `extract_content` - Content and learning resources
- `extract_events` - Events and community
- `extract_partners` - Partner program

### Compliance & Risk (6)
- `extract_security` - Security and compliance
- `extract_certifications` - Certifications and standards
- `extract_legal_compliance` - Legal and regulatory
- `extract_sustainability` - ESG and sustainability
- `extract_culture` - Culture and values
- `extract_contact` - Contact information

## Usage Examples

### Single Company Enrichment

```bash
# Basic usage
python cli.py enrich URL --schema SCHEMA_NAME --prompt PROMPT_NAME

# With company name
python cli.py enrich https://stripe.com \
  --schema company_profile \
  --prompt extract_company \
  --company "Stripe"

# With custom output
python cli.py enrich https://stripe.com \
  --schema tech_stack \
  --prompt extract_tech_stack \
  --output stripe_tech.json

# With custom variables
python cli.py enrich https://example.com \
  --schema custom \
  --prompt custom_prompt \
  --var industry=SaaS \
  --var focus=AI
```

### Batch Processing

```bash
# Process CSV file
python cli.py batch companies.csv \
  --schema company_profile \
  --prompt extract_company

# Custom column names
python cli.py batch leads.csv \
  --schema icp \
  --prompt extract_icp \
  --url-col website \
  --name-col company_name
```

### Example CSV Format

```csv
name,url
Stripe,https://stripe.com
Shopify,https://shopify.com
Vercel,https://vercel.com
```

## Output Format

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
    "headquarters": "San Francisco, CA",
    "description": "Payment processing platform..."
  },
  "enriched_at": "2025-01-12T15:30:00",
  "model_used": "claude-sonnet-4-20250514"
}
```

## Creating Custom Prompts

1. Create a new file in `prompts/` directory:

```bash
touch prompts/extract_custom.txt
```

2. Write your prompt with Jinja2 variables:

```
Extract custom data from {{ company_name }}.

URL: {{ url }}
Content: {{ content }}

Focus on: {{ focus_area }}

Extract specific fields...
```

3. Create matching schema in `schemas/`:

```json
{
  "name": "custom",
  "description": "Custom data extraction",
  "fields": {
    "field_name": {
      "type": "string",
      "description": "What this field represents",
      "required": true
    }
  }
}
```

4. Use it:

```bash
python cli.py enrich URL \
  --schema custom \
  --prompt extract_custom \
  --var focus_area="security"
```

## Docker Support

```bash
# Build
docker build -t enrichment-agent .

# Run
docker run -it --rm \
  -v $(pwd)/output:/app/output \
  -e FIRECRAWL_API_KEY=your_key \
  -e ANTHROPIC_API_KEY=your_key \
  enrichment-agent \
  enrich https://stripe.com \
  --schema company_profile \
  --prompt extract_company
```

## Performance & Cost

- **Speed:** ~5-8 seconds per URL
- **Batch (100):** ~10-15 minutes
- **Cost:** ~$0.004 per URL
  - Firecrawl: $0.001
  - Claude Sonnet: $0.003

## Use Cases

- **Sales Intelligence** - Enrich prospect lists
- **Competitive Analysis** - Research competitors
- **Market Research** - Analyze market segments
- **Due Diligence** - Investment research
- **Lead Enrichment** - Add data to CRM

## License

MIT License

## Support

For issues or questions, check the documentation or create an issue.
