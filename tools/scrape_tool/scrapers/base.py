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

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass
