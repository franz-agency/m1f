# m1f-research

AI-powered research tool that orchestrates the entire research workflow: from finding sources to creating AI-ready knowledge bundles.

## The Big Picture: Why m1f-research?

The m1f toolkit already provides powerful individual tools:
- **m1f-scrape**: Scrapes websites and downloads content
- **m1f-html2md**: Converts HTML to clean Markdown
- **m1f**: Bundles files for AI consumption

**m1f-research takes this further by automating the entire research workflow:**

1. **AI-Powered Discovery**: Instead of manually finding URLs, m1f-research uses AI (like Claude) to search for relevant sources on any topic
2. **Human-in-the-Loop**: Review and curate the discovered URLs before scraping
3. **Automated Pipeline**: Automatically scrapes approved URLs, converts to Markdown, and creates bundles
4. **AI-Ready Output**: Produces research bundles perfect for uploading to Claude's Project Knowledge or other AI tools

Think of it as your automated research assistant that:
- Takes a topic (e.g., "microservices best practices")
- Asks AI to find the best sources
- Lets you review what it found
- Downloads and processes everything
- Creates a knowledge bundle ready for AI analysis

### Key Advantage Over LLM "Research Mode"

**The crucial difference from built-in LLM research modes:** 
- **You control the sources**: Review and prioritize which URLs to include
- **Custom curation**: Remove low-quality or irrelevant sources before processing
- **Add your own sources**: Include specific URLs you trust
- **Persistent knowledge**: Create reusable knowledge bundles for your projects
- **No black box**: You see exactly what content goes into your research

## Overview

m1f-research orchestrates the complete research pipeline by intelligently combining all m1f tools:

- **Discovers** relevant URLs using AI (instead of manual searching)
- **Reviews** URLs with optional human curation
- **Scrapes** approved content using m1f-scrape
- **Converts** HTML to Markdown using m1f-html2md
- **Bundles** everything using m1f for AI consumption
- **Analyzes** content to extract key insights

### 7-Phase Workflow System

m1f-research implements a sophisticated workflow system that breaks research into 7 distinct phases:

1. **INITIALIZATION** - Setup and configuration validation
2. **QUERY_EXPANSION** - Generate multiple search query variations for comprehensive coverage
3. **URL_COLLECTION** - Search for relevant URLs using expanded queries
4. **URL_REVIEW** - Optional human review and curation of found URLs
5. **CRAWLING** - Intelligent web scraping with depth control and link following
6. **BUNDLING** - Organize scraped content into structured research bundles
7. **ANALYSIS** - Generate AI-powered insights and summaries

This workflow allows for flexible research strategies, checkpoint resumption, and fine-grained control over each phase.

## Practical Example: Research Workflow

Let's say you want to research "Python async programming best practices":

### Without m1f-research (Manual Process):
1. Google search for relevant articles
2. Open each link, evaluate quality
3. Use `m1f-scrape` on each good URL
4. Run `m1f-html2md` to convert each file
5. Use `m1f` to bundle everything
6. Upload to Claude's Project Knowledge

### With m1f-research (Automated):
```bash
# One command does it all!
m1f-research "Python async programming best practices"
```

What happens behind the scenes:
1. **AI searches** for the best sources on Python async programming
2. **You review** the URLs (optional - can be skipped)
3. **Automatically scrapes** all approved URLs
4. **Converts** everything to Markdown
5. **Creates bundle** ready for Claude: `research_bundle.md`
6. **Generates summary** with key insights

The result: A complete research bundle you can directly upload to Claude's Project Knowledge!

## Quick Start

```bash
# Basic research - let AI find sources
m1f-research "microservices best practices"

# Research with more sources
m1f-research "react state management" --urls 30 --scrape 15

# Interactive URL review (recommended for important research)
m1f-research "kubernetes security" --skip-review false

# Use the research bundle with Claude
# The output file research_bundle.md can be uploaded directly to Claude's Project Knowledge

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
- **Resume Support**: Continue interrupted research at any workflow phase
- **Advanced Filtering**: Search by date, query term
- **Pagination**: Handle large job lists efficiently
- **Phase Tracking**: Monitor progress through 7-phase workflow

### 🔍 Intelligent Search

- **Query Expansion**: Generate multiple search variations for comprehensive coverage
- Uses LLMs to find high-quality, relevant URLs
- Manual URL support via `--urls-file`
- Focuses on authoritative sources
- Mixes different content types

### 🎯 URL Review & Prioritization

This is where m1f-research shines compared to automated LLM research:

- **Interactive Review Interface**: See all discovered URLs before scraping
- **Quality Control**: Remove spam, paywalled, or low-quality sources
- **Add Custom URLs**: Include your trusted sources or internal documentation
- **Prioritize Sources**: Decide which sources are most important
- **Skip if Needed**: Use `--skip-review` for fully automated research

### 🌐 Advanced Crawling

- **Deep Crawling**: Follow links to specified depth levels
- **Intelligent Filtering**: Domain-based and pattern-based URL filtering
- **Site Limits**: Control maximum pages per domain

### 📥 Smart Scraping

- **Per-host delays**: Only after 3+ requests to same host
- Concurrent scraping across different hosts
- Automatic HTML to Markdown conversion
- Content deduplication via checksums

### 🧠 Content Analysis

- **Analysis Generator**: AI-powered insights and summaries
- Relevance scoring (0-10 scale)
- Key points extraction
- Content summarization
- Duplicate detection
- Template-based analysis approaches

### 📦 Organized Output

- **Hierarchical structure**: YYYY/MM/DD/job_id/
- Prominent bundle files (research_bundle.md)
- Clean Markdown output
- Symlink to latest research
- Phase-specific output organization

## Integration with Claude Projects

The research bundles created by m1f-research are perfect for Claude's Project Knowledge feature:

1. **Run Research**:
   ```bash
   m1f-research "your research topic"
   ```

2. **Find Your Bundle**:
   - Look in `./research-data/latest_research.md` (symlink to latest)
   - Or navigate to `./research-data/YYYY/MM/DD/job_id/research_bundle.md`

3. **Upload to Claude**:
   - Open Claude.ai or Claude desktop app
   - Create or open a project
   - Add the `research_bundle.md` to Project Knowledge
   - Claude now has deep knowledge about your research topic!

4. **Benefits**:
   - Claude can reference specific sources from your research
   - Knowledge persists across conversations in the project
   - You know exactly what information Claude is using
   - Can update research and refresh Claude's knowledge anytime

## Usage Examples

### Basic Research

```bash
# Research a programming topic
m1f-research "golang error handling"

# Output saved to: ./research-data/golang-error-handling-20240120-143022/
# Ready for upload to Claude Projects!
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

  # Workflow configuration
  workflow:
    expand_queries: true        # Generate search query variations
    max_queries: 5             # Maximum expanded queries
    skip_review: false         # Skip URL review interface
    crawl_depth: 0             # How many levels deep to crawl
    max_pages_per_site: 10     # Maximum pages per domain
    follow_external: false     # Follow external links
    generate_analysis: true    # Generate AI analysis
    analysis_type: "summary"   # Type of analysis to generate

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
                ├── research_bundle.md     # Main bundle
                ├── research_summary.md    # Summary
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
