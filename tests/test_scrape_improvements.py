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
        with patch.object(WebCrawler, "crawl_sync_with_stats") as mock_crawl:
            mock_crawl.return_value = {
                "site_dir": output_dir / "example.com",
                "scraped_urls": [
                    "https://example.com",
                    "https://example.com/page1",
                    "https://example.com/page2",
                ],
                "errors": [],
                "total_pages": 3,
            }

            with patch.object(WebCrawler, "find_downloaded_files") as mock_find:
                mock_find.return_value = [
                    output_dir / "example.com" / "index.html",
                    output_dir / "example.com" / "page1.html",
                    output_dir / "example.com" / "page2.html",
                ]

                with patch(
                    "sys.argv",
                    [
                        "pytest",
                        "https://example.com",
                        "-o",
                        str(output_dir),
                        "--save-urls",
                        str(urls_file),
                        "--max-pages",
                        "1",
                    ],
                ):
                    with patch("sys.stdout"):  # Suppress output
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
            site_dir / "page2.html",
        ]

        for f in test_files:
            f.write_text("<html><body>Test</body></html>")

        # Mock the crawl to return test data
        with patch.object(WebCrawler, "crawl_sync_with_stats") as mock_crawl:
            mock_crawl.return_value = {
                "site_dir": site_dir,
                "scraped_urls": ["https://example.com"],
                "errors": [],
                "total_pages": 1,
                "session_files": test_files,  # Add session_files to return value
            }

            with patch.object(WebCrawler, "find_downloaded_files") as mock_find:
                mock_find.return_value = test_files

                with patch(
                    "sys.argv",
                    [
                        "pytest",
                        "https://example.com",
                        "-o",
                        str(output_dir),
                        "--save-files",
                        str(files_file),
                        "--max-pages",
                        "1",
                    ],
                ):
                    with patch("sys.stdout"):  # Suppress output
                        main()

        # Check that files list was created
        assert files_file.exists()
        content = files_file.read_text()
        for f in test_files:
            assert str(f) in content

    def test_summary_statistics_display(self, tmp_path, capsys):
        """Test that summary statistics are displayed correctly with real local server scraping."""
        import socket
        import requests
        import subprocess
        from pathlib import Path
        import sys
        import os

        # Find the test server script
        server_path = Path(__file__).parent / "html2md_server" / "server.py"

        # Find a free port
        import random

        def find_free_port(start_port=None):
            if start_port is None:
                # Use a random port in the ephemeral range
                start_port = random.randint(9000, 9999)
            for port in range(start_port, start_port + 100):
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    try:
                        s.bind(("localhost", port))
                        s.close()  # Explicitly close to free the port
                        # Double-check it's still free
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
                            s2.bind(("localhost", port))
                            s2.close()
                        return port
                    except OSError:
                        continue
            raise RuntimeError("Could not find a free port")

        server_port = find_free_port()
        server_url = f"http://localhost:{server_port}"

        # Start the test server
        env = os.environ.copy()
        env["HTML2MD_SERVER_PORT"] = str(server_port)
        env["FLASK_ENV"] = "testing"  # Disable debug mode to prevent reloader
        env["FLASK_DEBUG"] = "0"  # Explicitly disable debug
        env["WERKZEUG_RUN_MAIN"] = "true"  # Prevent the reloader from running
        server_process = subprocess.Popen(
            [sys.executable, str(server_path)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for server to start
        import time

        server_started = False
        for i in range(50):  # 5 seconds timeout
            try:
                response = requests.get(f"{server_url}/", timeout=1)
                if response.status_code == 200:
                    server_started = True
                    break
            except requests.exceptions.RequestException:
                time.sleep(0.1)

            # Check if process died
            if server_process.poll() is not None:
                stdout, stderr = server_process.communicate()
                pytest.fail(f"Server process died. Stderr: {stderr.decode()}")

        if not server_started:
            server_process.terminate()
            stdout, stderr = server_process.communicate()
            pytest.fail(f"Test server failed to start. Stderr: {stderr.decode()}")

        try:
            output_dir = tmp_path / "output"

            # Run the actual scraper against the test server
            # The test server has several pages including a 404 page
            with patch(
                "sys.argv",
                [
                    "pytest",
                    f"{server_url}/",  # Start from index
                    "-o",
                    str(output_dir),
                    "--max-pages",
                    "5",  # Limit pages to scrape
                    "--request-delay",
                    "0",  # No delay for local server
                    "--max-depth",
                    "2",  # Limit depth to avoid scraping too much
                    "--disable-ssrf-check",  # Allow localhost for testing
                ],
            ):
                main()

            # Check output for statistics
            captured = capsys.readouterr()
            output = captured.out

            # Verify summary is displayed
            assert "Scraping Summary" in output

            # Check that statistics are present (exact numbers may vary based on test server content)
            assert "Successfully scraped" in output
            assert "Total URLs processed:" in output
            assert "Success rate:" in output
            assert "Total duration:" in output
            assert "Average time per page:" in output

            # Verify that output directory was created and contains files
            assert output_dir.exists()
            # Find the created site directory (it will be named after the host)
            site_dirs = [d for d in output_dir.iterdir() if d.is_dir()]
            assert len(site_dirs) > 0, "No site directory created"

            site_dir = site_dirs[0]
            html_files = list(site_dir.glob("**/*.html"))
            assert len(html_files) > 0, "No HTML files were scraped"

        finally:
            # Clean up: terminate the server
            server_process.terminate()
            server_process.wait(timeout=5)

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
        with patch.object(WebCrawler, "crawl_sync_with_stats") as mock_crawl:
            mock_crawl.return_value = {
                "site_dir": site_dir,
                "scraped_urls": ["https://example.com"],
                "errors": [],
                "total_pages": 1,
                "session_files": test_files,  # Add session_files to the return value
            }

            with patch.object(WebCrawler, "find_downloaded_files") as mock_find:
                mock_find.return_value = test_files

                with patch(
                    "sys.argv",
                    [
                        "pytest",
                        "https://example.com",
                        "-o",
                        str(output_dir),
                        "--verbose",
                        "--max-pages",
                        "1",
                    ],
                ):
                    main()

        # Check output
        captured = capsys.readouterr()
        output = captured.out

        # Should show first 15 and last 15 files
        assert "page000.html" in output  # First file
        assert "page014.html" in output  # 15th file
        assert "70 more files" in output  # Ellipsis message
        assert "page085.html" in output  # 86th file (first of last 15)
        assert "page099.html" in output  # Last file
        # The exact format may vary, check for key components
        assert (
            "Downloaded files in this session:" in output
            or "HTML files saved in this session: 100" in output
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
