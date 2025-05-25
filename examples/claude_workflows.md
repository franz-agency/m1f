# Claude Code Workflow Examples

This document provides example workflows using Claude Code with the m1f tools.

## Setup

First, ensure Claude Code is installed:

```bash
npm install -g @anthropic-ai/claude-code
```

## Example Workflows

### 1. Basic File Bundling

**Natural language prompt:**

```bash
python tools/claude_orchestrator.py "Bundle all Python files in the tools directory into a single m1f file with detailed separators"
```

**What Claude will do:**

- Identify all .py files in tools/
- Create an m1f bundle with detailed separators
- Include metadata for each file

### 2. HTML Documentation Conversion

**Complete workflow:**

```bash
python tools/claude_orchestrator.py "I have HTML documentation in ~/docs/html. Please analyze it, create a preprocessing config, convert to Markdown, and create topic-based m1f bundles"
```

**What Claude will do:**

1. Run analyze_html.py on sample files
2. Create a preprocessing configuration
3. Convert all HTML to Markdown
4. Organize by topics
5. Create separate m1f bundles

### 3. WordPress Site Export

**Natural language prompt:**

```bash
python tools/claude_orchestrator.py "Export my WordPress site at example.com to Markdown, organize by categories, and create m1f bundles for each category"
```

### 4. Project Analysis

**Interactive mode:**

```bash
python tools/claude_orchestrator.py -i
> Analyze this Python project and suggest optimal bundling strategies
> Create documentation bundles separating API docs from tutorials
> Generate a preprocessing config for the HTML files in docs/
```

### 5. Complex Documentation Processing

**Technical documentation example:**

```bash
python tools/claude_orchestrator.py "Process technical documentation:
1. Analyze HTML structure in ~/docs/technical-manual/
2. Create preprocessing to remove navigation, scripts, and metadata
3. Convert to clean Markdown preserving structure
4. Create these m1f bundles: concepts, templates, features, reference, installation
5. Each bundle should be under 5MB"
```

## Direct Claude Code Usage

You can also use Claude Code directly:

```bash
# Start Claude in your project
cd /path/to/m1f
claude

# In Claude's REPL:
> Bundle all test files into a single m1f for review
> Convert the HTML docs to Markdown with proper preprocessing
> Show me how to use s1f to extract specific files
```

## Combining Tools

**Pipeline example:**

```bash
# Using shell pipes with Claude
find . -name "*.html" | \
claude -p "Create a preprocessing config for these HTML files" | \
python tools/html2md/analyze_html.py --output preprocessing.json

# Then use the config
python tools/claude_orchestrator.py "Convert HTML files using preprocessing.json config"
```

## Tips

1. **Be specific** about file locations and desired output
2. **Use dry-run** mode first for complex operations
3. **Check generated commands** before execution
4. **Leverage Claude's understanding** of project structure

## Troubleshooting

If Claude Code is not available:

- The orchestrator will show an error message
- You can still use all tools directly
- See individual tool documentation for usage

## Advanced Usage

### Custom Workflows

Create a custom workflow script:

```python
#!/usr/bin/env python3
from tools.claude_orchestrator import ClaudeOrchestrator

orchestrator = ClaudeOrchestrator()

# Define complex workflow
workflow = """
1. Find all Markdown files modified in the last week
2. Create an m1f bundle with changelog format
3. If bundle is over 1MB, split into weekly chunks
4. Generate a summary report
"""

plan = orchestrator.analyze_request(workflow)
orchestrator.execute_plan(plan)
```

### Integration with CI/CD

```yaml
# .github/workflows/docs.yml
- name: Process Documentation
  run: |
    npm install -g @anthropic-ai/claude-code
    python tools/claude_orchestrator.py "Update documentation bundles from changed files"
```
