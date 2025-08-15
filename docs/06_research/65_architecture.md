# m1f-research Architecture

## Overview

The m1f-research tool is built on a modular architecture that combines web
search, content scraping, and AI-powered analysis to create comprehensive
research bundles.

## Core Components

### 1. Orchestrator (`orchestrator.py`)

- Central coordination of the research workflow
- Manages the 7-phase workflow system
- Handles configuration and state management
- Coordinates phase transitions and checkpoints

### 2. Workflow Manager (`workflow_phases.py`)

- Manages workflow phases and transitions
- Tracks phase completion and state
- Handles phase skipping based on configuration
- Provides resumption capabilities

### 3. Query Expander (`query_expander.py`)

- Generates multiple search query variations
- Uses LLM to create comprehensive query coverage
- Handles query expansion metadata
- Configurable expansion limits

### 4. URL Reviewer (`url_reviewer.py`)

- Interactive URL review and curation interface
- Allows human oversight of discovered URLs
- Supports batch operations and filtering
- Optional phase that can be skipped

### 5. Deep Crawler (`deep_crawler.py`)

- Intelligent multi-level web crawling
- Follows links to specified depth
- Respects domain limits and external link policies
- Integrates with URL filtering systems

### 6. LLM Interface (`llm_interface.py`)

- Abstraction layer for different LLM providers
- Supports Claude, Gemini, and CLI tools
- Manages API calls and response parsing

### 7. Scraper (`scraper.py`)

- Concurrent web scraping with rate limiting
- Integrates with html2md for content conversion
- Handles failures gracefully with retry logic

### 8. Analysis Generator (`analysis_generator.py`)

- Generates AI-powered insights and summaries
- Template-based analysis approaches
- Content relevance scoring and key points extraction
- Configurable analysis types

### 9. Bundle Creator (`bundle_creator.py`)

- Organizes scraped content into structured bundles
- Creates table of contents and summaries
- Formats output in clean Markdown
- Integrates phase-specific metadata

## Data Flow

### 7-Phase Workflow

```
User Query
    ↓
[1] INITIALIZATION
    ↓ (Configuration & Setup)
Workflow Manager
    ↓
[2] QUERY_EXPANSION (Optional)
    ↓ (Query Expander)
Expanded Queries
    ↓
[3] URL_COLLECTION
    ↓ (LLM Search)
Discovered URLs
    ↓
[4] URL_REVIEW (Optional)
    ↓ (URL Reviewer)
Curated URLs
    ↓
[5] CRAWLING
    ↓ (Deep Crawler + Scraper)
Raw Content
    ↓
[6] BUNDLING
    ↓ (Bundle Creator)
Research Bundle
    ↓
[7] ANALYSIS (Optional)
    ↓ (Analysis Generator)
Final Research Package
```

### Phase Dependencies

- INITIALIZATION → Required for all workflows
- QUERY_EXPANSION → Can be skipped if `expand_queries: false`
- URL_COLLECTION → Always required
- URL_REVIEW → Can be skipped if `skip_review: true`
- CRAWLING → Always required
- BUNDLING → Always required
- ANALYSIS → Can be skipped if `generate_analysis: false`

## Configuration System

The research tool uses a hierarchical configuration system:

1. **Default Config**: Built-in defaults
2. **User Config**: ~/.m1f.config.yml
3. **Project Config**: ./.m1f.config.yml
4. **CLI Arguments**: Command-line overrides

### Workflow Configuration

Workflow behavior is controlled by the `WorkflowConfig` class:

```python
@dataclass
class WorkflowConfig:
    expand_queries: bool = True        # Generate search query variations
    max_queries: int = 5              # Maximum expanded queries
    skip_review: bool = False         # Skip URL review interface
    crawl_depth: int = 0              # How many levels deep to crawl
    max_pages_per_site: int = 10      # Maximum pages per domain
    follow_external: bool = False     # Follow external links
    generate_analysis: bool = True    # Generate AI analysis
    analysis_type: str = "summary"    # Type of analysis to generate
```

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
5. **Workflow Phases**: Add custom phases to the workflow
6. **Crawling Strategies**: Implement domain-specific crawling logic
7. **URL Filters**: Create custom URL filtering rules
8. **Analysis Generators**: Add specialized analysis types

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
