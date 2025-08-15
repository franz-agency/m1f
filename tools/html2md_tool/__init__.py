"""
HTML to Markdown Converter - Modern Web Content Extraction Tool

A powerful, modular tool for converting HTML content to Markdown format,
optimized for processing entire websites and integration with m1f.
"""

# Get version from package metadata
try:
    from importlib.metadata import version

    __version__ = version("m1f")
    __version_info__ = tuple(int(x) for x in __version__.split(".")[:3])
except Exception:
    # During development, version might not be available
    __version__ = "dev"
    __version_info__ = (0, 0, 0)

__author__ = "Franz und Franz (https://franz.agency)"

from html2md_tool.api import Html2mdConverter
from html2md_tool.config import Config, ConversionOptions
from html2md_tool.core import HTMLParser, MarkdownConverter
from html2md_tool.utils import (
    convert_html,
    adjust_internal_links,
    extract_title_from_html,
)

# Alias for backward compatibility
HTML2MDConverter = Html2mdConverter

__all__ = [
    "Html2mdConverter",
    "HTML2MDConverter",  # Alias
    "Config",
    "ConversionOptions",
    "HTMLParser",
    "MarkdownConverter",
    "convert_html",
    "adjust_internal_links",
    "extract_title_from_html",
]
