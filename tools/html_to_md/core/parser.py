"""HTML parser with advanced content extraction capabilities."""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from bs4 import BeautifulSoup, Comment, NavigableString, Tag
from markdownify import markdownify

from ..config import ExtractorConfig
from ..utils.encoding import detect_encoding, normalize_encoding
from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class ParsedContent:
    """Container for parsed HTML content."""
    
    # Main content
    content: str
    title: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    opengraph: Dict[str, str] = field(default_factory=dict)
    schema_org: List[Dict[str, Any]] = field(default_factory=list)
    
    # Structure
    headings: List[Dict[str, Any]] = field(default_factory=list)
    links: List[Dict[str, str]] = field(default_factory=list)
    images: List[Dict[str, str]] = field(default_factory=list)
    
    # Encoding info
    original_encoding: Optional[str] = None
    detected_encoding: Optional[str] = None


class HTMLParser:
    """Advanced HTML parser with content extraction."""
    
    def __init__(self, config: ExtractorConfig):
        """Initialize parser with configuration.
        
        Args:
            config: Extractor configuration
        """
        self.config = config
        self._soup: Optional[BeautifulSoup] = None
    
    def parse(self, html: str, source_path: Optional[Path] = None) -> ParsedContent:
        """Parse HTML and extract content.
        
        Args:
            html: HTML content to parse
            source_path: Optional source file path for better error messages
            
        Returns:
            Parsed content with metadata
        """
        # Create BeautifulSoup object
        self._soup = BeautifulSoup(html, "html.parser")
        
        # Create result container
        result = ParsedContent(content="")
        
        # Extract metadata if configured
        if self.config.extract_metadata:
            result.metadata = self._extract_metadata()
            result.title = result.metadata.get("title")
        
        if self.config.extract_opengraph:
            result.opengraph = self._extract_opengraph()
        
        if self.config.extract_schema_org:
            result.schema_org = self._extract_schema_org()
        
        # Clean HTML before extraction
        self._clean_html()
        
        # Extract main content
        content_root = self._find_content_root()
        
        # Extract structural information
        result.headings = self._extract_headings(content_root)
        result.links = self._extract_links(content_root)
        result.images = self._extract_images(content_root)
        
        # Get the clean HTML for conversion
        if content_root:
            result.content = str(content_root)
        else:
            result.content = str(self._soup.body) if self._soup.body else str(self._soup)
        
        return result
    
    def parse_file(self, file_path: Path) -> ParsedContent:
        """Parse HTML file with encoding detection.
        
        Args:
            file_path: Path to HTML file
            
        Returns:
            Parsed content with metadata
        """
        # Detect encoding
        detected = detect_encoding(file_path)
        
        # Read file
        try:
            with open(file_path, "r", encoding=detected) as f:
                html = f.read()
        except UnicodeDecodeError:
            # Fallback to UTF-8 with replacement
            logger.warning(f"Encoding issues with {file_path}, using UTF-8 with replacement")
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                html = f.read()
            detected = "utf-8"
        
        # Parse content
        result = self.parse(html, file_path)
        result.detected_encoding = detected
        
        # Try to find declared encoding
        if self._soup:
            meta_charset = self._soup.find("meta", charset=True)
            if meta_charset:
                result.original_encoding = meta_charset.get("charset")
            else:
                meta_http_equiv = self._soup.find(
                    "meta", {"http-equiv": re.compile("content-type", re.I)}
                )
                if meta_http_equiv and meta_http_equiv.get("content"):
                    match = re.search(r"charset=([^;]+)", meta_http_equiv["content"])
                    if match:
                        result.original_encoding = match.group(1).strip()
        
        return result
    
    def _clean_html(self) -> None:
        """Clean HTML by removing unwanted elements."""
        if not self._soup:
            return
        
        # Remove specified elements
        for tag_name in self.config.remove_elements:
            for tag in self._soup.find_all(tag_name):
                tag.decompose()
        
        # Remove comments
        for comment in self._soup.find_all(string=lambda t: isinstance(t, Comment)):
            comment.extract()
        
        # Remove elements matching ignore selectors
        for selector in self.config.ignore_selectors:
            for element in self._soup.select(selector):
                element.decompose()
        
        # Strip attributes if configured
        if self.config.strip_attributes:
            for tag in self._soup.find_all(True):
                # Get current attributes
                current_attrs = dict(tag.attrs)
                
                # Clear all attributes
                tag.attrs.clear()
                
                # Restore preserved attributes
                for attr in self.config.preserve_attributes:
                    if attr in current_attrs:
                        tag.attrs[attr] = current_attrs[attr]
    
    def _find_content_root(self) -> Optional[Tag]:
        """Find the root element containing main content."""
        if not self._soup:
            return None
        
        # If a content selector is specified, use it
        if self.config.content_selector:
            content = self._soup.select_one(self.config.content_selector)
            if content:
                return content
            else:
                logger.warning(
                    f"Content selector '{self.config.content_selector}' not found"
                )
        
        # Try common content patterns
        content_patterns = [
            "main",
            "article",
            "[role='main']",
            "#content",
            ".content",
            "#main",
            ".main",
            ".post",
            ".entry-content",
            ".article-content",
        ]
        
        for pattern in content_patterns:
            content = self._soup.select_one(pattern)
            if content:
                return content
        
        # Fallback to body
        return self._soup.body
    
    def _extract_metadata(self) -> Dict[str, Any]:
        """Extract metadata from HTML head."""
        metadata = {}
        
        if not self._soup:
            return metadata
        
        # Title
        title_tag = self._soup.title
        if title_tag:
            metadata["title"] = title_tag.get_text(strip=True)
        
        # Meta tags
        for meta in self._soup.find_all("meta"):
            name = meta.get("name") or meta.get("property")
            content = meta.get("content")
            
            if name and content:
                # Clean up common prefixes
                if name.startswith(("og:", "twitter:", "article:")):
                    clean_name = name.split(":", 1)[1]
                else:
                    clean_name = name
                
                metadata[clean_name] = content
        
        # Canonical URL
        canonical = self._soup.find("link", rel="canonical")
        if canonical and canonical.get("href"):
            metadata["canonical_url"] = canonical["href"]
        
        # Language
        html_tag = self._soup.find("html")
        if html_tag and html_tag.get("lang"):
            metadata["language"] = html_tag["lang"]
        
        return metadata
    
    def _extract_opengraph(self) -> Dict[str, str]:
        """Extract OpenGraph metadata."""
        og_data = {}
        
        if not self._soup:
            return og_data
        
        for meta in self._soup.find_all("meta", property=re.compile("^og:")):
            prop = meta.get("property")
            content = meta.get("content")
            
            if prop and content:
                # Remove og: prefix
                key = prop[3:]
                og_data[key] = content
        
        return og_data
    
    def _extract_schema_org(self) -> List[Dict[str, Any]]:
        """Extract Schema.org structured data."""
        schema_data = []
        
        if not self._soup:
            return schema_data
        
        # Look for JSON-LD scripts
        for script in self._soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    schema_data.extend(data)
                else:
                    schema_data.append(data)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON-LD: {e}")
        
        return schema_data
    
    def _extract_headings(self, root: Optional[Tag]) -> List[Dict[str, Any]]:
        """Extract heading structure."""
        headings = []
        
        if not root:
            return headings
        
        for level in range(1, 7):
            for heading in root.find_all(f"h{level}"):
                headings.append({
                    "level": level,
                    "text": heading.get_text(strip=True),
                    "id": heading.get("id"),
                })
        
        return headings
    
    def _extract_links(self, root: Optional[Tag]) -> List[Dict[str, str]]:
        """Extract all links."""
        links = []
        
        if not root:
            return links
        
        for link in root.find_all("a", href=True):
            links.append({
                "href": link["href"],
                "text": link.get_text(strip=True),
                "title": link.get("title"),
            })
        
        return links
    
    def _extract_images(self, root: Optional[Tag]) -> List[Dict[str, str]]:
        """Extract all images."""
        images = []
        
        if not root:
            return images
        
        for img in root.find_all("img", src=True):
            images.append({
                "src": img["src"],
                "alt": img.get("alt", ""),
                "title": img.get("title"),
                "width": img.get("width"),
                "height": img.get("height"),
            })
        
        return images 