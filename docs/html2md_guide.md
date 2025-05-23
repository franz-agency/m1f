# HTML to Markdown Converter Guide

The `html2md` tool is a modern, modular converter designed to transform HTML content into clean Markdown format. It's particularly powerful for converting entire websites and integrates seamlessly with m1f for creating documentation bundles.

## Table of Contents
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Command Line Usage](#command-line-usage)
- [Configuration](#configuration)
- [Python API](#python-api)
- [HTTrack Integration](#httrack-integration)
- [Advanced Features](#advanced-features)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Installation

### Python Dependencies
```bash
pip install beautifulsoup4 markdownify pydantic rich requests chardet pyyaml

# Optional dependencies
pip install toml      # For TOML configuration files
pip install aiohttp   # For async web operations
```

### HTTrack Installation
HTTrack is required for website mirroring functionality:

```bash
# Ubuntu/Debian
sudo apt-get install httrack

# macOS
brew install httrack

# Windows
# Download installer from https://www.httrack.com/
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

### Convert a Website
```bash
python -m tools.html2md crawl https://docs.example.com -o ./docs/
```

## Command Line Usage

The tool provides three main commands:

### `convert` - Convert Files or Directories
```bash
python -m tools.html2md convert [source] -o [output] [options]

Options:
  -c, --config FILE         Configuration file (YAML/TOML)
  --content-selector SEL    CSS selector for main content
  --ignore-selectors SEL    CSS selectors to ignore (multiple allowed)
  --heading-offset N        Offset heading levels by N
  --no-frontmatter         Don't add YAML frontmatter
  --format FORMAT          Output format (markdown, m1f_bundle)
```

### `crawl` - Convert Entire Websites
```bash
python -m tools.html2md crawl [URL] -o [output] [options]

Options:
  --max-depth N            Maximum crawl depth
  --max-pages N            Maximum pages to crawl
```

### `config` - Generate Configuration File
```bash
python -m tools.html2md config -o config.yaml [options]

Options:
  --format FORMAT          Config format (yaml, toml, json)
```

## Configuration

### Configuration File Structure

Create a `config.yaml` file:

```yaml
# Basic settings
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
  heading_style: atx
  link_handling: convert
  link_extensions:
    .html: .md
    .htm: .md
  normalize_whitespace: true
  fix_encoding: true

# Web crawling (HTTrack)
crawler:
  max_depth: 10
  max_pages: 5000
  allowed_domains:
    - docs.example.com
    - api.example.com
  exclude_patterns:
    - "*.pdf"
    - "*.zip"
    - "*/download/*"
  respect_robots_txt: true
  concurrent_requests: 5
  request_delay: 0.5

# Parallel processing
parallel: true
max_workers: 4

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

#### Crawler Configuration
- `max_depth`: How deep to crawl from start page
- `max_pages`: Maximum number of pages to download
- `allowed_domains`: Restrict crawling to specific domains
- `exclude_patterns`: URL patterns to skip
- `respect_robots_txt`: Honor robots.txt rules

## Python API

### Basic Usage

```python
from tools.html2md import Html2mdConverter

# Create converter with configuration
converter = Html2mdConverter({
    "source": "./html",
    "destination": "./markdown"
})

# Convert a directory
results = converter.convert_directory()

# Convert a single file
output = converter.convert_file(Path("index.html"))

# Convert a URL
output = converter.convert_url("https://example.com/page.html")

# Convert entire website
results = converter.convert_website("https://docs.example.com")
```

### Advanced Configuration

```python
config = {
    "destination": "./output",
    "extractor": {
        "content_selector": "div.documentation",
        "ignore_selectors": [".nav-menu", ".footer"],
        "strip_attributes": True,
        "preserve_attributes": ["id", "href"]
    },
    "processor": {
        "heading_offset": 1,
        "link_handling": "convert",
        "code_block_style": "fenced",
        "detect_language": True
    },
    "crawler": {
        "max_depth": 5,
        "max_pages": 1000,
        "allowed_domains": ["docs.example.com"]
    }
}

converter = Html2mdConverter(config)
```

### Convenience Functions

```python
from tools.html2md import convert_file, convert_directory, convert_url

# Simple file conversion
output = convert_file("page.html", destination="./output")

# Directory conversion
outputs = convert_directory("./html", "./markdown", 
    extractor={"content_selector": "article"})

# URL conversion
output = convert_url("https://example.com", "./output")
```

## HTTrack Integration

The tool uses HTTrack for reliable website mirroring. HTTrack provides:

- **Professional mirroring**: Complete website downloads
- **Link preservation**: Maintains site structure
- **Bandwidth control**: Configurable delays and connections
- **Standards compliance**: Respects robots.txt
- **Resume support**: Can continue interrupted downloads

### HTTrack Options Mapping

| Config Option | HTTrack Flag | Description |
|--------------|--------------|-------------|
| max_depth | -r | Maximum mirror depth |
| max_pages | -m | Maximum file size (kb) |
| concurrent_requests | -c | Number of connections |
| request_delay | -E | Delay between requests (ms) |
| respect_robots_txt | -s0/-s2 | robots.txt handling |

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
destination: ./python-docs-md
extractor:
  content_selector: "div.document"
  ignore_selectors: 
    - ".sphinxsidebar"
    - ".related"
processor:
  heading_offset: 1
crawler:
  max_depth: 10
  allowed_domains:
    - docs.python.org
EOF

# Run conversion
python -m tools.html2md crawl https://docs.python.org/3/ -c docs-config.yaml
```

### Example 2: Convert Blog with Specific Content

```python
from tools.html2md import Html2mdConverter

converter = Html2mdConverter({
    "destination": "./blog-markdown",
    "extractor": {
        "content_selector": "article.post",
        "ignore_selectors": [
            ".post-navigation",
            ".comments-section",
            ".social-share"
        ],
        "extract_metadata": True
    },
    "processor": {
        "link_handling": "convert",
        "heading_offset": 0
    }
})

# Convert all blog posts
results = converter.convert_directory(Path("./blog-html"))
```

### Example 3: Create m1f Bundle from Website

```bash
python -m tools.html2md crawl https://docs.example.com \
  -o ./output \
  --format m1f_bundle \
  --content-selector "main.content" \
  --ignore-selectors "nav" "footer"
```

## Troubleshooting

### Common Issues

1. **HTTrack not found**
   ```
   RuntimeError: HTTrack is not installed
   ```
   Solution: Install HTTrack using your package manager

2. **Content selector not matching**
   ```
   WARNING: Content selector 'article' not found
   ```
   Solution: Inspect the HTML and adjust your selector

3. **Encoding issues**
   ```
   UnicodeDecodeError: 'utf-8' codec can't decode
   ```
   Solution: The tool auto-detects encoding, but you can force it:
   ```yaml
   source_encoding: iso-8859-1
   target_encoding: utf-8
   ```

4. **Large websites timing out**
   Solution: Adjust crawler settings:
   ```yaml
   crawler:
     timeout: 60.0
     max_pages: 1000
     concurrent_requests: 2
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
   max_workers: 8
   ```

2. **Limit crawl scope** for large websites:
   ```yaml
   crawler:
     max_depth: 3
     max_pages: 500
     allowed_domains: [docs.example.com]
   ```

3. **Target specific content** to reduce processing:
   ```yaml
   extractor:
     content_selector: "article.documentation"
   ```

## Integration with m1f

The converted Markdown files are optimized for m1f bundling:

1. Clean, consistent formatting
2. Preserved metadata in frontmatter
3. Proper link structure
4. UTF-8 encoding

To create an m1f bundle after conversion:

```bash
# Convert website
python -m tools.html2md crawl https://docs.example.com -o ./docs/

# Create m1f bundle
python -m m1f ./docs/ -o documentation.m1f.md
```

Or do it in one step:

```bash
python -m tools.html2md crawl https://docs.example.com \
  -o ./docs/ \
  --format m1f_bundle
``` 