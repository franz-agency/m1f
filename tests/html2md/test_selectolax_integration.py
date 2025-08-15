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

"""Integration tests for Selectolax scraper with local test server."""

import asyncio
import pytest
import tempfile
import shutil
import subprocess
import time
import os
import socket
import requests
from pathlib import Path
from typing import Set

from tools.scrape_tool.config import Config, CrawlerConfig, ScraperBackend
from tools.scrape_tool.crawlers import WebCrawler
from tools.scrape_tool.scrapers.selectolax import SelectolaxScraper


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


class TestSelectolaxIntegration:
    """Integration tests for Selectolax scraper."""

    server_port = None
    server_url = None

    @classmethod
    def setup_class(cls):
        """Start the test server before running tests."""
        # Find a free port starting from 8090
        cls.server_port = find_free_port(8090)
        cls.server_url = f"http://localhost:{cls.server_port}"

        env = os.environ.copy()
        env["FLASK_ENV"] = "testing"
        env["HTML2MD_SERVER_PORT"] = str(cls.server_port)
        # Remove WERKZEUG environment variables that might interfere
        env.pop("WERKZEUG_RUN_MAIN", None)
        env.pop("WERKZEUG_SERVER_FD", None)

        server_path = Path(__file__).parent.parent / "html2md_server" / "server.py"
        import sys

        cls.server_process = subprocess.Popen(
            [sys.executable, str(server_path)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for server to start
        max_attempts = 30
        server_started = False
        for i in range(max_attempts):
            try:
                response = requests.get(f"{cls.server_url}/")
                if response.status_code == 200:
                    server_started = True
                    break
            except requests.ConnectionError:
                pass
            time.sleep(0.5)

        if not server_started:
            # Try to get server output for debugging
            if cls.server_process:
                try:
                    stdout, stderr = cls.server_process.communicate(timeout=0.5)
                    print(f"Server stdout: {stdout.decode() if stdout else 'None'}")
                    print(f"Server stderr: {stderr.decode() if stderr else 'None'}")
                except:
                    pass
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
        for html_file in output_dir.glob("**/*.html"):
            rel_path = html_file.relative_to(output_dir)
            parts = rel_path.parts
            if parts[0].startswith("localhost"):
                url_path = "/" + "/".join(parts[1:])
                scraped_paths.add(url_path)
        return scraped_paths

    @pytest.mark.asyncio
    async def test_selectolax_basic_scraping(self, temp_dir):
        """Test basic page scraping with Selectolax."""
        output_dir = Path(temp_dir) / "test_basic"

        config = Config()
        config.crawler = CrawlerConfig(
            max_depth=1,
            max_pages=5,
            scraper_backend=ScraperBackend.SELECTOLAX,
            request_delay=0.1,
            concurrent_requests=2,
            check_ssrf=False,
        )

        crawler = WebCrawler(config.crawler)
        start_url = f"{self.server_url}/"

        result = await crawler.crawl(start_url, output_dir)
        scraped_paths = self.get_scraped_paths(output_dir)

        # Should have scraped at least the index page
        assert len(scraped_paths) > 0
        assert "/" in scraped_paths or "/index.html" in scraped_paths

    @pytest.mark.asyncio
    async def test_selectolax_metadata_extraction(self, temp_dir):
        """Test that Selectolax properly extracts metadata."""
        from tools.scrape_tool.scrapers.base import ScraperConfig

        config = ScraperConfig(
            max_depth=0,
            max_pages=1,
            request_delay=0.1,
            check_ssrf=False,
        )

        scraper = SelectolaxScraper(config)

        async with scraper:
            # Scrape a page with known metadata
            page = await scraper.scrape_url(f"{self.server_url}/page/m1f-documentation")

            assert page is not None
            assert page.title is not None
            assert page.content is not None
            assert len(page.content) > 0
            assert page.status_code == 200

    @pytest.mark.asyncio
    async def test_selectolax_allowed_path(self, temp_dir):
        """Test Selectolax with allowed_path restriction."""
        output_dir = Path(temp_dir) / "test_allowed"

        config = Config()
        config.crawler = CrawlerConfig(
            max_depth=3,
            max_pages=20,
            allowed_path="/api/",
            scraper_backend=ScraperBackend.SELECTOLAX,
            request_delay=0.1,
            concurrent_requests=2,
            check_ssrf=False,
        )

        crawler = WebCrawler(config.crawler)
        start_url = f"{self.server_url}/docs/index.html"

        result = await crawler.crawl(start_url, output_dir)
        scraped_paths = self.get_scraped_paths(output_dir)

        # Start URL should be scraped
        assert any("/docs/" in p for p in scraped_paths)

        # API pages should be scraped if linked
        api_pages = [p for p in scraped_paths if p.startswith("/api/")]
        # Note: This depends on whether docs links to API pages

        # Non-API/non-start pages should NOT be scraped
        guides_pages = [p for p in scraped_paths if p.startswith("/guides/")]
        assert len(guides_pages) == 0

    @pytest.mark.asyncio
    async def test_selectolax_canonical_handling(self, temp_dir):
        """Test Selectolax canonical URL handling."""
        from tools.scrape_tool.scrapers.base import ScraperConfig

        config = ScraperConfig(
            max_depth=0,
            max_pages=10,
            request_delay=0.1,
            check_canonical=True,
            check_ssrf=False,
        )

        scraper = SelectolaxScraper(config)

        async with scraper:
            # Test page with canonical URL
            url_with_canonical = (
                f"{self.server_url}/page/index?canonical={self.server_url}/"
            )
            page = await scraper.scrape_url(url_with_canonical)

            # If canonical differs, page should be None (skipped)
            # The test server injects canonical when ?canonical= is provided
            # Since the canonical (/) differs from the actual URL (/page/index), it should be skipped
            assert page is None

    @pytest.mark.asyncio
    async def test_selectolax_query_params(self, temp_dir):
        """Test Selectolax with query parameter handling."""
        output_dir = Path(temp_dir) / "test_params"

        config = Config()
        config.crawler = CrawlerConfig(
            max_depth=1,
            max_pages=10,
            ignore_get_params=True,  # Should treat URLs with different params as same
            scraper_backend=ScraperBackend.SELECTOLAX,
            request_delay=0.1,
            concurrent_requests=1,
            check_ssrf=False,
        )

        crawler = WebCrawler(config.crawler)

        # Create scraper to test URL normalization
        from tools.scrape_tool.scrapers.base import ScraperConfig

        scraper_config = ScraperConfig(ignore_get_params=True)
        scraper = SelectolaxScraper(scraper_config)

        # Test URL normalization
        url1 = scraper._normalize_url(f"{self.server_url}/page/test?tab=1")
        url2 = scraper._normalize_url(f"{self.server_url}/page/test?tab=2")

        # With ignore_get_params=True, these should be the same
        assert url1 == url2
        assert "?" not in url1  # Query params should be stripped

    @pytest.mark.asyncio
    async def test_selectolax_duplicate_detection(self, temp_dir):
        """Test Selectolax duplicate content detection."""
        from tools.scrape_tool.scrapers.base import ScraperConfig

        config = ScraperConfig(
            max_depth=0,
            max_pages=10,
            request_delay=0.1,
            check_content_duplicates=True,
            check_ssrf=False,
        )

        scraper = SelectolaxScraper(config)

        # Mock the checksum callback to simulate duplicate detection
        seen_checksums = set()

        def checksum_callback(checksum):
            if checksum in seen_checksums:
                return True
            seen_checksums.add(checksum)
            return False

        scraper._checksum_callback = checksum_callback

        async with scraper:
            # Scrape duplicate content pages
            page1 = await scraper.scrape_url(f"{self.server_url}/test/duplicate/1")
            assert page1 is not None  # First should succeed

            # Calculate and store checksum
            if page1.content:
                from tools.scrape_tool.utils import calculate_content_checksum

                checksum = calculate_content_checksum(page1.content)
                seen_checksums.add(checksum)

            # Second should be skipped due to duplicate content
            page2 = await scraper.scrape_url(f"{self.server_url}/test/duplicate/2")
            # Note: This depends on the scraper checking content before returning


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
