# HTML to Markdown Converter Guide

The `html2md` tool (v3.1.0) is a modern, async converter designed to transform
HTML content into clean Markdown format. Built with Python 3.10+ and modern
async architecture, it focuses on intelligent content extraction and conversion.

**Note:** Web scraping functionality has been moved to the separate `webscraper`
tool. Use `webscraper` to download websites, then `html2md` to convert the
downloaded HTML files.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Command Line Usage](#command-line-usage)
- [Configuration](#configuration)
- [Python API](#python-api)
- [Custom Extractors](#custom-extractors)
- [Advanced Features](#advanced-features)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Installation

### Python Dependencies

```bash
pip install beautifulsoup4 markdownify pydantic rich httpx chardet pyyaml aiofiles

# Optional dependencies
pip install toml      # For TOML configuration files
```

### Installation

```bash
pip install beautifulsoup4 markdownify pydantic rich chardet pyyaml aiofiles

# Optional dependencies
pip install toml      # For TOML configuration files
```

## Quick Start

### Convert a Single File

```bash
python -m tools.html2md convert index.html -o index.md
```

### Convert a Directory

```bash
python -m tools.html2md convert ./html_docs/ -o ./markdown_docs/
```

### Analyze HTML Structure

```bash
python -m tools.html2md analyze ./html/*.html --suggest-selectors
```

### Generate Configuration

```bash
python -m tools.html2md config -o config.yaml
```

## Command Line Usage

The tool provides three main commands:

### `convert` - Convert Files or Directories

```bash
python -m tools.html2md convert [source] -o [output] [options]

Options:
  -c, --config FILE         Configuration file (YAML format)
  --format FORMAT          Output format (markdown, m1f_bundle, json)
  --content-selector SEL    CSS selector for main content
  --ignore-selectors SEL    CSS selectors to ignore (space-separated)
  --heading-offset N        Offset heading levels by N
  --no-frontmatter         Don't add YAML frontmatter
  --parallel               Enable parallel processing
  --extractor FILE         Path to custom extractor Python file
  --log-file FILE          Log to file
  -v, --verbose            Enable verbose output
  -q, --quiet              Suppress all output except errors
```

### `analyze` - Analyze HTML Structure

```bash
python -m tools.html2md analyze [files] [options]

Options:
  --show-structure         Show detailed HTML structure
  --common-patterns        Find common patterns across files
  --suggest-selectors      Suggest CSS selectors (default)
  -v, --verbose            Enable verbose output
```

### `config` - Generate Configuration File

```bash
python -m tools.html2md config [options]

Options:
  -o, --output FILE        Output file (default: config.yaml)
  --format FORMAT          Config format (yaml, toml, json)
```

## Configuration

### Configuration File Structure

Create a `config.yaml` file:

```yaml
# Basic settings (v3.1.0 format)
source: ./html_docs
destination: ./markdown_docs
output_format: markdown

# Content extraction
extractor:
  content_selector: "article.content, main, .documentation"
  ignore_selectors:
    - nav
    - header
    - footer
    - .sidebar
    - .ads
    - "#comments"
  remove_elements:
    - script
    - style
    - iframe
  extract_metadata: true
  extract_opengraph: true

# Markdown processing
processor:
  heading_offset: 0
  add_frontmatter: true
  heading_style: atx
  link_handling: convert
  link_extensions:
    .html: .md
    .htm: .md
  normalize_whitespace: true
  fix_encoding: true

# Parallel processing
parallel: true

# Logging
verbose: false
quiet: false
log_file: ./conversion.log
```

### Configuration Options Explained

#### Extractor Configuration

- `content_selector`: CSS selector(s) to find main content
- `ignore_selectors`: Elements to remove before conversion
- `remove_elements`: HTML tags to completely remove
- `preserve_attributes`: HTML attributes to keep
- `extract_metadata`: Extract meta tags and title
- `extract_opengraph`: Extract OpenGraph metadata

#### Processor Configuration

- `heading_offset`: Adjust heading levels (e.g., h1→h2)
- `link_handling`: How to process links (convert/preserve/absolute/relative)
- `normalize_whitespace`: Clean up extra whitespace
- `fix_encoding`: Fix common encoding issues

#### Processing Configuration

- `parallel`: Enable parallel processing for multiple files
- `verbose`: Enable verbose logging
- `quiet`: Suppress all output except errors
- `log_file`: Path to log file

## Python API

### Basic Usage

```python
from tools.html2md.api import HTML2MDConverter
import asyncio

# Create converter with configuration
converter = HTML2MDConverter(
    outermost_selector="main",
    ignore_selectors=["nav", "footer"],
    add_frontmatter=True
)

# Convert a directory (async)
results = asyncio.run(converter.convert_directory("./html", "./markdown"))

# Convert a single file (async)
result = asyncio.run(converter.convert_file("index.html"))

# Convert with custom extractor
from pathlib import Path

converter = HTML2MDConverter(
    outermost_selector="main",
    extractor=Path("./extractors/custom_extractor.py")
)

result = asyncio.run(converter.convert_file("index.html"))
```

### Advanced Configuration

```python
from tools.html2md.config.models import HTML2MDConfig

# Create configuration with v3.1.0 models
config = HTML2MDConfig(
    source_dir="./html",
    destination_dir="./output",
    outermost_selector="div.documentation",
    ignore_selectors=[".nav-menu", ".footer"],
    strip_attributes=True,
    heading_offset=1,
    add_frontmatter=True,
    parallel=True,
    max_workers=4
)

converter = HTML2MDConverter.from_config(config)
```

### Convenience Functions

```python
from tools.html2md.api import convert_file, convert_directory
import asyncio

# Simple file conversion (async)
result = asyncio.run(convert_file("page.html", destination="page.md"))

# Directory conversion with options (async)
results = asyncio.run(convert_directory(
    source="./html",
    destination="./markdown",
    outermost_selector="article",
    parallel=True
))
```

## Custom Extractors

The custom extractor system allows you to create site-specific content extraction logic:

### Function-based Extractor

```python
# extractors/my_extractor.py
from bs4 import BeautifulSoup

def extract(soup: BeautifulSoup, config=None):
    """Extract main content."""
    # Custom extraction logic
    main = soup.find('main')
    if main:
        new_soup = BeautifulSoup('<html><body></body></html>', 'html.parser')
        new_soup.body.append(main)
        return new_soup
    return soup

def postprocess(markdown: str, config=None):
    """Clean up converted markdown."""
    import re
    return re.sub(r'\n{3,}', '\n\n', markdown)
```

### Using Custom Extractors

```bash
python -m tools.html2md convert ./html -o ./markdown \
  --extractor ./extractors/my_extractor.py
```

## Advanced Features

### Content Extraction with CSS Selectors

Target specific content areas:

```yaml
extractor:
  content_selector: |
    article.post-content,
    div.documentation-body,
    main[role="main"],
    #content:not(.sidebar)
```

### Link Handling Strategies

1. **Convert**: Change `.html` to `.md`

   ```yaml
   processor:
     link_handling: convert
     link_extensions:
       .html: .md
       .php: .md
   ```

2. **Preserve**: Keep original links

   ```yaml
   processor:
     link_handling: preserve
   ```

3. **Absolute**: Make all links absolute
   ```yaml
   processor:
     link_handling: absolute
   ```

### Metadata Extraction

The tool can extract and preserve:

- Page title
- Meta description
- OpenGraph data
- Schema.org structured data
- Custom meta tags

### m1f Bundle Creation

Generate m1f bundles directly:

```yaml
output_format: m1f_bundle
m1f:
  create_bundle: true
  bundle_name: my-documentation
  include_assets: true
  generate_index: true
  metadata:
    project: My Project Docs
    version: 1.0.0
```

## Examples

### Example 1: Convert Documentation Site

```bash
# Create configuration
cat > docs-config.yaml << EOF
source: ./python-docs-html
destination: ./python-docs-md
extractor:
  content_selector: "div.document"
  ignore_selectors:
    - ".sphinxsidebar"
    - ".related"
processor:
  heading_offset: 1
  add_frontmatter: true
parallel: true
EOF

# Run conversion
python -m tools.html2md convert ./python-docs-html -o ./python-docs-md -c docs-config.yaml
```

### Example 2: Convert Blog with Specific Content

```python
from tools.html2md.api import HTML2MDConverter
import asyncio

converter = HTML2MDConverter(
    outermost_selector="article.post",
    ignore_selectors=[
        ".post-navigation",
        ".comments-section",
        ".social-share"
    ],
    add_frontmatter=True,
    heading_offset=0
)

# Convert all blog posts (async)
results = asyncio.run(converter.convert_directory(
    "./blog-html",
    "./blog-markdown"
))
```

### Example 3: Create m1f Bundle from HTML

```bash
# First download the website using webscraper
python -m tools.scrape_tool https://docs.example.com -o ./html

# Then convert to m1f bundle
python -m tools.html2md convert ./html \
  -o ./output.m1f \
  --format m1f_bundle \
  --content-selector "main.content" \
  --ignore-selectors nav footer
```

## Troubleshooting

### Common Issues

1. **Content selector not matching**

   ```
   WARNING: Content selector 'article' not found
   ```

   Solution: Use the analyze command to find the right selectors:
   ```bash
   python -m tools.html2md analyze ./html/*.html --suggest-selectors
   ```

2. **Encoding issues**

   ```
   UnicodeDecodeError: 'utf-8' codec can't decode
   ```

   Solution: The tool auto-detects encoding, but HTML files may have mixed encodings. 
   All output is converted to UTF-8.

3. **Large directories timing out**

   Solution: Use parallel processing:
   ```bash
   python -m tools.html2md convert ./html -o ./md --parallel
   ```

4. **Missing content after conversion**

   Solution: Check your ignore selectors - they may be too broad:
   ```bash
   python -m tools.html2md convert ./html -o ./md \
     --content-selector "body" \
     --ignore-selectors .ads .cookie-notice
   ```

### Debug Mode

Enable verbose logging for debugging:

```bash
python -m tools.html2md convert ./html -o ./md -v --log-file debug.log
```

Or in configuration:

```yaml
verbose: true
log_file: ./conversion-debug.log
```

### Performance Tips

1. **Use parallel processing** for large directories:

   ```yaml
   parallel: true
   ```

2. **Target specific content** to reduce processing:
   ```yaml
   extractor:
     content_selector: "article.documentation"
   ```

3. **Use custom extractors** for complex sites to optimize extraction

## Integration with m1f

The converted Markdown files are optimized for m1f bundling:

1. Clean, consistent formatting
2. Preserved metadata in frontmatter
3. Proper link structure
4. UTF-8 encoding

To create an m1f bundle after conversion:

```bash
# Download website first
python -m tools.scrape_tool https://docs.example.com -o ./html/

# Convert to Markdown
python -m tools.html2md convert ./html/ -o ./docs/

# Create m1f bundle
python -m tools.m1f -s ./docs/ -o documentation.m1f.txt
```

Or convert directly to m1f bundle format:

```bash
python -m tools.html2md convert ./html/ \
  -o ./docs.m1f \
  --format m1f_bundle
```
