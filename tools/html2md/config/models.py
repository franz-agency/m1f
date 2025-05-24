"""Configuration models for html2md."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set


class OutputFormat(Enum):
    """Output format options."""
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"


@dataclass
class ConversionOptions:
    """Options for HTML to Markdown conversion."""
    strip_tags: List[str] = field(default_factory=lambda: ["script", "style"])
    keep_html_tags: List[str] = field(default_factory=list)
    code_language: str = ""
    heading_style: str = "atx"  # atx or setext
    bold_style: str = "**"  # ** or __
    italic_style: str = "*"  # * or _
    link_style: str = "inline"  # inline or reference
    list_marker: str = "-"  # -, *, or +
    code_block_style: str = "fenced"  # fenced or indented
    preserve_whitespace: bool = False
    wrap_width: int = 0  # 0 means no wrapping
    
    # Additional fields for test compatibility
    source_dir: Optional[str] = None
    destination_dir: Optional[Path] = None
    destination_directory: Optional[Path] = None  # Alias for destination_dir
    outermost_selector: Optional[str] = None
    ignore_selectors: Optional[List[str]] = None
    heading_offset: int = 0
    generate_frontmatter: bool = False
    add_frontmatter: bool = False  # Alias for generate_frontmatter
    frontmatter_fields: Optional[Dict[str, str]] = None
    convert_code_blocks: bool = True
    parallel: bool = False
    max_workers: int = 4
    
    def __post_init__(self):
        # Handle aliases
        if self.add_frontmatter:
            self.generate_frontmatter = True
        if self.destination_directory:
            self.destination_dir = self.destination_directory
            
    @classmethod
    def from_config_file(cls, path: Path) -> "ConversionOptions":
        """Load options from a configuration file."""
        import yaml
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Handle aliases in config file
        if 'source_directory' in data:
            data['source_dir'] = data.pop('source_directory')
        if 'destination_directory' in data:
            data['destination_dir'] = data.pop('destination_directory')
            
        return cls(**data)


@dataclass
class AssetConfig:
    """Configuration for asset handling."""
    download: bool = True
    directory: Path = Path("assets")
    max_size: int = 10 * 1024 * 1024  # 10MB
    allowed_types: Set[str] = field(default_factory=lambda: {
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "image/svg+xml", "application/pdf"
    })


@dataclass
class ExtractorConfig:
    """Configuration for HTML extraction."""
    parser: str = "html.parser"  # BeautifulSoup parser
    encoding: str = "utf-8"
    decode_errors: str = "ignore"
    prettify: bool = False


@dataclass
class ProcessorConfig:
    """Configuration for Markdown processing."""
    template: Optional[Path] = None
    metadata: Dict[str, str] = field(default_factory=dict)
    frontmatter: bool = False
    toc: bool = False
    toc_depth: int = 3


@dataclass
class CrawlerConfig:
    """Configuration for web crawling."""
    max_depth: int = 1
    follow_links: bool = False
    allowed_domains: Set[str] = field(default_factory=set)
    excluded_paths: Set[str] = field(default_factory=set)
    rate_limit: float = 1.0  # seconds between requests
    timeout: int = 30
    user_agent: str = "html2md/1.0"


@dataclass
class M1fConfig:
    """Configuration for M1F integration."""
    enabled: bool = False
    options: Dict[str, str] = field(default_factory=dict)


@dataclass
class Config:
    """Main configuration class."""
    source: Path
    destination: Path
    
    # Conversion options
    conversion: ConversionOptions = field(default_factory=ConversionOptions)
    
    # Component configs
    extractor: ExtractorConfig = field(default_factory=ExtractorConfig)
    processor: ProcessorConfig = field(default_factory=ProcessorConfig)
    assets: AssetConfig = field(default_factory=AssetConfig)
    crawler: CrawlerConfig = field(default_factory=CrawlerConfig)
    m1f: M1fConfig = field(default_factory=M1fConfig)
    
    # General options
    verbose: bool = False
    quiet: bool = False
    log_file: Optional[Path] = None
    dry_run: bool = False
    overwrite: bool = False
    
    # Processing options
    parallel: bool = True
    max_workers: int = 4
    chunk_size: int = 10