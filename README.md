# m1f - Make One File

A powerful suite of tools for working efficiently with Large Language Models
(LLMs) and AI, developed by [Franz und Franz](https://franz.agency).

## Project Overview

m1f provides utilities for efficiently working with LLMs by managing context.
The core tools are:

- **m1f (Make One File)**: Combines multiple project files into a single
  reference file for providing comprehensive context to LLMs
- **s1f (Split One File)**: Extracts individual files from a combined file,
  preserving original structure
- **webscraper**: Downloads websites for offline viewing and processing
- **html2md**: Modern HTML to Markdown converter with HTML analysis capabilities
- **token_counter**: Estimates token usage for LLM context planning and
  optimization

These tools solve the challenge of providing comprehensive context to AI
assistants while optimizing token usage.

## Quick Start

For the recommended development workflow and setup instructions, see the
[M1F Development Workflow](docs/01_m1f/04_m1f_development_workflow.md) guide. This
includes:

- Setting up convenient shell aliases for global access
- Using pre-generated m1f bundles in your projects
- Development best practices

## Features

### Content Deduplication

m1f automatically detects files with identical content and only includes them
once in the output. If the same file content appears in multiple locations
(different paths, filenames, or timestamps), only the first encountered version
will be included. This:

- Reduces redundancy in the combined output
- Decreases the token count for LLM processing
- Improves readability by eliminating duplicate sections
- Works automatically without requiring any special flags

This feature is especially useful in projects with:

- Code duplication across different directories
- Backup copies with identical content
- Files accessible through symbolic links or alternative paths

The deduplication is based purely on file content (using SHA256 checksums), so
even files with different names, paths, or modification times will be
deduplicated if their content is identical.

### Web Scraping and HTML Conversion

The toolkit now separates web scraping from HTML-to-Markdown conversion for
better modularity. The primary use case is downloading online documentation to
provide to LLMs like Claude.

#### webscraper

Downloads websites (especially documentation) for offline processing:

```bash
# Download a documentation website
python -m tools.webscraper https://docs.example.com -o ./downloaded_html

# Advanced options for larger documentation sites
python -m tools.webscraper https://docs.example.com -o ./html \
  --max-pages 50 \
  --max-depth 3 \
  --scraper beautifulsoup
```

Supported scrapers: beautifulsoup (default), httrack, scrapy, playwright,
selectolax

#### html2md

Converts HTML files to Markdown with intelligent content extraction:

```bash
# Convert HTML directory to Markdown
python -m tools.html2md convert ./downloaded_html -o ./markdown

# Analyze HTML structure to find best selectors
python -m tools.html2md analyze ./html/*.html --suggest-selectors

# Convert with specific content extraction
python -m tools.html2md convert ./html -o ./md \
  --content-selector "article.post" \
  --ignore-selectors "nav" ".sidebar" ".ads"
```

#### Complete Workflow: Documentation for LLMs

```bash
# 1. Download documentation
python -m tools.webscraper https://docs.framework.com -o ./docs_html

# 2. Convert to Markdown
python -m tools.html2md convert ./docs_html -o ./docs_md

# 3. Bundle into single file for LLM
python -m tools.m1f -s ./docs_md -o ./framework_docs.txt

# Now framework_docs.txt can be provided to Claude or other LLMs
```

### HTML2MD Integration with m1f

m1f includes enhanced support for working with HTML-to-Markdown converted
content:

- **Metadata Cleaning**: Use `--remove-scraped-metadata` to automatically remove
  URL, timestamp, and source information from scraped HTML2MD files
- **Clean Documentation Bundles**: Combine multiple scraped websites into clean,
  professional documentation without scraping artifacts
- **LLM-Ready Content**: Prepare web content for AI analysis by removing
  time-specific metadata that may confuse models

### Preset System

m1f includes a powerful preset system for applying different processing rules to
different file types:

- **Hierarchical Configuration**: Global (~/.m1f/) → User → Project settings
- **File-Specific Processing**: Different rules for HTML, CSS, JS, Python, etc.
- **Built-in Actions**: Minify, strip tags, remove comments, compress whitespace
- **Custom Processors**: Truncate large files, redact secrets, extract functions
- **Example Presets**: WordPress, web projects, documentation bundles

```bash
# Use WordPress preset for a WordPress site
python -m tools.m1f -s ./wp-site -o bundle.txt --preset presets/wordpress.m1f-presets.yml

# Apply production optimizations
python -m tools.m1f -s ./project -o bundle.txt --preset prod.yml --preset-group production
```

See [Preset System Guide](docs/01_m1f/02_m1f_presets.md) for detailed documentation.

## Installation

```bash
# Clone the repository
git clone https://github.com/franzundfriends/m1f.git
cd m1f

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Optional: Claude Code Integration

For AI-powered automation of m1f tools, you can install Claude Code:

```bash
npm install -g @anthropic-ai/claude-code
```

This enables natural language control of all tools. For example:

- "Bundle all Python files into a single m1f"
- "Convert HTML documentation to Markdown with preprocessing"
- "Create topic-based bundles from documentation"

See [Claude Code Integration Guide](docs/01_m1f/05_claude_code_integration.md) for setup
and usage.

## Documentation

For detailed documentation, please check the [docs directory](./docs/README.md).

## License

This project is licensed under the Apache 2.0 License. See the [LICENSE](LICENSE)
file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
