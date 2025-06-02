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
Tests for the HTML to Markdown converter.
"""
import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# Add the parent directory to sys.path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from tools.html2md import (
    convert_html,
    adjust_internal_links,
    extract_title_from_html,
)


class TestHtmlToMarkdown(unittest.TestCase):
    """Tests for the HTML to Markdown converter."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.html_dir = self.test_dir / "html"
        self.md_dir = self.test_dir / "markdown"
        self.html_dir.mkdir()
        self.md_dir.mkdir()

        # Create a sample HTML file
        self.sample_html = """<!DOCTYPE html>
<html>
<head>
    <title>Test Document</title>
</head>
<body>
    <h1>Test Heading</h1>
    <p>This is a <strong>test</strong> paragraph with <em>emphasis</em>.</p>
    <ul>
        <li>Item 1</li>
        <li>Item 2</li>
    </ul>
    <a href="page.html">Link to another page</a>
    <pre><code class="language-python">
def hello():
    print("Hello, world!")
    </code></pre>
</body>
</html>"""

        self.sample_html_path = self.html_dir / "sample.html"
        self.sample_html_path.write_text(self.sample_html)

    def tearDown(self):
        """Tear down test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_convert_html_basic(self):
        """Test basic HTML to Markdown conversion."""
        html = "<h1>Test</h1><p>This is a test.</p>"
        expected = "# Test\n\nThis is a test."
        result = convert_html(html)
        self.assertEqual(result.strip(), expected)

    def test_convert_html_with_code_blocks(self):
        """Test HTML to Markdown conversion with code blocks."""
        html = '<pre><code class="language-python">print("Hello")</code></pre>'
        result = convert_html(html, convert_code_blocks=True)
        self.assertIn("```python", result)
        self.assertIn('print("Hello")', result)

    def test_adjust_internal_links(self):
        """Test adjusting internal links from HTML to Markdown."""
        from bs4 import BeautifulSoup

        html = '<a href="page.html">Link</a><a href="https://example.com">External</a>'
        soup = BeautifulSoup(html, "html.parser")
        adjust_internal_links(soup)
        result = str(soup)
        self.assertIn('href="page.md"', result)
        self.assertIn('href="https://example.com"', result)

    def test_extract_title(self):
        """Test extracting title from HTML."""
        from bs4 import BeautifulSoup

        html = "<html><head><title>Test Title</title></head><body></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        result = extract_title_from_html(soup)
        self.assertEqual(result, "Test Title")

        # Test extracting from h1 when no title
        html = "<html><head></head><body><h1>H1 Title</h1></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        result = extract_title_from_html(soup)
        self.assertEqual(result, "H1 Title")


class TestFrontmatterAndHeadings(unittest.TestCase):
    """Tests for frontmatter generation and heading adjustments."""

    def test_heading_offset(self):
        """Test heading level adjustment."""
        html = "<h1>Title</h1><h2>Subtitle</h2>"

        # Test increasing heading levels
        result = convert_html(html, heading_offset=1)
        self.assertIn("## Title", result)
        self.assertIn("### Subtitle", result)

        # Test decreasing heading levels
        result = convert_html("<h2>Title</h2><h3>Subtitle</h3>", heading_offset=-1)
        self.assertIn("# Title", result)
        self.assertIn("## Subtitle", result)


if __name__ == "__main__":
    unittest.main()
