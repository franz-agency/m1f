"""
Research orchestrator - coordinates the research workflow
"""
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import logging

from .config import ResearchConfig
from .llm_interface import get_provider, LLMProvider
from .models import ResearchResult, ScrapedContent, AnalyzedContent


logger = logging.getLogger(__name__)


class ResearchOrchestrator:
    """Orchestrates the entire research workflow"""
    
    def __init__(self, config: ResearchConfig):
        self.config = config
        self.llm = self._init_llm()
        self.results: List[ResearchResult] = []
        
    def _init_llm(self) -> LLMProvider:
        """Initialize LLM provider from config"""
        return get_provider(
            self.config.llm.provider,
            api_key=None,  # Will use env var
            model=self.config.llm.model
        )
    
    async def run(self, query: str) -> Path:
        """
        Run the complete research workflow
        
        Returns:
            Path to the generated bundle
        """
        logger.info(f"Starting research for: {query}")
        
        # Create output directory
        output_dir = self._create_output_dir(query)
        
        # Step 1: Search for URLs
        if not self.config.dry_run:
            urls = await self._search_urls(query)
            logger.info(f"Found {len(urls)} URLs")
        else:
            logger.info("DRY RUN: Would search for URLs")
            urls = []
        
        # Step 2: Scrape content
        if not self.config.dry_run and urls:
            scraped_content = await self._scrape_urls(urls[:self.config.scrape_count])
            logger.info(f"Scraped {len(scraped_content)} pages")
            
            # Pre-filter scraped content if filtering is enabled
            if not self.config.no_filter and scraped_content:
                from .content_filter import ContentFilter
                pre_filter = ContentFilter(self.config.analysis)
                scraped_content = pre_filter.filter_scraped_content(scraped_content)
                logger.info(f"Pre-filtered to {len(scraped_content)} pages")
        else:
            logger.info("DRY RUN: Would scrape URLs")
            scraped_content = []
        
        # Step 3: Analyze content (if enabled)
        if not self.config.no_analysis and scraped_content and not self.config.dry_run:
            analyzed_content = await self._analyze_content(scraped_content, query)
            logger.info(f"Analyzed {len(analyzed_content)} pages")
        else:
            analyzed_content = [
                AnalyzedContent(
                    url=sc.url,
                    title=sc.title,
                    content=sc.markdown,
                    relevance_score=5.0,
                    key_points=[],
                    summary=""
                ) for sc in scraped_content
            ]
        
        # Step 4: Filter content (if enabled)
        if not self.config.no_filter and analyzed_content:
            filtered_content = self._filter_content(analyzed_content)
            logger.info(f"Filtered to {len(filtered_content)} relevant pages")
        else:
            filtered_content = analyzed_content
        
        # Step 5: Create bundle
        if filtered_content and not self.config.dry_run:
            bundle_path = await self._create_bundle(filtered_content, query, output_dir)
            logger.info(f"Created bundle at: {bundle_path}")
            return bundle_path
        else:
            logger.info("DRY RUN: Would create bundle")
            return output_dir / "research-bundle.md"
    
    async def run_interactive(self):
        """Run in interactive mode"""
        print("🔍 Welcome to m1f-research interactive mode!")
        print("Type 'exit' or 'quit' to stop.\n")
        
        while True:
            try:
                query = input("What would you like to research? > ").strip()
                
                if query.lower() in ['exit', 'quit']:
                    print("👋 Goodbye!")
                    break
                
                if not query:
                    continue
                
                # Run research
                bundle_path = await self.run(query)
                print(f"\n✅ Research complete! Bundle saved to: {bundle_path}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")
                if self.config.verbose > 0:
                    import traceback
                    traceback.print_exc()
    
    def _create_output_dir(self, query: str) -> Path:
        """Create output directory with hierarchical structure: YYYY/MM/DD/query_HHMMSS"""
        now = datetime.now()
        
        # Create hierarchical date structure
        year = now.strftime("%Y")
        month = now.strftime("%m")
        day = now.strftime("%d")
        
        # Sanitize query for directory name
        safe_name = "".join(c if c.isalnum() or c in "- " else "_" for c in query)
        safe_name = safe_name.replace(" ", "-").lower()[:40]  # Shorter to allow for timestamp
        
        # Add time for uniqueness
        time_suffix = now.strftime("%H%M%S")
        dir_name = f"{safe_name}_{time_suffix}"
        
        # Build hierarchical path: research-data/2025/07/22/query_171851/
        output_dir = self.config.output.directory / year / month / day / dir_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        return output_dir
    
    async def _search_urls(self, query: str) -> List[Dict[str, str]]:
        """Search for URLs using LLM"""
        try:
            urls = await self.llm.search_web(query, self.config.url_count)
            
            # Save URLs to file for reference
            if self.config.output.include_metadata:
                urls_file = self.config.output.directory / "search_results.json"
                urls_file.parent.mkdir(parents=True, exist_ok=True)
                with open(urls_file, 'w') as f:
                    json.dump(urls, f, indent=2)
            
            return urls
            
        except Exception as e:
            logger.error(f"Error searching for URLs: {e}")
            return []
    
    async def _scrape_urls(self, urls: List[Dict[str, str]]) -> List[ScrapedContent]:
        """Scrape content from URLs"""
        from .scraper import SmartScraper
        
        # Create progress callback if verbose
        def progress_callback(completed, total):
            if self.config.verbose > 0:
                logger.info(f"Scraping progress: {completed}/{total} ({completed/total*100:.1f}%)")
        
        # Use SmartScraper for advanced scraping
        async with SmartScraper(self.config.scraping) as scraper:
            if self.config.verbose > 0:
                scraper.set_progress_callback(progress_callback)
            
            scraped = await scraper.scrape_urls(urls)
            
            # Log statistics
            stats = scraper.get_stats()
            logger.info(f"Scraping complete: {stats['success_rate']*100:.1f}% success rate")
            
            if stats['failed_urls'] > 0:
                logger.warning(f"Failed to scrape {stats['failed_urls']} URLs")
                if self.config.verbose > 1:
                    for url in stats['failed_url_list']:
                        logger.debug(f"  Failed: {url}")
        
        return scraped
    
    async def _analyze_content(self, content: List[ScrapedContent], query: str) -> List[AnalyzedContent]:
        """Analyze scraped content for relevance and key points"""
        from .analyzer import ContentAnalyzer
        
        # Get template name from config if available
        template_name = getattr(self.config, 'template', 'general')
        
        # Use ContentAnalyzer for comprehensive analysis
        analyzer = ContentAnalyzer(self.llm, self.config.analysis, template_name=template_name)
        analyzed = await analyzer.analyze_content(content, query)
        
        # Log analysis results
        avg_relevance = sum(item.relevance_score for item in analyzed) / len(analyzed) if analyzed else 0
        logger.info(f"Average relevance score: {avg_relevance:.1f}/10")
        
        # Extract and log topics
        topics = await analyzer.extract_topics(analyzed)
        if topics['primary']:
            logger.info(f"Primary topics: {', '.join(topics['primary'][:5])}")
        
        return analyzed
    
    def _filter_content(self, content: List[AnalyzedContent]) -> List[AnalyzedContent]:
        """Filter content based on configuration"""
        from .content_filter import ContentFilter
        
        # Use ContentFilter for advanced filtering
        filter = ContentFilter(self.config.analysis)
        filtered = filter.filter_analyzed_content(content)
        
        # Sort by relevance
        filtered.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Log filter statistics
        stats = filter.get_filter_stats()
        logger.info(f"Filter stats: {stats['duplicate_checks']} duplicate checks performed")
        
        return filtered
    
    async def _create_bundle(self, content: List[AnalyzedContent], query: str, output_dir: Path) -> Path:
        """Create the final research bundle using SmartBundleCreator"""
        from .bundle_creator import SmartBundleCreator
        
        # Generate synthesis if we have an analyzer and it's enabled
        synthesis = None
        if not self.config.no_analysis and self.config.output.create_summary:
            from .analyzer import ContentAnalyzer
            analyzer = ContentAnalyzer(self.llm, self.config.analysis)
            synthesis = await analyzer.generate_synthesis(content, query)
        
        # Use SmartBundleCreator for intelligent organization
        bundle_creator = SmartBundleCreator(
            llm_provider=self.llm if not self.config.no_analysis else None,
            config=self.config.output,
            research_config=self.config
        )
        
        bundle_path = await bundle_creator.create_bundle(
            content_list=content,
            research_query=query,
            output_dir=output_dir,
            synthesis=synthesis
        )
        
        return bundle_path