# m1f-research Documentation

> ⚠️ **Early Alpha Warning**: m1f-research is in early alpha and under heavy development. Expect significant changes to features, APIs, and workflows.

AI-powered research orchestrator that automates the entire workflow from finding sources to creating Claude-ready knowledge bundles.

## What is m1f-research?

While the m1f toolkit provides individual tools (m1f-scrape, m1f-html2md, m1f), **m1f-research orchestrates them all** into an intelligent research pipeline:

1. **AI finds sources** on any topic (using Claude/Gemini)
2. **You review and curate** the URLs (unlike black-box LLM research modes)
3. **Automatically processes** everything: scrape → convert → bundle
4. **Creates knowledge bundles** ready for Claude's Project Knowledge

**Key advantage**: Unlike LLM "research modes", YOU control which sources are used and can add your own trusted sources.

## 🚀 New: 7-Phase Workflow System

The m1f-research tool now features an advanced workflow system that transforms simple queries into comprehensive research:

1. **Query Expansion** - Automatically generate search variations
2. **URL Collection** - Gather URLs from multiple sources  
3. **Interactive Review** - Curate URLs before scraping
4. **Deep Crawling** - Follow links for comprehensive coverage
5. **Smart Bundling** - Organize content intelligently
6. **AI Analysis** - Generate insights and summaries
7. **Phase Management** - Resume from any phase

## Documentation Files

- [60_research_overview.md](60_research_overview.md) - Overview, workflow system, and quick start
- [62_job_management.md](62_job_management.md) - Job persistence and filtering
- [63_cli_reference.md](63_cli_reference.md) - Complete command reference with workflow options
- [64_api_reference.md](64_api_reference.md) - Developer documentation
- [65_architecture.md](65_architecture.md) - Technical architecture and workflow components
- [66_examples.md](66_examples.md) - Real-world usage examples with workflow scenarios
- [67_cli_improvements.md](67_cli_improvements.md) - Enhanced CLI features and UX
- [68_job_deletion_guide.md](68_job_deletion_guide.md) - Complete guide to job deletion

## Quick Start

```bash
# Basic research with automatic workflow
m1f-research "python async programming"

# Interactive research with URL review
m1f-research "machine learning frameworks" --expand-queries --max-queries 10

# Deep research with crawling
m1f-research "rust web frameworks" --crawl-depth 2 --max-pages-per-site 20

# Generate comparative analysis
m1f-research "cloud providers" --analysis-type comparative

# List all jobs with phase status
m1f-research --list-jobs

# Resume a job from specific phase
m1f-research --resume abc123
```

## Workflow Configuration

Create a `.m1f-research.yml` for custom workflows:

```yaml
workflow:
  expand_queries: true      # Generate search variations
  max_queries: 5           # Number of query variations
  skip_review: false       # Interactive URL review
  crawl_depth: 1          # Follow links one level deep
  max_pages_per_site: 10  # Limit per domain
  generate_analysis: true  # Create AI analysis
  analysis_type: summary   # summary/comparative/technical/trend
```

For detailed documentation, see the numbered files above.
