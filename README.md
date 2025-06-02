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
- **token_counter**: Estimates token usage for LLM context planning and
  optimization
- **html2md**: Modern HTML to Markdown converter with website crawling
  capabilities using HTTrack

These tools solve the challenge of providing comprehensive context to AI
assistants while optimizing token usage.

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

### HTML2MD Integration

m1f now includes enhanced support for working with HTML-to-Markdown converted
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

See [Preset System Guide](docs/m1f_presets.md) for detailed documentation.

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

See [Claude Code Integration Guide](docs/CLAUDE_CODE_INTEGRATION.md) for setup
and usage.

## Documentation

For detailed documentation, please check the [docs directory](./docs/README.md).

## License

This project is licensed under the MIT License. See the [LICENSE.md](LICENSE)
file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
