# m1f Documentation

This directory contains detailed documentation for the m1f project.

## Contents

- [m1f (Make One File)](./m1f.md) - Documentation for the main tool that
  combines multiple files into a single file
- [s1f (Split One File)](./s1f.md) - Documentation for the tool that extracts
  individual files from a combined file
- [token_counter](./token_counter.md) - Documentation for the token estimation
  tool

## Quick Navigation

### Common Workflows

- **First-time setup**: Install requirements using
  `pip install -r requirements.txt`
- **Basic file combination**: Use
  `python tools/m1f.py -s ./your_project -o ./combined.txt`
- **File extraction**: Use
  `python tools/s1f.py -i ./combined.txt -d ./extracted_files`
- **Check token count**: Use `python tools/token_counter.py ./combined.txt`

### Key Concepts

- **Separator Styles**: Different formats for separating files in the combined
  output ([details](./m1f.md#separator-styles))
- **File Filtering**: Include/exclude specific files using patterns
  ([details](./m1f.md#command-line-options))
- **Security**: Scan for secrets before combining files
  ([details](./m1f.md#security-check))

## Project Overview

m1f and s1f are specialized utilities designed to help you work more efficiently
with Large Language Models (LLMs) by managing context. These tools solve a core
challenge when working with AI assistants: providing comprehensive context
efficiently.

The toolset allows you to:

- Combine multiple project files into a single reference file (perfect for
  providing context to LLMs)
- Extract individual files from a combined file (restore original files with
  their structure intact)
- Estimate token usage for LLM context planning
- Optimize your use of AI context windows by selecting only the most relevant
  files
