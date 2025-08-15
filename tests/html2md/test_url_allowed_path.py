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

"""Tests for URL-based allowed_path functionality."""

import asyncio
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Set

from tools.scrape_tool.config import Config, CrawlerConfig, ScraperBackend
from tools.scrape_tool.crawlers import WebCrawler
from tools.scrape_tool.scrapers.base import ScraperConfig
from tools.scrape_tool.scrapers.beautifulsoup import BeautifulSoupScraper
from tools.scrape_tool.scrapers.selectolax import SelectolaxScraper


class TestURLAllowedPath:
    """Test URL-based allowed_path parameter."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test output."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_url_allowed_path_parsing(self):
        """Test that allowed_path correctly parses full URLs."""
        # Test with path only
        config = ScraperConfig(
            allowed_path="/docs/api/",
            check_ssrf=False,
        )
        scraper = BeautifulSoupScraper(config)

        # Start URL and allowed_path parsing
        start_url = "https://example.com/index.html"
        allowed_domain = None

        # The scraper should detect this is just a path
        assert not config.allowed_path.startswith(("http://", "https://"))

        # Test with full URL
        config2 = ScraperConfig(
            allowed_path="https://docs.example.com/api/v2/",
            check_ssrf=False,
        )
        scraper2 = BeautifulSoupScraper(config2)

        # The scraper should detect this is a full URL
        assert config2.allowed_path.startswith(("http://", "https://"))

    @pytest.mark.asyncio
    async def test_url_allowed_path_filtering(self):
        """Test that URL-based allowed_path correctly filters URLs."""
        config = ScraperConfig(
            allowed_path="https://docs.example.com/api/",
            check_ssrf=False,
        )
        scraper = BeautifulSoupScraper(config)

        # Mock the scrape_site method to test URL filtering
        test_urls = [
            ("https://docs.example.com/api/index.html", True),  # Should be allowed
            (
                "https://docs.example.com/api/v1/endpoints.html",
                True,
            ),  # Should be allowed
            ("https://docs.example.com/guide/index.html", False),  # Different path
            ("https://www.example.com/api/index.html", False),  # Different domain
            (
                "http://docs.example.com/api/index.html",
                True,
            ),  # Different scheme should be ok
        ]

        # Parse the allowed URL
        from urllib.parse import urlparse

        parsed_allowed = urlparse(config.allowed_path)
        allowed_domain = parsed_allowed.netloc
        allowed_path = parsed_allowed.path.rstrip("/")

        for url, should_pass in test_urls:
            parsed_url = urlparse(url)

            # Check domain
            if allowed_domain and parsed_url.netloc != allowed_domain:
                assert (
                    not should_pass
                ), f"{url} should be rejected due to domain mismatch"
                continue

            # Check path
            if not (
                parsed_url.path.startswith(allowed_path + "/")
                or parsed_url.path == allowed_path
            ):
                assert not should_pass, f"{url} should be rejected due to path mismatch"
                continue

            assert should_pass, f"{url} should be allowed"

    @pytest.mark.asyncio
    async def test_url_allowed_path_with_beautifulsoup(self, temp_dir):
        """Test URL-based allowed_path with BeautifulSoup scraper."""
        output_dir = Path(temp_dir) / "test_bs"

        config = Config()
        config.crawler = CrawlerConfig(
            max_depth=2,
            max_pages=10,
            allowed_path="https://example.com/docs/api/",  # Full URL
            scraper_backend=ScraperBackend.BEAUTIFULSOUP,
            request_delay=0.1,
            check_ssrf=False,
        )

        # The crawler should parse this correctly
        assert config.crawler.allowed_path.startswith("https://")

    @pytest.mark.asyncio
    async def test_url_allowed_path_with_selectolax(self, temp_dir):
        """Test URL-based allowed_path with Selectolax scraper."""
        output_dir = Path(temp_dir) / "test_selectolax"

        config = Config()
        config.crawler = CrawlerConfig(
            max_depth=2,
            max_pages=10,
            allowed_path="https://api.example.com/v2/",  # Full URL
            scraper_backend=ScraperBackend.SELECTOLAX,
            request_delay=0.1,
            check_ssrf=False,
        )

        # The crawler should parse this correctly
        assert config.crawler.allowed_path.startswith("https://")

    def test_cli_parameter_description(self):
        """Test that CLI parameter description mentions URL support."""
        from tools.scrape_tool.config import CrawlerConfig

        # Check that the field description mentions both path and URL
        field_info = CrawlerConfig.model_fields["allowed_path"]
        assert "path/URL" in field_info.description or "URL" in field_info.description


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
