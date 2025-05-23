# HTML to Markdown Converter 2.0

A modern, modular tool for converting HTML content to Markdown format, optimized for processing entire websites and integration with m1f.

## Features

### 🚀 Core Features
- **Advanced Content Extraction**: Smart detection of main content using CSS selectors
- **Metadata Preservation**: Extracts OpenGraph, Schema.org, and meta tags
- **Parallel Processing**: Convert thousands of files efficiently
- **Web Crawling**: Convert entire websites using HTTrack
- **m1f Integration**: Direct creation of m1f bundles for LLM consumption

### 🎯 Content Selection
- CSS selectors for precise content targeting
- Ignore unwanted elements (nav, sidebar, ads)
- Preserve specific HTML attributes
- Smart heading detection and hierarchy

### 🔧 Processing Options
- Heading level adjustment
- Link conversion (HTML → Markdown)
- Code block language detection
- Encoding detection and conversion
- Whitespace normalization

### 🌐 Web Crawling with HTTrack
- Professional website mirroring with HTTrack
- Sitemap.xml support
- robots.txt compliance
- Domain restrictions
- Bandwidth and connection management

## Installation

```bash
# Install required dependencies
pip install beautifulsoup4 markdownify pydantic rich requests chardet pyyaml

# Optional dependencies
pip install toml  # For TOML config files

# Install HTTrack for website mirroring
# Ubuntu/Debian:
sudo apt-get install httrack

# macOS:
brew install httrack

# Windows:
# Download from https://www.httrack.com/
```

## Quick Start

### Convert a Single File
```bash
python -m tools.html_to_md convert index.html -o index.md
```

### Convert a Directory
```bash
python -m tools.html_to_md convert ./docs/html/ -o ./docs/markdown/
```

### Convert a Website
```bash
python -m tools.html_to_md crawl https://example.com -o ./example-docs/
```

### Using Configuration File
```bash
python -m tools.html_to_md convert ./html/ -c config.yaml
```

## Configuration

Create a `config.yaml` file for advanced options:

```yaml
source: ./html_docs
destination: ./markdown_docs

extractor:
  content_selector: "article.main-content"
  ignore_selectors:
    - nav
    - .sidebar
    - footer

processor:
  heading_offset: 1  # Convert h1 → h2, h2 → h3, etc.
  link_handling: convert
  
crawler:
  max_depth: 5
  max_pages: 1000
  allowed_domains:
    - example.com
  respect_robots_txt: true
  concurrent_requests: 5
```

## Python API

```python
from tools.html_to_md import HtmlToMarkdownConverter

# Simple conversion
converter = HtmlToMarkdownConverter({
    "source": "./html",
    "destination": "./markdown"
})

# Convert directory
outputs = converter.convert_directory()

# Convert URL
output = converter.convert_url("https://example.com/page.html")

# Convert entire website (uses HTTrack)
results = converter.convert_website("https://example.com")
```

## Advanced Usage

### Content Extraction

Extract specific content from complex HTML:

```python
config = {
    "extractor": {
        "content_selector": "main.post-content",
        "ignore_selectors": [".comments", ".social-share"],
        "strip_attributes": True,
        "preserve_attributes": ["id", "href", "src"]
    }
}
```

### Link Handling

Control how links are processed:

```python
config = {
    "processor": {
        "link_handling": "convert",  # convert, preserve, absolute, relative
        "link_extensions": {
            ".html": ".md",
            ".php": ".md"
        }
    }
}
```

### HTTrack Configuration

Fine-tune website mirroring:

```python
config = {
    "crawler": {
        "max_depth": 10,
        "max_pages": 5000,
        "concurrent_requests": 10,
        "request_delay": 0.5,  # seconds
        "allowed_domains": ["docs.example.com"],
        "exclude_patterns": [".*/api/.*", ".*\\.pdf$"]
    }
}
```

### m1f Bundle Creation

Generate m1f bundles directly:

```python
config = {
    "output_format": "m1f_bundle",
    "m1f": {
        "create_bundle": True,
        "bundle_name": "my-docs",
        "include_assets": True,
        "metadata": {
            "project": "My Documentation",
            "version": "1.0.0"
        }
    }
}
```

## Architecture

The tool is built with a modular architecture:

- **Core**: HTML parsing and Markdown conversion
- **Extractors**: Content extraction plugins
- **Processors**: Post-processing pipeline
- **Crawlers**: HTTrack integration for website mirroring
- **Config**: Flexible configuration system
- **Utils**: Encoding detection, logging

## Performance

- Parallel processing with configurable workers
- Efficient memory usage for large files
- Progress bars for long operations
- HTTrack for reliable website mirroring

## Contributing

Contributions are welcome! The modular architecture makes it easy to:

- Add new content extractors
- Create custom processors
- Implement new output formats
- Enhance crawling capabilities

## License

MIT License - see LICENSE.md for details

## Credits

Created by Franz und Franz (https://franz.agency) for the m1f project. 