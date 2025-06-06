# HTML2MD Workflow Guide

This guide explains the recommended workflow for converting websites to Markdown
using html2md with custom extractors.

## Overview

The html2md tool now supports a flexible workflow that separates concerns:

1. HTML acquisition (scraping or external)
2. Content analysis and extractor development
3. Conversion with site-specific extraction

## Directory Structure

All scraping projects use the `.scrapes` directory (gitignored):

```
.scrapes/
└── project-name/
    ├── html/         # Raw HTML files
    ├── md/           # Converted Markdown files
    └── extractors/   # Custom extraction scripts
```

## Complete Workflow

### Step 1: Set Up Project Structure

```bash
# Create project directories
mkdir -p .scrapes/my-docs/{html,md,extractors}
```

### Step 2: Acquire HTML Content

You have several options:

#### Option A: Use webscraper tool

```bash
python -m tools.m1f-scrape https://example.com \
  -o .scrapes/my-docs/html \
  --max-pages 50 \
  --scraper playwright
```

#### Option B: Manual download

- Save HTML files directly to `.scrapes/my-docs/html/`
- Use browser "Save As" or wget/curl
- Any method that gets HTML files

#### Option C: External scraping

- Use any scraping tool you prefer
- Just ensure HTML files end up in the html/ directory

### Step 3: Analyze HTML Structure (Optional)

Understand the HTML structure before creating extractors:

```bash
# Analyze a few sample files
python -m tools.html2md_tool analyze \
  .scrapes/my-docs/html/*.html \
  --suggest-selectors

# Get detailed structure analysis
python -m tools.html2md_tool analyze \
  .scrapes/my-docs/html/*.html \
  --show-structure \
  --common-patterns
```

### Step 4: Create Custom Extractor (Optional)

#### Manual Creation

Create `.scrapes/my-docs/extractors/custom_extractor.py`:

```python
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any

def extract(soup: BeautifulSoup, config: Optional[Dict[str, Any]] = None) -> BeautifulSoup:
    """Extract main content from HTML."""
    # Remove site-specific navigation
    for selector in ['nav', '.sidebar', '#header', '#footer']:
        for elem in soup.select(selector):
            elem.decompose()

    # Find main content area
    main = soup.find('main') or soup.find('article') or soup.find('.content')
    if main:
        # Create clean soup with just main content
        new_soup = BeautifulSoup('<html><body></body></html>', 'html.parser')
        new_soup.body.append(main)
        return new_soup

    return soup

def postprocess(markdown: str, config: Optional[Dict[str, Any]] = None) -> str:
    """Clean up converted markdown."""
    lines = markdown.split('\n')
    cleaned = []

    for line in lines:
        # Remove "Copy" buttons before code blocks
        if line.strip() == 'Copy':
            continue
        cleaned.append(line)

    return '\n'.join(cleaned)
```

#### Claude-Assisted Creation

Use Claude to analyze HTML and create a custom extractor:

```bash
# Have Claude analyze the HTML structure
claude -p "Analyze these HTML files and create a custom extractor for html2md. \
The extractor should:
1. Remove all navigation, headers, footers, and sidebars
2. Extract only the main content
3. Clean up any site-specific artifacts in the markdown
4. Handle the specific structure of this website

Write the extractor to .scrapes/my-docs/extractors/custom_extractor.py" \
--files .scrapes/my-docs/html/*.html
```

### Step 5: Convert HTML to Markdown

#### With Custom Extractor

```bash
cd .scrapes/my-docs
python ../../tools/html2md_tool.py convert html -o md \
  --extractor extractors/custom_extractor.py
```

#### With Default Extractor

```bash
cd .scrapes/my-docs
python ../../tools/html2md_tool.py convert html -o md
```

#### With CSS Selectors Only

```bash
cd .scrapes/my-docs
python ../../tools/html2md_tool.py convert html -o md \
  --content-selector "main.content" \
  --ignore-selectors "nav" ".sidebar" ".ads"
```

### Step 6: Review and Refine

1. Check the converted Markdown files
2. If quality needs improvement:
   - Update the custom extractor
   - Re-run the conversion
   - Iterate until satisfied

## Example: Documentation Site

Here's a complete example for converting a documentation site:

```bash
# 1. Setup
mkdir -p .scrapes/docs-site/{html,md,extractors}

# 2. Download documentation
python -m tools.m1f-scrape https://docs.example.com \
  -o .scrapes/docs-site/html \
  --max-pages 100 \
  --scraper playwright

# 3. Analyze structure
python -m tools.html2md_tool analyze \
  .scrapes/docs-site/html/*.html \
  --suggest-selectors

# 4. Create extractor for docs site
cat > .scrapes/docs-site/extractors/docs_extractor.py << 'EOF'
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any

def extract(soup: BeautifulSoup, config: Optional[Dict[str, Any]] = None) -> BeautifulSoup:
    # Remove docs-specific elements
    for selector in [
        '.docs-nav', '.docs-sidebar', '.docs-header',
        '.docs-footer', '.edit-page', '.feedback',
        '[class*="navigation"]', '[id*="toc"]'
    ]:
        for elem in soup.select(selector):
            elem.decompose()

    # Extract article content
    article = soup.find('article') or soup.find('.docs-content')
    if article:
        new_soup = BeautifulSoup('<html><body></body></html>', 'html.parser')
        new_soup.body.append(article)
        return new_soup

    return soup

def postprocess(markdown: str, config: Optional[Dict[str, Any]] = None) -> str:
    # Clean up docs-specific patterns
    import re

    # Remove "Copy" buttons
    markdown = re.sub(r'^Copy\s*\n', '', markdown, flags=re.MULTILINE)

    # Remove "On this page" sections
    markdown = re.sub(r'^On this page.*?(?=^#|\Z)', '', markdown,
                      flags=re.MULTILINE | re.DOTALL)

    return markdown.strip()
EOF

# 5. Convert with custom extractor
cd .scrapes/docs-site
python ../../tools/html2md_tool.py convert html -o md \
  --extractor extractors/docs_extractor.py

# 6. Create m1f bundle (optional)
python ../../tools/m1f.py -s md -o docs-bundle.txt
```

## Best Practices

### 1. Start Small

- Test with a few HTML files first
- Refine the extractor before processing everything

### 2. Iterative Development

- Create basic extractor
- Convert a sample
- Identify issues
- Update extractor
- Repeat until satisfied

### 3. Extractor Tips

- Use specific CSS selectors for the site
- Remove navigation early in extraction
- Handle site-specific patterns in postprocess
- Test with different page types

### 4. Organization

- Keep each project in its own directory
- Document site-specific quirks
- Save working extractors for reuse

### 5. Performance

- Use `--parallel` for large conversions
- Process in batches if needed
- Monitor memory usage

## Troubleshooting

### Common Issues

**Issue**: Navigation elements still appear in Markdown

- **Solution**: Add more specific selectors to the extractor
- Check for dynamic class names or IDs

**Issue**: Missing content

- **Solution**: Verify content selector is correct
- Check if content is loaded dynamically (use playwright scraper)

**Issue**: Broken formatting

- **Solution**: Adjust extraction logic
- Use postprocess to fix patterns

**Issue**: Encoding errors

- **Solution**: Ensure HTML files are UTF-8
- Use `--target-encoding utf-8` if needed

### Debug Tips

1. **Test extractor standalone**:

```python
from bs4 import BeautifulSoup
from pathlib import Path

# Load your extractor
import sys
sys.path.append('.scrapes/my-docs/extractors')
import custom_extractor

# Test on single file
html = Path('.scrapes/my-docs/html/sample.html').read_text()
soup = BeautifulSoup(html, 'html.parser')
result = custom_extractor.extract(soup)
print(result.prettify())
```

2. **Use verbose mode**:

```bash
python -m tools.html2md_tool convert html -o md \
  --extractor extractors/custom_extractor.py \
  --verbose
```

3. **Process single file**:

```bash
python -m tools.html2md_tool convert html/single-file.html \
  -o test.md \
  --extractor extractors/custom_extractor.py
```

## Advanced Techniques

### Multi-Stage Extraction

For complex sites, use multiple extraction stages:

```python
def extract(soup: BeautifulSoup, config: Optional[Dict[str, Any]] = None) -> BeautifulSoup:
    # Stage 1: Remove obvious non-content
    remove_selectors = ['script', 'style', 'nav', 'header', 'footer']
    for selector in remove_selectors:
        for elem in soup.select(selector):
            elem.decompose()

    # Stage 2: Find content container
    container = soup.select_one('.main-container') or soup.body

    # Stage 3: Clean within container
    for elem in container.select('.ads, .social-share, .related'):
        elem.decompose()

    # Stage 4: Extract final content
    content = container.select_one('article') or container

    new_soup = BeautifulSoup('<html><body></body></html>', 'html.parser')
    new_soup.body.append(content)
    return new_soup
```

### Conditional Extraction

Handle different page types:

```python
def extract(soup: BeautifulSoup, config: Optional[Dict[str, Any]] = None) -> BeautifulSoup:
    # Detect page type
    if soup.find('article', class_='blog-post'):
        return extract_blog_post(soup)
    elif soup.find('div', class_='documentation'):
        return extract_documentation(soup)
    elif soup.find('div', class_='api-reference'):
        return extract_api_reference(soup)
    else:
        return extract_generic(soup)
```

### Metadata Preservation

Keep important metadata:

```python
def extract(soup: BeautifulSoup, config: Optional[Dict[str, Any]] = None) -> BeautifulSoup:
    # Preserve title
    title = soup.find('title')

    # Extract content
    content = soup.find('main')

    # Create new soup with metadata
    new_soup = BeautifulSoup('<html><head></head><body></body></html>', 'html.parser')
    if title:
        new_soup.head.append(title)
    if content:
        new_soup.body.append(content)

    return new_soup
```

## Conclusion

The html2md workflow provides maximum flexibility:

- Separate HTML acquisition from conversion
- Site-specific extractors for optimal results
- Iterative refinement process
- Integration with other tools (webscraper, m1f)

This approach ensures you can handle any website structure and produce clean,
readable Markdown output.
