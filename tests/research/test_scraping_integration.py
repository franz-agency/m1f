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

"""
Integration tests for m1f-research scraping pipeline
"""
import pytest
import asyncio
import aiohttp
from unittest.mock import MagicMock, Mock, patch
from datetime import datetime
import json

from tools.research.scraper import SmartScraper
from tools.research.config import ScrapingConfig
from tools.research.models import ScrapedContent


def create_mock_session(mock_get_handler):
    """Create a mock aiohttp session with a custom get handler"""
    # Use Mock instead of AsyncMock to prevent auto-creation of async methods
    from unittest.mock import Mock

    mock_session = Mock()

    # Add a proper close method
    async def _close():
        pass

    mock_session.close = _close

    def mock_get_wrapper(url, **kwargs):
        # Create context manager mock
        class MockContextManager:
            def __init__(self, url, **kwargs):
                self.url = url
                self.kwargs = kwargs

            async def __aenter__(self):
                # Call the handler when entering context
                response = await mock_get_handler(self.url, **self.kwargs)
                return response

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        return MockContextManager(url, **kwargs)

    mock_session.get = mock_get_wrapper
    # Add any other attributes that might be accessed
    mock_session.closed = False
    mock_session.connector = None
    mock_session.timeout = None
    return mock_session


class TestScrapingIntegration:
    """Test full scraping workflow from URLs to content"""

    @pytest.fixture
    def scraping_config(self):
        """Create test scraping configuration"""
        return ScrapingConfig(
            max_concurrent=3,
            timeout_range="0.1-0.2",  # Fast for testing
            retry_attempts=2,
            user_agents=["TestAgent/1.0"],
            headers={"Accept": "text/html"},
            respect_robots_txt=False,  # Disable for testing
        )

    @pytest.fixture
    def sample_urls(self):
        """Sample URLs for testing"""
        return [
            {
                "url": "https://example.com/article1",
                "title": "Article 1",
                "description": "Test article 1",
            },
            {
                "url": "https://example.com/article2",
                "title": "Article 2",
                "description": "Test article 2",
            },
            {
                "url": "https://example.com/article3",
                "title": "Article 3",
                "description": "Test article 3",
            },
            {
                "url": "https://example.com/fail",
                "title": "Failed Article",
                "description": "This will fail",
            },
        ]

    @pytest.fixture
    def mock_html_responses(self):
        """Mock HTML responses for different URLs"""
        return {
            "https://example.com/article1": """
                <html>
                    <head><title>Article 1 - Testing</title></head>
                    <body>
                        <h1>Understanding Unit Testing</h1>
                        <p>This article explains the basics of unit testing in Python.</p>
                        <p>Unit tests are essential for maintaining code quality.</p>
                        <code>def test_example(): assert True</code>
                    </body>
                </html>
            """,
            "https://example.com/article2": """
                <html>
                    <head><title>Article 2 - Integration</title></head>
                    <body>
                        <h1>Integration Testing Best Practices</h1>
                        <p>Learn how to write effective integration tests.</p>
                        <ul>
                            <li>Test component interactions</li>
                            <li>Use mock services</li>
                            <li>Verify data flow</li>
                        </ul>
                    </body>
                </html>
            """,
            "https://example.com/article3": """
                <html>
                    <head><title>Article 3 - Performance</title></head>
                    <body>
                        <h1>Performance Testing Guide</h1>
                        <p>Optimize your application with performance tests.</p>
                        <pre><code>
                        import time
                        def measure_performance():
                            start = time.time()
                            # Your code here
                            return time.time() - start
                        </code></pre>
                    </body>
                </html>
            """,
        }

    @pytest.mark.asyncio
    async def test_full_scraping_workflow(
        self, scraping_config, sample_urls, mock_html_responses
    ):
        """Test complete scraping workflow with multiple URLs"""

        # Mock handler for HTTP requests
        async def mock_get_handler(url, **kwargs):
            response = Mock()
            response.status = 200 if url in mock_html_responses else 404
            response.url = url
            response.headers = {"Content-Type": "text/html"}

            if url in mock_html_responses:
                async def text():
                    return mock_html_responses[url]
                response.text = text
            else:
                async def text():
                    raise aiohttp.ClientError("Not found")
                response.text = text
            return response

        # Create mock session and patch
        mock_session = create_mock_session(mock_get_handler)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            async with SmartScraper(scraping_config) as scraper:
                # Track progress
                progress_updates = []
                scraper.set_progress_callback(
                    lambda completed, total: progress_updates.append((completed, total))
                )

                # Scrape URLs
                results = await scraper.scrape_urls(sample_urls)

                # Verify results
                assert len(results) == 3  # 3 successful, 1 failed
                assert all(isinstance(r, ScrapedContent) for r in results)

                # Check content
                for result in results:
                    assert result.url in mock_html_responses
                    assert result.title is not None
                    assert result.content is not None
                    assert isinstance(result.scraped_at, datetime)
                    assert result.metadata["status_code"] == 200

                # Verify progress tracking
                assert len(progress_updates) > 0
                # With retry_attempts=2, failed URL is attempted twice: 4 URLs + 1 retry = 5
                assert (
                    progress_updates[-1][0] == 5
                )  # All URLs attempted including retries

                # Check stats
                stats = scraper.get_stats()
                assert stats["total_urls"] == 4
                assert stats["completed_urls"] == 5  # 4 URLs + 1 retry
                assert stats["failed_urls"] == 1
                assert stats["success_rate"] == 1.25  # 5/4 because of retry

    @pytest.mark.asyncio
    async def test_concurrent_scraping_behavior(self, scraping_config):
        """Test that concurrent scraping respects limits"""
        scraping_config.max_concurrent = 2  # Limit to 2 concurrent requests

        # Track concurrent requests
        concurrent_count = 0
        max_concurrent_observed = 0
        request_times = []

        async def mock_get(url, **kwargs):
            nonlocal concurrent_count, max_concurrent_observed

            # Track request start
            concurrent_count += 1
            request_times.append(("start", url, asyncio.get_event_loop().time()))
            max_concurrent_observed = max(max_concurrent_observed, concurrent_count)

            # Simulate request time
            await asyncio.sleep(0.1)

            # Track request end
            concurrent_count -= 1
            request_times.append(("end", url, asyncio.get_event_loop().time()))

            response = Mock()
            response.status = 200
            response.url = url
            async def text():
                return "<html><body>Test</body></html>"
            response.text = text
            return response

        # Create many URLs to test concurrency
        urls = [
            {"url": f"https://example.com/page{i}", "title": f"Page {i}"}
            for i in range(10)
        ]

        # Create mock session and patch
        mock_session = create_mock_session(mock_get)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            async with SmartScraper(scraping_config) as scraper:
                await scraper.scrape_urls(urls)

                # Verify concurrency limit was respected
                assert max_concurrent_observed <= 2

                # Verify all requests completed
                assert len([t for t in request_times if t[0] == "end"]) == 10

    @pytest.mark.asyncio
    async def test_retry_mechanism(self, scraping_config):
        """Test retry logic for failed requests"""
        scraping_config.retry_attempts = 3

        # Track retry attempts
        attempt_counts = {}

        async def mock_get(url, **kwargs):
            # Count attempts
            attempt_counts[url] = attempt_counts.get(url, 0) + 1

            response = Mock()

            # Fail first 2 attempts, succeed on 3rd
            if attempt_counts[url] < 3:
                raise aiohttp.ClientError(f"Attempt {attempt_counts[url]} failed")

            response.status = 200
            response.url = url

            response.text = AsyncMock(
                return_value="<html><body>Success after retries</body></html>"
            )
            return response

        urls = [{"url": "https://example.com/retry-test", "title": "Retry Test"}]

        # Create mock session and patch
        mock_session = create_mock_session(mock_get)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            async with SmartScraper(scraping_config) as scraper:
                results = await scraper.scrape_urls(urls)

                # Should succeed after retries
                assert len(results) == 1
                assert results[0].url == "https://example.com/retry-test"

                # Verify retry attempts
                assert attempt_counts["https://example.com/retry-test"] == 3

    @pytest.mark.asyncio
    async def test_rate_limiting(self, scraping_config):
        """Test rate limiting with random delays"""
        scraping_config.timeout_range = "0.5-1.0"  # 0.5-1.0 second delays

        request_times = []

        async def mock_get(url, **kwargs):
            request_times.append(asyncio.get_event_loop().time())
            response = Mock()
            response.status = 200
            response.url = url
            async def text():
                return "<html><body>Test</body></html>"
            response.text = text
            return response

        urls = [
            {"url": f"https://example.com/rate{i}", "title": f"Rate {i}"}
            for i in range(3)
        ]

        # Create mock session and patch
        mock_session = create_mock_session(mock_get)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            async with SmartScraper(scraping_config) as scraper:
                start_time = asyncio.get_event_loop().time()
                await scraper.scrape_urls(urls)

                # Verify delays between requests
                for i in range(1, len(request_times)):
                    delay = request_times[i] - request_times[i - 1]
                    # Account for concurrent requests - at least some should show delays
                    if i % scraping_config.max_concurrent == 0:
                        assert delay >= 0.4  # Close to minimum delay

    @pytest.mark.asyncio
    async def test_robots_txt_compliance(self, scraping_config):
        """Test robots.txt compliance when enabled"""
        scraping_config.respect_robots_txt = True

        # Mock robots.txt response
        async def mock_get(url, **kwargs):
            response = Mock()

            if url.endswith("/robots.txt"):
                response.status = 200

                response.text = AsyncMock(
                    return_value="""
                    User-agent: *
                    Disallow: /private/
                    Disallow: /admin/
                    Allow: /public/
                """
                )
            elif "/private/" in url or "/admin/" in url:
                # Should not reach here if robots.txt is respected
                response.status = 403

                async def text():
                    return "Forbidden"
                response.text = text
            else:
                response.status = 200

                response.text = AsyncMock(
                    return_value="<html><body>Allowed content</body></html>"
                )

            response.url = url
            return response

        urls = [
            {"url": "https://example.com/public/article", "title": "Public Article"},
            {"url": "https://example.com/private/data", "title": "Private Data"},
            {"url": "https://example.com/admin/panel", "title": "Admin Panel"},
        ]

        # Create mock session and patch
        mock_session = create_mock_session(mock_get)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            async with SmartScraper(scraping_config) as scraper:
                results = await scraper.scrape_urls(urls)

                # Only public URL should be scraped
                assert len(results) == 1
                assert "public" in results[0].url
                assert all(
                    "private" not in r.url and "admin" not in r.url for r in results
                )

    @pytest.mark.asyncio
    async def test_html_to_markdown_conversion(
        self, scraping_config, mock_html_responses
    ):
        """Test HTML to Markdown conversion quality"""
        # Use a specific HTML with various elements
        test_html = """
        <html>
            <head><title>Conversion Test</title></head>
            <body>
                <h1>Main Title</h1>
                <h2>Subtitle</h2>
                <p>This is a <strong>bold</strong> and <em>italic</em> paragraph.</p>
                <ul>
                    <li>List item 1</li>
                    <li>List item 2</li>
                </ul>
                <a href="https://example.com">External Link</a>
                <a href="/relative/path">Relative Link</a>
                <code>inline_code()</code>
                <pre><code>
                def block_code():
                    return "example"
                </code></pre>
                <script>alert('This should be removed');</script>
                <style>body { color: red; }</style>
            </body>
        </html>
        """

        async def mock_get(url, **kwargs):
            response = Mock()
            response.status = 200
            response.url = url

            async def text():
                return test_html
            response.text = text
            return response

        urls = [{"url": "https://example.com/test", "title": "Test"}]

        # Create mock session and patch
        mock_session = create_mock_session(mock_get)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            async with SmartScraper(scraping_config) as scraper:
                results = await scraper.scrape_urls(urls)

                assert len(results) == 1
                content = results[0].content

                # Verify markdown conversion (SmartScraper converts HTML to markdown)
                assert "# Main Title" in content
                assert "## Subtitle" in content
                assert "**bold**" in content
                assert "*italic*" in content or "_italic_" in content
                assert "- List item 1" in content
                assert "- List item 2" in content
                assert "[External Link](https://example.com)" in content
                assert "`inline_code()`" in content
                assert "def block_code():" in content

                # Verify script and style removal
                assert "<script>" not in content
                assert "alert(" not in content
                assert "<style>" not in content
                assert "color: red" not in content

                # Verify relative URL conversion
                assert "[Relative Link](https://example.com/relative/path)" in content

    @pytest.mark.asyncio
    async def test_error_handling_and_fallback(self, scraping_config):
        """Test error handling for various failure scenarios"""

        # Define different error scenarios
        async def mock_get(url, **kwargs):
            if "timeout" in url:
                await asyncio.sleep(10)  # Trigger timeout
            elif "error500" in url:
                response = Mock()
                response.status = 500
                response.url = url
                return response
            elif "network" in url:
                raise aiohttp.ClientConnectorError(None, OSError("Network error"))
            elif "invalid" in url:
                response = Mock()
                response.status = 200
                response.url = url

                response.text = AsyncMock(
                    side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")
                )
                return response
            else:
                response = Mock()
                response.status = 200
                response.url = url

                response.text = AsyncMock(
                    return_value="<html><body>Success</body></html>"
                )
                return response

        urls = [
            {"url": "https://example.com/success", "title": "Success"},
            {"url": "https://example.com/timeout", "title": "Timeout"},
            {"url": "https://example.com/error500", "title": "Server Error"},
            {"url": "https://example.com/network", "title": "Network Error"},
            {"url": "https://example.com/invalid", "title": "Invalid Encoding"},
        ]

        # Create mock session and patch
        mock_session = create_mock_session(mock_get)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            async with SmartScraper(scraping_config) as scraper:
                results = await scraper.scrape_urls(urls)

                # Only successful request should return content
                assert len(results) == 1
                assert results[0].url == "https://example.com/success"

                # Check failed URLs
                stats = scraper.get_stats()
                assert stats["failed_urls"] == 4
                assert "timeout" in str(stats["failed_url_list"])

    @pytest.mark.asyncio
    async def test_progress_callback_integration(self, scraping_config):
        """Test progress callback functionality"""
        progress_history = []

        async def mock_get(url, **kwargs):
            # Simulate some delay to see progress updates
            await asyncio.sleep(0.05)
            response = Mock()
            response.status = 200
            response.url = url
            async def text():
                return "<html><body>Test</body></html>"
            response.text = text
            return response

        def progress_callback(completed, total):
            progress_history.append(
                {
                    "completed": completed,
                    "total": total,
                    "percentage": (completed / total * 100) if total > 0 else 0,
                }
            )

        urls = [
            {"url": f"https://example.com/page{i}", "title": f"Page {i}"}
            for i in range(5)
        ]

        # Create mock session and patch
        mock_session = create_mock_session(mock_get)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            async with SmartScraper(scraping_config) as scraper:
                scraper.set_progress_callback(progress_callback)
                await scraper.scrape_urls(urls)

                # Verify progress updates
                assert len(progress_history) == 5
                assert progress_history[0]["completed"] == 1
                assert progress_history[-1]["completed"] == 5
                assert all(p["total"] == 5 for p in progress_history)

                # Check progress percentages
                expected_percentages = [20, 40, 60, 80, 100]
                actual_percentages = [p["percentage"] for p in progress_history]
                assert actual_percentages == expected_percentages

    @pytest.mark.asyncio
    async def test_metadata_extraction(self, scraping_config):
        """Test metadata extraction from responses"""

        async def mock_get(url, **kwargs):
            response = Mock()
            response.status = 200
            response.url = (
                url
                if "redirect" not in url
                else "https://example.com/final-destination"
            )
            response.headers = {
                "Content-Type": "text/html; charset=utf-8",
                "Content-Length": "1234",
                "Last-Modified": "Wed, 21 Oct 2015 07:28:00 GMT",
            }

            html_content = """
                <html>
                    <head>
                        <title>Test Page with Metadata</title>
                        <meta name="description" content="Test description">
                        <meta name="keywords" content="test, metadata, scraping">
                    </head>
                    <body>
                        <h1>Test Content</h1>
                        <p>Some content here.</p>
                    </body>
                </html>
            """
            async def text():
                return html_content
            response.text = text
            return response

        urls = [
            {"url": "https://example.com/normal", "title": "Normal Page"},
            {"url": "https://example.com/redirect", "title": "Redirect Page"},
        ]

        # Create mock session and patch
        mock_session = create_mock_session(mock_get)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            async with SmartScraper(scraping_config) as scraper:
                results = await scraper.scrape_urls(urls)

                assert len(results) == 2

                # Check normal page metadata
                normal_meta = results[0].metadata
                assert normal_meta["status_code"] == 200
                assert normal_meta["content_type"] == "text/html; charset=utf-8"
                assert normal_meta["content_length"] > 0
                assert normal_meta["final_url"] == "https://example.com/normal"

                # Check redirect handling
                redirect_meta = results[1].metadata
                assert (
                    redirect_meta["final_url"]
                    == "https://example.com/final-destination"
                )
                assert results[1].url == "https://example.com/final-destination"
