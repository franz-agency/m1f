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

"""Test the multiple allowed paths feature for web scrapers."""

import asyncio
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import aiohttp
from urllib.parse import urljoin

from tools.scrape_tool.scrapers.base import ScraperConfig
from tools.scrape_tool.scrapers.beautifulsoup import BeautifulSoupScraper
from tools.scrape_tool.scrapers.selectolax import SelectolaxScraper
from tools.scrape_tool.crawlers import WebCrawler
from tools.scrape_tool.config import CrawlerConfig, ScraperBackend


# Check if selectolax is available
try:
    import selectolax
    SELECTOLAX_AVAILABLE = True
except ImportError:
    SELECTOLAX_AVAILABLE = False


class TestMultipleAllowedPathsFeature:
    """Test the multiple allowed paths parameter functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test output."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_html_responses(self):
        """Mock HTML responses for testing multiple paths."""
        return {
            "http://example.com/docs/index.html": """
                <html>
                <body>
                    <h1>Documentation Index</h1>
                    <a href="/docs/guide.html">Guide</a>
                    <a href="/api/overview.html">API Docs</a>
                    <a href="/api/endpoints.html">API Endpoints</a>
                    <a href="/guides/start.html">Getting Started</a>
                    <a href="/blog/news.html">Blog</a>
                    <a href="/admin/settings.html">Admin</a>
                </body>
                </html>
            """,
            "http://example.com/docs/guide.html": """
                <html>
                <body>
                    <h1>Guide</h1>
                    <p>Documentation guide content</p>
                    <a href="/docs/advanced.html">Advanced Guide</a>
                </body>
                </html>
            """,
            "http://example.com/docs/advanced.html": """
                <html>
                <body>
                    <h1>Advanced Guide</h1>
                    <p>Advanced documentation content</p>
                </body>
                </html>
            """,
            "http://example.com/api/overview.html": """
                <html>
                <body>
                    <h1>API Overview</h1>
                    <a href="/api/endpoints.html">Endpoints</a>
                    <a href="/api/auth.html">Authentication</a>
                </body>
                </html>
            """,
            "http://example.com/api/endpoints.html": """
                <html>
                <body>
                    <h1>API Endpoints</h1>
                    <p>List of endpoints</p>
                </body>
                </html>
            """,
            "http://example.com/api/auth.html": """
                <html>
                <body>
                    <h1>Authentication</h1>
                    <p>How to authenticate</p>
                </body>
                </html>
            """,
            "http://example.com/guides/start.html": """
                <html>
                <body>
                    <h1>Getting Started</h1>
                    <p>Should not be scraped when restricting to /docs/ and /api/</p>
                </body>
                </html>
            """,
            "http://example.com/blog/news.html": """
                <html>
                <body>
                    <h1>Blog News</h1>
                    <p>Should not be scraped</p>
                </body>
                </html>
            """,
            "http://example.com/admin/settings.html": """
                <html>
                <body>
                    <h1>Admin Settings</h1>
                    <p>Should not be scraped</p>
                </body>
                </html>
            """,
        }

    @pytest.mark.asyncio
    async def test_beautifulsoup_multiple_allowed_paths(self, mock_html_responses, temp_dir):
        """Test BeautifulSoup scraper with multiple allowed paths."""
        # Create config with multiple allowed paths
        config = ScraperConfig(
            max_pages=20, max_depth=3, allowed_paths=["/docs/", "/api/"], request_delay=0.1
        )

        scraper = BeautifulSoupScraper(config)

        # Mock the aiohttp response object properly
        def create_mock_response(url):
            response = AsyncMock()
            response.status = 200
            response.url = url
            response.charset = "utf-8"
            response.headers = {"content-type": "text/html"}

            # Get the HTML content
            html_content = mock_html_responses.get(url, "<html><body>404</body></html>")
            content_bytes = html_content.encode("utf-8")

            # Mock the read() method to return bytes
            response.read = AsyncMock(return_value=content_bytes)

            # Set up async context manager
            response.__aenter__ = AsyncMock(return_value=response)
            response.__aexit__ = AsyncMock(return_value=None)

            return response

        # Mock session.get to return our mock response
        mock_session = AsyncMock()
        mock_session.get = lambda url, **kwargs: create_mock_response(url)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.closed = False

        # Collect scraped URLs
        scraped_urls = []

        # Patch aiohttp.ClientSession to return our mock session
        with patch("aiohttp.ClientSession", return_value=mock_session):
            # Mock robots.txt check to always allow
            with patch.object(scraper, "can_fetch", return_value=True):
                async with scraper:
                    async for page in scraper.scrape_site("http://example.com/docs/index.html"):
                        scraped_urls.append(page.url)

        # Check that we scraped the start URL (always allowed)
        assert "http://example.com/docs/index.html" in scraped_urls

        # Check that we scraped pages under /docs/
        assert "http://example.com/docs/guide.html" in scraped_urls
        assert "http://example.com/docs/advanced.html" in scraped_urls

        # Check that we scraped pages under /api/
        assert "http://example.com/api/overview.html" in scraped_urls
        assert "http://example.com/api/endpoints.html" in scraped_urls
        assert "http://example.com/api/auth.html" in scraped_urls

        # Check that we did NOT scrape pages outside /docs/ and /api/
        assert "http://example.com/guides/start.html" not in scraped_urls
        assert "http://example.com/blog/news.html" not in scraped_urls
        assert "http://example.com/admin/settings.html" not in scraped_urls

    @pytest.mark.asyncio
    async def test_beautifulsoup_empty_allowed_paths(self, mock_html_responses, temp_dir):
        """Test BeautifulSoup scraper with empty allowed_paths list."""
        # Create config with empty allowed paths (should fall back to start URL path)
        config = ScraperConfig(
            max_pages=20, max_depth=3, allowed_paths=[], request_delay=0.1
        )

        scraper = BeautifulSoupScraper(config)

        # Mock the aiohttp response object properly
        def create_mock_response(url):
            response = AsyncMock()
            response.status = 200
            response.url = url
            response.charset = "utf-8"
            response.headers = {"content-type": "text/html"}

            # Get the HTML content
            html_content = mock_html_responses.get(url, "<html><body>404</body></html>")
            content_bytes = html_content.encode("utf-8")

            # Mock the read() method to return bytes
            response.read = AsyncMock(return_value=content_bytes)

            # Set up async context manager
            response.__aenter__ = AsyncMock(return_value=response)
            response.__aexit__ = AsyncMock(return_value=None)

            return response

        # Mock session.get to return our mock response
        mock_session = AsyncMock()
        mock_session.get = lambda url, **kwargs: create_mock_response(url)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.closed = False

        # Collect scraped URLs
        scraped_urls = []

        # Patch aiohttp.ClientSession to return our mock session
        with patch("aiohttp.ClientSession", return_value=mock_session):
            # Mock robots.txt check to always allow
            with patch.object(scraper, "can_fetch", return_value=True):
                async with scraper:
                    async for page in scraper.scrape_site("http://example.com/docs/index.html"):
                        scraped_urls.append(page.url)

        # Should fall back to using the start URL's path (/docs/)
        assert "http://example.com/docs/index.html" in scraped_urls
        assert "http://example.com/docs/guide.html" in scraped_urls
        assert "http://example.com/docs/advanced.html" in scraped_urls

        # Should NOT scrape pages outside /docs/
        assert "http://example.com/api/overview.html" not in scraped_urls
        assert "http://example.com/guides/start.html" not in scraped_urls

    @pytest.mark.asyncio
    @pytest.mark.skipif(not SELECTOLAX_AVAILABLE, reason="selectolax not installed")
    async def test_selectolax_multiple_allowed_paths(self, mock_html_responses, temp_dir):
        """Test Selectolax scraper with multiple allowed paths."""
        # Create config with multiple allowed paths
        config = ScraperConfig(
            max_pages=20, max_depth=3, allowed_paths=["/docs/", "/api/"], request_delay=0.1
        )

        scraper = SelectolaxScraper(config)

        # Mock httpx response object
        def create_mock_response(url):
            response = AsyncMock()
            response.status_code = 200
            response.url = url
            response.encoding = "utf-8"
            response.headers = {"content-type": "text/html"}

            # Get the HTML content as text (selectolax uses .text directly)
            response.text = mock_html_responses.get(url, "<html><body>404</body></html>")

            # Mock raise_for_status
            response.raise_for_status = Mock()

            return response

        # Mock httpx client
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=lambda url, **kwargs: create_mock_response(url)
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.aclose = AsyncMock()

        # Collect scraped URLs
        scraped_urls = []

        # Patch httpx.AsyncClient to return our mock client
        with patch("httpx.AsyncClient", return_value=mock_client):
            # Mock robots.txt check to always allow
            with patch.object(scraper, "can_fetch", return_value=True):
                async with scraper:
                    async for page in scraper.scrape_site("http://example.com/docs/index.html"):
                        scraped_urls.append(page.url)

        # Check that we scraped the start URL (always allowed)
        assert "http://example.com/docs/index.html" in scraped_urls

        # Check that we scraped pages under both /docs/ and /api/
        assert "http://example.com/docs/guide.html" in scraped_urls
        assert "http://example.com/docs/advanced.html" in scraped_urls
        assert "http://example.com/api/overview.html" in scraped_urls
        assert "http://example.com/api/endpoints.html" in scraped_urls
        assert "http://example.com/api/auth.html" in scraped_urls

        # Check that we did NOT scrape pages outside /docs/ and /api/
        assert "http://example.com/guides/start.html" not in scraped_urls
        assert "http://example.com/blog/news.html" not in scraped_urls
        assert "http://example.com/admin/settings.html" not in scraped_urls

    def test_crawler_config_multiple_allowed_paths(self):
        """Test that CrawlerConfig properly accepts allowed_paths."""
        config = CrawlerConfig(
            max_depth=5, max_pages=100, allowed_paths=["/docs/", "/api/", "/guides/"]
        )

        assert config.allowed_paths == ["/docs/", "/api/", "/guides/"]

        # Test that both fields can be None
        config2 = CrawlerConfig()
        assert config2.allowed_path is None
        assert config2.allowed_paths is None

    def test_base_scraper_url_allowed_multiple_paths(self):
        """Test that base scraper _is_url_allowed works with multiple paths."""
        from tools.scrape_tool.scrapers.base import WebScraperBase, ScraperConfig
        
        # Create a minimal concrete implementation for testing
        class TestScraper(WebScraperBase):
            async def scrape_url(self, url: str):
                pass
            async def scrape_site(self, start_url: str):
                pass

        config = ScraperConfig(allowed_paths=["/docs/", "/api/"])
        scraper = TestScraper(config)

        # URLs within allowed paths should be allowed
        assert scraper._is_url_allowed("http://example.com/docs/guide.html")
        assert scraper._is_url_allowed("http://example.com/api/endpoints.html")
        assert scraper._is_url_allowed("http://example.com/docs/")
        assert scraper._is_url_allowed("http://example.com/api/")

        # URLs outside allowed paths should be blocked
        assert not scraper._is_url_allowed("http://example.com/guides/start.html")
        assert not scraper._is_url_allowed("http://example.com/blog/news.html")
        assert not scraper._is_url_allowed("http://example.com/admin/settings.html")

    def test_base_scraper_backward_compatibility(self):
        """Test that base scraper still works with single allowed_path."""
        from tools.scrape_tool.scrapers.base import WebScraperBase, ScraperConfig
        
        # Create a minimal concrete implementation for testing
        class TestScraper(WebScraperBase):
            async def scrape_url(self, url: str):
                pass
            async def scrape_site(self, start_url: str):
                pass

        # Test with old single allowed_path
        config = ScraperConfig(allowed_path="/docs/")
        scraper = TestScraper(config)

        assert scraper._is_url_allowed("http://example.com/docs/guide.html")
        assert not scraper._is_url_allowed("http://example.com/api/endpoints.html")

        # Test with no path restrictions
        config = ScraperConfig()
        scraper = TestScraper(config)

        assert scraper._is_url_allowed("http://example.com/docs/guide.html")
        assert scraper._is_url_allowed("http://example.com/api/endpoints.html")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])