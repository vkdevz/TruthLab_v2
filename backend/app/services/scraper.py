import ipaddress
import socket
from urllib.parse import urlparse
import httpx
import trafilatura
from fastapi import HTTPException


class ScraperService:
    @staticmethod
    def validate_url_safety(url: str) -> None:
        """Validates that a URL does not point to localhost, private IP networks, or metadata servers (anti-SSRF)."""
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise HTTPException(status_code=400, detail="Only HTTP and HTTPS URLs are permitted.")

        hostname = parsed.hostname
        if not hostname:
            raise HTTPException(status_code=400, detail="Invalid target URL.")

        # Disallow localhost keywords
        if hostname.lower() in {"localhost", "127.0.0.1", "0.0.0.0", "::1"}:
            raise HTTPException(status_code=400, detail="Access to localhost is prohibited.")

        # Resolve IP and verify it is not in private/link-local/loopback ranges
        try:
            ip_str = socket.gethostbyname(hostname)
            ip_obj = ipaddress.ip_address(ip_str)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved:
                raise HTTPException(
                    status_code=400,
                    detail=f"Access to private or local network IP addresses ({ip_str}) is prohibited."
                )
        except socket.gaierror:
            raise HTTPException(status_code=400, detail=f"Could not resolve domain: {hostname}")

    async def fetch_article_content(self, url: str) -> dict[str, str]:
        """Fetches and extracts clean body text and metadata from an article URL."""
        self.validate_url_safety(url)

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to fetch content from URL: {str(exc)}"
                )

        html_content = response.text
        
        # Use Trafilatura for precise readability extraction
        extracted_text = trafilatura.extract(
            html_content,
            include_comments=False,
            include_tables=True,
            no_fallback=False
        )
        
        extracted_meta = trafilatura.extract_metadata(html_content)
        title = extracted_meta.title if extracted_meta and extracted_meta.title else ""
        date = extracted_meta.date if extracted_meta and extracted_meta.date else ""

        if not extracted_text:
            raise HTTPException(
                status_code=422,
                detail="Could not extract readable article text from the provided URL."
            )

        return {
            "title": title,
            "publication_date": date,
            "text": extracted_text,
            "source_domain": urlparse(url).netloc,
        }


scraper_service = ScraperService()
