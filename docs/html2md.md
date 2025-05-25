# html2md (HTML to Markdown Converter)

A modern HTML to Markdown converter with async I/O, HTTrack integration, and parallel processing capabilities.

## Overview

The html2md tool (v2.0.0) provides a robust solution for converting HTML content to
Markdown format, with fine-grained control over the conversion process. Built with
Python 3.10+ and modern async architecture, it is especially useful for transforming 
existing HTML documentation, extracting specific content from web pages, and preparing 
content for use with Large Language Models.

## Key Features

- **Async I/O**: High-performance concurrent file processing
- **HTTrack Integration**: Download and convert entire websites
- **API Mode**: Programmatic access for integration with other tools
- **Type Safety**: Full type annotations throughout the codebase
- **Modern Architecture**: Clean modular design with dependency injection
- Recursive directory scanning for batch conversion
- CSS selector support for extracting specific content
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
python -m tools.html2md --source-dir ./website --destination-dir ./docs

# Extract only main content from HTML files
python -m tools.html2md --source-dir ./website --destination-dir ./docs \
  --outermost-selector "main.content" --ignore-selectors "nav" ".sidebar" "footer"

# Add YAML frontmatter and adjust heading levels
python -m tools.html2md --source-dir ./website --destination-dir ./docs \
  --add-frontmatter --heading-offset 1

# Download and convert a website with HTTrack (new in v2.0.0)
python -m tools.html2md --source-dir https://example.com --destination-dir ./docs \
  --httrack --include-patterns "*.html" "*/docs/*"
```

## Command Line Options

| Option                  | Description                                                                  |
| ----------------------- | ---------------------------------------------------------------------------- |
| `--source-dir`          | Directory containing HTML files to process                                   |
| `--destination-dir`     | Directory where converted Markdown files will be written                     |
| `--outermost-selector`  | CSS selector to extract specific content (e.g., `main` or `article.content`) |
| `--ignore-selectors`    | CSS selectors for elements to remove (e.g., `nav` `.sidebar` `footer`)       |
| `--remove-elements`     | HTML elements to remove (default: script, style, iframe, noscript)           |
| `--include-extensions`  | File extensions to include (default: .html, .htm, .xhtml)                    |
| `--exclude-patterns`    | Patterns to exclude from processing                                          |
| `--exclude-dirs`        | Directory names to exclude from processing                                   |
| `--heading-offset`      | Number to add to heading levels (e.g., h1 → h2 if offset=1)                  |
| `--add-frontmatter`     | Add YAML frontmatter to the output Markdown                                  |
| `--frontmatter-fields`  | Custom frontmatter fields (format: key=value)                                |
| `--strip-classes`       | Strip class attributes from HTML elements (default: true)                    |
| `--add-line-breaks`     | Add line breaks between block elements (default: true)                       |
| `--convert-code-blocks` | Convert code blocks with language hints (default: true)                      |
| `--target-encoding`     | Convert all files to the specified character encoding                        |
| `--parallel`            | Enable parallel processing for faster conversion                             |
| `--max-workers`         | Maximum number of worker processes for parallel conversion                   |
| `-f, --force`           | Force overwrite of existing Markdown files                                   |
| `-v, --verbose`         | Enable verbose output                                                        |
| `-q, --quiet`           | Suppress all console output                                                  |

## Usage Examples

### Basic Conversion

```bash
# Simple conversion of all HTML files in a directory
python -m tools.html2md --source-dir ./website --destination-dir ./docs

# Convert files with verbose logging
python -m tools.html2md --source-dir ./website --destination-dir ./docs --verbose
```

### Content Selection

```bash
# Extract only the main content and ignore navigation elements
python -m tools.html2md --source-dir ./website --destination-dir ./docs \
  --outermost-selector "main" --ignore-selectors "nav" ".sidebar" "footer"

# Extract article content and remove additional elements
python -m tools.html2md --source-dir ./website --destination-dir ./docs \
  --outermost-selector "article.content" \
  --ignore-selectors ".author-bio" ".share-buttons" ".related-articles" \
  --remove-elements "script" "style" "iframe" "noscript" "div.comments"
```

### File Filtering

```bash
# Process only specific file types
python -m tools.html2md --source-dir ./website --destination-dir ./docs \
  --include-extensions .html .xhtml

# Exclude specific directories and patterns
python -m tools.html2md --source-dir ./website --destination-dir ./docs \
  --exclude-dirs "drafts" "archived" "temp" \
  --exclude-patterns "draft-" "temp-" "_private"
```

### Formatting Options

```bash
# Adjust heading levels (e.g., h1 → h2, h2 → h3)
python -m tools.html2md --source-dir ./website --destination-dir ./docs \
  --heading-offset 1

# Add YAML frontmatter with custom fields
python -m tools.html2md --source-dir ./website --destination-dir ./docs \
  --add-frontmatter --frontmatter-fields "layout=post" "category=documentation"

# Preserve class attributes and disable line breaks adjustment
python -m tools.html2md --source-dir ./website --destination-dir ./docs \
  --strip-classes=False --add-line-breaks=False
```

### Performance Optimization

```bash
# Use parallel processing for faster conversion of large sites
python -m tools.html2md --source-dir ./website --destination-dir ./docs \
  --parallel --max-workers 4

# Force overwrite of existing files
python -m tools.html2md --source-dir ./website --destination-dir ./docs \
  --force
```

### HTTrack Integration (New in v2.0.0)

```bash
# Download and convert an entire website
python -m tools.html2md --source-dir https://example.com --destination-dir ./docs \
  --httrack --httrack-path /usr/local/bin/httrack

# Download specific sections of a website
python -m tools.html2md --source-dir https://docs.example.com --destination-dir ./docs \
  --httrack --include-patterns "*/api/*" "*/guide/*" --exclude-patterns "*/old/*"
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

HTML2MD v2.0.0 features a modern, modular architecture:

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
└── utils.py          # Utility functions
```

### Key Components

- **API Mode**: Use as a library in other Python projects
- **HTTrack Integration**: Download and convert websites in one step
- **Type Safety**: Full type hints and dataclass models
- **Clean Architecture**: Separation of concerns with dependency injection

## Integration with m1f

The html2md tool works well with the m1f (Make One File) tool for
comprehensive documentation handling:

1. First convert HTML files to Markdown:

   ```bash
   python -m tools.html2md --source-dir ./html-docs --destination-dir ./markdown-docs
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

## Programmatic API (New in v2.0.0)

Use html2md in your Python projects:

```python
from tools.html2md.api import HTML2MDConverter
import asyncio

# Create converter instance
converter = HTML2MDConverter(
    outermost_selector="main",
    ignore_selectors=["nav", "footer"],
    add_frontmatter=True
)

# Convert a single file
result = asyncio.run(converter.convert_file("page.html"))
print(result.content)

# Convert multiple URLs
urls = ["https://example.com/page1", "https://example.com/page2"]
results = asyncio.run(converter.convert_directory_from_urls(urls))
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

For HTTrack support:
```bash
# Ubuntu/Debian
sudo apt-get install httrack

# macOS
brew install httrack
```
