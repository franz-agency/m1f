# Copyright 2025 Franz und Franz GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Abstract base class for web scrapers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, AsyncGenerator, Set
from pathlib import Path
import logging
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
import asyncio
import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class ScraperConfig:
    """Configuration for web scrapers."""

    max_depth: int = 10
    max_pages: int = 10000
    allowed_domains: Optional[List[str]] = None
    allowed_path: Optional[str] = None
    exclude_patterns: Optional[List[str]] = None
    respect_robots_txt: bool = True
    concurrent_requests: int = 5
    request_delay: float = 0.5
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    custom_headers: Optional[Dict[str, str]] = None
    timeout: float = 30.0
    follow_redirects: bool = True
    verify_ssl: bool = True
    ignore_get_params: bool = False
    check_canonical: bool = True
    check_content_duplicates: bool = True
    check_ssrf: bool = True

    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.allowed_domains is None:
            self.allowed_domains = []
        if self.exclude_patterns is None:
            self.exclude_patterns = []
        if self.custom_headers is None:
            self.custom_headers = {}


@dataclass
class ScrapedPage:
    """Represents a scraped web page."""

    url: str
    content: str
    title: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    encoding: str = "utf-8"
    status_code: Optional[int] = None
    headers: Optional[Dict[str, str]] = None
    normalized_url: Optional[str] = None
    canonical_url: Optional[str] = None
    content_checksum: Optional[str] = None
    file_type: str = "html"  # 'html', 'image', 'pdf', 'css', 'js', etc.
    file_size: Optional[int] = None  # File size in bytes
    is_binary: bool = False  # True for binary files like images, PDFs
    binary_content: Optional[bytes] = None  # Binary content for non-HTML files

    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.metadata is None:
            self.metadata = {}
        if self.headers is None:
            self.headers = {}


class WebScraperBase(ABC):
    """Abstract base class for web scrapers."""

    def __init__(self, config: ScraperConfig):
        """Initialize the scraper with configuration.

        Args:
            config: Scraper configuration
        """
        self.config = config
        self._visited_urls: Set[str] = set()
        self._robots_parsers: Dict[str, RobotFileParser] = {}
        self._robots_fetch_lock = asyncio.Lock()
        self._checksum_callback = None  # Callback to check if checksum exists

    @abstractmethod
    async def scrape_url(self, url: str) -> ScrapedPage:
        """Scrape a single URL.

        Args:
            url: URL to scrape

        Returns:
            ScrapedPage object containing the scraped content

        Raises:
            Exception: If scraping fails
        """
        pass

    @abstractmethod
    async def scrape_site(self, start_url: str) -> AsyncGenerator[ScrapedPage, None]:
        """Scrape an entire website starting from a URL.

        Args:
            start_url: URL to start crawling from

        Yields:
            ScrapedPage objects as they are scraped
        """
        pass

    def _is_private_ip(self, hostname: str) -> bool:
        """Check if hostname resolves to a private IP address.

        Args:
            hostname: Hostname or IP address to check

        Returns:
            True if the hostname resolves to a private IP, False otherwise
        """
        import socket
        import ipaddress

        try:
            # Set a timeout for DNS resolution to avoid hanging
            socket.setdefaulttimeout(2.0)
            # Get IP address from hostname
            ip = socket.gethostbyname(hostname)
            ip_obj = ipaddress.ip_address(ip)

            # Check for private networks
            if ip_obj.is_private:
                return True

            # Check for loopback
            if ip_obj.is_loopback:
                return True

            # Check for link-local
            if ip_obj.is_link_local:
                return True

            # Check for multicast
            if ip_obj.is_multicast:
                return True

            # Check for cloud metadata endpoint
            if str(ip_obj).startswith("169.254."):
                return True

            return False

        except (socket.gaierror, ValueError):
            # If we can't resolve the hostname, it's likely a normal website
            # with DNS issues or a domain that doesn't exist anymore
            # Don't treat this as a private IP
            return False

    async def validate_url(self, url: str) -> bool:
        """Validate if a URL should be scraped based on configuration and robots.txt.

        Args:
            url: URL to validate

        Returns:
            True if URL should be scraped, False otherwise
        """
        from urllib.parse import urlparse

        try:
            parsed = urlparse(url)

            # Check if URL has valid scheme
            if parsed.scheme not in ("http", "https"):
                return False

            # Extract hostname (remove port if present)
            hostname = parsed.hostname or parsed.netloc.split(":")[0]

            # Check for SSRF - block private IPs (if enabled)
            if self.config.check_ssrf and self._is_private_ip(hostname):
                logger.warning(f"Blocked URL {url} - private IP address detected")
                return False

            # Check allowed domains
            if self.config.allowed_domains:
                domain_allowed = False
                for domain in self.config.allowed_domains:
                    if domain in parsed.netloc:
                        domain_allowed = True
                        break
                if not domain_allowed:
                    return False

            # Check exclude patterns
            if self.config.exclude_patterns:
                for pattern in self.config.exclude_patterns:
                    if pattern in url:
                        logger.debug(f"URL {url} excluded by pattern: {pattern}")
                        return False

            return True

        except Exception as e:
            logger.error(f"Error validating URL {url}: {e}")
            return False

    async def _fetch_robots_txt(self, base_url: str) -> Optional[RobotFileParser]:
        """Fetch and parse robots.txt for a given base URL.

        Args:
            base_url: Base URL of the website

        Returns:
            RobotFileParser object or None if fetch fails
        """
        robots_url = urljoin(base_url, "/robots.txt")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    robots_url,
                    timeout=aiohttp.ClientTimeout(total=10),
                    headers={"User-Agent": self.config.user_agent},
                ) as response:
                    if response.status == 200:
                        content = await response.text()
                        parser = RobotFileParser()
                        parser.parse(content.splitlines())
                        return parser
                    else:
                        logger.debug(
                            f"No robots.txt found at {robots_url} (status: {response.status})"
                        )
                        return None
        except Exception as e:
            logger.debug(f"Error fetching robots.txt from {robots_url}: {e}")
            return None

    async def can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt.

        Args:
            url: URL to check

        Returns:
            True if URL can be fetched, False otherwise
        """
        if not self.config.respect_robots_txt:
            return True

        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # Check if we already have the robots.txt for this domain
        if base_url not in self._robots_parsers:
            async with self._robots_fetch_lock:
                # Double-check after acquiring lock
                if base_url not in self._robots_parsers:
                    parser = await self._fetch_robots_txt(base_url)
                    self._robots_parsers[base_url] = parser

        parser = self._robots_parsers.get(base_url)
        if parser is None:
            # No robots.txt or fetch failed - allow by default
            return True

        # Check if the URL is allowed for our user agent
        return parser.can_fetch(self.config.user_agent, url)

    def is_visited(self, url: str) -> bool:
        """Check if URL has already been visited.

        Args:
            url: URL to check

        Returns:
            True if URL has been visited, False otherwise
        """
        return url in self._visited_urls

    def mark_visited(self, url: str) -> None:
        """Mark URL as visited.

        Args:
            url: URL to mark as visited
        """
        self._visited_urls.add(url)

    def set_checksum_callback(self, callback):
        """Set callback function to check if content checksum exists.

        Args:
            callback: Function that takes a checksum string and returns bool
        """
        self._checksum_callback = callback
    
    def _is_url_allowed(self, url: str) -> bool:
        """Check if URL is allowed based on domain and path restrictions.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL is allowed, False otherwise
        """
        parsed = urlparse(url)
        
        # Check allowed domains if configured
        if hasattr(self.config, 'allowed_domains') and self.config.allowed_domains:
            if parsed.netloc not in self.config.allowed_domains:
                return False
        
        # Check allowed path if configured
        if hasattr(self.config, 'allowed_path') and self.config.allowed_path:
            if not parsed.path.startswith(self.config.allowed_path):
                return False
        
        # Check excluded paths if configured
        if hasattr(self.config, 'excluded_paths') and self.config.excluded_paths:
            for excluded in self.config.excluded_paths:
                if excluded in parsed.path:
                    return False
        
        return True

    async def download_binary_file(self, url: str, max_size: Optional[int] = None) -> Optional[ScrapedPage]:
        """Download binary content from URL with security checks.
        
        Args:
            url: URL to download
            max_size: Maximum file size in bytes
            
        Returns:
            ScrapedPage with binary content or None if download fails
        """
        import aiohttp
        import mimetypes
        from pathlib import Path
        
        # Security: For assets, we allow external domains (CDNs, etc.)
        # Assets like images, CSS, JS often come from CDNs and should be allowed
        # Path restrictions don't apply to assets - only to crawled HTML pages
        parsed = urlparse(url)
        
        # Check if external assets are allowed
        if hasattr(self.config, 'download_external_assets') and not self.config.download_external_assets:
            # If external assets are disabled, check if it's from allowed domains
            if hasattr(self.config, 'allowed_domains') and self.config.allowed_domains:
                if parsed.netloc not in self.config.allowed_domains:
                    logger.debug(f"External asset blocked (download_external_assets=False): {url}")
                    return None
        
        # Security: Check for SSRF if enabled (this is always important)
        if self.config.check_ssrf:
            if self._is_private_ip(parsed.netloc.split(':')[0]):
                logger.warning(f"SSRF protection: Blocked private IP for {url}")
                return None
        
        try:
            # Determine file type from URL
            parsed_url = urlparse(url)
            path = parsed_url.path.lower()
            file_extension = Path(path).suffix
            mime_type, _ = mimetypes.guess_type(path)
            
            # Determine file type category
            file_type = "unknown"
            if file_extension in [".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico"]:
                file_type = "image"
            elif file_extension == ".pdf":
                file_type = "pdf"
            elif file_extension == ".css":
                file_type = "css"
            elif file_extension == ".js":
                file_type = "js"
            elif file_extension in [".woff", ".woff2", ".ttf", ".eot"]:
                file_type = "font"
            elif file_extension in [".mp4", ".webm", ".mp3", ".wav", ".ogg"]:
                file_type = "media"
            elif file_extension in [".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"]:
                file_type = "document"
            elif file_extension in [".zip", ".tar", ".gz", ".rar", ".7z"]:
                file_type = "archive"
            elif file_extension in [".md", ".txt", ".csv", ".json", ".xml"]:
                file_type = "text"
            
            async with aiohttp.ClientSession() as session:
                headers = {"User-Agent": self.config.user_agent} if self.config.user_agent else {}
                async with session.get(url, headers=headers, timeout=self.config.timeout) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to download {url}: HTTP {response.status}")
                        return None
                    
                    # Security: Validate Content-Type header
                    content_type_header = response.headers.get('content-type', '').lower()
                    
                    # Block potentially dangerous content types
                    dangerous_content_types = [
                        'application/x-executable',
                        'application/x-msdownload', 
                        'application/x-msdos-program',
                        'application/x-sh',
                        'application/x-shellscript',
                        'application/x-httpd-php',
                        'application/x-httpd-cgi',
                    ]
                    
                    for dangerous_type in dangerous_content_types:
                        if dangerous_type in content_type_header:
                            logger.warning(f"Blocked dangerous content type {content_type_header}: {url}")
                            return None
                    
                    # Check content length
                    content_length = response.headers.get('content-length')
                    if content_length and max_size:
                        if int(content_length) > max_size:
                            logger.warning(f"File {url} too large: {content_length} bytes (max: {max_size})")
                            return None
                    
                    # Read content with size limit - read in chunks to prevent memory exhaustion
                    chunks = []
                    total_size = 0
                    chunk_size = 8192  # 8KB chunks
                    
                    async for chunk in response.content.iter_chunked(chunk_size):
                        total_size += len(chunk)
                        if max_size and total_size > max_size:
                            logger.warning(f"Downloaded file {url} exceeds size limit: {total_size} bytes")
                            return None
                        chunks.append(chunk)
                    
                    content = b''.join(chunks)
                    
                    # Validate file content
                    from ..file_validator import FileValidator
                    validation_result = FileValidator.validate_file(
                        content, file_extension, content_type_header
                    )
                    
                    if not validation_result['valid']:
                        logger.error(f"File validation failed for {url}: {validation_result['error']}")
                        # Still return the file but mark it as potentially invalid
                        # User can decide what to do with invalid files
                    
                    if validation_result.get('warnings'):
                        for warning in validation_result['warnings']:
                            logger.warning(f"File validation warning for {url}: {warning}")
                    
                    # Create ScrapedPage for binary content
                    page = ScrapedPage(
                        url=url,
                        content="",  # Empty for binary files
                        title=Path(parsed_url.path).name if parsed_url.path else "download",
                        metadata={
                            "mime_type": mime_type or "application/octet-stream",
                            "validation": validation_result
                        },
                        status_code=response.status,
                        headers=dict(response.headers),
                        file_type=file_type,
                        file_size=len(content),
                        is_binary=True,
                        binary_content=content
                    )
                    
                    return page
                    
        except asyncio.TimeoutError:
            logger.error(f"Timeout downloading {url}")
            return None
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            return None

    def is_asset_url(self, url: str, allowed_extensions: list[str]) -> bool:
        """Check if URL points to an asset file based on extension.
        
        Args:
            url: URL to check
            allowed_extensions: List of allowed file extensions (with dots)
            
        Returns:
            True if URL is for an allowed asset type
        """
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        
        for ext in allowed_extensions:
            if path.endswith(ext.lower()):
                return True
        return False

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass
