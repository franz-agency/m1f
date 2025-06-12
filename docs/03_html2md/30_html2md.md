# html2md (HTML to Markdown Converter)

A modern HTML to Markdown converter with HTML structure analysis, custom
extractors, async I/O, and parallel processing capabilities.

## Overview

The html2md tool (v3.1.0) provides a robust solution for converting HTML content
to Markdown format, with fine-grained control over the conversion process. Built
with Python 3.10+ and modern async architecture, it focuses on intelligent
content extraction and conversion.

**New in v3.1.0:** Custom extractor plugin system for site-specific content
extraction.

**Note:** Web scraping functionality has been moved to the separate `webscraper`
tool for better modularity. Use `webscraper` to download websites, then
`html2md` to convert the downloaded HTML files.

## Key Features

- **Custom Extractor System**: Create site-specific extractors for optimal
  content extraction
- **HTML Structure Analysis**: Analyze HTML files to find optimal content
  selectors
- **Intelligent Content Extraction**: Use CSS selectors to extract specific
  content
- **Async I/O**: High-performance concurrent file processing
- **API Mode**: Programmatic access for integration with other tools
- **Type Safety**: Full type annotations throughout the codebase
- **Modern Architecture**: Clean modular design
- **Workflow Integration**: .scrapes directory structure for organized
  processing
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
m1f-html2md convert ./website -o ./docs

# Use a custom extractor for site-specific conversion
m1f-html2md convert ./website -o ./docs \
  --extractor ./extractors/custom_extractor.py

# Extract only main content from HTML files
m1f-html2md convert ./website -o ./docs \
  --content-selector "main.content" --ignore-selectors nav .sidebar footer

# Skip YAML frontmatter and adjust heading levels
m1f-html2md convert ./website -o ./docs \
  --no-frontmatter --heading-offset 1

# Analyze HTML structure to find best selectors
m1f-html2md analyze ./html/*.html --suggest-selectors

# Analyze with detailed structure output
m1f-html2md analyze ./html/*.html --show-structure --common-patterns

# Generate a configuration file
m1f-html2md config -o config.yaml
```

### Complete Workflow Example with .scrapes Directory

```bash
# Step 1: Create project structure
mkdir -p .scrapes/my-project/{html,md,extractors}

# Step 2: Download website using webscraper
m1f-scrape https://example.com -o .scrapes/my-project/html

# Step 3: Analyze HTML structure (optional)
m1f-html2md analyze .scrapes/my-project/html/*.html --suggest-selectors

# Step 4: Create custom extractor (optional)
# Use Claude to analyze and create site-specific extractor:
claude -p "Analyze these HTML files and create a custom extractor for html2md" \
  --files .scrapes/my-project/html/*.html

# Step 5: Convert with custom extractor
m1f-html2md convert .scrapes/my-project/html -o .scrapes/my-project/md \
  --extractor .scrapes/my-project/extractors/custom_extractor.py
```

## Command Line Interface

The html2md tool uses subcommands for different operations:

### Convert Command

Convert local HTML files to Markdown:

```bash
m1f-html2md convert <source> -o <output> [options]
```

| Option               | Description                                                   |
| -------------------- | ------------------------------------------------------------- |
| `source`             | Source file or directory                                      |
| `-o, --output`       | Output file or directory (required)                           |
| `-c, --config`       | Configuration file path (YAML format)                         |
| `--format`           | Output format: markdown, m1f_bundle, json (default: markdown) |
| `--extractor`        | Path to custom extractor Python file                          |
| `--content-selector` | CSS selector for main content                                 |
| `--ignore-selectors` | CSS selectors to ignore (space-separated)                     |
| `--heading-offset`   | Offset heading levels (default: 0)                            |
| `--no-frontmatter`   | Don't add YAML frontmatter                                    |
| `--parallel`         | Enable parallel processing                                    |
| `--log-file`         | Log to file                                                   |
| `-v, --verbose`      | Enable verbose output                                         |
| `-q, --quiet`        | Suppress all output except errors                             |
| `--version`          | Show version information and exit                             |

### Analyze Command

Analyze HTML structure for optimal content extraction:

```bash
m1f-html2md analyze <files> [options]
```

| Option                | Description                                                          |
| --------------------- | -------------------------------------------------------------------- |
| `files`               | HTML files to analyze (2-3 files recommended)                        |
| `--show-structure`    | Show detailed HTML structure                                         |
| `--common-patterns`   | Find common patterns across files                                    |
| `--suggest-selectors` | Suggest CSS selectors for content extraction (default if no options) |
| `-v, --verbose`       | Enable verbose output                                                |
| `-q, --quiet`         | Suppress all output except errors                                    |
| `--log-file`          | Log to file                                                          |

### Config Command

Generate a configuration file template:

```bash
m1f-html2md config [options]
```

| Option         | Description                                            |
| -------------- | ------------------------------------------------------ |
| `-o, --output` | Output configuration file (default: config.yaml)       |
| `--format`     | Configuration format: yaml, toml, json (default: yaml) |

## Usage Examples

### Basic Conversion

```bash
# Simple conversion of all HTML files in a directory
m1f-html2md convert ./website -o ./docs

# Convert files with verbose logging
m1f-html2md convert ./website -o ./docs --verbose

# Convert to m1f bundle format
m1f-html2md convert ./website -o ./docs.m1f --format m1f_bundle

# Convert to JSON format for processing
m1f-html2md convert ./website -o ./data.json --format json
```

### Content Selection

```bash
# Extract only the main content and ignore navigation elements
m1f-html2md convert ./website -o ./docs \
  --content-selector "main" --ignore-selectors nav .sidebar footer

# Extract article content from specific selectors
m1f-html2md convert ./website -o ./docs \
  --content-selector "article.content" \
  --ignore-selectors .author-bio .share-buttons .related-articles
```

### HTML Analysis

```bash
# Analyze HTML files to find optimal selectors
m1f-html2md analyze ./html/*.html

# Show detailed structure of HTML files
m1f-html2md analyze ./html/*.html --show-structure

# Find common patterns across multiple files
m1f-html2md analyze ./html/*.html --common-patterns

# Get all analysis options
m1f-html2md analyze ./html/*.html \
  --show-structure --common-patterns --suggest-selectors
```

### File Filtering

```bash
# Process only specific file types
m1f-html2md convert ./website -o ./docs \
  -c config.yaml  # Use a configuration file for file filtering
```

### Formatting Options

```bash
# Adjust heading levels (e.g., h1 → h2, h2 → h3)
m1f-html2md convert ./website -o ./docs \
  --heading-offset 1

# Skip frontmatter generation
m1f-html2md convert ./website -o ./docs \
  --no-frontmatter

# Use configuration file for advanced formatting options
m1f-html2md convert ./website -o ./docs -c config.yaml

# Log conversion process to file
m1f-html2md convert ./website -o ./docs \
  --log-file conversion.log
```

### Performance Optimization

```bash
# Use parallel processing for faster conversion of large sites
m1f-html2md convert ./website -o ./docs \
  --parallel
```

## Custom Extractors

The custom extractor system allows you to create site-specific content
extraction logic for optimal results. Extractors can be simple functions or full
classes.

### Creating a Custom Extractor

#### Function-based Extractor

```python
# extractors/simple_extractor.py
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any

def extract(soup: BeautifulSoup, config: Optional[Dict[str, Any]] = None) -> BeautifulSoup:
    """Extract main content from HTML."""
    # Remove navigation elements
    for nav in soup.find_all(['nav', 'header', 'footer']):
        nav.decompose()

    # Find main content
    main = soup.find('main') or soup.find('article')
    if main:
        new_soup = BeautifulSoup('<html><body></body></html>', 'html.parser')
        new_soup.body.append(main)
        return new_soup

    return soup

def postprocess(markdown: str, config: Optional[Dict[str, Any]] = None) -> str:
    """Clean up the converted markdown."""
    # Remove duplicate newlines
    import re
    return re.sub(r'\n{3,}', '\n\n', markdown)
```

#### Class-based Extractor

```python
# extractors/advanced_extractor.py
from tools.html2md.extractors import BaseExtractor
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any

class Extractor(BaseExtractor):
    """Custom extractor for specific website."""

    def extract(self, soup: BeautifulSoup, config: Optional[Dict[str, Any]] = None) -> BeautifulSoup:
        """Extract content with site-specific logic."""
        # Custom extraction logic
        return soup

    def preprocess(self, html: str, config: Optional[Dict[str, Any]] = None) -> str:
        """Preprocess raw HTML before parsing."""
        # Fix common HTML issues
        return html.replace('&nbsp;', ' ')

    def postprocess(self, markdown: str, config: Optional[Dict[str, Any]] = None) -> str:
        """Post-process converted markdown."""
        # Clean up site-specific artifacts
        return markdown
```

### Using Custom Extractors

```bash
# Use with CLI
m1f-html2md convert ./html -o ./markdown \
  --extractor ./extractors/my_extractor.py

# Use with API
from tools.html2md.api import Html2mdConverter
from pathlib import Path

converter = Html2mdConverter(
    config,
    extractor=Path("./extractors/my_extractor.py")
)
```

### .scrapes Directory Structure

The recommended workflow uses a `.scrapes` directory (gitignored) for organizing
scraping projects:

```
.scrapes/
└── project-name/
    ├── html/         # Raw HTML files from scraping
    ├── md/           # Converted Markdown files
    └── extractors/   # Custom extraction scripts
        └── custom_extractor.py
```

This structure keeps scraped content organized and separate from your main
codebase.

## Advanced Features

### YAML Frontmatter

By default, the converter adds YAML frontmatter to each Markdown file,
including:

- Title extracted from HTML title tag or first h1 element
- Source filename
- Conversion date
- Original file modification date

To disable frontmatter generation, use the `--no-frontmatter` option:

```bash
m1f-html2md convert ./website -o ./docs --no-frontmatter
```

The generated frontmatter looks like:

```yaml
---
title: Extracted from HTML
source_file: original.html
date_converted: 2023-06-15T14:30:21
date_modified: 2023-06-12T10:15:33
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
3. All output files are written in UTF-8 encoding
4. Handles BOM (Byte Order Mark) detection for Unicode files

## Architecture

HTML2MD v3.1.0 features a modern, modular architecture:

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
├── extractors.py     # Custom extractor system
├── preprocessors.py  # HTML preprocessing
├── analyze_html.py   # HTML structure analysis
└── utils.py          # Utility functions

.scrapes/             # Project scrapes directory (gitignored)
└── project-name/
    ├── html/         # Raw HTML files
    ├── md/           # Converted Markdown
    └── extractors/   # Custom extractors
```

### Key Components

- **API Mode**: Use as a library in other Python projects
- **Custom Extractors**: Pluggable extractor system for site-specific logic
- **Type Safety**: Full type hints and dataclass models
- **Clean Architecture**: Separation of concerns with dependency injection
- **Async Support**: Modern async/await for high performance
- **Workflow Integration**: Organized .scrapes directory structure

## Integration with m1f

The html2md tool works well with the m1f (Make One File) tool for comprehensive
documentation handling:

1. First convert HTML files to Markdown:

   ```bash
   m1f-html2md convert ./html-docs -o ./markdown-docs
   ```

2. Then use m1f to combine the Markdown files:
   ```bash
   m1f -s ./markdown-docs -o ./combined-docs.m1f.txt \
     --separator-style Markdown
   ```

This workflow is ideal for:

- Converting documentation from HTML to Markdown format
- Consolidating documentation from multiple sources
- Preparing content for LLM context windows
- Creating searchable knowledge bases

## Performance Considerations

- For large websites with many HTML files, use the `--parallel` option
- Conversion speed depends on file size, complexity, and number of files
- Memory usage scales with file sizes when parallel processing is enabled
- The tool uses async I/O for efficient file operations

## Programmatic API

Use html2md in your Python projects:

```python
from tools.html2md.api import Html2mdConverter
from tools.html2md.config import Config
from tools.html2md.extractors import BaseExtractor
from pathlib import Path

# Create converter with configuration
config = Config(
    source=Path("./html"),
    destination=Path("./markdown")
)
converter = Html2mdConverter(config)

# Convert with custom extractor
converter = Html2mdConverter(
    config,
    extractor=Path("./extractors/custom_extractor.py")
)

# Or with inline extractor
class MyExtractor(BaseExtractor):
    def extract(self, soup, config=None):
        # Custom logic
        return soup

converter = Html2mdConverter(config, extractor=MyExtractor())

# Convert a single file
output_path = converter.convert_file(Path("page.html"))
print(f"Converted to: {output_path}")

# Convert entire directory
results = converter.convert_directory()
print(f"Converted {len(results)} files")
```

## Requirements and Dependencies

- Python 3.10 or newer
- Required packages:
  - beautifulsoup4: For HTML parsing
  - markdownify: For HTML to Markdown conversion
  - aiofiles: For async file operations
  - rich: For console output
  - pydantic: For configuration models
- Optional packages:
  - chardet: For encoding detection
  - pyyaml: For YAML configuration files
  - toml: For TOML configuration files

Install dependencies:

```bash
pip install beautifulsoup4 markdownify chardet pyyaml aiofiles rich pydantic
```

**Note**: For web scraping functionality, use the separate `webscraper` tool
which provides multiple backend options including HTTrack.
