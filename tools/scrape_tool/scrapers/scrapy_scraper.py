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

"""Scrapy backend for industrial-strength web scraping."""

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import AsyncIterator, Optional, Dict, Any, List
from urllib.parse import urlparse
import json

try:
    import scrapy
    from scrapy.crawler import CrawlerProcess, CrawlerRunner
    from scrapy.utils.project import get_project_settings
    from twisted.internet import reactor, defer
    from scrapy.utils.log import configure_logging

    SCRAPY_AVAILABLE = True
except ImportError:
    SCRAPY_AVAILABLE = False

from .base import WebScraperBase, ScrapedPage, ScraperConfig

logger = logging.getLogger(__name__)


class ScrapySpider(scrapy.Spider if SCRAPY_AVAILABLE else object):
    """Custom Scrapy spider for HTML2MD."""

    name = "html2md_spider"

    def __init__(
        self, start_url: str, config: ScraperConfig, output_file: str, *args, **kwargs
    ):
        """Initialize spider with configuration."""
        # Initialize parent class first if Scrapy is available
        if SCRAPY_AVAILABLE and scrapy.Spider in self.__class__.__mro__:
            super().__init__(*args, **kwargs)

        self.start_urls = [start_url]
        self.config = config
        self.output_file = output_file
        self.pages_scraped = 0

        # Parse domain for allowed domains
        parsed = urlparse(start_url)
        if config.allowed_domains:
            self.allowed_domains = list(config.allowed_domains)
        else:
            self.allowed_domains = [parsed.netloc]

    def parse(self, response):
        """Parse a response and extract data."""
        # Check page limit
        if self.pages_scraped >= self.config.max_pages:
            return

        self.pages_scraped += 1

        # Extract page data
        # Convert headers to string dict (headers might contain bytes)
        headers = {}
        for key, value in response.headers.items():
            key_str = key.decode("utf-8") if isinstance(key, bytes) else str(key)
            value_str = (
                value[0].decode("utf-8")
                if isinstance(value[0], bytes)
                else str(value[0])
            )
            headers[key_str] = value_str

        page_data = {
            "url": response.url,
            "content": response.text,
            "title": response.css("title::text").get(""),
            "encoding": response.encoding,
            "status_code": response.status,
            "headers": headers,
            "metadata": self._extract_metadata(response),
        }

        # Save to output file
        with open(self.output_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(page_data) + "\n")

        # Follow links if not at max depth
        depth = response.meta.get("depth", 0)
        if depth < self.config.max_depth and self.pages_scraped < self.config.max_pages:
            # Extract all links
            for href in response.css("a::attr(href)").getall():
                # Skip non-HTTP links
                if href.startswith(("mailto:", "tel:", "javascript:", "#")):
                    continue

                # Skip if matches exclude pattern
                if self.config.exclude_patterns:
                    if any(pattern in href for pattern in self.config.exclude_patterns):
                        continue

                yield response.follow(href, callback=self.parse)

    def _extract_metadata(self, response) -> Dict[str, Any]:
        """Extract metadata from the response."""
        metadata = {}

        # Meta description
        desc = response.css('meta[name="description"]::attr(content)').get()
        if desc:
            metadata["description"] = desc

        # Meta keywords
        keywords = response.css('meta[name="keywords"]::attr(content)').get()
        if keywords:
            metadata["keywords"] = keywords

        # Open Graph tags
        for og_tag in response.css('meta[property^="og:"]'):
            prop = og_tag.css("::attr(property)").get()
            content = og_tag.css("::attr(content)").get()
            if prop and content:
                metadata[prop] = content

        return metadata


class ScrapyScraper(WebScraperBase):
    """Industrial-strength scraper using Scrapy framework.

    Scrapy provides:
    - Built-in request throttling and retry logic
    - Concurrent request handling with Twisted
    - Middleware system for customization
    - robots.txt compliance
    - Auto-throttle based on server response times

    Best for:
    - Large-scale web scraping projects
    - Sites requiring complex crawling logic
    - Projects needing middleware (proxies, auth, etc.)
    """

    def __init__(self, config: ScraperConfig):
        """Initialize the Scrapy scraper.

        Args:
            config: Scraper configuration

        Raises:
            ImportError: If scrapy is not installed
        """
        if not SCRAPY_AVAILABLE:
            raise ImportError(
                "scrapy is required for this scraper. "
                "Install with: pip install scrapy"
            )

        super().__init__(config)
        self._temp_dir: Optional[Path] = None
        self._output_file: Optional[Path] = None

    async def __aenter__(self):
        """Enter async context."""
        # Create temporary directory for output
        self._temp_dir = Path(tempfile.mkdtemp(prefix="scrapy_html2md_"))
        self._output_file = self._temp_dir / "output.jsonl"
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context and cleanup."""
        # Cleanup temporary files
        if self._temp_dir and self._temp_dir.exists():
            import shutil

            shutil.rmtree(self._temp_dir)

    async def scrape_url(self, url: str) -> ScrapedPage:
        """Scrape a single URL using Scrapy.

        Args:
            url: URL to scrape

        Returns:
            ScrapedPage object with scraped content
        """
        # Use a simpler approach for single URLs - just use aiohttp
        # since Scrapy is more suited for site-wide crawling
        import aiohttp
        import aiofiles

        async with aiohttp.ClientSession() as session:
            headers = {"User-Agent": self.config.user_agent}
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)

            async with session.get(
                url,
                headers=headers,
                timeout=timeout,
                allow_redirects=self.config.follow_redirects,
            ) as response:
                content = await response.text()

                # Parse with BeautifulSoup to extract title
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(content, "html.parser")
                title = soup.title.string if soup.title else ""

                # Extract metadata
                metadata = {}
                desc_tag = soup.find("meta", attrs={"name": "description"})
                if desc_tag and desc_tag.get("content"):
                    metadata["description"] = desc_tag["content"]

                keywords_tag = soup.find("meta", attrs={"name": "keywords"})
                if keywords_tag and keywords_tag.get("content"):
                    metadata["keywords"] = keywords_tag["content"]

                # Extract OG tags
                for og_tag in soup.find_all(
                    "meta", attrs={"property": lambda x: x and x.startswith("og:")}
                ):
                    if og_tag.get("content"):
                        metadata[og_tag["property"]] = og_tag["content"]

                return ScrapedPage(
                    url=str(response.url),
                    content=content,
                    title=title,
                    encoding=response.charset or "utf-8",
                    status_code=response.status,
                    headers=dict(response.headers),
                    metadata=metadata,
                )

    async def scrape_site(self, start_url: str) -> AsyncIterator[ScrapedPage]:
        """Scrape an entire website using Scrapy.

        Args:
            start_url: Starting URL for crawling

        Yields:
            ScrapedPage objects for each scraped page
        """
        # Clear output file
        if self._output_file.exists():
            self._output_file.unlink()

        # Configure Scrapy settings
        settings = get_project_settings()
        settings.update(
            {
                "USER_AGENT": self.config.user_agent,
                "ROBOTSTXT_OBEY": self.config.respect_robots_txt,
                "CONCURRENT_REQUESTS": self.config.concurrent_requests,
                "DOWNLOAD_DELAY": self.config.request_delay,
                "RANDOMIZE_DOWNLOAD_DELAY": True,  # Randomize delays
                "DEPTH_LIMIT": self.config.max_depth,
                "LOG_ENABLED": logger.isEnabledFor(logging.DEBUG),
                "TELNETCONSOLE_ENABLED": False,
                "AUTOTHROTTLE_ENABLED": True,  # Enable auto-throttle
                "AUTOTHROTTLE_START_DELAY": self.config.request_delay,
                "AUTOTHROTTLE_MAX_DELAY": self.config.request_delay * 10,
                "AUTOTHROTTLE_TARGET_CONCURRENCY": self.config.concurrent_requests,
                "HTTPCACHE_ENABLED": True,  # Enable cache
                "HTTPCACHE_DIR": str(self._temp_dir / "cache"),
                "REDIRECT_ENABLED": self.config.follow_redirects,
                "DOWNLOAD_TIMEOUT": self.config.timeout,
            }
        )

        # Use multiprocessing to run Scrapy in a separate process
        # to avoid reactor threading issues
        import multiprocessing
        import time

        def run_spider_process():
            """Run spider in separate process."""
            from scrapy.crawler import CrawlerProcess
            from scrapy.utils.project import get_project_settings

            # Re-create settings in the new process
            settings = get_project_settings()
            settings.update(
                {
                    "USER_AGENT": self.config.user_agent,
                    "ROBOTSTXT_OBEY": self.config.respect_robots_txt,
                    "CONCURRENT_REQUESTS": self.config.concurrent_requests,
                    "DOWNLOAD_DELAY": self.config.request_delay,
                    "RANDOMIZE_DOWNLOAD_DELAY": True,
                    "DEPTH_LIMIT": self.config.max_depth,
                    "LOG_ENABLED": logger.isEnabledFor(logging.DEBUG),
                    "TELNETCONSOLE_ENABLED": False,
                    "AUTOTHROTTLE_ENABLED": True,
                    "AUTOTHROTTLE_START_DELAY": self.config.request_delay,
                    "AUTOTHROTTLE_MAX_DELAY": self.config.request_delay * 10,
                    "AUTOTHROTTLE_TARGET_CONCURRENCY": self.config.concurrent_requests,
                    "HTTPCACHE_ENABLED": True,
                    "HTTPCACHE_DIR": str(self._temp_dir / "cache"),
                    "REDIRECT_ENABLED": self.config.follow_redirects,
                    "DOWNLOAD_TIMEOUT": self.config.timeout,
                }
            )

            process = CrawlerProcess(settings)
            process.crawl(
                ScrapySpider,
                start_url=start_url,
                config=self.config,
                output_file=str(self._output_file),
            )
            process.start()

        # Start spider in separate process
        process = multiprocessing.Process(target=run_spider_process)
        process.start()

        # Monitor output file and yield results as they come in
        last_position = 0
        pages_yielded = 0

        while True:
            # Check if spider process is still running
            if not process.is_alive():
                # Read any remaining data
                if self._output_file.exists():
                    with open(self._output_file, "r", encoding="utf-8") as f:
                        f.seek(last_position)
                        for line in f:
                            if line.strip():
                                data = json.loads(line.strip())
                                yield ScrapedPage(**data)
                                pages_yielded += 1
                break

            # Read new data from output file
            if self._output_file.exists():
                with open(self._output_file, "r", encoding="utf-8") as f:
                    f.seek(last_position)
                    for line in f:
                        if line.strip():
                            data = json.loads(line.strip())
                            yield ScrapedPage(**data)
                            pages_yielded += 1

                            # Check page limit
                            if pages_yielded >= self.config.max_pages:
                                # Terminate the process
                                process.terminate()
                                process.join(timeout=5)
                                if process.is_alive():
                                    process.kill()
                                return

                    last_position = f.tell()

            # Small delay to avoid busy waiting
            await asyncio.sleep(0.1)

        logger.info(f"Scrapy scraping complete. Scraped {pages_yielded} pages")
