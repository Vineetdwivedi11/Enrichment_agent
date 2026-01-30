"""Enrichment Agent - Extract structured data from websites."""

from .config import settings
from .models import ExtractionSchema, PromptTemplate, EnrichmentResult, WebsiteContent
from .scraper import FirecrawlScraper
from .extractor import LLMExtractor

__version__ = "2.0.0"

__all__ = [
    "settings",
    "ExtractionSchema",
    "PromptTemplate",
    "EnrichmentResult",
    "WebsiteContent",
    "FirecrawlScraper",
    "LLMExtractor",
]
