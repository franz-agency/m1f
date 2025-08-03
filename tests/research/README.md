# M1F-Research Test Suite

Comprehensive test suite for the m1f-research tool with 5 test files and ~25 test methods, covering research workflows, LLM integration, and content analysis.

## 📁 Test Structure

```
tests/research/
├── README.md                           # This file
├── conftest.py                         # Research-specific test fixtures (if exists)
│
├── Core Workflow Tests
│   ├── test_research_workflow.py       # End-to-end research workflows
│   └── test_scraping_integration.py    # Web scraping integration
│
├── Analysis Tests
│   ├── test_content_analysis.py        # Content analysis and scoring
│   └── test_analysis_templates.py      # Template system tests
│
└── Provider Tests
    └── test_llm_providers.py           # LLM provider integrations
```

## 🧪 Test Categories

### 1. **Research Workflows**

**End-to-End Workflows** (`test_research_workflow.py`):
- 🔄 Complete research pipelines
- 📊 Multi-stage processing
- 🎯 Goal-oriented workflows
- 📝 Report generation
- ⚡ Workflow optimization

**Scraping Integration** (`test_scraping_integration.py`):
- 🌐 Full scraping workflow
- 🔀 Concurrent scraping behavior
- 🔄 Retry mechanisms
- ⏱️ Rate limiting compliance
- 🤖 Robots.txt respect
- 📝 HTML to Markdown conversion
- ⚠️ Error handling
- 📊 Progress tracking
- 📋 Metadata extraction

### 2. **Content Analysis**

**Content Analysis** (`test_content_analysis.py`):
- 🔍 Content filtering pipeline
- 🚫 Spam detection
- 🌍 Language detection
- 📊 Quality scoring
- 🔄 Duplicate detection
- 🤖 LLM-based analysis
- 📋 Template-based scoring
- 🔀 Batch processing
- ⚠️ Error recovery

**Analysis Templates** (`test_analysis_templates.py`):
- 📋 Template loading and parsing
- 🎯 Template application
- 🔧 Custom template creation
- 📊 Scoring adjustments
- 🔄 Template inheritance
- ⚙️ Dynamic templates

### 3. **LLM Provider Integration**

**Provider Tests** (`test_llm_providers.py`):
- 🤖 Provider abstraction layer
- 🔌 Multiple provider support
- 🔄 Fallback mechanisms
- 📊 Response parsing
- ⚠️ Error handling
- 💰 Cost tracking
- 🚦 Rate limit handling
- 🔐 Authentication

## 🧪 Test Fixtures

**Core Fixtures:**
- `default_scraping_config` - Standard scraping configuration
- `default_analysis_config` - Standard analysis configuration
- `mock_llm_provider` - Mock LLM provider for testing
- `mock_aiohttp_session` - Mock HTTP session
- `sample_scraped_content_list` - Sample scraped content
- `temp_dir` - Temporary directory for test files

**Mock Objects:**
- LLM API responses
- Web scraping results
- Content analysis outputs
- Template configurations

## 🚀 Running Tests

### Run All Research Tests
```bash
pytest tests/research/ -v
```

### Run Specific Test Files
```bash
# Workflow tests
pytest tests/research/test_research_workflow.py -v

# Scraping tests
pytest tests/research/test_scraping_integration.py -v

# Analysis tests
pytest tests/research/test_content_analysis.py -v

# LLM provider tests
pytest tests/research/test_llm_providers.py -v
```

### Run with Options
```bash
# Async test support
pytest tests/research/ -v --asyncio-mode=auto

# Show output
pytest tests/research/ -s

# Run specific test
pytest tests/research/test_scraping_integration.py::TestScrapingIntegration::test_full_scraping_workflow -v

# With coverage
pytest tests/research/ --cov=tools.research --cov-report=html
```

## 📊 Test Coverage

**Scraping Integration:**
- URL processing and validation
- Concurrent request handling
- Rate limiting and delays
- Retry logic with backoff
- Robots.txt compliance
- HTML to Markdown conversion
- Error recovery strategies

**Content Analysis:**
- Quality assessment algorithms
- Language detection accuracy
- Spam filtering effectiveness
- Duplicate detection methods
- LLM prompt engineering
- Template matching logic
- Batch processing efficiency

**LLM Integration:**
- Provider initialization
- API request formatting
- Response parsing
- Token usage tracking
- Cost calculation
- Error handling
- Fallback strategies

## 🧪 Testing Patterns

### Async Testing
```python
@pytest.mark.asyncio
async def test_async_workflow():
    """Test async research workflow."""
    async with aiohttp.ClientSession() as session:
        result = await research_function(session)
        assert result.success
```

### Mock LLM Providers
```python
def test_llm_analysis(mock_llm_provider):
    """Test with mocked LLM."""
    mock_llm_provider.analyze.return_value = AsyncMock(
        return_value={"score": 0.9, "summary": "test"}
    )
    # Test implementation
```

### Integration Testing
```python
async def test_full_pipeline():
    """Test complete research pipeline."""
    # Setup
    config = ResearchConfig(...)
    
    # Execute
    results = await run_research_pipeline(config)
    
    # Verify
    assert all(r.analyzed for r in results)
```

## 📝 Writing New Tests

### Test Template
```python
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock
from tools.research import ResearchWorkflow

class TestNewFeature:
    """Tests for new research feature."""
    
    @pytest.mark.asyncio
    async def test_feature(self, mock_llm_provider, sample_scraped_content_list):
        """Test description."""
        # Arrange
        workflow = ResearchWorkflow(
            llm_provider=mock_llm_provider
        )
        
        # Act
        results = await workflow.process(sample_scraped_content_list)
        
        # Assert
        assert len(results) > 0
        assert all(r.processed for r in results)
```

### Best Practices
1. **Use async fixtures** - For async components
2. **Mock external APIs** - Don't make real API calls
3. **Test error paths** - Include failure scenarios
4. **Verify concurrency** - Test parallel execution
5. **Check rate limits** - Ensure compliance

## 🔧 Troubleshooting

### Common Issues

**Async Test Failures:**
- Ensure `pytest-asyncio` is installed
- Use `@pytest.mark.asyncio` decorator
- Handle async context managers properly

**Mock Issues:**
- Use `AsyncMock` for async functions
- Configure return values correctly
- Reset mocks between tests

**Integration Problems:**
- Check fixture dependencies
- Verify test data consistency
- Monitor resource cleanup

### Debug Commands
```bash
# Run with debug logging
pytest tests/research/ -v --log-cli-level=DEBUG

# Run with traceback
pytest tests/research/ --tb=long

# Run specific test with output
pytest tests/research/test_content_analysis.py::test_spam_detection -vvs
```

## 🛠️ Maintenance

- **Mock updates** - Keep mocks synchronized with actual APIs
- **Test data** - Update sample content regularly
- **Performance** - Monitor test execution time
- **Coverage** - Maintain comprehensive test coverage
- **Documentation** - Update when adding new features
