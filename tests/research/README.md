# m1f-research Integration Tests

This directory contains comprehensive integration tests for the m1f-research
scraping and content analysis pipeline.

## Test Structure

### test_scraping_integration.py

Tests the complete web scraping workflow including:

- **Full scraping workflow** - End-to-end scraping of multiple URLs
- **Concurrent scraping behavior** - Validates concurrency limits are respected
- **Retry mechanism** - Tests automatic retry on failed requests
- **Rate limiting** - Ensures proper delays between requests
- **Robots.txt compliance** - Tests respect for robots.txt when enabled
- **HTML to Markdown conversion** - Validates quality of HTML conversion
- **Error handling** - Tests graceful failure recovery
- **Progress tracking** - Validates progress callback functionality
- **Metadata extraction** - Tests extraction of response metadata

### test_content_analysis.py

Tests the content filtering and LLM-based analysis including:

- **Content filtering pipeline** - Complete filtering workflow
- **Spam detection** - Identifies and filters spam/low-quality content
- **Language detection** - Filters content by language
- **Quality scoring** - Evaluates content structure and readability
- **Duplicate detection** - Identifies and removes duplicate content
- **LLM-based analysis** - Integration with LLM for content analysis
- **Template-based scoring** - Tests scoring adjustments based on templates
- **Batch processing** - Validates concurrent batch analysis
- **Error recovery** - Tests fallback mechanisms for LLM failures

## Running Tests

```bash
# Run all research tests
pytest tests/research/

# Run specific test file
pytest tests/research/test_scraping_integration.py
pytest tests/research/test_content_analysis.py

# Run with verbose output
pytest tests/research/ -vv

# Run specific test
pytest tests/research/test_scraping_integration.py::TestScrapingIntegration::test_full_scraping_workflow
```

## Test Fixtures

The `conftest.py` file provides common fixtures:

- `default_scraping_config` - Standard scraping configuration
- `default_analysis_config` - Standard analysis configuration
- `mock_llm_provider` - Mock LLM provider for testing
- `mock_aiohttp_session` - Mock HTTP session
- `sample_scraped_content_list` - Sample scraped content
- `temp_dir` - Temporary directory for test files

## Key Testing Patterns

1. **Async Testing**: Uses `pytest.mark.asyncio` for async functions
2. **Mocking**: Extensive use of `AsyncMock` for external dependencies
3. **Integration Focus**: Tests component interactions rather than units
4. **Error Scenarios**: Covers various failure modes and recovery
5. **Performance**: Tests concurrency limits and batch processing

## Coverage Areas

- Web scraping with retry and rate limiting
- Content quality assessment
- Language detection
- Spam filtering
- Duplicate detection
- LLM integration
- Template-based scoring
- Error handling and recovery
- Progress tracking
- Metadata extraction
