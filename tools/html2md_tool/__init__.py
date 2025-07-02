"""
HTML to Markdown Converter - Modern Web Content Extraction Tool

A powerful, modular tool for converting HTML content to Markdown format,
optimized for processing entire websites and integration with m1f.
"""

try:
    from .._version import __version__, __version_info__
except ImportError:
    # Fallback when running as standalone script
    __version__ = "3.3.0"
    __version_info__ = (3, 3, 0)

__author__ = "Franz und Franz (https://franz.agency)"

from .api import Html2mdConverter
from .config import Config, ConversionOptions
from .core import HTMLParser, MarkdownConverter
from .utils import convert_html, adjust_internal_links, extract_title_from_html

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
