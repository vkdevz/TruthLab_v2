import ipaddress
import socket
from urllib.parse import urlparse
import httpx
import trafilatura
from fastapi import HTTPException


class URLValidator:
    """Validates URLs and enforces strict Anti-SSRF constraints."""

    ALLOWED_SCHEMES = {"http", "https"}
    ALLOWED_PORTS = {80, 443, 8080, 8443}
    BLOCKED_HOSTNAMES = {
        "localhost", "127.0.0.1", "0.0.0.0", "::1",
        "metadata.google.internal", "169.254.169.254", "instance-data",
        "metadata", "kubernetes.default", "metadata.azure.com",
    }
    BLOCKED_NETWORKS = [
        ipaddress.ip_network("10.0.0.0/8"),          # RFC 1918 Private
        ipaddress.ip_network("172.16.0.0/12"),        # RFC 1918 Private
        ipaddress.ip_network("192.168.0.0/16"),       # RFC 1918 Private
        ipaddress.ip_network("127.0.0.0/8"),          # Loopback
        ipaddress.ip_network("169.254.0.0/16"),       # Link-local / Cloud Metadata
        ipaddress.ip_network("100.64.0.0/10"),        # Carrier-Grade NAT (RFC 6598)
        ipaddress.ip_network("192.0.2.0/24"),         # TEST-NET-1
        ipaddress.ip_network("198.51.100.0/24"),      # TEST-NET-2
        ipaddress.ip_network("203.0.113.0/24"),       # TEST-NET-3
        ipaddress.ip_network("198.18.0.0/15"),        # Benchmark testing
        ipaddress.ip_network("224.0.0.0/4"),          # Multicast
        ipaddress.ip_network("240.0.0.0/4"),          # Reserved / Future use
        ipaddress.ip_network("0.0.0.0/8"),            # Broadcast
        ipaddress.ip_network("::1/128"),              # IPv6 Loopback
        ipaddress.ip_network("fc00::/7"),             # IPv6 Unique Local Address
        ipaddress.ip_network("fe80::/10"),            # IPv6 Link-local
        ipaddress.ip_network("ff00::/8"),             # IPv6 Multicast
        ipaddress.ip_network("2001:db8::/32"),        # IPv6 Documentation
    ]

    @classmethod
    def _is_blocked_ip(cls, ip_obj: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved or ip_obj.is_multicast or ip_obj.is_unspecified:
            return True
        for net in cls.BLOCKED_NETWORKS:
            if ip_obj in net:
                return True
        if hasattr(ip_obj, "ipv4_mapped") and ip_obj.ipv4_mapped:
            return cls._is_blocked_ip(ip_obj.ipv4_mapped)
        return False

    @classmethod
    def validate_url(cls, url: str) -> None:
        if not url or not isinstance(url, str):
            raise HTTPException(status_code=400, detail="URL must be a non-empty string.")

        if "\x00" in url:
            raise HTTPException(status_code=400, detail="Null bytes are strictly prohibited in URLs.")

        try:
            parsed = urlparse(url.strip())
        except Exception:
            raise HTTPException(status_code=400, detail="Malformed URL structure.")

        if parsed.scheme.lower() not in cls.ALLOWED_SCHEMES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported URL scheme '{parsed.scheme}'. Only HTTP and HTTPS are permitted."
            )

        if parsed.username or parsed.password:
            raise HTTPException(status_code=400, detail="User authentication credentials in URLs are prohibited.")

        hostname = parsed.hostname
        if not hostname:
            raise HTTPException(status_code=400, detail="URL must include a valid hostname.")

        if hostname.lower() in cls.BLOCKED_HOSTNAMES:
            raise HTTPException(status_code=400, detail=f"Access to blocked hostname '{hostname}' is forbidden.")

        # Port validation if explicit port is provided
        if parsed.port and parsed.port not in cls.ALLOWED_PORTS:
            raise HTTPException(
                status_code=400,
                detail=f"Forbidden port '{parsed.port}'. Permitted ports: {sorted(cls.ALLOWED_PORTS)}"
            )

        # Check if hostname directly represents an IP literal or obfuscated IP
        if "0x" in hostname.lower():
            raise HTTPException(
                status_code=400,
                detail=f"Obfuscated hexadecimal IP address formats ({hostname}) are strictly prohibited."
            )

        dot_parts = hostname.split(".")
        if all(p.isdigit() for p in dot_parts) and 1 <= len(dot_parts) <= 4:
            # Check for leading zero octal obfuscation or integer IP
            if any(len(p) > 1 and p.startswith("0") for p in dot_parts) or len(dot_parts) < 4:
                raise HTTPException(
                    status_code=400,
                    detail=f"Obfuscated octal or non-canonical IP address formats ({hostname}) are strictly prohibited."
                )

        try:
            direct_ip = ipaddress.ip_address(hostname)
            if cls._is_blocked_ip(direct_ip):
                raise HTTPException(
                    status_code=400,
                    detail=f"Access to private/local network address ({hostname}) is prohibited."
                )
        except ValueError:
            pass  # It is a domain name, proceed to DNS resolution

        # DNS resolution to verify destination IP is public
        try:
            addr_info = socket.getaddrinfo(hostname, None)
            for item in addr_info:
                ip_str = item[4][0]
                ip_obj = ipaddress.ip_address(ip_str)
                if cls._is_blocked_ip(ip_obj):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Access to private/local network address ({ip_str}) is prohibited."
                    )
        except socket.gaierror:
            raise HTTPException(status_code=400, detail=f"Could not resolve hostname: '{hostname}'.")


class URLIngestionService:
    """Safely fetches and parses web article content with timeout, size, and redirect boundaries."""

    MAX_RESPONSE_BYTES = 5 * 1024 * 1024  # 5 MB
    REQUEST_TIMEOUT_SECONDS = 8.0
    MAX_REDIRECTS = 3

    def __init__(self, validator: type[URLValidator] = URLValidator):
        self.validator = validator

    async def ingest_url(self, url: str) -> dict[str, str]:
        clean_url = url.strip()
        self.validator.validate_url(clean_url)

        headers = {
            "User-Agent": "MisinformationVerifier/1.0 (Research Bot; +https://domain.edu/bot)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        # Follow redirects safely while validating each destination hop against SSRF
        current_url = clean_url
        redirect_count = 0
        html_content = ""

        async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT_SECONDS, follow_redirects=False) as client:
            while True:
                try:
                    response = await client.get(current_url, headers=headers)
                except httpx.TimeoutException:
                    raise HTTPException(status_code=504, detail="Target URL request timed out.")
                except httpx.HTTPError as exc:
                    raise HTTPException(status_code=400, detail=f"HTTP connection failed: {str(exc)}")

                if response.is_redirect:
                    redirect_count += 1
                    if redirect_count > self.MAX_REDIRECTS:
                        raise HTTPException(status_code=400, detail="Too many redirects encountered.")
                    
                    location = response.headers.get("Location")
                    if not location:
                        raise HTTPException(status_code=400, detail="Malformed redirect without Location header.")
                    
                    # Resolve relative redirect
                    from urllib.parse import urljoin
                    next_url = urljoin(current_url, location)
                    self.validator.validate_url(next_url)
                    current_url = next_url
                    continue

                if response.status_code >= 400:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Target URL returned error HTTP {response.status_code}."
                    )

                content_type = response.headers.get("Content-Type", "").lower()
                if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unsupported Content-Type '{content_type}'. Target must be HTML."
                    )

                if len(response.content) > self.MAX_RESPONSE_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail="HTML page exceeds maximum allowed size of 5 MB."
                    )

                html_content = response.text
                break

        # Extract readable content via Trafilatura
        extracted_text = trafilatura.extract(
            html_content,
            include_comments=False,
            include_tables=False,
            no_fallback=False
        )

        metadata = trafilatura.extract_metadata(html_content)
        title = metadata.title if metadata and metadata.title else ""
        date = metadata.date if metadata and metadata.date else ""

        if not extracted_text or len(extracted_text.strip()) < 20:
            raise HTTPException(
                status_code=422,
                detail="Unable to extract substantial readable article content from URL."
            )

        return {
            "title": title,
            "publication_date": date,
            "text": extracted_text.strip(),
            "source_domain": urlparse(current_url).netloc,
            "canonical_url": current_url,
        }


url_ingestion_service = URLIngestionService()
