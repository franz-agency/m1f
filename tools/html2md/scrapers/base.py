"""Abstract base class for web scrapers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, AsyncGenerator, Set
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class ScraperConfig:
    """Configuration for web scrapers."""
    max_depth: int = 10
    max_pages: int = 1000
    allowed_domains: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None
    respect_robots_txt: bool = True
    concurrent_requests: int = 5
    request_delay: float = 0.5
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    custom_headers: Optional[Dict[str, str]] = None
    timeout: float = 30.0
    follow_redirects: bool = True
    verify_ssl: bool = True
    
    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.allowed_domains is None:
            self.allowed_domains = []
        if self.exclude_patterns is None:
            self.exclude_patterns = []
        if self.custom_headers is None:
            self.custom_headers = {}

@dataclass
class ScrapedPage:
    """Represents a scraped web page."""
    url: str
    content: str
    title: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    encoding: str = "utf-8"
    status_code: Optional[int] = None
    headers: Optional[Dict[str, str]] = None
    
    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.metadata is None:
            self.metadata = {}
        if self.headers is None:
            self.headers = {}

class WebScraperBase(ABC):
    """Abstract base class for web scrapers."""
    
    def __init__(self, config: ScraperConfig):
        """Initialize the scraper with configuration.
        
        Args:
            config: Scraper configuration
        """
        self.config = config
        self._visited_urls: Set[str] = set()
        
    @abstractmethod
    async def scrape_url(self, url: str) -> ScrapedPage:
        """Scrape a single URL.
        
        Args:
            url: URL to scrape
            
        Returns:
            ScrapedPage object containing the scraped content
            
        Raises:
            Exception: If scraping fails
        """
        pass
    
    @abstractmethod
    async def scrape_site(self, start_url: str) -> AsyncGenerator[ScrapedPage, None]:
        """Scrape an entire website starting from a URL.
        
        Args:
            start_url: URL to start crawling from
            
        Yields:
            ScrapedPage objects as they are scraped
        """
        pass
    
    def validate_url(self, url: str) -> bool:
        """Validate if a URL should be scraped based on configuration.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL should be scraped, False otherwise
        """
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(url)
            
            # Check if URL has valid scheme
            if parsed.scheme not in ('http', 'https'):
                return False
            
            # Check allowed domains
            if self.config.allowed_domains:
                domain_allowed = False
                for domain in self.config.allowed_domains:
                    if domain in parsed.netloc:
                        domain_allowed = True
                        break
                if not domain_allowed:
                    return False
            
            # Check exclude patterns
            if self.config.exclude_patterns:
                for pattern in self.config.exclude_patterns:
                    if pattern in url:
                        logger.debug(f"URL {url} excluded by pattern: {pattern}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating URL {url}: {e}")
            return False
    
    def is_visited(self, url: str) -> bool:
        """Check if URL has already been visited.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL has been visited, False otherwise
        """
        return url in self._visited_urls
    
    def mark_visited(self, url: str) -> None:
        """Mark URL as visited.
        
        Args:
            url: URL to mark as visited
        """
        self._visited_urls.add(url)
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass