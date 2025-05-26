#!/usr/bin/env python3
"""Web crawling functionality using HTTrack."""

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Set
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class HTTrackCrawler:
    """Web crawler using the real HTTrack command-line tool."""

    def __init__(self, config):
        """Initialize HTTrack crawler with configuration.
        
        Args:
            config: CrawlerConfig instance with crawling settings
        """
        self.config = config
        self.httrack_path = self._find_httrack()
        
    def _find_httrack(self) -> str:
        """Find HTTrack executable on the system.
        
        Returns:
            Path to httrack executable
            
        Raises:
            RuntimeError: If HTTrack is not found
        """
        # Check common locations
        possible_paths = [
            "httrack",  # In PATH
            "/usr/bin/httrack",
            "/usr/local/bin/httrack",
            "/opt/httrack/bin/httrack"
        ]
        
        for path in possible_paths:
            if shutil.which(path) or Path(path).exists():
                logger.debug(f"Found HTTrack at: {path}")
                return path
                
        raise RuntimeError(
            "HTTrack is not installed or not found in PATH. "
            "Please install it using: sudo apt-get install httrack"
        )
    
    def crawl(self, start_url: str, output_dir: Path) -> Path:
        """Crawl a website using HTTrack.
        
        Args:
            start_url: Starting URL for crawling
            output_dir: Directory to store downloaded files
            
        Returns:
            Path to the directory containing downloaded files
            
        Raises:
            subprocess.CalledProcessError: If HTTrack fails
        """
        logger.info(f"Starting HTTrack crawl of {start_url}")
        
        # Parse URL to get domain
        parsed_url = urlparse(start_url)
        domain = parsed_url.netloc
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        site_dir = output_dir / domain
        
        # Build HTTrack command
        cmd = self._build_httrack_command(start_url, output_dir)
        
        logger.debug(f"Running HTTrack command: {' '.join(cmd)}")
        
        try:
            # Run HTTrack
            result = subprocess.run(
                cmd,
                cwd=output_dir,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode != 0:
                logger.error(f"HTTrack failed with return code {result.returncode}")
                logger.error(f"STDOUT: {result.stdout}")
                logger.error(f"STDERR: {result.stderr}")
                raise subprocess.CalledProcessError(
                    result.returncode, cmd, result.stdout, result.stderr
                )
            
            logger.info("HTTrack crawl completed successfully")
            logger.debug(f"HTTrack output: {result.stdout}")
            
            return site_dir
            
        except subprocess.TimeoutExpired:
            logger.error("HTTrack crawl timed out after 1 hour")
            raise
        except Exception as e:
            logger.error(f"HTTrack crawl failed: {e}")
            raise
    
    def _build_httrack_command(self, start_url: str, output_dir: Path) -> List[str]:
        """Build HTTrack command with appropriate options.
        
        Args:
            start_url: Starting URL for crawling
            output_dir: Output directory
            
        Returns:
            List of command arguments
        """
        cmd = [self.httrack_path]
        
        # Basic options
        cmd.extend([
            start_url,
            "-O", str(output_dir),  # Output directory
            "-q",  # Quiet mode (less verbose)
            "-r", str(self.config.max_depth),  # Recursion depth
            "-s0" if self.config.respect_robots_txt else "-s2",  # robots.txt handling
            "-c", str(getattr(self.config, 'concurrent_requests', 4)),  # Connections
            "-T", str(self.config.timeout),  # Timeout
        ])
        
        # Rate limiting
        if hasattr(self.config, 'request_delay') and self.config.request_delay > 0:
            # Convert seconds to milliseconds for HTTrack
            delay_ms = int(self.config.request_delay * 1000)
            cmd.extend(["-E", str(delay_ms)])
        
        # User agent
        if hasattr(self.config, 'user_agent'):
            cmd.extend(["-F", self.config.user_agent])
        else:
            cmd.extend(["-F", "html2md-httrack/2.0 (+https://franz.agency)"])
        
        # Domain restrictions
        if self.config.allowed_domains:
            for domain in self.config.allowed_domains:
                cmd.extend(["+", f"*{domain}/*"])
        
        # Path exclusions
        if self.config.excluded_paths:
            for path in self.config.excluded_paths:
                cmd.extend(["-", path])
        
        # Additional HTTrack options for better HTML extraction
        cmd.extend([
            "-j",  # Parse Java files (for better link extraction)
            "-K",  # Keep original links when possible
            "-x",  # Do not make any index files
            "-N", "100",  # Maximum number of non-HTML files per site
            "-G",  # Store all files in cache
        ])
        
        # File type restrictions (focus on HTML)
        cmd.extend([
            "-*",  # Exclude all by default
            "+*.html",
            "+*.htm",
            "+*.php",
            "+*.asp",
            "+*.aspx",
            "+*.jsp",
            "+*.css",  # Include CSS for completeness
            "+*.js",   # Include JS for completeness
        ])
        
        return cmd
    
    def find_downloaded_files(self, site_dir: Path) -> List[Path]:
        """Find all HTML files downloaded by HTTrack.
        
        Args:
            site_dir: Directory containing downloaded files
            
        Returns:
            List of HTML file paths
        """
        if not site_dir.exists():
            logger.warning(f"Site directory does not exist: {site_dir}")
            return []
        
        html_files = []
        
        # HTTrack typically creates files with various extensions
        patterns = ["*.html", "*.htm", "*.php", "*.asp", "*.aspx", "*.jsp"]
        
        for pattern in patterns:
            files = list(site_dir.rglob(pattern))
            html_files.extend(files)
        
        # Filter out HTTrack's own files
        filtered_files = []
        for file_path in html_files:
            # Skip HTTrack's index and cache files
            if file_path.name.startswith(("hts-", "index.html")) and file_path.parent == site_dir:
                continue
            # Skip cache directories
            if "hts-cache" in str(file_path):
                continue
            filtered_files.append(file_path)
        
        logger.info(f"Found {len(filtered_files)} HTML files in {site_dir}")
        return sorted(filtered_files)
    
    def cleanup_httrack_files(self, site_dir: Path) -> None:
        """Clean up HTTrack-specific files and directories.
        
        Args:
            site_dir: Directory containing downloaded files
        """
        if not site_dir.exists():
            return
        
        # Remove HTTrack cache and metadata
        cleanup_patterns = [
            "hts-cache",
            "hts-log.txt",
            "cookies.txt",
            "index.html"  # HTTrack's generated index
        ]
        
        for pattern in cleanup_patterns:
            for item in site_dir.rglob(pattern):
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                        logger.debug(f"Removed directory: {item}")
                    else:
                        item.unlink()
                        logger.debug(f"Removed file: {item}")
                except Exception as e:
                    logger.warning(f"Failed to remove {item}: {e}")


class AsyncHTTrackCrawler(HTTrackCrawler):
    """Async wrapper for HTTrack crawler."""
    
    async def crawl_async(self, start_url: str, output_dir: Path) -> Path:
        """Async version of crawl method.
        
        Args:
            start_url: Starting URL for crawling
            output_dir: Directory to store downloaded files
            
        Returns:
            Path to the directory containing downloaded files
        """
        import asyncio
        
        # Run HTTrack in a thread pool since it's a blocking operation
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.crawl, start_url, output_dir) 