"""
pytest configuration for m1f-research tests
"""
import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing"""
    def _mock_response(query):
        if "search" in query.lower():
            return {
                "urls": [
                    "https://example.com/article1",
                    "https://example.com/article2",
                    "https://example.com/article3"
                ]
            }
        elif "analyze" in query.lower():
            return {
                "relevance": 8,
                "key_points": ["Point 1", "Point 2", "Point 3"],
                "content_type": "tutorial"
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