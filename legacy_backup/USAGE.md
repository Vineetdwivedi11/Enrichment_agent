# Enrichment Agent - Usage Guide

Complete guide to using all 34 prompts for comprehensive company intelligence.

## Installation

```bash
cd enrichment-agent
pip install -r requirements.txt
cp .env.example .env
# Add your API keys to .env
```

## Basic Commands

```bash
# List available prompts
python cli.py list-prompts

# List available schemas
python cli.py list-schemas

# Enrich single URL
python cli.py enrich URL --schema SCHEMA --prompt PROMPT

# Batch process
python cli.py batch file.csv --schema SCHEMA --prompt PROMPT
```

## All 34 Prompts with Examples

### 1. Company Profile
```bash
python cli.py enrich https://stripe.com \
  --schema company_profile \
  --prompt extract_company \
  --company "Stripe"
```
**Extracts:** Name, industry, size, description, HQ, social media

### 2. Technology Stack
```bash
python cli.py enrich https://vercel.com \
  --schema tech_stack \
  --prompt extract_tech_stack \
  --company "Vercel"
```
**Extracts:** Languages, frameworks, databases, cloud, mobile

### 3. Contact Information
```bash
python cli.py enrich https://notion.so \
  --schema contact_info \
  --prompt extract_contact \
  --company "Notion"
```
**Extracts:** Emails, phones, addresses, social profiles

### 4. Pricing
```bash
python cli.py enrich https://linear.app \
  --schema pricing_info \
  --prompt extract_pricing \
  --company "Linear"
```
**Extracts:** Pricing model, tiers, trials, billing

### 5. Leadership Team
```bash
python cli.py enrich https://stripe.com \
  --schema leadership \
  --prompt extract_leadership \
  --company "Stripe"
```
**Extracts:** Executives, founders, titles, backgrounds

### 6. Hiring & Jobs
```bash
python cli.py enrich https://stripe.com \
  --schema hiring \
  --prompt extract_hiring \
  --company "Stripe"
```
**Extracts:** Open positions, departments, benefits, culture

### 7. Customer Testimonials
```bash
python cli.py enrich https://stripe.com \
  --schema customers \
  --prompt extract_customers \
  --company "Stripe"
```
**Extracts:** Customer names, quotes, case studies, results

### 8. Product Features
```bash
python cli.py enrich https://stripe.com \
  --schema product_features \
  --prompt extract_product_features \
  --company "Stripe"
```
**Extracts:** Core features, USPs, capabilities, integrations

### 9. Integrations
```bash
python cli.py enrich https://stripe.com \
  --schema integrations \
  --prompt extract_integrations \
  --company "Stripe"
```
**Extracts:** Native integrations, API, partnerships, marketplace

### 10. Security & Compliance
```bash
python cli.py enrich https://stripe.com \
  --schema security \
  --prompt extract_security \
  --company "Stripe"
```
**Extracts:** Certifications, encryption, compliance, security features

## Batch Processing Examples

### Competitive Analysis
```bash
# Create competitors.csv
cat > competitors.csv << CSV
name,url
Stripe,https://stripe.com
Square,https://square.com
Adyen,https://adyen.com
CSV

# Extract for all
python cli.py batch competitors.csv \
  --schema product_features \
  --prompt extract_product_features
```

### Sales Prospecting
```bash
# Process prospects
python cli.py batch prospects.csv \
  --schema company_profile \
  --prompt extract_company

# Get contact info
python cli.py batch prospects.csv \
  --schema contact_info \
  --prompt extract_contact

# Check tech stack
python cli.py batch prospects.csv \
  --schema tech_stack \
  --prompt extract_tech_stack
```

### Investment Research
```bash
# Full due diligence
for prompt in company leadership funding customers security; do
  python cli.py batch portfolio.csv \
    --schema $prompt \
    --prompt extract_$prompt
done
```

## Custom Variables

Pass custom data to prompts:

```bash
python cli.py enrich https://example.com \
  --schema custom \
  --prompt custom_prompt \
  --var industry="SaaS" \
  --var region="North America" \
  --var focus="Enterprise"
```

Access in prompt template:
```
Industry: {{ industry }}
Region: {{ region }}
Focus: {{ focus }}
```

## Output Management

### Default Output
```bash
# Automatically named: output/Company_Name_20250112_153045.json
python cli.py enrich URL --schema X --prompt Y
```

### Custom Output
```bash
# Specify exact filename
python cli.py enrich URL \
  --schema company_profile \
  --prompt extract_company \
  --output my_data/stripe_full.json
```

### Batch Output
```bash
# Creates: output/batch_20250112_153045.json
python cli.py batch companies.csv \
  --schema company_profile \
  --prompt extract_company
```

## Docker Usage

```bash
# Build image
docker build -t enrichment-agent .

# Run single enrichment
docker-compose run enrichment-agent \
  enrich https://stripe.com \
  --schema company_profile \
  --prompt extract_company \
  --company "Stripe"

# Batch process
docker-compose run enrichment-agent \
  batch /app/examples/companies.csv \
  --schema company_profile \
  --prompt extract_company
```

## Tips & Best Practices

### 1. Start Simple
Test with one company before batch processing:
```bash
# Test first
python cli.py enrich https://example.com \
  --schema company_profile \
  --prompt extract_company

# Then batch
python cli.py batch companies.csv \
  --schema company_profile \
  --prompt extract_company
```

### 2. Verify Output
Always check results:
```bash
# After enrichment
cat output/Company_Name_*.json | jq .
```

### 3. Use Multiple Prompts
Extract different aspects:
```bash
# Company basics
python cli.py enrich URL --schema company_profile --prompt extract_company

# Tech details  
python cli.py enrich URL --schema tech_stack --prompt extract_tech_stack

# Contacts
python cli.py enrich URL --schema contact_info --prompt extract_contact
```

### 4. Handle Rate Limits
For large batches, add delays or process in stages.

## Troubleshooting

### API Errors

**Firecrawl Error:**
```bash
# Check API key
echo $FIRECRAWL_API_KEY

# Test simple URL
python cli.py enrich https://example.com \
  --schema company_profile \
  --prompt extract_company
```

**Claude Error:**
```bash
# Verify API key
echo $ANTHROPIC_API_KEY

# Check rate limits (50 req/min for Sonnet)
```

### Missing Data

If extraction returns empty fields:
- Content may not contain the information
- Prompt may need refinement
- Schema may need adjustment
- Website may be JavaScript-heavy (Firecrawl handles this)

### Timeout Errors

```bash
# Increase timeout in .env
REQUEST_TIMEOUT=120
```

## Performance Benchmarks

- **Single URL:** ~5-8 seconds
- **10 URLs:** ~1-2 minutes
- **100 URLs:** ~10-15 minutes
- **1000 URLs:** ~2-3 hours

## Cost Calculation

Per URL: ~$0.004
- Firecrawl: $0.001
- Claude Sonnet: $0.003

For 1000 companies: ~$4.00

## Next Steps

1. Test with sample companies
2. Create custom prompts for your use case
3. Build custom schemas
4. Set up batch workflows
5. Integrate with your CRM or database

---

For more information, see README.md
