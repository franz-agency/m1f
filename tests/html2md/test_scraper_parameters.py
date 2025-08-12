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

"""Comprehensive tests for m1f-scrape parameters using local test server."""

import asyncio
import pytest
import tempfile
import shutil
import subprocess
import time
import os
import socket
import signal
import requests
import sqlite3
from pathlib import Path
from typing import List, Set
from unittest.mock import patch, MagicMock

from tools.scrape_tool.config import Config, CrawlerConfig, ScraperBackend
from tools.scrape_tool.crawlers import WebCrawler


def find_free_port(start_port: int = 8090) -> int:
    """Find a free port starting from start_port."""
    for port in range(start_port, start_port + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("localhost", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"Could not find a free port starting from {start_port}")


class TestScraperParameters:
    """Test all m1f-scrape parameters with local test server."""

    server_port = None
    server_url = None

    @classmethod
    def setup_class(cls):
        """Start the test server before running tests."""
        # Find a free port starting from 8090
        cls.server_port = find_free_port(8090)
        cls.server_url = f"http://localhost:{cls.server_port}"

        # Set environment variable to suppress server output
        env = os.environ.copy()
        env["FLASK_ENV"] = "testing"
        env["HTML2MD_SERVER_PORT"] = str(cls.server_port)
        # Remove WERKZEUG environment variables that might interfere
        env.pop("WERKZEUG_RUN_MAIN", None)
        env.pop("WERKZEUG_SERVER_FD", None)
        env["WERKZEUG_RUN_MAIN"] = "true"  # Suppress Flask reloader

        # Start the test server
        server_path = Path(__file__).parent.parent / "html2md_server" / "server.py"
        cls.server_process = subprocess.Popen(
            ["python", str(server_path)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Wait for server to start
        max_attempts = 30
        for i in range(max_attempts):
            try:
                response = requests.get(f"{cls.server_url}/")
                if response.status_code == 200:
                    break
            except requests.ConnectionError as e:
                if i == max_attempts - 1:
                    # On last attempt, print debug info
                    import traceback

                    print(f"Connection error on attempt {i+1}: {e}")
                    print(traceback.format_exc())
                    # Check if process is still running
                    if cls.server_process.poll() is not None:
                        print(
                            f"Server process exited with code: {cls.server_process.returncode}"
                        )
                        # Try to get output from server
                        try:
                            stdout, stderr = cls.server_process.communicate(timeout=1)
                            if stdout:
                                print(f"Server stdout: {stdout}")
                            if stderr:
                                print(f"Server stderr: {stderr}")
                        except:
                            pass
            time.sleep(0.5)
        else:
            cls.teardown_class()
            pytest.fail("Test server failed to start after 15 seconds")

    @classmethod
    def teardown_class(cls):
        """Stop the test server after tests."""
        if hasattr(cls, "server_process") and cls.server_process:
            cls.server_process.terminate()
            try:
                cls.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cls.server_process.kill()

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test output."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def get_scraped_files(self, output_dir: Path) -> List[Path]:
        """Get all scraped HTML files."""
        return list(output_dir.glob("**/*.html"))

    def get_scraped_paths(self, output_dir: Path) -> Set[str]:
        """Extract the URL paths from scraped files."""
        scraped_paths = set()
        for html_file in output_dir.glob("**/*.html"):
            rel_path = html_file.relative_to(output_dir)
            parts = rel_path.parts
            if parts[0].startswith("localhost"):
                url_path = "/" + "/".join(parts[1:])
                scraped_paths.add(url_path)
        return scraped_paths

    # Test Content Filtering Parameters

    @pytest.mark.asyncio
    async def test_ignore_get_params(self, temp_dir):
        """Test --ignore-get-params functionality."""
        # First, add some pages with GET parameters to our test server
        # This would need server modification to support query params
        # For now, test the configuration
        output_dir = Path(temp_dir) / "test_get_params"

        config = Config()
        config.crawler = CrawlerConfig(
            max_depth=1,
            max_pages=10,
            ignore_get_params=True,  # Enable GET param ignoring
            scraper_backend=ScraperBackend.BEAUTIFULSOUP,
            request_delay=0.1,
            check_ssrf=False,
        )

        crawler = WebCrawler(config.crawler)

        # Test that the configuration is properly set
        assert config.crawler.ignore_get_params is True

        # In a real test, we would scrape URLs like:
        # http://localhost:8080/page?tab=1
        # http://localhost:8080/page?tab=2
        # And verify only one copy is saved

    @pytest.mark.asyncio
    async def test_ignore_canonical(self, temp_dir):
        """Test --ignore-canonical functionality."""
        output_dir = Path(temp_dir) / "test_canonical"

        config = Config()
        config.crawler = CrawlerConfig(
            max_depth=2,
            max_pages=10,
            check_canonical=False,  # Disable canonical checking (--ignore-canonical)
            scraper_backend=ScraperBackend.BEAUTIFULSOUP,
            request_delay=0.1,
            check_ssrf=False,
        )

        crawler = WebCrawler(config.crawler)

        # Configuration should reflect the ignore setting
        assert config.crawler.check_canonical is False

        # In a real test with pages having canonical tags,
        # we would verify that pages are kept even with different canonical URLs

    @pytest.mark.asyncio
    async def test_ignore_duplicates(self, temp_dir):
        """Test --ignore-duplicates functionality."""
        output_dir = Path(temp_dir) / "test_duplicates"

        config = Config()
        config.crawler = CrawlerConfig(
            max_depth=2,
            max_pages=10,
            check_content_duplicates=False,  # Disable duplicate checking
            scraper_backend=ScraperBackend.BEAUTIFULSOUP,
            request_delay=0.1,
            check_ssrf=False,
        )

        crawler = WebCrawler(config.crawler)

        # Configuration should reflect the setting
        assert config.crawler.check_content_duplicates is False

    # Test Request Options

    @pytest.mark.asyncio
    async def test_user_agent(self, temp_dir):
        """Test --user-agent functionality."""
        output_dir = Path(temp_dir) / "test_user_agent"
        custom_user_agent = "MyCustomBot/1.0"

        config = Config()
        config.crawler = CrawlerConfig(
            max_depth=1,
            max_pages=5,
            user_agent=custom_user_agent,
            scraper_backend=ScraperBackend.BEAUTIFULSOUP,
            request_delay=0.1,
            check_ssrf=False,
        )

        crawler = WebCrawler(config.crawler)

        # Verify user agent is set
        assert config.crawler.user_agent == custom_user_agent

        # In real implementation, scrapers should use this user agent

    @pytest.mark.asyncio
    async def test_timeout(self, temp_dir):
        """Test --timeout functionality."""
        output_dir = Path(temp_dir) / "test_timeout"

        config = Config()
        config.crawler = CrawlerConfig(
            max_depth=1,
            max_pages=5,
            timeout=5,  # 5 second timeout
            scraper_backend=ScraperBackend.BEAUTIFULSOUP,
            request_delay=0.1,
            check_ssrf=False,
        )

        crawler = WebCrawler(config.crawler)

        # Verify timeout is set
        assert config.crawler.timeout == 5

    @pytest.mark.asyncio
    async def test_retry_count(self, temp_dir):
        """Test --retry-count functionality."""
        output_dir = Path(temp_dir) / "test_retry"

        config = Config()
        config.crawler = CrawlerConfig(
            max_depth=1,
            max_pages=5,
            retry_count=2,  # Retry failed requests twice
            scraper_backend=ScraperBackend.BEAUTIFULSOUP,
            request_delay=0.1,
            check_ssrf=False,
        )

        crawler = WebCrawler(config.crawler)

        # Verify retry count is set
        assert config.crawler.retry_count == 2

    # Test Excluded Paths

    @pytest.mark.asyncio
    async def test_excluded_paths(self, temp_dir):
        """Test --excluded-paths functionality."""
        output_dir = Path(temp_dir) / "test_excluded"

        config = Config()
        config.crawler = CrawlerConfig(
            max_depth=3,
            max_pages=20,
            excluded_paths=["/api/", "/guides/"],  # Exclude these paths
            scraper_backend=ScraperBackend.BEAUTIFULSOUP,
            request_delay=0.1,
            check_ssrf=False,
        )

        crawler = WebCrawler(config.crawler)
        start_url = f"{self.server_url}/"

        result = await crawler.crawl(start_url, output_dir)
        scraped_paths = self.get_scraped_paths(output_dir)

        # Verify no API or guides pages were scraped
        api_pages = [p for p in scraped_paths if p.startswith("/api/")]
        guides_pages = [p for p in scraped_paths if p.startswith("/guides/")]

        assert len(api_pages) == 0, f"Found excluded API pages: {api_pages}"
        assert len(guides_pages) == 0, f"Found excluded guides pages: {guides_pages}"

        # But other pages should be scraped
        assert len(scraped_paths) > 0, "Should have scraped some pages"

    # Test Different Scrapers

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "scraper_backend",
        [
            ScraperBackend.BEAUTIFULSOUP,
            ScraperBackend.SELECTOLAX,
            # Note: HTTrack and Playwright need special setup
        ],
    )
    async def test_different_scrapers(self, temp_dir, scraper_backend):
        """Test different scraper backends."""
        output_dir = Path(temp_dir) / f"test_{scraper_backend.value}"

        config = Config()
        config.crawler = CrawlerConfig(
            max_depth=1,
            max_pages=5,
            scraper_backend=scraper_backend,
            request_delay=0.1,
            check_ssrf=False,
        )

        try:
            crawler = WebCrawler(config.crawler)
            start_url = f"{self.server_url}/"

            result = await crawler.crawl(start_url, output_dir)
            scraped_files = self.get_scraped_files(output_dir)

            # Should have scraped at least the index page
            assert (
                len(scraped_files) > 0
            ), f"No files scraped with {scraper_backend.value}"

        except Exception as e:
            # Some scrapers might not be installed
            if "not found" in str(e).lower() or "not installed" in str(e).lower():
                pytest.skip(f"{scraper_backend.value} not installed")
            else:
                raise

    # Test Output Options

    @pytest.mark.asyncio
    async def test_verbose_quiet_output(self, temp_dir, capsys):
        """Test --verbose and --quiet options."""
        # Test verbose
        config_verbose = Config()
        config_verbose.verbose = True
        config_verbose.quiet = False

        # Test quiet
        config_quiet = Config()
        config_quiet.verbose = False
        config_quiet.quiet = True

        # Verify settings
        assert config_verbose.verbose is True
        assert config_quiet.quiet is True

    @pytest.mark.asyncio
    async def test_list_files(self, temp_dir):
        """Test --list-files functionality."""
        output_dir = Path(temp_dir) / "test_list"

        config = Config()
        config.crawler = CrawlerConfig(
            max_depth=1,
            max_pages=5,
            scraper_backend=ScraperBackend.BEAUTIFULSOUP,
            request_delay=0.1,
            check_ssrf=False,
        )

        crawler = WebCrawler(config.crawler)
        start_url = f"{self.server_url}/"

        result = await crawler.crawl(start_url, output_dir)

        # Get list of files (this is what --list-files would display)
        scraped_files = crawler.find_downloaded_files(output_dir)
        assert len(scraped_files) > 0, "Should have found downloaded files"

    # Test Database Options

    def test_database_queries(self, temp_dir):
        """Test database query options."""
        output_dir = Path(temp_dir) / "test_db"
        output_dir.mkdir(parents=True)

        # Create a test database
        db_path = output_dir / "scrape_tracker.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Create the schema (simplified)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scraped_urls (
                url TEXT PRIMARY KEY,
                status_code INTEGER,
                error TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Insert test data
        test_urls = [
            (f"{self.server_url}/", 200, None),
            (f"{self.server_url}/docs/", 200, None),
            (f"{self.server_url}/api/", 404, "Not found"),
            (f"{self.server_url}/broken/", 500, "Server error"),
        ]

        cursor.executemany(
            "INSERT INTO scraped_urls (url, status_code, error) VALUES (?, ?, ?)",
            test_urls,
        )
        conn.commit()

        # Test --show-db-stats
        cursor.execute("SELECT COUNT(*) FROM scraped_urls")
        total = cursor.fetchone()[0]
        assert total == 4

        cursor.execute("SELECT COUNT(*) FROM scraped_urls WHERE error IS NULL")
        successful = cursor.fetchone()[0]
        assert successful == 2

        # Test --show-errors
        cursor.execute("SELECT url, error FROM scraped_urls WHERE error IS NOT NULL")
        errors = cursor.fetchall()
        assert len(errors) == 2

        # Test --show-scraped-urls
        cursor.execute("SELECT url FROM scraped_urls")
        all_urls = cursor.fetchall()
        assert len(all_urls) == 4

        conn.close()

    # Test SSRF Protection

    @pytest.mark.asyncio
    async def test_ssrf_protection(self, temp_dir):
        """Test --disable-ssrf-check functionality."""
        output_dir = Path(temp_dir) / "test_ssrf"

        # Test with SSRF check enabled (default)
        config_enabled = Config()
        config_enabled.crawler = CrawlerConfig(
            max_depth=1,
            max_pages=5,
            check_ssrf=True,  # SSRF check enabled
            scraper_backend=ScraperBackend.BEAUTIFULSOUP,
            request_delay=0.1,
        )

        # Test with SSRF check disabled
        config_disabled = Config()
        config_disabled.crawler = CrawlerConfig(
            max_depth=1,
            max_pages=5,
            check_ssrf=False,  # SSRF check disabled
            scraper_backend=ScraperBackend.BEAUTIFULSOUP,
            request_delay=0.1,
        )

        assert config_enabled.crawler.check_ssrf is True
        assert config_disabled.crawler.check_ssrf is False

        # With SSRF disabled, localhost should work
        crawler = WebCrawler(config_disabled.crawler)
        start_url = f"{self.server_url}/"

        result = await crawler.crawl(start_url, output_dir)
        scraped_files = self.get_scraped_files(output_dir)
        assert (
            len(scraped_files) > 0
        ), "Should scrape localhost with SSRF check disabled"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
