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
    allowed_paths: Optional[list[str]] = Field(
        default=None,
        description="List of paths/URLs to restrict crawling to (alternative to allowed_path)",
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
        default=5.0,
        ge=0,
        le=60,
        description="Delay between requests in seconds (default: 5s for rate limiting)",
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
    download_assets: bool = Field(
        default=False,
        description="Download linked assets like images, PDFs, and other files",
    )
    download_external_assets: bool = Field(
        default=True,
        description="Allow downloading assets from external domains (CDNs, etc.)",
    )
    asset_types: list[str] = Field(
        default_factory=lambda: [
            # Images (safe)
            ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico",
            # Stylesheets and fonts (safe)
            ".css", ".woff", ".woff2", ".ttf", ".eot",
            # Documents (potentially risky but commonly needed)
            ".pdf", ".txt", ".md", ".csv",
            # Data formats (safe)
            ".json", ".xml",
            # Note: .js removed by default for security
            # Note: Office files removed by default (.doc, .docx, .xls, .xlsx, .ppt, .pptx)
            # Note: Archives removed by default (.zip, .tar, .gz, .rar, .7z)
            # Note: Media files removed by default (.mp4, .webm, .mp3, .wav, .ogg)
        ],
        description="File extensions to download when download_assets is enabled (security-filtered defaults)",
    )
    max_asset_size: int = Field(
        default=50 * 1024 * 1024,  # 50MB
        ge=0,
        le=1024 * 1024 * 1024,  # 1GB max
        description="Maximum file size in bytes for asset downloads",
    )
    assets_subdirectory: str = Field(
        default="assets",
        description="Subdirectory name for storing downloaded assets",
    )
    max_assets_per_page: int = Field(
        default=-1,  # -1 means no limit
        ge=-1,
        description="Maximum number of assets to download per page (-1 for unlimited)",
    )
    total_assets_limit: int = Field(
        default=-1,  # -1 means no limit
        ge=-1,
        description="Maximum total number of assets to download in a session (-1 for unlimited)",
    )


class Config(BaseModel):
    """Main configuration for m1f-scrape."""

    crawler: CrawlerConfig = Field(
        default_factory=CrawlerConfig, description="Crawler configuration"
    )
    verbose: bool = Field(default=False, description="Enable verbose output")
    quiet: bool = Field(default=False, description="Suppress output except errors")
