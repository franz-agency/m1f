#!/usr/bin/env python3
"""
Comprehensive test suite for html2md converter using the test server.
Tests various HTML structures, edge cases, and conversion options.
"""

import os
import sys
import pytest
import asyncio
import aiohttp
import subprocess
import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import json
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.html2md import HTML2MDConverter, ConversionOptions


class TestServer:
    """Manages the test server lifecycle."""

    def __init__(self, port: int = 8080):
        self.port = port
        self.process = None
        self.base_url = f"http://localhost:{port}"

    def start(self):
        """Start the test server."""
        server_path = Path(__file__).parent / "html2md_server" / "server.py"
        self.process = subprocess.Popen(
            [sys.executable, str(server_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # Wait for server to start
        time.sleep(2)

    def stop(self):
        """Stop the test server."""
        if self.process:
            self.process.terminate()
            self.process.wait()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


@pytest.fixture(scope="session")
def test_server():
    """Fixture to manage test server lifecycle."""
    with TestServer() as server:
        yield server


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


class TestHTML2MDConversion:
    """Test HTML to Markdown conversion with various scenarios."""

    @pytest.mark.asyncio
    async def test_basic_conversion(self, test_server, temp_output_dir):
        """Test basic HTML to Markdown conversion."""
        converter = HTML2MDConverter(
            ConversionOptions(
                source_dir=f"{test_server.base_url}/page",
                destination_dir=temp_output_dir,
            )
        )

        # Convert a simple page
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{test_server.base_url}/page/m1f-documentation"
            ) as resp:
                html_content = await resp.text()

        markdown = converter.convert_html(html_content)

        # Verify conversion
        assert "# M1F - Make One File" in markdown
        assert "```python" in markdown  # Code blocks preserved
        assert "[" in markdown and "](" in markdown  # Links converted

    @pytest.mark.asyncio
    async def test_content_selection(self, test_server, temp_output_dir):
        """Test CSS selector-based content extraction."""
        converter = HTML2MDConverter(
            ConversionOptions(
                source_dir=f"{test_server.base_url}/page",
                destination_dir=temp_output_dir,
                outermost_selector="article",
                ignore_selectors=["nav", ".sidebar", "footer"],
            )
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{test_server.base_url}/page/html2md-documentation"
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
    async def test_complex_layouts(self, test_server, temp_output_dir):
        """Test conversion of complex CSS layouts."""
        converter = HTML2MDConverter(
            ConversionOptions(
                source_dir=f"{test_server.base_url}/page",
                destination_dir=temp_output_dir,
                outermost_selector="article",
            )
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{test_server.base_url}/page/complex-layout"
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
    async def test_code_examples(self, test_server, temp_output_dir):
        """Test code block conversion with various languages."""
        converter = HTML2MDConverter(
            ConversionOptions(
                source_dir=f"{test_server.base_url}/page",
                destination_dir=temp_output_dir,
                convert_code_blocks=True,
            )
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{test_server.base_url}/page/code-examples"
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
    async def test_parallel_conversion(self, test_server, temp_output_dir):
        """Test parallel processing of multiple files."""
        converter = HTML2MDConverter(
            ConversionOptions(
                source_dir=test_server.base_url,
                destination_dir=temp_output_dir,
                parallel=True,
                max_workers=4,
            )
        )

        # Get list of test pages
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{test_server.base_url}/api/test-pages") as resp:
                pages = await resp.json()

        # Convert all pages in parallel
        results = await converter.convert_directory_from_urls(
            [f"{test_server.base_url}/page/{page}" for page in pages.keys()]
        )

        # Verify all conversions completed
        assert len(results) == len(pages)
        assert all(r.success for r in results)

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

        assert options.source_directory == "./html"
        assert options.outermost_selector == "article"
        assert options.parallel is True
        assert options.max_workers == 8


class TestCLI:
    """Test command-line interface."""

    def test_cli_help(self):
        """Test CLI help output."""
        result = subprocess.run(
            [sys.executable, "-m", "tools.html2md", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "--source-dir" in result.stdout
        assert "--destination-dir" in result.stdout
        assert "--outermost-selector" in result.stdout

    def test_cli_basic_conversion(self, test_server, temp_output_dir):
        """Test basic CLI conversion."""
        result = subprocess.run(
            [
                sys.executable,
                "-m", "tools.html2md",
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
                "-m", "tools.html2md",
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
