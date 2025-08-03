#!/usr/bin/env python3
"""Tests for m1f-scrape improvements."""

import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tools.scrape_tool.cli import main
from tools.scrape_tool.crawlers import WebCrawler


class TestScrapeImprovements:
    """Test the new features added to m1f-scrape."""

    def test_save_urls_option(self, tmp_path):
        """Test that --save-urls option saves URLs to file."""
        output_dir = tmp_path / "output"
        urls_file = tmp_path / "urls.txt"
        
        # Mock the crawl to return test data
        with patch.object(WebCrawler, 'crawl_sync_with_stats') as mock_crawl:
            mock_crawl.return_value = {
                "site_dir": output_dir / "example.com",
                "scraped_urls": [
                    "https://example.com",
                    "https://example.com/page1",
                    "https://example.com/page2"
                ],
                "errors": [],
                "total_pages": 3
            }
            
            with patch.object(WebCrawler, 'find_downloaded_files') as mock_find:
                mock_find.return_value = [
                    output_dir / "example.com" / "index.html",
                    output_dir / "example.com" / "page1.html",
                    output_dir / "example.com" / "page2.html"
                ]
                
                with patch('sys.argv', [
                    'pytest',
                    'https://example.com',
                    '-o', str(output_dir),
                    '--save-urls', str(urls_file),
                    '--max-pages', '1'
                ]):
                    with patch('sys.stdout'):  # Suppress output
                        main()
        
        # Check that URLs file was created
        assert urls_file.exists()
        content = urls_file.read_text()
        assert "https://example.com" in content
        assert "https://example.com/page1" in content
        assert "https://example.com/page2" in content

    def test_save_files_option(self, tmp_path):
        """Test that --save-files option saves file list."""
        output_dir = tmp_path / "output"
        files_file = tmp_path / "files.txt"
        
        # Create actual files for testing
        site_dir = output_dir / "example.com"
        site_dir.mkdir(parents=True, exist_ok=True)
        
        test_files = [
            site_dir / "index.html",
            site_dir / "page1.html",
            site_dir / "page2.html"
        ]
        
        for f in test_files:
            f.write_text("<html><body>Test</body></html>")
        
        # Mock the crawl to return test data
        with patch.object(WebCrawler, 'crawl_sync_with_stats') as mock_crawl:
            mock_crawl.return_value = {
                "site_dir": site_dir,
                "scraped_urls": ["https://example.com"],
                "errors": [],
                "total_pages": 1
            }
            
            with patch.object(WebCrawler, 'find_downloaded_files') as mock_find:
                mock_find.return_value = test_files
                
                with patch('sys.argv', [
                    'pytest',
                    'https://example.com',
                    '-o', str(output_dir),
                    '--save-files', str(files_file),
                    '--max-pages', '1'
                ]):
                    with patch('sys.stdout'):  # Suppress output
                        main()
        
        # Check that files list was created
        assert files_file.exists()
        content = files_file.read_text()
        for f in test_files:
            assert str(f) in content

    def test_summary_statistics_display(self, tmp_path, capsys):
        """Test that summary statistics are displayed correctly."""
        output_dir = tmp_path / "output"
        site_dir = output_dir / "example.com"
        
        # Mock the crawl to return test data with some errors
        with patch.object(WebCrawler, 'crawl_sync_with_stats') as mock_crawl:
            mock_crawl.return_value = {
                "site_dir": site_dir,
                "scraped_urls": [
                    "https://example.com",
                    "https://example.com/page1",
                    "https://example.com/page2"
                ],
                "errors": [
                    {"url": "https://example.com/error", "error": "404 Not Found"}
                ],
                "total_pages": 4
            }
            
            with patch.object(WebCrawler, 'find_downloaded_files') as mock_find:
                mock_find.return_value = []
                
                # Mock time to control duration calculation
                start_time = time.time()
                with patch('tools.scrape_tool.cli.time.time') as mock_time:
                    mock_time.side_effect = [start_time, start_time + 10.5]  # 10.5 seconds duration
                    
                    with patch('sys.argv', [
                        'pytest',
                        'https://example.com',
                        '-o', str(output_dir),
                        '--max-pages', '1'
                    ]):
                        main()
        
        # Check output for statistics
        captured = capsys.readouterr()
        output = captured.out
        
        assert "Scraping Summary" in output
        assert "Successfully scraped 2 pages" in output  # 3 total - 1 error = 2 successful
        assert "Failed to scrape 1 pages" in output
        assert "Total URLs processed: 3" in output  # 3 scraped URLs
        assert "Success rate: 66.7%" in output  # 2/3 = 66.7%
        assert "Total duration: 10.5 seconds" in output
        assert "Average time per page: 3.50 seconds" in output  # 10.5/3 = 3.50

    def test_verbose_file_listing_limit(self, tmp_path, capsys):
        """Test that verbose file listing is limited to 30 files."""
        output_dir = tmp_path / "output"
        site_dir = output_dir / "example.com"
        site_dir.mkdir(parents=True, exist_ok=True)
        
        # Create many test files
        test_files = []
        for i in range(100):
            f = site_dir / f"page{i:03d}.html"
            f.write_text(f"<html><body>Page {i}</body></html>")
            test_files.append(f)
        
        # Mock the crawl
        with patch.object(WebCrawler, 'crawl_sync_with_stats') as mock_crawl:
            mock_crawl.return_value = {
                "site_dir": site_dir,
                "scraped_urls": ["https://example.com"],
                "errors": [],
                "total_pages": 1
            }
            
            with patch.object(WebCrawler, 'find_downloaded_files') as mock_find:
                mock_find.return_value = test_files
                
                with patch('sys.argv', [
                    'pytest',
                    'https://example.com',
                    '-o', str(output_dir),
                    '--verbose',
                    '--max-pages', '1'
                ]):
                    main()
        
        # Check output
        captured = capsys.readouterr()
        output = captured.out
        
        # Should show first 15 and last 15 files
        assert "page000.html" in output  # First file
        assert "page014.html" in output  # 15th file
        assert "... (70 more files) ..." in output  # Ellipsis message
        assert "page085.html" in output  # 86th file (first of last 15)
        assert "page099.html" in output  # Last file
        assert "Total: 100 files (showing first 15 and last 15)" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])