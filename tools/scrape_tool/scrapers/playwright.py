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

"""Playwright scraper backend for JavaScript-heavy websites."""

import asyncio
import logging
from typing import AsyncIterator, Set, Optional, Dict, Any, TYPE_CHECKING
from urllib.parse import urljoin, urlparse
import re

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    if TYPE_CHECKING:
        from playwright.async_api import Page
    else:
        Page = Any

from .base import WebScraperBase, ScrapedPage, ScraperConfig

logger = logging.getLogger(__name__)


class PlaywrightScraper(WebScraperBase):
    """Browser-based scraper using Playwright for JavaScript rendering.

    Playwright provides:
    - Full JavaScript execution and rendering
    - Support for SPAs and dynamic content
    - Multiple browser engines (Chromium, Firefox, WebKit)
    - Screenshot and PDF generation capabilities
    - Network interception and modification
    - Mobile device emulation

    Best for:
    - JavaScript-heavy websites and SPAs
    - Sites requiring user interaction (clicking, scrolling)
    - Content behind authentication
    - Visual regression testing
    """

    def __init__(self, config: ScraperConfig):
        """Initialize the Playwright scraper.

        Args:
            config: Scraper configuration

        Raises:
            ImportError: If playwright is not installed
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "playwright is required for this scraper. "
                "Install with: pip install playwright && playwright install"
            )

        super().__init__(config)
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._visited_urls: Set[str] = set()

        # Browser configuration from scraper config
        self._browser_config = config.__dict__.get("browser_config", {})
        self._browser_type = self._browser_config.get("browser", "chromium")
        self._headless = self._browser_config.get("headless", True)
        self._viewport = self._browser_config.get(
            "viewport", {"width": 1920, "height": 1080}
        )
        self._wait_until = self._browser_config.get("wait_until", "networkidle")
        self._wait_timeout = self._browser_config.get("wait_timeout", 30000)

    async def __aenter__(self):
        """Enter async context and launch browser."""
        self._playwright = await async_playwright().start()

        # Launch browser based on type
        if self._browser_type == "firefox":
            self._browser = await self._playwright.firefox.launch(
                headless=self._headless
            )
        elif self._browser_type == "webkit":
            self._browser = await self._playwright.webkit.launch(
                headless=self._headless
            )
        else:  # Default to chromium
            self._browser = await self._playwright.chromium.launch(
                headless=self._headless
            )

        # Create browser context with custom user agent
        self._context = await self._browser.new_context(
            user_agent=self.config.user_agent,
            viewport=self._viewport,
            ignore_https_errors=True,  # Handle self-signed certificates
            accept_downloads=False,
        )

        # Set default timeout
        self._context.set_default_timeout(self._wait_timeout)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context and cleanup."""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def scrape_url(self, url: str) -> ScrapedPage:
        """Scrape a single URL using Playwright.

        Args:
            url: URL to scrape

        Returns:
            ScrapedPage object with scraped content

        Raises:
            Exception: If scraping fails
        """
        if not self._context:
            raise RuntimeError("Scraper not initialized. Use async context manager.")

        page = None
        try:
            # Create new page
            page = await self._context.new_page()

            # Navigate to URL
            response = await page.goto(url, wait_until=self._wait_until)

            if not response:
                raise Exception(f"Failed to navigate to {url}")

            # Wait for any additional dynamic content
            if self._browser_config.get("wait_for_selector"):
                await page.wait_for_selector(
                    self._browser_config["wait_for_selector"],
                    timeout=self._wait_timeout,
                )

            # Execute any custom JavaScript
            if self._browser_config.get("execute_script"):
                await page.evaluate(self._browser_config["execute_script"])

            # Get the final rendered HTML
            content = await page.content()

            # Extract title
            title = await page.title()

            # Extract metadata
            metadata = await self._extract_metadata(page)

            # Get response headers and status
            status_code = response.status
            headers = response.headers

            # Detect encoding
            encoding = "utf-8"  # Default for rendered content

            # Take screenshot if configured
            if self._browser_config.get("screenshot"):
                screenshot_path = self._browser_config.get(
                    "screenshot_path", "screenshot.png"
                )
                await page.screenshot(path=screenshot_path, full_page=True)
                metadata["screenshot"] = screenshot_path

            return ScrapedPage(
                url=page.url,  # Use final URL after redirects
                content=content,
                title=title,
                encoding=encoding,
                status_code=status_code,
                headers=headers,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"Error scraping {url} with Playwright: {e}")
            raise
        finally:
            if page:
                await page.close()

    async def _extract_metadata(self, page: Page) -> Dict[str, Any]:
        """Extract metadata from the page."""
        metadata = {}

        # Extract meta tags
        meta_tags = await page.evaluate(
            """
            () => {
                const metadata = {};
                
                // Get description
                const desc = document.querySelector('meta[name="description"]');
                if (desc) metadata.description = desc.content;
                
                // Get keywords
                const keywords = document.querySelector('meta[name="keywords"]');
                if (keywords) metadata.keywords = keywords.content;
                
                // Get Open Graph tags
                document.querySelectorAll('meta[property^="og:"]').forEach(tag => {
                    const prop = tag.getAttribute('property');
                    if (prop && tag.content) {
                        metadata[prop] = tag.content;
                    }
                });
                
                // Get Twitter Card tags
                document.querySelectorAll('meta[name^="twitter:"]').forEach(tag => {
                    const name = tag.getAttribute('name');
                    if (name && tag.content) {
                        metadata[name] = tag.content;
                    }
                });
                
                // Get canonical URL
                const canonical = document.querySelector('link[rel="canonical"]');
                if (canonical) metadata.canonical = canonical.href;
                
                // Get page load time
                if (window.performance && window.performance.timing) {
                    const timing = window.performance.timing;
                    metadata.load_time = timing.loadEventEnd - timing.navigationStart;
                }
                
                return metadata;
            }
        """
        )

        metadata.update(meta_tags)

        # Add browser info
        metadata["browser"] = self._browser_type
        metadata["viewport"] = self._viewport

        return metadata

    async def scrape_site(self, start_url: str) -> AsyncIterator[ScrapedPage]:
        """Scrape an entire website using Playwright.

        Args:
            start_url: Starting URL for crawling

        Yields:
            ScrapedPage objects for each scraped page
        """
        if not self._context:
            raise RuntimeError("Scraper not initialized. Use async context manager.")

        # Parse start URL to get base domain
        parsed_start = urlparse(start_url)
        base_domain = parsed_start.netloc

        # Initialize queue
        queue = asyncio.Queue()
        await queue.put((start_url, 0))  # (url, depth)

        # Track visited URLs
        self._visited_urls.clear()
        self._visited_urls.add(start_url)

        # Semaphore for concurrent pages
        semaphore = asyncio.Semaphore(self.config.concurrent_requests)

        # Active tasks
        tasks = set()
        pages_scraped = 0

        async def process_url(url: str, depth: int):
            """Process a single URL and extract links."""
            async with semaphore:
                page = None
                try:
                    # Respect request delay
                    if self.config.request_delay > 0:
                        await asyncio.sleep(self.config.request_delay)

                    # Create new page
                    page = await self._context.new_page()

                    # Navigate to URL
                    response = await page.goto(url, wait_until=self._wait_until)

                    if not response:
                        logger.warning(f"Failed to navigate to {url}")
                        return None

                    # Wait for dynamic content
                    if self._browser_config.get("wait_for_selector"):
                        await page.wait_for_selector(
                            self._browser_config["wait_for_selector"],
                            timeout=self._wait_timeout,
                        )

                    # Get content
                    content = await page.content()
                    title = await page.title()
                    metadata = await self._extract_metadata(page)

                    # Create scraped page
                    scraped_page = ScrapedPage(
                        url=page.url,
                        content=content,
                        title=title,
                        encoding="utf-8",
                        status_code=response.status,
                        headers=response.headers,
                        metadata=metadata,
                    )

                    # Extract links if not at max depth
                    if depth < self.config.max_depth:
                        # Get all links using JavaScript
                        links = await page.evaluate(
                            """
                            () => {
                                return Array.from(document.querySelectorAll('a[href]'))
                                    .map(a => a.href)
                                    .filter(href => href && (href.startsWith('http://') || href.startsWith('https://')));
                            }
                        """
                        )

                        for link in links:
                            # Parse URL
                            parsed_url = urlparse(link)

                            # Skip if different domain (unless allowed)
                            if self.config.allowed_domains:
                                if parsed_url.netloc not in self.config.allowed_domains:
                                    continue
                            elif parsed_url.netloc != base_domain:
                                continue

                            # Skip if matches exclude pattern
                            if self.config.exclude_patterns:
                                if any(
                                    re.match(pattern, link)
                                    for pattern in self.config.exclude_patterns
                                ):
                                    continue

                            # Skip if already visited
                            if link in self._visited_urls:
                                continue

                            # Add to queue
                            self._visited_urls.add(link)
                            await queue.put((link, depth + 1))

                    return scraped_page

                except Exception as e:
                    logger.error(f"Error processing {url}: {e}")
                    return None
                finally:
                    if page:
                        await page.close()

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

        logger.info(f"Playwright scraping complete. Scraped {pages_scraped} pages")
