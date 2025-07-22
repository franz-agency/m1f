# m1f-research Architecture

## Overview

The m1f-research tool is built on a modular architecture that combines web
search, content scraping, and AI-powered analysis to create comprehensive
research bundles.

## Core Components

### 1. Orchestrator (`orchestrator.py`)

- Central coordination of the research workflow
- Manages the pipeline: search → scrape → analyze → bundle
- Handles configuration and state management

### 2. LLM Interface (`llm_interface.py`)

- Abstraction layer for different LLM providers
- Supports Claude, Gemini, and CLI tools
- Manages API calls and response parsing

### 3. Scraper (`scraper.py`)

- Concurrent web scraping with rate limiting
- Integrates with html2md for content conversion
- Handles failures gracefully with retry logic

### 4. Analyzer (`analyzer.py`)

- Content relevance scoring
- Key points extraction
- Duplicate detection
- Template-based analysis

### 5. Bundle Creator (`bundle_creator.py`)

- Organizes scraped content into structured bundles
- Creates table of contents and summaries
- Formats output in clean Markdown

## Data Flow

```
User Query
    ↓
Orchestrator
    ↓
LLM Search → URLs
    ↓
Concurrent Scraping → Raw Content
    ↓
HTML to Markdown → Clean Content
    ↓
Content Analysis → Scored Content
    ↓
Bundle Creation → Research Bundle
```

## Configuration System

The research tool uses a hierarchical configuration system:

1. **Default Config**: Built-in defaults
2. **User Config**: ~/.m1f.config.yml
3. **Project Config**: ./.m1f.config.yml
4. **CLI Arguments**: Command-line overrides

## Templates

Templates customize the research process for different use cases:

- **Search Prompts**: How to find URLs
- **Analysis Focus**: What to extract
- **Output Format**: How to structure results

### Template Structure

```yaml
template_name:
  description: "Purpose of this template"
  search:
    focus: "What to look for"
    source_types: ["tutorial", "documentation", "discussion"]
  analysis:
    relevance_prompt: "Custom relevance criteria"
    key_points_prompt: "What to extract"
  output:
    structure: "How to organize results"
```

## Concurrency Model

The tool uses asyncio for efficient concurrent operations:

- **URL Search**: Sequential (LLM rate limits)
- **Web Scraping**: Concurrent with semaphore (default: 5)
- **Content Analysis**: Batch processing
- **Bundle Creation**: Sequential

## Error Handling

- **Graceful Degradation**: Failed scrapes don't stop the process
- **Retry Logic**: Automatic retries for transient failures
- **Fallback Providers**: Switch providers on API errors
- **Detailed Logging**: Track issues for debugging

## Security Considerations

- **URL Validation**: Prevent SSRF attacks
- **Content Sanitization**: Remove potentially harmful content
- **Rate Limiting**: Respect server resources
- **API Key Management**: Secure credential handling

## Extension Points

The architecture supports several extension mechanisms:

1. **Custom Providers**: Add new LLM providers
2. **Scraper Backends**: Integrate new scraping tools
3. **Analysis Templates**: Create domain-specific templates
4. **Output Formats**: Add new bundle formats

## Performance Optimizations

- **Concurrent Scraping**: Parallel downloads
- **Streaming Processing**: Handle large content
- **Caching**: Avoid duplicate work
- **Lazy Loading**: Load components on demand

## Future Architecture Plans

- **Plugin System**: Dynamic loading of extensions
- **Distributed Scraping**: Scale across multiple machines
- **Knowledge Graph**: Build connections between research
- **Real-time Updates**: Monitor sources for changes
