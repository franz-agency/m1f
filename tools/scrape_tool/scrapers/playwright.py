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
        # Add option to control SSL validation (default to secure)
        ignore_https_errors = getattr(self.config, "ignore_https_errors", False)

        self._context = await self._browser.new_context(
            user_agent=self.config.user_agent,
            viewport=self._viewport,
            ignore_https_errors=ignore_https_errors,  # Only ignore if explicitly configured
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
            # Check robots.txt before scraping
            if not await self.can_fetch(url):
                raise ValueError(f"URL {url} is blocked by robots.txt")

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

            # Execute any custom JavaScript (with security warning)
            if self._browser_config.get("execute_script"):
                script = self._browser_config["execute_script"]

                # Basic validation to prevent obvious malicious scripts
                dangerous_patterns = [
                    "fetch",
                    "XMLHttpRequest",
                    "eval",
                    "Function",
                    "localStorage",
                    "sessionStorage",
                    "document.cookie",
                    "window.location",
                    "navigator",
                    "WebSocket",
                ]

                script_lower = script.lower()
                for pattern in dangerous_patterns:
                    if pattern.lower() in script_lower:
                        logger.warning(
                            f"Potentially dangerous JavaScript pattern '{pattern}' detected in script. Skipping execution."
                        )
                        break
                else:
                    # Only execute if no dangerous patterns found
                    logger.warning(
                        "Executing custom JavaScript. This feature should only be used with trusted scripts."
                    )
                    try:
                        await page.evaluate(script)
                    except Exception as e:
                        logger.error(f"Error executing custom JavaScript: {e}")

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

        # Store the base path for subdirectory restriction
        # Handle allowed paths (single or multiple)
        allowed_domain = None
        allowed_path_configs = []  # List of (domain, path) tuples
        
        # Get list of allowed paths (new multiple paths or fallback to single path)
        allowed_paths_list = []
        if hasattr(self.config, 'allowed_paths') and self.config.allowed_paths:
            allowed_paths_list = self.config.allowed_paths
        elif self.config.allowed_path:
            allowed_paths_list = [self.config.allowed_path]
        
        if allowed_paths_list:
            for allowed_path in allowed_paths_list:
                # Check if allowed_path is a full URL or just a path
                if allowed_path.startswith(("http://", "https://")):
                    # It's a full URL - extract domain and path
                    parsed_allowed = urlparse(allowed_path)
                    path_config = (parsed_allowed.netloc, parsed_allowed.path.rstrip("/"))
                    allowed_path_configs.append(path_config)
                    logger.info(f"Restricting crawl to URL: {parsed_allowed.netloc}{parsed_allowed.path.rstrip('/')}")
                    # For backward compatibility, set allowed_domain from first URL if not set
                    if allowed_domain is None:
                        allowed_domain = parsed_allowed.netloc
                else:
                    # It's just a path
                    path_config = (None, allowed_path.rstrip("/"))
                    allowed_path_configs.append(path_config)
                    logger.info(f"Restricting crawl to allowed path: {allowed_path.rstrip('/')}")
        else:
            # Use the start URL's path if no allowed paths specified
            base_path = parsed_start.path.rstrip("/")
            if base_path:
                allowed_path_configs.append((None, base_path))
                logger.info(f"Restricting crawl to subdirectory: {base_path}")

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

                    # Check robots.txt before scraping
                    if not await self.can_fetch(url):
                        logger.info(f"Skipping {url} - blocked by robots.txt")
                        return None

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

                    # Check canonical URL if enabled
                    if self.config.check_canonical and metadata.get("canonical"):
                        canonical_url = metadata["canonical"]
                        normalized_current = self._normalize_url(page.url)
                        normalized_canonical = self._normalize_url(canonical_url)

                        if normalized_current != normalized_canonical:
                            # Check if we should respect the canonical URL
                            should_skip = True

                            # Check allowed paths (single or multiple)
                            allowed_paths_list = []
                            if hasattr(self.config, 'allowed_paths') and self.config.allowed_paths:
                                allowed_paths_list = self.config.allowed_paths
                            elif self.config.allowed_path:
                                allowed_paths_list = [self.config.allowed_path]
                            
                            if allowed_paths_list:
                                # Parse URLs to check paths
                                current_parsed = urlparse(normalized_current)
                                canonical_parsed = urlparse(normalized_canonical)

                                # If current URL is within any allowed_path but canonical is outside all,
                                # don't skip - the user explicitly wants content from allowed_path
                                current_in_allowed = any(
                                    current_parsed.path.startswith(allowed_path)
                                    for allowed_path in allowed_paths_list
                                )
                                canonical_in_allowed = any(
                                    canonical_parsed.path.startswith(allowed_path)
                                    for allowed_path in allowed_paths_list
                                )
                                
                                if current_in_allowed and not canonical_in_allowed:
                                    should_skip = False
                                    logger.info(
                                        f"Not skipping {url} - canonical URL {canonical_url} is outside allowed_paths {allowed_paths_list}"
                                    )

                            if should_skip:
                                logger.info(
                                    f"Skipping {url} - canonical URL differs: {canonical_url}"
                                )
                                visited.add(url)
                                return None  # Skip this page

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
                    if self.config.max_depth == -1 or depth < self.config.max_depth:
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

                            # Check subdirectory restriction (but always allow the start URL)
                            if allowed_path_configs and link != start_url:
                                # Check if URL matches any of the allowed path configurations
                                path_allowed = False
                                for allowed_domain_config, allowed_path_config in allowed_path_configs:
                                    # If a domain is specified in the config, check it matches
                                    if allowed_domain_config and parsed_url.netloc != allowed_domain_config:
                                        continue  # Try next config
                                    
                                    # Check if the path is allowed
                                    if (parsed_url.path.startswith(allowed_path_config + "/") or 
                                        parsed_url.path == allowed_path_config):
                                        path_allowed = True
                                        break  # Found a matching config
                                
                                if not path_allowed:
                                    logger.debug(
                                        f"Skipping {link} - outside allowed paths {allowed_path_configs}"
                                    )
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

                    # Check max pages limit (skip if -1 for unlimited)
                    if (
                        self.config.max_pages != -1
                        and pages_scraped >= self.config.max_pages
                    ):
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

                        # Check if we've hit the page limit (skip if -1 for unlimited)
                        if (
                            self.config.max_pages != -1
                            and pages_scraped >= self.config.max_pages
                        ):
                            # Cancel remaining tasks
                            for t in tasks:
                                t.cancel()
                            return

        logger.info(f"Playwright scraping complete. Scraped {pages_scraped} pages")
