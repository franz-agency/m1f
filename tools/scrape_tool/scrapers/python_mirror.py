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

"""Python-based web scraper implementation for complete website mirroring."""

import asyncio
import logging
from pathlib import Path
from typing import AsyncGenerator, Set, Dict, Optional
from urllib.parse import urlparse, urljoin, unquote
import os
import re

import aiohttp
import aiofiles
from bs4 import BeautifulSoup

from .base import WebScraperBase, ScrapedPage, ScraperConfig

logger = logging.getLogger(__name__)


class PythonMirrorScraper(WebScraperBase):
    """Python-based web scraper for complete website mirroring.

    This scraper downloads and saves web pages to disk, preserving the
    directory structure similar to HTTrack but using pure Python.
    """

    def __init__(self, config: ScraperConfig):
        """Initialize the Python mirror scraper.

        Args:
            config: Scraper configuration
        """
        super().__init__(config)
        self.session: Optional[aiohttp.ClientSession] = None
        self._semaphore = asyncio.Semaphore(config.concurrent_requests)
        self.output_dir: Optional[Path] = None

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
        if self.config.user_agent:
            headers["User-Agent"] = self.config.user_agent
        if self.config.custom_headers:
            headers.update(self.config.custom_headers)

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
            await asyncio.sleep(0.25)

    def _url_to_filepath(self, url: str, output_dir: Path) -> Path:
        """Convert URL to local file path.

        Args:
            url: URL to convert
            output_dir: Base output directory

        Returns:
            Local file path
        """
        parsed = urlparse(url)

        # Create domain directory
        domain_dir = output_dir / parsed.netloc

        # Handle path
        path = parsed.path.strip("/")
        if not path or path.endswith("/"):
            path = (path or "") + "index.html"
        elif "." not in os.path.basename(path):
            # No extension, assume HTML
            path = path + ".html"

        # Create full file path
        file_path = domain_dir / path

        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        return file_path

    async def _save_page(self, page: ScrapedPage, output_dir: Path) -> Path:
        """Save a scraped page to disk.

        Args:
            page: Scraped page to save
            output_dir: Output directory

        Returns:
            Path to saved file
        """
        file_path = self._url_to_filepath(page.url, output_dir)

        try:
            async with aiofiles.open(file_path, "w", encoding=page.encoding) as f:
                await f.write(page.content)
            logger.info(f"Saved {page.url} to {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error saving {page.url}: {e}")
            raise

    async def scrape_url(self, url: str) -> ScrapedPage:
        """Scrape a single URL.

        Args:
            url: URL to scrape

        Returns:
            ScrapedPage object containing the scraped content

        Raises:
            Exception: If scraping fails
        """
        if not self.session:
            raise RuntimeError("Scraper must be used as async context manager")

        async with self._semaphore:
            try:
                logger.info(f"Scraping URL: {url}")

                async with self.session.get(
                    url, allow_redirects=self.config.follow_redirects
                ) as response:
                    status_code = response.status
                    headers = dict(response.headers)

                    # Get content
                    content = await response.text()

                    # Parse with BeautifulSoup
                    soup = BeautifulSoup(content, "html.parser")

                    # Extract title
                    title = soup.find("title")
                    title_text = title.get_text(strip=True) if title else None

                    # Extract metadata
                    metadata = {}
                    for meta in soup.find_all("meta"):
                        name = meta.get("name") or meta.get("property")
                        content_value = meta.get("content", "")
                        if name and content_value:
                            metadata[str(name)] = content_value

                    return ScrapedPage(
                        url=str(response.url),
                        content=str(soup),
                        title=title_text,
                        metadata=metadata,
                        encoding=response.get_encoding() or "utf-8",
                        status_code=status_code,
                        headers=headers,
                    )

            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                raise

    async def scrape_site(self, start_url: str) -> AsyncGenerator[ScrapedPage, None]:
        """Scrape entire website starting from URL.

        Args:
            start_url: Starting URL for crawling

        Yields:
            ScrapedPage objects for each scraped page
        """

        # Parse start URL
        parsed_start = urlparse(start_url)
        base_domain = parsed_start.netloc

        # URLs to visit
        to_visit: Set[str] = {start_url}
        visited: Set[str] = set()
        depth_map: Dict[str, int] = {start_url: 0}

        # Ensure we're in context
        if not self.session:
            await self.__aenter__()

        pages_scraped = 0

        while to_visit and (
            self.config.max_pages == -1 or pages_scraped < self.config.max_pages
        ):
            url = to_visit.pop()

            # Skip if already visited
            normalized_url = self._normalize_url(url)
            if normalized_url in visited:
                continue

            visited.add(normalized_url)

            # Check depth
            current_depth = depth_map.get(url, 0)
            if self.config.max_depth != -1 and current_depth > self.config.max_depth:
                continue

            # Check if URL should be scraped
            if not await self.validate_url(url):
                continue

            # Check robots.txt
            if not await self.can_fetch(url):
                logger.info(f"Skipping {url} - blocked by robots.txt")
                continue

            try:
                # Scrape the page
                page = await self.scrape_url(url)

                # Save to disk if output_dir is set (optional for compatibility)
                if self.output_dir:
                    await self._save_page(page, self.output_dir)

                yield page
                pages_scraped += 1

                # Extract links if not at max depth
                if self.config.max_depth == -1 or current_depth < self.config.max_depth:
                    soup = BeautifulSoup(page.content, "html.parser")

                    for tag in soup.find_all("a", href=True):
                        href = tag["href"]
                        absolute_url = urljoin(url, href)

                        # Remove fragment
                        absolute_url = absolute_url.split("#")[0]

                        # Check if same domain
                        parsed_url = urlparse(absolute_url)
                        if parsed_url.netloc != base_domain:
                            continue

                        # Skip non-HTTP URLs
                        if parsed_url.scheme not in ("http", "https"):
                            continue

                        # Add to queue
                        normalized_new = self._normalize_url(absolute_url)
                        if normalized_new not in visited:
                            to_visit.add(absolute_url)
                            depth_map[absolute_url] = current_depth + 1

                # Respect rate limit
                if self.config.request_delay > 0:
                    await asyncio.sleep(self.config.request_delay)

            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                continue

        logger.info(f"Crawl complete. Scraped {pages_scraped} pages")

    def set_output_dir(self, output_dir: Path):
        """Set the output directory for saving scraped pages.

        Args:
            output_dir: Directory to save pages to
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
