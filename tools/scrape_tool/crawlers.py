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

"""Web crawling functionality using configurable scraper backends."""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

from .scrapers import create_scraper, ScraperConfig, ScrapedPage
from .config import CrawlerConfig, ScraperBackend

logger = logging.getLogger(__name__)


class WebCrawler:
    """Web crawler that uses configurable scraper backends."""

    def __init__(self, config: CrawlerConfig):
        """Initialize crawler with configuration.

        Args:
            config: CrawlerConfig instance with crawling settings
        """
        self.config = config
        self._scraper_config = self._create_scraper_config()

    def _create_scraper_config(self) -> ScraperConfig:
        """Create scraper configuration from crawler config.

        Returns:
            ScraperConfig instance
        """
        # Convert allowed_domains from set to list
        allowed_domains = (
            list(self.config.allowed_domains) if self.config.allowed_domains else []
        )

        # Convert excluded_paths to exclude_patterns
        exclude_patterns = (
            list(self.config.excluded_paths) if self.config.excluded_paths else []
        )

        # Create scraper config
        scraper_kwargs = {
            "max_depth": self.config.max_depth,
            "max_pages": self.config.max_pages,
            "allowed_domains": allowed_domains,
            "exclude_patterns": exclude_patterns,
            "respect_robots_txt": self.config.respect_robots_txt,
            "concurrent_requests": self.config.concurrent_requests,
            "request_delay": self.config.request_delay,
            "timeout": float(self.config.timeout),
            "follow_redirects": True,  # Always follow redirects
        }

        # Only add user_agent if it's not None
        if self.config.user_agent is not None:
            scraper_kwargs["user_agent"] = self.config.user_agent

        scraper_config = ScraperConfig(**scraper_kwargs)

        # Apply any backend-specific configuration
        if self.config.scraper_config:
            for key, value in self.config.scraper_config.items():
                if hasattr(scraper_config, key):
                    # Special handling for custom_headers to ensure it's a dict
                    if key == "custom_headers":
                        if value is None:
                            value = {}
                        elif not isinstance(value, dict):
                            logger.warning(
                                f"Invalid custom_headers type: {type(value)}, using empty dict"
                            )
                            value = {}
                    setattr(scraper_config, key, value)

        return scraper_config

    async def crawl(self, start_url: str, output_dir: Path) -> Dict[str, Any]:
        """Crawl a website using the configured scraper backend.

        Args:
            start_url: Starting URL for crawling
            output_dir: Directory to store downloaded files

        Returns:
            Dictionary with crawl results including:
            - pages: List of scraped pages
            - total_pages: Total number of pages scraped
            - errors: List of any errors encountered

        Raises:
            Exception: If crawling fails
        """
        logger.info(
            f"Starting crawl of {start_url} using {self.config.scraper_backend} backend"
        )

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Parse URL to get domain for output structure
        parsed_url = urlparse(start_url)
        domain = parsed_url.netloc
        site_dir = output_dir / domain
        site_dir.mkdir(exist_ok=True)

        # Create scraper instance
        backend_name = self.config.scraper_backend.value
        scraper = create_scraper(backend_name, self._scraper_config)

        pages = []
        errors = []

        try:
            async with scraper:
                async for page in scraper.scrape_site(start_url):
                    pages.append(page)

                    # Save page to disk
                    try:
                        await self._save_page(page, site_dir)
                    except Exception as e:
                        logger.error(f"Failed to save page {page.url}: {e}")
                        errors.append({"url": page.url, "error": str(e)})
                        # Continue with other pages despite the error

        except Exception as e:
            logger.error(f"Crawl failed: {e}")
            raise

        logger.info(
            f"Crawl completed. Scraped {len(pages)} pages with {len(errors)} errors"
        )

        return {
            "pages": pages,
            "total_pages": len(pages),
            "errors": errors,
            "output_dir": site_dir,
        }

    async def _save_page(self, page: ScrapedPage, output_dir: Path) -> Path:
        """Save a scraped page to disk.

        Args:
            page: ScrapedPage instance
            output_dir: Directory to save the page

        Returns:
            Path to saved file
        """
        # Parse URL to create file path
        parsed = urlparse(page.url)

        # Create subdirectories based on URL path
        if parsed.path and parsed.path != "/":
            # Remove leading slash and split path
            path_parts = parsed.path.lstrip("/").split("/")

            # Handle file extension
            if path_parts[-1].endswith(".html") or "." in path_parts[-1]:
                filename = path_parts[-1]
                subdirs = path_parts[:-1]
            else:
                # Assume it's a directory, create index.html
                filename = "index.html"
                subdirs = path_parts

            # Create subdirectories with path validation
            if subdirs:
                # Sanitize subdirectory names to prevent path traversal
                safe_subdirs = []
                for part in subdirs:
                    # Remove any path traversal attempts
                    safe_part = (
                        part.replace("..", "").replace("./", "").replace("\\", "")
                    )
                    if safe_part and safe_part not in (".", ".."):
                        safe_subdirs.append(safe_part)

                if safe_subdirs:
                    subdir = output_dir / Path(*safe_subdirs)
                    subdir.mkdir(parents=True, exist_ok=True)
                    file_path = subdir / filename
                else:
                    file_path = output_dir / filename
            else:
                file_path = output_dir / filename
        else:
            # Root page
            file_path = output_dir / "index.html"

        # Ensure .html extension
        if not file_path.suffix:
            file_path = file_path.with_suffix(".html")
        elif file_path.suffix not in (".html", ".htm"):
            file_path = file_path.with_name(f"{file_path.name}.html")

        # Write content
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(page.content, encoding=page.encoding)

        logger.debug(f"Saved {page.url} to {file_path}")

        # Save metadata if available
        try:
            metadata_path = file_path.with_suffix(".meta.json")
            import json

            metadata = {
                "url": page.url,
                "title": page.title,
                "encoding": page.encoding,
                "status_code": page.status_code,
                "headers": page.headers if page.headers else {},
                "metadata": page.metadata if page.metadata else {},
            }
            # Filter out None values and ensure all keys are strings
            clean_metadata = {}
            for k, v in metadata.items():
                if v is not None:
                    if isinstance(v, dict):
                        # Clean nested dictionaries - ensure no None keys
                        clean_v = {}
                        for sub_k, sub_v in v.items():
                            if sub_k is not None:
                                clean_v[str(sub_k)] = sub_v
                        clean_metadata[k] = clean_v
                    else:
                        clean_metadata[k] = v

            metadata_path.write_text(json.dumps(clean_metadata, indent=2, default=str))
        except Exception as e:
            logger.warning(f"Failed to save metadata for {page.url}: {e}")
            # Don't fail the entire page save just because metadata failed

        return file_path

    def find_downloaded_files(self, site_dir: Path) -> List[Path]:
        """Find all HTML files in the output directory.

        Args:
            site_dir: Directory containing downloaded files

        Returns:
            List of HTML file paths
        """
        if not site_dir.exists():
            logger.warning(f"Site directory does not exist: {site_dir}")
            return []

        html_files = []

        # Find all HTML files
        patterns = ["*.html", "*.htm"]
        for pattern in patterns:
            files = list(site_dir.rglob(pattern))
            html_files.extend(files)

        # Filter out metadata files
        filtered_files = [f for f in html_files if not f.name.endswith(".meta.json")]

        logger.info(f"Found {len(filtered_files)} HTML files in {site_dir}")
        return sorted(filtered_files)

    def crawl_sync(self, start_url: str, output_dir: Path) -> Path:
        """Synchronous version of crawl method.

        Args:
            start_url: Starting URL for crawling
            output_dir: Directory to store downloaded files

        Returns:
            Path to site directory
        """
        # Run async crawl using asyncio.run()
        result = asyncio.run(self.crawl(start_url, output_dir))
        return result["output_dir"]
