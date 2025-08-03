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

"""Tests for web scraper backends."""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from tools.scrape_tool.scrapers import create_scraper, ScraperConfig, SCRAPER_REGISTRY
from tools.scrape_tool.scrapers.base import ScrapedPage
from tools.scrape_tool.scrapers.beautifulsoup import BeautifulSoupScraper
from tools.scrape_tool.scrapers.httrack import HTTrackScraper

# Import new scrapers conditionally
try:
    from tools.scrape_tool.scrapers.selectolax import SelectolaxScraper

    SELECTOLAX_AVAILABLE = True
except ImportError:
    SELECTOLAX_AVAILABLE = False


try:
    from tools.scrape_tool.scrapers.playwright import PlaywrightScraper

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class TestScraperFactory:
    """Test scraper factory function."""

    def test_create_beautifulsoup_scraper(self):
        """Test creating BeautifulSoup scraper."""
        config = ScraperConfig()
        scraper = create_scraper("beautifulsoup", config)
        assert isinstance(scraper, BeautifulSoupScraper)

    def test_create_bs4_scraper_alias(self):
        """Test creating BeautifulSoup scraper with bs4 alias."""
        config = ScraperConfig()
        scraper = create_scraper("bs4", config)
        assert isinstance(scraper, BeautifulSoupScraper)

    def test_create_httrack_scraper(self):
        """Test creating HTTrack scraper."""
        config = ScraperConfig()
        with patch("shutil.which", return_value="/usr/bin/httrack"):
            scraper = create_scraper("httrack", config)
            assert isinstance(scraper, HTTrackScraper)

    def test_create_unknown_scraper_raises_error(self):
        """Test creating unknown scraper raises ValueError."""
        config = ScraperConfig()
        with pytest.raises(ValueError, match="Unknown scraper backend: unknown"):
            create_scraper("unknown", config)

    def test_scraper_registry(self):
        """Test scraper registry contains expected backends."""
        assert "beautifulsoup" in SCRAPER_REGISTRY
        assert "bs4" in SCRAPER_REGISTRY
        assert "httrack" in SCRAPER_REGISTRY

        # Check optional scrapers if available
        if SELECTOLAX_AVAILABLE:
            assert "selectolax" in SCRAPER_REGISTRY
            assert "httpx" in SCRAPER_REGISTRY
        if PLAYWRIGHT_AVAILABLE:
            assert "playwright" in SCRAPER_REGISTRY


class TestScraperConfig:
    """Test ScraperConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ScraperConfig()
        assert config.max_depth == 10
        assert config.max_pages == 10000
        assert config.respect_robots_txt is True
        assert config.concurrent_requests == 5
        assert config.request_delay == 0.5
        assert "Chrome" in config.user_agent
        assert config.timeout == 30.0
        assert config.follow_redirects is True
        assert config.verify_ssl is True

    def test_custom_config(self):
        """Test custom configuration values."""
        config = ScraperConfig(
            max_depth=5,
            max_pages=100,
            respect_robots_txt=False,
            user_agent="TestBot/1.0",
        )
        assert config.max_depth == 5
        assert config.max_pages == 100
        assert config.respect_robots_txt is False
        assert config.user_agent == "TestBot/1.0"


class TestBeautifulSoupScraper:
    """Test BeautifulSoup scraper implementation."""

    @pytest.fixture
    def scraper(self):
        """Create scraper instance."""
        config = ScraperConfig(max_depth=2, max_pages=10, request_delay=0.1)
        return BeautifulSoupScraper(config)

    @pytest.mark.asyncio
    async def test_scrape_url(self, scraper):
        """Test scraping a single URL."""
        test_html = """
        <html>
        <head>
            <title>Test Page</title>
            <meta name="description" content="Test description">
        </head>
        <body>
            <h1>Test Content</h1>
            <a href="/page2">Link</a>
        </body>
        </html>
        """

        # Mock aiohttp response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.charset = "utf-8"
        mock_response.read = AsyncMock(return_value=test_html.encode("utf-8"))
        mock_response.url = "https://example.com/test"

        # Mock session
        mock_session = AsyncMock()
        # Create a proper async context manager mock
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = Mock(return_value=mock_context)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            scraper.session = mock_session
            page = await scraper.scrape_url("https://example.com/test")

            assert isinstance(page, ScrapedPage)
            assert page.url == "https://example.com/test"
            assert page.title == "Test Page"
            assert "Test Content" in page.content
            assert page.metadata["description"] == "Test description"
            assert page.encoding == "utf-8"
            assert page.status_code == 200

    @pytest.mark.asyncio
    async def test_validate_url(self, scraper):
        """Test URL validation."""
        # Valid URLs
        assert await scraper.validate_url("https://example.com") is True
        assert await scraper.validate_url("http://example.com/page") is True

        # Invalid URLs
        assert await scraper.validate_url("ftp://example.com") is False
        assert await scraper.validate_url("javascript:alert()") is False
        assert await scraper.validate_url("mailto:test@example.com") is False

    @pytest.mark.asyncio
    async def test_validate_url_with_allowed_domains(self, scraper):
        """Test URL validation with allowed domains."""
        scraper.config.allowed_domains = ["example.com", "test.com"]

        assert await scraper.validate_url("https://example.com/page") is True
        assert await scraper.validate_url("https://test.com/page") is True
        assert await scraper.validate_url("https://other.com/page") is False

    @pytest.mark.asyncio
    async def test_validate_url_with_exclude_patterns(self, scraper):
        """Test URL validation with exclude patterns."""
        scraper.config.exclude_patterns = ["/admin/", ".pdf", "private"]

        assert await scraper.validate_url("https://example.com/page") is True
        assert await scraper.validate_url("https://example.com/admin/page") is False
        assert await scraper.validate_url("https://example.com/file.pdf") is False
        assert await scraper.validate_url("https://example.com/private/data") is False


class TestHTTrackScraper:
    """Test HTTrack scraper implementation."""

    @pytest.fixture
    def scraper(self):
        """Create scraper instance."""
        config = ScraperConfig(max_depth=2, max_pages=10)
        with patch("shutil.which", return_value="/usr/bin/httrack"):
            return HTTrackScraper(config)

    def test_httrack_not_installed(self):
        """Test fallback when HTTrack is not installed."""
        config = ScraperConfig()
        with patch("shutil.which", return_value=None):
            # Should not raise error, but use Python fallback
            scraper = HTTrackScraper(config)
            assert not scraper.use_httrack  # Should use fallback

    @pytest.mark.asyncio
    async def test_scrape_url(self, scraper, tmp_path):
        """Test scraping single URL with HTTrack."""
        test_html = "<html><head><title>Test</title></head><body>Content</body></html>"

        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"", b""))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with patch("tempfile.mkdtemp", return_value=str(tmp_path)):
                # Create expected output file after HTTrack mock is called
                # Use the actual hash calculation to match the scraper's logic
                url_hash = str(hash("https://example.com"))[-8:]
                output_dir = tmp_path / f"single_{url_hash}" / "example.com"
                output_dir.mkdir(parents=True)
                output_file = output_dir / "index.html"
                output_file.write_text(test_html)

                async with scraper:
                    page = await scraper.scrape_url("https://example.com")

                    assert isinstance(page, ScrapedPage)
                    assert page.url == "https://example.com"
                    assert page.title == "Test"
                    assert "Content" in page.content


@pytest.mark.asyncio
async def test_scraper_context_manager():
    """Test scraper async context manager."""
    config = ScraperConfig()
    scraper = BeautifulSoupScraper(config)

    assert scraper.session is None

    async with scraper:
        assert scraper.session is not None

    # Session should be closed after exiting context
    await asyncio.sleep(0.2)  # Allow time for cleanup


@pytest.mark.skipif(not SELECTOLAX_AVAILABLE, reason="selectolax not installed")
class TestSelectolaxScraper:
    """Test Selectolax scraper implementation."""

    @pytest.fixture
    def scraper(self):
        """Create scraper instance."""
        config = ScraperConfig(
            max_depth=2, max_pages=10, request_delay=0.1, concurrent_requests=10
        )
        return SelectolaxScraper(config)

    @pytest.mark.asyncio
    async def test_scrape_url(self, scraper):
        """Test scraping a single URL."""
        test_html = """
        <html>
        <head>
            <title>Test Page</title>
            <meta name="description" content="Test description">
            <meta property="og:title" content="OG Test Title">
        </head>
        <body>
            <h1>Test Content</h1>
            <a href="/page2">Link</a>
        </body>
        </html>
        """

        # Mock httpx response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.encoding = "utf-8"
        mock_response.text = test_html
        mock_response.url = "https://example.com/test"
        mock_response.raise_for_status = Mock()

        # Mock client
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            async with scraper:
                scraper._client = mock_client
                page = await scraper.scrape_url("https://example.com/test")

                assert isinstance(page, ScrapedPage)
                assert page.url == "https://example.com/test"
                assert page.title == "Test Page"
                assert "Test Content" in page.content
                assert page.metadata["description"] == "Test description"
                assert page.metadata["og:title"] == "OG Test Title"
                assert page.encoding == "utf-8"
                assert page.status_code == 200

    def test_httpx_not_available(self):
        """Test error when httpx/selectolax not installed."""
        config = ScraperConfig()
        with patch("tools.scrape_tool.scrapers.selectolax.HTTPX_AVAILABLE", False):
            with pytest.raises(ImportError, match="httpx and selectolax are required"):
                SelectolaxScraper(config)


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="playwright not installed")
class TestPlaywrightScraper:
    """Test Playwright scraper implementation."""

    @pytest.fixture
    def scraper(self):
        """Create scraper instance."""
        config = ScraperConfig(
            max_depth=2, max_pages=10, request_delay=1.0, concurrent_requests=2
        )
        # Add browser config to __dict__
        config.__dict__["browser_config"] = {
            "browser": "chromium",
            "headless": True,
            "viewport": {"width": 1920, "height": 1080},
        }
        return PlaywrightScraper(config)

    def test_playwright_not_available(self):
        """Test error when playwright not installed."""
        config = ScraperConfig()
        with patch("tools.scrape_tool.scrapers.playwright.PLAYWRIGHT_AVAILABLE", False):
            with pytest.raises(ImportError, match="playwright is required"):
                PlaywrightScraper(config)

    @pytest.mark.asyncio
    async def test_scrape_url(self, scraper):
        """Test scraping a single URL with Playwright."""
        test_html = """
        <html>
        <head>
            <title>Test Page</title>
            <meta name="description" content="Test description">
        </head>
        <body>
            <h1>Test Content</h1>
            <a href="/page2">Link</a>
        </body>
        </html>
        """

        # Mock page object
        mock_page = AsyncMock()
        mock_page.url = "https://example.com/test"
        mock_page.title = AsyncMock(return_value="Test Page")
        mock_page.content = AsyncMock(return_value=test_html)
        mock_page.evaluate = AsyncMock(
            return_value={
                "description": "Test description",
                "canonical": "https://example.com/test",
            }
        )
        mock_page.close = AsyncMock()

        # Mock response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "text/html"}

        mock_page.goto = AsyncMock(return_value=mock_response)

        # Mock context
        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.set_default_timeout = Mock()

        # Mock browser
        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)

        # Mock playwright
        mock_chromium = AsyncMock()
        mock_chromium.launch = AsyncMock(return_value=mock_browser)

        mock_playwright_instance = Mock()
        mock_playwright_instance.chromium = mock_chromium
        mock_playwright_instance.stop = AsyncMock()

        mock_playwright = AsyncMock()
        mock_playwright.start = AsyncMock(return_value=mock_playwright_instance)

        with patch(
            "playwright.async_api.async_playwright", return_value=mock_playwright
        ):
            async with scraper:
                scraper._context = mock_context
                page = await scraper.scrape_url("https://example.com/test")

                assert isinstance(page, ScrapedPage)
                assert page.url == "https://example.com/test"
                assert page.title == "Test Page"
                assert "Test Content" in page.content
                assert page.metadata["description"] == "Test description"


class TestNewScraperRegistry:
    """Test that new scrapers are properly registered."""

    @pytest.mark.skipif(not SELECTOLAX_AVAILABLE, reason="selectolax not installed")
    def test_selectolax_in_registry(self):
        """Test selectolax scraper is in registry."""
        assert "selectolax" in SCRAPER_REGISTRY
        assert "httpx" in SCRAPER_REGISTRY  # Alias
        assert SCRAPER_REGISTRY["selectolax"] == SelectolaxScraper
        assert SCRAPER_REGISTRY["httpx"] == SelectolaxScraper

    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="playwright not installed")
    def test_playwright_in_registry(self):
        """Test playwright scraper is in registry."""
        assert "playwright" in SCRAPER_REGISTRY
        assert SCRAPER_REGISTRY["playwright"] == PlaywrightScraper

    @pytest.mark.skipif(not SELECTOLAX_AVAILABLE, reason="selectolax not installed")
    def test_create_selectolax_scraper(self):
        """Test creating selectolax scraper via factory."""
        config = ScraperConfig()
        scraper = create_scraper("selectolax", config)
        assert isinstance(scraper, SelectolaxScraper)

    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="playwright not installed")
    def test_create_playwright_scraper(self):
        """Test creating playwright scraper via factory."""
        config = ScraperConfig()
        scraper = create_scraper("playwright", config)
        assert isinstance(scraper, PlaywrightScraper)
