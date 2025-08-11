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

"""Utility functions for mf1-html2md."""

import logging
from pathlib import Path
from typing import Optional

from ..shared.logging import (
    get_logger as shared_get_logger,
    configure_logging as shared_configure_logging,
)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return shared_get_logger(name)


def configure_logging(
    verbose: bool = False, quiet: bool = False, log_file: Optional[Path] = None
) -> None:
    """Configure logging for the application.

    Args:
        verbose: Enable verbose logging
        quiet: Suppress all but error messages
        log_file: Optional log file path
    """
    # Use the shared configure_logging function
    shared_configure_logging(verbose=verbose, quiet=quiet, log_file=log_file)

    # Suppress some noisy loggers specific to html2md
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def validate_url(url: str) -> bool:
    """Validate URL format.

    Args:
        url: URL to validate

    Returns:
        True if valid, False otherwise
    """
    from urllib.parse import urlparse

    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for filesystem.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    import re

    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)

    # Remove control characters
    filename = re.sub(r"[\x00-\x1f\x7f]", "", filename)

    # Limit length
    if len(filename) > 200:
        filename = filename[:200]

    # Ensure not empty
    if not filename:
        filename = "untitled"

    return filename


def format_size(size: int) -> str:
    """Format byte size to human readable format.

    Args:
        size: Size in bytes

    Returns:
        Formatted size string
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def convert_html(
    html_content: str,
    base_url: Optional[str] = None,
    convert_code_blocks: bool = False,
    heading_offset: int = 0,
) -> str:
    """Convert HTML content to Markdown.

    Args:
        html_content: HTML content as string
        base_url: Optional base URL for resolving relative links
        convert_code_blocks: Whether to convert code blocks to fenced style
        heading_offset: Offset to apply to heading levels

    Returns:
        Markdown content
    """
    from .config.models import ExtractorConfig, ProcessorConfig
    from .core import HTMLParser, MarkdownConverter

    # Create default configs
    extractor_config = ExtractorConfig()
    processor_config = ProcessorConfig()

    # Parse HTML
    parser = HTMLParser(extractor_config)
    soup = parser.parse(html_content, base_url)

    # Apply heading offset if needed
    if heading_offset != 0:
        # Collect all heading tags first to avoid processing them multiple times
        headings = []
        for i in range(1, 7):
            headings.extend([(tag, i) for tag in soup.find_all(f"h{i}")])

        # Now modify them
        for tag, level in headings:
            new_level = max(1, min(6, level + heading_offset))
            tag.name = f"h{new_level}"

    # Convert to Markdown
    converter = MarkdownConverter(processor_config)
    options = {}
    if convert_code_blocks:
        options["code_language"] = "python"
        options["code_block_style"] = "fenced"

    result = converter.convert(soup, options)

    # Handle code blocks if needed
    if convert_code_blocks:
        import re

        # Convert indented code blocks to fenced
        result = re.sub(r"^    (.+)$", r"```\n\1\n```", result, flags=re.MULTILINE)
        # Fix language-specific code blocks
        result = re.sub(
            r'```\n(.*?)class="language-(\w+)"(.*?)\n```',
            r"```\2\n\1\3\n```",
            result,
            flags=re.DOTALL,
        )

    return result


def adjust_internal_links(content, base_path: str = ""):
    """Adjust internal links in HTML/Markdown content.

    Args:
        content: BeautifulSoup object or Markdown string
        base_path: Base path for links

    Returns:
        Modified string if content is string, None if BeautifulSoup (modifies in place)
    """
    from bs4 import BeautifulSoup

    if isinstance(content, str):
        # If string is passed, work with markdown links
        import re

        # Pattern for markdown links
        link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

        def replace_link(match):
            text = match.group(1)
            url = match.group(2)

            # Skip external links
            if url.startswith(("http://", "https://", "#", "mailto:")):
                return match.group(0)

            # Adjust internal link
            if base_path and not url.startswith("/"):
                url = f"{base_path}/{url}"

            # Convert .html/.htm to .md
            if url.endswith(".html"):
                url = url[:-5] + ".md"
            elif url.endswith(".htm"):
                url = url[:-4] + ".md"

            return f"[{text}]({url})"

        return link_pattern.sub(replace_link, content)
    else:
        # Work with BeautifulSoup object - modify in place
        for link in content.find_all("a"):
            href = link.get("href")
            if href:
                # Skip external links
                if not href.startswith(("http://", "https://", "#", "mailto:")):
                    # Adjust internal link
                    if base_path and not href.startswith("/"):
                        href = f"{base_path}/{href}"

                    # Convert .html/.htm to .md
                    if href.endswith(".html"):
                        href = href[:-5] + ".md"
                    elif href.endswith(".htm"):
                        href = href[:-4] + ".md"

                    link["href"] = href


def extract_title_from_html(html_content) -> Optional[str]:
    """Extract title from HTML content.

    Args:
        html_content: HTML content as string or BeautifulSoup object

    Returns:
        Title if found, None otherwise
    """
    from bs4 import BeautifulSoup

    if isinstance(html_content, str):
        soup = BeautifulSoup(html_content, "html.parser")
    else:
        # Already a BeautifulSoup object
        soup = html_content

    # Try <title> tag first
    if title_tag := soup.find("title"):
        return title_tag.get_text(strip=True)

    # Try <h1> tag
    if h1_tag := soup.find("h1"):
        return h1_tag.get_text(strip=True)

    # Try meta title
    if meta_title := soup.find("meta", {"name": "title"}):
        if content := meta_title.get("content"):
            return content

    # Try og:title
    if og_title := soup.find("meta", {"property": "og:title"}):
        if content := og_title.get("content"):
            return content

    return None


def create_progress_bar():
    """Create a simple text-based progress indicator.

    Note: Rich progress bars are no longer used. This returns None
    and calling code should handle progress display differently.

    Returns:
        None
    """
    return None
