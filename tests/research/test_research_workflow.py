"""
End-to-end tests for m1f-research workflow
"""
import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

from tools.research import (
    ResearchConfig, 
    EnhancedResearchOrchestrator,
    ClaudeProvider,
    EnhancedResearchCommand
)
from tools.research.models import ScrapedContent, AnalyzedContent


class TestResearchWorkflow:
    """Test the complete research workflow"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test output"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def mock_config(self, temp_dir):
        """Create a test configuration"""
        config = ResearchConfig(
            query="test query",
            url_count=5,
            scrape_count=3,
            dry_run=False,
            verbose=1,
            no_filter=True,  # Disable filtering for easier testing
            no_analysis=False
        )
        # Set the search limit explicitly
        config.scraping.search_limit = 5
        config.output.directory = temp_dir
        # Adjust minimum content length for test content
        config.analysis.min_content_length = 20
        return config
    
    @pytest.fixture
    def mock_llm_provider(self):
        """Create a mock LLM provider"""
        provider = MagicMock(spec=ClaudeProvider)
        
        # Mock search_web
        async def mock_search_web(query, num_results):
            return [
                {"url": f"https://example{i}.com", "title": f"Example {i}", "description": f"Description {i}"}
                for i in range(num_results)
            ]
        
        # Mock query method for analyzer
        async def mock_query(prompt, system=None, **kwargs):
            from tools.research.llm_interface import LLMResponse
            return LLMResponse(
                content='{"relevance_score": 8.0, "key_points": ["Point 1", "Point 2"], "summary": "Test summary", "content_type": "tutorial"}',
                usage={"total_tokens": 100},
                error=None
            )
        
        # Mock analyze_content
        async def mock_analyze_content(content, analysis_type):
            if analysis_type == "relevance":
                return {
                    "relevance_score": 8.0,
                    "reason": "Highly relevant",
                    "key_topics": ["topic1", "topic2"]
                }
            elif analysis_type == "summary":
                return {
                    "summary": "This is a summary",
                    "main_points": ["Point 1", "Point 2"],
                    "content_type": "tutorial"
                }
            return {}
        
        provider.query = AsyncMock(side_effect=mock_query)
        provider.search_web = AsyncMock(side_effect=mock_search_web)
        provider.analyze_content = AsyncMock(side_effect=mock_analyze_content)
        
        return provider
    
    @pytest.mark.asyncio
    async def test_basic_research_workflow(self, mock_config, mock_llm_provider, temp_dir):
        """Test basic research workflow end-to-end"""
        # Create orchestrator with mocked LLM
        orchestrator = EnhancedResearchOrchestrator(mock_config)
        orchestrator.llm = mock_llm_provider
        
        # Mock scraping to avoid actual web requests
        async def mock_scrape_urls(urls):
            return [
                ScrapedContent(
                    url=url,
                    title=f"Title for {url}",
                    content=f"Content from {url}",
                    content_type="text/html"
                )
                for url in urls[:3]
            ]
        
        orchestrator._scrape_urls = mock_scrape_urls
        
        # Mock the bundle creation to ensure it creates a file
        async def mock_create_bundle(content, query):
            # Use the orchestrator's output directory
            output_dir = orchestrator.current_job.output_dir if orchestrator.current_job else mock_config.output.directory
            # Convert to Path if it's a string
            output_dir = Path(output_dir) if isinstance(output_dir, str) else output_dir
            # Ensure the output directory exists
            output_dir.mkdir(parents=True, exist_ok=True)
            bundle_path = output_dir / "research-bundle.md"
            bundle_content = f"""# Research: {query}

## Summary
Total sources: {len(content)}

## Results
"""
            for i, item in enumerate(content):
                bundle_content += f"### {item.title}\n{item.content}\n\n"
            
            bundle_path.write_text(bundle_content)
            return bundle_path
        
        orchestrator._create_bundle = mock_create_bundle
        
        # Run research
        result = await orchestrator.research("test query")
        
        # Verify results
        assert result.bundle_path is not None
        assert result.bundle_path.exists()
        assert result.bundle_path.suffix == ".md"
        
        # Check bundle content
        content = result.bundle_path.read_text()
        assert "Research: test query" in content
        assert "Total sources: 3" in content
        assert "https://example0.com" in content
        
        # Verify LLM was called for search
        mock_llm_provider.search_web.assert_called_once_with("test query", 5)
        # Analysis happens via query method, not analyze_content in the workflow
        assert mock_llm_provider.query.call_count > 0
    
    @pytest.mark.asyncio
    async def test_dry_run_mode(self, mock_config, mock_llm_provider, temp_dir):
        """Test dry run mode doesn't perform actual operations"""
        mock_config.dry_run = True
        
        orchestrator = EnhancedResearchOrchestrator(mock_config)
        orchestrator.llm = mock_llm_provider
        
        # Run in dry mode
        result = await orchestrator.research("test query")
        
        # Verify no actual operations were performed
        mock_llm_provider.search_web.assert_not_called()
        mock_llm_provider.analyze_content.assert_not_called()
        
        # In dry run mode, bundle path is set to output dir but no bundle file is created
        assert result.bundle_path is not None
        assert result.bundle_path.is_dir()  # It's the output directory, not a file
        assert not result.bundle_created  # Bundle was not actually created
    
    @pytest.mark.asyncio
    async def test_no_analysis_mode(self, mock_config, mock_llm_provider, temp_dir):
        """Test running without analysis"""
        mock_config.no_analysis = True
        
        orchestrator = EnhancedResearchOrchestrator(mock_config)
        orchestrator.llm = mock_llm_provider
        
        # Mock scraping
        async def mock_scrape_urls(urls):
            return [
                ScrapedContent(
                    url=f"https://example{i}.com",
                    title=f"Example {i}",
                    content=f"Content {i}",
                    content_type="text/markdown"
                )
                for i in range(2)
            ]
        
        orchestrator._scrape_urls = mock_scrape_urls
        
        # Run research
        result = await orchestrator.research("test query")
        
        # Verify analysis was skipped
        mock_llm_provider.analyze_content.assert_not_called()
        
        # But search should still happen
        mock_llm_provider.search_web.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_content_filtering(self, mock_config, temp_dir):
        """Test content filtering based on relevance"""
        mock_config.analysis.relevance_threshold = 7.0
        mock_config.analysis.min_content_length = 50  # Lower threshold for test
        
        orchestrator = EnhancedResearchOrchestrator(mock_config)
        
        # Create test content with different relevance scores
        content = [
            AnalyzedContent(
                url="https://high.com",
                title="High relevance",
                content="This is high-quality content with substantial information about the topic.",
                relevance_score=9.0,
                key_points=["Point 1", "Point 2"],
                summary="High quality summary",
                content_type="tutorial"
            ),
            AnalyzedContent(
                url="https://low.com", 
                title="Low relevance",
                content="This is low-quality content with minimal information.",
                relevance_score=4.0,
                key_points=["Point 1"],
                summary="Low quality summary",
                content_type="blog"
            ),
            AnalyzedContent(
                url="https://medium.com",
                title="Medium relevance", 
                content="This is medium-quality content with decent information.",
                relevance_score=7.5,
                key_points=["Point 1", "Point 2", "Point 3"],
                summary="Medium quality summary",
                content_type="reference"
            )
        ]
        
        # Filter content
        from tools.research.content_filter import ContentFilter
        filter = ContentFilter(mock_config.analysis)
        filtered = filter.filter_analyzed_content(content)
        
        # Verify filtering
        assert len(filtered) == 2
        assert all(item.relevance_score >= 7.0 for item in filtered)
        assert filtered[0].relevance_score == 9.0  # Should be sorted by relevance
    
    def test_cli_argument_parsing(self):
        """Test CLI argument parsing"""
        command = EnhancedResearchCommand()
        
        # Test basic args
        args = command.parser.parse_args(["machine learning", "--urls", "30", "--scrape", "15"])
        assert args.query == "machine learning"
        assert args.urls == 30
        assert args.scrape == 15
        
        # Test provider selection
        args = command.parser.parse_args(["test", "--provider", "gemini"])
        assert args.provider == "gemini"
        
        # Test interactive mode
        args = command.parser.parse_args(["--interactive"])
        assert args.interactive is True
        assert args.query is None  # Query not required in interactive mode
    
    @pytest.mark.asyncio
    async def test_config_from_yaml(self, temp_dir):
        """Test loading configuration from YAML"""
        # Create test YAML config
        yaml_content = """
research:
  llm:
    provider: gemini
    model: gemini-pro
    temperature: 0.8
  defaults:
    url_count: 25
    scrape_count: 12
  analysis:
    relevance_threshold: 6.5
  templates:
    technical:
      description: Technical research
      analysis_focus: implementation
      url_count: 30
"""
        config_path = temp_dir / "test_config.yml"
        config_path.write_text(yaml_content)
        
        # Load config
        config = ResearchConfig.from_yaml(config_path)
        
        # Verify loaded values
        assert config.llm.provider == "gemini"
        assert config.llm.model == "gemini-pro"
        assert config.llm.temperature == 0.8
        assert config.url_count == 25
        assert config.scrape_count == 12
        assert config.analysis.relevance_threshold == 6.5
        assert "technical" in config.templates
        assert config.templates["technical"].url_count == 30