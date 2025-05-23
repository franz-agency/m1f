"""Configuration models using Pydantic for validation and serialization."""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field, field_validator, ConfigDict


class OutputFormat(str, Enum):
    """Supported output formats."""
    MARKDOWN = "markdown"
    M1F_BUNDLE = "m1f_bundle"
    JSON = "json"


class HeadingStyle(str, Enum):
    """Markdown heading styles."""
    ATX = "atx"  # # Heading
    SETEXT = "setext"  # Heading\n======


class LinkHandling(str, Enum):
    """How to handle links in the conversion."""
    PRESERVE = "preserve"  # Keep original links
    CONVERT = "convert"  # Convert .html to .md
    ABSOLUTE = "absolute"  # Make all links absolute
    RELATIVE = "relative"  # Make all links relative


class ExtractorConfig(BaseModel):
    """Configuration for content extractors."""
    
    model_config = ConfigDict(extra="forbid")
    
    # CSS selectors
    content_selector: Optional[str] = Field(
        None,
        description="CSS selector for main content area"
    )
    ignore_selectors: List[str] = Field(
        default_factory=list,
        description="CSS selectors for elements to ignore"
    )
    
    # Element handling
    remove_elements: Set[str] = Field(
        default_factory=lambda: {"script", "style", "iframe", "noscript"},
        description="HTML elements to remove completely"
    )
    preserve_elements: Set[str] = Field(
        default_factory=set,
        description="HTML elements to preserve as-is"
    )
    
    # Attribute handling
    strip_attributes: bool = Field(
        True,
        description="Whether to strip HTML attributes"
    )
    preserve_attributes: Set[str] = Field(
        default_factory=lambda: {"id", "href", "src", "alt"},
        description="Attributes to preserve when stripping"
    )
    
    # Content extraction
    extract_metadata: bool = Field(
        True,
        description="Extract metadata from HTML head"
    )
    extract_opengraph: bool = Field(
        True,
        description="Extract OpenGraph metadata"
    )
    extract_schema_org: bool = Field(
        True,
        description="Extract Schema.org structured data"
    )


class ProcessorConfig(BaseModel):
    """Configuration for post-processors."""
    
    model_config = ConfigDict(extra="forbid")
    
    # Text processing
    normalize_whitespace: bool = Field(
        True,
        description="Normalize whitespace in output"
    )
    fix_encoding: bool = Field(
        True,
        description="Fix common encoding issues"
    )
    
    # Markdown formatting
    heading_offset: int = Field(
        0,
        ge=-6,
        le=6,
        description="Offset to apply to heading levels"
    )
    heading_style: HeadingStyle = Field(
        HeadingStyle.ATX,
        description="Markdown heading style"
    )
    
    # Code blocks
    code_block_style: str = Field(
        "fenced",
        description="Code block style: fenced or indented"
    )
    detect_language: bool = Field(
        True,
        description="Try to detect code language from classes"
    )
    
    # Links
    link_handling: LinkHandling = Field(
        LinkHandling.CONVERT,
        description="How to handle links"
    )
    link_extensions: Dict[str, str] = Field(
        default_factory=lambda: {".html": ".md", ".htm": ".md"},
        description="Extension mappings for link conversion"
    )
    
    # Lists
    unordered_list_style: str = Field(
        "-",
        description="Character for unordered lists: -, *, or +"
    )
    
    # Line breaks
    line_breaks_between_blocks: bool = Field(
        True,
        description="Add line breaks between block elements"
    )


class CrawlerConfig(BaseModel):
    """Configuration for web crawling."""
    
    model_config = ConfigDict(extra="forbid")
    
    # Crawling behavior
    follow_links: bool = Field(
        True,
        description="Follow links to crawl entire site"
    )
    max_depth: Optional[int] = Field(
        None,
        ge=0,
        description="Maximum crawl depth"
    )
    max_pages: Optional[int] = Field(
        None,
        ge=1,
        description="Maximum number of pages to crawl"
    )
    
    # URL handling
    allowed_domains: Set[str] = Field(
        default_factory=set,
        description="Domains allowed for crawling"
    )
    url_patterns: List[str] = Field(
        default_factory=list,
        description="Regex patterns for URLs to include"
    )
    exclude_patterns: List[str] = Field(
        default_factory=list,
        description="Regex patterns for URLs to exclude"
    )
    
    # Sitemap
    use_sitemap: bool = Field(
        True,
        description="Use sitemap.xml if available"
    )
    sitemap_urls: List[str] = Field(
        default_factory=list,
        description="Additional sitemap URLs"
    )
    
    # robots.txt
    respect_robots_txt: bool = Field(
        True,
        description="Respect robots.txt rules"
    )
    
    # Performance
    concurrent_requests: int = Field(
        5,
        ge=1,
        le=50,
        description="Number of concurrent requests"
    )
    request_delay: float = Field(
        0.1,
        ge=0,
        description="Delay between requests in seconds"
    )
    timeout: float = Field(
        30.0,
        ge=1.0,
        description="Request timeout in seconds"
    )
    
    # User agent
    user_agent: str = Field(
        "html_to_md/2.0 (https://github.com/franzundfraz/m1f)",
        description="User agent string"
    )
    
    @field_validator("allowed_domains")
    @classmethod
    def normalize_domains(cls, v: Set[str]) -> Set[str]:
        """Normalize domain names."""
        return {domain.lower().strip() for domain in v}


class AssetConfig(BaseModel):
    """Configuration for asset handling."""
    
    model_config = ConfigDict(extra="forbid")
    
    download_assets: bool = Field(
        False,
        description="Download images and other assets"
    )
    asset_types: Set[str] = Field(
        default_factory=lambda: {"image", "video", "audio"},
        description="Types of assets to download"
    )
    asset_extensions: Set[str] = Field(
        default_factory=lambda: {
            ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg",
            ".mp4", ".webm", ".mp3", ".wav"
        },
        description="File extensions to consider as assets"
    )
    max_asset_size: Optional[int] = Field(
        10 * 1024 * 1024,  # 10MB
        description="Maximum asset size in bytes"
    )
    asset_dir: str = Field(
        "assets",
        description="Directory name for downloaded assets"
    )


class M1FConfig(BaseModel):
    """Configuration for m1f integration."""
    
    model_config = ConfigDict(extra="forbid")
    
    create_bundle: bool = Field(
        False,
        description="Create m1f bundle after conversion"
    )
    bundle_name: Optional[str] = Field(
        None,
        description="Name for the m1f bundle"
    )
    chunk_size: Optional[int] = Field(
        None,
        description="Maximum chunk size for large sites"
    )
    include_assets: bool = Field(
        True,
        description="Include assets in m1f bundle"
    )
    generate_index: bool = Field(
        True,
        description="Generate index file for navigation"
    )
    
    # m1f specific metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for m1f bundle"
    )


class ConversionOptions(BaseModel):
    """Main configuration for HTML to Markdown conversion."""
    
    model_config = ConfigDict(extra="forbid")
    
    # Input/Output
    source: Path = Field(
        ...,
        description="Source directory or URL"
    )
    destination: Path = Field(
        ...,
        description="Destination directory"
    )
    output_format: OutputFormat = Field(
        OutputFormat.MARKDOWN,
        description="Output format"
    )
    
    # File handling
    file_extensions: Set[str] = Field(
        default_factory=lambda: {".html", ".htm", ".xhtml"},
        description="File extensions to process"
    )
    exclude_patterns: List[str] = Field(
        default_factory=list,
        description="Glob patterns to exclude"
    )
    force_overwrite: bool = Field(
        False,
        description="Overwrite existing files"
    )
    
    # Encoding
    source_encoding: Optional[str] = Field(
        None,
        description="Force source encoding"
    )
    target_encoding: str = Field(
        "utf-8",
        description="Target file encoding"
    )
    
    # Sub-configurations
    extractor: ExtractorConfig = Field(
        default_factory=ExtractorConfig,
        description="Content extraction settings"
    )
    processor: ProcessorConfig = Field(
        default_factory=ProcessorConfig,
        description="Post-processing settings"
    )
    crawler: CrawlerConfig = Field(
        default_factory=CrawlerConfig,
        description="Web crawling settings"
    )
    assets: AssetConfig = Field(
        default_factory=AssetConfig,
        description="Asset handling settings"
    )
    m1f: M1FConfig = Field(
        default_factory=M1FConfig,
        description="m1f integration settings"
    )
    
    # Processing
    parallel: bool = Field(
        True,
        description="Enable parallel processing"
    )
    max_workers: Optional[int] = Field(
        None,
        description="Maximum worker processes"
    )
    
    # Logging
    verbose: bool = Field(
        False,
        description="Enable verbose output"
    )
    quiet: bool = Field(
        False,
        description="Suppress output"
    )
    log_file: Optional[Path] = Field(
        None,
        description="Log file path"
    )
    
    @field_validator("source")
    @classmethod
    def validate_source(cls, v: Path) -> Path:
        """Validate source path or URL."""
        # Check if it's a URL
        if str(v).startswith(("http://", "https://")):
            return v
        # Otherwise check if path exists
        if not v.exists():
            raise ValueError(f"Source path does not exist: {v}")
        return v.resolve()
    
    @field_validator("destination")
    @classmethod
    def validate_destination(cls, v: Path) -> Path:
        """Ensure destination directory can be created."""
        return v.resolve() 