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

"""Test the refactored exclude patterns functionality."""

import pytest
from tools.scrape_tool.scrapers.base import WebScraperBase, ScraperConfig


class TestExcludePatternsDRY:
    """Test that exclude patterns work consistently across all scrapers."""
    
    def test_should_exclude_url_regex(self):
        """Test regex pattern exclusion."""
        # Create a minimal concrete implementation for testing
        class TestScraper(WebScraperBase):
            async def scrape_url(self, url: str):
                pass
            async def scrape_site(self, start_url: str):
                pass
        
        config = ScraperConfig(
            exclude_patterns=[
                r".*\.pdf$",  # Regex: ends with .pdf
                r"/admin/.*",  # Regex: admin paths
                r".*\?utm_.*",  # Regex: URLs with utm parameters
            ]
        )
        scraper = TestScraper(config)
        
        # Test regex patterns
        assert scraper._should_exclude_url("http://example.com/file.pdf")
        assert scraper._should_exclude_url("http://example.com/docs/guide.pdf")
        assert scraper._should_exclude_url("http://example.com/admin/settings")
        assert scraper._should_exclude_url("http://example.com/admin/users/list")
        assert scraper._should_exclude_url("http://example.com/page?utm_source=test")
        
        # Should NOT exclude these
        assert not scraper._should_exclude_url("http://example.com/file.html")
        assert not scraper._should_exclude_url("http://example.com/administrator")
        assert not scraper._should_exclude_url("http://example.com/page?ref=test")
    
    def test_should_exclude_url_substring(self):
        """Test substring pattern exclusion (fallback for invalid regex)."""
        class TestScraper(WebScraperBase):
            async def scrape_url(self, url: str):
                pass
            async def scrape_site(self, start_url: str):
                pass
        
        config = ScraperConfig(
            exclude_patterns=[
                "private",  # Simple substring
                "staging",  # Simple substring
                "/temp/",  # Path substring
            ]
        )
        scraper = TestScraper(config)
        
        # Test substring patterns
        assert scraper._should_exclude_url("http://example.com/private/docs")
        assert scraper._should_exclude_url("http://example.com/docs/private-api")
        assert scraper._should_exclude_url("http://staging.example.com/page")
        assert scraper._should_exclude_url("http://example.com/temp/file.html")
        
        # Should NOT exclude these
        assert not scraper._should_exclude_url("http://example.com/public/docs")
        assert not scraper._should_exclude_url("http://example.com/temporary")
    
    def test_excluded_paths(self):
        """Test excluded_paths (path-only matching)."""
        class TestScraper(WebScraperBase):
            async def scrape_url(self, url: str):
                pass
            async def scrape_site(self, start_url: str):
                pass
        
        # Mock config with excluded_paths
        config = ScraperConfig()
        config.excluded_paths = ["/internal/", "/test/", "/debug"]
        scraper = TestScraper(config)
        
        # Test path exclusions
        assert scraper._should_exclude_url("http://example.com/internal/api")
        assert scraper._should_exclude_url("http://example.com/test/suite")
        assert scraper._should_exclude_url("http://example.com/debug/logs")
        assert scraper._should_exclude_url("http://example.com/path/debug/info")
        
        # Should NOT exclude these (domain/query params ignored)
        assert not scraper._should_exclude_url("http://example.com/public/api")
        assert not scraper._should_exclude_url("http://example.com/production")
    
    def test_mixed_patterns_and_paths(self):
        """Test combination of exclude_patterns and excluded_paths."""
        class TestScraper(WebScraperBase):
            async def scrape_url(self, url: str):
                pass
            async def scrape_site(self, start_url: str):
                pass
        
        config = ScraperConfig(
            exclude_patterns=[r".*\.zip$", "download"]
        )
        config.excluded_paths = ["/archive/"]
        scraper = TestScraper(config)
        
        # Test both types work together
        assert scraper._should_exclude_url("http://example.com/file.zip")  # Pattern
        assert scraper._should_exclude_url("http://example.com/download/file")  # Pattern
        assert scraper._should_exclude_url("http://example.com/archive/old")  # Path
        
        # Should NOT exclude
        assert not scraper._should_exclude_url("http://example.com/file.pdf")
        assert not scraper._should_exclude_url("http://example.com/uploads/file")
    
    @pytest.mark.asyncio
    async def test_validate_url_uses_should_exclude(self):
        """Test that validate_url properly uses _should_exclude_url."""
        class TestScraper(WebScraperBase):
            async def scrape_url(self, url: str):
                pass
            async def scrape_site(self, start_url: str):
                pass
        
        config = ScraperConfig(
            exclude_patterns=["blocked"],
            check_ssrf=False  # Disable SSRF check for testing
        )
        scraper = TestScraper(config)
        
        # Test that validate_url excludes based on patterns
        assert await scraper.validate_url("http://example.com/allowed") is True
        assert await scraper.validate_url("http://example.com/blocked/page") is False
    
    @pytest.mark.asyncio
    async def test_validate_url_async(self):
        """Test async validate_url method."""
        class TestScraper(WebScraperBase):
            async def scrape_url(self, url: str):
                pass
            async def scrape_site(self, start_url: str):
                pass
        
        config = ScraperConfig(
            exclude_patterns=["forbidden"],
            check_ssrf=False
        )
        scraper = TestScraper(config)
        
        # Test async validation
        assert await scraper.validate_url("http://example.com/good") is True
        assert await scraper.validate_url("http://example.com/forbidden") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])