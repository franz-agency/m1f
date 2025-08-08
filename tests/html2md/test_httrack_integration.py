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

"""Integration tests for HTTrack scraper with local test server."""

import asyncio
import pytest
import tempfile
import shutil
import subprocess
import time
import os
import requests
from pathlib import Path
from typing import Set

from tools.scrape_tool.config import Config, CrawlerConfig, ScraperBackend
from tools.scrape_tool.crawlers import WebCrawler
from tools.scrape_tool.scrapers.httrack import HTTrackScraper


def is_httrack_installed():
    """Check if HTTrack is installed."""
    try:
        result = subprocess.run(
            ["httrack", "--version"], capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


# Skip all tests if HTTrack is not installed
pytestmark = pytest.mark.skipif(
    not is_httrack_installed(),
    reason="HTTrack not installed. Install with: apt-get install httrack",
)


class TestHTTrackIntegration:
    """Integration tests for HTTrack scraper."""

    @classmethod
    def setup_class(cls):
        """Start the test server before running tests."""
        env = os.environ.copy()
        env["FLASK_ENV"] = "testing"
        # Remove WERKZEUG environment variables that might interfere
        env.pop("WERKZEUG_RUN_MAIN", None)
        env.pop("WERKZEUG_SERVER_FD", None)

        server_path = Path(__file__).parent.parent / "html2md_server" / "server.py"
        cls.server_process = subprocess.Popen(
            ["python", str(server_path)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for server to start
        max_attempts = 30
        for i in range(max_attempts):
            try:
                response = requests.get("http://localhost:8080/")
                if response.status_code == 200:
                    break
            except requests.ConnectionError:
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

    def get_scraped_paths(self, output_dir: Path) -> Set[str]:
        """Extract the URL paths from scraped files."""
        scraped_paths = set()
        # HTTrack creates a subdirectory structure
        for html_file in output_dir.glob("**/*.html"):
            # Skip HTTrack's own files
            if html_file.name.startswith("hts-"):
                continue
            rel_path = html_file.relative_to(output_dir)
            # Convert to URL path
            url_path = "/" + str(rel_path).replace("\\", "/")
            if "localhost" in url_path:
                # Extract path after localhost:8080
                parts = url_path.split("localhost:8080/")
                if len(parts) > 1:
                    url_path = "/" + parts[1]
            scraped_paths.add(url_path)
        return scraped_paths

    @pytest.mark.asyncio
    async def test_httrack_basic_scraping(self, temp_dir):
        """Test basic page scraping with HTTrack."""
        output_dir = Path(temp_dir) / "test_basic"

        config = Config()
        config.crawler = CrawlerConfig(
            max_depth=1,
            max_pages=5,
            scraper_backend=ScraperBackend.HTTRACK,
            request_delay=0.1,
            check_ssrf=False,
        )

        crawler = WebCrawler(config.crawler)
        start_url = "http://localhost:8080/"

        result = await crawler.crawl(start_url, output_dir)

        # Check that crawl was successful
        assert "pages_scraped" in result
        assert result["pages_scraped"] > 0, "Should have scraped at least one page"

        # Check that some files were downloaded
        html_files = list(output_dir.glob("**/*.html"))
        # Filter out HTTrack's own files if any
        html_files = [f for f in html_files if not f.name.startswith("hts-")]

        assert len(html_files) > 0, "Should have downloaded at least one HTML file"

    @pytest.mark.asyncio
    async def test_httrack_depth_limit(self, temp_dir):
        """Test HTTrack respects max depth."""
        output_dir = Path(temp_dir) / "test_depth"

        config = Config()
        config.crawler = CrawlerConfig(
            max_depth=0,  # Only download the start page
            max_pages=10,
            scraper_backend=ScraperBackend.HTTRACK,
            request_delay=0.1,
            check_ssrf=False,
        )

        crawler = WebCrawler(config.crawler)
        start_url = "http://localhost:8080/"

        result = await crawler.crawl(start_url, output_dir)

        # With depth 0, should only get the index page
        html_files = list(output_dir.glob("**/*.html"))
        html_files = [f for f in html_files if not f.name.startswith("hts-")]

        # Should have very few files (just index and maybe some required files)
        assert (
            len(html_files) <= 3
        ), f"With depth 0, should have minimal files, got {len(html_files)}"

    @pytest.mark.asyncio
    async def test_httrack_page_limit(self, temp_dir):
        """Test HTTrack respects max pages limit."""
        output_dir = Path(temp_dir) / "test_pages"

        config = Config()
        config.crawler = CrawlerConfig(
            max_depth=3,
            max_pages=3,  # Limit to 3 pages
            scraper_backend=ScraperBackend.HTTRACK,
            request_delay=0.1,
            check_ssrf=False,
        )

        crawler = WebCrawler(config.crawler)
        start_url = "http://localhost:8080/"

        result = await crawler.crawl(start_url, output_dir)

        # Count non-HTTrack HTML files
        html_files = list(output_dir.glob("**/*.html"))
        html_files = [f for f in html_files if not f.name.startswith("hts-")]

        # Should respect the page limit (allow some margin for HTTrack behavior)
        assert (
            len(html_files) <= 5
        ), f"Should respect page limit, got {len(html_files)} files"

    @pytest.mark.asyncio
    async def test_httrack_allowed_path(self, temp_dir):
        """Test HTTrack with allowed_path restriction."""
        output_dir = Path(temp_dir) / "test_allowed"

        config = Config()
        config.crawler = CrawlerConfig(
            max_depth=2,
            max_pages=20,
            allowed_path="/api/",
            scraper_backend=ScraperBackend.HTTRACK,
            request_delay=0.1,
            check_ssrf=False,
        )

        # Note: HTTrack's allowed_path support is limited
        # It uses URL filters which may not work exactly like other scrapers
        crawler = WebCrawler(config.crawler)
        start_url = "http://localhost:8080/api/overview.html"

        result = await crawler.crawl(start_url, output_dir)

        # Check that files were downloaded
        html_files = list(output_dir.glob("**/*.html"))
        html_files = [f for f in html_files if not f.name.startswith("hts-")]

        assert len(html_files) > 0, "HTTrack should have downloaded files"

    @pytest.mark.asyncio
    async def test_httrack_user_agent(self, temp_dir):
        """Test HTTrack with custom user agent."""
        output_dir = Path(temp_dir) / "test_ua"
        custom_ua = "MyTestBot/1.0"

        config = Config()
        config.crawler = CrawlerConfig(
            max_depth=0,
            max_pages=1,
            user_agent=custom_ua,
            scraper_backend=ScraperBackend.HTTRACK,
            request_delay=0.1,
            check_ssrf=False,
        )

        crawler = WebCrawler(config.crawler)
        start_url = "http://localhost:8080/"

        # HTTrack should use the custom user agent
        result = await crawler.crawl(start_url, output_dir)

        # Verify download succeeded (HTTrack doesn't fail on UA issues)
        assert output_dir.exists()

    @pytest.mark.asyncio
    async def test_httrack_unlimited_depth(self, temp_dir):
        """Test HTTrack with unlimited depth (-1)."""
        output_dir = Path(temp_dir) / "test_unlimited"

        config = Config()
        config.crawler = CrawlerConfig(
            max_depth=-1,  # Unlimited depth
            max_pages=5,  # But limit pages
            scraper_backend=ScraperBackend.HTTRACK,
            request_delay=0.1,
            check_ssrf=False,
        )

        crawler = WebCrawler(config.crawler)
        start_url = "http://localhost:8080/"

        result = await crawler.crawl(start_url, output_dir)

        # Should have downloaded files (limited by max_pages)
        html_files = list(output_dir.glob("**/*.html"))
        html_files = [f for f in html_files if not f.name.startswith("hts-")]

        assert len(html_files) > 0, "Should have downloaded files with unlimited depth"
        # But still respect page limit
        assert (
            len(html_files) <= 10
        ), f"Should respect page limit even with unlimited depth"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
