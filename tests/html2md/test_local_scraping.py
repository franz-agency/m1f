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

"""
Local Scraping Test
Test HTML to Markdown conversion by scraping from the local test server.

This script scrapes test pages from the local development server and converts
them to Markdown format. It now places scraped metadata (URL, timestamp) at
the end of each generated file, making them compatible with the m1f tool's
--remove-scraped-metadata option.

Usage:
    python test_local_scraping.py

Requirements:
    - Local test server running at http://localhost:8090 (or next available port)
    - Start server with: cd tests/html2md_server && python server.py

Features:
    - Scrapes multiple test pages with different configurations
    - Applies CSS selectors to extract specific content
    - Removes unwanted elements (nav, footer, etc.)
    - Places scraped metadata at the end of files (new format)
    - Compatible with m1f --remove-scraped-metadata option
"""

import os
import subprocess
import socket
import platform
import logging
import requests
import sys
from pathlib import Path
from bs4 import BeautifulSoup
import markdownify
from urllib.parse import urljoin
import time
import pytest

# Add colorama imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from tools.shared.colors import info, error, warning, success, header

# Add logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test server configuration
# Use a different port to avoid conflicts with other tests
TEST_SERVER_PORT = 8090
TEST_SERVER_URL = f"http://localhost:{TEST_SERVER_PORT}"


def is_port_in_use(port):
    """Check if a port is currently in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("localhost", port))
            return False
        except OSError:
            return True


@pytest.fixture(scope="module", autouse=True)
def test_server():
    """Start the test server before running tests."""
    server_port = TEST_SERVER_PORT
    server_path = (
        Path(__file__).parent.parent.parent / "tests" / "html2md_server" / "server.py"
    )

    # Check if server script exists
    if not server_path.exists():
        pytest.fail(f"Server script not found: {server_path}")

    # Check if port is already in use
    if is_port_in_use(server_port):
        logger.warning(
            f"Port {server_port} is already in use. Assuming server is already running."
        )
        # Try to connect to existing server
        try:
            response = requests.get(TEST_SERVER_URL, timeout=5)
            if response.status_code == 200:
                logger.info("Connected to existing server")
                yield
                return
        except requests.exceptions.RequestException:
            pytest.fail(f"Port {server_port} is in use but server is not responding")

    # Start server process
    logger.info(f"Starting test server on port {server_port}...")

    # Environment variables for the server
    env = os.environ.copy()
    env["FLASK_ENV"] = "testing"
    env["FLASK_DEBUG"] = "0"
    env["HTML2MD_SERVER_PORT"] = str(server_port)

    # Platform-specific process creation
    if platform.system() == "Windows":
        # Windows-specific handling
        process = subprocess.Popen(
            [sys.executable, "-u", str(server_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            bufsize=1,
            universal_newlines=True,
        )
    else:
        # Unix-like systems
        process = subprocess.Popen(
            [sys.executable, "-u", str(server_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            preexec_fn=os.setsid,
            bufsize=1,
            universal_newlines=True,
        )

    # Wait for server to start
    max_wait = 30  # seconds
    start_time = time.time()
    server_ready = False

    while time.time() - start_time < max_wait:
        # Check if process is still running
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            logger.error(f"Server process terminated with code {process.returncode}")
            if stdout:
                logger.error(f"stdout: {stdout}")
            if stderr:
                logger.error(f"stderr: {stderr}")
            pytest.fail("Server process terminated unexpectedly")

        # Try to connect to server
        try:
            response = requests.get(f"{TEST_SERVER_URL}/api/test-pages", timeout=2)
            if response.status_code == 200:
                logger.info(
                    f"Server started successfully after {time.time() - start_time:.2f} seconds"
                )
                server_ready = True
                break
        except requests.exceptions.RequestException:
            # Server not ready yet
            pass

        time.sleep(0.5)

    if not server_ready:
        # Try to get process output for debugging
        process.terminate()
        stdout, stderr = process.communicate(timeout=5)
        logger.error("Server failed to start within timeout")
        if stdout:
            logger.error(f"stdout: {stdout}")
        if stderr:
            logger.error(f"stderr: {stderr}")
        pytest.fail(f"Server failed to start within {max_wait} seconds")

    # Run tests
    yield

    # Cleanup: stop the server
    logger.info("Stopping test server...")
    try:
        if platform.system() == "Windows":
            # Windows: use terminate
            process.terminate()
        else:
            # Unix: send SIGTERM to process group
            import signal

            os.killpg(os.getpgid(process.pid), signal.SIGTERM)

        # Wait for process to terminate
        process.wait(timeout=5)
    except Exception as e:
        logger.error(f"Error stopping server: {e}")
        # Force kill if needed
        process.kill()
        process.wait()


def check_server_connectivity():
    """Check if the test server is running and accessible."""
    try:
        response = requests.get(TEST_SERVER_URL, timeout=5)
        if response.status_code == 200:
            success(f"Test server is running at {TEST_SERVER_URL}")
            return True
        else:
            error(f"Test server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        error(f"Cannot connect to test server at {TEST_SERVER_URL}")
        error(
            "   Make sure the server is running with: cd tests/html2md_server && python server.py"
        )
        return False
    except Exception as e:
        error(f"Error connecting to test server: {e}")
        return False


def test_server_connectivity(test_server):
    """Test if the test server is running and accessible (pytest compatible)."""
    # The test_server fixture already ensures the server is running
    assert check_server_connectivity(), "Test server should be accessible"


def scrape_and_convert(page_name, outermost_selector=None, ignore_selectors=None):
    """Scrape a page from the test server and convert it to Markdown."""
    url = f"{TEST_SERVER_URL}/page/{page_name}"

    info(f"\n🔍 Scraping: {url}")

    try:
        # Fetch HTML
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"  # Updated user agent
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        info(f"   📄 Fetched {len(response.text)} characters")

        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Apply outermost selector if specified
        if outermost_selector:
            content = soup.select_one(outermost_selector)
            if content:
                info(f"   🎯 Applied selector: {outermost_selector}")
                soup = BeautifulSoup(str(content), "html.parser")
            else:
                warning(
                    f"   Selector '{outermost_selector}' not found, using full page"
                )

        # Remove ignored elements
        if ignore_selectors:
            for selector in ignore_selectors:
                elements = soup.select(selector)
                if elements:
                    info(
                        f"   🗑️  Removed {len(elements)} elements matching '{selector}'"
                    )
                    for element in elements:
                        element.decompose()

        # Convert to Markdown
        html_content = str(soup)
        markdown = markdownify.markdownify(
            html_content, heading_style="atx", bullets="-"
        )

        success(f"   Converted to {len(markdown)} characters of Markdown")

        # Save to file
        output_dir = Path("tests/mf1-html2md/scraped_examples")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"scraped_{page_name}.md"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown)
            f.write("\n\n---\n\n")
            f.write(f"*Scraped from: {url}*\n\n")
            f.write(f"*Scraped at: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            f.write(f"*Source URL: {url}*")

        info(f"   💾 Saved to: {output_path}")

        return {
            "success": True,
            "url": url,
            "html_length": len(response.text),
            "markdown_length": len(markdown),
            "output_file": output_path,
        }

    except Exception as e:
        error(f"   Error: {e}")
        return {"success": False, "url": url, "error": str(e)}


def main():
    """Run local scraping tests."""
    header("🚀 HTML2MD Local Scraping Test")
    info("=" * 50)

    # Check server connectivity
    if not check_server_connectivity():
        sys.exit(1)

    # Test pages to scrape
    test_cases = [
        {
            "name": "m1f-documentation",
            "description": "M1F Documentation (simple conversion)",
            "outermost_selector": None,
            "ignore_selectors": ["nav", "footer"],
        },
        {
            "name": "mf1-html2md-documentation",
            "description": "HTML2MD Documentation (with code blocks)",
            "outermost_selector": "main",
            "ignore_selectors": ["nav", ".sidebar", "footer"],
        },
        {
            "name": "complex-layout",
            "description": "Complex Layout (challenging structure)",
            "outermost_selector": "article, main",
            "ignore_selectors": ["nav", "header", "footer", ".sidebar"],
        },
        {
            "name": "code-examples",
            "description": "Code Examples (syntax highlighting test)",
            "outermost_selector": "main.container",
            "ignore_selectors": ["nav", "footer", "aside"],
        },
    ]

    results = []

    info(f"\n📋 Running {len(test_cases)} test cases...")

    for i, test_case in enumerate(test_cases, 1):
        info(f"\n[{i}/{len(test_cases)}] {test_case['description']}")

        result = scrape_and_convert(
            test_case["name"],
            test_case["outermost_selector"],
            test_case["ignore_selectors"],
        )

        results.append({**result, **test_case})

    # Summary
    info("\n" + "=" * 50)
    header("📊 SCRAPING TEST SUMMARY")
    info("=" * 50)

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    success(f"Successful: {len(successful)}/{len(results)}")
    if len(failed) > 0:
        error(f"Failed: {len(failed)}/{len(results)}")
    else:
        info(f"Failed: {len(failed)}/{len(results)}")

    if successful:
        info(f"\n📄 Generated Markdown files:")
        for result in successful:
            info(f"   • {result['output_file']} ({result['markdown_length']} chars)")

    if failed:
        error(f"\nFailed conversions:")
        for result in failed:
            error(f"   • {result['name']}: {result['error']}")

    info(f"\n🔗 Test server: {TEST_SERVER_URL}")
    info("💡 You can now examine the generated .md files to see conversion quality")


if __name__ == "__main__":
    main()
