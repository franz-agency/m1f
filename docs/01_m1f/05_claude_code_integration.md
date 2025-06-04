# Claude Code Integration Guide

This guide explains how to integrate Claude Code as an optional AI assistant for
the m1f tools project.

## Overview

Claude Code can help automate complex workflows by understanding natural
language prompts and executing the appropriate tools with correct parameters.

## Installation

### Prerequisites

- Node.js installed on your system
- An Anthropic API key (get one at https://console.anthropic.com)

### Install Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

### Initial Setup

1. Start Claude Code:

   ```bash
   claude
   ```

2. Login with your API key:

   ```
   /login
   ```

3. Configure Claude Code for this project:
   ```bash
   cd /path/to/m1f
   claude config
   ```

## Project Configuration

Create `.claude/settings.json` in the project root:

```json
{
  "model": "claude-opus-4",
  "customInstructions": "You are helping with the m1f tools project. Key tools available: m1f.py (file bundler), s1f.py (file splitter), html2md (HTML to Markdown converter), wp_export_md.py (WordPress exporter).",
  "permissions": {
    "write": true,
    "execute": true
  }
}
```

## Using Claude Code with m1f Tools

### Basic Commands

1. **Bundle files into m1f**:

   ```bash
   claude -p "Bundle all Python files in the tools directory into a single m1f file"
   ```

2. **Convert HTML to Markdown**:

   ```bash
   claude -p "Convert all HTML files in ~/docs to Markdown with preprocessing"
   ```

3. **Analyze and preprocess HTML**:
   ```bash
   claude -p "Analyze the HTML files in the docs folder and create a preprocessing config"
   ```

### Advanced Workflows

1. **Complete documentation conversion workflow**:

   ```bash
   claude -p "I have scraped HTML documentation in ~/docs/html. Please:
   1. Analyze a few sample files to understand the structure
   2. Create a preprocessing configuration
   3. Convert all HTML to Markdown
   4. Create thematic m1f bundles (concepts, reference, installation, etc.)"
   ```

2. **Export WordPress site**:
   ```bash
   claude -p "Export my WordPress site at example.com to Markdown, organizing by categories"
   ```

## Programmatic Usage

### Using Claude Code in Scripts

```python
#!/usr/bin/env python3
import subprocess
import json

def claude_command(prompt):
    """Execute a Claude Code command and return the result."""
    result = subprocess.run(
        ['claude', '-p', prompt, '--output-format', 'json'],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)

# Example: Get optimal m1f parameters
response = claude_command(
    "What are the optimal m1f parameters for bundling a Python project with tests?"
)
print(response)
```

### Integration with m1f Tools

Create `tools/claude_orchestrator.py`:

```python
#!/usr/bin/env python3
"""Orchestrate m1f tools using Claude Code."""

import subprocess
import json
from pathlib import Path

class ClaudeOrchestrator:
    def __init__(self):
        self.tools = {
            'm1f': 'tools/m1f.py',
            's1f': 'tools/s1f.py',
            'html2md': 'tools/html2md',
            'wp_export': 'tools/wp_export_md.py'
        }

    def analyze_request(self, user_prompt):
        """Use Claude to analyze user request and determine actions."""
        analysis_prompt = f"""
        Analyze this request and return a JSON with:
        1. tool: which tool to use ({', '.join(self.tools.keys())})
        2. parameters: dict of parameters for the tool
        3. steps: list of steps to execute

        Request: {user_prompt}
        """

        result = subprocess.run(
            ['claude', '-p', analysis_prompt, '--output-format', 'json'],
            capture_output=True,
            text=True
        )
        return json.loads(result.stdout)

    def execute_workflow(self, user_prompt):
        """Execute a complete workflow based on user prompt."""
        plan = self.analyze_request(user_prompt)

        for step in plan['steps']:
            print(f"Executing: {step['description']}")
            # Execute the actual command
            subprocess.run(step['command'], shell=True)
```

## Best Practices

1. **Create project-specific instructions** in `.claude/settings.json`
2. **Use Claude for complex workflows** that require multiple steps
3. **Leverage Claude's understanding** of file patterns and project structure
4. **Combine with shell pipes** for powerful automation

## Example Workflows

### 1. Documentation Processing Pipeline

```bash
# Complete pipeline with Claude
claude -p "Process the scraped documentation in ~/scraped-docs:
1. Analyze HTML structure
2. Create preprocessing config
3. Convert to Markdown preserving structure
4. Create m1f bundles by topic
5. Generate a summary report"
```

### 2. Project Analysis

```bash
# Analyze project for bundling
claude -p "Analyze this Python project and suggest:
1. Which files should be bundled together
2. Optimal m1f parameters
3. Any files that should be excluded"
```

### 3. Automated Testing

```bash
# Run tests and fix issues
claude -p "Run the test suite, identify any failures, and fix them"
```

## Environment Variables

Set these in your shell profile for persistent configuration:

```bash
export ANTHROPIC_MODEL="claude-sonnet-4-20250514"
export CLAUDE_CODE_PROJECT_ROOT="/path/to/m1f"
```

## Troubleshooting

1. **Permission errors**: Ensure Claude Code has write permissions in settings
2. **Model selection**: Use Claude Opus 4 for the most complex analysis, Claude
   Sonnet 4 for balanced performance
3. **Rate limits**: Be mindful of API usage limits

## Security Considerations

1. **Never commit API keys** to version control
2. **Use `.claude/settings.local.json`** for personal settings
3. **Review Claude's actions** before executing in production

## Further Resources

- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)
- [m1f Tools Documentation](00_m1f.md)
- [html2md Documentation](../03_html2md/30_html2md.md)
