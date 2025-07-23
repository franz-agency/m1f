# m1f-research

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

# List all research jobs
m1f-research --list-jobs

# Resume a job
m1f-research --resume abc123

# Filter jobs by date
m1f-research --list-jobs --date 2025-07

# Search for specific topics
m1f-research --list-jobs --search "python"
```

## Installation

m1f-research is included with the m1f toolkit. Ensure you have:

1. m1f installed with the research extension
2. An API key for your chosen LLM provider:
   - Claude: Set `ANTHROPIC_API_KEY`
   - Gemini: Set `GOOGLE_API_KEY`

## Features

### 🗄️ Job Management

- **Persistent Jobs**: All research tracked in SQLite database
- **Resume Support**: Continue interrupted research
- **Advanced Filtering**: Search by date, query term
- **Pagination**: Handle large job lists efficiently

### 🔍 Intelligent Search

- Uses LLMs to find high-quality, relevant URLs
- Manual URL support via `--urls-file`
- Focuses on authoritative sources
- Mixes different content types

### 📥 Smart Scraping

- **Per-host delays**: Only after 3+ requests to same host
- Concurrent scraping across different hosts
- Automatic HTML to Markdown conversion
- Content deduplication via checksums

### 🧠 Content Analysis

- Relevance scoring (0-10 scale)
- Key points extraction
- Content summarization
- Duplicate detection

### 📦 Organized Output

- **Hierarchical structure**: YYYY/MM/DD/job_id/
- Prominent bundle files (📚_RESEARCH_BUNDLE.md)
- Clean Markdown output
- Symlink to latest research

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

### Key Command Line Options

| Option             | Description              | Default |
| ------------------ | ------------------------ | ------- |
| **Research**       |                          |         |
| `--urls`           | Number of URLs to find   | 20      |
| `--scrape`         | Number of URLs to scrape | 10      |
| `--urls-file`      | File with manual URLs    | None    |
| **Job Management** |                          |         |
| `--resume`         | Resume job by ID         | None    |
| `--list-jobs`      | List all jobs            | False   |
| `--status`         | Show job details         | None    |
| **Filtering**      |                          |         |
| `--search`         | Search jobs by query     | None    |
| `--date`           | Filter by date           | None    |
| `--limit`          | Pagination limit         | None    |
| `--offset`         | Pagination offset        | 0       |
| **Cleanup**        |                          |         |
| `--clean-raw`      | Clean job raw data       | None    |
| `--clean-all-raw`  | Clean all raw data       | False   |

See [63_cli_reference.md](63_cli_reference.md) for complete option list.

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

Research data uses hierarchical date-based organization:

```
./research-data/
├── research_jobs.db              # Main job database
├── latest_research.md           # Symlink to latest bundle
└── 2025/
    └── 07/
        └── 23/
            └── abc123_topic-name/
                ├── research.db           # Job-specific database
                ├── 📚_RESEARCH_BUNDLE.md # Main bundle
                ├── 📊_EXECUTIVE_SUMMARY.md # Summary
                ├── metadata.json         # Job metadata
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

## Documentation

- [62_job_management.md](62_job_management.md) - Job persistence and filtering
  guide
- [63_cli_reference.md](63_cli_reference.md) - Complete CLI reference
- [64_api_reference.md](64_api_reference.md) - Developer API documentation
- [65_architecture.md](65_architecture.md) - Technical architecture details
- [66_examples.md](66_examples.md) - Real-world usage examples

## Future Features

- Multi-source research (GitHub, arXiv, YouTube)
- Knowledge graph building
- Research collaboration
- Export to various formats
- Job tagging system

## Contributing

m1f-research is part of the m1f project. Contributions welcome!

- Report issues: [GitHub Issues](https://github.com/m1f/m1f/issues)
- Submit PRs: Follow m1f contribution guidelines
- Request features: Open a discussion
