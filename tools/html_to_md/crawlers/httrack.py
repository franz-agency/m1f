"""HTTrack wrapper for website mirroring."""

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

from ..config import CrawlerConfig
from ..utils import get_logger

logger = get_logger(__name__)


class HTTrackCrawler:
    """Wrapper around HTTrack for website mirroring."""
    
    def __init__(self, config: CrawlerConfig):
        """Initialize HTTrack crawler.
        
        Args:
            config: Crawler configuration
        """
        self.config = config
        self._check_httrack()
    
    def _check_httrack(self) -> None:
        """Check if HTTrack is installed."""
        if not shutil.which("httrack"):
            raise RuntimeError(
                "HTTrack is not installed. Please install it:\n"
                "  Ubuntu/Debian: sudo apt-get install httrack\n"
                "  macOS: brew install httrack\n"
                "  Windows: Download from https://www.httrack.com/"
            )
    
    def crawl(self, start_url: str, output_dir: Path) -> Path:
        """Crawl a website using HTTrack.
        
        Args:
            start_url: Starting URL for crawling
            output_dir: Directory to save the mirrored website
            
        Returns:
            Path to the mirrored website directory
        """
        logger.info(f"Starting HTTrack crawl of {start_url}")
        
        # Parse URL to get domain
        parsed = urlparse(start_url)
        domain = parsed.netloc
        
        # Create temporary directory for HTTrack
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Build HTTrack command
            cmd = self._build_httrack_command(start_url, temp_path)
            
            # Run HTTrack
            logger.debug(f"Running HTTrack command: {' '.join(cmd)}")
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                logger.debug(f"HTTrack output: {result.stdout}")
                
            except subprocess.CalledProcessError as e:
                logger.error(f"HTTrack failed: {e.stderr}")
                raise RuntimeError(f"HTTrack failed: {e.stderr}")
            
            # Find the mirrored site directory
            site_dir = self._find_site_directory(temp_path, domain)
            
            if not site_dir:
                raise RuntimeError(f"Could not find mirrored site for {domain}")
            
            # Move to output directory
            output_path = output_dir / domain
            if output_path.exists():
                import shutil
                shutil.rmtree(output_path)
            
            shutil.move(str(site_dir), str(output_path))
            
            logger.info(f"Website mirrored to {output_path}")
            return output_path
    
    def _build_httrack_command(self, start_url: str, output_dir: Path) -> List[str]:
        """Build HTTrack command with configuration options.
        
        Args:
            start_url: Starting URL
            output_dir: Output directory
            
        Returns:
            Command arguments list
        """
        cmd = [
            "httrack",
            start_url,
            "-O", str(output_dir),  # Output directory
            "-q",  # Quiet mode
            "-%v",  # Less verbose
        ]
        
        # Add depth limit
        if self.config.max_depth:
            cmd.extend(["-r", str(self.config.max_depth)])
        
        # Add page limit
        if self.config.max_pages:
            cmd.extend(["-m", str(self.config.max_pages * 1000)])  # HTTrack uses bytes
        
        # robots.txt handling
        if self.config.respect_robots_txt:
            cmd.append("-s0")  # Respect robots.txt
        else:
            cmd.append("-s2")  # Ignore robots.txt
        
        # User agent
        if self.config.user_agent:
            cmd.extend(["-F", self.config.user_agent])
        
        # Timeout
        if self.config.timeout:
            cmd.extend(["-T", str(int(self.config.timeout))])
        
        # Request delay
        if self.config.request_delay:
            cmd.extend(["-E", str(int(self.config.request_delay * 1000))])  # ms
        
        # Concurrent connections
        if self.config.concurrent_requests:
            cmd.extend(["-c", str(self.config.concurrent_requests)])
        
        # Domain restrictions
        if self.config.allowed_domains:
            # HTTrack syntax: +domain.com/* -otherdomain.com/*
            for domain in self.config.allowed_domains:
                cmd.append(f"+{domain}/*")
            cmd.append("-*")  # Exclude everything else
        
        # URL patterns
        if self.config.url_patterns:
            for pattern in self.config.url_patterns:
                cmd.append(f"+{pattern}")
        
        # Exclude patterns
        if self.config.exclude_patterns:
            for pattern in self.config.exclude_patterns:
                cmd.append(f"-{pattern}")
        
        # Additional HTTrack options
        cmd.extend([
            "-%P",  # No external pages
            "-n",   # Get only HTML files
            "-k",   # Keep original links
            "-K",   # Keep original links (absolute)
            "-p",   # Preserve file names
            "-%s",  # No update check
            "--disable-security-limits",  # For large sites
        ])
        
        return cmd
    
    def _find_site_directory(self, httrack_dir: Path, domain: str) -> Optional[Path]:
        """Find the directory containing the mirrored site.
        
        Args:
            httrack_dir: HTTrack output directory
            domain: Expected domain name
            
        Returns:
            Path to site directory or None
        """
        # HTTrack creates a directory structure like:
        # output_dir/domain.com/...
        
        # Look for domain directory
        for item in httrack_dir.iterdir():
            if item.is_dir():
                # Check if it matches the domain
                if domain in item.name:
                    return item
                
                # Check subdirectories
                for subitem in item.iterdir():
                    if subitem.is_dir() and domain in subitem.name:
                        return subitem
        
        # Fallback: find any directory with HTML files
        for item in httrack_dir.iterdir():
            if item.is_dir():
                html_files = list(item.glob("**/*.html"))
                if html_files:
                    return item
        
        return None
    
    def find_downloaded_files(self, site_dir: Path) -> List[Path]:
        """Find all HTML files in the mirrored site.
        
        Args:
            site_dir: Directory containing mirrored site
            
        Returns:
            List of HTML file paths
        """
        html_files = []
        
        # Common HTTrack file extensions
        extensions = [".html", ".htm", ".xhtml"]
        
        for ext in extensions:
            html_files.extend(site_dir.glob(f"**/*{ext}"))
        
        # Filter out HTTrack meta files
        html_files = [
            f for f in html_files
            if not any(skip in f.name for skip in ["hts-cache", "hts-log", "hts-stats"])
        ]
        
        return sorted(html_files)


class SimpleCrawler:
    """Simple fallback crawler using requests for single pages or small sites."""
    
    def __init__(self, config: CrawlerConfig):
        """Initialize simple crawler.
        
        Args:
            config: Crawler configuration
        """
        self.config = config
        self.visited: Set[str] = set()
        self.to_visit: List[str] = []
    
    async def crawl_single(self, url: str) -> Dict[str, str]:
        """Crawl a single page.
        
        Args:
            url: URL to crawl
            
        Returns:
            Dictionary mapping URL to HTML content
        """
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            headers = {"User-Agent": self.config.user_agent}
            
            async with session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as response:
                response.raise_for_status()
                html = await response.text()
                
                return {url: html} 