"""
End-to-end tests for m1f-research workflow
"""
import pytest
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

from tools.research import (
    ResearchConfig, 
    ResearchOrchestrator,
    ClaudeProvider,
    ResearchCommand
)
from tools.research.models import ScrapedContent, AnalyzedContent


class TestResearchWorkflow:
    """Test the complete research workflow"""
    
    @pytest.fixture
    def mock_config(self, temp_dir):
        """Create a test configuration"""
        config = ResearchConfig(
            query="test query",
            url_count=5,
            scrape_count=3,
            dry_run=False,
            verbose=1
        )
        config.output.directory = temp_dir
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
        
        provider.search_web = AsyncMock(side_effect=mock_search_web)
        provider.analyze_content = AsyncMock(side_effect=mock_analyze_content)
        
        return provider
    
    @pytest.mark.asyncio
    async def test_basic_research_workflow(self, mock_config, mock_llm_provider, temp_dir):
        """Test basic research workflow end-to-end"""
        # Create orchestrator with mocked LLM
        orchestrator = ResearchOrchestrator(mock_config)
        orchestrator.llm = mock_llm_provider
        
        # Mock scraping to avoid actual web requests
        async def mock_scrape_urls(urls):
            return [
                ScrapedContent(
                    url=url["url"],
                    title=url["title"],
                    html=f"<html><body><p>Content from {url['url']}</p></body></html>",
                    markdown=f"Content from {url['url']}",
                    scraped_at=None
                )
                for url in urls[:3]
            ]
        
        orchestrator._scrape_urls = mock_scrape_urls
        
        # Run research
        bundle_path = await orchestrator.run("test query")
        
        # Verify results
        assert bundle_path.exists()
        assert bundle_path.suffix == ".md"
        
        # Check bundle content
        content = bundle_path.read_text()
        assert "Research: test query" in content
        assert "Total sources: 3" in content
        assert "Example 0" in content
        
        # Verify LLM was called
        mock_llm_provider.search_web.assert_called_once_with("test query", 5)
        assert mock_llm_provider.analyze_content.call_count > 0
    
    @pytest.mark.asyncio
    async def test_dry_run_mode(self, mock_config, mock_llm_provider, temp_dir):
        """Test dry run mode doesn't perform actual operations"""
        mock_config.dry_run = True
        
        orchestrator = ResearchOrchestrator(mock_config)
        orchestrator.llm = mock_llm_provider
        
        # Run in dry mode
        bundle_path = await orchestrator.run("test query")
        
        # Verify no actual operations were performed
        mock_llm_provider.search_web.assert_not_called()
        mock_llm_provider.analyze_content.assert_not_called()
        
        # Bundle path should be returned but not created
        assert not bundle_path.exists()
    
    @pytest.mark.asyncio
    async def test_no_analysis_mode(self, mock_config, mock_llm_provider, temp_dir):
        """Test running without analysis"""
        mock_config.no_analysis = True
        
        orchestrator = ResearchOrchestrator(mock_config)
        orchestrator.llm = mock_llm_provider
        
        # Mock scraping
        async def mock_scrape_urls(urls):
            return [
                ScrapedContent(
                    url=f"https://example{i}.com",
                    title=f"Example {i}",
                    html=f"<p>Content {i}</p>",
                    markdown=f"Content {i}",
                    scraped_at=None
                )
                for i in range(2)
            ]
        
        orchestrator._scrape_urls = mock_scrape_urls
        
        # Run research
        bundle_path = await orchestrator.run("test query")
        
        # Verify analysis was skipped
        mock_llm_provider.analyze_content.assert_not_called()
        
        # But search should still happen
        mock_llm_provider.search_web.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_content_filtering(self, mock_config, temp_dir):
        """Test content filtering based on relevance"""
        mock_config.analysis.relevance_threshold = 7.0
        
        orchestrator = ResearchOrchestrator(mock_config)
        
        # Create test content with different relevance scores
        content = [
            AnalyzedContent(
                url="https://high.com",
                title="High relevance",
                content="Content",
                relevance_score=9.0,
                key_points=[],
                summary=""
            ),
            AnalyzedContent(
                url="https://low.com", 
                title="Low relevance",
                content="Content",
                relevance_score=4.0,
                key_points=[],
                summary=""
            ),
            AnalyzedContent(
                url="https://medium.com",
                title="Medium relevance", 
                content="Content",
                relevance_score=7.5,
                key_points=[],
                summary=""
            )
        ]
        
        # Filter content
        filtered = orchestrator._filter_content(content)
        
        # Verify filtering
        assert len(filtered) == 2
        assert all(item.relevance_score >= 7.0 for item in filtered)
        assert filtered[0].relevance_score == 9.0  # Should be sorted by relevance
    
    def test_cli_argument_parsing(self):
        """Test CLI argument parsing"""
        command = ResearchCommand()
        
        # Test basic args
        args = command.parse_args(["machine learning", "--urls", "30", "--scrape", "15"])
        assert args.query == "machine learning"
        assert args.urls == 30
        assert args.scrape == 15
        
        # Test provider selection
        args = command.parse_args(["test", "--provider", "gemini"])
        assert args.provider == "gemini"
        
        # Test interactive mode
        args = command.parse_args(["--interactive"])
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