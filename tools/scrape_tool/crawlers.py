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
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
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
        self._db_path: Optional[Path] = None
        self._db_conn: Optional[sqlite3.Connection] = None

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
            "allowed_path": self.config.allowed_path,
            "exclude_patterns": exclude_patterns,
            "respect_robots_txt": self.config.respect_robots_txt,
            "concurrent_requests": self.config.concurrent_requests,
            "request_delay": self.config.request_delay,
            "timeout": float(self.config.timeout),
            "follow_redirects": True,  # Always follow redirects
            "ignore_get_params": self.config.ignore_get_params,
            "check_canonical": self.config.check_canonical,
            "check_content_duplicates": self.config.check_content_duplicates,
            "check_ssrf": self.config.check_ssrf,
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

    def _init_database(self, output_dir: Path) -> None:
        """Initialize SQLite database for tracking scraped URLs.

        Args:
            output_dir: Directory where the database will be created
        """
        self._db_path = output_dir / "scrape_tracker.db"
        self._db_conn = sqlite3.connect(str(self._db_path))

        # Create table if it doesn't exist
        cursor = self._db_conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scraped_urls (
                url TEXT PRIMARY KEY,
                normalized_url TEXT,
                canonical_url TEXT,
                content_checksum TEXT,
                status_code INTEGER,
                target_filename TEXT,
                scraped_at TIMESTAMP,
                error TEXT
            )
        """
        )

        # Create table for content checksums
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS content_checksums (
                checksum TEXT PRIMARY KEY,
                first_url TEXT,
                first_seen TIMESTAMP
            )
        """
        )
        self._db_conn.commit()
        cursor.close()

    def _close_database(self) -> None:
        """Close the database connection."""
        if self._db_conn:
            self._db_conn.close()
            self._db_conn = None

    def _is_url_scraped(self, url: str) -> bool:
        """Check if a URL has already been scraped.

        Args:
            url: URL to check

        Returns:
            True if URL has been scraped, False otherwise
        """
        if not self._db_conn:
            return False

        cursor = self._db_conn.cursor()
        cursor.execute("SELECT 1 FROM scraped_urls WHERE url = ?", (url,))
        result = cursor.fetchone()
        cursor.close()
        return result is not None

    def _get_scraped_urls(self) -> Set[str]:
        """Get all URLs that have been scraped.

        Returns:
            Set of scraped URLs
        """
        if not self._db_conn:
            return set()

        cursor = self._db_conn.cursor()
        cursor.execute("SELECT url FROM scraped_urls")
        urls = {row[0] for row in cursor.fetchall()}
        cursor.close()
        return urls

    def _get_content_checksums(self) -> Set[str]:
        """Get all content checksums from previous scraping.

        Returns:
            Set of content checksums
        """
        if not self._db_conn:
            return set()

        cursor = self._db_conn.cursor()
        cursor.execute("SELECT checksum FROM content_checksums")
        checksums = {row[0] for row in cursor.fetchall()}
        cursor.close()
        return checksums

    def _record_content_checksum(self, checksum: str, url: str) -> None:
        """Record a content checksum in the database.

        Args:
            checksum: Content checksum
            url: First URL where this content was seen
        """
        if not self._db_conn:
            return

        cursor = self._db_conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO content_checksums (checksum, first_url, first_seen)
                VALUES (?, ?, ?)
            """,
                (checksum, url, datetime.now()),
            )
            self._db_conn.commit()
        except sqlite3.IntegrityError:
            # Checksum already exists
            pass
        cursor.close()

    def _is_content_checksum_exists(self, checksum: str) -> bool:
        """Check if a content checksum already exists in the database.

        Args:
            checksum: Content checksum to check

        Returns:
            True if checksum exists, False otherwise
        """
        if not self._db_conn:
            return False

        cursor = self._db_conn.cursor()
        cursor.execute(
            "SELECT 1 FROM content_checksums WHERE checksum = ?", (checksum,)
        )
        result = cursor.fetchone()
        cursor.close()
        return result is not None

    def _record_scraped_url(
        self,
        url: str,
        status_code: Optional[int],
        target_filename: str,
        error: Optional[str] = None,
        normalized_url: Optional[str] = None,
        canonical_url: Optional[str] = None,
        content_checksum: Optional[str] = None,
    ) -> None:
        """Record a scraped URL in the database.

        Args:
            url: URL that was scraped
            status_code: HTTP status code
            target_filename: Path to the saved file
            error: Error message if scraping failed
            normalized_url: URL after GET parameter normalization
            canonical_url: Canonical URL from the page
            content_checksum: SHA-256 checksum of text content
        """
        if not self._db_conn:
            return

        cursor = self._db_conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO scraped_urls 
            (url, normalized_url, canonical_url, content_checksum, 
             status_code, target_filename, scraped_at, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                url,
                normalized_url,
                canonical_url,
                content_checksum,
                status_code,
                target_filename,
                datetime.now(),
                error,
            ),
        )
        self._db_conn.commit()
        cursor.close()

    def _get_scraped_pages_info(self) -> List[Dict[str, Any]]:
        """Get information about previously scraped pages.

        Returns:
            List of dictionaries with url and target_filename
        """
        if not self._db_conn:
            return []

        cursor = self._db_conn.cursor()
        cursor.execute(
            """
            SELECT url, target_filename 
            FROM scraped_urls 
            WHERE error IS NULL AND target_filename != ''
        """
        )
        pages = [{"url": row[0], "filename": row[1]} for row in cursor.fetchall()]
        cursor.close()
        return pages

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

        # Initialize database for tracking
        self._init_database(output_dir)

        # Check if this is a resume operation
        scraped_urls = self._get_scraped_urls()
        if scraped_urls:
            logger.info(
                f"Resuming crawl - found {len(scraped_urls)} previously scraped URLs"
            )

        # Create scraper instance
        backend_name = self.config.scraper_backend.value
        scraper = create_scraper(backend_name, self._scraper_config)

        pages = []
        errors = []

        try:
            async with scraper:
                # Pass already scraped URLs to the scraper if it supports it
                if hasattr(scraper, "_visited_urls"):
                    scraper._visited_urls.update(scraped_urls)

                # Set up checksum callback if deduplication is enabled
                if self._scraper_config.check_content_duplicates:
                    # Pass the database connection to the scraper for checksum queries
                    if hasattr(scraper, "set_checksum_callback"):
                        scraper.set_checksum_callback(self._is_content_checksum_exists)
                        logger.info("Enabled database-backed content deduplication")

                # Pass information about scraped pages for resume functionality
                if scraped_urls and hasattr(scraper, "set_resume_info"):
                    pages_info = self._get_scraped_pages_info()
                    resume_info = []
                    for page_info in pages_info[:20]:  # Read first 20 pages for links
                        try:
                            file_path = output_dir / page_info["filename"]
                            if file_path.exists():
                                content = file_path.read_text(encoding="utf-8")
                                resume_info.append(
                                    {"url": page_info["url"], "content": content}
                                )
                        except Exception as e:
                            logger.warning(
                                f"Failed to read {page_info['filename']}: {e}"
                            )

                    if resume_info:
                        scraper.set_resume_info(resume_info)

                async for page in scraper.scrape_site(start_url):
                    # Skip if already scraped
                    if self._is_url_scraped(page.url):
                        logger.info(f"Skipping already scraped URL: {page.url}")
                        continue

                    # Log progress - show current URL being scraped
                    pages.append(page)
                    logger.info(f"Processing: {page.url} (page {len(pages)})")

                    # Save page to disk
                    try:
                        file_path = await self._save_page(page, site_dir)
                        # Record successful scrape with all metadata
                        self._record_scraped_url(
                            page.url,
                            page.status_code,
                            str(file_path.relative_to(output_dir)),
                            error=None,
                            normalized_url=page.normalized_url,
                            canonical_url=page.canonical_url,
                            content_checksum=page.content_checksum,
                        )
                        # Record content checksum if present
                        if (
                            page.content_checksum
                            and self._scraper_config.check_content_duplicates
                        ):
                            self._record_content_checksum(
                                page.content_checksum, page.url
                            )
                    except Exception as e:
                        logger.error(f"Failed to save page {page.url}: {e}")
                        errors.append({"url": page.url, "error": str(e)})
                        # Record failed scrape
                        self._record_scraped_url(
                            page.url,
                            page.status_code if hasattr(page, "status_code") else None,
                            "",
                            str(e),
                        )
                        # Continue with other pages despite the error

        except Exception as e:
            logger.error(f"Crawl failed: {e}")
            raise
        finally:
            # Always close database connection
            self._close_database()

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
        try:
            # Run async crawl using asyncio.run()
            result = asyncio.run(self.crawl(start_url, output_dir))
            return result["output_dir"]
        except KeyboardInterrupt:
            # Re-raise to let CLI handle it gracefully
            raise
