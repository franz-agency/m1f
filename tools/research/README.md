# m1f-research

> **Note**: This documentation has been moved to
> [docs/06_research/](../../docs/06_research/)

AI-powered research tool that automatically finds, scrapes, and bundles
information on any topic.

## Overview

m1f-research extends the m1f toolkit with intelligent research capabilities. It
uses LLMs to:

- Find relevant URLs for any research topic
- Scrape and convert web content to clean Markdown
- Analyze content for relevance and extract key insights
- Create organized research bundles

## Quick Start

```bash
# Basic research
m1f-research "microservices best practices"

# Research with more sources
m1f-research "react state management" --urls 30 --scrape 15

# Research with manual URL list
m1f-research "python async" --urls-file my-links.txt

# Resume an existing job
m1f-research --resume abc123

# Add more URLs to existing job
m1f-research --resume abc123 --urls-file more-links.txt

# List all research jobs
m1f-research --list-jobs

# Check job status
m1f-research --status abc123

# Use different LLM provider
m1f-research "machine learning" --provider gemini

# Interactive mode
m1f-research --interactive
```

## Installation

m1f-research is included with the m1f toolkit. Ensure you have:

1. m1f installed with the research extension
2. An API key for your chosen LLM provider:
   - Claude: Set `ANTHROPIC_API_KEY`
   - Gemini: Set `GOOGLE_API_KEY`

## Features

### 🗄️ Job Management

- **Persistent Jobs**: All research jobs are tracked in a SQLite database
- **Resume Support**: Continue interrupted research or add more URLs
- **Job History**: View all past research with statistics
- **Per-Job Database**: Each job has its own database for URL/content tracking

### 🔍 Intelligent Search

- Uses LLMs to find high-quality, relevant URLs
- Focuses on authoritative sources
- Mixes different content types (tutorials, docs, discussions)
- **Manual URL Support**: Add your own URLs via --urls-file

### 📥 Smart Scraping

- **Per-Host Delay Management**: Only delays after 3+ requests to same host
- Concurrent scraping with intelligent scheduling
- Automatic HTML to Markdown conversion
- Handles failures gracefully
- **Content Deduplication**: Tracks content by checksum

### 🧠 Content Analysis

- Relevance scoring (0-10 scale)
- Key points extraction
- Content summarization
- Duplicate detection

### 📦 Organized Bundles

- **Hierarchical Output**: YYYY/MM/DD directory structure
- **Prominent Bundle Files**: 📚_RESEARCH_BUNDLE.md and 📊_EXECUTIVE_SUMMARY.md
- Clean Markdown output
- Table of contents
- Source metadata
- Relevance-based ordering

## Usage Examples

### Basic Research

```bash
# Research a programming topic
m1f-research "golang error handling"

# Output saved to: ./research-data/golang-error-handling-20240120-143022/
```

### Advanced Options

```bash
# Specify output location and name
m1f-research "kubernetes security" \
  --output ./research \
  --name k8s-security

# Use a specific template
m1f-research "react hooks" --template technical

# Skip analysis for faster results
m1f-research "python asyncio" --no-analysis

# Dry run to see what would happen
m1f-research "rust ownership" --dry-run
```

### Configuration File

```bash
# Use a custom configuration
m1f-research "database optimization" --config research.yml
```

## Configuration

### Command Line Options

| Option             | Description                   | Default          |
| ------------------ | ----------------------------- | ---------------- |
| `--urls`           | Number of URLs to find        | 20               |
| `--scrape`         | Number of URLs to scrape      | 10               |
| `--output`         | Output directory              | ./research-data  |
| `--name`           | Bundle name                   | auto-generated   |
| `--provider`       | LLM provider                  | claude           |
| `--model`          | Specific model                | provider default |
| `--template`       | Research template             | general          |
| `--concurrent`     | Max concurrent scrapes        | 5                |
| `--no-filter`      | Disable filtering             | false            |
| `--no-analysis`    | Skip analysis                 | false            |
| `--interactive`    | Interactive mode              | false            |
| `--dry-run`        | Preview only                  | false            |
| **Job Management** |                               |                  |
| `--resume`         | Resume existing job by ID     | None             |
| `--list-jobs`      | List all research jobs        | false            |
| `--status`         | Show job status by ID         | None             |
| `--urls-file`      | File with URLs (one per line) | None             |

### Configuration File (.m1f.config.yml)

```yaml
research:
  # LLM settings
  llm:
    provider: claude
    model: claude-3-opus-20240229
    temperature: 0.7

  # Default counts
  defaults:
    url_count: 30
    scrape_count: 15

  # Scraping behavior
  scraping:
    timeout_range: "1-3"
    max_concurrent: 5
    retry_attempts: 2

  # Content analysis
  analysis:
    relevance_threshold: 7.0
    min_content_length: 100
    prefer_code_examples: true

  # Output settings
  output:
    directory: ./research-data
    create_summary: true
    create_index: true

  # Research templates
  templates:
    technical:
      description: "Technical documentation and code"
      url_count: 30
      analysis_focus: implementation

    academic:
      description: "Academic papers and theory"
      url_count: 20
      analysis_focus: theory
```

## Templates

Pre-configured templates optimize research for different needs:

### technical

- Focuses on implementation details
- Prioritizes code examples
- Higher URL count for comprehensive coverage

### academic

- Emphasizes theoretical content
- Looks for citations and references
- Filters for authoritative sources

### tutorial

- Searches for step-by-step guides
- Prioritizes beginner-friendly content
- Includes examples and exercises

### general (default)

- Balanced approach
- Mixes different content types
- Suitable for most topics

## Output Structure

Research bundles are organized with hierarchical date structure:

```
./research-data/
├── research_jobs.db              # Main job tracking database
├── latest_research.md           # Symlink to most recent bundle
└── 2025/
    └── 07/
        └── 22/
            └── abc123_topic-name/
                ├── research.db           # Job-specific database
                ├── 📚_RESEARCH_BUNDLE.md # Main research bundle
                ├── 📊_EXECUTIVE_SUMMARY.md # Executive summary
                ├── research-bundle.md    # Standard bundle
                ├── metadata.json         # Research metadata
                └── search_results.json   # Found URLs
```

### Bundle Format

```markdown
# Research: [Your Topic]

Generated on: 2024-01-20 14:30:22 Total sources: 10

---

## Table of Contents

1. [Source Title 1](#1-source-title-1)
2. [Source Title 2](#2-source-title-2) ...

---

## Summary

[Research summary and top sources]

---

## 1. Source Title

**Source:** https://example.com/article **Relevance:** 8.5/10

### Key Points:

- Important point 1
- Important point 2

### Content:

[Full content in Markdown]

---
```

## Providers

### Claude (Anthropic)

- Default provider
- Best for: Comprehensive research, nuanced analysis
- Set: `ANTHROPIC_API_KEY`

### Gemini (Google)

- Fast and efficient
- Best for: Quick research, technical topics
- Set: `GOOGLE_API_KEY`

### CLI Tools

- Use local tools like `gemini-cli`
- Best for: Privacy, offline capability
- Example: `--provider gemini-cli`

## Tips

1. **Start broad, then narrow**: Use more URLs initially, let analysis filter
2. **Use templates**: Match template to your research goal
3. **Interactive mode**: Great for exploratory research
4. **Combine with m1f**: Feed research bundles into m1f for AI analysis

## Troubleshooting

### No API Key

```
Error: API key not set for ClaudeProvider
```

Solution: Set environment variable or pass in config

### Rate Limiting

```
Error: 429 Too Many Requests
```

Solution: Reduce `--concurrent` or increase timeout range

### Low Quality Results

- Increase `--urls` for more options
- Adjust `relevance_threshold` in config
- Try different `--template`

## Database Architecture

### Main Database (research_jobs.db)

Tracks all research jobs:

- Job ID, query, status, timestamps
- Configuration used
- Statistics (URLs found, scraped, analyzed)

### Per-Job Database (research.db)

Tracks job-specific data:

- URLs (source, status, checksums)
- Content (markdown, metadata)
- Analysis results (scores, key points)

### Smart Delay Management

The scraper implements intelligent per-host delays:

- No delay for first 3 requests to a host
- Random 1-3 second delay after threshold
- Allows fast parallel scraping of different hosts

## Future Features

- Multi-source research (GitHub, arXiv, YouTube)
- Knowledge graph building
- Research collaboration
- Custom source plugins
- Web UI
- Export to various formats (PDF, DOCX)
- Integration with note-taking tools

## Contributing

m1f-research is part of the m1f project. Contributions welcome!

- Report issues: [GitHub Issues](https://github.com/m1f/m1f/issues)
- Submit PRs: Follow m1f contribution guidelines
- Request features: Open a discussion
