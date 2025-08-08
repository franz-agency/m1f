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

"""Configuration models for m1f-scrape."""

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ScraperBackend(str, Enum):
    """Available scraper backends."""

    HTTRACK = "httrack"
    BEAUTIFULSOUP = "beautifulsoup"
    BS4 = "bs4"  # Alias for beautifulsoup
    SELECTOLAX = "selectolax"
    HTTPX = "httpx"
    PLAYWRIGHT = "playwright"


class CrawlerConfig(BaseModel):
    """Configuration for web crawler."""

    max_depth: int = Field(
        default=5,
        ge=-1,
        le=1000,
        description="Maximum crawl depth (-1 for unlimited)",
    )
    max_pages: int = Field(
        default=10000,
        ge=-1,
        le=10000000,
        description="Maximum pages to crawl (-1 for unlimited)",
    )
    follow_external_links: bool = Field(
        default=False, description="Follow links to external domains"
    )
    allowed_domains: Optional[list[str]] = Field(
        default=None, description="List of allowed domains to crawl"
    )
    allowed_path: Optional[str] = Field(
        default=None,
        description="Restrict crawling to this path/URL and its subdirectories (e.g., /docs/ or https://example.com/docs/)",
    )
    excluded_paths: list[str] = Field(
        default_factory=list, description="URL paths to exclude from crawling"
    )
    scraper_backend: ScraperBackend = Field(
        default=ScraperBackend.BEAUTIFULSOUP, description="Web scraper backend to use"
    )
    scraper_config: Dict[str, Any] = Field(
        default_factory=dict, description="Backend-specific configuration"
    )
    request_delay: float = Field(
        default=15.0,
        ge=0,
        le=60,
        description="Delay between requests in seconds (default: 15s for Cloudflare)",
    )
    concurrent_requests: int = Field(
        default=2,
        ge=1,
        le=20,
        description="Number of concurrent requests (default: 2 for Cloudflare)",
    )
    user_agent: Optional[str] = Field(
        default=None, description="Custom user agent string"
    )
    respect_robots_txt: bool = Field(
        default=True, description="Respect robots.txt rules"
    )
    timeout: int = Field(
        default=30, ge=1, le=300, description="Request timeout in seconds"
    )
    retry_count: int = Field(
        default=3, ge=0, le=10, description="Number of retries for failed requests"
    )
    ignore_get_params: bool = Field(
        default=False,
        description="Ignore GET parameters in URLs to avoid duplicate content",
    )
    check_canonical: bool = Field(
        default=True, description="Skip pages if canonical URL differs from current URL"
    )
    check_content_duplicates: bool = Field(
        default=True,
        description="Skip pages with duplicate content (based on text-only checksum)",
    )
    check_ssrf: bool = Field(
        default=True,
        description="Check for SSRF vulnerabilities by blocking private IP addresses",
    )
    force_rescrape: bool = Field(
        default=False,
        description="Force re-scraping of all URLs, ignoring database cache",
    )


class Config(BaseModel):
    """Main configuration for m1f-scrape."""

    crawler: CrawlerConfig = Field(
        default_factory=CrawlerConfig, description="Crawler configuration"
    )
    verbose: bool = Field(default=False, description="Enable verbose output")
    quiet: bool = Field(default=False, description="Suppress output except errors")
