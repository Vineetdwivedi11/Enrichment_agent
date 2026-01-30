# Firecrawl Scraping Logic - Complete Explanation

## Overview

The research agent uses an **intelligent 3-step scraping process** to extract the most relevant information from websites efficiently.

## The Complete Flow

```
Input: Company website URL
        ↓
STEP 1: Get Sitemap
        ↓
STEP 2: Rank Pages by Importance
        ↓
STEP 3: Scrape Top N Pages (default: 5)
        ↓
STEP 4: Extract Key Points
        ↓
Output: Structured research data
```

---

## STEP 1: Get Sitemap

### What It Does
Discovers all pages on the website without scraping them.

### API Call
```python
POST https://api.firecrawl.dev/v1/map
{
    "url": "https://acme.com",
    "mode": "sitemap"
}
```

### Response
```python
{
    "links": [
        "https://acme.com/",
        "https://acme.com/about",
        "https://acme.com/products",
        "https://acme.com/team",
        "https://acme.com/contact",
        "https://acme.com/blog/post-1",
        "https://acme.com/blog/post-2",
        # ... potentially hundreds more
    ]
}
```

### Why This Step?
- **Efficiency**: Don't scrape blindly
- **Selectivity**: Choose only important pages
- **Cost**: Firecrawl charges per page scraped
- **Speed**: Faster than scraping everything

### Fallback
If sitemap fails (API error, no sitemap.xml), scrape just the homepage.

---

## STEP 2: Rank Pages by Importance

### Algorithm

Pages are scored based on URL patterns and depth:

```python
def get_score(url: str) -> int:
    """
    Higher score = more important page
    """
    path = parse_url(url).path.lower()
    
    # 1. Homepage gets highest score
    if path in ['/', '']:
        return 1000
    
    # 2. Check priority patterns
    PRIORITY_PATTERNS = [
        'about', 'team', 'company', 'who-we-are',      # Score: 900-890
        'products', 'services', 'solutions',            # Score: 880-870
        'contact', 'careers', 'jobs',                   # Score: 860-850
        'customers', 'case-studies', 'testimonials',    # Score: 840-830
        'blog', 'news', 'press'                         # Score: 820-810
    ]
    
    for index, pattern in enumerate(PRIORITY_PATTERNS):
        if pattern in path:
            return 900 - (index * 10)
    
    # 3. Shorter paths are more important
    path_depth = count_path_segments(path)
    return max(0, 500 - (path_depth * 50))
```

### Examples

| URL | Score | Reasoning |
|-----|-------|-----------|
| `https://acme.com/` | 1000 | Homepage |
| `https://acme.com/about` | 900 | First priority pattern |
| `https://acme.com/team` | 890 | Second priority pattern |
| `https://acme.com/products` | 880 | Third priority pattern |
| `https://acme.com/products/widget-a` | 450 | Depth 2, no pattern match |
| `https://acme.com/blog/2024/01/post` | 350 | Depth 4, no pattern match |

### Sorting

Pages are sorted by score (descending):
```python
ranked_pages = sorted(all_pages, key=get_score, reverse=True)
```

Result:
```python
[
    "https://acme.com/",              # 1000
    "https://acme.com/about",         # 900
    "https://acme.com/team",          # 890
    "https://acme.com/products",      # 880
    "https://acme.com/contact",       # 860
    "https://acme.com/customers",     # 840
    "https://acme.com/blog/latest",   # 450
    # ... rest
]
```

### Selection

Take top N pages (default: 5):
```python
pages_to_scrape = ranked_pages[:5]  # Top 5
```

---

## STEP 3: Scrape Selected Pages

### For Each Page

```python
POST https://api.firecrawl.dev/v1/scrape
{
    "url": page_url,
    "formats": ["markdown"],
    "onlyMainContent": true
}
```

### What `onlyMainContent` Does
- Removes navigation menus
- Removes footers
- Removes sidebars
- Removes ads
- **Keeps**: Main article/content only

### Response Per Page
```python
{
    "data": {
        "markdown": "# About Us\n\nAcme Corp is a leading...",
        "metadata": {
            "title": "About Us - Acme Corp",
            "description": "Learn about Acme Corp..."
        }
    }
}
```

### Aggregation

Content from all pages is combined:
```python
all_content = []

for page in pages_to_scrape:
    response = scrape(page)
    content = response["data"]["markdown"]
    all_content.append(f"## {page}\n\n{content}\n\n")

combined_content = "\n".join(all_content)
```

### Result Structure

```markdown
## https://acme.com/
# Acme Corp
Leading provider of...

## https://acme.com/about
# About Us
Founded in 2010...

## https://acme.com/products
# Our Products
We offer three main solutions...

## https://acme.com/team
# Meet the Team
John Smith - CEO...

## https://acme.com/contact
# Contact Us
Email: contact@acme.com...
```

---

## STEP 4: Extract Key Points

### Algorithm

Extracts 5-10 key insights from all scraped content.

#### 4.1 Extract Headings

```python
for line in content.split('\n'):
    # Find markdown headings (## or ###, but not ####)
    if line.startswith('##') and not line.startswith('####'):
        heading = line.lstrip('#').strip()
        if 10 < len(heading) < 200:
            key_points.append(heading)
```

**Example headings extracted:**
- "About Us"
- "Our Mission"
- "Products and Services"

#### 4.2 Extract Bold Text

```python
# Find text between ** markers
if '**' in line:
    parts = line.split('**')
    for i in range(1, len(parts), 2):  # Every odd index
        bold_text = parts[i].strip()
        if 10 < len(bold_text) < 200:
            key_points.append(bold_text)
```

**Example bold text:**
- "Leading provider of cloud solutions"
- "Trusted by over 10,000 companies"

#### 4.3 Find Important Sentences

```python
IMPORTANT_KEYWORDS = [
    'specialize', 'focus', 'provide', 'offer', 'solution',
    'mission', 'vision', 'goal', 'value', 'founded',
    'serve', 'help', 'enable', 'deliver', 'leading'
]

for sentence in sentences:
    sentence_lower = sentence.lower()
    if any(keyword in sentence_lower for keyword in IMPORTANT_KEYWORDS):
        if 20 < len(sentence) < 300:
            key_points.append(sentence)
```

**Example sentences:**
- "We specialize in enterprise cloud infrastructure."
- "Our mission is to democratize access to technology."
- "Founded in 2010, we've grown to serve Fortune 500 companies."

#### 4.4 Deduplicate

```python
seen = set()
unique_points = []

for point in key_points:
    normalized = point.lower().strip()
    if normalized not in seen:
        seen.add(normalized)
        unique_points.append(point)
```

#### 4.5 Limit to Top 10

```python
final_key_points = unique_points[:10]
```

### Example Output

```python
key_points = [
    "Leading provider of cloud infrastructure solutions",
    "Founded in 2010 and serving over 10,000 enterprises",
    "We specialize in scalable, secure cloud platforms",
    "Our mission is to simplify enterprise technology",
    "Three main products: CloudDB, CloudCompute, CloudStorage",
    "Trusted by Fortune 500 companies including Microsoft and Google",
    "24/7 support with 99.99% uptime guarantee",
    "Headquartered in San Francisco with offices in 12 countries",
    "Team of 500+ engineers and cloud specialists",
    "Recently raised $100M Series C funding"
]
```

---

## Complete Example Run

### Input
```python
python cli.py research "Acme Corp" --website https://acme.com --max-pages 5
```

### Process

**Step 1: Get Sitemap**
```
Found 47 pages on acme.com
```

**Step 2: Rank Pages**
```
Top pages:
1. https://acme.com/ (score: 1000)
2. https://acme.com/about (score: 900)
3. https://acme.com/products (score: 880)
4. https://acme.com/team (score: 890)
5. https://acme.com/contact (score: 860)
```

**Step 3: Scrape**
```
✓ Scraped https://acme.com/
✓ Scraped https://acme.com/about
✓ Scraped https://acme.com/products
✓ Scraped https://acme.com/team
✓ Scraped https://acme.com/contact

Total content: ~15,000 words
```

**Step 4: Extract Key Points**
```
Extracted 10 key insights:
- Leading cloud infrastructure provider
- Founded 2010, serving 10,000+ enterprises
- Specializes in scalable, secure platforms
- Mission: Simplify enterprise technology
- 3 main products: DB, Compute, Storage
- ...
```

### Output

```json
{
  "company_name": "Acme Corp",
  "website_url": "https://acme.com",
  "website_data": {
    "url": "https://acme.com",
    "title": "Acme Corp - Cloud Infrastructure",
    "description": "Leading provider...",
    "content": "## https://acme.com/\n# Acme Corp...",
    "key_points": [
      "Leading cloud infrastructure provider",
      "Founded 2010, serving 10,000+ enterprises",
      ...
    ],
    "pages_scraped": [
      "https://acme.com/",
      "https://acme.com/about",
      "https://acme.com/products",
      "https://acme.com/team",
      "https://acme.com/contact"
    ],
    "scraped_at": "2025-01-12T14:30:00"
  }
}
```

---

## Why This Approach?

### ✅ Efficient
- Scrapes only 5 pages instead of entire site
- Sitemap API call is cheap (1 credit)
- Scraping is expensive (1 credit per page)

### ✅ Intelligent
- Prioritizes important pages automatically
- Ignores blog posts, legal pages, etc.
- Gets the "executive summary" pages

### ✅ Fast
- 5 pages scrape in ~10-15 seconds
- Entire site might take 5+ minutes

### ✅ Cost-Effective
- **This approach**: 1 sitemap + 5 scrapes = 6 credits
- **Scraping everything**: 47 scrapes = 47 credits
- **Savings**: ~87% cost reduction

### ✅ High Quality
- Key pages have the most important information
- Removes fluff automatically
- Extracts actionable insights

---

## Configuration

### Adjust Number of Pages

```bash
# Default: 5 pages
python cli.py research "Acme" --website https://acme.com

# Custom: 3 pages
python cli.py research "Acme" --website https://acme.com --max-pages 3

# More detail: 10 pages
python cli.py research "Acme" --website https://acme.com --max-pages 10
```

### Customizing Priority Patterns

Edit `src/firecrawl_scraper.py`:

```python
PRIORITY_PATTERNS = [
    'about', 'team',           # Company info
    'products', 'services',    # Offerings
    'contact', 'careers',      # Contact/hiring
    'customers', 'partners',   # Social proof
    'blog', 'news',           # Updates
    
    # Add your own:
    'pricing', 'features',    # For SaaS companies
    'research', 'publications' # For research orgs
]
```

---

## Error Handling

### Sitemap Fails
```python
try:
    all_pages = get_sitemap(url)
except:
    # Fallback: just scrape homepage
    pages_to_scrape = [url]
```

### Page Scrape Fails
```python
for page_url in pages_to_scrape:
    try:
        content = scrape(page_url)
        all_content.append(content)
    except Exception as e:
        print(f"Failed to scrape {page_url}: {e}")
        continue  # Skip this page, continue with others
```

### No Key Points Found
```python
if not key_points:
    # Use page titles as fallback
    key_points = [page.title for page in scraped_pages]
```

---

## Performance Metrics

### Typical Run (5 pages)
- **Sitemap**: ~2 seconds
- **Ranking**: < 0.1 seconds
- **Scraping**: ~2 seconds per page = 10 seconds
- **Key points**: < 0.5 seconds
- **Total**: ~12-15 seconds

### Credits Used (Firecrawl)
- **Sitemap**: 1 credit
- **Scrape**: 1 credit per page
- **Total (5 pages)**: 6 credits

### Cost Estimate
- Firecrawl: $0.001 per credit
- **5 pages**: $0.006 (~1 cent)
- **100 companies**: ~$0.60

---

## Advanced: Adding AI Summarization

You can enhance key points with LLM summarization:

```python
from anthropic import Anthropic

def enhance_key_points(content: str) -> List[str]:
    """Use Claude to extract better key points."""
    
    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""Extract 5-10 key points from this company information:

{content[:10000]}  # Limit context

Format as bullet points."""
        }]
    )
    
    # Parse bullet points from response
    return parse_bullet_points(response.content[0].text)
```

This would give even better quality but adds cost and latency.

---

## Summary

The Firecrawl scraping logic is a **4-step intelligent pipeline**:

1. **Discover** all pages (sitemap)
2. **Rank** by importance (URL patterns)
3. **Scrape** top N pages (default: 5)
4. **Extract** key insights (headings + keywords)

This approach is:
- ✅ 87% cheaper than scraping everything
- ✅ 10x faster
- ✅ Higher quality (important pages only)
- ✅ Automatic (no manual page selection)

Perfect for B2B prospect research! 🎯
