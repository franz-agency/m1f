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
pytest configuration for m1f-research tests
"""
import pytest
from pathlib import Path
import tempfile
import shutil
import asyncio
import time
import gc
import sys
from unittest.mock import AsyncMock, MagicMock
import json

from tools.research.models import ScrapedContent, AnalyzedContent
from tools.research.config import ScrapingConfig, AnalysisConfig
from tools.research.llm_interface import LLMProvider, LLMResponse


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files with proper cleanup"""
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    yield temp_path
    
    # Windows-specific cleanup to handle SQLite file locking
    _cleanup_temp_dir_with_retry(temp_path)


def _cleanup_temp_dir_with_retry(temp_path: Path, max_retries: int = 3):
    """Clean up temporary directory with retry logic for Windows SQLite issues"""
    
    # Force garbage collection to close any remaining database connections
    gc.collect()
    
    for attempt in range(max_retries):
        try:
            # First, try to find and cleanup any SQLite databases
            for db_file in temp_path.rglob("*.db"):
                try:
                    # Force close any connections by attempting to connect and immediately close
                    import sqlite3
                    conn = sqlite3.connect(str(db_file))
                    conn.close()
                    
                    # On Windows, sometimes we need a brief delay
                    if sys.platform == "win32":
                        time.sleep(0.1)
                        
                except Exception:
                    pass  # Ignore errors here
            
            # Now try to remove the directory
            shutil.rmtree(temp_path)
            return  # Success!
            
        except (OSError, PermissionError) as e:
            if attempt < max_retries - 1:
                # Wait a bit and try again
                time.sleep(0.5 * (attempt + 1))
                gc.collect()  # Force garbage collection again
            else:
                # Last attempt failed, log the error but don't fail the test
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to cleanup temp directory after {max_retries} attempts: {e}")
                # Try to at least remove files one by one
                try:
                    for file_path in temp_path.rglob("*"):
                        if file_path.is_file():
                            try:
                                file_path.unlink()
                            except Exception:
                                pass
                except Exception:
                    pass


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing"""

    def _mock_response(query):
        if "search" in query.lower():
            return {
                "urls": [
                    "https://example.com/article1",
                    "https://example.com/article2",
                    "https://example.com/article3",
                ]
            }
        elif "analyze" in query.lower():
            return {
                "relevance": 8,
                "key_points": ["Point 1", "Point 2", "Point 3"],
                "content_type": "tutorial",
            }
        return {"response": "Mock response"}

    return _mock_response


@pytest.fixture
def sample_html_content():
    """Sample HTML content for testing"""
    return """
    <html>
        <head><title>Test Article</title></head>
        <body>
            <h1>Sample Article Title</h1>
            <p>This is a sample article about testing.</p>
            <p>It contains multiple paragraphs with useful content.</p>
            <code>def example(): pass</code>
        </body>
    </html>
    """


@pytest.fixture
def sample_markdown_content():
    """Expected markdown conversion of sample HTML"""
    return """# Sample Article Title

This is a sample article about testing.

It contains multiple paragraphs with useful content.

```
def example(): pass
```"""


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp session for testing"""
    session = AsyncMock()

    async def mock_get(url, **kwargs):
        response = AsyncMock()
        response.status = 200
        response.url = url
        response.headers = {"Content-Type": "text/html"}
        response.text = AsyncMock(return_value="<html><body>Mock content</body></html>")
        return response

    session.get = mock_get
    return session


@pytest.fixture
def default_scraping_config():
    """Default scraping configuration for tests"""
    return ScrapingConfig(
        max_concurrent=3,
        timeout_range="0.1-0.2",
        retry_attempts=2,
        user_agents=["TestAgent/1.0"],
        headers={"Accept": "text/html"},
        respect_robots_txt=False,
    )


@pytest.fixture
def default_analysis_config():
    """Default analysis configuration for tests"""
    return AnalysisConfig(
        min_content_length=100,
        max_content_length=10000,
        relevance_threshold=5.0,
        language="en",
        prefer_code_examples=True,
    )


@pytest.fixture
def mock_llm_provider():
    """Create a mock LLM provider for testing"""
    provider = AsyncMock(spec=LLMProvider)

    async def mock_query(prompt):
        # Default mock response
        return LLMResponse(
            content=json.dumps(
                {
                    "relevance_score": 7.0,
                    "key_points": ["Test point 1", "Test point 2"],
                    "summary": "Test summary of content",
                    "content_type": "article",
                }
            ),
            tokens_used=100,
        )

    provider.query = mock_query
    return provider


@pytest.fixture
def sample_scraped_content_list():
    """List of sample scraped content for testing"""
    from datetime import datetime

    return [
        ScrapedContent(
            url="https://example.com/article1",
            title="Test Article 1",
            html="<html><body>Content 1</body></html>",
            markdown="# Test Article 1\n\nContent 1",
            scraped_at=datetime.now(),
            metadata={"status_code": 200},
        ),
        ScrapedContent(
            url="https://example.com/article2",
            title="Test Article 2",
            html="<html><body>Content 2</body></html>",
            markdown="# Test Article 2\n\nContent 2",
            scraped_at=datetime.now(),
            metadata={"status_code": 200},
        ),
        ScrapedContent(
            url="https://example.com/article3",
            title="Test Article 3",
            html="<html><body>Content 3</body></html>",
            markdown="# Test Article 3\n\nContent 3",
            scraped_at=datetime.now(),
            metadata={"status_code": 200},
        ),
    ]


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def research_temp_dir():
    """
    Specialized temporary directory fixture for research tests that need database cleanup
    This ensures proper cleanup of SQLite databases before directory removal
    """
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    
    # Store references to cleanup functions
    orchestrators = []
    
    class TempDirManager:
        def __init__(self, path):
            self.path = path
            self.orchestrators = []
        
        def register_orchestrator(self, orchestrator):
            """Register an orchestrator for cleanup"""
            self.orchestrators.append(orchestrator)
        
        def cleanup_orchestrators(self):
            """Clean up all registered orchestrators"""
            for orchestrator in self.orchestrators:
                try:
                    if hasattr(orchestrator, 'cleanup_databases'):
                        orchestrator.cleanup_databases()
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug(f"Error cleaning up orchestrator: {e}")
            self.orchestrators.clear()
    
    manager = TempDirManager(temp_path)
    yield manager
    
    # Cleanup orchestrators first
    manager.cleanup_orchestrators()
    
    # Force garbage collection
    gc.collect()
    
    # Then cleanup the directory
    _cleanup_temp_dir_with_retry(temp_path)
