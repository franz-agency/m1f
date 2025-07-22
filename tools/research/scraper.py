"""
Smart scraper with advanced features for m1f-research
"""
import asyncio
import random
import aiohttp
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
from urllib.parse import urlparse, urljoin
import re

from .models import ScrapedContent
from .config import ScrapingConfig

logger = logging.getLogger(__name__)


class SmartScraper:
    """
    Advanced web scraper with:
    - Random timeouts for politeness
    - Concurrent scraping with rate limiting
    - Auto-retry on failures
    - Progress tracking
    - Robots.txt respect
    """
    
    def __init__(self, config: ScrapingConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(config.max_concurrent)
        self.progress_callback = None
        self.total_urls = 0
        self.completed_urls = 0
        self.failed_urls = []
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def set_progress_callback(self, callback):
        """Set callback for progress updates"""
        self.progress_callback = callback
    
    async def scrape_urls(self, urls: List[Dict[str, str]]) -> List[ScrapedContent]:
        """
        Scrape multiple URLs concurrently
        
        Args:
            urls: List of dicts with 'url', 'title', 'description'
            
        Returns:
            List of successfully scraped content
        """
        self.total_urls = len(urls)
        self.completed_urls = 0
        self.failed_urls = []
        
        # Create scraping tasks
        tasks = [self._scrape_with_retry(url_info) for url_info in urls]
        
        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out failures and exceptions
        scraped_content = []
        for result in results:
            if isinstance(result, ScrapedContent):
                scraped_content.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Scraping exception: {result}")
        
        logger.info(f"Scraped {len(scraped_content)}/{len(urls)} URLs successfully")
        return scraped_content
    
    async def _scrape_with_retry(self, url_info: Dict[str, str]) -> Optional[ScrapedContent]:
        """Scrape a single URL with retry logic"""
        url = url_info['url']
        
        for attempt in range(self.config.retry_attempts):
            try:
                result = await self._scrape_single_url(url_info)
                if result:
                    return result
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.config.retry_attempts - 1:
                    # Exponential backoff
                    await asyncio.sleep(2 ** attempt)
        
        # All attempts failed
        self.failed_urls.append(url)
        return None
    
    async def _scrape_single_url(self, url_info: Dict[str, str]) -> Optional[ScrapedContent]:
        """Scrape a single URL with rate limiting"""
        async with self.semaphore:
            url = url_info['url']
            
            # Random delay for politeness
            min_delay, max_delay = self._parse_timeout_range()
            delay = random.uniform(min_delay, max_delay)
            await asyncio.sleep(delay)
            
            # Check robots.txt if enabled
            if self.config.respect_robots_txt and not await self._check_robots_txt(url):
                logger.info(f"Skipping {url} due to robots.txt")
                return None
            
            # Prepare headers
            headers = {
                'User-Agent': random.choice(self.config.user_agents),
                **self.config.headers
            }
            
            try:
                async with self.session.get(
                    url, 
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                    allow_redirects=True
                ) as response:
                    # Update progress
                    self.completed_urls += 1
                    if self.progress_callback:
                        self.progress_callback(self.completed_urls, self.total_urls)
                    
                    if response.status == 200:
                        html = await response.text()
                        
                        # Convert to markdown
                        markdown = await self._html_to_markdown(html, url)
                        
                        return ScrapedContent(
                            url=str(response.url),  # Use final URL after redirects
                            title=url_info.get('title', self._extract_title(html)),
                            html=html,
                            markdown=markdown,
                            scraped_at=datetime.now(),
                            metadata={
                                'status_code': response.status,
                                'content_type': response.headers.get('Content-Type', ''),
                                'content_length': len(html),
                                'final_url': str(response.url)
                            }
                        )
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        return None
                        
            except asyncio.TimeoutError:
                logger.error(f"Timeout scraping {url}")
                return None
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                return None
    
    async def _html_to_markdown(self, html: str, base_url: str) -> str:
        """Convert HTML to Markdown"""
        try:
            # Try to import and use existing converters
            from markdownify import markdownify
            
            # Configure markdownify for better output
            markdown = markdownify(
                html,
                heading_style="ATX",
                bullets="-",
                code_language="python",
                wrap=True,
                wrap_width=80
            )
            
            # Fix relative URLs
            markdown = self._fix_relative_urls(markdown, base_url)
            
            return markdown
            
        except ImportError:
            # Fallback to basic conversion
            return self._basic_html_to_markdown(html)
    
    def _basic_html_to_markdown(self, html: str) -> str:
        """Basic HTML to Markdown conversion"""
        # Remove script and style tags
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        
        # Convert common tags
        conversions = [
            (r'<h1[^>]*>(.*?)</h1>', r'# \1\n'),
            (r'<h2[^>]*>(.*?)</h2>', r'## \1\n'),
            (r'<h3[^>]*>(.*?)</h3>', r'### \1\n'),
            (r'<h4[^>]*>(.*?)</h4>', r'#### \1\n'),
            (r'<h5[^>]*>(.*?)</h5>', r'##### \1\n'),
            (r'<h6[^>]*>(.*?)</h6>', r'###### \1\n'),
            (r'<p[^>]*>(.*?)</p>', r'\1\n\n'),
            (r'<br[^>]*>', '\n'),
            (r'<strong[^>]*>(.*?)</strong>', r'**\1**'),
            (r'<b[^>]*>(.*?)</b>', r'**\1**'),
            (r'<em[^>]*>(.*?)</em>', r'*\1*'),
            (r'<i[^>]*>(.*?)</i>', r'*\1*'),
            (r'<code[^>]*>(.*?)</code>', r'`\1`'),
            (r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', r'[\2](\1)'),
            (r'<li[^>]*>(.*?)</li>', r'- \1\n'),
            (r'<ul[^>]*>', '\n'),
            (r'</ul>', '\n'),
            (r'<ol[^>]*>', '\n'),
            (r'</ol>', '\n'),
        ]
        
        for pattern, replacement in conversions:
            html = re.sub(pattern, replacement, html, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove remaining tags
        html = re.sub(r'<[^>]+>', '', html)
        
        # Clean up whitespace
        html = re.sub(r'\n\s*\n\s*\n', '\n\n', html)
        html = html.strip()
        
        return html
    
    def _fix_relative_urls(self, markdown: str, base_url: str) -> str:
        """Convert relative URLs to absolute URLs"""
        # Parse base URL
        parsed_base = urlparse(base_url)
        base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"
        
        # Fix markdown links
        def fix_link(match):
            text = match.group(1)
            url = match.group(2)
            
            # Skip if already absolute
            if url.startswith(('http://', 'https://', 'mailto:', '#')):
                return match.group(0)
            
            # Convert to absolute
            if url.startswith('/'):
                url = base_domain + url
            else:
                url = urljoin(base_url, url)
            
            return f'[{text}]({url})'
        
        markdown = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', fix_link, markdown)
        
        return markdown
    
    def _extract_title(self, html: str) -> str:
        """Extract title from HTML"""
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        if title_match:
            title = title_match.group(1).strip()
            # Clean up title
            title = re.sub(r'\s+', ' ', title)
            return title[:200]  # Limit length
        return "Untitled"
    
    async def _check_robots_txt(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt"""
        # Simple implementation - in production would use robotparser
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        try:
            async with self.session.get(
                robots_url,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    robots_txt = await response.text()
                    # Very basic check - just look for explicit disallow
                    path = parsed.path or '/'
                    if f"Disallow: {path}" in robots_txt:
                        return False
        except:
            # If we can't check robots.txt, assume it's OK
            pass
        
        return True
    
    def _parse_timeout_range(self) -> tuple[float, float]:
        """Parse timeout range string"""
        parts = self.config.timeout_range.split('-')
        if len(parts) == 2:
            return float(parts[0]), float(parts[1])
        else:
            val = float(parts[0])
            return val, val
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scraping statistics"""
        return {
            'total_urls': self.total_urls,
            'completed_urls': self.completed_urls,
            'failed_urls': len(self.failed_urls),
            'success_rate': self.completed_urls / self.total_urls if self.total_urls > 0 else 0,
            'failed_url_list': self.failed_urls
        }