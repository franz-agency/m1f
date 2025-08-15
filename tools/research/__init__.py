"""
m1f-research: AI-powered research extension for m1f

This module provides functionality to research any topic by:
- Using LLMs to find relevant URLs
- Scraping web content
- Converting HTML to Markdown
- Creating organized bundles from research findings
"""

from .cli import EnhancedResearchCommand, main
from .llm_interface import (
    LLMProvider,
    ClaudeProvider,
    ClaudeCodeProvider,
    GeminiProvider,
    CLIProvider,
    get_provider,
)
from .config import (
    ResearchConfig,
    LLMConfig,
    ScrapingConfig,
    OutputConfig,
    AnalysisConfig,
)
from .orchestrator import EnhancedResearchOrchestrator
from .models import ResearchResult, ScrapedContent, AnalyzedContent, ResearchSource
from .scraper import SmartScraper
from .content_filter import ContentFilter
from .analyzer import ContentAnalyzer
from .bundle_creator import SmartBundleCreator
from .readme_generator import ReadmeGenerator
from .analysis_templates import TEMPLATES, get_template
from .job_manager import JobManager
from .research_db import ResearchDatabase, JobDatabase, ResearchJob
from .url_manager import URLManager
from .smart_scraper import EnhancedSmartScraper

try:
    from _version import __version__, __version_info__
except ImportError:
    # Fallback for when running as a script
    __version__ = "3.8.2"
    __version_info__ = (3, 8, 2)
__all__ = [
    # Version
    "__version__",
    "__version_info__",
    # CLI
    "EnhancedResearchCommand",
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
    "EnhancedResearchOrchestrator",
    "SmartScraper",
    "EnhancedSmartScraper",
    "ContentFilter",
    "ContentAnalyzer",
    "SmartBundleCreator",
    "ReadmeGenerator",
    # Job Management
    "JobManager",
    "ResearchDatabase",
    "JobDatabase",
    "ResearchJob",
    "URLManager",
    # Models
    "ResearchResult",
    "ScrapedContent",
    "AnalyzedContent",
    "ResearchSource",
    # Templates
    "TEMPLATES",
    "get_template",
]
