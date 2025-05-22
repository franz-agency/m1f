#!/usr/bin/env python3
"""
Integration tests for HTML to Markdown conversion with prepare_docs.py.
"""
import os
import sys
import unittest
import tempfile
import shutil
import subprocess
from pathlib import Path

# Add the parent directory to sys.path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


class TestIntegration(unittest.TestCase):
    """Integration tests for HTML to Markdown conversion tools."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary directories for test
        self.test_dir = Path(tempfile.mkdtemp())
        self.html_dir = self.test_dir / "html"
        self.html_dir.mkdir()
        self.md_dir = self.test_dir / "markdown"
        self.md_dir.mkdir()

        # Copy the sample HTML file to the test directory
        src_html = Path(__file__).parent / "source" / "html" / "sample.html"
        if src_html.exists():
            self.sample_html_path = self.html_dir / "sample.html"
            shutil.copy(src_html, self.sample_html_path)
        else:
            self.skipTest(f"Source HTML file not found: {src_html}")

        # Find the tools directory
        self.tools_dir = Path(__file__).parents[2] / "tools"
        self.html_to_md_script = self.tools_dir / "html_to_md.py"
        self.prepare_docs_script = self.tools_dir / "prepare_docs.py"

        if not self.html_to_md_script.exists():
            self.skipTest(f"html_to_md.py script not found: {self.html_to_md_script}")

        if not self.prepare_docs_script.exists():
            self.skipTest(
                f"prepare_docs.py script not found: {self.prepare_docs_script}"
            )

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)

    def test_direct_conversion(self):
        """Test direct conversion with html_to_md.py."""
        cmd = [
            sys.executable,
            str(self.html_to_md_script),
            "--source-dir",
            str(self.html_dir),
            "--destination-dir",
            str(self.md_dir),
            "--add-frontmatter",
            "--convert-code-blocks",
            "--force",
        ]

        # Run the command
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        # Check that the command completed successfully
        self.assertEqual(result.returncode, 0)

        # Check that the output file was created
        output_file = self.md_dir / "sample.md"
        self.assertTrue(output_file.exists())

        # Check that the content contains key elements
        content = output_file.read_text()
        self.assertIn("# HTML to Markdown Conversion Example", content)
        self.assertIn("```python", content)
        self.assertIn("```javascript", content)
        self.assertIn("| Name | Description | Value |", content)

        # Check that links were converted
        self.assertIn("another-page.md", content)
        self.assertIn("details.md", content)

        # Check that unwanted elements were removed
        self.assertNotIn("<script>", content)
        self.assertNotIn("<style>", content)

    def test_html_structure_preservation(self):
        """Test that the HTML structure is properly preserved in Markdown."""
        # Convert the HTML
        cmd = [
            sys.executable,
            str(self.html_to_md_script),
            "--source-dir",
            str(self.html_dir),
            "--destination-dir",
            str(self.md_dir),
            "--outermost-selector",
            "main.content",  # Only convert main content
            "--ignore-selectors",
            "nav",
            "footer",
            ".advertisement",
            "--add-frontmatter",
            "--force",
        ]

        # Run the command
        subprocess.run(cmd, check=True, capture_output=True, text=True)

        # Check output
        output_file = self.md_dir / "sample.md"
        content = output_file.read_text()

        # Check heading structure
        self.assertIn("# HTML to Markdown Conversion Example", content)
        self.assertIn("## Text Formatting", content)
        self.assertIn("### Unordered List", content)

        # Check that only main content was included
        self.assertNotIn("Related Links", content)  # From sidebar
        self.assertNotIn("Home", content)  # From nav
        self.assertNotIn("All rights reserved", content)  # From footer

    def test_code_block_language_detection(self):
        """Test that code block languages are properly detected."""
        # Convert the HTML
        cmd = [
            sys.executable,
            str(self.html_to_md_script),
            "--source-dir",
            str(self.html_dir),
            "--destination-dir",
            str(self.md_dir),
            "--convert-code-blocks",
            "--force",
        ]

        # Run the command
        subprocess.run(cmd, check=True, capture_output=True, text=True)

        # Check output
        output_file = self.md_dir / "sample.md"
        content = output_file.read_text()

        # Verify python code block
        python_index = content.find("```python")
        self.assertGreater(python_index, 0)
        self.assertIn(
            'print("Hello, world!")', content[python_index : python_index + 200]
        )

        # Verify javascript code block
        js_index = content.find("```javascript")
        self.assertGreater(js_index, 0)
        self.assertIn("function calculateSum", content[js_index : js_index + 200])


if __name__ == "__main__":
    unittest.main()
