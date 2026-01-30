#!/usr/bin/env python3
"""
Research Agent CLI - Prospect Intelligence Tool

Scrapes website data using Firecrawl and LinkedIn data using Bright Data APIs
to generate comprehensive prospect research reports.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from config import settings
from firecrawl_scraper import FirecrawlScraper
from linkedin_scraper import LinkedInScraper
from google_sheets import GoogleSheetsExporter
from models import ProspectResearch

app = typer.Typer(help="Research Agent - Automated Prospect Intelligence Tool")
console = Console()


@app.command()
def research(
    company_name: str = typer.Argument(..., help="Company name to research"),
    website: Optional[str] = typer.Option(None, "--website", "-w", help="Company website URL"),
    linkedin_url: Optional[str] = typer.Option(None, "--linkedin", "-l", help="LinkedIn company URL"),
    max_pages: int = typer.Option(5, "--max-pages", "-m", help="Maximum pages to scrape per website"),
    output_json: bool = typer.Option(True, "--json/--no-json", help="Save JSON output"),
    output_sheet: bool = typer.Option(False, "--sheet/--no-sheet", help="Export to Google Sheets"),
    sheet_name: Optional[str] = typer.Option(None, "--sheet-name", help="Google Sheet name (if exporting)"),
    output_dir: Path = typer.Option(Path("./output"), "--output-dir", "-o", help="Output directory"),
):
    """
    Research a company/prospect using website scraping and LinkedIn data.
    
    Examples:
        research-agent research "Acme Corp" --website https://acme.com --max-pages 5
        research-agent research "Acme Corp" --website https://acme.com --linkedin https://linkedin.com/company/acme
        research-agent research "Acme Corp" --website https://acme.com --sheet --sheet-name "Q1 Prospects"
    """
    
    console.print(f"\n[bold cyan]🔍 Starting research for:[/bold cyan] {company_name}\n")
    
    # Run async operations
    import asyncio
    asyncio.run(_research_async(
        company_name, website, linkedin_url, max_pages,
        output_json, output_sheet, sheet_name, output_dir
    ))


async def _research_async(
    company_name: str,
    website: Optional[str],
    linkedin_url: Optional[str],
    max_pages: int,
    output_json: bool,
    output_sheet: bool,
    sheet_name: Optional[str],
    output_dir: Path
):
    """Async research operation."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # Initialize research object
        research_data = ProspectResearch(
            company_name=company_name,
            website_url=website,
            linkedin_url=linkedin_url,
            timestamp=datetime.now()
        )
        
        # 1. Scrape website if provided
        if website:
            task = progress.add_task(f"Scraping website (max {max_pages} pages)...", total=None)
            try:
                scraper = FirecrawlScraper()
                website_data = scraper.scrape_website(website, max_pages=max_pages)
                research_data.website_data = website_data
                progress.update(task, completed=True)
                console.print(f"[green]✓[/green] Scraped {len(website_data.pages_scraped)} pages")
                console.print(f"[green]✓[/green] Extracted {len(website_data.key_points)} key points")
            except Exception as e:
                progress.update(task, completed=True)
                console.print(f"[yellow]⚠[/yellow] Website scraping failed: {e}")
        
        # 2. Scrape LinkedIn if provided
        if linkedin_url:
            task = progress.add_task("Fetching LinkedIn company data...", total=None)
            try:
                linkedin = LinkedInScraper()
                company_data = await linkedin.scrape_company(linkedin_url)
                research_data.linkedin_company_data = company_data
                progress.update(task, completed=True)
                console.print(f"[green]✓[/green] LinkedIn company data fetched (source: {company_data.source})")
            except Exception as e:
                progress.update(task, completed=True)
                console.print(f"[yellow]⚠[/yellow] LinkedIn scraping failed: {e}")
            
            # Get company posts
            task = progress.add_task("Fetching LinkedIn posts...", total=None)
            try:
                posts = await linkedin.get_company_posts(linkedin_url, limit=10)
                research_data.linkedin_posts = posts
                progress.update(task, completed=True)
                if posts:
                    console.print(f"[green]✓[/green] Fetched {len(posts)} LinkedIn posts (source: {posts[0].source})")
                else:
                    console.print(f"[yellow]⚠[/yellow] No LinkedIn posts found")
            except Exception as e:
                progress.update(task, completed=True)
                console.print(f"[yellow]⚠[/yellow] Failed to fetch posts: {e}")
    
    # 3. Save outputs
    console.print("\n[bold cyan]💾 Saving results...[/bold cyan]\n")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    if output_json:
        json_file = output_dir / f"{company_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_file, 'w') as f:
            json.dump(research_data.model_dump(), f, indent=2, default=str)
        console.print(f"[green]✓[/green] JSON saved: {json_file}")
    
    # Export to Google Sheets
    if output_sheet:
        try:
            exporter = GoogleSheetsExporter()
            sheet_url = exporter.export_research(research_data, sheet_name)
            console.print(f"[green]✓[/green] Google Sheet created: {sheet_url}")
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to export to Google Sheets: {e}")
    
    console.print("\n[bold green]✅ Research completed![/bold green]\n")


@app.command()
def linkedin_profile(
    profile_url: str = typer.Argument(..., help="LinkedIn profile URL"),
    output_json: bool = typer.Option(True, "--json/--no-json", help="Save JSON output"),
    output_dir: Path = typer.Option(Path("./output"), "--output-dir", "-o", help="Output directory"),
):
    """
    Research an individual LinkedIn profile.
    
    Example:
        research-agent linkedin-profile "https://linkedin.com/in/john-doe"
    """
    
    console.print(f"\n[bold cyan]🔍 Fetching LinkedIn profile:[/bold cyan] {profile_url}\n")
    
    try:
        linkedin = LinkedInScraper()
        profile_data = linkedin.scrape_profile(profile_url)
        
        console.print("[green]✓[/green] Profile data fetched successfully\n")
        
        if output_json:
            output_dir.mkdir(parents=True, exist_ok=True)
            json_file = output_dir / f"linkedin_profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(json_file, 'w') as f:
                json.dump(profile_data, f, indent=2, default=str)
            console.print(f"[green]✓[/green] JSON saved: {json_file}")
        
        console.print("\n[bold green]✅ Complete![/bold green]\n")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        sys.exit(1)


@app.command()
def config_check():
    """Check configuration and API credentials."""
    
    console.print("\n[bold cyan]⚙️  Configuration Check[/bold cyan]\n")
    
    checks = {
        "Firecrawl API Key": bool(settings.FIRECRAWL_API_KEY),
        "Bright Data API Key": bool(settings.BRIGHTDATA_API_KEY),
        "Google Sheets Credentials": settings.GOOGLE_CREDENTIALS_PATH.exists() if settings.GOOGLE_CREDENTIALS_PATH else False,
    }
    
    for name, status in checks.items():
        icon = "✓" if status else "✗"
        color = "green" if status else "red"
        console.print(f"[{color}]{icon}[/{color}] {name}")
    
    console.print()


if __name__ == "__main__":
    app()
