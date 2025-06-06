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

"""BeautifulSoup4-based web scraper implementation."""

import asyncio
import logging
from typing import Set, AsyncGenerator, Optional, Dict
from urllib.parse import urljoin, urlparse, unquote
import aiohttp
from bs4 import BeautifulSoup
import chardet

from .base import WebScraperBase, ScrapedPage, ScraperConfig

logger = logging.getLogger(__name__)


class BeautifulSoupScraper(WebScraperBase):
    """BeautifulSoup4-based web scraper for simple HTML extraction."""

    def __init__(self, config: ScraperConfig):
        """Initialize the BeautifulSoup scraper.

        Args:
            config: Scraper configuration
        """
        super().__init__(config)
        self.session: Optional[aiohttp.ClientSession] = None
        self._semaphore = asyncio.Semaphore(config.concurrent_requests)

    async def __aenter__(self):
        """Create aiohttp session on entry."""
        headers = {}

        # Only add User-Agent if it's not None
        if self.config.user_agent:
            headers["User-Agent"] = self.config.user_agent

        if self.config.custom_headers:
            # Filter out None keys when updating headers
            for k, v in self.config.custom_headers.items():
                if k is not None and v is not None:
                    headers[k] = v

        # Final validation to ensure no None values
        headers = {k: v for k, v in headers.items() if k is not None and v is not None}

        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        connector = aiohttp.TCPConnector(
            ssl=self.config.verify_ssl, limit=self.config.concurrent_requests * 2
        )

        self.session = aiohttp.ClientSession(
            headers=headers, timeout=timeout, connector=connector
        )
        return self

    async def __aexit__(self, *args):
        """Close aiohttp session on exit."""
        if self.session and not self.session.closed:
            await self.session.close()
            # Small delay to allow connections to close properly
            await asyncio.sleep(0.25)

    async def scrape_url(self, url: str) -> ScrapedPage:
        """Scrape a single URL using BeautifulSoup.

        Args:
            url: URL to scrape

        Returns:
            ScrapedPage object containing the scraped content

        Raises:
            Exception: If scraping fails
        """
        if not self.session:
            raise RuntimeError("Scraper must be used as async context manager")

        async with self._semaphore:  # Limit concurrent requests
            try:
                logger.info(f"Scraping URL: {url}")

                async with self.session.get(
                    url, allow_redirects=self.config.follow_redirects
                ) as response:
                    # Get response info
                    status_code = response.status
                    # Convert headers to dict with string keys, skip None keys
                    headers = {}
                    for k, v in response.headers.items():
                        if k is not None:
                            headers[str(k)] = str(v)

                    # Handle encoding
                    content_bytes = await response.read()

                    # Try to detect encoding if not specified
                    encoding = response.charset
                    if not encoding:
                        detected = chardet.detect(content_bytes)
                        encoding = detected.get("encoding", "utf-8")
                        logger.debug(f"Detected encoding for {url}: {encoding}")

                    # Decode content
                    try:
                        content = content_bytes.decode(encoding or "utf-8")
                    except (UnicodeDecodeError, LookupError):
                        # Fallback to utf-8 with error handling
                        content = content_bytes.decode("utf-8", errors="replace")
                        encoding = "utf-8"

                    # Parse with BeautifulSoup
                    soup = BeautifulSoup(content, "html.parser")

                    # Extract metadata
                    title = soup.find("title")
                    title_text = title.get_text(strip=True) if title else None

                    metadata = self._extract_metadata(soup)

                    return ScrapedPage(
                        url=str(response.url),  # Use final URL after redirects
                        content=str(soup),
                        title=title_text,
                        metadata=metadata,
                        encoding=encoding,
                        status_code=status_code,
                        headers=headers,
                    )

            except asyncio.TimeoutError:
                logger.error(f"Timeout while scraping {url}")
                raise
            except aiohttp.ClientError as e:
                logger.error(f"Client error while scraping {url}: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error while scraping {url}: {e}")
                raise

    async def scrape_site(self, start_url: str) -> AsyncGenerator[ScrapedPage, None]:
        """Scrape entire website starting from URL.

        Args:
            start_url: URL to start crawling from

        Yields:
            ScrapedPage objects as they are scraped
        """
        # Parse start URL to get base domain
        start_parsed = urlparse(start_url)
        base_domain = start_parsed.netloc

        # If no allowed domains specified, restrict to start domain
        if not self.config.allowed_domains:
            self.config.allowed_domains = [base_domain]
            logger.info(f"Restricting crawl to domain: {base_domain}")

        # URLs to visit
        to_visit: Set[str] = {start_url}
        depth_map: Dict[str, int] = {start_url: 0}

        async with self:
            while to_visit and len(self._visited_urls) < self.config.max_pages:
                # Get next URL
                url = to_visit.pop()

                # Skip if already visited
                if self.is_visited(url):
                    continue

                # Validate URL
                if not await self.validate_url(url):
                    continue

                # Check robots.txt
                if not await self.can_fetch(url):
                    logger.info(f"Skipping {url} - blocked by robots.txt")
                    continue

                # Check depth
                current_depth = depth_map.get(url, 0)
                if current_depth > self.config.max_depth:
                    logger.debug(
                        f"Skipping {url} - exceeds max depth {self.config.max_depth}"
                    )
                    continue

                # Mark as visited
                self.mark_visited(url)

                try:
                    # Scrape the page
                    page = await self.scrape_url(url)
                    yield page

                    # Extract links if not at max depth
                    if current_depth < self.config.max_depth:
                        new_urls = self._extract_links(page.content, url)
                        for new_url in new_urls:
                            if (
                                new_url not in self._visited_urls
                                and new_url not in to_visit
                            ):
                                to_visit.add(new_url)
                                depth_map[new_url] = current_depth + 1
                                logger.debug(
                                    f"Added URL to queue: {new_url} (depth: {current_depth + 1})"
                                )

                    # Respect rate limit
                    if self.config.request_delay > 0:
                        await asyncio.sleep(self.config.request_delay)

                except Exception as e:
                    logger.error(f"Error processing {url}: {e}")
                    # Continue with other URLs
                    continue

        logger.info(f"Crawl complete. Visited {len(self._visited_urls)} pages")

    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract metadata from HTML.

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            Dictionary of metadata key-value pairs
        """
        metadata = {}

        # Extract meta tags
        for meta in soup.find_all("meta"):
            # Try different meta tag formats
            name = meta.get("name") or meta.get("property") or meta.get("http-equiv")
            content = meta.get("content", "")

            if name is not None and content:
                # Ensure name is a string
                metadata[str(name)] = content

        # Extract other useful information
        # Canonical URL
        canonical = soup.find("link", {"rel": "canonical"})
        if canonical and canonical.get("href"):
            metadata["canonical"] = canonical["href"]

        # Author
        author = soup.find("meta", {"name": "author"})
        if author and author.get("content"):
            metadata["author"] = author["content"]

        return metadata

    def _extract_links(self, html_content: str, base_url: str) -> Set[str]:
        """Extract all links from HTML content.

        Args:
            html_content: HTML content to parse
            base_url: Base URL for resolving relative links

        Returns:
            Set of absolute URLs found in the content
        """
        links = set()

        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Find all links (only from anchor tags, not link tags which often point to CSS)
            for tag in soup.find_all("a"):
                href = tag.get("href")
                if href:
                    # Clean and resolve URL
                    href = href.strip()
                    if href and not href.startswith(
                        ("#", "javascript:", "mailto:", "tel:")
                    ):
                        absolute_url = urljoin(base_url, href)
                        # Remove fragment
                        absolute_url = absolute_url.split("#")[0]
                        if absolute_url:
                            # Skip non-HTML resources
                            if not any(
                                absolute_url.endswith(ext)
                                for ext in [
                                    ".css",
                                    ".js",
                                    ".json",
                                    ".xml",
                                    ".ico",
                                    ".jpg",
                                    ".jpeg",
                                    ".png",
                                    ".gif",
                                    ".svg",
                                    ".webp",
                                    ".pdf",
                                    ".zip",
                                ]
                            ):
                                links.add(unquote(absolute_url))

        except Exception as e:
            logger.error(f"Error extracting links from {base_url}: {e}")

        return links
