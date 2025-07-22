"""
m1f-research: AI-powered research extension for m1f

This module provides functionality to research any topic by:
- Using LLMs to find relevant URLs
- Scraping web content
- Converting HTML to Markdown
- Creating organized bundles from research findings
"""

from .cli import ResearchCommand, main
from .llm_interface import LLMProvider, ClaudeProvider, GeminiProvider, CLIProvider, get_provider
from .config import ResearchConfig, LLMConfig, ScrapingConfig, OutputConfig, AnalysisConfig
from .orchestrator import ResearchOrchestrator
from .models import ResearchResult, ScrapedContent, AnalyzedContent, ResearchSource
from .scraper import SmartScraper
from .content_filter import ContentFilter
from .analyzer import ContentAnalyzer
from .bundle_creator import SmartBundleCreator
from .readme_generator import ReadmeGenerator
from .analysis_templates import TEMPLATES, get_template

try:
    from .._version import __version__, __version_info__
except ImportError:
    # Fallback for when running as a script
    __version__ = "3.7.2"
    __version_info__ = (3, 7, 2)
__all__ = [
    # Version
    "__version__",
    "__version_info__",
    
    # CLI
    "ResearchCommand",
    "main",
    
    # LLM
    "LLMProvider",
    "ClaudeProvider", 
    "GeminiProvider",
    "CLIProvider",
    "get_provider",
    
    # Config
    "ResearchConfig",
    "LLMConfig",
    "ScrapingConfig", 
    "OutputConfig",
    "AnalysisConfig",
    
    # Core
    "ResearchOrchestrator",
    "SmartScraper",
    "ContentFilter",
    "ContentAnalyzer",
    "SmartBundleCreator",
    "ReadmeGenerator",
    
    # Models
    "ResearchResult",
    "ScrapedContent",
    "AnalyzedContent",
    "ResearchSource",
    
    # Templates
    "TEMPLATES",
    "get_template",
]