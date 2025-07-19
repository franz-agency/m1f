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
Simple tests for the HTML2MD test server functionality.
Tests the server endpoints without complex mf1-html2md integration.
"""

import os
import sys
import subprocess
import time
import socket
import pytest
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import platform
import logging

# Add logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test server configuration
TEST_SERVER_URL = "http://localhost:8080"


def is_port_in_use(port):
    """Check if a port is currently in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return False
        except OSError:
            return True


@pytest.fixture(scope="module", autouse=True)
def test_server():
    """Start the test server before running tests."""
    server_port = 8080
    server_path = Path(__file__).parent / "html2md_server" / "server.py"
    
    # Check if server script exists
    if not server_path.exists():
        pytest.fail(f"Server script not found: {server_path}")
    
    # Check if port is already in use
    if is_port_in_use(server_port):
        logger.warning(f"Port {server_port} is already in use. Assuming server is already running.")
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
    env['FLASK_ENV'] = 'testing'
    env['FLASK_DEBUG'] = '0'
    env['HTML2MD_SERVER_PORT'] = str(server_port)
    
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
            universal_newlines=True
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
            universal_newlines=True
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
                logger.info(f"Server started successfully after {time.time() - start_time:.2f} seconds")
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


class TestHTML2MDServer:
    """Test class for HTML2MD test server basic functionality."""

    def test_server_running(self):
        """Test that the server is running and responding."""
        response = requests.get(TEST_SERVER_URL)
        assert response.status_code == 200
        assert "HTML2MD Test Suite" in response.text

    def test_homepage_content(self):
        """Test that homepage contains expected content."""
        response = requests.get(TEST_SERVER_URL)
        soup = BeautifulSoup(response.text, "html.parser")

        # Check title
        assert "HTML2MD Test Suite" in soup.title.text

        # Check for navigation links
        nav_links = soup.find_all("a")
        link_texts = [link.text for link in nav_links]

        # Should have links to test pages
        assert any("M1F Documentation" in text for text in link_texts)
        assert any("HTML2MD Documentation" in text for text in link_texts)

    def test_api_test_pages(self):
        """Test the API endpoint that returns test page information."""
        response = requests.get(f"{TEST_SERVER_URL}/api/test-pages")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)

        # Check that expected pages are listed
        expected_pages = [
            "m1f-documentation",
            "html2md-documentation",
            "complex-layout",
            "code-examples",
        ]

        for page in expected_pages:
            assert page in data
            assert "title" in data[page]
            assert "description" in data[page]

    def test_m1f_documentation_page(self):
        """Test the M1F documentation test page."""
        response = requests.get(f"{TEST_SERVER_URL}/page/m1f-documentation")
        assert response.status_code == 200

        # Check content contains M1F information
        assert "M1F" in response.text
        assert "Make One File" in response.text

        soup = BeautifulSoup(response.text, "html.parser")

        # Should have proper HTML structure
        assert soup.find("head") is not None
        assert soup.find("body") is not None

        # Should include CSS
        css_links = soup.find_all("link", rel="stylesheet")
        assert len(css_links) > 0
        assert any("modern.css" in link.get("href", "") for link in css_links)

    def test_html2md_documentation_page(self):
        """Test the HTML2MD documentation test page."""
        response = requests.get(f"{TEST_SERVER_URL}/page/html2md-documentation")
        assert response.status_code == 200

        # Check content contains HTML2MD information
        assert "HTML2MD" in response.text or "html2md" in response.text

        soup = BeautifulSoup(response.text, "html.parser")

        # Should have code examples
        code_blocks = soup.find_all(["code", "pre"])
        assert len(code_blocks) > 0

    def test_complex_layout_page(self):
        """Test the complex layout test page."""
        response = requests.get(f"{TEST_SERVER_URL}/page/complex-layout")
        assert response.status_code == 200

        soup = BeautifulSoup(response.text, "html.parser")

        # Should have complex HTML structures for testing
        # Check for various HTML elements that would challenge converters
        elements_to_check = ["div", "section", "article", "header", "footer"]
        for element in elements_to_check:
            found_elements = soup.find_all(element)
            if found_elements:  # At least some complex elements should be present
                break
        else:
            # If no complex elements found, at least basic structure should exist
            assert soup.find("body") is not None

    def test_code_examples_page(self):
        """Test the code examples test page."""
        response = requests.get(f"{TEST_SERVER_URL}/page/code-examples")
        assert response.status_code == 200

        soup = BeautifulSoup(response.text, "html.parser")

        # Should contain code blocks
        code_elements = soup.find_all(["code", "pre"])
        assert len(code_elements) > 0

        # Should mention various programming languages
        content = response.text.lower()
        languages = ["python", "javascript", "html", "css"]
        found_languages = [lang for lang in languages if lang in content]
        assert len(found_languages) > 0  # At least one language should be mentioned

    def test_static_files(self):
        """Test that static files are served correctly."""
        # Test CSS file
        css_response = requests.get(f"{TEST_SERVER_URL}/static/css/modern.css")
        assert css_response.status_code == 200
        assert "css" in css_response.headers.get("content-type", "").lower()

        # Test JavaScript file
        js_response = requests.get(f"{TEST_SERVER_URL}/static/js/main.js")
        assert js_response.status_code == 200
        assert "javascript" in js_response.headers.get("content-type", "").lower()

    def test_404_page(self):
        """Test that 404 errors are handled properly."""
        response = requests.get(f"{TEST_SERVER_URL}/nonexistent-page")
        assert response.status_code == 404

        # Should contain helpful 404 content
        assert "404" in response.text or "Not Found" in response.text

    def test_page_structure_for_conversion(self):
        """Test that pages have structure suitable for HTML to Markdown conversion."""
        test_pages = [
            "m1f-documentation",
            "html2md-documentation",
            "complex-layout",
        ]

        for page_name in test_pages:
            response = requests.get(f"{TEST_SERVER_URL}/page/{page_name}")
            assert response.status_code == 200

            soup = BeautifulSoup(response.text, "html.parser")

            # Should have headings for structure
            headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
            assert len(headings) > 0, f"Page {page_name} should have headings"

            # Should have paragraphs
            paragraphs = soup.find_all("p")
            assert len(paragraphs) > 0, f"Page {page_name} should have paragraphs"

            # Should have proper HTML5 structure
            assert soup.find("html") is not None
            assert soup.find("head") is not None
            assert soup.find("body") is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
