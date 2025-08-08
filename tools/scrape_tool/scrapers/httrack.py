# Copyright 2025 Franz und Franz GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""HTTrack-based web scraper implementation with Python fallback."""

import asyncio
import logging
import os
import shutil
import shlex
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Optional
from urllib.parse import urlparse, urljoin

from .base import WebScraperBase, ScrapedPage, ScraperConfig
from .python_mirror import PythonMirrorScraper

logger = logging.getLogger(__name__)


class HTTrackScraper(PythonMirrorScraper):
    """HTTrack-based web scraper with Python fallback.

    This scraper attempts to use HTTrack for website mirroring, but falls back
    to a pure Python implementation if HTTrack is not available or fails.
    """

    def __init__(self, config: ScraperConfig):
        """Initialize the HTTrack scraper.

        Args:
            config: Scraper configuration
        """
        super().__init__(config)
        self.httrack_path = shutil.which("httrack")
        self.use_httrack = bool(self.httrack_path)
        if not self.use_httrack:
            logger.warning(
                "HTTrack not found. Using Python-based mirroring instead. "
                "For better performance, install HTTrack: "
                "apt-get install httrack (Linux) or "
                "brew install httrack (macOS)"
            )
        self.temp_dir: Optional[Path] = None

    async def __aenter__(self):
        """Create temporary directory for HTTrack output and initialize parent."""
        # Initialize parent context manager for Python fallback
        await super().__aenter__()

        # Create temp dir for HTTrack
        self.temp_dir = Path(tempfile.mkdtemp(prefix="html2md_httrack_"))
        logger.debug(f"Created temporary directory: {self.temp_dir}")
        return self

    async def __aexit__(self, *args):
        """Clean up temporary directory and parent resources."""
        # Clean up parent resources
        await super().__aexit__(*args)

        # Clean up temp directory
        if self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
                logger.debug(f"Cleaned up temporary directory: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory: {e}")

    async def scrape_url(self, url: str) -> ScrapedPage:
        """Scrape a single URL using HTTrack or Python fallback.

        Note: HTTrack is designed for full site mirroring, so this method
        will create a minimal mirror and extract just the requested page.
        If HTTrack fails or is not available, uses Python implementation.

        Args:
            url: URL to scrape

        Returns:
            ScrapedPage object containing the scraped content
        """
        # If HTTrack is not available, use parent Python implementation
        if not self.use_httrack:
            return await super().scrape_url(url)

        # HTTrack has issues with localhost, use Python implementation
        parsed = urlparse(url)
        if parsed.hostname in ["localhost", "127.0.0.1", "::1"]:
            logger.info(f"Using Python implementation for localhost URL: {url}")
            return await super().scrape_url(url)

        if not self.temp_dir:
            raise RuntimeError("Scraper must be used as async context manager")

        # Create a subdirectory for this specific URL
        url_hash = str(hash(url))[-8:]
        output_dir = self.temp_dir / f"single_{url_hash}"
        output_dir.mkdir(exist_ok=True)

        # Build HTTrack command for single page
        # Properly escape all arguments to prevent command injection
        cmd = [
            self.httrack_path,
            url,  # URL is validated by validate_url method
            "-O",
            str(output_dir),
            "-r1",  # Depth 1 (just this page)
            "-%P",  # No external pages
            "-p1",  # Download HTML files
            "-%e0",  # Don't download error pages
            "--quiet",  # Quiet mode
            "--disable-security-limits",
            f"--user-agent={shlex.quote(self.config.user_agent)}",  # Escape user agent
            "--timeout=" + str(int(self.config.timeout)),
        ]

        if not self.config.verify_ssl:
            cmd.append("--assume-insecure")

        if self.config.ignore_get_params:
            cmd.append("-N0")  # Don't parse query strings

        # Run HTTrack
        logger.debug(f"Running HTTrack command: {' '.join(cmd)}")
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode("utf-8", errors="replace")
            logger.warning(
                f"HTTrack failed: {error_msg}. Falling back to Python implementation."
            )
            # Fall back to Python implementation
            return await super().scrape_url(url)

        # Find the downloaded file
        # HTTrack creates files in a domain subdirectory
        parsed_url = urlparse(url)

        # Try multiple possible locations
        possible_files = [
            # Domain/path structure
            output_dir / parsed_url.netloc / parsed_url.path.lstrip("/"),
            output_dir / parsed_url.netloc / (parsed_url.path.lstrip("/") + ".html"),
            output_dir / parsed_url.netloc / "index.html",
            # Sometimes HTTrack puts files directly in output dir
            output_dir / "index.html",
        ]

        # If path ends with /, add index.html
        if parsed_url.path.endswith("/") or not parsed_url.path:
            possible_files.insert(
                0,
                output_dir
                / parsed_url.netloc
                / parsed_url.path.lstrip("/")
                / "index.html",
            )

        expected_file = None
        for pf in possible_files:
            if pf.exists() and pf.is_file():
                expected_file = pf
                break

        if not expected_file:
            # Try to find any HTML file in the domain directory
            domain_dir = output_dir / parsed_url.netloc
            if domain_dir.exists():
                html_files = list(domain_dir.rglob("*.html"))
                # Exclude HTTrack's own index files
                html_files = [f for f in html_files if "hts-cache" not in str(f)]
                if html_files:
                    expected_file = html_files[0]

        if not expected_file:
            # Last resort: find any HTML file
            html_files = list(output_dir.rglob("*.html"))
            # Exclude HTTrack's own files and cache
            html_files = [
                f
                for f in html_files
                if "hts-cache" not in str(f) and f.name != "index.html"
            ]
            if html_files:
                expected_file = html_files[0]
            else:
                logger.warning(
                    f"HTTrack did not download any HTML files for {url}. Falling back to Python implementation."
                )
                # Fall back to Python implementation
                return await super().scrape_url(url)

        # Read the content
        try:
            content = expected_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = expected_file.read_text(encoding="latin-1")
        except Exception as e:
            logger.warning(
                f"Failed to read HTTrack output file: {e}. Falling back to Python implementation."
            )
            return await super().scrape_url(url)

        # Extract title from content
        title = None
        if "<title>" in content and "</title>" in content:
            start = content.find("<title>") + 7
            end = content.find("</title>")
            title = content[start:end].strip()

        # For single URL scraping, we don't apply deduplication checks
        # but we still extract canonical URL for metadata
        canonical_url_found = None
        if "<link" in content and "canonical" in content:
            import re

            canonical_match = re.search(
                r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']',
                content,
                re.IGNORECASE,
            )
            if not canonical_match:
                canonical_match = re.search(
                    r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']',
                    content,
                    re.IGNORECASE,
                )
            if canonical_match:
                canonical_url_found = urljoin(url, canonical_match.group(1))

        return ScrapedPage(
            url=url,
            content=content,
            title=title,
            encoding="utf-8",
            normalized_url=url,
            canonical_url=canonical_url_found,
            content_checksum=None,  # Not calculated for single URL
        )

    async def scrape_site(self, start_url: str) -> AsyncGenerator[ScrapedPage, None]:
        """Scrape entire website using HTTrack or Python fallback.

        Args:
            start_url: URL to start crawling from

        Yields:
            ScrapedPage objects as they are scraped
        """
        # If HTTrack is not available, use parent Python implementation
        if not self.use_httrack:
            async for page in super().scrape_site(start_url):
                yield page
            return

        # HTTrack has issues with localhost, use Python implementation
        parsed = urlparse(start_url)
        if parsed.hostname in ["localhost", "127.0.0.1", "::1"]:
            logger.info(f"Using Python implementation for localhost URL: {start_url}")
            async for page in super().scrape_site(start_url):
                yield page
            return

        if not self.temp_dir:
            raise RuntimeError("Scraper must be used as async context manager")

        output_dir = self.temp_dir / "site"
        output_dir.mkdir(exist_ok=True)

        # Build HTTrack command with conservative settings for Cloudflare
        # Calculate connection rate (max 0.5 connections per second)
        connection_rate = min(0.5, 1 / self.config.request_delay)

        # Limit concurrent connections (max 2 for Cloudflare sites)
        concurrent_connections = min(2, self.config.concurrent_requests)

        cmd = [
            self.httrack_path,
            start_url,  # URL is validated by validate_url method
            "-O",
            str(output_dir),
            f"-r{999999 if self.config.max_depth == -1 else self.config.max_depth}",  # Max depth (-1 = unlimited)
            "-%P",  # No external pages
            "--quiet",  # Quiet mode
            "--disable-security-limits",
            f"--user-agent={shlex.quote(self.config.user_agent)}",  # Escape user agent
            "--timeout=" + str(int(self.config.timeout)),
            f"--sockets={concurrent_connections}",  # Max 2 connections
            f"--connection-per-second={connection_rate:.2f}",  # Max 0.5/sec
            f"--max-files={self.config.max_pages if self.config.max_pages != -1 else 999999999}",  # Use very large number for unlimited
            "--max-rate=100000",  # Limit bandwidth to 100KB/s
            "--min-rate=1000",  # Minimum 1KB/s
        ]

        # Parse start URL for domain and path restrictions
        parsed = urlparse(start_url)
        base_path = parsed.path.rstrip("/")

        # Add domain restrictions
        if self.config.allowed_domains:
            for domain in self.config.allowed_domains:
                cmd.extend(["+*" + domain + "*"])
        else:
            # Restrict to same domain by default
            cmd.extend(["+*" + parsed.netloc + "*"])

        # Add subdirectory restriction if path is specified
        # Use allowed_path if specified, otherwise use the URL's path
        if self.config.allowed_path:
            # Check if allowed_path is a full URL or just a path
            if self.config.allowed_path.startswith(("http://", "https://")):
                # It's a full URL - extract domain and path
                parsed_allowed = urlparse(self.config.allowed_path)
                allowed_domain = parsed_allowed.netloc
                allowed_path = parsed_allowed.path.rstrip("/")
                logger.info(
                    f"Restricting HTTrack crawl to URL: {allowed_domain}{allowed_path}"
                )
                # Allow the specified URL and everything under it
                cmd.extend([f"+*{allowed_domain}{allowed_path}/*"])
                # Exclude everything else on that domain
                cmd.extend([f"-*{allowed_domain}/*"])
            else:
                # It's just a path
                allowed_path = self.config.allowed_path.rstrip("/")
                logger.info(
                    f"Restricting HTTrack crawl to allowed path: {allowed_path}"
                )
                # Allow the specified path and everything under it
                cmd.extend([f"+*{parsed.netloc}{allowed_path}/*"])
                # Exclude everything else on the same domain
                cmd.extend([f"-*{parsed.netloc}/*"])
        elif base_path:
            logger.info(f"Restricting HTTrack crawl to subdirectory: {base_path}")
            # Allow the base path and everything under it
            cmd.extend([f"+*{parsed.netloc}{base_path}/*"])
            # Exclude everything else on the same domain
            cmd.extend([f"-*{parsed.netloc}/*"])

        # Add exclusions
        if self.config.exclude_patterns:
            for pattern in self.config.exclude_patterns:
                cmd.extend(["-*" + pattern + "*"])

        if not self.config.verify_ssl:
            cmd.append("--assume-insecure")

        if self.config.ignore_get_params:
            cmd.append("-N0")  # Don't parse query strings

        if self.config.respect_robots_txt:
            cmd.append("--robots=3")  # Respect robots.txt

        # Run HTTrack
        logger.info(f"Starting HTTrack crawl from {start_url}")
        logger.debug(f"HTTrack command: {' '.join(cmd)}")

        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        # Wait for HTTrack to complete
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode("utf-8", errors="replace")
            logger.error(f"HTTrack failed: {error_msg}")
            # Continue to process any files that were downloaded

        # Find all downloaded HTML files
        html_files = list(output_dir.rglob("*.html"))
        logger.info(f"HTTrack downloaded {len(html_files)} HTML files")

        # Yield each file as a ScrapedPage
        for html_file in html_files:
            # Skip HTTrack's own files
            if html_file.name in ("index.html", "hts-log.txt", "hts-cache"):
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
                    url = f"{parsed_start.scheme}://{domain}/" + "/".join(path_parts)

                    # Remove .html extension if it wasn't in original
                    if url.endswith("/index.html"):
                        url = url[:-11]  # Remove /index.html
                    elif url.endswith(".html") and ".html" not in start_url:
                        url = url[:-5]  # Remove .html

                    # Read content
                    try:
                        content = html_file.read_text(encoding="utf-8")
                    except UnicodeDecodeError:
                        content = html_file.read_text(encoding="latin-1")

                    # Store metadata for database
                    normalized_url = url.rstrip("/")
                    if self.config.ignore_get_params and "?" in normalized_url:
                        normalized_url = normalized_url.split("?")[0]
                    canonical_url_found = None
                    content_checksum = None

                    # Order: 1. GET parameter normalization (already done above)
                    # 2. Canonical URL check
                    if self.config.check_canonical:
                        # Simple regex-based extraction for canonical URL
                        import re

                        canonical_match = re.search(
                            r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']',
                            content,
                            re.IGNORECASE,
                        )
                        if not canonical_match:
                            # Try alternate order
                            canonical_match = re.search(
                                r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']',
                                content,
                                re.IGNORECASE,
                            )

                        if canonical_match:
                            canonical_url_found = canonical_match.group(1)
                            # Make canonical URL absolute
                            canonical_url_found = urljoin(url, canonical_url_found)
                            # Normalize canonical URL too
                            normalized_canonical = canonical_url_found.rstrip("/")
                            if (
                                self.config.ignore_get_params
                                and "?" in normalized_canonical
                            ):
                                normalized_canonical = normalized_canonical.split("?")[
                                    0
                                ]

                            if normalized_url != normalized_canonical:
                                # Check if we should respect the canonical URL
                                should_skip = True

                                if self.config.allowed_path:
                                    # Parse URLs to check paths
                                    current_parsed = urlparse(normalized_url)
                                    canonical_parsed = urlparse(normalized_canonical)

                                    # If current URL is within allowed_path but canonical is outside,
                                    # don't skip - the user explicitly wants content from allowed_path
                                    if current_parsed.path.startswith(
                                        self.config.allowed_path
                                    ):
                                        if not canonical_parsed.path.startswith(
                                            self.config.allowed_path
                                        ):
                                            should_skip = False
                                            logger.info(
                                                f"Not skipping {url} - canonical URL {canonical_url_found} is outside allowed_path {self.config.allowed_path}"
                                            )

                                if should_skip:
                                    logger.info(
                                        f"Skipping {url} - canonical URL differs: {canonical_url_found}"
                                    )
                                    continue  # Skip this file

                    # 3. Content duplicate check
                    if self.config.check_content_duplicates:
                        from ..utils import calculate_content_checksum

                        content_checksum = calculate_content_checksum(content)

                        # Check if checksum exists using callback
                        if self._checksum_callback and self._checksum_callback(
                            content_checksum
                        ):
                            logger.info(f"Skipping {url} - duplicate content detected")
                            continue  # Skip this file

                    # Extract title
                    title = None
                    if "<title>" in content and "</title>" in content:
                        start_idx = content.find("<title>") + 7
                        end_idx = content.find("</title>")
                        title = content[start_idx:end_idx].strip()

                    self.mark_visited(url)

                    yield ScrapedPage(
                        url=url,
                        content=content,
                        title=title,
                        encoding="utf-8",
                        normalized_url=normalized_url,
                        canonical_url=canonical_url_found,
                        content_checksum=content_checksum,
                    )

            except Exception as e:
                logger.error(f"Error processing {html_file}: {e}")
                continue
