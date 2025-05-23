


M1F - Make One File Documentation



# M1F - Make One File

A powerful tool for combining multiple files into a single, well-formatted document

[Get Started](#quick-start)
[Download](#download)



## Overview

M1F (Make One File) is a sophisticated file aggregation tool designed to combine multiple source files into a single, well-formatted output file. It's particularly useful for creating comprehensive documentation, preparing code for Large Language Model (LLM) contexts, and archiving projects.

**Key Benefits:**

- Combine entire codebases into a single file for LLM analysis
- Create comprehensive documentation from multiple sources
- Archive projects with preserved structure and formatting
- Generate readable outputs with customizable separators


## Core Features

### 🔍 Smart File Discovery

Recursively scans directories with powerful glob pattern support

`*.py, **/*.js, src/**/*.{ts,tsx}`

### 🎨 Multiple Output Formats

XML, Markdown, and Plain text separators with syntax highlighting

`--separator-style XML|Markdown|Plain`

### 🚀 Performance Optimized

Parallel processing and streaming for large codebases

`--parallel --max-workers 8`

### 🔧 Highly Configurable

Extensive filtering options and customizable output

`--config config.yaml`



## Quick Start

Get up and running with M1F in seconds:

```
# Basic usage - combine all Python files
$ python tools/m1f.py --source-directory ./src --output-file combined.txt --include-patterns "*.py"

# Advanced usage with multiple patterns
$ python tools/m1f.py \
    --source-directory ./project \
    --output-file project.m1f.md \
    --include-patterns "*.py" "*.js" "*.md" \
    --exclude-patterns "*test*" "*__pycache__*" \
    --separator-style Markdown \
    --parallel
```


## Detailed Usage

### Command Line Options

| Option | Description | Default | Example |
| --- | --- | --- | --- |
| `--source-directory` | Directory to scan for files | Current directory | `./src` |
| `--output-file` | Output file path | combined\_output.txt | `output.m1f.md` |
| `--include-patterns` | Glob patterns to include | None | `"*.py" "*.js"` |
| `--exclude-patterns` | Glob patterns to exclude | None | `"*test*" "*.log"` |
| `--separator-style` | Output format style | XML | `Markdown` |
| `--parallel` | Enable parallel processing | False | `--parallel` |
| `--max-file-size` | Maximum file size in MB | 10 | `--max-file-size 50` |

### Configuration File

For complex setups, use a YAML configuration file:

```
# m1f-config.yaml
source_directory: ./src
output_file: ./output/combined.m1f.md
separator_style: Markdown

include_patterns:
  - "**/*.py"
  - "**/*.js"
  - "**/*.ts"
  - "**/*.md"
  - "**/Dockerfile"

exclude_patterns:
  - "**/__pycache__/**"
  - "**/node_modules/**"
  - "**/.git/**"
  - "**/*.test.js"
  - "**/*.spec.ts"

options:
  parallel: true
  max_workers: 4
  max_file_size: 20
  respect_gitignore: true
  include_hidden: false
  
metadata:
  include_timestamp: true
  include_hash: true
  hash_algorithm: sha256
```

## Real-World Examples

### Example 1: Preparing Code for LLM Analysis

Combine an entire Python project for ChatGPT or Claude analysis:

```
python tools/m1f.py \
    --source-directory ./my-python-project \
    --output-file project-for-llm.txt \
    --include-patterns "*.py" "*.md" "requirements.txt" "pyproject.toml" \
    --exclude-patterns "*__pycache__*" "*.pyc" ".git/*" \
    --separator-style XML \
    --metadata-include-timestamp \
    --metadata-include-hash
```
View Output Sample
```
<file path="src/main.py" hash="a1b2c3..." timestamp="2024-01-15T10:30:00">
#!/usr/bin/env python3
"""Main application entry point."""

import sys
from app import Application

def main():
    app = Application()
    return app.run(sys.argv[1:])

if __name__ == "__main__":
    sys.exit(main())
</file>

<file path="src/app.py" hash="d4e5f6..." timestamp="2024-01-15T10:25:00">
"""Application core logic."""

class Application:
    def __init__(self):
        self.config = self.load_config()
    
    def run(self, args):
        # Implementation details...
        pass
</file>
```


### Example 2: Creating Documentation Archive

Combine all documentation files with preserved structure:

```
python tools/m1f.py \
    --source-directory ./docs \
    --output-file documentation.m1f.md \
    --include-patterns "**/*.md" "**/*.rst" "**/*.txt" \
    --separator-style Markdown \
    --preserve-directory-structure \
    --add-table-of-contents
```

### Example 3: Multi-Language Project

Combine a full-stack application with multiple languages:

```
python tools/m1f.py \
    --config fullstack-config.yaml
```

Where `fullstack-config.yaml` contains:

```
source_directory: ./fullstack-app
output_file: ./fullstack-combined.m1f.md
separator_style: Markdown

include_patterns:
  # Backend
  - "backend/**/*.py"
  - "backend/**/*.sql"
  - "backend/**/Dockerfile"
  
  # Frontend
  - "frontend/**/*.js"
  - "frontend/**/*.jsx"
  - "frontend/**/*.ts"
  - "frontend/**/*.tsx"
  - "frontend/**/*.css"
  - "frontend/**/*.scss"
  
  # Configuration
  - "**/*.json"
  - "**/*.yaml"
  - "**/*.yml"
  - "**/.*rc"
  
  # Documentation
  - "**/*.md"
  - "**/README*"

exclude_patterns:
  - "**/node_modules/**"
  - "**/__pycache__/**"
  - "**/dist/**"
  - "**/build/**"
  - "**/.git/**"
  - "**/*.min.js"
  - "**/*.map"
```


## Advanced Features

### Parallel Processing

For large codebases, enable parallel processing:

```
# Parallel processing configuration
from m1f import M1F

m1f = M1F(
    parallel=True,
    max_workers=8,  # Number of CPU cores
    chunk_size=100  # Files per chunk
)

# Process large directory
m1f.process_directory(
    source_dir="/path/to/large/project",
    output_file="large_project.m1f.txt"
)
```
### Custom Separators

Define your own separator format:

```
# Custom separator function
def custom_separator(file_path, file_info):
    return f"""
╔══════════════════════════════════════════════════════════════╗
║ File: {file_path}
║ Size: {file_info['size']} bytes
║ Modified: {file_info['modified']}
╚══════════════════════════════════════════════════════════════╝
"""

m1f = M1F(separator_function=custom_separator)
```
### Streaming Mode

For extremely large outputs, use streaming mode:

```
# Stream output to avoid memory issues
python tools/m1f.py \
    --source-directory ./massive-project \
    --output-file output.m1f.txt \
    --streaming-mode \
    --buffer-size 8192
```

## Integration with Other Tools

### 🔄 With html2md

Convert HTML documentation to Markdown, then combine:

```
# First convert HTML to MD
python tools/html2md.py --source-dir ./html-docs --destination-dir ./md-docs

# Then combine with m1f
python tools/m1f.py --source-directory ./md-docs --output-file docs.m1f.md
```

### 🤖 With LLMs

Prepare code for AI analysis:

```
# Create context for LLM
import subprocess

# Run m1f
subprocess.run([
    "python", "tools/m1f.py",
    "--source-directory", "./src",
    "--output-file", "context.txt",
    "--max-file-size", "5"  # Keep under token limits
])

# Now use with your LLM API
with open("context.txt", "r") as f:
    context = f.read()
    # Send to OpenAI, Anthropic, etc.
```



## Troubleshooting

Common Issues and Solutions
#### Issue: Output file too large

**Solution:** Use more restrictive patterns or increase max file size limit:

`--max-file-size 100 --exclude-patterns "*.log" "*.dat"`

#### Issue: Memory errors with large projects

**Solution:** Enable streaming mode:

`--streaming-mode --buffer-size 4096`

#### Issue: Encoding errors

**Solution:** Specify encoding or skip binary files:

`--encoding utf-8 --skip-binary-files`




### Navigation

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Examples](#examples)
- [Advanced](#advanced-features)
- [Integration](#integration)
- [Troubleshooting](#troubleshooting)

### Version Info

Current Version: **2.0.0**

Python: **3.9+**

### Related Tools

- [html2md](/page/html2md-documentation)
- [s1f](/page/s1f-documentation)




 

---

*Scraped from: http://localhost:8080/page/m1f-documentation*

*Scraped at: 2025-05-23 11:55:26*

*Source URL: http://localhost:8080/page/m1f-documentation*