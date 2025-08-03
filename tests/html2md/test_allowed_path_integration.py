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

"""Integration tests for the allowed_path feature using the test server."""

import asyncio
import pytest
import tempfile
import shutil
import subprocess
import time
import os
import signal
import requests
from pathlib import Path
from typing import List, Set

from tools.scrape_tool.config import Config, CrawlerConfig, ScraperBackend
from tools.scrape_tool.crawlers import WebCrawler


class TestAllowedPathIntegration:
    """Integration tests for allowed_path parameter with real server."""

    @classmethod
    def setup_class(cls):
        """Start the test server before running tests."""
        # Set environment variable to suppress server output
        env = os.environ.copy()
        env["FLASK_ENV"] = "testing"

        # Start the test server
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
            # Read server output for debugging
            if cls.server_process:
                stdout, stderr = cls.server_process.communicate(timeout=1)
                print(f"Server stdout: {stdout.decode()}")
                print(f"Server stderr: {stderr.decode()}")
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

    def get_scraped_paths(self, output_dir: Path) -> Set[str]:
        """Extract the URL paths from scraped files."""
        scraped_paths = set()

        # Find all HTML files in the output directory
        for html_file in output_dir.glob("**/*.html"):
            # Convert file path back to URL path
            rel_path = html_file.relative_to(output_dir)

            # Handle the domain directory structure (localhost:8080/...)
            parts = rel_path.parts
            if parts[0].startswith("localhost"):
                # Remove domain part and reconstruct path
                url_path = "/" + "/".join(parts[1:])
                # Add the path as is (with .html)
                scraped_paths.add(url_path)

        return scraped_paths

    @pytest.mark.asyncio
    async def test_allowed_path_restricts_crawling(self, temp_dir):
        """Test that allowed_path properly restricts crawling to specified path."""
        output_dir = Path(temp_dir) / "test_restricted"

        # Create config with allowed_path set to /api/
        config = Config()
        config.crawler = CrawlerConfig(
            max_depth=3,
            max_pages=20,
            allowed_path="/api/",
            scraper_backend=ScraperBackend.BEAUTIFULSOUP,
            request_delay=0.1,
            concurrent_requests=2,
            check_ssrf=False,  # Disable SSRF check for localhost testing
        )

        # Create crawler
        crawler = WebCrawler(config.crawler)

        # Start from docs index but restrict to /api/
        start_url = "http://localhost:8080/docs/index.html"

        # Run the crawl
        result = await crawler.crawl(start_url, output_dir)

        # Get scraped paths
        scraped_paths = self.get_scraped_paths(output_dir)

        # The start URL should always be scraped
        assert "/docs/index.html" in scraped_paths or "/docs/" in scraped_paths

        # API pages should be scraped
        api_pages = [p for p in scraped_paths if p.startswith("/api/")]
        assert len(api_pages) > 0, f"No API pages found. Scraped: {scraped_paths}"

        # Should have scraped specific API pages
        expected_api_pages = {
            "/api/overview.html",
            "/api/endpoints.html",
            "/api/authentication.html",
        }
        for page in expected_api_pages:
            assert any(
                page in p or page.rstrip(".html") in p for p in scraped_paths
            ), f"Expected {page} not found. Scraped: {scraped_paths}"

        # Non-API pages (except start URL) should NOT be scraped
        non_api_pages = [
            p
            for p in scraped_paths
            if not p.startswith("/api/") and not p.startswith("/docs/")
        ]
        assert (
            len(non_api_pages) == 0
        ), f"Found non-API pages that shouldn't be scraped: {non_api_pages}"

        # Guides should NOT be scraped
        guides_pages = [p for p in scraped_paths if p.startswith("/guides/")]
        assert (
            len(guides_pages) == 0
        ), f"Found guides pages that shouldn't be scraped: {guides_pages}"

    @pytest.mark.asyncio
    async def test_without_allowed_path_uses_start_url_path(self, temp_dir):
        """Test that without allowed_path, it restricts to the start URL's path."""
        output_dir = Path(temp_dir) / "test_default"

        # Create config WITHOUT allowed_path
        config = Config()
        config.crawler = CrawlerConfig(
            max_depth=3,
            max_pages=20,
            scraper_backend=ScraperBackend.BEAUTIFULSOUP,
            request_delay=0.1,
            concurrent_requests=2,
            check_ssrf=False,  # Disable SSRF check for localhost testing
        )

        # Create crawler
        crawler = WebCrawler(config.crawler)

        # Start from /api/overview.html
        start_url = "http://localhost:8080/api/overview.html"

        # Run the crawl
        result = await crawler.crawl(start_url, output_dir)

        # Get scraped paths
        scraped_paths = self.get_scraped_paths(output_dir)

        # Should have scraped API pages
        api_pages = [p for p in scraped_paths if p.startswith("/api/")]
        assert len(api_pages) > 0, f"No API pages found. Scraped: {scraped_paths}"

        # Should NOT have scraped pages outside /api/
        non_api_pages = [p for p in scraped_paths if not p.startswith("/api/")]
        assert (
            len(non_api_pages) == 0
        ), f"Found non-API pages that shouldn't be scraped: {non_api_pages}"

    @pytest.mark.asyncio
    async def test_allowed_path_with_root(self, temp_dir):
        """Test allowed_path with root path allows all pages."""
        output_dir = Path(temp_dir) / "test_root"

        # Create config with allowed_path set to root
        config = Config()
        config.crawler = CrawlerConfig(
            max_depth=2,
            max_pages=20,
            allowed_path="/",
            scraper_backend=ScraperBackend.BEAUTIFULSOUP,
            request_delay=0.1,
            concurrent_requests=2,
            check_ssrf=False,  # Disable SSRF check for localhost testing
        )

        # Create crawler
        crawler = WebCrawler(config.crawler)

        # Start from docs index
        start_url = "http://localhost:8080/docs/index.html"

        # Run the crawl
        result = await crawler.crawl(start_url, output_dir)

        # Get scraped paths
        scraped_paths = self.get_scraped_paths(output_dir)

        # Should have scraped pages from multiple directories
        has_api = any(p.startswith("/api/") for p in scraped_paths)
        has_docs = any(p.startswith("/docs/") for p in scraped_paths)
        has_guides = any(p.startswith("/guides/") for p in scraped_paths)

        assert (
            has_api or has_docs or has_guides
        ), f"Should have scraped from multiple directories. Scraped: {scraped_paths}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
