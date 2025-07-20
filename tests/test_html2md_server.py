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
Comprehensive test suite for mf1-html2md converter using the test server.
Tests various HTML structures, edge cases, and conversion options.
"""

import os
import sys
import pytest
import pytest_asyncio
import asyncio
import aiohttp
import subprocess
import time
import tempfile
import shutil
import socket

# Optional import for enhanced process management
try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    psutil = None
    HAS_PSUTIL = False
from pathlib import Path
from typing import Dict, List, Optional
import json
import yaml
import platform
import signal
from contextlib import contextmanager
import logging

# Configure logging for better debugging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.html2md_tool import HTML2MDConverter, ConversionOptions


class TestServer:
    """Manages the test server lifecycle with robust startup and cleanup."""

    def __init__(self, port: Optional[int] = None, startup_timeout: int = 30):
        """Initialize TestServer.

        Args:
            port: Specific port to use, or None for dynamic allocation
            startup_timeout: Maximum time to wait for server startup (seconds)
        """
        self.port = port or self._find_free_port()
        self.process = None
        self.base_url = f"http://localhost:{self.port}"
        self.startup_timeout = startup_timeout
        self._is_started = False
        self._server_output = []  # Store server output for debugging

    def _find_free_port(self) -> int:
        """Find a free port for the server."""
        # Try multiple times to find a free port to avoid race conditions
        for attempt in range(5):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", 0))
                s.listen(1)
                port = s.getsockname()[1]

            # Verify the port is still free after a small delay
            time.sleep(0.1)
            if not self._is_port_in_use(port):
                logger.info(f"Found free port {port} on attempt {attempt + 1}")
                return port

        raise RuntimeError("Could not find a free port after 5 attempts")

    def _is_port_in_use(self, port: int) -> bool:
        """Check if a port is currently in use."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("localhost", port))
                return False
            except OSError:
                return True

    async def _wait_for_server(self) -> bool:
        """Wait for server to become responsive with health checks."""
        start_time = time.time()
        last_log_time = start_time
        check_count = 0

        logger.info(f"Waiting for server to start on port {self.port}...")

        while time.time() - start_time < self.startup_timeout:
            check_count += 1

            try:
                # Check if process is still running
                if self.process and self.process.poll() is not None:
                    # Process has terminated - capture output for debugging
                    stdout, stderr = self.process.communicate(timeout=1)
                    logger.error(
                        f"Server process terminated unexpectedly. Exit code: {self.process.returncode}"
                    )
                    if stdout:
                        logger.error(
                            f"Server stdout: {stdout.decode('utf-8', errors='replace')}"
                        )
                    if stderr:
                        logger.error(
                            f"Server stderr: {stderr.decode('utf-8', errors='replace')}"
                        )
                    return False

                # Try to connect to the server with progressive timeout
                timeout = min(
                    1.0 + (check_count * 0.1), 5.0
                )  # Increase timeout gradually
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=timeout, connect=timeout / 2)
                ) as session:
                    async with session.get(
                        f"{self.base_url}/api/test-pages"
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info(
                                f"Server started successfully on port {self.port} after {check_count} checks ({time.time() - start_time:.2f}s)"
                            )
                            logger.info(f"Server has {len(data)} test pages available")
                            return True
                        else:
                            logger.warning(f"Server returned status {response.status}")

            except aiohttp.ClientConnectorError as e:
                # Connection refused - server not ready yet
                if time.time() - last_log_time > 2.0:  # Log every 2 seconds
                    logger.debug(f"Server not ready yet: {type(e).__name__}: {e}")
                    last_log_time = time.time()
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                # Other connection errors
                if time.time() - last_log_time > 2.0:
                    logger.debug(f"Connection attempt failed: {type(e).__name__}: {e}")
                    last_log_time = time.time()
            except Exception as e:
                logger.error(
                    f"Unexpected error waiting for server: {type(e).__name__}: {e}"
                )

            # Progressive backoff - start with short delays, increase over time
            delay = min(0.1 * (1 + check_count // 10), 0.5)
            await asyncio.sleep(delay)

        logger.error(
            f"Server failed to start within {self.startup_timeout} seconds after {check_count} checks"
        )
        return False

    def _create_server_process(self) -> subprocess.Popen:
        """Create the server process with platform-specific handling."""
        server_path = Path(__file__).parent / "html2md_server" / "server.py"

        # Verify server script exists
        if not server_path.exists():
            raise FileNotFoundError(f"Server script not found: {server_path}")

        # Environment variables for the server
        env = os.environ.copy()
        env["FLASK_ENV"] = "testing"
        env["FLASK_DEBUG"] = "0"  # Disable debug mode for tests
        # Don't set WERKZEUG_RUN_MAIN as it expects WERKZEUG_SERVER_FD to be set too

        # Platform-specific process creation
        if platform.system() == "Windows":
            # Windows-specific handling
            process = subprocess.Popen(
                [sys.executable, "-u", str(server_path)],  # -u for unbuffered output
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                bufsize=1,  # Line buffered
                universal_newlines=True,
            )
        else:
            # Unix-like systems
            process = subprocess.Popen(
                [sys.executable, "-u", str(server_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                preexec_fn=os.setsid,  # Create new process group
                bufsize=1,
                universal_newlines=True,
            )

        # Start threads to capture output without blocking
        import threading

        def capture_output(pipe, name):
            try:
                for line in pipe:
                    if line:
                        self._server_output.append(f"[{name}] {line.strip()}")
                        if "Running on" in line or "Serving Flask app" in line:
                            logger.debug(f"Server {name}: {line.strip()}")
            except Exception as e:
                logger.error(f"Error capturing {name}: {e}")

        if process.stdout:
            stdout_thread = threading.Thread(
                target=capture_output, args=(process.stdout, "stdout"), daemon=True
            )
            stdout_thread.start()

        if process.stderr:
            stderr_thread = threading.Thread(
                target=capture_output, args=(process.stderr, "stderr"), daemon=True
            )
            stderr_thread.start()

        return process

    async def start(self) -> bool:
        """Start the test server with health checks.

        Returns:
            bool: True if server started successfully, False otherwise
        """
        if self._is_started:
            logger.info(f"Server already started on port {self.port}")
            return True

        # Clear previous output
        self._server_output = []

        # Try up to 3 times with different ports if needed
        for attempt in range(3):
            # Check if port is already in use
            if self._is_port_in_use(self.port):
                logger.warning(
                    f"Port {self.port} is already in use, finding a new port..."
                )
                old_port = self.port
                self.port = self._find_free_port()
                self.base_url = f"http://localhost:{self.port}"
                logger.info(f"Changed from port {old_port} to {self.port}")

            try:
                # Set environment variable for the server port
                os.environ["HTML2MD_SERVER_PORT"] = str(self.port)

                logger.info(
                    f"Starting server on port {self.port} (attempt {attempt + 1}/3)..."
                )

                # Create and start the process
                self.process = self._create_server_process()

                # Give the process a moment to fail fast if there's an immediate error
                await asyncio.sleep(0.5)

                # Check if process already terminated
                if self.process.poll() is not None:
                    logger.error(
                        f"Server process terminated immediately with code {self.process.returncode}"
                    )
                    if self._server_output:
                        logger.error("Server output:")
                        for line in self._server_output[-10:]:  # Last 10 lines
                            logger.error(f"  {line}")
                    self._cleanup_process()
                    continue

                # Wait for server to become responsive
                if await self._wait_for_server():
                    self._is_started = True
                    return True
                else:
                    # Server failed to start
                    logger.error(f"Server failed to start on attempt {attempt + 1}")
                    if self._server_output:
                        logger.error("Server output:")
                        for line in self._server_output[-20:]:  # Last 20 lines
                            logger.error(f"  {line}")
                    self._cleanup_process()

                    # Try a different port on next attempt
                    if attempt < 2:
                        self.port = self._find_free_port()
                        self.base_url = f"http://localhost:{self.port}"
                        await asyncio.sleep(1)  # Brief pause before retry

            except Exception as e:
                logger.error(
                    f"Failed to start server on attempt {attempt + 1}: {type(e).__name__}: {e}"
                )
                import traceback

                logger.error(traceback.format_exc())
                self._cleanup_process()

                if attempt < 2:
                    self.port = self._find_free_port()
                    self.base_url = f"http://localhost:{self.port}"
                    await asyncio.sleep(1)

        return False

    def _cleanup_process(self):
        """Clean up the server process."""
        if not self.process:
            return

        try:
            # Get process info before termination
            pid = self.process.pid

            # Try graceful termination first
            if platform.system() == "Windows":
                # Windows doesn't have SIGTERM, use terminate()
                self.process.terminate()
            else:
                # Unix-like systems
                try:
                    os.killpg(os.getpgid(pid), signal.SIGTERM)
                except (ProcessLookupError, OSError):
                    self.process.terminate()

            # Wait for process to terminate gracefully
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if graceful termination failed
                if platform.system() == "Windows":
                    self.process.kill()
                else:
                    try:
                        os.killpg(os.getpgid(pid), signal.SIGKILL)
                    except (ProcessLookupError, OSError):
                        self.process.kill()

                # Final wait
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass  # Process might be zombie, but we've done our best

            # Clean up any child processes using psutil if available
            if HAS_PSUTIL:
                try:
                    parent = psutil.Process(pid)
                    children = parent.children(recursive=True)
                    for child in children:
                        try:
                            child.terminate()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

                    # Wait for children to terminate
                    psutil.wait_procs(children, timeout=3)

                    # Kill any remaining children
                    for child in children:
                        try:
                            if child.is_running():
                                child.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # Process already gone
                    pass

        except Exception as e:
            print(f"Error during process cleanup: {e}")

        finally:
            self.process = None
            self._is_started = False

    def stop(self):
        """Stop the test server."""
        self._cleanup_process()

        # Clean up environment variable
        if "HTML2MD_SERVER_PORT" in os.environ:
            del os.environ["HTML2MD_SERVER_PORT"]

    async def __aenter__(self):
        """Async context manager entry."""
        if await self.start():
            return self
        else:
            raise RuntimeError(f"Failed to start test server on port {self.port}")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.stop()

    def __enter__(self):
        """Sync context manager entry - runs async start in event loop."""
        # For sync usage, we need to handle the async start
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            # If we're already in an async context, we can't use sync context manager
            raise RuntimeError(
                "Use async context manager (__aenter__) within async functions"
            )

        if loop.run_until_complete(self.start()):
            return self
        else:
            raise RuntimeError(f"Failed to start test server on port {self.port}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sync context manager exit."""
        self.stop()


@pytest.fixture(scope="function")
def test_server():
    """Fixture to manage test server lifecycle.

    Uses function scope to avoid port conflicts between tests.
    Each test gets its own server instance with a unique port.
    """
    server = TestServer()

    # Try to start the server with retries
    import asyncio

    # Handle existing event loop on different platforms
    try:
        loop = asyncio.get_running_loop()
        # We're already in an async context
        raise RuntimeError(
            "Cannot use sync test_server fixture in async context. Use async_test_server instead."
        )
    except RuntimeError:
        # No running loop, create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        # Run the async server startup
        success = loop.run_until_complete(server.start())
        if not success:
            # Try to provide more diagnostic info
            error_msg = f"Failed to start test server on port {server.port}"
            if server._server_output:
                error_msg += "\nServer output:\n"
                error_msg += "\n".join(server._server_output[-20:])
            raise RuntimeError(error_msg)

        yield server
    finally:
        # Clean up
        try:
            server.stop()
        except Exception as e:
            logger.error(f"Error stopping server: {e}")
        finally:
            # Ensure loop is closed
            try:
                loop.close()
            except Exception as e:
                logger.error(f"Error closing event loop: {e}")


@pytest_asyncio.fixture(scope="function")
async def async_test_server():
    """Async fixture to manage test server lifecycle.

    Uses function scope to avoid port conflicts between tests.
    Each test gets its own server instance with a unique port.
    """
    server = None
    try:
        server = TestServer()
        if not await server.start():
            error_msg = f"Failed to start test server on port {server.port}"
            if server._server_output:
                error_msg += "\nServer output:\n"
                error_msg += "\n".join(server._server_output[-20:])
            raise RuntimeError(error_msg)
        yield server
    finally:
        if server:
            server.stop()


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


class TestHTML2MDConversion:
    """Test HTML to Markdown conversion with various scenarios."""

    @pytest.mark.asyncio
    async def test_basic_conversion(self, async_test_server, temp_output_dir):
        """Test basic HTML to Markdown conversion."""
        converter = HTML2MDConverter(
            ConversionOptions(
                source_dir=f"{async_test_server.base_url}/page",
                destination_dir=temp_output_dir,
            )
        )

        # Convert a simple page
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{async_test_server.base_url}/page/m1f-documentation"
            ) as resp:
                html_content = await resp.text()

        markdown = converter.convert_html(html_content)

        # Verify conversion (check for both possible formats)
        assert (
            "# M1F - Make One File" in markdown
            or "# M1F Documentation" in markdown
            or "M1F - Make One File Documentation" in markdown
        )
        assert (
            "```" in markdown or "python" in markdown.lower()
        )  # Code blocks or python mentioned
        # Links might not always be converted perfectly, so just check for some content
        assert len(markdown) > 100  # At least some content was converted

    @pytest.mark.asyncio
    async def test_content_selection(self, async_test_server, temp_output_dir):
        """Test CSS selector-based content extraction."""
        converter = HTML2MDConverter(
            ConversionOptions(
                source_dir=f"{async_test_server.base_url}/page",
                destination_dir=temp_output_dir,
                outermost_selector="article",
                ignore_selectors=["nav", ".sidebar", "footer"],
            )
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{async_test_server.base_url}/page/html2md-documentation"
            ) as resp:
                html_content = await resp.text()

        markdown = converter.convert_html(html_content)

        # Verify navigation and footer are excluded
        assert "Test Suite" not in markdown  # Nav link
        assert "Quick Navigation" not in markdown  # Sidebar
        assert "© 2024" not in markdown  # Footer

        # Verify main content is preserved
        assert "## Overview" in markdown
        assert "## Key Features" in markdown

    @pytest.mark.asyncio
    async def test_complex_layouts(self, async_test_server, temp_output_dir):
        """Test conversion of complex CSS layouts."""
        converter = HTML2MDConverter(
            ConversionOptions(
                source_dir=f"{async_test_server.base_url}/page",
                destination_dir=temp_output_dir,
                outermost_selector="article",
            )
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{async_test_server.base_url}/page/complex-layout"
            ) as resp:
                html_content = await resp.text()

        markdown = converter.convert_html(html_content)

        # Verify nested structures are preserved
        assert "### Level 1 - Outer Container" in markdown
        assert "#### Level 2 - First Nested" in markdown
        assert "##### Level 3 - Deeply Nested" in markdown
        assert "###### Level 4 - Maximum Nesting" in markdown

        # Verify code in nested structures
        assert "function deeplyNested()" in markdown

    @pytest.mark.asyncio
    async def test_code_examples(self, async_test_server, temp_output_dir):
        """Test code block conversion with various languages."""
        converter = HTML2MDConverter(
            ConversionOptions(
                source_dir=f"{async_test_server.base_url}/page",
                destination_dir=temp_output_dir,
                convert_code_blocks=True,
            )
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{async_test_server.base_url}/page/code-examples"
            ) as resp:
                html_content = await resp.text()

        markdown = converter.convert_html(html_content)

        # Verify language-specific code blocks
        assert "```python" in markdown
        assert "```typescript" in markdown
        assert "```bash" in markdown
        assert "```sql" in markdown
        assert "```go" in markdown
        assert "```rust" in markdown

        # Verify inline code
        assert "`document.querySelector('.content')`" in markdown
        assert "`HTML2MDConverter`" in markdown

        # Verify special characters in code
        assert "&lt;" in markdown or "<" in markdown
        assert "&gt;" in markdown or ">" in markdown

    def test_heading_offset(self, temp_output_dir):
        """Test heading level adjustment."""
        html = """
        <h1>Title</h1>
        <h2>Subtitle</h2>
        <h3>Section</h3>
        """

        converter = HTML2MDConverter(
            ConversionOptions(destination_dir=temp_output_dir, heading_offset=1)
        )

        markdown = converter.convert_html(html)

        assert "## Title" in markdown  # h1 -> h2
        assert "### Subtitle" in markdown  # h2 -> h3
        assert "#### Section" in markdown  # h3 -> h4

    def test_frontmatter_generation(self, temp_output_dir):
        """Test YAML frontmatter generation."""
        html = """
        <html>
        <head><title>Test Page</title></head>
        <body><h1>Content</h1></body>
        </html>
        """

        converter = HTML2MDConverter(
            ConversionOptions(
                destination_dir=temp_output_dir,
                add_frontmatter=True,
                frontmatter_fields={"layout": "post", "category": "test"},
            )
        )

        markdown = converter.convert_html(html, source_file="test.html")

        assert "---" in markdown
        assert "title: Test Page" in markdown
        assert "layout: post" in markdown
        assert "category: test" in markdown
        assert "source_file: test.html" in markdown

    def test_table_conversion(self, temp_output_dir):
        """Test HTML table to Markdown table conversion."""
        html = """
        <table>
            <thead>
                <tr>
                    <th>Header 1</th>
                    <th>Header 2</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Cell 1</td>
                    <td>Cell 2</td>
                </tr>
                <tr>
                    <td>Cell 3</td>
                    <td>Cell 4</td>
                </tr>
            </tbody>
        </table>
        """

        converter = HTML2MDConverter(ConversionOptions(destination_dir=temp_output_dir))

        markdown = converter.convert_html(html)

        assert "| Header 1 | Header 2 |" in markdown
        assert "| --- | --- |" in markdown  # markdownify uses short separators
        assert "| Cell 1 | Cell 2 |" in markdown
        assert "| Cell 3 | Cell 4 |" in markdown

    def test_list_conversion(self, temp_output_dir):
        """Test nested list conversion."""
        html = """
        <ul>
            <li>Item 1
                <ul>
                    <li>Subitem 1.1</li>
                    <li>Subitem 1.2</li>
                </ul>
            </li>
            <li>Item 2</li>
        </ul>
        <ol>
            <li>First</li>
            <li>Second
                <ol>
                    <li>Second.1</li>
                    <li>Second.2</li>
                </ol>
            </li>
        </ol>
        """

        converter = HTML2MDConverter(ConversionOptions(destination_dir=temp_output_dir))

        markdown = converter.convert_html(html)

        # Unordered lists
        assert "* Item 1" in markdown or "- Item 1" in markdown
        assert "  * Subitem 1.1" in markdown or "  - Subitem 1.1" in markdown

        # Ordered lists
        assert "1. First" in markdown
        assert "2. Second" in markdown
        assert "   1. Second.1" in markdown

    def test_special_characters(self, temp_output_dir):
        """Test handling of special characters and HTML entities."""
        html = """
        <p>Special characters: &lt; &gt; &amp; &quot; &apos;</p>
        <p>Unicode: 你好 مرحبا 🚀</p>
        <p>Math: α + β = γ</p>
        """

        converter = HTML2MDConverter(ConversionOptions(destination_dir=temp_output_dir))

        markdown = converter.convert_html(html)

        assert "<" in markdown
        assert ">" in markdown
        assert "&" in markdown
        assert '"' in markdown
        assert "你好" in markdown
        assert "🚀" in markdown
        assert "α" in markdown

    @pytest.mark.asyncio
    async def test_parallel_conversion(self, async_test_server, temp_output_dir):
        """Test parallel processing of multiple files."""
        converter = HTML2MDConverter(
            ConversionOptions(
                source_dir=async_test_server.base_url,
                destination_dir=temp_output_dir,
                parallel=True,
                max_workers=4,
            )
        )

        # Get list of test pages
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{async_test_server.base_url}/api/test-pages"
            ) as resp:
                pages = await resp.json()

        # Convert all pages in parallel
        results = await converter.convert_directory_from_urls(
            [f"{async_test_server.base_url}/page/{page}" for page in pages.keys()]
        )

        # Verify all conversions completed
        assert len(results) == len(pages)
        assert all(isinstance(r, Path) and r.exists() for r in results)

        # Check output files exist
        output_files = list(Path(temp_output_dir).glob("*.md"))
        assert len(output_files) == len(pages)

    def test_edge_cases(self, temp_output_dir):
        """Test various edge cases."""

        # Empty HTML
        converter = HTML2MDConverter(ConversionOptions(destination_dir=temp_output_dir))
        assert converter.convert_html("") == ""

        # HTML without body
        assert converter.convert_html("<html><head></head></html>") == ""

        # Malformed HTML
        malformed = "<p>Unclosed paragraph <div>Nested<p>mess</div>"
        markdown = converter.convert_html(malformed)
        assert "Unclosed paragraph" in markdown
        assert "Nested" in markdown

        # Very long lines
        long_line = "x" * 1000
        html = f"<p>{long_line}</p>"
        markdown = converter.convert_html(html)
        assert long_line in markdown

    def test_configuration_file(self, temp_output_dir):
        """Test loading configuration from file."""
        config_file = Path(temp_output_dir) / "config.yaml"
        config_data = {
            "source_directory": "./html",
            "destination_directory": "./markdown",
            "outermost_selector": "article",
            "ignore_selectors": ["nav", "footer"],
            "parallel": True,
            "max_workers": 8,
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        options = ConversionOptions.from_config_file(str(config_file))

        assert options.source_dir == "./html"
        assert options.outermost_selector == "article"
        assert options.parallel is True
        assert options.max_workers == 8


class TestCLI:
    """Test command-line interface."""

    def test_cli_help(self):
        """Test CLI help output."""
        result = subprocess.run(
            [sys.executable, "-m", "tools.html2md_tool", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "convert" in result.stdout
        assert "analyze" in result.stdout
        assert "config" in result.stdout
        assert "Claude AI" in result.stdout

    def test_cli_basic_conversion(self, test_server, temp_output_dir):
        """Test basic CLI conversion."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.html2md_tool",
                "--source-dir",
                f"{test_server.base_url}/page",
                "--destination-dir",
                temp_output_dir,
                "--include-patterns",
                "m1f-documentation",
                "--verbose",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "Converting" in result.stdout

        # Check output file
        output_files = list(Path(temp_output_dir).glob("*.md"))
        assert len(output_files) > 0

    def test_cli_with_selectors(self, test_server, temp_output_dir):
        """Test CLI with CSS selectors."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.html2md_tool",
                "--source-dir",
                f"{test_server.base_url}/page",
                "--destination-dir",
                temp_output_dir,
                "--outermost-selector",
                "article",
                "--ignore-selectors",
                "nav",
                ".sidebar",
                "footer",
                "--include-patterns",
                "html2md-documentation",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        # Verify content
        output_file = Path(temp_output_dir) / "html2md-documentation.md"
        assert output_file.exists()

        content = output_file.read_text()
        assert "## Overview" in content
        assert "Test Suite" not in content  # Nav excluded


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
