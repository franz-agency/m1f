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
Data models for m1f-research
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


@dataclass
class ResearchResult:
    """Complete research result"""

    query: str
    job_id: str
    urls_found: int
    scraped_content: List["ScrapedContent"]
    analyzed_content: List["AnalyzedContent"]
    bundle_path: Optional["Path"] = None
    bundle_created: bool = False
    output_dir: Optional["Path"] = None
    generated_at: datetime = field(default_factory=datetime.now)
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScrapedContent:
    """Scraped web content"""

    url: str
    title: str
    content: str  # HTML or markdown content
    content_type: str = ""
    scraped_at: datetime = field(default_factory=datetime.now)
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

    # Compatibility with old API
    @property
    def metadata(self) -> Dict[str, Any]:
        return self.analysis_metadata


@dataclass
class ResearchSource:
    """A source for research (web, github, arxiv, etc.)"""

    name: str
    type: str
    weight: float = 1.0
    config: Dict[str, Any] = field(default_factory=dict)
