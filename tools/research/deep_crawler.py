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
Deep crawling implementation for recursive page discovery
"""

import logging
import asyncio
from typing import List, Dict, Set, Optional, Tuple
from urllib.parse import urljoin, urlparse, urlunparse
from dataclasses import dataclass
import hashlib
import re

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

logger = logging.getLogger(__name__)


@dataclass
class CrawlResult:
    """Result of a crawl operation"""

    url: str
    depth: int
    parent_url: Optional[str]
    discovered_urls: List[str]
    error: Optional[str] = None


class DeepCrawler:
    """Handles recursive crawling with depth control"""

    def __init__(
        self,
        max_depth: int = 0,
        max_pages_per_site: int = 10,
        follow_external: bool = False,
        url_manager=None,
    ):
        """
        Initialize the deep crawler

        Args:
            max_depth: Maximum crawl depth (0 = no deep crawling)
            max_pages_per_site: Maximum pages to crawl per site
            follow_external: Whether to follow external links
            url_manager: URLManager instance for database operations
        """
        self.max_depth = max_depth
        self.max_pages_per_site = max_pages_per_site
        self.follow_external = follow_external
        self.url_manager = url_manager
        self.crawled_urls: Set[str] = set()
        self.discovered_urls: Dict[str, int] = {}  # url -> depth
        self.pages_per_site: Dict[str, int] = {}  # domain -> count

    async def crawl_with_depth(
        self,
        start_url: str,
        html_content: str,
        current_depth: int = 0,
        parent_url: Optional[str] = None,
    ) -> CrawlResult:
        """
        Crawl a page and discover linked pages up to max_depth

        Args:
            start_url: The URL being crawled
            html_content: HTML content of the page
            current_depth: Current crawl depth
            parent_url: Parent URL that linked to this page

        Returns:
            CrawlResult with discovered URLs
        """
        logger.info(f"Crawling {start_url} at depth {current_depth}")

        # Mark as crawled
        self.crawled_urls.add(self._normalize_url(start_url))

        # Track pages per site
        domain = urlparse(start_url).netloc
        self.pages_per_site[domain] = self.pages_per_site.get(domain, 0) + 1

        discovered = []

        # Only extract links if we haven't reached max depth
        if current_depth < self.max_depth:
            try:
                discovered = await self._extract_links(start_url, html_content)

                # Filter discovered URLs
                filtered_urls = []
                for url in discovered:
                    if self._should_crawl(url, start_url, current_depth + 1):
                        filtered_urls.append(url)
                        # Track discovered URL with its depth
                        norm_url = self._normalize_url(url)
                        if norm_url not in self.discovered_urls:
                            self.discovered_urls[norm_url] = current_depth + 1

                discovered = filtered_urls
                logger.info(f"Discovered {len(discovered)} new URLs to crawl")

            except Exception as e:
                logger.error(f"Error extracting links from {start_url}: {e}")
                return CrawlResult(
                    url=start_url,
                    depth=current_depth,
                    parent_url=parent_url,
                    discovered_urls=[],
                    error=str(e),
                )

        return CrawlResult(
            url=start_url,
            depth=current_depth,
            parent_url=parent_url,
            discovered_urls=discovered,
        )

    async def _extract_links(self, base_url: str, html_content: str) -> List[str]:
        """Extract all links from HTML content"""
        if not BeautifulSoup:
            logger.warning("BeautifulSoup not available, cannot extract links")
            return []

        try:
            soup = BeautifulSoup(html_content, "html.parser")
            links = []

            # Find all link elements
            for tag in soup.find_all(["a", "link"]):
                href = tag.get("href")
                if href:
                    # Make absolute URL
                    absolute_url = urljoin(base_url, href)

                    # Clean and validate URL
                    if self._is_valid_url(absolute_url):
                        links.append(absolute_url)

            # Deduplicate
            return list(set(links))

        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            return []

    def _should_crawl(self, url: str, parent_url: str, depth: int) -> bool:
        """Determine if a URL should be crawled"""
        # Check depth limit
        if depth > self.max_depth:
            return False

        # Check if already crawled
        norm_url = self._normalize_url(url)
        if norm_url in self.crawled_urls:
            return False

        # Check pages per site limit
        domain = urlparse(url).netloc
        if self.pages_per_site.get(domain, 0) >= self.max_pages_per_site:
            logger.debug(f"Reached max pages limit for {domain}")
            return False

        # Check external links policy
        if not self.follow_external:
            parent_domain = urlparse(parent_url).netloc
            url_domain = urlparse(url).netloc
            if parent_domain != url_domain:
                logger.debug(f"Skipping external URL: {url}")
                return False

        # Check URL patterns to exclude
        if self._should_exclude_url(url):
            return False

        return True

    def _should_exclude_url(self, url: str) -> bool:
        """Check if URL should be excluded from crawling"""
        # Common file extensions to exclude
        excluded_extensions = {
            ".pdf",
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".svg",
            ".webp",
            ".mp3",
            ".mp4",
            ".avi",
            ".mov",
            ".wmv",
            ".zip",
            ".tar",
            ".gz",
            ".rar",
            ".7z",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".ppt",
            ".pptx",
            ".exe",
            ".dmg",
            ".pkg",
            ".deb",
            ".rpm",
        }

        url_lower = url.lower()
        for ext in excluded_extensions:
            if url_lower.endswith(ext):
                return True

        # Exclude common non-content URLs
        excluded_patterns = [
            r"/login",
            r"/signin",
            r"/signup",
            r"/register",
            r"/logout",
            r"/signout",
            r"/download",
            r"/print",
            r"mailto:",
            r"tel:",
            r"javascript:",
            r"#$",  # Anchor-only links
        ]

        for pattern in excluded_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True

        return False

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid for crawling"""
        try:
            parsed = urlparse(url)

            # Must have scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                return False

            # Only HTTP(S)
            if parsed.scheme not in ["http", "https"]:
                return False

            return True

        except Exception:
            return False

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for deduplication"""
        try:
            parsed = urlparse(url.lower())

            # Remove fragments
            normalized = urlunparse(
                (
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path.rstrip("/"),
                    parsed.params,
                    parsed.query,
                    "",  # No fragment
                )
            )

            return normalized

        except Exception:
            return url.lower()

    async def process_crawl_queue(
        self, initial_urls: List[str], scraper_callback=None
    ) -> Dict[str, CrawlResult]:
        """
        Process a queue of URLs with depth-first crawling

        Args:
            initial_urls: List of starting URLs
            scraper_callback: Async function to scrape a URL

        Returns:
            Dictionary of URL -> CrawlResult
        """
        results = {}
        queue = [(url, 0, None) for url in initial_urls]  # (url, depth, parent)

        while (
            queue and len(self.crawled_urls) < self.max_pages_per_site * 10
        ):  # Safety limit
            url, depth, parent = queue.pop(0)

            # Skip if already crawled
            norm_url = self._normalize_url(url)
            if norm_url in self.crawled_urls:
                continue

            # Scrape the page if callback provided
            html_content = None
            if scraper_callback:
                try:
                    scrape_result = await scraper_callback(url)
                    if scrape_result and hasattr(scrape_result, "html"):
                        html_content = scrape_result.html
                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")
                    results[url] = CrawlResult(
                        url=url,
                        depth=depth,
                        parent_url=parent,
                        discovered_urls=[],
                        error=str(e),
                    )
                    continue

            # Crawl and discover new URLs
            if html_content:
                result = await self.crawl_with_depth(url, html_content, depth, parent)
                results[url] = result

                # Add discovered URLs to queue
                for discovered_url in result.discovered_urls:
                    if depth + 1 <= self.max_depth:
                        queue.append((discovered_url, depth + 1, url))

            # Small delay to avoid overwhelming servers
            await asyncio.sleep(0.5)

        logger.info(f"Deep crawl complete: {len(results)} pages crawled")
        return results

    def get_crawl_statistics(self) -> Dict[str, any]:
        """Get statistics about the crawl"""
        return {
            "total_crawled": len(self.crawled_urls),
            "total_discovered": len(self.discovered_urls),
            "pages_per_site": dict(self.pages_per_site),
            "max_depth_reached": (
                max(self.discovered_urls.values()) if self.discovered_urls else 0
            ),
        }

    def reset(self):
        """Reset crawler state"""
        self.crawled_urls.clear()
        self.discovered_urls.clear()
        self.pages_per_site.clear()
