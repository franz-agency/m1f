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

"""Test concurrent asset downloads optimization."""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path

from tools.scrape_tool.crawlers import WebCrawler, CrawlerConfig
from tools.scrape_tool.scrapers.base import ScrapedPage


class TestConcurrentAssetDownloads:
    """Test that assets are downloaded concurrently without delays."""

    @pytest.mark.asyncio
    async def test_assets_download_concurrently(self, tmp_path):
        """Test that multiple assets are downloaded in parallel."""
        # Track download times
        download_times = []

        async def mock_download_binary(url, max_size):
            """Mock download that tracks timing."""
            start = time.time()
            # Simulate download time
            await asyncio.sleep(0.1)  # 100ms per asset
            download_times.append(time.time() - start)

            return ScrapedPage(
                url=url,
                content="",
                title="asset.jpg",
                is_binary=True,
                binary_content=b"fake image data",
                file_type="image",
                file_size=100,
                status_code=200,
                headers={},
            )

        # Create crawler with test config
        config = CrawlerConfig(
            download_assets=True,
            asset_types=["images"],
            concurrent_requests=5,  # Allow 5 concurrent downloads
            request_delay=0,  # No delay for assets
            output_dir=str(tmp_path),
        )
        crawler = WebCrawler(config)

        # Mock the scraper
        mock_scraper = AsyncMock()
        mock_scraper.download_binary_file = mock_download_binary
        mock_scraper.extract_asset_urls = Mock(
            return_value=[
                "http://example.com/image1.jpg",
                "http://example.com/image2.jpg",
                "http://example.com/image3.jpg",
                "http://example.com/image4.jpg",
                "http://example.com/image5.jpg",
            ]
        )
        # Add attributes to prevent unawaited coroutine warnings
        mock_scraper._visited_urls = set()
        mock_scraper.set_checksum_callback = Mock()

        # Create a test page
        test_page = ScrapedPage(
            url="http://example.com/page.html",
            content="<html><body>Test</body></html>",
            title="Test Page",
            status_code=200,
            headers={},
            is_binary=False,
        )

        # Mock the crawl to return our test page
        async def mock_scrape_site(url):
            yield test_page

        mock_scraper.scrape_site = mock_scrape_site

        # Run the crawl
        start_time = time.time()
        with patch(
            "tools.scrape_tool.crawlers.create_scraper", return_value=mock_scraper
        ):
            result = await crawler.crawl("http://example.com", tmp_path)
        total_time = time.time() - start_time

        # Verify assets were downloaded concurrently
        # If sequential: 5 assets * 0.1s = 0.5s minimum
        # If concurrent: should be close to 0.1s (all in parallel)
        assert (
            total_time < 0.3
        ), f"Downloads took {total_time}s, expected < 0.3s for concurrent downloads"
        assert len(download_times) == 5, "Should have downloaded 5 assets"

    @pytest.mark.asyncio
    async def test_no_delay_between_assets(self, tmp_path):
        """Test that request_delay is NOT applied between asset downloads."""
        download_timestamps = []

        async def mock_download_with_timestamp(url, max_size):
            """Track exact download timestamps."""
            download_timestamps.append(time.time())
            return ScrapedPage(
                url=url,
                content="",
                title="asset.css",
                is_binary=True,
                binary_content=b"css content",
                file_type="css",
                file_size=50,
                status_code=200,
                headers={},
            )

        # Create crawler with a request delay
        config = CrawlerConfig(
            download_assets=True,
            asset_types=["css"],
            concurrent_requests=1,  # Force sequential to check delays
            request_delay=1.0,  # 1 second delay (should NOT apply to assets)
            output_dir=str(tmp_path),
        )
        crawler = WebCrawler(config)

        # Mock scraper
        mock_scraper = AsyncMock()
        mock_scraper.download_binary_file = mock_download_with_timestamp
        mock_scraper.extract_asset_urls = Mock(
            return_value=[
                "http://example.com/style1.css",
                "http://example.com/style2.css",
                "http://example.com/style3.css",
            ]
        )
        # Add attributes to prevent unawaited coroutine warnings
        mock_scraper._visited_urls = set()
        mock_scraper.set_checksum_callback = Mock()

        test_page = ScrapedPage(
            url="http://example.com/index.html",
            content="<html><head></head></html>",
            title="Test",
            status_code=200,
            headers={},
            is_binary=False,
        )

        async def mock_scrape_site(url):
            yield test_page

        mock_scraper.scrape_site = mock_scrape_site

        # Run crawl
        with patch(
            "tools.scrape_tool.crawlers.create_scraper", return_value=mock_scraper
        ):
            await crawler.crawl("http://example.com", tmp_path)

        # Check timestamps - assets should download without delays
        assert len(download_timestamps) == 3
        for i in range(1, len(download_timestamps)):
            time_diff = download_timestamps[i] - download_timestamps[i - 1]
            # Should be much less than the 1 second request_delay
            assert (
                time_diff < 0.5
            ), f"Asset downloads had {time_diff}s delay, expected no delay"

    @pytest.mark.asyncio
    async def test_batch_processing_respects_limits(self, tmp_path):
        """Test that concurrent downloads respect the configured limit."""
        concurrent_downloads = []
        max_concurrent = 0

        async def mock_download_tracking_concurrency(url, max_size):
            """Track concurrent downloads."""
            nonlocal max_concurrent
            concurrent_downloads.append(1)
            current = len(concurrent_downloads)
            max_concurrent = max(max_concurrent, current)

            await asyncio.sleep(0.05)  # Simulate download

            concurrent_downloads.pop()
            return ScrapedPage(
                url=url,
                content="",
                title="file.js",
                is_binary=True,
                binary_content=b"js",
                file_type="js",
                file_size=10,
                status_code=200,
                headers={},
            )

        # Create crawler with specific concurrent limit
        config = CrawlerConfig(
            download_assets=True,
            asset_types=["js"],
            concurrent_requests=3,  # Max 3 concurrent
            output_dir=str(tmp_path),
        )
        crawler = WebCrawler(config)

        # Create 10 assets to download
        mock_scraper = AsyncMock()
        mock_scraper.download_binary_file = mock_download_tracking_concurrency
        mock_scraper.extract_asset_urls = Mock(
            return_value=[f"http://example.com/script{i}.js" for i in range(10)]
        )
        # Add attributes to prevent unawaited coroutine warnings
        mock_scraper._visited_urls = set()
        mock_scraper.set_checksum_callback = Mock()

        test_page = ScrapedPage(
            url="http://example.com/app.html",
            content="<html></html>",
            title="App",
            status_code=200,
            headers={},
            is_binary=False,
        )

        async def mock_scrape_site(url):
            yield test_page

        mock_scraper.scrape_site = mock_scrape_site

        # Run crawl
        with patch(
            "tools.scrape_tool.crawlers.create_scraper", return_value=mock_scraper
        ):
            await crawler.crawl("http://example.com", tmp_path)

        # Verify concurrent limit was respected
        assert (
            max_concurrent <= 3
        ), f"Max concurrent was {max_concurrent}, expected <= 3"
        assert max_concurrent > 1, "Should have had some concurrent downloads"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
