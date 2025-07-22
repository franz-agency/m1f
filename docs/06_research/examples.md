# m1f-research Examples

## Command Line Examples

### Basic Research

```bash
# Simple research on a topic
m1f-research "python async programming"

# Research with more sources
m1f-research "kubernetes networking" --urls 40 --scrape 20

# Use a specific template
m1f-research "react performance optimization" --template technical
```

### Different Providers

```bash
# Use Gemini instead of Claude
m1f-research "machine learning basics" --provider gemini

# Use a CLI tool
m1f-research "rust ownership" --provider gemini-cli

# Specify a particular model
m1f-research "quantum computing" --provider claude --model claude-3-opus-20240229
```

### Output Control

```bash
# Custom output location
m1f-research "microservices patterns" --output ~/research/microservices

# Named bundle
m1f-research "docker best practices" --name docker-guide

# JSON output format
m1f-research "api design" --format json
```

### Processing Options

```bash
# Faster scraping with more concurrency
m1f-research "golang concurrency" --concurrent 10

# Slower, more respectful scraping
m1f-research "web scraping ethics" --concurrent 2 --timeout "2-5"

# Skip analysis for raw content
m1f-research "css grid layouts" --no-analysis

# Skip filtering to get all URLs
m1f-research "obscure programming languages" --no-filter
```

### Interactive Mode

```bash
# Start interactive research session
m1f-research --interactive

# In interactive mode:
# > Enter research query: microservices vs monoliths
# > Number of URLs to find [20]: 30
# > Number to scrape [10]: 15
# > Template [general]: technical
# > Start research? [Y/n]: y
```

## Configuration File Examples

### Basic Configuration

```yaml
# .m1f.config.yml
research:
  llm:
    provider: claude
    temperature: 0.7

  defaults:
    url_count: 30
    scrape_count: 15

  output:
    directory: ./my-research
```

### Advanced Configuration

```yaml
# research-config.yml
research:
  llm:
    provider: gemini
    model: gemini-pro
    temperature: 0.8
    max_tokens: 4000

  defaults:
    url_count: 50
    scrape_count: 25

  scraping:
    timeout_range: "2-4"
    max_concurrent: 8
    retry_attempts: 3
    user_agent: "m1f-research/1.0"

  analysis:
    relevance_threshold: 7.5
    min_content_length: 200
    prefer_code_examples: true
    extract_metadata: true

  output:
    directory: ./research-output
    create_summary: true
    create_index: true
    include_metadata: true

  filters:
    allowed_domains:
      - "*.github.io"
      - "docs.*.com"
      - "*.readthedocs.io"
    blocked_domains:
      - "spam-site.com"
    url_patterns:
      - "*/api/*"
      - "*/reference/*"
```

### Template-Specific Config

```yaml
# technical-research.yml
research:
  templates:
    technical:
      description: "Deep technical documentation"
      url_count: 40
      scrape_count: 20

      search:
        focus: "implementation, architecture, code examples"
        prefer_sources:
          - "GitHub"
          - "official docs"
          - "technical blogs"

      analysis:
        relevance_prompt: |
          Rate based on:
          - Code examples
          - Technical depth
          - Practical applicability

        key_points_prompt: |
          Extract:
          - Core concepts
          - Implementation details
          - Best practices
          - Common pitfalls

      output:
        group_by: "subtopic"
        include_code_stats: true
```

## Python Script Examples

### Basic Research Script

```python
#!/usr/bin/env python3
import asyncio
from tools.research import ResearchOrchestrator

async def main():
    orchestrator = ResearchOrchestrator()

    results = await orchestrator.research(
        query="GraphQL best practices",
        url_count=30,
        scrape_count=15
    )

    print(f"Research complete!")
    print(f"Bundle saved to: {results.bundle_path}")
    print(f"Total sources: {len(results.content)}")
    print(f"Average relevance: {sum(a.relevance for a in results.analyses) / len(results.analyses):.1f}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Custom Template Script

```python
#!/usr/bin/env python3
import asyncio
from tools.research import ResearchOrchestrator, ResearchTemplate

# Define custom template
security_template = ResearchTemplate(
    name="security",
    description="Security-focused research",
    search_prompt="""
    Find authoritative sources about {query} focusing on:
    - Security vulnerabilities
    - Best practices for security
    - OWASP guidelines
    - Security tools and scanning
    """,
    analysis_focus="security implications",
    relevance_criteria="security relevance and actionable advice"
)

async def main():
    orchestrator = ResearchOrchestrator()

    results = await orchestrator.research(
        query="API security",
        template=security_template,
        url_count=40,
        scrape_count=20
    )

    # Print security-specific summary
    print("\n=== Security Research Summary ===")
    for analysis in sorted(results.analyses, key=lambda a: a.relevance, reverse=True)[:5]:
        print(f"\n{analysis.url}")
        print(f"Relevance: {analysis.relevance}/10")
        print("Key Security Points:")
        for point in analysis.key_points[:3]:
            print(f"  - {point}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Batch Research Script

```python
#!/usr/bin/env python3
import asyncio
from pathlib import Path
from tools.research import ResearchOrchestrator

async def research_topic(orchestrator, topic, output_dir):
    """Research a single topic"""
    print(f"\nResearching: {topic}")

    results = await orchestrator.research(
        query=topic,
        url_count=20,
        scrape_count=10,
        output_dir=output_dir / topic.replace(" ", "_")
    )

    return topic, results

async def main():
    topics = [
        "microservices architecture",
        "event-driven design",
        "domain-driven design",
        "CQRS pattern",
        "saga pattern"
    ]

    orchestrator = ResearchOrchestrator()
    output_dir = Path("./architecture-research")
    output_dir.mkdir(exist_ok=True)

    # Research all topics
    tasks = [research_topic(orchestrator, topic, output_dir) for topic in topics]
    results = await asyncio.gather(*tasks)

    # Create index
    with open(output_dir / "index.md", "w") as f:
        f.write("# Architecture Research\n\n")
        for topic, result in results:
            f.write(f"## {topic}\n")
            f.write(f"- Sources: {len(result.content)}\n")
            f.write(f"- Bundle: [{result.bundle_path.name}](./{result.bundle_path.relative_to(output_dir)})\n\n")

if __name__ == "__main__":
    asyncio.run(main())
```

### Research Pipeline Script

```python
#!/usr/bin/env python3
import asyncio
import json
from datetime import datetime
from tools.research import ResearchOrchestrator
from tools.m1f import bundle_files

async def research_and_bundle(query):
    """Research a topic and create an m1f bundle"""

    # Phase 1: Research
    print(f"Phase 1: Researching {query}")
    orchestrator = ResearchOrchestrator()

    research_results = await orchestrator.research(
        query=query,
        url_count=30,
        scrape_count=15,
        output_dir=f"./pipeline/{query.replace(' ', '_')}"
    )

    # Phase 2: Bundle with m1f
    print(f"Phase 2: Creating m1f bundle")
    bundle_path = bundle_files(
        paths=[str(research_results.bundle_path.parent)],
        output=f"./pipeline/{query.replace(' ', '_')}_complete.txt",
        preset="docs-bundle"
    )

    # Phase 3: Create report
    print(f"Phase 3: Generating report")
    report = {
        "query": query,
        "timestamp": datetime.now().isoformat(),
        "research": {
            "urls_found": len(research_results.urls),
            "urls_scraped": len(research_results.content),
            "avg_relevance": sum(a.relevance for a in research_results.analyses) / len(research_results.analyses)
        },
        "bundle": {
            "path": str(bundle_path),
            "size": bundle_path.stat().st_size
        }
    }

    report_path = f"./pipeline/{query.replace(' ', '_')}_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    return report

async def main():
    queries = [
        "react state management",
        "vue composition api",
        "angular signals"
    ]

    # Process all queries
    results = []
    for query in queries:
        result = await research_and_bundle(query)
        results.append(result)
        print(f"Completed: {query}\n")

    # Summary
    print("\n=== Pipeline Summary ===")
    for result in results:
        print(f"\n{result['query']}:")
        print(f"  - URLs scraped: {result['research']['urls_scraped']}")
        print(f"  - Avg relevance: {result['research']['avg_relevance']:.1f}")
        print(f"  - Bundle size: {result['bundle']['size'] / 1024:.1f} KB")

if __name__ == "__main__":
    asyncio.run(main())
```

## Real-World Use Cases

### 1. Technology Evaluation

```bash
# Research multiple competing technologies
m1f-research "kafka vs rabbitmq vs redis streams" --urls 50 --scrape 30 --template technical

# Deep dive into one technology
m1f-research "apache kafka internals architecture" --urls 40 --scrape 25
```

### 2. Learning New Topics

```bash
# Beginner-friendly research
m1f-research "python for beginners" --template tutorial

# Advanced topics with academic sources
m1f-research "distributed consensus algorithms" --template academic
```

### 3. Problem Solving

```bash
# Debug specific issues
m1f-research "kubernetes pod stuck terminating" --urls 30

# Find best practices
m1f-research "postgresql performance tuning large tables" --template technical
```

### 4. Documentation Collection

```bash
# Gather API documentation
m1f-research "stripe api payment intents" --template reference

# Collect migration guides
m1f-research "migrate django 3 to 4" --urls 40
```

### 5. Security Research

```bash
# Security audit preparation
m1f-research "OWASP top 10 2023 examples" --urls 50 --scrape 30

# Vulnerability research
m1f-research "log4j vulnerability explanation CVE-2021-44228"
```

## Tips and Tricks

### 1. Optimize for Quality

```bash
# More URLs, selective scraping
m1f-research "complex topic" --urls 60 --scrape 20

# This finds many options but only scrapes the best
```

### 2. Domain-Specific Research

```bash
# Create custom config for specific domains
cat > medical-research.yml << EOF
research:
  filters:
    allowed_domains:
      - "*.nih.gov"
      - "pubmed.ncbi.nlm.nih.gov"
      - "*.nature.com"
EOF

m1f-research "covid vaccine efficacy" --config medical-research.yml
```

### 3. Combine with Other Tools

```bash
# Research → m1f bundle → AI analysis
m1f-research "topic" && \
m1f ./m1f/research/topic-*/ -o analysis.txt && \
cat analysis.txt | llm "Summarize the key findings"
```

### 4. Scheduled Research

```bash
# Daily research updates (cron job)
0 9 * * * /usr/local/bin/m1f-research "AI news today" --name "ai-news-$(date +%Y%m%d)"
```

### 5. Research Archive

```bash
# Organize research by date
m1f-research "topic" --output "./research/$(date +%Y)/$(date +%m)/$(date +%d)/"
```
