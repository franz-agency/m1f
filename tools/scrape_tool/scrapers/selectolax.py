#!/usr/bin/env python3
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

"""httpx + selectolax scraper backend for blazing fast HTML parsing."""

import asyncio
import logging
from typing import AsyncIterator, Set, Optional, Dict, Any
from urllib.parse import urljoin, urlparse
import re

try:
    import httpx
    from selectolax.parser import HTMLParser

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from .base import WebScraperBase, ScrapedPage, ScraperConfig

logger = logging.getLogger(__name__)


class SelectolaxScraper(WebScraperBase):
    """High-performance scraper using httpx for async HTTP and selectolax for parsing.

    This scraper is optimized for speed and low memory usage. It uses:
    - httpx: Modern async HTTP client with connection pooling
    - selectolax: Blazing fast HTML parser built on C libraries

    Best for:
    - Large-scale scraping where performance is critical
    - Simple HTML parsing without JavaScript
    - Minimal resource usage requirements
    """

    def __init__(self, config: ScraperConfig):
        """Initialize the selectolax scraper.

        Args:
            config: Scraper configuration

        Raises:
            ImportError: If httpx or selectolax are not installed
        """
        if not HTTPX_AVAILABLE:
            raise ImportError(
                "httpx and selectolax are required for this scraper. "
                "Install with: pip install httpx selectolax"
            )

        super().__init__(config)
        self._client: Optional[httpx.AsyncClient] = None
        self._visited_urls: Set[str] = set()
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL by removing GET parameters if configured.
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized URL
        """
        if self.config.ignore_get_params and "?" in url:
            return url.split("?")[0]
        return url

    async def __aenter__(self):
        """Enter async context and create HTTP client."""
        # Configure client with connection pooling for performance
        limits = httpx.Limits(
            max_keepalive_connections=20,
            max_connections=self.config.concurrent_requests * 2,
            keepalive_expiry=30.0,
        )

        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.config.timeout),
            limits=limits,
            follow_redirects=self.config.follow_redirects,
            headers={"User-Agent": self.config.user_agent},
        )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context and cleanup."""
        if self._client:
            await self._client.aclose()

    async def scrape_url(self, url: str) -> ScrapedPage:
        """Scrape a single URL.

        Args:
            url: URL to scrape

        Returns:
            ScrapedPage object with scraped content

        Raises:
            Exception: If scraping fails
        """
        if not self._client:
            raise RuntimeError("Scraper not initialized. Use async context manager.")

        try:
            # Check robots.txt before scraping
            if not await self.can_fetch(url):
                raise ValueError(f"URL {url} is blocked by robots.txt")

            # Make HTTP request
            response = await self._client.get(url)
            response.raise_for_status()

            # Parse HTML with selectolax
            html_parser = HTMLParser(response.text)
            
            # Store metadata for database
            normalized_url = self._normalize_url(str(response.url))
            canonical_url = None
            content_checksum = None
            
            # Order: 1. GET parameter normalization (already done in _normalize_url)
            # 2. Canonical URL check
            if self.config.check_canonical:
                canonical_link = html_parser.css_first('link[rel="canonical"]')
                if canonical_link and canonical_link.attributes.get("href"):
                    canonical_url = canonical_link.attributes["href"]
                    # Make canonical URL absolute
                    canonical_url = urljoin(url, canonical_url)
                    # Normalize canonical URL too
                    normalized_canonical = self._normalize_url(canonical_url)
                    
                    if normalized_url != normalized_canonical:
                        logger.info(f"Skipping {url} - canonical URL differs: {canonical_url}")
                        return None  # Return None to indicate skip, not an error
            
            # 3. Content duplicate check
            if self.config.check_content_duplicates:
                from ..utils import calculate_content_checksum
                content_checksum = calculate_content_checksum(response.text)
                
                # Check if checksum exists using callback
                if self._checksum_callback and self._checksum_callback(content_checksum):
                    logger.info(f"Skipping {url} - duplicate content detected")
                    return None  # Return None to indicate skip, not an error

            # Extract title
            title = ""
            title_tag = html_parser.css_first("title")
            if title_tag:
                title = title_tag.text(strip=True)

            # Extract metadata
            metadata = {}

            # Get meta description
            meta_desc = html_parser.css_first('meta[name="description"]')
            if meta_desc:
                metadata["description"] = meta_desc.attributes.get("content", "")

            # Get meta keywords
            meta_keywords = html_parser.css_first('meta[name="keywords"]')
            if meta_keywords:
                metadata["keywords"] = meta_keywords.attributes.get("content", "")

            # Get Open Graph data
            for og_tag in html_parser.css('meta[property^="og:"]'):
                prop = og_tag.attributes.get("property", "")
                content = og_tag.attributes.get("content", "")
                if prop and content:
                    metadata[prop] = content

            # Detect encoding from meta tag or response
            encoding = response.encoding or "utf-8"
            meta_charset = html_parser.css_first("meta[charset]")
            if meta_charset:
                encoding = meta_charset.attributes.get("charset", encoding)
            else:
                # Check for http-equiv Content-Type
                meta_content_type = html_parser.css_first(
                    'meta[http-equiv="Content-Type"]'
                )
                if meta_content_type:
                    content = meta_content_type.attributes.get("content", "")
                    match = re.search(r"charset=([^;]+)", content)
                    if match:
                        encoding = match.group(1).strip()

            return ScrapedPage(
                url=str(response.url),  # Use final URL after redirects
                content=response.text,
                title=title,
                encoding=encoding,
                status_code=response.status_code,
                headers=dict(response.headers),
                metadata=metadata,
                normalized_url=normalized_url,
                canonical_url=canonical_url,
                content_checksum=content_checksum,
            )

        except httpx.HTTPError as e:
            logger.error(f"HTTP error scraping {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            raise

    async def scrape_site(self, start_url: str) -> AsyncIterator[ScrapedPage]:
        """Scrape an entire website starting from the given URL.

        Args:
            start_url: Starting URL for crawling

        Yields:
            ScrapedPage objects for each scraped page
        """
        if not self._client:
            raise RuntimeError("Scraper not initialized. Use async context manager.")

        # Parse start URL to get base domain
        parsed_start = urlparse(start_url)
        base_domain = parsed_start.netloc
        
        # Store the base path for subdirectory restriction
        base_path = parsed_start.path.rstrip('/')
        if base_path:
            logger.info(f"Restricting crawl to subdirectory: {base_path}")

        # Initialize queue with start URL
        queue = asyncio.Queue()
        await queue.put((start_url, 0))  # (url, depth)

        # Track visited URLs
        self._visited_urls.clear()
        normalized_start = self._normalize_url(start_url)
        self._visited_urls.add(normalized_start)

        # Semaphore for concurrent requests
        semaphore = asyncio.Semaphore(self.config.concurrent_requests)

        # Active tasks
        tasks = set()
        pages_scraped = 0

        async def process_url(url: str, depth: int):
            """Process a single URL."""
            async with semaphore:
                try:
                    # Respect request delay
                    if self.config.request_delay > 0:
                        await asyncio.sleep(self.config.request_delay)

                    # Scrape the page
                    page = await self.scrape_url(url)
                    
                    # Skip if page is None (duplicate content or canonical mismatch)
                    if page is None:
                        return None

                    # Extract links if not at max depth
                    if depth < self.config.max_depth:
                        html_parser = HTMLParser(page.content)

                        for link in html_parser.css("a[href]"):
                            href = link.attributes.get("href", "")
                            if not href:
                                continue

                            # Resolve relative URLs
                            absolute_url = urljoin(url, href)

                            # Parse URL
                            parsed_url = urlparse(absolute_url)

                            # Skip if different domain (unless allowed)
                            if self.config.allowed_domains:
                                if parsed_url.netloc not in self.config.allowed_domains:
                                    continue
                            elif parsed_url.netloc != base_domain:
                                continue

                            # Check subdirectory restriction
                            if base_path:
                                if not parsed_url.path.startswith(base_path + '/') and parsed_url.path != base_path:
                                    continue

                            # Skip if matches exclude pattern
                            if self.config.exclude_patterns:
                                if any(
                                    re.match(pattern, absolute_url)
                                    for pattern in self.config.exclude_patterns
                                ):
                                    continue

                            # Normalize URL
                            normalized_url = self._normalize_url(absolute_url)
                            
                            # Skip if already visited
                            if normalized_url in self._visited_urls:
                                continue

                            # Skip non-HTTP(S) URLs
                            if parsed_url.scheme not in ("http", "https"):
                                continue

                            # Add to queue
                            self._visited_urls.add(normalized_url)
                            await queue.put((normalized_url, depth + 1))

                    return page

                except Exception as e:
                    logger.error(f"Error processing {url}: {e}")
                    return None

        # Process URLs from queue
        while not queue.empty() or tasks:
            # Start new tasks if under limit
            while not queue.empty() and len(tasks) < self.config.concurrent_requests:
                try:
                    url, depth = queue.get_nowait()

                    # Check max pages limit
                    if pages_scraped >= self.config.max_pages:
                        break

                    # Create task
                    task = asyncio.create_task(process_url(url, depth))
                    tasks.add(task)

                except asyncio.QueueEmpty:
                    break

            # Wait for at least one task to complete
            if tasks:
                done, tasks = await asyncio.wait(
                    tasks, return_when=asyncio.FIRST_COMPLETED
                )

                # Process completed tasks
                for task in done:
                    page = await task
                    if page:
                        pages_scraped += 1
                        yield page

                        # Check if we've hit the page limit
                        if pages_scraped >= self.config.max_pages:
                            # Cancel remaining tasks
                            for t in tasks:
                                t.cancel()
                            return

        logger.info(f"Scraping complete. Scraped {pages_scraped} pages")
