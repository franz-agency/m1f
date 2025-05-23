"""
HTML to Markdown Converter - Modern Web Content Extraction Tool

A powerful, modular tool for converting HTML content to Markdown format,
optimized for processing entire websites and integration with m1f.
"""

__version__ = "2.0.0"
__author__ = "Franz und Franz (https://franz.agency)"

from .api import Html2mdConverter
from .config import Config, ConversionOptions
from .core import HTMLParser, MarkdownConverter

__all__ = [
    "Html2mdConverter",
    "Config", 
    "ConversionOptions",
    "HTMLParser",
    "MarkdownConverter",
] 