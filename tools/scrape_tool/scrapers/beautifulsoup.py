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
from typing import Set, AsyncGenerator, Optional, Dict, List
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
        self._resume_info: List[Dict[str, str]] = []

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

                    # Store metadata for database
                    normalized_url = self._normalize_url(str(response.url))
                    canonical_url = None
                    content_checksum = None

                    # Order: 1. GET parameter normalization (already done in _normalize_url)
                    # 2. Canonical URL check
                    if self.config.check_canonical:
                        canonical_link = soup.find("link", {"rel": "canonical"})
                        if canonical_link and canonical_link.get("href"):
                            canonical_url = canonical_link["href"]
                            # Make canonical URL absolute
                            canonical_url = urljoin(url, canonical_url)
                            # Normalize canonical URL too
                            normalized_canonical = self._normalize_url(canonical_url)

                            if normalized_url != normalized_canonical:
                                logger.info(
                                    f"Skipping {url} - canonical URL differs: {canonical_url}"
                                )
                                return (
                                    None  # Return None to indicate skip, not an error
                                )

                    # 3. Content duplicate check
                    if self.config.check_content_duplicates:
                        from ..utils import calculate_content_checksum

                        content_checksum = calculate_content_checksum(content)

                        # Check if checksum exists using callback or fall back to database query
                        if self._checksum_callback and self._checksum_callback(
                            content_checksum
                        ):
                            logger.info(f"Skipping {url} - duplicate content detected")
                            return None  # Return None to indicate skip, not an error

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
                        normalized_url=normalized_url,
                        canonical_url=canonical_url,
                        content_checksum=content_checksum,
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

    def set_resume_info(self, resume_info: List[Dict[str, str]]) -> None:
        """Set resume information for continuing a crawl.

        Args:
            resume_info: List of dicts with 'url' and 'content' keys
        """
        self._resume_info = resume_info
        logger.info(
            f"Loaded {len(resume_info)} previously scraped pages for link extraction"
        )

    async def populate_queue_from_content(
        self,
        content: str,
        url: str,
        to_visit: Set[str],
        depth_map: Dict[str, int],
        current_depth: int,
    ) -> None:
        """Extract links from content and add to queue.

        Args:
            content: HTML content to extract links from
            url: URL of the page
            to_visit: Set of URLs to visit
            depth_map: Mapping of URLs to their depth
            current_depth: Current crawl depth
        """
        if current_depth < self.config.max_depth:
            new_urls = self._extract_links(content, url)
            for new_url in new_urls:
                normalized_new_url = self._normalize_url(new_url)
                if (
                    normalized_new_url not in self._visited_urls
                    and normalized_new_url not in to_visit
                ):
                    to_visit.add(normalized_new_url)
                    depth_map[normalized_new_url] = current_depth + 1
                    logger.debug(
                        f"Added URL to queue: {normalized_new_url} (depth: {current_depth + 1})"
                    )

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

        # Store the base path for subdirectory restriction
        # Use allowed_path if specified, otherwise use the start URL's path
        if self.config.allowed_path:
            base_path = self.config.allowed_path.rstrip("/")
            logger.info(f"Restricting crawl to allowed path: {base_path}")
        else:
            base_path = start_parsed.path.rstrip("/")
            if base_path:
                logger.info(f"Restricting crawl to subdirectory: {base_path}")

        # If no allowed domains specified, restrict to start domain
        if not self.config.allowed_domains:
            self.config.allowed_domains = [base_domain]
            logger.info(f"Restricting crawl to domain: {base_domain}")

        # URLs to visit
        to_visit: Set[str] = {start_url}
        depth_map: Dict[str, int] = {start_url: 0}

        # Check if we're already in a context manager
        should_close_session = False
        if not self.session:
            await self.__aenter__()
            should_close_session = True

        try:
            # If we have resume info, populate the queue from previously scraped pages
            if self._resume_info:
                logger.info("Populating queue from previously scraped pages...")
                for page_info in self._resume_info:
                    url = page_info["url"]
                    content = page_info["content"]
                    # Assume depth 0 for scraped pages, their links will be depth 1
                    await self.populate_queue_from_content(
                        content, url, to_visit, depth_map, 0
                    )
                logger.info(
                    f"Found {len(to_visit)} URLs to visit after analyzing scraped pages"
                )
            while to_visit and (
                self.config.max_pages == -1
                or len(self._visited_urls) < self.config.max_pages
            ):
                # Get next URL
                url = to_visit.pop()

                # Skip if already visited (normalize URL first)
                normalized_url = self._normalize_url(url)
                if self.is_visited(normalized_url):
                    continue

                # Validate URL
                if not await self.validate_url(url):
                    continue

                # Check subdirectory restriction (but always allow the start URL)
                if base_path and url != start_url:
                    url_parsed = urlparse(url)
                    if (
                        not url_parsed.path.startswith(base_path + "/")
                        and url_parsed.path != base_path
                    ):
                        logger.debug(
                            f"Skipping {url} - outside allowed path {base_path}"
                        )
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
                self.mark_visited(normalized_url)

                try:
                    # Scrape the page
                    page = await self.scrape_url(url)

                    # Skip if page is None (duplicate content or canonical mismatch)
                    if page is None:
                        continue

                    yield page

                    # Extract links if not at max depth
                    await self.populate_queue_from_content(
                        page.content, url, to_visit, depth_map, current_depth
                    )

                    # Respect rate limit
                    if self.config.request_delay > 0:
                        await asyncio.sleep(self.config.request_delay)

                except Exception as e:
                    logger.error(f"Error processing {url}: {e}")
                    # Continue with other URLs
                    continue

        finally:
            # Clean up session if we created it
            if should_close_session:
                await self.__aexit__(None, None, None)

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

                        # Remove GET parameters if configured to do so
                        if self.config.ignore_get_params and "?" in absolute_url:
                            absolute_url = absolute_url.split("?")[0]

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
