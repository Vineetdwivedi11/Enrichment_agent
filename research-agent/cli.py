#!/usr/bin/env python3
"""Enrichment Agent CLI - Extract structured data from websites."""

import json
from pathlib import Path
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from src.config import settings
from src.models import PromptTemplate, ExtractionSchema, EnrichmentResult
from src.scraper import FirecrawlScraper
from src.simple_scraper import SimpleScraper
from src.extractor import LLMExtractor
from src.models import WebsiteData
from src.linkedin_scraper import LinkedInScraper
from src.google_sheets import GoogleSheetsExporter


app = typer.Typer(help="Enrichment Agent - Extract structured data from websites")
console = Console()


@app.command()
def list_prompts():
    """List all available prompt templates."""
    prompts_dir = settings.PROMPTS_DIR
    
    if not prompts_dir.exists():
        console.print(f"[red]Prompts directory not found: {prompts_dir}[/red]")
        return
    
    prompt_files = list(prompts_dir.glob("*.txt")) + list(prompts_dir.glob("*.md"))
    
    if not prompt_files:
        console.print("[yellow]No prompt templates found[/yellow]")
        return
    
    table = Table(title="Available Prompt Templates")
    table.add_column("Name", style="cyan")
    table.add_column("Variables", style="magenta")
    
    for prompt_file in sorted(prompt_files):
        try:
            template = PromptTemplate.from_file(str(prompt_file))
            table.add_row(
                template.name,
                ", ".join(template.variables) if template.variables else "None"
            )
        except Exception as e:
            console.print(f"[red]Error loading {prompt_file}: {e}[/red]")
    
    console.print(table)


@app.command()
def list_schemas():
    """List all available extraction schemas."""
    schemas_dir = settings.SCHEMAS_DIR
    
    if not schemas_dir.exists():
        console.print(f"[red]Schemas directory not found: {schemas_dir}[/red]")
        return
    
    schema_files = list(schemas_dir.glob("*.json"))
    
    if not schema_files:
        console.print("[yellow]No extraction schemas found[/yellow]")
        return
    
    table = Table(title="Available Extraction Schemas")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Fields", style="magenta")
    
    for schema_file in sorted(schema_files):
        try:
            schema = ExtractionSchema.from_file(str(schema_file))
            desc = schema.description[:60] + "..." if len(schema.description) > 60 else schema.description
            table.add_row(schema.name, desc, str(len(schema.fields)))
        except Exception as e:
            console.print(f"[red]Error loading {schema_file}: {e}[/red]")
    
    console.print(table)


@app.command()
def enrich(
    url: str = typer.Argument(..., help="Website URL to enrich"),
    schema: str = typer.Option(..., "--schema", "-s", help="Schema name"),
    prompt: str = typer.Option(..., "--prompt", "-p", help="Prompt template name"),
    company_name: str = typer.Option(None, "--company", "-c", help="Company name"),
    output_file: str = typer.Option(None, "--output", "-o", help="Output JSON file"),
    var: list[str] = typer.Option(None, "--var", help="Template variables (format: key=value)")
):
    """Enrich a website URL using a prompt template and extraction schema."""
    
    template_vars = {}
    if var:
        for v in var:
            if "=" not in v:
                console.print(f"[red]Invalid variable format: {v}. Use key=value[/red]")
                return
            key, value = v.split("=", 1)
            template_vars[key.strip()] = value.strip()
    
    if company_name:
        template_vars["company_name"] = company_name
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        
        task = progress.add_task("Loading schema...", total=None)
        schema_file = settings.SCHEMAS_DIR / f"{schema}.json"
        
        if not schema_file.exists():
            console.print(f"[red]Schema not found: {schema_file}[/red]")
            return
        
        extraction_schema = ExtractionSchema.from_file(str(schema_file))
        progress.update(task, completed=True)
        console.print(f"[green]✓[/green] Loaded schema: {extraction_schema.name}")
        
        task = progress.add_task("Loading prompt template...", total=None)
        prompt_file = settings.PROMPTS_DIR / f"{prompt}.txt"
        if not prompt_file.exists():
            prompt_file = settings.PROMPTS_DIR / f"{prompt}.md"
        
        if not prompt_file.exists():
            console.print(f"[red]Prompt template not found: {prompt}[/red]")
            return
        
        prompt_template = PromptTemplate.from_file(str(prompt_file))
        progress.update(task, completed=True)
        console.print(f"[green]✓[/green] Loaded prompt: {prompt_template.name}")
        
        task = progress.add_task(f"Scraping {url}...", total=None)
        scraper = None
        if settings.USE_FREE_SCRAPER or not settings.FIRECRAWL_API_KEY:
            scraper = SimpleScraper()
            console.print("[dim]Using SimpleScraper (Free)[/dim]")
        else:
            scraper = FirecrawlScraper()
        
        try:
            website_content = scraper.scrape_website(url)
            progress.update(task, completed=True)
            console.print(f"[green]✓[/green] Scraped website ({len(website_content.content or '')} chars)")
        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"[red]✗[/red] Failed to scrape: {e}")
            return
        
        task = progress.add_task("Extracting data with Claude...", total=None)
        extractor = LLMExtractor()
        
        try:
            extracted_data = extractor.extract(
                website_content,
                prompt_template,
                extraction_schema,
                **template_vars
            )
            progress.update(task, completed=True)
            console.print(f"[green]✓[/green] Extracted {len(extracted_data)} fields")
        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"[red]✗[/red] Failed to extract: {e}")
            return
    
    result = EnrichmentResult(
        company_name=company_name or url,
        url=url,
        schema_used=extraction_schema.name,
        prompt_used=prompt_template.name,
        extracted_data=extracted_data,
        model_used=settings.ANTHROPIC_MODEL
    )
    
    console.print("\n[bold cyan]Extraction Results:[/bold cyan]")
    console.print(json.dumps(extracted_data, indent=2))
    
    if output_file:
        output_path = Path(output_file)
    else:
        settings.OUTPUT_DIR.mkdir(exist_ok=True)
        timestamp = result.enriched_at.strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in (company_name or "enrichment") if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        output_path = settings.OUTPUT_DIR / f"{safe_name}_{timestamp}.json"
    
    with open(output_path, 'w') as f:
        json.dump(result.to_json(), f, indent=2)
    
    console.print(f"\n[green]✓[/green] Saved to: {output_path}")


@app.command()
def batch(
    input_file: str = typer.Argument(..., help="CSV file with URLs"),
    schema: str = typer.Option(..., "--schema", "-s", help="Schema name"),
    prompt: str = typer.Option(..., "--prompt", "-p", help="Prompt template name"),
    url_column: str = typer.Option("url", "--url-col", help="Column name for URLs"),
    name_column: str = typer.Option("name", "--name-col", help="Column name for company names")
):
    """Batch enrich multiple URLs from a CSV file."""
    import csv
    
    input_path = Path(input_file)
    
    if not input_path.exists():
        console.print(f"[red]Input file not found: {input_file}[/red]")
        return
    
    urls_data = []
    with open(input_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            urls_data.append({
                "name": row.get(name_column, ""),
                "url": row.get(url_column, "")
            })
    
    console.print(f"[cyan]Processing {len(urls_data)} URLs...[/cyan]\n")
    
    schema_file = settings.SCHEMAS_DIR / f"{schema}.json"
    extraction_schema = ExtractionSchema.from_file(str(schema_file))
    
    prompt_file = settings.PROMPTS_DIR / f"{prompt}.txt"
    if not prompt_file.exists():
        prompt_file = settings.PROMPTS_DIR / f"{prompt}.md"
    prompt_template = PromptTemplate.from_file(str(prompt_file))
    
    scraper = None
    if settings.USE_FREE_SCRAPER or not settings.FIRECRAWL_API_KEY:
        scraper = SimpleScraper()
        console.print("[dim]Using SimpleScraper (Free)[/dim]")
    else:
        scraper = FirecrawlScraper()
    extractor = LLMExtractor()
    
    results = []
    
    for idx, item in enumerate(urls_data, 1):
        url = item.get("url", "")
        name = item.get("name", url)
        
        console.print(f"[{idx}/{len(urls_data)}] Processing: {name}")
        
        try:
            website_content = scraper.scrape_website(url)
            extracted_data = extractor.extract(
                website_content,
                prompt_template,
                extraction_schema,
                company_name=name
            )
            
            result = EnrichmentResult(
                company_name=name,
                url=url,
                schema_used=extraction_schema.name,
                prompt_used=prompt_template.name,
                extracted_data=extracted_data,
                model_used=settings.ANTHROPIC_MODEL
            )
            
            results.append(result)
            console.print(f"  [green]✓[/green] Success\n")
        
        except Exception as e:
            console.print(f"  [red]✗[/red] Error: {e}\n")
            continue
    
    settings.OUTPUT_DIR.mkdir(exist_ok=True)
    timestamp = results[0].enriched_at.strftime("%Y%m%d_%H%M%S") if results else "empty"
    output_path = settings.OUTPUT_DIR / f"batch_{timestamp}.json"
    
    with open(output_path, 'w') as f:
        json.dump([r.to_json() for r in results], f, indent=2)
    
    console.print(f"\n[green]✓[/green] Processed {len(results)}/{len(urls_data)} successfully")
    console.print(f"[green]✓[/green] Saved to: {output_path}")


if __name__ == "__main__":
    app()
