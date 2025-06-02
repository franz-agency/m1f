"""HTTrack-based web scraper implementation."""

import asyncio
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Optional, Set
from urllib.parse import urlparse, urljoin

from .base import WebScraperBase, ScrapedPage, ScraperConfig

logger = logging.getLogger(__name__)


class HTTrackScraper(WebScraperBase):
    """HTTrack-based web scraper for complete website mirroring."""
    
    def __init__(self, config: ScraperConfig):
        """Initialize the HTTrack scraper.
        
        Args:
            config: Scraper configuration
        """
        super().__init__(config)
        self.httrack_path = shutil.which('httrack')
        if not self.httrack_path:
            raise RuntimeError(
                "HTTrack not found. Please install HTTrack: "
                "apt-get install httrack (Linux) or "
                "brew install httrack (macOS) or "
                "download from https://www.httrack.com (Windows)"
            )
        self.temp_dir: Optional[Path] = None
        
    async def __aenter__(self):
        """Create temporary directory for HTTrack output."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix='html2md_httrack_'))
        logger.debug(f"Created temporary directory: {self.temp_dir}")
        return self
        
    async def __aexit__(self, *args):
        """Clean up temporary directory."""
        if self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
                logger.debug(f"Cleaned up temporary directory: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory: {e}")
                
    async def scrape_url(self, url: str) -> ScrapedPage:
        """Scrape a single URL using HTTrack.
        
        Note: HTTrack is designed for full site mirroring, so this method
        will create a minimal mirror and extract just the requested page.
        
        Args:
            url: URL to scrape
            
        Returns:
            ScrapedPage object containing the scraped content
        """
        if not self.temp_dir:
            raise RuntimeError("Scraper must be used as async context manager")
            
        # Create a subdirectory for this specific URL
        url_hash = str(hash(url))[-8:]
        output_dir = self.temp_dir / f"single_{url_hash}"
        output_dir.mkdir(exist_ok=True)
        
        # Build HTTrack command for single page
        cmd = [
            self.httrack_path,
            url,
            '-O', str(output_dir),
            '-r1',  # Depth 1 (just this page)
            '-%P',  # No external pages
            '-p0',  # Don't download non-HTML files
            '--quiet',  # Quiet mode
            '--disable-security-limits',
            f'--user-agent={self.config.user_agent}',
            '--timeout=' + str(int(self.config.timeout)),
        ]
        
        if not self.config.verify_ssl:
            cmd.append('--assume-insecure')
            
        # Run HTTrack
        logger.debug(f"Running HTTrack command: {' '.join(cmd)}")
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8', errors='replace')
            raise RuntimeError(f"HTTrack failed: {error_msg}")
            
        # Find the downloaded file
        parsed_url = urlparse(url)
        expected_file = output_dir / parsed_url.netloc / parsed_url.path.lstrip('/')
        if expected_file.is_dir():
            expected_file = expected_file / 'index.html'
        elif not expected_file.suffix:
            html_file = Path(str(expected_file) + '.html')
            if html_file.exists():
                expected_file = html_file
                
        if not expected_file.exists():
            # Try to find any HTML file
            html_files = list(output_dir.rglob('*.html'))
            if html_files:
                expected_file = html_files[0]
            else:
                raise RuntimeError(f"HTTrack did not download any HTML files for {url}")
                
        # Read the content
        try:
            content = expected_file.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = expected_file.read_text(encoding='latin-1')
            
        # Extract title from content
        title = None
        if '<title>' in content and '</title>' in content:
            start = content.find('<title>') + 7
            end = content.find('</title>')
            title = content[start:end].strip()
            
        return ScrapedPage(
            url=url,
            content=content,
            title=title,
            encoding='utf-8'
        )
        
    async def scrape_site(self, start_url: str) -> AsyncGenerator[ScrapedPage, None]:
        """Scrape entire website using HTTrack.
        
        Args:
            start_url: URL to start crawling from
            
        Yields:
            ScrapedPage objects as they are scraped
        """
        if not self.temp_dir:
            raise RuntimeError("Scraper must be used as async context manager")
            
        output_dir = self.temp_dir / 'site'
        output_dir.mkdir(exist_ok=True)
        
        # Build HTTrack command
        cmd = [
            self.httrack_path,
            start_url,
            '-O', str(output_dir),
            f'-r{self.config.max_depth}',  # Max depth
            '-%P',  # No external pages
            '--quiet',  # Quiet mode
            '--disable-security-limits',
            f'--user-agent={self.config.user_agent}',
            '--timeout=' + str(int(self.config.timeout)),
            f'--sockets={self.config.concurrent_requests}',
            f'--connection-per-second={1/self.config.request_delay:.1f}',
            f'--max-files={self.config.max_pages}',
        ]
        
        # Add domain restrictions
        if self.config.allowed_domains:
            for domain in self.config.allowed_domains:
                cmd.extend(['+*' + domain + '*'])
        else:
            # Restrict to same domain by default
            parsed = urlparse(start_url)
            cmd.extend(['+*' + parsed.netloc + '*'])
            
        # Add exclusions
        if self.config.exclude_patterns:
            for pattern in self.config.exclude_patterns:
                cmd.extend(['-*' + pattern + '*'])
                
        if not self.config.verify_ssl:
            cmd.append('--assume-insecure')
            
        if self.config.respect_robots_txt:
            cmd.append('--robots=3')  # Respect robots.txt
            
        # Run HTTrack
        logger.info(f"Starting HTTrack crawl from {start_url}")
        logger.debug(f"HTTrack command: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait for HTTrack to complete
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8', errors='replace')
            logger.error(f"HTTrack failed: {error_msg}")
            # Continue to process any files that were downloaded
            
        # Find all downloaded HTML files
        html_files = list(output_dir.rglob('*.html'))
        logger.info(f"HTTrack downloaded {len(html_files)} HTML files")
        
        # Yield each file as a ScrapedPage
        for html_file in html_files:
            # Skip HTTrack's own files
            if html_file.name in ('index.html', 'hts-log.txt', 'hts-cache'):
                continue
                
            try:
                # Reconstruct URL from file path
                rel_path = html_file.relative_to(output_dir)
                parts = rel_path.parts
                
                # First part should be domain
                if len(parts) > 0:
                    domain = parts[0]
                    path_parts = parts[1:] if len(parts) > 1 else []
                    
                    # Reconstruct URL
                    parsed_start = urlparse(start_url)
                    url = f"{parsed_start.scheme}://{domain}/" + '/'.join(path_parts)
                    
                    # Remove .html extension if it wasn't in original
                    if url.endswith('/index.html'):
                        url = url[:-11]  # Remove /index.html
                    elif url.endswith('.html') and '.html' not in start_url:
                        url = url[:-5]  # Remove .html
                        
                    # Read content
                    try:
                        content = html_file.read_text(encoding='utf-8')
                    except UnicodeDecodeError:
                        content = html_file.read_text(encoding='latin-1')
                        
                    # Extract title
                    title = None
                    if '<title>' in content and '</title>' in content:
                        start_idx = content.find('<title>') + 7
                        end_idx = content.find('</title>')
                        title = content[start_idx:end_idx].strip()
                        
                    self.mark_visited(url)
                    
                    yield ScrapedPage(
                        url=url,
                        content=content,
                        title=title,
                        encoding='utf-8'
                    )
                    
            except Exception as e:
                logger.error(f"Error processing {html_file}: {e}")
                continue