# m1f-research API Reference

## Command Line Interface

### Basic Usage

```bash
m1f-research [OPTIONS] <query>
```

### Options

#### Search Options

- `--urls <count>` - Number of URLs to find (default: 20)
- `--scrape <count>` - Number of URLs to scrape (default: 10)
- `--template <name>` - Research template to use (default: general)

#### LLM Options

- `--provider <name>` - LLM provider (claude, gemini, cli)
- `--model <name>` - Specific model to use
- `--temperature <float>` - LLM temperature (0.0-1.0)

#### Output Options

- `--output <dir>` - Output directory (default: ./m1f/research)
- `--name <name>` - Bundle name (default: auto-generated)
- `--format <format>` - Output format (markdown, json)

#### Processing Options

- `--concurrent <count>` - Max concurrent scrapes (default: 5)
- `--timeout <range>` - Timeout range in seconds (e.g., "1-3")
- `--no-filter` - Disable URL filtering
- `--no-analysis` - Skip content analysis
- `--no-summary` - Skip summary generation

#### Other Options

- `--config <file>` - Custom config file
- `--interactive` - Interactive mode
- `--dry-run` - Preview without execution
- `--verbose` - Verbose output
- `--quiet` - Minimal output

## Python API

### Basic Usage

```python
from tools.research import ResearchOrchestrator

# Create orchestrator
orchestrator = ResearchOrchestrator()

# Run research
results = await orchestrator.research(
    query="microservices best practices",
    url_count=30,
    scrape_count=15
)

# Access results
print(f"Found {len(results.urls)} URLs")
print(f"Scraped {len(results.content)} pages")
print(f"Bundle saved to: {results.bundle_path}")
```

### Configuration

```python
from tools.research import ResearchConfig

config = ResearchConfig(
    llm_provider="claude",
    model="claude-3-opus-20240229",
    temperature=0.7,
    url_count=30,
    scrape_count=15,
    output_dir="./research",
    concurrent_limit=5,
    timeout_range=(1, 3)
)

orchestrator = ResearchOrchestrator(config)
```

### Custom Templates

```python
from tools.research import ResearchTemplate

template = ResearchTemplate(
    name="custom",
    description="Custom research template",
    search_prompt="Find {query} focusing on...",
    analysis_focus="implementation details",
    relevance_criteria="practical examples"
)

results = await orchestrator.research(
    query="react hooks",
    template=template
)
```

### Providers

```python
from tools.research import ClaudeProvider, GeminiProvider

# Claude provider
claude = ClaudeProvider(
    api_key="your-api-key",
    model="claude-3-opus-20240229"
)

# Gemini provider
gemini = GeminiProvider(
    api_key="your-api-key",
    model="gemini-pro"
)

# Use custom provider
orchestrator = ResearchOrchestrator(
    config=config,
    llm_provider=claude
)
```

### Scraping

```python
from tools.research import Scraper

scraper = Scraper(
    concurrent_limit=5,
    timeout_range=(1, 3),
    retry_attempts=2
)

# Scrape single URL
content = await scraper.scrape_url("https://example.com")

# Scrape multiple URLs
urls = ["https://example1.com", "https://example2.com"]
results = await scraper.scrape_urls(urls)
```

### Analysis

```python
from tools.research import Analyzer

analyzer = Analyzer(llm_provider=claude)

# Analyze content
analysis = await analyzer.analyze_content(
    content="Article content...",
    query="microservices",
    template="technical"
)

print(f"Relevance: {analysis.relevance}/10")
print(f"Key points: {analysis.key_points}")
```

### Bundle Creation

```python
from tools.research import BundleCreator

creator = BundleCreator()

# Create bundle
bundle_path = await creator.create_bundle(
    query="microservices",
    scraped_content=results,
    analysis_results=analyses,
    output_dir="./research"
)
```

## Data Models

### ResearchResult

```python
@dataclass
class ResearchResult:
    query: str
    urls: List[str]
    content: List[ScrapedContent]
    analyses: List[ContentAnalysis]
    bundle_path: Path
    metadata: Dict[str, Any]
```

### ScrapedContent

```python
@dataclass
class ScrapedContent:
    url: str
    title: str
    content: str
    scraped_at: datetime
    success: bool
    error: Optional[str]
```

### ContentAnalysis

```python
@dataclass
class ContentAnalysis:
    url: str
    relevance: float
    key_points: List[str]
    summary: str
    metadata: Dict[str, Any]
```

## Error Handling

```python
from tools.research import ResearchError, ScrapingError, AnalysisError

try:
    results = await orchestrator.research("query")
except ResearchError as e:
    print(f"Research failed: {e}")
except ScrapingError as e:
    print(f"Scraping failed: {e}")
except AnalysisError as e:
    print(f"Analysis failed: {e}")
```

## Events and Callbacks

```python
# Progress callback
def on_progress(stage: str, current: int, total: int):
    print(f"{stage}: {current}/{total}")

# Error callback
def on_error(error: Exception, context: Dict):
    print(f"Error in {context['stage']}: {error}")

# Use callbacks
results = await orchestrator.research(
    query="microservices",
    on_progress=on_progress,
    on_error=on_error
)
```

## Advanced Usage

### Custom URL Filters

```python
def custom_filter(url: str) -> bool:
    # Only allow specific domains
    allowed = ["docs.python.org", "realpython.com"]
    return any(domain in url for domain in allowed)

orchestrator.add_url_filter(custom_filter)
```

### Content Processors

```python
def process_content(content: str) -> str:
    # Custom content processing
    return content.replace("old_term", "new_term")

orchestrator.add_content_processor(process_content)
```

### Result Transformers

```python
def transform_results(results: ResearchResult) -> Dict:
    # Custom result transformation
    return {
        "query": results.query,
        "sources": len(results.content),
        "top_relevance": max(a.relevance for a in results.analyses)
    }

transformed = transform_results(results)
```
