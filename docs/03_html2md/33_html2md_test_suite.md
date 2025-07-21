# HTML2MD Test Suite Documentation

A comprehensive test suite for validating the html2md converter (v2.0.0) with
challenging real-world HTML structures.

## Overview

The HTML2MD test suite provides a robust testing framework consisting of:

- A Flask-based web server serving complex HTML test pages
- Comprehensive pytest test cases covering all conversion features including
  async operations
- Real-world documentation examples with challenging HTML structures
- Automated test runner with coverage reporting
- Full support for testing async/await patterns and parallel processing

## Architecture

```
tests/
├── html2md_server/
│   ├── server.py              # Flask test server
│   ├── requirements.txt       # Test suite dependencies
│   ├── run_tests.sh          # Automated test runner
│   ├── README.md             # Test suite documentation
│   ├── static/
│   │   ├── css/
│   │   │   └── modern.css    # Modern CSS with dark mode
│   │   └── js/
│   │       └── main.js       # Interactive features
│   └── test_pages/
│       ├── index.html        # Test suite homepage
│       ├── m1f-documentation.html
│       ├── html2md-documentation.html
│       ├── complex-layout.html
│       ├── code-examples.html
│       └── ...               # Additional test pages
└── test_html2md_server.py    # Pytest test cases
```

## Test Server

### Features

- Modern Flask-based web server
- RESTful API endpoints for test page discovery
- CORS enabled for cross-origin testing
- Dynamic page generation support
- Static asset serving with proper MIME types

### Running the Server

```bash
# Start server on default port 8080
python tests/html2md_server/server.py

# Server provides:
# - http://localhost:8080/            # Test suite homepage
# - http://localhost:8080/page/{name} # Individual test pages
# - http://localhost:8080/api/test-pages # JSON API
```

## Test Pages

### 1. M1F Documentation (`m1f-documentation.html`)

Tests real documentation conversion with:

- Complex heading hierarchies
- Code examples in multiple languages
- Nested structures and feature grids
- Command-line documentation tables
- Advanced layout with inline styles

### 2. HTML2MD Documentation (`html2md-documentation.html`)

Comprehensive documentation page testing:

- Multi-level navigation structures
- API documentation with code examples
- Complex tables and option grids
- Details/Summary elements
- Sidebar navigation

### 3. Complex Layout Test (`complex-layout.html`)

CSS layout challenges:

- **Flexbox layouts**: Multi-item flex containers
- **CSS Grid**: Complex grid with spanning items
- **Nested structures**: Up to 4 levels deep
- **Positioning**: Absolute, relative, sticky elements
- **Multi-column layouts**: CSS columns with rules
- **Masonry layouts**: Pinterest-style card layouts
- **Overflow containers**: Scrollable areas

### 4. Code Examples Test (`code-examples.html`)

Programming language support:

- **Languages tested**: Python, TypeScript, JavaScript, Bash, SQL, Go, Rust
- **Inline code**: Mixed with regular text
- **Code with special characters**: HTML entities, Unicode
- **Configuration files**: YAML, JSON examples
- **Edge cases**: Empty blocks, long lines, whitespace-only

### 5. Additional Test Pages (Planned)

- **Edge Cases**: Malformed HTML, special characters
- **Modern Features**: HTML5 elements, web components
- **Tables and Lists**: Complex nested structures
- **Multimedia**: Images, videos, iframes

## Test Suite Features

### Content Selection Testing

```python
# Test CSS selector-based extraction (v2.0.0 async API)
from tools.html2md.api import HTML2MDConverter
import asyncio

converter = HTML2MDConverter(
    outermost_selector="article",
    ignore_selectors=["nav", ".sidebar", "footer"]
)

# Async conversion
result = asyncio.run(converter.convert_file("test.html"))
```

### Code Block Detection

- Automatic language detection from class names
- Preservation of syntax highlighting hints
- Special character handling in code

### Layout Preservation

- Nested structure maintenance
- List hierarchy preservation
- Table structure conversion
- Heading level consistency

### Edge Case Handling

- Empty HTML documents
- Malformed HTML structures
- Very long lines
- Unicode and special characters
- Missing closing tags

## Running Tests

### Quick Start

```bash
# Run all tests with the automated script
./tests/html2md_server/run_tests.sh

# This will:
# 1. Install dependencies
# 2. Start the test server
# 3. Run all pytest tests
# 4. Generate coverage report
# 5. Clean up processes
```

### Manual Testing

```bash
# Install dependencies
pip install -r tests/html2md_server/requirements.txt

# Start server in one terminal
python tests/html2md_server/server.py

# Run tests in another terminal
pytest tests/test_html2md_server.py -v

# Run with coverage
pytest tests/test_html2md_server.py --cov=tools.html2md_tool --cov-report=html
```

### Test Options

```bash
# Run specific test
pytest tests/test_html2md_server.py::TestHTML2MDConversion::test_code_examples -v

# Run with detailed output
pytest tests/test_html2md_server.py -vv -s

# Run only fast tests
pytest tests/test_html2md_server.py -m "not slow"
```

## Test Coverage

### Core Features Tested

- ✅ Basic HTML to Markdown conversion
- ✅ Async I/O operations with aiofiles
- ✅ CSS selector content extraction
- ✅ Element filtering with ignore selectors
- ✅ Complex nested HTML structures
- ✅ Code block language detection
- ✅ Table conversion (simple and complex)
- ✅ List conversion (ordered, unordered, nested)
- ✅ Special characters and HTML entities
- ✅ Unicode support
- ✅ YAML frontmatter generation
- ✅ Heading level offset adjustment
- ✅ Parallel processing with asyncio
- ✅ Configuration file loading (YAML/TOML)
- ✅ CLI argument parsing
- ✅ API mode for programmatic access
- ✅ HTTrack integration (when available)
- ✅ URL conversion from lists

### Performance Testing

- Parallel conversion of multiple files
- Large file handling
- Memory usage monitoring
- Conversion speed benchmarks

## Writing New Tests

### Adding Test Pages

1. Create HTML file in `tests/html2md_server/test_pages/`
2. Register in `server.py`:
   ```python
   TEST_PAGES = {
       'your-test': {
           'title': 'Your Test Title',
           'description': 'What this tests'
       }
   }
   ```
3. Add corresponding test case

### Test Case Structure

```python
class TestYourFeature:
    async def test_your_feature(self, test_server, temp_output_dir):
        """Test description."""
        from tools.html2md.api import HTML2MDConverter

        converter = HTML2MDConverter(
            outermost_selector="main",
            ignore_selectors=["nav", "footer"],
            add_frontmatter=True
        )

        # Perform async conversion
        results = await converter.convert_directory(
            f"{test_server.base_url}/page",
            temp_output_dir
        )

        # Assert expected results
        assert len(results) > 0
```

## Continuous Integration

### GitHub Actions Integration

```yaml
# .github/workflows/test.yml
- name: Run HTML2MD Tests
  run: |
    cd tests/html2md_server
    ./run_tests.sh
```

### Local Development

```bash
# Watch mode for development
pytest-watch tests/test_html2md_server.py

# Run with debugging
pytest tests/test_html2md_server.py --pdb
```

## Troubleshooting

### Common Issues

**Server won't start**

- Check if port 8080 is already in use
- Ensure Flask dependencies are installed
- Check Python version (3.9+ required)

**Tests fail with connection errors**

- Ensure server is running
- Check firewall settings
- Verify localhost resolution

**Coverage report issues**

- Install pytest-cov: `pip install pytest-cov`
- Ensure tools.html2md module is in Python path
- For async tests, use pytest-asyncio: `pip install pytest-asyncio`

## Future Enhancements

1. **Additional Test Pages**
   - SVG content handling
   - MathML equations
   - Microdata and structured data
   - Progressive web app features
   - WebAssembly integration tests
   - Shadow DOM content extraction

2. **Test Automation**
   - Visual regression testing
   - Performance benchmarking
   - Memory leak detection
   - Cross-platform testing

3. **Enhanced Reporting**
   - HTML test reports with screenshots
   - Conversion diff visualization
   - Performance metrics dashboard

## Contributing

To contribute to the test suite:

1. Identify untested scenarios
2. Create representative HTML test pages
3. Write comprehensive test cases
4. Document the test purpose
5. Submit PR with test results

The test suite aims to cover all real-world HTML conversion scenarios to ensure
robust and reliable Markdown output.
