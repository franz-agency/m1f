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

__version__ = "0.1.0"
__all__ = [
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
    
    # Models
    "ResearchResult",
    "ScrapedContent",
    "AnalyzedContent",
    "ResearchSource",
]