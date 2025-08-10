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
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urlparse, urljoin

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
        self._session_id: Optional[int] = None

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

    def _migrate_database_v2(self, cursor) -> None:
        """Migrate database to v2 with session support.
        
        TODO: Remove this migration after 2025-10 when all users have updated.
        Migration adds:
        - scraping_sessions table
        - session_id column to scraped_urls
        - Default session 1 for legacy data
        """
        # Check if migration is needed
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scraping_sessions'")
        if cursor.fetchone() is not None:
            return  # Already migrated
        
        logger.info("Migrating database to v2 (adding session support)")
        
        # Create scraping_sessions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scraping_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_url TEXT NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                total_pages INTEGER DEFAULT 0,
                successful_pages INTEGER DEFAULT 0,
                failed_pages INTEGER DEFAULT 0,
                max_depth INTEGER,
                max_pages INTEGER,
                allowed_path TEXT,
                excluded_paths TEXT,
                scraper_backend TEXT,
                request_delay REAL,
                concurrent_requests INTEGER,
                ignore_get_params BOOLEAN,
                check_canonical BOOLEAN,
                check_content_duplicates BOOLEAN,
                force_rescrape BOOLEAN,
                user_agent TEXT,
                timeout INTEGER,
                status TEXT DEFAULT 'running'
            )
        """
        )
        
        # Check if scraped_urls exists and needs session_id column
        cursor.execute("PRAGMA table_info(scraped_urls)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if columns and 'session_id' not in columns:
            # Add session_id column
            cursor.execute("ALTER TABLE scraped_urls ADD COLUMN session_id INTEGER DEFAULT 1")
            
            # Create default session for existing data
            cursor.execute("""
                INSERT INTO scraping_sessions 
                (id, start_url, start_time, status, total_pages)
                VALUES (1, 'Legacy data (before session tracking)', 
                        COALESCE((SELECT MIN(scraped_at) FROM scraped_urls), datetime('now')),
                        'completed',
                        (SELECT COUNT(*) FROM scraped_urls WHERE error IS NULL))
            """)
            
            # Update all existing URLs to session 1
            cursor.execute("UPDATE scraped_urls SET session_id = 1 WHERE session_id IS NULL")
        
        self._db_conn.commit()
        logger.info("Database migration to v2 completed")

    def _cleanup_orphaned_sessions(self) -> None:
        """Clean up sessions that were left in 'running' state from crashes or kills.
        
        Mark old running sessions as 'interrupted' if no URLs have been scraped 
        in the last hour (indicating the process died).
        """
        if not self._db_conn:
            return
            
        cursor = self._db_conn.cursor()
        
        # Find sessions that are still marked as running
        cursor.execute(
            """
            SELECT id, start_url, start_time 
            FROM scraping_sessions 
            WHERE status = 'running'
            """
        )
        
        running_sessions = cursor.fetchall()
        orphaned_sessions = []
        
        one_hour_ago = datetime.now() - timedelta(hours=1)
        
        # Check each running session to see if it's truly orphaned
        for session_id, start_url, start_time in running_sessions:
            # Get the most recent scraped URL timestamp for this session
            cursor.execute(
                """
                SELECT MAX(scraped_at) 
                FROM scraped_urls 
                WHERE session_id = ?
                """,
                (session_id,)
            )
            result = cursor.fetchone()
            last_activity = result[0] if result and result[0] else start_time
            
            # If no activity in the last hour, consider it orphaned
            # Convert string timestamp to datetime if needed
            if isinstance(last_activity, str):
                from datetime import datetime as dt
                last_activity = dt.fromisoformat(last_activity.replace('Z', '+00:00'))
            
            if last_activity < one_hour_ago:
                orphaned_sessions.append((session_id, start_url, start_time))
        
        for session_id, start_url, start_time in orphaned_sessions:
            # Get statistics for the orphaned session
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN error IS NULL THEN 1 END) as successful,
                    COUNT(CASE WHEN error IS NOT NULL THEN 1 END) as failed
                FROM scraped_urls 
                WHERE session_id = ?
                """,
                (session_id,)
            )
            result = cursor.fetchone()
            total, successful, failed = result if result else (0, 0, 0)
            
            # Mark as interrupted and update statistics
            cursor.execute(
                """
                UPDATE scraping_sessions 
                SET status = 'interrupted', 
                    end_time = ?,
                    total_pages = ?,
                    successful_pages = ?,
                    failed_pages = ?
                WHERE id = ?
                """,
                (start_time, total, successful, failed, session_id)
            )
            
            logger.warning(
                f"Cleaned up orphaned session #{session_id} from {start_time} "
                f"({successful} pages scraped before interruption)"
            )
        
        if orphaned_sessions:
            self._db_conn.commit()
            logger.info(f"Cleaned up {len(orphaned_sessions)} orphaned sessions")
        
        cursor.close()

    def _init_database(self, output_dir: Path) -> None:
        """Initialize SQLite database for tracking scraped URLs.

        Args:
            output_dir: Directory where the database will be created
        """
        self._db_path = output_dir / "scrape_tracker.db"
        self._db_conn = sqlite3.connect(str(self._db_path))

        # Create table if it doesn't exist
        cursor = self._db_conn.cursor()
        
        # Run migration if needed (TODO: Remove after 2025-10)
        self._migrate_database_v2(cursor)
        
        # Clean up any orphaned sessions from previous crashes
        self._cleanup_orphaned_sessions()
        
        # Create current schema tables (if not created by migration)
        # Create scraping_sessions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scraping_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_url TEXT NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                total_pages INTEGER DEFAULT 0,
                successful_pages INTEGER DEFAULT 0,
                failed_pages INTEGER DEFAULT 0,
                max_depth INTEGER,
                max_pages INTEGER,
                allowed_path TEXT,
                excluded_paths TEXT,
                scraper_backend TEXT,
                request_delay REAL,
                concurrent_requests INTEGER,
                ignore_get_params BOOLEAN,
                check_canonical BOOLEAN,
                check_content_duplicates BOOLEAN,
                force_rescrape BOOLEAN,
                user_agent TEXT,
                timeout INTEGER,
                status TEXT DEFAULT 'running'
            )
        """
        )
        
        # Create scraped_urls table with session_id
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scraped_urls (
                url TEXT PRIMARY KEY,
                session_id INTEGER,
                normalized_url TEXT,
                canonical_url TEXT,
                content_checksum TEXT,
                status_code INTEGER,
                target_filename TEXT,
                file_type TEXT DEFAULT 'html',
                file_size INTEGER,
                scraped_at TIMESTAMP,
                error TEXT,
                FOREIGN KEY (session_id) REFERENCES scraping_sessions(id)
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

    def _start_session(self, start_url: str) -> int:
        """Start a new scraping session.
        
        Args:
            start_url: The starting URL for this session
            
        Returns:
            The session ID
        """
        if not self._db_conn:
            return None
            
        cursor = self._db_conn.cursor()
        
        # Convert excluded_paths set to JSON string if present
        import json
        excluded_paths_str = None
        if self.config.excluded_paths:
            excluded_paths_str = json.dumps(list(self.config.excluded_paths))
        
        cursor.execute(
            """
            INSERT INTO scraping_sessions (
                start_url, start_time, max_depth, max_pages, allowed_path,
                excluded_paths, scraper_backend, request_delay, concurrent_requests,
                ignore_get_params, check_canonical, check_content_duplicates,
                force_rescrape, user_agent, timeout, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                start_url,
                datetime.now(),
                self.config.max_depth,
                self.config.max_pages,
                self.config.allowed_path,
                excluded_paths_str,
                self.config.scraper_backend.value if self.config.scraper_backend else None,
                self.config.request_delay,
                self.config.concurrent_requests,
                self.config.ignore_get_params,
                self.config.check_canonical,
                self.config.check_content_duplicates,
                self.config.force_rescrape,
                self.config.user_agent,
                self.config.timeout,
                'running'
            )
        )
        self._db_conn.commit()
        
        self._session_id = cursor.lastrowid
        cursor.close()
        
        logger.info(f"Started scraping session #{self._session_id}")
        return self._session_id
    
    def _end_session(self, status: str = 'completed') -> None:
        """End the current scraping session.
        
        Args:
            status: The final status of the session (completed, interrupted, failed)
        """
        if not self._db_conn or not self._session_id:
            return
            
        cursor = self._db_conn.cursor()
        
        # Get counts from the current session
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN error IS NULL THEN 1 END) as successful,
                COUNT(CASE WHEN error IS NOT NULL THEN 1 END) as failed
            FROM scraped_urls 
            WHERE session_id = ?
            """,
            (self._session_id,)
        )
        result = cursor.fetchone()
        if result:
            total, successful, failed = result
        else:
            total, successful, failed = 0, 0, 0
        
        cursor.execute(
            """
            UPDATE scraping_sessions 
            SET end_time = ?, status = ?, total_pages = ?, 
                successful_pages = ?, failed_pages = ?
            WHERE id = ?
            """,
            (
                datetime.now(),
                status,
                total,
                successful,
                failed,
                self._session_id
            )
        )
        self._db_conn.commit()
        cursor.close()
        
        logger.info(f"Ended scraping session #{self._session_id} with status: {status}")

    def _close_database(self) -> None:
        """Close the database connection."""
        if self._db_conn:
            # End session if still running (should not happen in normal flow)
            if self._session_id:
                self._end_session('completed')
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
        file_type: str = "html",
        file_size: Optional[int] = None,
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
            file_type: Type of file (html, image, pdf, etc.)
            file_size: Size of file in bytes
        """
        if not self._db_conn:
            return

        cursor = self._db_conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO scraped_urls 
            (url, session_id, normalized_url, canonical_url, content_checksum, 
             status_code, target_filename, file_type, file_size, scraped_at, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                url,
                self._session_id,
                normalized_url,
                canonical_url,
                content_checksum,
                status_code,
                target_filename,
                file_type,
                file_size,
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
        
        # Start a new session
        self._start_session(start_url)

        # Check if this is a resume operation (skip if force_rescrape is enabled)
        scraped_urls = set()
        if not self.config.force_rescrape:
            scraped_urls = self._get_scraped_urls()
            if scraped_urls:
                logger.info(
                    f"Resuming crawl - found {len(scraped_urls)} previously scraped URLs"
                )
        else:
            logger.info("Force rescrape enabled - ignoring database cache")

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
                                # Only read HTML files, skip binary files (images, PDFs, etc.)
                                if file_path.suffix.lower() in ['.html', '.htm', '.xhtml']:
                                    content = file_path.read_text(encoding="utf-8")
                                    resume_info.append(
                                        {"url": page_info["url"], "content": content}
                                    )
                                else:
                                    logger.debug(f"Skipping binary file for resume: {page_info['filename']}")
                        except Exception as e:
                            logger.warning(
                                f"Failed to read {page_info['filename']}: {e}"
                            )

                    if resume_info:
                        scraper.set_resume_info(resume_info)

                async for page in scraper.scrape_site(start_url):
                    # Skip if already scraped (unless force_rescrape is enabled)
                    if not self.config.force_rescrape and self._is_url_scraped(page.url):
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
                            file_type=page.file_type,
                            file_size=page.file_size,
                        )
                        # Record content checksum if present
                        if (
                            page.content_checksum
                            and self._scraper_config.check_content_duplicates
                        ):
                            self._record_content_checksum(
                                page.content_checksum, page.url
                            )
                        
                        # Extract and download assets if enabled
                        if self.config.download_assets and not page.is_binary:
                            asset_urls = scraper.extract_asset_urls(
                                page.content, page.url, self.config.asset_types
                            )
                            
                            # Security: Limit assets per page (if configured)
                            if self.config.max_assets_per_page > 0 and len(asset_urls) > self.config.max_assets_per_page:
                                logger.warning(
                                    f"Page {page.url} has {len(asset_urls)} assets, "
                                    f"limiting to {self.config.max_assets_per_page}"
                                )
                                asset_urls = list(asset_urls)[:self.config.max_assets_per_page]
                            
                            logger.info(f"Found {len(asset_urls)} assets on {page.url}")
                            
                            # Track total assets downloaded
                            if not hasattr(self, '_total_assets_downloaded'):
                                self._total_assets_downloaded = 0
                            
                            # Track downloaded assets for this page
                            downloaded_assets = {}
                            
                            for asset_url in asset_urls:
                                # Security: Check total assets limit (if configured)
                                if self.config.total_assets_limit > 0 and self._total_assets_downloaded >= self.config.total_assets_limit:
                                    logger.warning(
                                        f"Reached total assets limit of {self.config.total_assets_limit}, "
                                        f"skipping remaining assets"
                                    )
                                    break
                                
                                # Skip if already downloaded
                                if not self.config.force_rescrape and self._is_url_scraped(asset_url):
                                    logger.debug(f"Skipping already downloaded asset: {asset_url}")
                                    # Still track it for HTML update if we can find its path
                                    asset_info = self._get_scraped_url_info(asset_url)
                                    if asset_info and asset_info.get('target_filename'):
                                        downloaded_assets[asset_url] = output_dir / asset_info['target_filename']
                                    continue
                                
                                # Download asset
                                logger.debug(f"Downloading asset: {asset_url}")
                                asset_page = await scraper.download_binary_file(
                                    asset_url, self.config.max_asset_size
                                )
                                
                                if asset_page:
                                    try:
                                        asset_path = await self._save_page(asset_page, site_dir)
                                        self._record_scraped_url(
                                            asset_page.url,
                                            asset_page.status_code,
                                            str(asset_path.relative_to(output_dir)),
                                            error=None,
                                            file_type=asset_page.file_type,
                                            file_size=asset_page.file_size,
                                        )
                                        self._total_assets_downloaded += 1
                                        downloaded_assets[asset_url] = asset_path
                                        logger.debug(f"Saved asset {asset_url} to {asset_path}")
                                    except ValueError as e:
                                        # Security exception (dangerous file, path traversal, etc.)
                                        logger.error(f"Security: Blocked asset {asset_url}: {e}")
                                    except Exception as e:
                                        logger.error(f"Failed to save asset {asset_url}: {e}")
                                else:
                                    logger.warning(f"Failed to download asset: {asset_url}")
                            
                            # Update HTML file with correct asset paths if we downloaded any
                            if downloaded_assets:
                                await self._update_html_with_asset_paths(file_path, page, site_dir, downloaded_assets)
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
            if self._session_id:
                self._end_session('failed')
            raise
        finally:
            # End session with completed status if not already ended
            if self._session_id and self._db_conn:
                self._end_session('completed')
            # Always close database connection
            self._close_database()

        logger.info(
            f"Crawl completed. Scraped {len(pages)} pages with {len(errors)} errors"
        )

        return {
            "pages": pages,
            "total_pages": len(pages),
            "pages_scraped": len(pages),  # For compatibility
            "errors": errors,
            "output_dir": site_dir,
        }

    def _get_scraped_url_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Get information about a previously scraped URL.
        
        Args:
            url: The URL to look up
            
        Returns:
            Dictionary with url info or None if not found
        """
        if not self._db_conn:
            return None
        
        try:
            cursor = self._db_conn.cursor()
            cursor.execute(
                "SELECT target_filename, status_code, error, scraped_at FROM scraped_urls WHERE url = ?",
                (url,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    'target_filename': row[0],
                    'status_code': row[1],
                    'error': row[2],
                    'scraped_at': row[3]
                }
        except Exception as e:
            logger.error(f"Failed to get scraped URL info: {e}")
        
        return None
    
    async def _update_html_with_asset_paths(self, html_path: Path, page: ScrapedPage, site_dir: Path, downloaded_assets: Dict[str, Path]):
        """Update HTML file with correct paths to downloaded assets.
        
        Args:
            html_path: Path to the HTML file to update
            page: The original ScrapedPage object
            site_dir: The site directory
            downloaded_assets: Map of asset URLs to their local paths
        """
        try:
            # Read the current HTML content
            html_content = html_path.read_text(encoding=page.encoding)
            
            # Adjust links with the downloaded asset paths
            updated_content = self._adjust_html_links(
                html_content,
                page.url,
                html_path,
                site_dir,
                downloaded_assets
            )
            
            # Write the updated content back
            html_path.write_text(updated_content, encoding=page.encoding)
            logger.debug(f"Updated HTML file {html_path} with {len(downloaded_assets)} asset paths")
            
        except Exception as e:
            logger.error(f"Failed to update HTML with asset paths: {e}")
    
    def _adjust_html_links(self, html_content: str, original_url: str, saved_path: Path, site_dir: Path, downloaded_assets: Dict[str, Path] = None) -> str:
        """Adjust relative links in HTML content to work from the new saved location.
        
        Args:
            html_content: The HTML content to adjust
            original_url: The original URL of the page
            saved_path: Where the file will be saved
            site_dir: The site directory (domain folder)
            downloaded_assets: Optional mapping of asset URLs to their local paths
            
        Returns:
            HTML content with adjusted links
        """
        import os
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin, urlparse
        
        soup = BeautifulSoup(html_content, 'html.parser')
        original_parsed = urlparse(original_url)
        
        # Calculate the relative path from saved location to site root
        try:
            rel_to_root = os.path.relpath(site_dir, saved_path.parent)
            if rel_to_root == '.':
                rel_to_root = ''
            else:
                rel_to_root = rel_to_root.replace('\\', '/') + '/'
        except ValueError:
            # If on different drives on Windows
            rel_to_root = ''
        
        # Adjust all links
        for tag_name, attr_name in [('a', 'href'), ('link', 'href'), ('script', 'src'), ('img', 'src'), 
                                     ('source', 'srcset'), ('source', 'src'), ('video', 'src'), ('audio', 'src')]:
            for tag in soup.find_all(tag_name):
                attr_value = tag.get(attr_name)
                if not attr_value:
                    continue
                    
                # Skip anchors and special protocols (but not http/https - we might have downloaded them)
                if attr_value.startswith(('#', 'mailto:', 'javascript:', 'data:')):
                    continue
                
                # Check if this is an asset we downloaded
                if downloaded_assets and self.config.download_assets:
                    # Build the absolute URL for this attribute
                    if attr_value.startswith(('http://', 'https://', '//')):
                        absolute_url = attr_value
                        if attr_value.startswith('//'):
                            absolute_url = original_parsed.scheme + ':' + attr_value
                    else:
                        # Relative URL - resolve it against the original page URL
                        absolute_url = urljoin(original_url, attr_value)
                    
                    # Check if we downloaded this asset
                    if absolute_url in downloaded_assets:
                        # Replace with path to downloaded asset
                        asset_path = downloaded_assets[absolute_url]
                        # Calculate relative path from HTML file to asset
                        try:
                            rel_path = os.path.relpath(asset_path, saved_path.parent)
                            rel_path = rel_path.replace('\\', '/')
                            tag[attr_name] = rel_path
                            continue  # Skip normal link adjustment for this asset
                        except ValueError:
                            # Different drives on Windows, use the original logic
                            pass
                
                # Skip absolute URLs after checking for downloaded assets
                if attr_value.startswith(('http://', 'https://', '//')):
                    continue
                
                # Handle relative URLs
                if attr_value.startswith('/'):
                    # Absolute path - make it relative to site root
                    new_path = rel_to_root + attr_value.lstrip('/')
                    tag[attr_name] = new_path
                elif attr_value.startswith('./'):
                    # Relative to current directory - need to adjust based on original URL structure
                    # Get the original directory path
                    orig_path_parts = original_parsed.path.rstrip('/').split('/')
                    if orig_path_parts[-1] and ('.' in orig_path_parts[-1] or not orig_path_parts[-1]):
                        # Last part is a file, remove it
                        orig_path_parts = orig_path_parts[:-1]
                    
                    # Reconstruct the path
                    relative_part = attr_value[2:]  # Remove ./
                    if orig_path_parts:
                        # The link was relative to /magazin/ or similar
                        new_path = rel_to_root + '/'.join(orig_path_parts[1:]) + '/' + relative_part
                    else:
                        new_path = rel_to_root + relative_part
                    
                    # Clean up the path
                    new_path = new_path.replace('//', '/')
                    tag[attr_name] = new_path
                elif attr_value.startswith('../'):
                    # Handle parent directory references
                    # This is complex, so for now just make it relative to root
                    cleaned = attr_value
                    levels_up = 0
                    while cleaned.startswith('../'):
                        levels_up += 1
                        cleaned = cleaned[3:]
                    
                    orig_path_parts = original_parsed.path.rstrip('/').split('/')
                    if orig_path_parts[-1] and '.' in orig_path_parts[-1]:
                        orig_path_parts = orig_path_parts[:-1]
                    
                    # Go up the required number of levels
                    if len(orig_path_parts) > levels_up:
                        base_parts = orig_path_parts[1:-levels_up] if levels_up > 0 else orig_path_parts[1:]
                        if base_parts:
                            new_path = rel_to_root + '/'.join(base_parts) + '/' + cleaned
                        else:
                            new_path = rel_to_root + cleaned
                    else:
                        new_path = rel_to_root + cleaned
                    
                    new_path = new_path.replace('//', '/')
                    tag[attr_name] = new_path
        
        return str(soup)

    async def _save_page(self, page: ScrapedPage, output_dir: Path) -> Path:
        """Save a scraped page to disk with adjusted links.

        Args:
            page: ScrapedPage instance
            output_dir: Directory to save the page

        Returns:
            Path to saved file
        """
        # Handle binary files differently
        if page.is_binary and page.binary_content:
            return await self._save_binary_file(page, output_dir)
        
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

        # Adjust links in HTML content before saving
        adjusted_content = self._adjust_html_links(
            page.content, 
            page.url, 
            file_path,
            output_dir.parent  # This is the site_dir (domain folder)
        )

        # Write content
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(adjusted_content, encoding=page.encoding)

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

    async def _save_binary_file(self, page: ScrapedPage, output_dir: Path) -> Path:
        """Save binary file to disk with security checks.
        
        Args:
            page: ScrapedPage with binary content
            output_dir: Directory to save the file
            
        Returns:
            Path to saved file
            
        Raises:
            ValueError: If file path is unsafe or file type is dangerous
        """
        import hashlib
        import re
        import os
        
        # Security: Define dangerous file extensions that should never be saved
        DANGEROUS_EXTENSIONS = {
            '.exe', '.dll', '.bat', '.cmd', '.com', '.scr', '.vbs', '.vbe',
            '.js', '.jse', '.wsf', '.wsh', '.ps1', '.psm1', '.msi', '.jar',
            '.app', '.deb', '.rpm', '.dmg', '.pkg', '.sh', '.bash', '.zsh',
            '.fish', '.ksh', '.csh', '.tcsh', '.py', '.pyc', '.pyo', '.pyw',
            '.rb', '.pl', '.php', '.asp', '.aspx', '.jsp', '.cgi'
        }
        
        # Parse URL to create file path
        parsed = urlparse(page.url)
        
        # Create assets subdirectory if configured
        assets_dir = output_dir / self.config.assets_subdirectory
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        # Create file path from URL
        if parsed.path and parsed.path != "/":
            path_parts = parsed.path.lstrip("/").split("/")
            filename = path_parts[-1]
            subdirs = path_parts[:-1] if len(path_parts) > 1 else []
            
            # Security: Check for dangerous extensions
            file_ext = Path(filename).suffix.lower()
            if file_ext in DANGEROUS_EXTENSIONS:
                logger.warning(f"Blocked dangerous file type {file_ext}: {page.url}")
                raise ValueError(f"Dangerous file type {file_ext} not allowed")
            
            # Security: Sanitize filename more aggressively
            # Remove any character that could be used for path traversal or command injection
            safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
            safe_filename = safe_filename.lstrip('.')  # Remove leading dots
            
            if not safe_filename:
                safe_filename = f"asset_{hashlib.md5(page.url.encode()).hexdigest()[:8]}"
            
            # Create subdirectories with strict sanitization
            if subdirs:
                safe_subdirs = []
                for part in subdirs:
                    # Security: More aggressive sanitization
                    safe_part = re.sub(r'[^a-zA-Z0-9._-]', '_', part)
                    safe_part = safe_part.strip('._')  # Remove leading/trailing dots and underscores
                    if safe_part and safe_part not in (".", ".."):
                        safe_subdirs.append(safe_part)
                
                if safe_subdirs:
                    subdir = assets_dir / Path(*safe_subdirs)
                    subdir.mkdir(parents=True, exist_ok=True)
                    file_path = subdir / safe_filename  # Use safe_filename instead of filename
                else:
                    file_path = assets_dir / safe_filename  # Use safe_filename
            else:
                file_path = assets_dir / safe_filename  # Use safe_filename
        else:
            # Use URL hash for files without clear names
            url_hash = hashlib.md5(page.url.encode()).hexdigest()[:8]
            extension = ""
            if page.file_type == "image":
                # Try to determine extension from content type
                content_type = page.headers.get("content-type", "")
                if "jpeg" in content_type or "jpg" in content_type:
                    extension = ".jpg"
                elif "png" in content_type:
                    extension = ".png"
                elif "gif" in content_type:
                    extension = ".gif"
                elif "webp" in content_type:
                    extension = ".webp"
                elif "svg" in content_type:
                    extension = ".svg"
            elif page.file_type == "pdf":
                extension = ".pdf"
            
            # Security: Check extension even for generated filenames
            if extension.lower() in DANGEROUS_EXTENSIONS:
                logger.warning(f"Blocked dangerous file type {extension}: {page.url}")
                raise ValueError(f"Dangerous file type {extension} not allowed")
            
            file_path = assets_dir / f"asset_{url_hash}{extension}"
        
        # Security: Final path validation - ensure file_path is within output_dir
        try:
            # Don't use resolve() on non-existent paths - it can cause issues
            # Instead, check the relative path components
            import os
            output_dir_abs = output_dir.resolve()
            
            # Get the relative path from output_dir to file_path
            try:
                rel_path = os.path.relpath(file_path, output_dir)
                # Check if path tries to escape (contains ..)
                if ".." in rel_path:
                    raise ValueError(f"Path traversal attempt detected: {rel_path}")
            except ValueError:
                # os.path.relpath raises ValueError if on different drives on Windows
                raise ValueError(f"Invalid file path: {file_path}")
                
        except Exception as e:
            logger.error(f"Path validation failed for {page.url}: {e}")
            raise ValueError(f"Invalid file path: {e}")
        
        # Security: Check file size before writing
        if page.file_size and page.file_size > self.config.max_asset_size:
            raise ValueError(f"File size {page.file_size} exceeds limit {self.config.max_asset_size}")
        
        # Write binary content
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(page.binary_content)
        
        # Save metadata
        try:
            metadata_path = file_path.with_suffix(file_path.suffix + ".meta.json")
            metadata = {
                "url": page.url,
                "file_type": page.file_type,
                "file_size": page.file_size,
                "status_code": page.status_code,
                "headers": page.headers or {},
                "checksum": hashlib.sha256(page.binary_content).hexdigest(),
            }
            
            # Add validation results if available
            if page.metadata and 'validation' in page.metadata:
                metadata['validation'] = page.metadata['validation']
            
            metadata_path.write_text(json.dumps(metadata, indent=2, default=str))
        except Exception as e:
            logger.warning(f"Failed to save metadata for binary file {page.url}: {e}")
        
        logger.debug(f"Saved binary file {page.url} to {file_path}")
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
            # Mark session as interrupted before re-raising
            if self._session_id:
                try:
                    self._end_session('interrupted')
                except:
                    pass  # Don't let DB errors mask the interrupt
            # Re-raise to let CLI handle it gracefully
            raise

    def crawl_sync_with_stats(self, start_url: str, output_dir: Path) -> Dict[str, Any]:
        """Synchronous version of crawl method that returns detailed statistics.

        Args:
            start_url: Starting URL for crawling
            output_dir: Directory to store downloaded files

        Returns:
            Dictionary containing:
            - site_dir: Path to site directory
            - scraped_urls: List of URLs scraped in this session
            - errors: List of errors encountered in this session
            - total_pages: Total number of pages scraped in this session
            - session_files: List of files created in this session
            - session_id: ID of this scraping session
        """
        try:
            # Run async crawl using asyncio.run()
            result = asyncio.run(self.crawl(start_url, output_dir))
            
            # Extract URLs from the pages scraped in this session
            pages = result.get("pages", [])
            scraped_urls = [page.url for page in pages]
            
            # Get list of files created in this session
            session_files = []
            for page in pages:
                # Reconstruct the file path for each scraped page using same logic as _save_page
                parsed = urlparse(page.url)
                # Note: result["output_dir"] already contains the domain (it's actually site_dir)
                site_dir = result["output_dir"]
                
                # Same logic as in _save_page method
                if parsed.path and parsed.path != "/":
                    path_parts = parsed.path.lstrip("/").split("/")
                    
                    # Handle file extension
                    if path_parts[-1].endswith(".html") or "." in path_parts[-1]:
                        filename = path_parts[-1]
                        subdirs = path_parts[:-1]
                    else:
                        # Assume it's a directory, create index.html
                        filename = "index.html"
                        subdirs = path_parts
                    
                    # Build the file path
                    if subdirs:
                        # Sanitize subdirectory names (same as _save_page)
                        safe_subdirs = []
                        for part in subdirs:
                            safe_part = part.replace("..", "").replace("./", "").replace("\\", "")
                            if safe_part and safe_part not in (".", ".."):
                                safe_subdirs.append(safe_part)
                        
                        if safe_subdirs:
                            file_path = site_dir / Path(*safe_subdirs) / filename
                        else:
                            file_path = site_dir / filename
                    else:
                        file_path = site_dir / filename
                else:
                    # Root page
                    file_path = site_dir / "index.html"
                
                if file_path.exists():
                    session_files.append(file_path)
            
            return {
                "site_dir": result["output_dir"],
                "scraped_urls": scraped_urls,
                "errors": result.get("errors", []),
                "total_pages": len(pages),
                "pages_scraped": result.get("pages_scraped", len(pages)),
                "session_files": session_files,
                "session_id": self._session_id,
            }
        except KeyboardInterrupt:
            # Mark session as interrupted before re-raising
            if self._session_id:
                try:
                    self._end_session('interrupted')
                except:
                    pass  # Don't let DB errors mask the interrupt
            # Re-raise to let CLI handle it gracefully
            raise
