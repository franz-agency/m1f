# m1f Documentation

This directory contains detailed documentation for the m1f project v3.2.0.

## Contents

### Core Tools

- [m1f (Make One File)](01_m1f/00_m1f.md) - Documentation for the main tool that
  combines multiple files into a single file with content deduplication and
  async I/O
- [s1f (Split One File)](02_s1f/20_s1f.md) - Documentation for the tool that
  extracts individual files from a combined file with modern Python architecture
- [token_counter](99_misc/98_token_counter.md) - Documentation for the token
  estimation tool

### Web Scraping and HTML Conversion

- [webscraper](04_scrape/40_webscraper.md) - Download websites for offline
  viewing and processing
- [html2md Overview](03_html2md/30_html2md.md) - Comprehensive guide to the HTML
  to Markdown converter
- [html2md Guide](03_html2md/31_html2md_guide.md) - Detailed usage guide with
  examples
- [html2md Test Suite](03_html2md/33_html2md_test_suite.md) - Documentation for
  the comprehensive test suite

### Advanced Features

- [Auto Bundle Guide](01_m1f/20_auto_bundle_guide.md) - Automatic project
  bundling for AI/LLM consumption
- [Claude + m1f Workflows](01_m1f/30_claude_workflows.md) - Turn Claude into
  your personal m1f expert with smart prompt enhancement
- [Claude Code Integration](01_m1f/31_claude_code_integration.md) - Optional
  AI-powered tool automation
- [Preset System Guide](01_m1f/10_m1f_presets.md) - File-specific processing
  rules and configurations
- [Per-File-Type Settings](01_m1f/11_preset_per_file_settings.md) - Fine-grained
  control over file processing

### Development

- [Version Management](05_development/55_version_management.md) - Version
  management and release process
- [Git Hooks Setup](05_development/56_git_hooks_setup.md) - Git hooks for
  automated bundling

## Quick Navigation

### Common Workflows

- **First-time setup**: Install Python 3.10+ and requirements:
  ```bash
  python -m venv .venv
  source .venv/bin/activate  # On Windows: .venv\Scripts\activate
  pip install -r requirements.txt
  ```
- **Basic file combination**: Use
  `m1f -s ./your_project -o ./combined.txt`
- **File extraction**: Use
  `m1f-s1f -i ./combined.txt -d ./extracted_files`
- **Check token count**: Use `m1f-token-counter ./combined.txt`
- **Download website**: Use
  `m1f-scrape https://example.com -o ./html`
- **Convert HTML to Markdown**: Use
  `m1f-html2md convert ./html ./markdown`
- **Auto-bundle project**: Use `./scripts/auto_bundle.sh` or configure with
  `.m1f.config.yml`

### Key Concepts

- **Separator Styles**: Different formats for separating files in the combined
  output ([details](01_m1f/00_m1f.md#separator-styles))
- **File Filtering**: Include/exclude specific files using patterns
  ([details](01_m1f/00_m1f.md#command-line-options))
- **Security**: Scan for secrets before combining files
  ([details](01_m1f/00_m1f.md#security-check))
- **Content Selection**: Extract specific content using CSS selectors
  ([details](03_html2md/30_html2md.md#content-selection))

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
