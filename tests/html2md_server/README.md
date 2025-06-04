# HTML2MD Test Suite

A comprehensive test suite for the html2md converter featuring a local web
server with challenging HTML test pages.

## Overview

This test suite provides:

- A Flask-based web server serving complex HTML test pages
- Modern, responsive HTML pages with various challenging structures
- Comprehensive pytest-based test cases
- Real-world documentation examples (M1F and HTML2MD docs)

## Features

### Test Pages

1. **M1F Documentation** - Complete documentation for the Make One File tool
2. **HTML2MD Documentation** - Full documentation for the HTML to Markdown
   converter
3. **Complex Layout Test** - Tests CSS Grid, Flexbox, nested structures, and
   positioning
4. **Code Examples Test** - Multiple programming languages with syntax
   highlighting
5. **Edge Cases Test** - Malformed HTML, special characters, and unusual
   structures
6. **Modern Features Test** - HTML5 elements, web components, and semantic
   markup
7. **Tables and Lists Test** - Complex tables and deeply nested lists
8. **Multimedia Test** - Images, videos, and other media elements

### Test Coverage

- ✅ CSS selector-based content extraction
- ✅ Complex nested HTML structures
- ✅ Code blocks with language detection
- ✅ Tables and lists conversion
- ✅ Special characters and Unicode
- ✅ YAML frontmatter generation
- ✅ Heading level adjustment
- ✅ Parallel processing
- ✅ Edge cases and error handling

## Setup

### Requirements

```bash
pip install flask flask-cors beautifulsoup4 markdownify pytest pytest-asyncio aiohttp
```

### Running the Test Server

```bash
# Start the test server
python tests/html2md_server/server.py

# Server will run at http://localhost:8080
```

### Running Tests

```bash
# Run all tests
pytest tests/test_html2md_server.py -v

# Run specific test
pytest tests/test_html2md_server.py::TestHTML2MDConversion::test_code_examples -v

# Run with coverage
pytest tests/test_html2md_server.py --cov=tools.mf1-html2md --cov-report=html
```

## Test Structure

```
tests/html2md_server/
├── server.py              # Flask test server
├── static/
│   ├── css/
│   │   └── modern.css    # Modern CSS with dark mode
│   └── js/
│       └── main.js       # Interactive features
├── test_pages/
│   ├── index.html        # Test suite homepage
│   ├── m1f-documentation.html
│   ├── html2md-documentation.html
│   ├── complex-layout.html
│   ├── code-examples.html
│   └── ...               # More test pages
└── README.md             # This file
```

## Usage Examples

### Manual Testing

1. Start the server:

   ```bash
   python tests/html2md_server/server.py
   ```

2. Test conversion with various options:

   ```bash
   # Basic conversion
   python tools/mf1-html2md.py \
     --source-dir http://localhost:8080/page \
     --destination-dir ./output

   # With content selection
   python tools/mf1-html2md.py \
     --source-dir http://localhost:8080/page \
     --destination-dir ./output \
     --outermost-selector "article" \
     --ignore-selectors "nav" ".sidebar" "footer"

   # Specific page with options
   python tools/mf1-html2md.py \
     --source-dir http://localhost:8080/page/code-examples \
     --destination-dir ./output \
     --add-frontmatter \
     --heading-offset 1
   ```

### Automated Testing

The test suite includes comprehensive pytest tests:

```python
# Example test structure
class TestHTML2MDConversion:
    async def test_basic_conversion(self, test_server, temp_output_dir):
        """Test basic HTML to Markdown conversion."""

    async def test_content_selection(self, test_server, temp_output_dir):
        """Test CSS selector-based content extraction."""

    async def test_code_examples(self, test_server, temp_output_dir):
        """Test code block conversion with various languages."""
```

## Adding New Test Pages

1. Create a new HTML file in `test_pages/`
2. Add an entry to `TEST_PAGES` in `server.py`
3. Include challenging HTML structures
4. Add corresponding test cases in `test_html2md_server.py`

Example:

```python
# In server.py
TEST_PAGES = {
    'your-new-test': {
        'title': 'Your New Test',
        'description': 'Description of what this tests'
    }
}
```

## Features Tested

### HTML Elements

- Headings (h1-h6)
- Paragraphs and text formatting
- Lists (ordered, unordered, nested)
- Tables (simple and complex)
- Code blocks and inline code
- Links and images
- Blockquotes
- Details/Summary elements

### CSS Layouts

- Flexbox
- CSS Grid
- Multi-column layouts
- Absolute/relative positioning
- Floating elements
- Sticky elements
- Overflow containers

### Special Cases

- Unicode and emoji
- HTML entities
- Special characters in code
- Very long lines
- Empty elements
- Malformed HTML
- Deeply nested structures

## Contributing

To add new test cases:

1. Identify a challenging HTML pattern
2. Create a test page demonstrating the pattern
3. Add test cases to verify correct conversion
4. Document the test purpose and expected behavior

## License

Part of the M1F project. See main project license.
