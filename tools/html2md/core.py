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

"""Core HTML parsing and Markdown conversion functionality."""

import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, NavigableString, Tag
from markdownify import markdownify

from .config.models import ExtractorConfig, ProcessorConfig


class HTMLParser:
    """HTML parsing and extraction."""

    def __init__(self, config: ExtractorConfig):
        """Initialize parser with configuration."""
        self.config = config

    def parse(self, html: str, base_url: Optional[str] = None) -> BeautifulSoup:
        """Parse HTML content.

        Args:
            html: HTML content
            base_url: Base URL for resolving relative links

        Returns:
            BeautifulSoup object
        """
        soup = BeautifulSoup(html, self.config.parser)

        if base_url:
            self._resolve_urls(soup, base_url)

        if self.config.prettify:
            return BeautifulSoup(soup.prettify(), self.config.parser)

        return soup

    def parse_file(self, file_path) -> BeautifulSoup:
        """Parse HTML file.

        Args:
            file_path: Path to HTML file

        Returns:
            BeautifulSoup object
        """
        from pathlib import Path

        file_path = Path(file_path)

        # Read file with proper encoding detection
        encodings = [self.config.encoding, "utf-8", "latin-1", "cp1252"]
        html_content = None

        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    html_content = f.read()
                break
            except (UnicodeDecodeError, LookupError):
                continue

        if html_content is None:
            # Fallback: read as binary and decode with errors='ignore'
            with open(file_path, "rb") as f:
                html_content = f.read().decode(
                    self.config.encoding, errors=self.config.decode_errors
                )

        # Get base URL from file path for relative URL resolution
        base_url = file_path.as_uri()

        return self.parse(html_content, base_url)

    def _resolve_urls(self, soup: BeautifulSoup, base_url: str) -> None:
        """Resolve relative URLs to absolute.

        Args:
            soup: BeautifulSoup object
            base_url: Base URL
        """
        # Resolve links
        for tag in soup.find_all(["a", "link"]):
            if href := tag.get("href"):
                tag["href"] = urljoin(base_url, href)

        # Resolve images and other resources
        for tag in soup.find_all(["img", "script", "source"]):
            if src := tag.get("src"):
                tag["src"] = urljoin(base_url, src)

    def extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract metadata from HTML.

        Args:
            soup: BeautifulSoup object

        Returns:
            Dictionary of metadata
        """
        metadata = {}

        # Title
        if title := soup.find("title"):
            metadata["title"] = title.get_text(strip=True)

        # Meta tags
        for meta in soup.find_all("meta"):
            if name := meta.get("name"):
                if content := meta.get("content"):
                    metadata[name] = content
            elif prop := meta.get("property"):
                if content := meta.get("content"):
                    metadata[prop] = content

        return metadata


class MarkdownConverter:
    """Convert HTML to Markdown."""

    def __init__(self, config: ProcessorConfig):
        """Initialize converter with configuration."""
        self.config = config

    def convert(
        self, soup: BeautifulSoup, options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Convert BeautifulSoup object to Markdown.

        Args:
            soup: BeautifulSoup object
            options: Additional conversion options

        Returns:
            Markdown content
        """
        # Pre-process code blocks to preserve language info
        for code_block in soup.find_all("code"):
            if code_block.parent and code_block.parent.name == "pre":
                # Get language from class
                classes = code_block.get("class", [])
                for cls in classes:
                    if cls.startswith("language-"):
                        lang = cls.replace("language-", "")
                        # Add language marker
                        code_block.string = f"```{lang}\n{code_block.get_text()}\n```"
                        code_block.parent.unwrap()  # Remove pre tag
                        break

        # Merge options
        opts = {
            "heading_style": "atx",
            "bullets": "-",
            "code_language": "",
            "strip": ["script", "style"],
        }
        if options:
            opts.update(options)

        # Convert to markdown
        markdown = markdownify(str(soup), **opts)

        # Post-process
        markdown = self._post_process(markdown)

        # Add frontmatter if enabled
        if self.config.frontmatter and self.config.metadata:
            markdown = self._add_frontmatter(markdown)

        # Add TOC if enabled
        if self.config.toc:
            markdown = self._add_toc(markdown)

        return markdown

    def _post_process(self, markdown: str) -> str:
        """Post-process markdown content.

        Args:
            markdown: Raw markdown

        Returns:
            Processed markdown
        """
        # Remove excessive blank lines
        markdown = re.sub(r"\n{3,}", "\n\n", markdown)

        # Fix spacing around headings
        markdown = re.sub(r"(^|\n)(#{1,6})\s+", r"\1\n\2 ", markdown)

        # Ensure single blank line before headings
        markdown = re.sub(r"([^\n])\n(#{1,6})\s+", r"\1\n\n\2 ", markdown)

        # Fix list formatting
        markdown = re.sub(r"(\n\s*[-*+]\s+)", r"\n\1", markdown)

        # Trim
        return markdown.strip()

    def _add_frontmatter(self, markdown: str) -> str:
        """Add frontmatter to markdown.

        Args:
            markdown: Markdown content

        Returns:
            Markdown with frontmatter
        """
        import yaml

        frontmatter = yaml.dump(self.config.metadata, default_flow_style=False)
        return f"---\n{frontmatter}---\n\n{markdown}"

    def _add_toc(self, markdown: str) -> str:
        """Add table of contents to markdown.

        Args:
            markdown: Markdown content

        Returns:
            Markdown with TOC
        """
        toc_lines = ["## Table of Contents\n"]

        # Extract headings
        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

        for match in heading_pattern.finditer(markdown):
            level = len(match.group(1))
            if level <= self.config.toc_depth:
                title = match.group(2)
                indent = "  " * (level - 1)
                anchor = re.sub(r"[^\w\s-]", "", title.lower())
                anchor = re.sub(r"\s+", "-", anchor)
                toc_lines.append(f"{indent}- [{title}](#{anchor})")

        if len(toc_lines) > 1:
            toc = "\n".join(toc_lines) + "\n\n"
            return toc + markdown

        return markdown
