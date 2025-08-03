# M1F Test Suite Documentation

This directory contains the comprehensive test suite for the m1f tool suite, including m1f, s1f, html2md, m1f-scrape, and m1f-research tools. Built with Python 3.10+ features and modern testing practices.

## Overview

- **43 test files** with ~290 test methods
- **Comprehensive fixture system** with module-specific extensions
- **Multi-platform support** with Windows-specific handling
- **Security testing** with path traversal and secret detection
- **Performance testing** for large files and parallel processing
- **Real-world test data** including international filenames

## Test Structure

```
tests/
├── conftest.py                    # Global fixtures and test configuration
├── base_test.py                   # Base test classes with common utilities
├── test_html2md_server.py         # HTML2MD server tests
├── test_html2md_server_fixed.py   # Fixed server tests
├── test_m1f_claude_improvements.py # Claude-suggested improvements
├── test_simple_server.py          # Simple server tests
│
├── m1f/                           # m1f tests (23 test files, ~180 methods)
│   ├── conftest.py               # m1f-specific fixtures
│   ├── test_m1f_basic.py         # Core functionality
│   ├── test_m1f_advanced.py      # Advanced features
│   ├── test_m1f_encoding.py      # Character encoding
│   ├── test_m1f_integration.py   # End-to-end tests
│   ├── test_m1f_presets_*.py     # Preset system (basic, integration, v3.2)
│   ├── test_security_check.py    # Secret detection
│   ├── test_path_traversal_security.py # Security vulnerabilities
│   ├── test_content_deduplication.py   # File deduplication
│   ├── test_parallel_processing.py     # Async operations
│   ├── test_symlinks*.py         # Symbolic link handling
│   ├── test_large_file.py        # Performance testing
│   ├── test_cross_platform_paths.py # Windows/Linux compatibility
│   └── source/                   # Test data
│       ├── glob_*/               # Pattern matching tests
│       ├── exotic_encodings/     # Non-UTF8 encodings
│       └── advanced_glob_test/   # International filenames
│
├── s1f/                          # s1f tests (6 test files, ~40 methods)
│   ├── conftest.py              # s1f-specific fixtures
│   ├── test_s1f_basic.py        # Core extraction
│   ├── test_s1f_async.py        # Async operations
│   ├── test_s1f_encoding.py     # Encoding preservation
│   ├── test_s1f_target_encoding.py # Encoding conversion
│   ├── test_s1f.py              # General functionality
│   └── test_path_traversal_security.py # Security tests
│
├── html2md/                      # html2md tests (5 test files, ~30 methods)
│   ├── test_html2md.py          # Core conversion
│   ├── test_integration.py      # End-to-end tests
│   ├── test_claude_integration.py # AI optimization
│   ├── test_scrapers.py         # Scraping backends
│   ├── test_local_scraping.py   # Local file processing
│   ├── source/html/             # Test HTML files
│   ├── expected/                # Expected outputs
│   └── scraped_examples/        # Real-world examples
│
├── html2md_server/               # HTML2MD test infrastructure
│   ├── server.py                # Flask test server
│   ├── manage_server.py         # Server management
│   ├── test_pages/              # 8+ complex HTML test pages
│   ├── static/                  # CSS/JS resources
│   └── README.md                # Server documentation
│
└── research/                     # m1f-research tests (5 test files, ~25 methods)
    ├── test_research_workflow.py # End-to-end workflows
    ├── test_llm_providers.py    # LLM integrations
    ├── test_content_analysis.py # Content analysis
    ├── test_analysis_templates.py # Template system
    └── test_scraping_integration.py # Scraping integration
```

## Key Features

### Global Test Infrastructure (conftest.py)

**Core Fixtures:**
- `tools_dir` - Path to tools directory
- `test_data_dir` - Path to test data
- `temp_dir` - Temporary directory with auto-cleanup
- `isolated_filesystem` - Isolated filesystem environment
- `create_test_file` - Factory for creating test files
- `create_test_directory_structure` - Complex directory creation
- `capture_logs` - Log output capture and examination
- `anyio_backend` - Async testing support

**Platform Support:**
- Windows-specific cleanup handling
- Cross-platform path separator handling
- File locking issue mitigation

**Test Markers:**
```python
@pytest.mark.unit         # Fast, isolated unit tests
@pytest.mark.integration  # End-to-end integration tests
@pytest.mark.slow        # Long-running tests
@pytest.mark.requires_git # Tests requiring git
@pytest.mark.encoding    # Encoding-related tests
```

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -vv

# Run specific tool tests
pytest tests/m1f/
pytest tests/s1f/
pytest tests/html2md/
pytest tests/research/

# Run by marker
pytest -m unit              # Fast unit tests only
pytest -m integration       # Integration tests only
pytest -m "not slow"       # Skip slow tests
pytest -m encoding         # Encoding tests only
```

### Advanced Testing

```bash
# Run with coverage
pytest --cov=tools --cov-report=html --cov-report=term

# Run specific test patterns
pytest -k "test_encoding"   # All encoding tests
pytest -k "test_security"   # Security tests

# Debug options
pytest -x                   # Stop on first failure
pytest --pdb               # Drop into debugger on failure
pytest -s                  # Show print statements

# Parallel execution
pytest -n auto             # Use all CPU cores
```

### Test Categories by Tool

#### M1F Tests
- **Basic**: Core file bundling functionality
- **Advanced**: Complex scenarios, edge cases
- **Encoding**: UTF-8, UTF-16, exotic encodings
- **Security**: Path traversal, secret detection
- **Presets**: YAML preset system, file-specific rules
- **Performance**: Large files, parallel processing
- **Cross-platform**: Windows/Linux compatibility

#### S1F Tests
- **Extraction**: All M1F format variations
- **Async**: Asynchronous file operations
- **Encoding**: Preservation and conversion
- **Security**: Malicious path protection

#### HTML2MD Tests
- **Conversion**: HTML to Markdown accuracy
- **Scrapers**: BeautifulSoup, Scrapy, Playwright
- **AI Integration**: Claude-powered optimization
- **Local Processing**: File system operations

#### Research Tests
- **Workflows**: End-to-end research automation
- **LLM Providers**: Provider abstraction testing
- **Content Analysis**: Scoring and analysis
- **Templates**: Analysis template system

## Writing New Tests

### Test Structure Template

```python
from __future__ import annotations

import pytest
from pathlib import Path
from ..base_test import BaseM1FTest  # or BaseS1FTest, etc.

class TestFeatureName(BaseM1FTest):
    """Tests for specific feature area."""
    
    @pytest.mark.unit
    async def test_specific_behavior(self, temp_dir: Path, create_test_file):
        """Test description explaining what and why."""
        # Arrange
        test_file = create_test_file("test.txt", "content")
        
        # Act
        result = await some_function(test_file)
        
        # Assert
        assert result.success
        assert "expected" in result.output
```

### Best Practices

1. **Use Type Hints**: All functions should have complete type annotations
2. **Clear Naming**: Test names should describe the behavior being tested
3. **Docstrings**: Explain what the test validates and why
4. **AAA Pattern**: Arrange-Act-Assert structure
5. **Isolation**: Tests should not depend on each other
6. **Fixtures**: Use fixtures for common setup/teardown
7. **Markers**: Apply appropriate test markers
8. **Cleanup**: Ensure proper resource cleanup

## Test Servers

### HTML2MD Test Server

```bash
# Start the test server
cd tests/html2md_server
python server.py

# Or use management script
python manage_server.py start

# Access test pages
http://localhost:8080/
```

Provides:
- Complex HTML test pages (CSS Grid, Flexbox, nested structures)
- Modern web features (HTML5, semantic markup)
- Real documentation examples
- Edge cases and malformed HTML

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure tools directory is in PYTHONPATH
2. **Fixture Not Found**: Check conftest.py placement
3. **Encoding Failures**: Some tests require specific system encodings
4. **Permission Errors**: Temporary file cleanup issues
5. **Port Conflicts**: Test server requires port 8080
6. **Async Errors**: Ensure anyio is installed

### Platform-Specific Issues

**Windows:**
- File locking during cleanup
- Path separator differences
- Encoding defaults

**Linux/macOS:**
- Symbolic link tests require permissions
- Case-sensitive filesystem assumptions

## Test Data Organization

### M1F Test Data (`m1f/source/`)
- Pattern matching test cases
- International filenames
- Various encodings (UTF-8, UTF-16, Latin-1, etc.)
- Nested directory structures
- Binary and text files

### S1F Test Data
- Pre-generated M1F bundles
- Various separator styles
- Corrupted/malformed inputs

### HTML2MD Test Data
- Complex HTML structures
- Real website snapshots
- Various content types
- Edge cases

## Contributing

When adding new tests:

1. **Follow existing patterns** - Consistency is key
2. **Add to appropriate directory** - Keep tests organized
3. **Update fixtures** - Add reusable components to conftest.py
4. **Document special requirements** - Note any dependencies
5. **Run full test suite** - Ensure no regressions
6. **Update this README** - Document new test categories

## Performance Considerations

- Tests use async I/O where possible
- Large file tests are marked as `@pytest.mark.slow`
- Parallel test execution is supported
- Resource cleanup is automatic

## Security Testing

The test suite includes comprehensive security testing:
- Path traversal attempts
- Secret detection validation
- Input sanitization
- Malformed data handling
