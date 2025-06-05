# Test Suite Documentation

This directory contains the modernized test suite for the m1f tool suite,
including m1f, s1f, html2md, and m1f-scrape tools, using Python 3.10+ features
and modern testing practices.

## Test Structure

```
tests/
├── conftest.py              # Global fixtures and test configuration
├── base_test.py             # Base test classes with common utilities
├── pytest.ini               # Test-specific pytest configuration
├── test_html2md_server.py   # HTML2MD server tests
├── test_simple_server.py    # Simple server tests
├── m1f/                     # m1f-specific tests
│   ├── conftest.py          # m1f-specific fixtures
│   ├── test_m1f_basic.py    # Basic functionality tests
│   ├── test_m1f_advanced.py # Advanced features tests
│   ├── test_m1f_encoding.py # Encoding-related tests
│   ├── test_m1f_edge_cases.py # Edge cases and special scenarios
│   ├── test_m1f_file_hash.py # Filename mtime hash functionality
│   ├── test_m1f_integration.py # Integration and CLI tests
│   ├── test_m1f_presets_basic.py # Basic preset tests
│   ├── test_m1f_presets_integration.py # Advanced preset tests
│   ├── test_m1f_presets_v3_2.py # V3.2 preset features
│   └── source/              # Test data and resources
├── s1f/                     # s1f-specific tests
│   ├── conftest.py          # s1f-specific fixtures
│   ├── test_s1f_basic.py    # Basic functionality tests
│   ├── test_s1f_encoding.py # Encoding-related tests
│   ├── test_s1f_async.py    # Async functionality tests
│   └── ...                  # Other test files and resources
├── html2md/                 # html2md-specific tests
│   ├── __init__.py          # Package marker
│   ├── test_html2md.py      # Core HTML2MD functionality tests
│   ├── test_integration.py  # Integration tests
│   ├── test_local_scraping.py # Local scraping tests
│   ├── test_scrapers.py     # Scraper backend tests
│   ├── source/              # Test HTML files
│   ├── expected/            # Expected output files
│   └── scraped_examples/    # Real-world scraping test cases
└── html2md_server/          # Test server for HTML2MD
    ├── server.py            # Test server implementation
    ├── manage_server.py     # Server management utilities
    └── test_pages/          # Test HTML pages
```

## Key Features

### Modern Python 3.10+ Features

- **Type Hints**: All functions and fixtures use modern type hints with the
  union operator (`|`)
- **Structural Pattern Matching**: Where applicable (Python 3.10+)
- **Better Type Annotations**: Using `from __future__ import annotations`
- **Modern pathlib Usage**: Consistent use of `Path` objects

### Test Organization

- **Modular Test Files**: Tests are split into focused modules by functionality
- **Base Test Classes**: Common functionality is abstracted into base classes
- **Fixture Hierarchy**: Global, tool-specific, and test-specific fixtures
- **Clear Test Markers**: Tests are marked with categories (unit, integration,
  slow, encoding)

### Key Fixtures

#### Global Fixtures (conftest.py)

- `temp_dir`: Creates a temporary directory for test files
- `isolated_filesystem`: Provides an isolated filesystem environment
- `create_test_file`: Factory for creating test files
- `create_test_directory_structure`: Creates complex directory structures
- `capture_logs`: Captures and examines log output
- `cleanup_logging`: Automatically cleans up logging handlers

#### M1F-Specific Fixtures (m1f/conftest.py)

- `run_m1f`: Runs m1f with specified arguments
- `m1f_cli_runner`: Runs m1f as a subprocess
- `create_m1f_test_structure`: Creates m1f-specific test structures

#### S1F-Specific Fixtures (s1f/conftest.py)

- `run_s1f`: Runs s1f with specified arguments
- `s1f_cli_runner`: Runs s1f as a subprocess
- `create_combined_file`: Creates combined files in different formats
- `create_m1f_output`: Uses m1f to create realistic test files

#### HTML2MD-Specific Fixtures (html2md/conftest.py)

- `html2md_runner`: Runs html2md with specified arguments
- `create_test_html`: Creates test HTML files with various structures
- `test_server`: Manages test HTTP server for scraping tests
- `mock_url_fetcher`: Mocks URL fetching for unit tests

#### Scraper Test Utilities

- Test server in `html2md_server/` for realistic scraping scenarios
- Pre-scraped examples for regression testing
- Multiple scraper backend configurations

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run encoding-related tests
pytest -m encoding

# Skip slow tests
pytest -m "not slow"
```

### Run Tests for Specific Tools

```bash
# Run only m1f tests
pytest tests/m1f/

# Run only s1f tests
pytest tests/s1f/

# Run only html2md tests
pytest tests/html2md/

# Run scraper tests
pytest tests/html2md/test_scrapers.py

# Run preset tests
pytest tests/m1f/test_m1f_presets*.py
```

### Run Specific Test Files

```bash
# Run basic m1f tests
pytest tests/m1f/test_m1f_basic.py

# Run encoding tests for both tools
pytest tests/m1f/test_m1f_encoding.py tests/s1f/test_s1f_encoding.py
```

### Run with Coverage

```bash
# Install pytest-cov if not already installed
pip install pytest-cov

# Run with coverage report
pytest --cov=tools --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)

- Fast, isolated tests of individual components
- No external dependencies
- Mock external interactions

### Integration Tests (`@pytest.mark.integration`)

- Test interaction between multiple components
- May create real files and directories
- Test end-to-end workflows

### Slow Tests (`@pytest.mark.slow`)

- Tests that take significant time (e.g., large file handling)
- Skipped in quick test runs

### Encoding Tests (`@pytest.mark.encoding`)

- Tests related to character encoding
- May require specific system encodings

## Writing New Tests

### Test Class Structure

```python
from __future__ import annotations

import pytest
from ..base_test import BaseM1FTest  # or BaseS1FTest

class TestFeatureName(BaseM1FTest):
    """Description of what these tests cover."""

    @pytest.mark.unit
    def test_specific_behavior(self, fixture1, fixture2):
        """Test description."""
        # Arrange
        ...

        # Act
        ...

        # Assert
        ...
```

### Using Fixtures

```python
def test_with_temp_files(self, create_test_file, temp_dir):
    """Example using fixture to create test files."""
    # Create a test file
    test_file = create_test_file("test.txt", "content")

    # Use temp_dir for output
    output_file = temp_dir / "output.txt"
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("value1", "result1"),
    ("value2", "result2"),
])
def test_multiple_cases(self, input, expected):
    """Test with multiple input/output pairs."""
    assert process(input) == expected
```

## Best Practices

1. **Use Type Hints**: All test functions and fixtures should have type hints
2. **Clear Test Names**: Test names should describe what is being tested
3. **Docstrings**: Each test should have a docstring explaining its purpose
4. **Arrange-Act-Assert**: Follow the AAA pattern for test structure
5. **Use Fixtures**: Leverage fixtures for common setup and teardown
6. **Mark Tests**: Use appropriate markers for test categorization
7. **Isolated Tests**: Each test should be independent and not rely on others

## Test Server for HTML2MD

The test suite includes a test server for HTML2MD scraping tests:

```bash
# Start the test server
cd tests/html2md_server
python server.py

# Or use the management script
python manage_server.py start

# Run scraping tests with the server
pytest tests/html2md/test_local_scraping.py
```

The test server provides:
- Static HTML pages for testing various HTML structures
- Realistic website scenarios
- Controlled environment for scraper testing

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the tools directory is in the Python path
2. **Fixture Not Found**: Check that conftest.py files are properly placed
3. **Encoding Errors**: Some encoding tests may fail on systems without specific
   encodings
4. **Permission Errors**: Ensure proper cleanup of temporary files
5. **Test Server Issues**: Ensure port 8080 is available for the test server
6. **Scraper Timeouts**: Some scraper tests may timeout on slow connections

### Debug Options

```bash
# Run with verbose output
pytest -vv

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Drop into debugger on failure
pytest --pdb
```

## Test Coverage

The test suite provides comprehensive coverage for:

### m1f Tool
- File combination with various separators
- Encoding detection and conversion
- Preset system and file-specific processing
- Security scanning
- Archive creation
- Edge cases and error handling

### s1f Tool
- File extraction from combined files
- Format detection (Standard, Detailed, Markdown, etc.)
- Encoding preservation
- Async file processing
- Checksum validation

### html2md Tool
- HTML to Markdown conversion
- URL scraping and fetching
- Multiple scraper backends (BeautifulSoup, Playwright, etc.)
- Content extraction and cleaning
- Metadata preservation

### m1f-scrape Tool
- Website scraping with multiple backends
- Crawling and link following
- Rate limiting and politeness
- Content downloading and organization

## Contributing

When adding new tests:
1. Follow the existing test structure
2. Add appropriate markers (@pytest.mark.unit, etc.)
3. Update this README if adding new test categories
4. Ensure tests are independent and reproducible
5. Add fixtures to appropriate conftest.py files
6. Document any special test requirements
