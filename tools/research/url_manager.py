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

"""
URL management for m1f-research with file support and deduplication
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urlunparse

from m1f.file_operations import (
    safe_exists,
    safe_read_text,
)

from .research_db import JobDatabase

logger = logging.getLogger(__name__)


class URLManager:
    """Manages URL collection, deduplication, and tracking"""

    def __init__(self, job_db: JobDatabase):
        self.job_db = job_db

    def add_urls_from_list(
        self, urls: List[Dict[str, str]], source: str = "llm"
    ) -> int:
        """Add URLs from a list (LLM-generated or manual)"""
        return self.job_db.add_urls(urls, added_by=source)

    async def add_urls_from_file(self, file_path: Path) -> int:
        """Add URLs from a text file (one URL per line)"""
        if not safe_exists(file_path):
            logger.error(f"URL file not found: {file_path}")
            return 0

        urls = []
        try:
            content = safe_read_text(file_path)
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):  # Skip comments
                    # Support optional title after URL
                    parts = line.split("\t", 1)
                    url = parts[0].strip()
                    title = parts[1].strip() if len(parts) > 1 else ""

                    if url.startswith(("http://", "https://")):
                        urls.append(
                            {
                                "url": url,
                                "title": title,
                                "description": f"From file: {file_path.name}",
                            }
                        )

        except Exception as e:
            logger.error(f"Error reading URL file {file_path}: {e}")
            return 0

        logger.info(f"Found {len(urls)} URLs in {file_path}")
        return self.add_urls_from_list(urls, source="manual")

    def get_unscraped_urls(self) -> List[str]:
        """Get all URLs that haven't been scraped yet"""
        return self.job_db.get_unscraped_urls()

    def get_urls_grouped_by_host(self) -> Dict[str, List[str]]:
        """Get unscraped URLs grouped by host for smart delay management"""
        return self.job_db.get_urls_by_host()

    def normalize_url(self, url: str) -> str:
        """Normalize a URL for deduplication"""
        try:
            parsed = urlparse(url)

            # Normalize components
            scheme = parsed.scheme.lower()
            netloc = parsed.netloc.lower()
            path = parsed.path.rstrip("/")

            # Remove default ports
            if netloc.endswith(":80") and scheme == "http":
                netloc = netloc[:-3]
            elif netloc.endswith(":443") and scheme == "https":
                netloc = netloc[:-4]

            # Reconstruct URL
            normalized = urlunparse(
                (
                    scheme,
                    netloc,
                    path,
                    parsed.params,
                    parsed.query,
                    "",  # Remove fragment
                )
            )

            return normalized

        except Exception as e:
            logger.warning(f"Could not normalize URL {url}: {e}")
            return url

    def deduplicate_urls(self, urls: List[str]) -> List[str]:
        """Remove duplicate URLs based on normalization"""
        seen = set()
        unique = []

        for url in urls:
            normalized = self.normalize_url(url)
            if normalized not in seen:
                seen.add(normalized)
                unique.append(url)

        if len(urls) != len(unique):
            logger.info(f"Deduplicated {len(urls)} URLs to {len(unique)} unique URLs")

        return unique

    def get_host_from_url(self, url: str) -> str:
        """Extract host from URL"""
        try:
            return urlparse(url).netloc
        except:
            return "unknown"

    def create_url_batches(self, max_per_host: int = 5) -> List[List[str]]:
        """Create URL batches for parallel scraping with host limits"""
        urls_by_host = self.get_urls_grouped_by_host()
        batches = []

        # First pass: Add up to max_per_host from each host
        current_batch = []
        host_counts = {}

        for host, urls in urls_by_host.items():
            for url in urls[:max_per_host]:
                current_batch.append(url)
                host_counts[host] = host_counts.get(host, 0) + 1

                # Create new batch when we have enough diversity
                if len(current_batch) >= 10:  # Batch size
                    batches.append(current_batch)
                    current_batch = []

        # Add remaining URLs
        if current_batch:
            batches.append(current_batch)

        # Second pass: Add remaining URLs from hosts with many URLs
        for host, urls in urls_by_host.items():
            if len(urls) > max_per_host:
                remaining = urls[max_per_host:]
                for i in range(0, len(remaining), max_per_host):
                    batch = remaining[i : i + max_per_host]
                    batches.append(batch)

        logger.info(f"Created {len(batches)} URL batches for scraping")
        return batches

    def mark_url_scraped(
        self,
        url: str,
        status_code: int,
        content_checksum: Optional[str] = None,
        error_message: Optional[str] = None,
    ):
        """Mark a URL as scraped"""
        self.job_db.mark_url_scraped(url, status_code, content_checksum, error_message)

    def get_stats(self) -> Dict[str, int]:
        """Get URL statistics"""
        return self.job_db.get_stats()
