"""
Data models for m1f-research
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class ResearchResult:
    """Complete research result"""
    query: str
    bundle_path: str
    sources_found: int
    sources_scraped: int
    sources_analyzed: int
    sources_included: int
    generated_at: datetime
    config: Dict[str, Any]


@dataclass 
class ScrapedContent:
    """Scraped web content"""
    url: str
    title: str
    html: str
    markdown: str
    scraped_at: datetime
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalyzedContent:
    """Analyzed content with relevance and insights"""
    url: str
    title: str
    content: str  # markdown content
    relevance_score: float  # 0-10
    key_points: List[str]
    summary: str
    content_type: Optional[str] = None  # tutorial, reference, blog, etc.
    analysis_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResearchSource:
    """A source for research (web, github, arxiv, etc.)"""
    name: str
    type: str
    weight: float = 1.0
    config: Dict[str, Any] = field(default_factory=dict)