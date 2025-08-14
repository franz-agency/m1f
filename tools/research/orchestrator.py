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
Enhanced research orchestrator with job management and persistence
"""

import asyncio
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import logging

from ..m1f.file_operations import (
    safe_open,
)

from .config import ResearchConfig
from .llm_interface import get_provider, LLMProvider
from .models import ResearchResult, ScrapedContent, AnalyzedContent
from .job_manager import JobManager
from .research_db import ResearchJob, JobDatabase
from .url_manager import URLManager
from .smart_scraper import EnhancedSmartScraper
from .content_filter import ContentFilter
from .analyzer import ContentAnalyzer
from .bundle_creator import SmartBundleCreator
from .readme_generator import ReadmeGenerator

logger = logging.getLogger(__name__)

try:
    from ..scrape_tool.scrapers.base import WebScraperBase as WebScraper
except ImportError:
    logger.warning("Could not import WebScraperBase from scrape_tool")
    WebScraper = None

try:
    from ..html2md_tool import HTML2MDConverter as HTMLToMarkdownConverter
except ImportError:
    logger.warning("Could not import HTML2MDConverter from html2md_tool")
    HTMLToMarkdownConverter = None


class EnhancedResearchOrchestrator:
    """Enhanced orchestrator with job persistence and resume support"""

    def __init__(self, config: ResearchConfig):
        self.config = config
        self.llm = self._init_llm()
        self.job_manager = JobManager(config.output.directory)
        self.current_job: Optional[ResearchJob] = None
        self.job_db: Optional[JobDatabase] = None
        self.url_manager: Optional[URLManager] = None
        self.progress_callback = None

    def _init_llm(self) -> Optional[LLMProvider]:
        """Initialize LLM provider from config"""
        if self.config.dry_run:
            return None

        try:
            # Determine effective provider with sensible defaults
            provider_name = (self.config.llm.provider or "claude").lower()

            if provider_name == "auto":
                # Prefer Claude Code subscription (no API key needed)
                provider_name = "claude-code"
                # If Claude Code is not desired, fallback to Claude API if key is present
                if not os.getenv("CLAUDE_CODE", "1") and os.getenv("ANTHROPIC_API_KEY"):
                    provider_name = "claude"
                # Else fallback to Gemini if key available
                elif (
                    not os.getenv("CLAUDE_CODE", "1")
                    and not os.getenv("ANTHROPIC_API_KEY")
                    and os.getenv("GOOGLE_API_KEY")
                ):
                    provider_name = "gemini"

            # If user selected Claude but no API key is present, transparently use Claude Code
            if provider_name == "claude" and not os.getenv("ANTHROPIC_API_KEY"):
                provider_name = "claude-code"

            return get_provider(
                provider_name,
                api_key=None,  # Providers will read from environment when needed
                model=self.config.llm.model,
            )
        except Exception as e:
            logger.error(f"Failed to initialize LLM provider: {e}")
            if not self.config.no_analysis:
                raise
            return None

    def set_progress_callback(self, callback):
        """Set callback for progress updates"""
        self.progress_callback = callback

    async def research(
        self, query: str, job_id: Optional[str] = None, urls_file: Optional[Path] = None
    ) -> ResearchResult:
        """
        Run research workflow with job management

        Args:
            query: Research query
            job_id: Existing job ID to resume
            urls_file: Optional file with additional URLs

        Returns:
            ResearchResult with all findings
        """
        logger.info(f"Starting research for: {query}")

        try:
            # Initialize or resume job
            if job_id:
                self.current_job = self.job_manager.get_job(job_id)
                if not self.current_job:
                    raise ValueError(f"Job {job_id} not found")
                logger.info(f"Resuming job {job_id}")
            else:
                self.current_job = self.job_manager.create_job(query, self.config)
                logger.info(f"Created new job {self.current_job.job_id}")

            # Setup job database and URL manager
            self.job_db = self.job_manager.get_job_database(self.current_job)
            self.url_manager = URLManager(self.job_db)

            # Phase 1: URL Collection
            urls = await self._collect_urls(query, urls_file, resume=bool(job_id))

            if not urls:
                logger.warning("No URLs to scrape")
                self.job_manager.update_job_status(self.current_job.job_id, "completed")
                return self._create_empty_result()

            # Phase 2: Smart Scraping
            scraped_content = await self._scrape_urls(urls)

            # Phase 3: Content Filtering
            filtered_content = await self._filter_content(scraped_content)

            # Phase 4: Content Analysis (optional)
            if not self.config.no_analysis and self.llm:
                analyzed_content = await self._analyze_content(filtered_content)
            else:
                # Convert to AnalyzedContent with defaults
                analyzed_content = [
                    self._scraped_to_analyzed(s) for s in filtered_content
                ]

            # Phase 5: Bundle Creation
            bundle_path = await self._create_bundle(analyzed_content, query)

            # Update job status
            self.job_manager.update_job_stats(self.current_job)
            self.job_manager.update_job_status(self.current_job.job_id, "completed")

            # Create symlink to latest research
            await self.job_manager.create_symlink_to_latest(self.current_job)

            return ResearchResult(
                query=query,
                job_id=self.current_job.job_id,
                urls_found=len(urls),
                scraped_content=scraped_content,
                analyzed_content=analyzed_content,
                bundle_path=bundle_path,
                bundle_created=True,
                output_dir=Path(self.current_job.output_dir),
            )

        except Exception as e:
            logger.error(f"Research failed: {e}")
            if self.current_job:
                self.job_manager.update_job_status(self.current_job.job_id, "failed")
            raise

    async def _collect_urls(
        self, query: str, urls_file: Optional[Path], resume: bool
    ) -> List[str]:
        """Collect URLs from LLM and/or file"""
        all_urls = []

        # Add URLs from file if provided
        if urls_file:
            added = await self.url_manager.add_urls_from_file(urls_file)
            logger.info(f"Added {added} URLs from file")

        # Get URLs from LLM if not resuming
        if not resume and not self.config.dry_run:
            logger.info("Searching for URLs using LLM...")
            if self.progress_callback:
                self.progress_callback(
                    "searching", 0, self.config.scraping.search_limit
                )
            try:
                llm_urls = await self.llm.search_web(
                    query, self.config.scraping.search_limit
                )
                added = self.url_manager.add_urls_from_list(llm_urls, source="llm")
                logger.info(f"Added {added} URLs from LLM search")
                if self.progress_callback:
                    self.progress_callback(
                        "searching", added, self.config.scraping.search_limit
                    )
            except Exception as e:
                logger.error(f"Error searching for URLs: {e}")
                if not urls_file:  # If no manual URLs, this is fatal
                    # Provide helpful error message for common issues
                    if "Failed to parse" in str(e) and "JSON" in str(e):
                        error_msg = (
                            "LLM failed to generate URLs. This can happen when:\n"
                            "1. Using Claude without API key (falls back to Claude Code which may refuse URL generation)\n"
                            "2. Query contains sensitive topics\n\n"
                            "Solutions:\n"
                            "- Set ANTHROPIC_API_KEY environment variable to use Claude API\n"
                            "- Use --provider gemini with GOOGLE_API_KEY set\n"
                            "- Provide URLs manually with --urls-file\n"
                            "- Try rephrasing your query"
                        )
                        raise Exception(error_msg) from e
                    raise

        # Get unscraped URLs
        all_urls = self.url_manager.get_unscraped_urls()
        logger.info(f"Total URLs to scrape: {len(all_urls)}")

        # Update stats
        self.job_manager.update_job_stats(
            self.current_job, total_urls=self.job_db.get_stats()["total_urls"]
        )

        # Limit URLs if configured
        if (
            self.config.scraping.scrape_limit
            and len(all_urls) > self.config.scraping.scrape_limit
        ):
            all_urls = all_urls[: self.config.scraping.scrape_limit]
            logger.info(f"Limited to {len(all_urls)} URLs")

        return all_urls

    async def _scrape_urls(self, urls: List[str]) -> List[ScrapedContent]:
        """Scrape URLs with smart delay management"""
        if self.config.dry_run:
            logger.info("DRY RUN: Would scrape URLs")
            return []

        scraped_content = []

        async with EnhancedSmartScraper(
            self.config.scraping, self.job_db, self.url_manager
        ) as scraper:
            # Set progress callback
            def scraping_progress(completed, total, percentage):
                logger.info(
                    f"Scraping progress: {completed}/{total} ({percentage:.1f}%)"
                )
                if self.progress_callback:
                    self.progress_callback("scraping", completed, total)
                if completed % 5 == 0:  # Update stats every 5 URLs
                    self.job_manager.update_job_stats(
                        self.current_job,
                        scraped_urls=self.job_db.get_stats()["scraped_urls"],
                    )

            scraper.set_progress_callback(scraping_progress)

            # Scrape URLs
            raw_content = await scraper.scrape_urls(urls)

            # Convert HTML to Markdown
            for scraped in raw_content:
                try:
                    # Use html2md tool if available
                    if HTMLToMarkdownConverter:
                        converter = HTMLToMarkdownConverter()
                        markdown = converter.convert(scraped.content)
                    else:
                        # Fallback to basic conversion
                        markdown = self._basic_html_to_markdown(scraped.content)

                    # Save to database
                    self.job_db.save_content(
                        url=scraped.url,
                        title=scraped.title,
                        markdown=markdown,
                        metadata={
                            "scraped_at": scraped.scraped_at.isoformat(),
                            "content_type": scraped.content_type,
                        },
                    )

                    # Update scraped content
                    scraped.content = markdown
                    scraped_content.append(scraped)

                except Exception as e:
                    logger.error(f"Error converting {scraped.url}: {e}")

        # Final stats update
        stats = scraper.get_statistics()
        logger.info(
            f"Scraping complete: {stats['successful_urls']} successful, "
            f"{stats['failed_urls']} failed"
        )

        self.job_manager.update_job_stats(self.current_job)

        return scraped_content

    async def _filter_content(
        self, content: List[ScrapedContent]
    ) -> List[ScrapedContent]:
        """Filter content for quality"""
        if self.config.no_filter:
            logger.info("Content filtering disabled")
            return content

        filter = ContentFilter(self.config.filtering)
        filtered = []

        for item in content:
            passed, reason = filter.filter_content(item.content)

            # Update database
            self.job_db.save_content(
                url=item.url,
                title=item.title,
                markdown=item.content,
                metadata={"scraped_at": item.scraped_at.isoformat()},
                filtered=not passed,
                filter_reason=reason,
            )

            if passed:
                filtered.append(item)
            else:
                logger.debug(f"Filtered out {item.url}: {reason}")

        logger.info(f"Filtered {len(content)} to {len(filtered)} items")

        # Update stats
        self.job_manager.update_job_stats(
            self.current_job, filtered_urls=len(content) - len(filtered)
        )

        return filtered

    async def _analyze_content(
        self, content: List[ScrapedContent]
    ) -> List[AnalyzedContent]:
        """Analyze content with LLM"""
        if not content:
            return []

        if self.config.no_analysis:
            # Convert to AnalyzedContent with defaults
            return [self._scraped_to_analyzed(s) for s in content]

        analyzer = ContentAnalyzer(self.llm, self.config.analysis)

        # Call the proper analyze_content method with the research query
        try:
            analyzed = await analyzer.analyze_content(content, self.current_job.query)

            # Save analysis to database
            for result in analyzed:
                self.job_db.save_analysis(
                    url=result.url,
                    relevance_score=result.relevance_score,
                    key_points=result.key_points,
                    content_type=result.content_type,
                    analysis_data={
                        "summary": result.summary,
                        "metadata": result.analysis_metadata,
                    },
                )

            # Sort by relevance
            analyzed.sort(key=lambda x: x.relevance_score, reverse=True)

            # Update stats
            self.job_manager.update_job_stats(
                self.current_job,
                analyzed_urls=len(analyzed),
            )

            return analyzed

        except Exception as e:
            logger.error(f"Error analyzing content: {e}")
            # Fallback to basic conversion
            return [self._scraped_to_analyzed(s) for s in content]

    async def _create_bundle(self, content: List[AnalyzedContent], query: str) -> Path:
        """Create the final research bundle"""
        if self.config.dry_run:
            logger.info("DRY RUN: Would create bundle")
            return Path(self.current_job.output_dir)

        output_dir = Path(self.current_job.output_dir)

        # Create bundle
        bundle_creator = SmartBundleCreator(
            llm_provider=self.llm if not self.config.no_analysis else None,
            config=self.config.output,
            research_config=self.config,
        )

        bundle_path = await bundle_creator.create_bundle(
            content, query, output_dir, synthesis=None  # TODO: Add synthesis generation
        )

        # Create prominent bundle file
        await self._create_prominent_bundle(output_dir, content, query)

        logger.info(f"Bundle created at: {bundle_path}")
        return bundle_path

    async def _create_prominent_bundle(
        self, output_dir: Path, content: List[AnalyzedContent], query: str
    ):
        """Create the prominent RESEARCH_BUNDLE.md file"""
        bundle_path = output_dir / "📚_RESEARCH_BUNDLE.md"

        # Create header
        bundle_content = f"""# 📚 Research Bundle: {query}

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Job ID**: {self.current_job.job_id}  
**Total Sources**: {len(content)}

---

## 📊 Executive Summary

This research bundle contains {len(content)} carefully selected sources about "{query}".

"""

        # Add table of contents
        bundle_content += "## 📑 Table of Contents\n\n"
        for i, item in enumerate(content, 1):
            title = item.title or f"Source {i}"
            bundle_content += f"{i}. [{title}](#{i}-{self._slugify(title)})\n"

        bundle_content += "\n---\n\n"

        # Add all content
        for i, item in enumerate(content, 1):
            title = item.title or f"Source {i}"
            bundle_content += f"## {i}. {title}\n\n"
            bundle_content += f"**Source**: {item.url}\n"

            if hasattr(item, "relevance_score"):
                bundle_content += f"**Relevance**: {item.relevance_score}/10\n"

            if hasattr(item, "key_points") and item.key_points:
                bundle_content += "\n### Key Points:\n"
                for point in item.key_points:
                    bundle_content += f"- {point}\n"

            bundle_content += f"\n### Content:\n\n{item.content}\n\n"
            bundle_content += "---\n\n"

        # Write bundle
        with safe_open(bundle_path, "w", encoding="utf-8") as f:
            if f:
                f.write(bundle_content)

        logger.info(f"Created prominent bundle: {bundle_path}")

        # Also create executive summary
        summary_path = output_dir / "📊_EXECUTIVE_SUMMARY.md"
        summary_content = f"""# 📊 Executive Summary: {query}

**Job ID**: {self.current_job.job_id}  
**Date**: {datetime.now().strftime('%Y-%m-%d')}

## Overview

Research on "{query}" yielded {len(content)} high-quality sources.

## Top Sources

"""

        for i, item in enumerate(content[:5], 1):  # Top 5
            summary_content += f"{i}. **{item.title}**\n"
            if hasattr(item, "summary"):
                summary_content += f"   - {item.summary[:200]}...\n"
            summary_content += f"   - [Link]({item.url})\n\n"

        with safe_open(summary_path, "w", encoding="utf-8") as f:
            if f:
                f.write(summary_content)

    def _scraped_to_analyzed(self, scraped: ScrapedContent) -> AnalyzedContent:
        """Convert ScrapedContent to AnalyzedContent"""
        return AnalyzedContent(
            url=scraped.url,
            title=scraped.title,
            content=scraped.content,
            relevance_score=5.0,  # Default
            key_points=[],
            summary="",
            content_type="unknown",
            analysis_metadata={},
        )

    def _basic_html_to_markdown(self, html: str) -> str:
        """Basic HTML to Markdown conversion"""
        import re

        # Remove script and style tags
        html = re.sub(
            r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE
        )
        html = re.sub(
            r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE
        )

        # Basic conversions
        conversions = [
            (r"<h1[^>]*>(.*?)</h1>", r"# \1\n"),
            (r"<h2[^>]*>(.*?)</h2>", r"## \1\n"),
            (r"<h3[^>]*>(.*?)</h3>", r"### \1\n"),
            (r"<p[^>]*>(.*?)</p>", r"\1\n\n"),
            (r"<strong[^>]*>(.*?)</strong>", r"**\1**"),
            (r"<b[^>]*>(.*?)</b>", r"**\1**"),
            (r"<em[^>]*>(.*?)</em>", r"*\1*"),
            (r"<i[^>]*>(.*?)</i>", r"*\1*"),
            (r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', r"[\2](\1)"),
            (r"<br[^>]*>", "\n"),
            (r"<[^>]+>", ""),  # Remove remaining tags
        ]

        for pattern, replacement in conversions:
            html = re.sub(pattern, replacement, html, flags=re.IGNORECASE | re.DOTALL)

        # Clean up
        html = re.sub(r"\n{3,}", "\n\n", html)
        return html.strip()

    def _slugify(self, text: str) -> str:
        """Create URL-safe slug from text"""
        import re

        text = re.sub(r"[^\w\s-]", "", text.lower())
        text = re.sub(r"[-\s]+", "-", text)
        return text[:50]

    def _create_empty_result(self) -> ResearchResult:
        """Create empty result when no URLs found"""
        return ResearchResult(
            query=self.current_job.query if self.current_job else "",
            job_id=self.current_job.job_id if self.current_job else "",
            urls_found=0,
            scraped_content=[],
            analyzed_content=[],
            bundle_path=(
                Path(self.current_job.output_dir) if self.current_job else Path()
            ),
            bundle_created=False,
            output_dir=(
                Path(self.current_job.output_dir) if self.current_job else Path()
            ),
        )

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of a research job"""
        job = self.job_manager.get_job(job_id)
        if not job:
            return {"error": f"Job {job_id} not found"}

        return self.job_manager.get_job_info(job)

    async def list_jobs(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all research jobs"""
        return self.job_manager.list_jobs(status)
