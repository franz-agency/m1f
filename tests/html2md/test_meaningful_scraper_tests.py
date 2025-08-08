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

"""Meaningful integration tests for m1f-scrape that test actual functionality."""

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
from tools.scrape_tool.scrapers.selectolax import SelectolaxScraper
from tools.scrape_tool.scrapers.beautifulsoup import BeautifulSoupScraper
from tools.scrape_tool.scrapers.base import ScraperConfig


class TestMeaningfulScraperFeatures:
    """Tests that verify actual scraper functionality, not just configuration."""

    @classmethod
    def setup_class(cls):
        """Start the test server before running tests."""
        env = os.environ.copy()
        env["FLASK_ENV"] = "testing"
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
        server_started = False
        for i in range(30):
            try:
                response = requests.get("http://localhost:8080/")
                if response.status_code == 200:
                    server_started = True
                    break
            except requests.ConnectionError:
                pass
            time.sleep(0.5)

        if not server_started:
            cls.teardown_class()
            pytest.fail("Test server failed to start")

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

    @pytest.mark.asyncio
    async def test_ignore_get_params_actually_works(self, temp_dir):
        """Test that --ignore-get-params actually deduplicates URLs with query params."""
        output_dir = Path(temp_dir) / "test_params"

        # Test WITH ignore_get_params=True
        config = ScraperConfig(
            max_depth=0,
            max_pages=10,
            ignore_get_params=True,
            request_delay=0.1,
            check_ssrf=False,
        )

        scraper = BeautifulSoupScraper(config)

        # URLs with different query params should normalize to same URL
        url1 = "http://localhost:8080/page/index?tab=1&view=list"
        url2 = "http://localhost:8080/page/index?tab=2&view=grid"

        normalized1 = scraper._normalize_url(url1)
        normalized2 = scraper._normalize_url(url2)

        # Key test: Both should normalize to same URL
        assert (
            normalized1 == normalized2
        ), "URLs with different query params should normalize to same URL"
        assert "?" not in normalized1, "Query params should be stripped"

        # Test actual scraping behavior
        async with scraper:
            # Mark first URL as visited
            scraper.mark_visited(normalized1)

            # Second URL should be considered already visited
            assert scraper.is_visited(
                normalized2
            ), "URL with different query params should be considered visited"

    @pytest.mark.asyncio
    async def test_canonical_url_with_allowed_path_real_behavior(self, temp_dir):
        """Test that canonical URL + allowed_path interaction actually works."""
        output_dir = Path(temp_dir) / "test_canonical_allowed"

        config = ScraperConfig(
            max_depth=0,
            max_pages=10,
            allowed_path="/page/",  # Restrict to /page/
            check_canonical=True,  # Check canonical URLs
            request_delay=0.1,
            check_ssrf=False,
        )

        scraper = BeautifulSoupScraper(config)

        async with scraper:
            # Test 1: Page in allowed_path with canonical outside should NOT be skipped
            url_in_allowed = "http://localhost:8080/page/m1f-documentation?canonical=http://localhost:8080/"
            page = await scraper.scrape_url(url_in_allowed)

            assert (
                page is not None
            ), "Page in allowed_path should be kept even if canonical points outside"

            # Test 2: Page in allowed_path with canonical also in allowed_path but different
            url_with_canonical_in_path = "http://localhost:8080/page/m1f-documentation?canonical=http://localhost:8080/page/html2md-documentation"
            page2 = await scraper.scrape_url(url_with_canonical_in_path)

            assert (
                page2 is None
            ), "Page should be skipped if canonical differs and both are in allowed_path"

    @pytest.mark.asyncio
    async def test_excluded_paths_actually_excludes(self, temp_dir):
        """Test that excluded_paths actually prevents scraping those paths."""
        output_dir = Path(temp_dir) / "test_excluded"

        config = Config()
        config.crawler = CrawlerConfig(
            max_depth=2,
            max_pages=50,
            excluded_paths=["/api/", "/guides/"],  # Exclude these
            scraper_backend=ScraperBackend.BEAUTIFULSOUP,
            request_delay=0.1,
            check_ssrf=False,
        )

        crawler = WebCrawler(config.crawler)
        start_url = "http://localhost:8080/"

        # Actually crawl the site
        await crawler.crawl(start_url, output_dir)

        # Check actual files created
        all_files = list(output_dir.glob("**/*.html"))

        # Verify NO files from excluded paths were saved
        for file in all_files:
            file_path = str(file.relative_to(output_dir))
            assert "/api/" not in file_path, f"Found excluded API file: {file_path}"
            assert (
                "/guides/" not in file_path
            ), f"Found excluded guides file: {file_path}"

        # Verify we did scrape some files (not everything was excluded)
        assert len(all_files) > 0, "Should have scraped some files"

    @pytest.mark.asyncio
    async def test_duplicate_content_detection_actually_works(self, temp_dir):
        """Test that duplicate content detection actually prevents saving duplicates."""
        output_dir = Path(temp_dir) / "test_duplicates"

        config = Config()
        config.crawler = CrawlerConfig(
            max_depth=1,
            max_pages=10,
            check_content_duplicates=True,  # Enable duplicate detection
            scraper_backend=ScraperBackend.BEAUTIFULSOUP,
            request_delay=0.1,
            check_ssrf=False,
        )

        crawler = WebCrawler(config.crawler)

        # The test server has /test/duplicate/1 and /test/duplicate/2 with identical content
        # We'll crawl from a page that links to both

        # First, let's manually test the duplicate detection
        scraper_config = ScraperConfig(
            max_depth=0,
            max_pages=10,
            check_content_duplicates=True,
            request_delay=0.1,
            check_ssrf=False,
        )
        scraper = BeautifulSoupScraper(scraper_config)

        async with scraper:
            # Scrape first duplicate page
            page1 = await scraper.scrape_url("http://localhost:8080/test/duplicate/1")
            assert page1 is not None, "First duplicate page should be scraped"

            # Simulate the checksum being stored (normally done by crawler)
            if page1.content:
                from tools.scrape_tool.utils import calculate_content_checksum

                checksum = calculate_content_checksum(page1.content)

                # Set up checksum callback to simulate database
                seen_checksums = {checksum}
                scraper._checksum_callback = lambda c: c in seen_checksums

            # Try to scrape second duplicate page
            page2 = await scraper.scrape_url("http://localhost:8080/test/duplicate/2")

            # This should be None because content is duplicate
            assert page2 is None, "Second page with duplicate content should be skipped"

    @pytest.mark.asyncio
    async def test_max_depth_unlimited_actually_works(self, temp_dir):
        """Test that max_depth=-1 actually allows unlimited depth."""
        output_dir = Path(temp_dir) / "test_unlimited_depth"

        config = Config()
        config.crawler = CrawlerConfig(
            max_depth=-1,  # Unlimited depth
            max_pages=5,  # But limit total pages
            scraper_backend=ScraperBackend.BEAUTIFULSOUP,
            request_delay=0.1,
            check_ssrf=False,
        )

        crawler = WebCrawler(config.crawler)
        start_url = "http://localhost:8080/"

        await crawler.crawl(start_url, output_dir)

        # Check that we scraped nested pages (depth > 1)
        all_files = list(output_dir.glob("**/*.html"))

        # Look for deeply nested paths
        has_deep_paths = False
        for file in all_files:
            parts = file.relative_to(output_dir).parts
            # If we have paths like localhost/api/endpoints.html, that's depth 2+
            if len(parts) >= 3:  # localhost:8080/category/page.html
                has_deep_paths = True
                break

        assert (
            has_deep_paths or len(all_files) >= 3
        ), "With unlimited depth, should scrape nested pages"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "scraper_backend",
        [
            ScraperBackend.BEAUTIFULSOUP,
            ScraperBackend.SELECTOLAX,
        ],
    )
    async def test_timeout_actually_enforced(self, temp_dir, scraper_backend):
        """Test that timeout parameter actually times out slow requests."""
        from tools.scrape_tool.scrapers.base import ScraperConfig

        config = ScraperConfig(
            max_depth=0,
            max_pages=1,
            timeout=2,  # 2 second timeout
            check_ssrf=False,
        )

        if scraper_backend == ScraperBackend.BEAUTIFULSOUP:
            from tools.scrape_tool.scrapers.beautifulsoup import BeautifulSoupScraper

            scraper = BeautifulSoupScraper(config)
        else:
            from tools.scrape_tool.scrapers.selectolax import SelectolaxScraper

            scraper = SelectolaxScraper(config)

        async with scraper:
            # Try to scrape slow endpoint that takes 10 seconds
            # This should timeout after 2 seconds
            start_time = time.time()

            try:
                page = await scraper.scrape_url(
                    "http://localhost:8080/test/slow?delay=10"
                )
                # If we get here, timeout didn't work
                elapsed = time.time() - start_time
                assert elapsed < 5, f"Request should have timed out but took {elapsed}s"
            except Exception as e:
                # Good, it timed out
                elapsed = time.time() - start_time
                assert elapsed < 5, f"Timeout took too long: {elapsed}s"
                # Check exception type name as well since some timeout exceptions have empty string representation
                exception_info = f"{type(e).__name__} {str(e)}".lower()
                assert "timeout" in exception_info or "timed out" in exception_info


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
