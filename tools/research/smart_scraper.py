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

"""
Enhanced smart scraper with per-host delay management for m1f-research
"""
import asyncio
import random
import aiohttp
import hashlib
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from collections import defaultdict
import logging
from urllib.parse import urlparse, urljoin
import re

from .models import ScrapedContent
from .config import ScrapingConfig
from .url_manager import URLManager
from .research_db import JobDatabase

logger = logging.getLogger(__name__)


class HostDelayManager:
    """Manages delays per host to be polite to servers"""

    def __init__(
        self, delay_range: Tuple[float, float] = (1.0, 3.0), threshold: int = 3
    ):
        self.delay_range = delay_range
        self.threshold = threshold
        self.host_request_count = defaultdict(int)
        self.last_request_time = {}

    async def wait_if_needed(self, url: str):
        """Wait if we're making too many requests to the same host"""
        host = urlparse(url).netloc
        self.host_request_count[host] += 1

        # Only delay if we've made more than threshold requests to this host
        if self.host_request_count[host] > self.threshold:
            delay = random.uniform(*self.delay_range)
            logger.debug(
                f"Delaying {delay:.1f}s for host {host} (request #{self.host_request_count[host]})"
            )
            await asyncio.sleep(delay)
        else:
            logger.debug(
                f"No delay for host {host} (request #{self.host_request_count[host]})"
            )

    def get_host_stats(self) -> Dict[str, int]:
        """Get request counts per host"""
        return dict(self.host_request_count)


class EnhancedSmartScraper:
    """
    Enhanced web scraper with:
    - Per-host delay management
    - Database integration
    - Content checksum tracking
    - Better error handling
    """

    def __init__(
        self, config: ScrapingConfig, job_db: JobDatabase, url_manager: URLManager
    ):
        self.config = config
        self.job_db = job_db
        self.url_manager = url_manager
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(config.max_concurrent)
        self.delay_manager = HostDelayManager(
            delay_range=(config.delay[0], config.delay[1]), threshold=3
        )

        # Progress tracking
        self.progress_callback = None
        self.total_urls = 0
        self.completed_urls = 0
        self.successful_urls = 0
        self.failed_urls = []

    async def __aenter__(self):
        """Async context manager entry"""
        headers = {"User-Agent": random.choice(self.config.user_agents)}
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def set_progress_callback(self, callback):
        """Set callback for progress updates"""
        self.progress_callback = callback

    async def scrape_urls(self, urls: List[str]) -> List[ScrapedContent]:
        """
        Scrape multiple URLs with smart host-based delays
        """
        self.total_urls = len(urls)
        self.completed_urls = 0
        self.successful_urls = 0
        self.failed_urls = []

        # Group URLs by host for smart scheduling
        urls_by_host = defaultdict(list)
        for url in urls:
            host = urlparse(url).netloc
            urls_by_host[host].append(url)

        logger.info(
            f"Scraping {len(urls)} URLs from {len(urls_by_host)} different hosts"
        )

        # Create tasks with mixed hosts for better parallelism
        tasks = []
        url_queue = []

        # Interleave URLs from different hosts
        max_urls = max(len(urls) for urls in urls_by_host.values())
        for i in range(max_urls):
            for host, host_urls in urls_by_host.items():
                if i < len(host_urls):
                    url_queue.append(host_urls[i])

        # Create scraping tasks
        for url in url_queue:
            task = self._scrape_with_semaphore(url)
            tasks.append(task)

        # Run all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        scraped_content = []
        for url, result in zip(url_queue, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to scrape {url}: {result}")
                self.failed_urls.append(url)
            elif result:
                scraped_content.append(result)
                self.successful_urls += 1

        # Log statistics
        logger.info(
            f"Scraping complete: {self.successful_urls}/{self.total_urls} successful"
        )
        if self.failed_urls:
            logger.warning(f"Failed to scrape {len(self.failed_urls)} URLs")

        host_stats = self.delay_manager.get_host_stats()
        logger.info(
            f"Requests per host: {dict(list(host_stats.items())[:5])}..."
        )  # Show first 5

        return scraped_content

    async def _scrape_with_semaphore(self, url: str) -> Optional[ScrapedContent]:
        """Scrape a single URL with semaphore control"""
        async with self.semaphore:
            return await self._scrape_url(url)

    async def _scrape_url(self, url: str) -> Optional[ScrapedContent]:
        """Scrape a single URL with retries and smart delays"""
        # Apply per-host delay if needed
        await self.delay_manager.wait_if_needed(url)

        # Check robots.txt if configured
        if not await self._check_robots_txt(url):
            logger.info(f"Skipping {url} due to robots.txt")
            self.url_manager.mark_url_scraped(
                url, -1, error_message="Blocked by robots.txt"
            )
            self._update_progress()
            return None

        # Try scraping with retries
        for attempt in range(self.config.retries):
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()

                        # Calculate content checksum
                        content_checksum = hashlib.sha256(content.encode()).hexdigest()

                        # Create scraped content object
                        scraped = ScrapedContent(
                            url=url,
                            title=self._extract_title(content),
                            content=content,
                            content_type=response.headers.get("Content-Type", ""),
                            scraped_at=datetime.now(),
                        )

                        # Mark as scraped in database
                        self.url_manager.mark_url_scraped(
                            url, response.status, content_checksum=content_checksum
                        )

                        self._update_progress()
                        return scraped

                    else:
                        error_msg = f"HTTP {response.status}"
                        if attempt < self.config.retries - 1:
                            logger.warning(f"{error_msg} for {url}, retrying...")
                            await asyncio.sleep(2**attempt)  # Exponential backoff
                        else:
                            logger.warning(f"{error_msg} for {url}")
                            self.url_manager.mark_url_scraped(
                                url, response.status, error_message=error_msg
                            )
                            self._update_progress()
                            return None

            except asyncio.TimeoutError:
                error_msg = "Timeout"
                if attempt < self.config.retries - 1:
                    logger.warning(f"Timeout for {url}, retrying...")
                    await asyncio.sleep(2**attempt)
                else:
                    logger.error(
                        f"Timeout for {url} after {self.config.retries} attempts"
                    )
                    self.url_manager.mark_url_scraped(url, -1, error_message=error_msg)
                    self._update_progress()
                    return None

            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error scraping {url}: {e}")
                if attempt < self.config.retries - 1:
                    await asyncio.sleep(2**attempt)
                else:
                    self.url_manager.mark_url_scraped(url, -1, error_message=error_msg)
                    self._update_progress()
                    return None

        return None

    async def _check_robots_txt(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt"""
        if not self.config.respect_robots_txt:
            return True

        try:
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

            # Simple check - just see if robots.txt mentions the path
            async with self.session.get(robots_url) as response:
                if response.status == 200:
                    content = await response.text()
                    path = parsed.path or "/"

                    # Very basic robots.txt parsing
                    lines = content.lower().split("\n")
                    user_agent_applies = False

                    for line in lines:
                        line = line.strip()
                        if line.startswith("user-agent:"):
                            user_agent_applies = "*" in line or "bot" in line
                        elif user_agent_applies and line.startswith("disallow:"):
                            disallowed = line.split(":", 1)[1].strip()
                            if disallowed and path.lower().startswith(disallowed):
                                return False

            return True

        except Exception as e:
            logger.debug(f"Could not check robots.txt for {url}: {e}")
            return True  # Allow if we can't check

    def _extract_title(self, html: str) -> str:
        """Extract title from HTML"""
        match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Try h1 as fallback
        match = re.search(r"<h1[^>]*>([^<]+)</h1>", html, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        return "Untitled"

    def _update_progress(self):
        """Update progress and call callback if set"""
        self.completed_urls += 1
        if self.progress_callback:
            progress = (self.completed_urls / self.total_urls) * 100
            self.progress_callback(self.completed_urls, self.total_urls, progress)

    def get_statistics(self) -> Dict[str, Any]:
        """Get scraping statistics"""
        return {
            "total_urls": self.total_urls,
            "completed_urls": self.completed_urls,
            "successful_urls": self.successful_urls,
            "failed_urls": len(self.failed_urls),
            "host_stats": self.delay_manager.get_host_stats(),
        }
