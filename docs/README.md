# m1f Documentation

This directory contains detailed documentation for the m1f project v2.0.0.

## Contents

### Core Tools

- [m1f (Make One File)](./m1f.md) - Documentation for the main tool that
  combines multiple files into a single file with content deduplication and
  async I/O
- [s1f (Split One File)](./s1f.md) - Documentation for the tool that extracts
  individual files from a combined file with modern Python architecture
- [token_counter](./token_counter.md) - Documentation for the token estimation
  tool

### HTML to Markdown Converter

- [html2md Overview](./html2md.md) - Comprehensive guide to the HTML to Markdown
  converter
- [html2md Guide](./html2md_guide.md) - Detailed usage guide with examples
- [html2md Test Suite](./html2md_test_suite.md) - Documentation for the
  comprehensive test suite

### Advanced Features

- [Auto Bundle Guide](./AUTO_BUNDLE_GUIDE.md) - Automatic project bundling for AI/LLM consumption
- [Claude Code Integration](./CLAUDE_CODE_INTEGRATION.md) - Optional AI-powered tool automation

## Quick Navigation

### Common Workflows

- **First-time setup**: Install Python 3.10+ and requirements:
  ```bash
  python -m venv .venv
  source .venv/bin/activate  # On Windows: .venv\Scripts\activate
  pip install -r requirements.txt
  ```
- **Basic file combination**: Use
  `python -m tools.m1f -s ./your_project -o ./combined.txt`
- **File extraction**: Use
  `python -m tools.s1f -i ./combined.txt -d ./extracted_files`
- **Check token count**: Use `python tools/token_counter.py ./combined.txt`
- **Convert HTML to Markdown**: Use
  `python -m tools.html2md convert ./html ./markdown`
- **Auto-bundle project**: Use `./scripts/auto_bundle.sh` or configure with `.m1f.config.yml`

### Key Concepts

- **Separator Styles**: Different formats for separating files in the combined
  output ([details](./m1f.md#separator-styles))
- **File Filtering**: Include/exclude specific files using patterns
  ([details](./m1f.md#command-line-options))
- **Security**: Scan for secrets before combining files
  ([details](./m1f.md#security-check))
- **Content Selection**: Extract specific content using CSS selectors
  ([details](./html2md.md#content-selection))

## Project Overview

m1f v2.0.0 is a comprehensive toolkit designed to help you work more efficiently
with Large Language Models (LLMs) by managing context. Built with modern Python
3.10+ architecture, these tools solve core challenges when working with AI
assistants.

### Key Features

- **Modern Architecture**: Complete modular rewrite with async I/O, type hints,
  and clean architecture
- **Content Deduplication**: Automatically detect and skip duplicate files based
  on SHA256 checksums
- **Performance**: Async operations and parallel processing for large projects
- **Type Safety**: Full type annotations for better IDE support and fewer
  runtime errors
- **Professional Tools**: HTTrack integration for website scraping, CSS
  selectors for content extraction

### What You Can Do

- Combine multiple project files into a single reference file with automatic
  deduplication
- Extract individual files from a combined file with preserved structure and
  metadata
- Convert entire websites to clean Markdown format with HTTrack integration
- Filter files by size, type, or custom patterns
- Detect and handle symlinks with cycle prevention
- Remove scraped metadata for clean documentation bundles
- Estimate token usage for optimal LLM context planning
