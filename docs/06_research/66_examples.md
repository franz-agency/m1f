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

### Query Control Examples

```bash
# No query expansion - use only the original query
m1f-research "python type hints" --max-queries 1

# More query variations for comprehensive research
m1f-research "distributed systems" --max-queries 10

# Provide specific query variations
m1f-research "react hooks" --custom-queries \
  "react hooks best practices 2025" \
  "useState vs useReducer" \
  "custom hooks patterns" \
  "react hooks testing strategies"

# Interactive query input - enter variations manually
m1f-research "database optimization" --interactive-queries
# This will prompt:
# Original query: database optimization
# Enter custom query variations (one per line, empty line to finish):
# 1> database index optimization
# 2> query performance tuning
# 3> database normalization best practices
# 4> 

# Combine with other options
m1f-research "microservices" --custom-queries \
  "microservices architecture patterns" \
  "microservices vs monoliths 2025" \
  --urls 40 --scrape 20 --template technical
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

## Workflow Examples

### Query Expansion Workflow

```bash
# Basic query expansion
m1f-research "python web frameworks" --expand-queries

# Advanced query expansion with more variations
m1f-research "machine learning model deployment" --expand-queries --max-queries 8

# Query expansion with specific focus
m1f-research "kubernetes best practices" --expand-queries --template technical
```

### URL Review Workflow

```bash
# Enable URL review for manual curation
m1f-research "AI ethics research" --skip-review false

# Automated workflow (skip review)
m1f-research "python libraries 2024" --skip-review

# Review with expanded queries
m1f-research "microservices patterns" --expand-queries --skip-review false
```

### Deep Crawling Workflow

```bash
# Single-level crawling
m1f-research "vue.js documentation" --crawl-depth 1

# Multi-level crawling with site limits
m1f-research "react ecosystem" --crawl-depth 2 --max-pages-per-site 15

# External link following
m1f-research "web development trends" --crawl-depth 1 --follow-external

# Comprehensive crawling
m1f-research "database optimization" --crawl-depth 3 --max-pages-per-site 25 --follow-external
```

### Analysis Generation Workflow

```bash
# Summary analysis (default)
m1f-research "golang best practices" --analysis-type summary

# Detailed analysis
m1f-research "system design principles" --analysis-type detailed

# Skip analysis for raw content
m1f-research "API documentation" --no-analysis
```

### Complete Workflow Examples

```bash
# Full-featured research with all phases
m1f-research "distributed systems patterns" \
  --expand-queries --max-queries 6 \
  --crawl-depth 2 --follow-external \
  --max-pages-per-site 20 \
  --analysis-type detailed \
  --skip-review false

# Minimal automated workflow
m1f-research "quick reference guide" \
  --no-expand-queries \
  --skip-review \
  --crawl-depth 0 \
  --analysis-type summary

# Academic research workflow
m1f-research "quantum computing research 2024" \
  --template academic \
  --expand-queries --max-queries 10 \
  --crawl-depth 1 \
  --analysis-type detailed \
  --skip-review false
```

## Python Script Examples

### Basic Research Script

```python
#!/usr/bin/env python3
import asyncio
from tools.research import ResearchOrchestrator
from tools.shared.colors import info, success

async def main():
    orchestrator = ResearchOrchestrator()

    results = await orchestrator.research(
        query="GraphQL best practices",
        url_count=30,
        scrape_count=15
    )

    success(f"Research complete!")
    info(f"Bundle saved to: {results.bundle_path}")
    info(f"Total sources: {len(results.content)}")
    info(f"Average relevance: {sum(a.relevance for a in results.analyses) / len(results.analyses):.1f}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Custom Template Script with Workflow

```python
#!/usr/bin/env python3
import asyncio
from tools.research import ResearchOrchestrator, ResearchTemplate, ResearchConfig, WorkflowConfig
from tools.shared.colors import info

# Define custom template with workflow configuration
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

# Configure workflow for security research
workflow_config = WorkflowConfig(
    expand_queries=True,
    max_queries=8,
    skip_review=False,  # Review URLs for security relevance
    crawl_depth=2,
    max_pages_per_site=15,
    follow_external=True,
    generate_analysis=True,
    analysis_type="detailed"
)

async def main():
    config = ResearchConfig(
        query="API security",
        url_count=40,
        scrape_count=20,
        template="security",
        workflow=workflow_config
    )
    
    orchestrator = ResearchOrchestrator(config=config)
    orchestrator.register_template(security_template)

    results = await orchestrator.research_with_workflow()

    # Print security-specific summary
    info("\n=== Security Research Summary ===")
    info(f"Workflow completed with {len(results.content)} sources")
    info(f"Analysis type: {workflow_config.analysis_type}")
    
    for analysis in sorted(results.analyses, key=lambda a: a.relevance, reverse=True)[:5]:
        info(f"\n{analysis.url}")
        info(f"Relevance: {analysis.relevance}/10")
        info("Key Security Points:")
        for point in analysis.key_points[:3]:
            info(f"  - {point}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Batch Research Script

```python
#!/usr/bin/env python3
import asyncio
from pathlib import Path
from tools.research import ResearchOrchestrator
from tools.shared.colors import info

async def research_topic(orchestrator, topic, output_dir):
    """Research a single topic"""
    info(f"\nResearching: {topic}")

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

### Advanced Workflow Pipeline Script

```python
#!/usr/bin/env python3
import asyncio
import json
from datetime import datetime
from tools.research import ResearchOrchestrator, ResearchConfig, WorkflowConfig
from tools.research.workflow_phases import WorkflowPhase
from tools.m1f import bundle_files
from tools.shared.colors import info, success, warning

async def research_with_workflow(query, workflow_config):
    """Research a topic using the 7-phase workflow"""

    info(f"Starting workflow research for: {query}")
    
    config = ResearchConfig(
        query=query,
        url_count=30,
        scrape_count=15,
        workflow=workflow_config
    )
    
    orchestrator = ResearchOrchestrator(config=config)
    
    # Monitor workflow phases
    phase_results = {}
    
    try:
        # Execute workflow with phase tracking
        research_results = await orchestrator.research_with_workflow()
        
        # Get workflow summary
        if hasattr(orchestrator, 'workflow_manager'):
            phase_summary = orchestrator.workflow_manager.get_phase_summary(research_results.job_id)
            phase_results = phase_summary
        
        info(f"Workflow completed successfully")
        info(f"Completed phases: {phase_results.get('completed_phases', [])}")
        
        return research_results, phase_results
        
    except Exception as e:
        warning(f"Workflow failed: {e}")
        return None, {"error": str(e)}

async def comprehensive_research_pipeline():
    """Run comprehensive research with different workflow configurations"""
    
    research_configs = [
        {
            "query": "microservices architecture patterns",
            "workflow": WorkflowConfig(
                expand_queries=True,
                max_queries=6,
                skip_review=False,
                crawl_depth=2,
                follow_external=True,
                generate_analysis=True,
                analysis_type="detailed"
            )
        },
        {
            "query": "python async programming",
            "workflow": WorkflowConfig(
                expand_queries=True,
                max_queries=4,
                skip_review=True,  # Automated
                crawl_depth=1,
                follow_external=False,
                generate_analysis=True,
                analysis_type="summary"
            )
        },
        {
            "query": "quick docker reference",
            "workflow": WorkflowConfig(
                expand_queries=False,  # Minimal
                skip_review=True,
                crawl_depth=0,
                generate_analysis=False
            )
        }
    ]
    
    results = []
    
    for config in research_configs:
        info(f"\n{'='*50}")
        info(f"Processing: {config['query']}")
        info(f"Workflow type: {'Comprehensive' if config['workflow'].expand_queries else 'Minimal'}")
        
        research_result, phase_result = await research_with_workflow(
            config['query'], 
            config['workflow']
        )
        
        if research_result:
            # Create detailed report
            report = {
                "query": config['query'],
                "timestamp": datetime.now().isoformat(),
                "workflow_config": {
                    "expand_queries": config['workflow'].expand_queries,
                    "crawl_depth": config['workflow'].crawl_depth,
                    "analysis_type": config['workflow'].analysis_type,
                },
                "phase_results": phase_result,
                "research_stats": {
                    "urls_found": len(research_result.urls) if research_result.urls else 0,
                    "urls_scraped": len(research_result.content) if research_result.content else 0,
                },
                "bundle_path": str(research_result.bundle_path) if research_result.bundle_path else None
            }
            
            results.append(report)
            success(f"Completed: {config['query']}")
        else:
            warning(f"Failed: {config['query']}")
    
    # Generate summary report
    summary_path = "./pipeline_summary.json"
    with open(summary_path, "w") as f:
        json.dump({
            "pipeline_run": datetime.now().isoformat(),
            "total_queries": len(research_configs),
            "successful": len(results),
            "results": results
        }, f, indent=2)
    
    info(f"\n=== Pipeline Summary ===")
    info(f"Total queries processed: {len(research_configs)}")
    info(f"Successful completions: {len(results)}")
    info(f"Summary saved to: {summary_path}")
    
    for result in results:
        info(f"\n{result['query']}:")
        info(f"  - Workflow: {result['workflow_config']}")
        info(f"  - Completed phases: {len(result['phase_results'].get('completed_phases', []))}")
        info(f"  - URLs processed: {result['research_stats']['urls_scraped']}")

if __name__ == "__main__":
    asyncio.run(comprehensive_research_pipeline())
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
m1f-research "topic" --analysis-type detailed && \
m1f ./m1f/research/topic-*/ -o analysis.txt && \
cat analysis.txt | llm "Summarize the key findings"

# Multi-stage workflow research
m1f-research "react hooks patterns" --expand-queries --crawl-depth 1 && \
m1f-research --resume [job-id] --analysis-type detailed && \
m1f ./research-data/*/[job-id]/ -o react-hooks-complete.txt
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
