# html2md (HTML to Markdown Converter)

A modern HTML to Markdown converter with HTML structure analysis, async I/O, and
parallel processing capabilities.

## Overview

The html2md tool (v3.0.0) provides a robust solution for converting HTML content
to Markdown format, with fine-grained control over the conversion process. Built
with Python 3.10+ and modern async architecture, it focuses on intelligent
content extraction and conversion.

**Note:** Web scraping functionality has been moved to the separate `webscraper`
tool for better modularity. Use `webscraper` to download websites, then
`html2md` to convert the downloaded HTML files.

## Key Features

- **HTML Structure Analysis**: Analyze HTML files to find optimal content
  selectors
- **Intelligent Content Extraction**: Use CSS selectors to extract specific
  content
- **Async I/O**: High-performance concurrent file processing
- **API Mode**: Programmatic access for integration with other tools
- **Type Safety**: Full type annotations throughout the codebase
- **Modern Architecture**: Clean modular design
- Recursive directory scanning for batch conversion
- Smart internal link handling (HTML → Markdown)
- Customizable element filtering and removal
- YAML frontmatter generation
- Heading level adjustment
- Code block language detection
- Character encoding detection and conversion
- Parallel processing for faster conversion

## Quick Start

```bash
# Basic conversion of all HTML files in a directory
python -m tools.html2md convert ./website -o ./docs

# Extract only main content from HTML files
python -m tools.html2md convert ./website -o ./docs \
  --content-selector "main.content" --ignore-selectors "nav" ".sidebar" "footer"

# Add YAML frontmatter and adjust heading levels
python -m tools.html2md convert ./website -o ./docs \
  --no-frontmatter --heading-offset 1

# Analyze HTML structure to find best selectors
python -m tools.html2md analyze ./html/*.html --suggest-selectors

# Analyze with detailed structure output
python -m tools.html2md analyze ./html/*.html --show-structure --common-patterns
```

### Complete Workflow Example

```bash
# Step 1: Download website using webscraper
python -m tools.webscraper https://example.com -o ./html_files

# Step 2: Analyze HTML structure
python -m tools.html2md analyze ./html_files/*.html --suggest-selectors

# Step 3: Convert with optimal selectors
python -m tools.html2md convert ./html_files -o ./markdown \
  --content-selector "article" \
  --ignore-selectors "nav" ".sidebar" ".ads"
```

## Command Line Interface

The html2md tool uses subcommands for different operations:

### Convert Command

Convert local HTML files to Markdown:

```bash
python -m tools.html2md convert <source> -o <output> [options]
```

| Option               | Description                               |
| -------------------- | ----------------------------------------- |
| `source`             | Source file or directory                  |
| `-o, --output`       | Output file or directory (required)       |
| `-c, --config`       | Configuration file path                   |
| `--content-selector` | CSS selector for main content             |
| `--ignore-selectors` | CSS selectors to ignore (space-separated) |
| `--heading-offset`   | Offset heading levels                     |
| `--no-frontmatter`   | Don't add YAML frontmatter                |
| `--parallel`         | Enable parallel processing                |
| `-v, --verbose`      | Enable verbose output                     |
| `-q, --quiet`        | Suppress all output except errors         |

### Analyze Command

Analyze HTML structure for optimal content extraction:

```bash
python -m tools.html2md analyze <files> [options]
```

| Option                | Description                                                          |
| --------------------- | -------------------------------------------------------------------- |
| `files`               | HTML files to analyze (2-3 files recommended)                        |
| `--show-structure`    | Show detailed HTML structure                                         |
| `--common-patterns`   | Find common patterns across files                                    |
| `--suggest-selectors` | Suggest CSS selectors for content extraction (default if no options) |

## Usage Examples

### Basic Conversion

```bash
# Simple conversion of all HTML files in a directory
python -m tools.html2md convert ./website -o ./docs

# Convert files with verbose logging
python -m tools.html2md convert ./website -o ./docs --verbose
```

### Content Selection

```bash
# Extract only the main content and ignore navigation elements
python -m tools.html2md convert ./website -o ./docs \
  --content-selector "main" --ignore-selectors "nav" ".sidebar" "footer"

# Extract article content from specific selectors
python -m tools.html2md convert ./website -o ./docs \
  --content-selector "article.content" \
  --ignore-selectors ".author-bio" ".share-buttons" ".related-articles"
```

### HTML Analysis

```bash
# Analyze HTML files to find optimal selectors
python -m tools.html2md analyze ./html/*.html

# Show detailed structure of HTML files
python -m tools.html2md analyze ./html/*.html --show-structure

# Find common patterns across multiple files
python -m tools.html2md analyze ./html/*.html --common-patterns

# Get all analysis options
python -m tools.html2md analyze ./html/*.html \
  --show-structure --common-patterns --suggest-selectors
```

### File Filtering

```bash
# Process only specific file types
python -m tools.html2md convert ./website -o ./docs \
  -c config.yaml  # Use a configuration file for file filtering
```

### Formatting Options

```bash
# Adjust heading levels (e.g., h1 → h2, h2 → h3)
python -m tools.html2md convert ./website -o ./docs \
  --heading-offset 1

# Skip frontmatter generation
python -m tools.html2md convert ./website -o ./docs \
  --no-frontmatter

# Use configuration file for advanced formatting options
python -m tools.html2md convert ./website -o ./docs -c config.yaml
```

### Performance Optimization

```bash
# Use parallel processing for faster conversion of large sites
python -m tools.html2md convert ./website -o ./docs \
  --parallel
```

## Advanced Features

### YAML Frontmatter

When using the `--add-frontmatter` option, the converter will automatically
generate YAML frontmatter for each Markdown file, including:

- Title extracted from HTML title tag or first h1 element
- Source filename
- Conversion date
- Original file modification date

Custom frontmatter fields can be added using the `--frontmatter-fields` option:

```bash
python -m tools.html2md --source-dir ./website --destination-dir ./docs \
  --add-frontmatter --frontmatter-fields "layout=post" "author=John Doe" "category=tutorial"
```

This will add the following YAML frontmatter to each converted file:

```yaml
---
title: Extracted from HTML
source_file: original.html
date_converted: 2023-06-15T14:30:21
date_modified: 2023-06-12T10:15:33
layout: post
author: John Doe
category: tutorial
---
```

### Heading Level Adjustment

The `--heading-offset` option allows you to adjust the hierarchical structure of
the document by incrementing or decrementing heading levels. This is useful
when:

- Integrating content into an existing document with its own heading hierarchy
- Making h1 headings become h2 headings for better document structure
- Ensuring proper nesting of headings for better semantics

Positive values increase heading levels (e.g., h1 → h2), while negative values
decrease them (e.g., h2 → h1).

### Code Block Language Detection

The converter can automatically detect language hints from HTML code blocks that
use language classes, such as:

```html
<pre><code class="language-python">def example():
    return "Hello, world!"
</code></pre>
```

This will be converted to a properly formatted Markdown code block with language
hint:

````markdown
```python
def example():
    return "Hello, world!"
```
````

### Character Encoding Handling

The converter provides robust character encoding detection and conversion:

1. Automatically detects the encoding of source HTML files
2. Properly handles UTF-8, UTF-16, and other encodings
3. Can convert all files to a specified encoding using `--target-encoding`
4. Handles BOM (Byte Order Mark) detection for Unicode files

## Architecture

HTML2MD v3.0.0 features a modern, modular architecture:

```
tools/html2md/
├── __init__.py       # Package initialization
├── __main__.py       # Entry point for module execution
├── api.py            # Programmatic API for other tools
├── cli.py            # Command-line interface
├── config/           # Configuration management
│   ├── __init__.py
│   ├── loader.py     # Config file loader
│   └── models.py     # Config data models
├── core.py           # Core conversion logic
├── crawlers.py       # Web crawling with scraper backends
├── scrapers/         # Pluggable web scraper backends
│   ├── __init__.py
│   ├── base.py       # Abstract base class
│   ├── beautifulsoup.py  # BeautifulSoup scraper
│   ├── httrack.py    # HTTrack wrapper
│   ├── selectolax.py # httpx + selectolax scraper
│   ├── scrapy_scraper.py # Scrapy framework integration
│   └── playwright.py # Playwright browser automation
├── preprocessors.py  # HTML preprocessing
└── utils.py          # Utility functions
```

### Key Components

- **API Mode**: Use as a library in other Python projects
- **Scraper Backends**: Pluggable architecture supporting BeautifulSoup and
  HTTrack
- **Type Safety**: Full type hints and dataclass models
- **Clean Architecture**: Separation of concerns with dependency injection
- **Async Support**: Modern async/await for high performance

## Integration with m1f

The html2md tool works well with the m1f (Make One File) tool for comprehensive
documentation handling:

1. First convert HTML files to Markdown:

   ```bash
   python -m tools.html2md convert ./html-docs -o ./markdown-docs
   ```

2. Then use m1f to combine the Markdown files:
   ```bash
   python -m tools.m1f --source-directory ./markdown-docs \
     --output-file ./combined-docs.m1f.txt --separator-style Markdown
   ```

This workflow is ideal for:

- Converting documentation from HTML to Markdown format
- Consolidating documentation from multiple sources
- Preparing content for LLM context windows
- Creating searchable knowledge bases

## Performance Considerations

- For large websites with many HTML files, use the `--parallel` option
- Conversion speed depends on file size, complexity, and number of files
- The `--max-workers` option can be used to control the number of parallel
  processes
- Memory usage scales with the number of worker processes and file sizes

## Programmatic API

Use html2md in your Python projects:

```python
from tools.html2md.api import Html2mdConverter
from tools.html2md.config import Config
from pathlib import Path

# Create converter with configuration
config = Config(
    source=Path("./html"),
    destination=Path("./markdown")
)
converter = Html2mdConverter(config)

# Convert a single file
output_path = converter.convert_file(Path("page.html"))
print(f"Converted to: {output_path}")

# Convert entire directory
results = converter.convert_directory()
print(f"Converted {len(results)} files")

# Convert a URL
output_path = converter.convert_url("https://example.com")

# Convert entire website with crawling
results = converter.convert_website("https://example.com")
for source, output in results.items():
    print(f"{source} -> {output}")
```

## Requirements and Dependencies

- Python 3.10 or newer
- Required packages:
  - beautifulsoup4: For HTML parsing
  - markdownify: For HTML to Markdown conversion
  - aiofiles: For async file operations
  - httpx: For async HTTP requests
- Optional packages:
  - chardet: For encoding detection
  - pyyaml: For frontmatter generation
  - httrack: For website downloading (system package)

Install dependencies:

```bash
pip install beautifulsoup4 markdownify chardet pyyaml aiofiles httpx
```

For HTTrack support (required for website crawling):

```bash
# Ubuntu/Debian
sudo apt-get install httrack

# macOS
brew install httrack

# Windows (use WSL)
sudo apt-get install httrack
```

**Note**: The tool uses the native HTTrack command-line utility, not a Python
module, for professional-grade website mirroring.
