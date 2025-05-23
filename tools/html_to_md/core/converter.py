"""Markdown converter with advanced formatting options."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag
from markdownify import MarkdownConverter as BaseConverter

from ..config import HeadingStyle, LinkHandling, ProcessorConfig
from ..utils.logging_utils import get_logger
from .parser import ParsedContent

logger = get_logger(__name__)


class CustomMarkdownConverter(BaseConverter):
    """Custom markdownify converter with enhanced features."""
    
    def __init__(self, config: ProcessorConfig, base_url: Optional[str] = None, **options):
        """Initialize converter with custom options.
        
        Args:
            config: Processor configuration
            base_url: Base URL for resolving relative links
            **options: Additional markdownify options
        """
        self.config = config
        self.base_url = base_url
        
        # Set default options based on config
        options.setdefault("heading_style", config.heading_style.value)
        options.setdefault("bullets", config.unordered_list_style)
        options.setdefault("code_language_callback", self._detect_code_language)
        
        super().__init__(**options)
    
    def convert_a(self, el: Tag, text: str, convert_as_inline: bool) -> str:
        """Convert anchor tags with link handling."""
        href = el.get("href", "")
        title = el.get("title")
        
        if not href:
            return text
        
        # Handle link based on configuration
        if self.config.link_handling == LinkHandling.CONVERT:
            href = self._convert_link_extension(href)
        elif self.config.link_handling == LinkHandling.ABSOLUTE and self.base_url:
            href = urljoin(self.base_url, href)
        elif self.config.link_handling == LinkHandling.RELATIVE and self.base_url:
            href = self._make_relative(href, self.base_url)
        
        # Format link
        if title:
            return f'[{text}]({href} "{title}")'
        else:
            return f'[{text}]({href})'
    
    def convert_img(self, el: Tag, text: str, convert_as_inline: bool) -> str:
        """Convert image tags."""
        src = el.get("src", "")
        alt = el.get("alt", "")
        title = el.get("title")
        
        if not src:
            return ""
        
        # Handle image URL based on link handling config
        if self.config.link_handling == LinkHandling.ABSOLUTE and self.base_url:
            src = urljoin(self.base_url, src)
        elif self.config.link_handling == LinkHandling.RELATIVE and self.base_url:
            src = self._make_relative(src, self.base_url)
        
        # Format image
        if title:
            return f'![{alt}]({src} "{title}")'
        else:
            return f'![{alt}]({src})'
    
    def convert_pre(self, el: Tag, text: str, convert_as_inline: bool) -> str:
        """Convert pre tags with code block detection."""
        if self.config.code_block_style != "fenced":
            # Use indented code blocks
            return "\n" + "\n".join("    " + line for line in text.split("\n")) + "\n"
        
        # Check for code tag inside pre
        code = el.find("code")
        if code and self.config.detect_language:
            lang = self._detect_code_language(code)
            if lang:
                return f"\n```{lang}\n{text}\n```\n"
        
        return f"\n```\n{text}\n```\n"
    
    def _detect_code_language(self, el: Tag) -> Optional[str]:
        """Detect programming language from code element."""
        if not self.config.detect_language:
            return None
        
        # Check class attribute
        classes = el.get("class", [])
        for cls in classes:
            # Common patterns: language-python, lang-js, hljs-python
            if cls.startswith(("language-", "lang-", "hljs-")):
                return cls.split("-", 1)[1]
        
        # Check data attributes
        if el.get("data-language"):
            return el["data-language"]
        
        return None
    
    def _convert_link_extension(self, href: str) -> str:
        """Convert link extensions based on mapping."""
        parsed = urlparse(href)
        
        # Skip external links or fragments
        if parsed.scheme or href.startswith("#"):
            return href
        
        path = Path(parsed.path)
        
        # Check if extension should be converted
        if path.suffix.lower() in self.config.link_extensions:
            new_suffix = self.config.link_extensions[path.suffix.lower()]
            new_path = path.with_suffix(new_suffix).as_posix()
            
            # Preserve fragment
            if parsed.fragment:
                new_path += f"#{parsed.fragment}"
            
            return new_path
        
        return href
    
    def _make_relative(self, url: str, base: str) -> str:
        """Make URL relative to base."""
        # This is a simplified implementation
        # In production, you'd want more robust relative path calculation
        if url.startswith(base):
            return url[len(base):].lstrip("/")
        return url


class MarkdownConverter:
    """Main converter for HTML to Markdown with post-processing."""
    
    def __init__(self, config: ProcessorConfig):
        """Initialize converter.
        
        Args:
            config: Processor configuration
        """
        self.config = config
    
    def convert(
        self,
        parsed_content: ParsedContent,
        base_url: Optional[str] = None,
        add_frontmatter: bool = True
    ) -> str:
        """Convert parsed HTML content to Markdown.
        
        Args:
            parsed_content: Parsed HTML content
            base_url: Base URL for link resolution
            add_frontmatter: Whether to add YAML frontmatter
            
        Returns:
            Markdown content
        """
        # Apply heading offset if needed
        if self.config.heading_offset != 0:
            html = self._adjust_heading_levels(parsed_content.content)
        else:
            html = parsed_content.content
        
        # Convert to markdown
        converter = CustomMarkdownConverter(self.config, base_url)
        markdown = converter.convert(html)
        
        # Post-process markdown
        markdown = self._post_process(markdown)
        
        # Add frontmatter if requested
        if add_frontmatter:
            frontmatter = self._create_frontmatter(parsed_content)
            markdown = frontmatter + markdown
        
        return markdown
    
    def _adjust_heading_levels(self, html: str) -> str:
        """Adjust heading levels in HTML."""
        soup = BeautifulSoup(html, "html.parser")
        
        # Process headings in the correct order
        if self.config.heading_offset > 0:
            # When increasing levels, process in reverse to avoid cascading
            for level in range(6, 0, -1):
                new_level = min(6, level + self.config.heading_offset)
                for heading in soup.find_all(f"h{level}"):
                    heading.name = f"h{new_level}"
        else:
            # When decreasing levels, process normally
            for level in range(1, 7):
                new_level = max(1, level + self.config.heading_offset)
                for heading in soup.find_all(f"h{level}"):
                    heading.name = f"h{new_level}"
        
        return str(soup)
    
    def _post_process(self, markdown: str) -> str:
        """Post-process markdown content."""
        # Normalize whitespace if configured
        if self.config.normalize_whitespace:
            # Remove trailing whitespace
            markdown = "\n".join(line.rstrip() for line in markdown.split("\n"))
            
            # Normalize multiple blank lines
            markdown = re.sub(r"\n{3,}", "\n\n", markdown)
            
            # Ensure single newline at end
            markdown = markdown.rstrip() + "\n"
        
        # Fix common encoding issues if configured
        if self.config.fix_encoding:
            # Common replacements
            replacements = {
                """: '"',
                """: '"',
                "'": "'",
                "'": "'",
                "–": "-",
                "—": "--",
                "…": "...",
                " ": " ",  # non-breaking space
            }
            
            for old, new in replacements.items():
                markdown = markdown.replace(old, new)
        
        # Add line breaks between blocks if configured
        if self.config.line_breaks_between_blocks:
            # Add blank line before headings
            markdown = re.sub(r"(?<!\n)\n(#{1,6} )", r"\n\n\1", markdown)
            
            # Add blank line before lists
            markdown = re.sub(r"(?<!\n)\n([-*+] |\d+\. )", r"\n\n\1", markdown)
            
            # Add blank line before blockquotes
            markdown = re.sub(r"(?<!\n)\n(> )", r"\n\n\1", markdown)
            
            # Add blank line before code blocks
            markdown = re.sub(r"(?<!\n)\n(```)", r"\n\n\1", markdown)
        
        return markdown
    
    def _create_frontmatter(self, parsed_content: ParsedContent) -> str:
        """Create YAML frontmatter from parsed content."""
        frontmatter = {}
        
        # Add title
        if parsed_content.title:
            frontmatter["title"] = parsed_content.title
        
        # Add relevant metadata
        if parsed_content.metadata:
            # Select useful metadata fields
            useful_fields = {
                "description", "author", "date", "keywords",
                "canonical_url", "language"
            }
            
            for field in useful_fields:
                if field in parsed_content.metadata:
                    frontmatter[field] = parsed_content.metadata[field]
        
        # Add OpenGraph data if available
        if parsed_content.opengraph:
            # Map OpenGraph to frontmatter
            og_mapping = {
                "title": "og_title",
                "description": "og_description",
                "image": "og_image",
                "type": "og_type",
            }
            
            for og_field, fm_field in og_mapping.items():
                if og_field in parsed_content.opengraph:
                    frontmatter[fm_field] = parsed_content.opengraph[og_field]
        
        # Add encoding info if different from UTF-8
        if parsed_content.original_encoding and parsed_content.original_encoding.lower() != "utf-8":
            frontmatter["original_encoding"] = parsed_content.original_encoding
        
        # Format as YAML
        if not frontmatter:
            return ""
        
        lines = ["---"]
        for key, value in frontmatter.items():
            if isinstance(value, str) and (":" in value or "\n" in value):
                # Quote strings containing colons or newlines
                value = f'"{value}"'
            lines.append(f"{key}: {value}")
        lines.append("---")
        lines.append("")  # Empty line after frontmatter
        
        return "\n".join(lines) + "\n" 