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

from tools.html2md_tool import (
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
    
    def test_table_of_contents_link_conversion(self):
        """Test that HTML links in content are converted to MD links."""
        from tools.html2md_tool.api import Html2mdConverter
        
        # Create HTML with table of contents - put links in main content, not nav
        # since nav elements are typically filtered out (which is correct behavior)
        toc_html = """<!DOCTYPE html>
        <html>
        <head>
            <title>Table of Contents</title>
        </head>
        <body>
            <h1>Documentation Index</h1>
            <main>
                <h2>Table of Contents</h2>
                <ul>
                    <li><a href="./getting-started.html">Getting Started Guide</a></li>
                    <li><a href="./installation.html">Installation</a></li>
                    <li><a href="./magazin/11/retargeting-reaktivierung-von-kaeufern-oder-haette-der-user-sowieso-gekauft.html">Retargeting Article</a></li>
                    <li><a href="../other-section/configuration.html">Configuration</a></li>
                    <li><a href="chapter1/introduction.htm">Introduction (HTM file)</a></li>
                    <li><a href="https://example.com/external.html">External Link (should not change)</a></li>
                    <li><a href="#section">Anchor Link (should not change)</a></li>
                    <li><a href="mailto:test@example.com">Email Link (should not change)</a></li>
                </ul>
                <h2>Quick Links</h2>
                <p>See also: <a href="./appendix.html">Appendix</a> and 
                   <a href="glossary.html">Glossary</a></p>
            </main>
        </body>
        </html>"""
        
        # Convert HTML to Markdown - using default config which filters nav but keeps main content
        converter = Html2mdConverter()
        markdown = converter.convert_html(toc_html)
        
        # Check that all internal .html links are converted to .md
        self.assertIn("[Getting Started Guide](./getting-started.md)", markdown)
        self.assertIn("[Installation](./installation.md)", markdown)
        self.assertIn("[Retargeting Article](./magazin/11/retargeting-reaktivierung-von-kaeufern-oder-haette-der-user-sowieso-gekauft.md)", markdown)
        self.assertIn("[Configuration](../other-section/configuration.md)", markdown)
        self.assertIn("[Introduction (HTM file)](chapter1/introduction.md)", markdown)  # .htm should also be converted
        self.assertIn("[Appendix](./appendix.md)", markdown)
        self.assertIn("[Glossary](glossary.md)", markdown)
        
        # Check that external links are NOT converted
        self.assertIn("[External Link (should not change)](https://example.com/external.html)", markdown)
        self.assertIn("[Anchor Link (should not change)](#section)", markdown)
        self.assertIn("[Email Link (should not change)](mailto:test@example.com)", markdown)
        
        # Ensure no .html or .htm links remain in the markdown (except external ones)
        lines = markdown.split('\n')
        for line in lines:
            # Skip lines with external links
            if 'https://' in line or 'http://' in line:
                continue
            # Check that no internal .html or .htm links remain
            if '](' in line and ('.html)' in line or '.htm)' in line):
                # This should only happen for external links
                self.assertTrue('https://' in line or 'http://' in line,
                              f"Found unconverted HTML link in line: {line}")

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
