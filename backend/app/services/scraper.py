from urllib.parse import urlparse
from fastapi import HTTPException
from backend.app.ingestion.url_ingest import URLValidator, url_ingestion_service


class ScraperService:
    """Safe URL scraping adapter delegating to URLValidator and URLIngestionService
    for unified Anti-SSRF enforcement and content extraction."""

    @staticmethod
    def validate_url_safety(url: str) -> None:
        """Validates that a URL is safe against SSRF, redirect loops, private IPs, and loopback addresses."""
        URLValidator.validate_url(url)

    async def fetch_article_content(self, url: str) -> dict[str, str]:
        """Safely fetches and extracts clean body text and metadata from an article URL."""
        article_data = await url_ingestion_service.ingest_url(url)
        return {
            "title": article_data.get("title", ""),
            "publication_date": article_data.get("publication_date", ""),
            "text": article_data.get("text", ""),
            "source_domain": article_data.get("source_domain", urlparse(url).netloc),
        }


scraper_service = ScraperService()
