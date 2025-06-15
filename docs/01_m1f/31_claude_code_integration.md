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
  "customInstructions": "You are helping with the m1f tools project. Key tools available: m1f.py (file bundler), s1f.py (file splitter), mf1-html2md (HTML to Markdown converter), wp_export_md.py (WordPress exporter).",
  "permissions": {
    "write": true,
    "execute": true
  }
}
```

## m1f-claude Tool

### Quick Project Setup with --init

The `m1f-claude --init` command provides an intelligent way to set up m1f for your project:

```bash
# Initialize m1f configuration with basic bundles
m1f-claude --init

# With verbose output to see what's happening
m1f-claude --init --verbose
```

#### What --init Does:

1. **Project Analysis**
   - Runs m1f to create file and directory lists in `m1f/` directory
   - Creates `project_analysis_filelist.txt` and `project_analysis_dirlist.txt`
   - Respects .gitignore patterns and excludes m1f/ directory
   - Analyzes project type, languages, and structure

2. **Automatic Bundle Creation**
   - **complete.txt**: Full project bundle (excluding meta files)
   - **docs.txt**: All documentation files with 50+ supported extensions
   - Both bundles are created immediately without Claude Code

3. **Configuration File**
   - Creates `.m1f.config.yml` with complete and docs bundles configured
   - Includes all documentation extensions (.md, .txt, .rst, .adoc, etc.)
   - No global file size limits
   - Proper meta file exclusions (LICENSE*, CLAUDE.md, *.lock)

4. **Advanced Segmentation (Optional)**
   - If Claude Code is installed, offers to create topic-specific bundles
   - Analyzes project structure for components, API, styles, etc.
   - Adds these bundles to your existing configuration
   - Uses `--allowedTools Read,Write,Edit,MultiEdit` for file operations

#### Example Output:

```
🚀 Initializing m1f for your project...
==================================================
✅ Git repository detected: /home/user/my-project
✅ m1f documentation already available
⚠️  No m1f configuration found - will help you create one
✅ Claude Code is available

📊 Project Analysis
==============================
Analyzing project structure with m1f...
📄 Created file list: project_analysis_filelist.txt
📁 Created directory list: project_analysis_dirlist.txt
✅ Found 127 files in 59 directories
📁 Project Type: Next.js Application
💻 Languages: JavaScript (37 files), TypeScript (30 files)
📂 Code Dirs: src/app, src/components, src/lib

📦 Creating Initial Bundles
==============================
Creating complete project bundle...
✅ Created: m1f/complete.txt
Creating documentation bundle...
✅ Created: m1f/docs.txt

📝 Creating .m1f.config.yml with basic bundles...
✅ Configuration created with complete and docs bundles

🤖 Claude Code for Advanced Segmentation
──────────────────────────────────────────────────
Basic bundles created! Now Claude can help you create topic-specific bundles.

[Claude analyzes and adds topic-specific bundles]

✅ Advanced segmentation complete!
📝 Claude has analyzed your project and added topic-specific bundles.

🚀 Next steps:
• Your basic bundles are ready in m1f/
  - complete.txt: Full project bundle
  - docs.txt: All documentation files
• Run 'm1f-update' to regenerate bundles after config changes
• Use Claude to create topic-specific bundles as needed
```

#### Troubleshooting:

- **Use --verbose** to see the full prompt and command parameters
- **Check file permissions** if config isn't being modified
- **Ensure Claude Code is installed**: `npm install -g @anthropic-ai/claude-code`
- **Analysis files are kept** in m1f/ directory for reference

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
            'mf1-html2md': 'tools/mf1-html2md',
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
