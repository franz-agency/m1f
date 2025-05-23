# m1f Documentation

This directory contains detailed documentation for the m1f project.

## Contents

### Core Tools

- [m1f (Make One File)](./m1f.md) - Documentation for the main tool that
  combines multiple files into a single file
- [s1f (Split One File)](./s1f.md) - Documentation for the tool that extracts
  individual files from a combined file
- [token_counter](./token_counter.md) - Documentation for the token estimation
  tool

### HTML to Markdown Converter

- [html2md Overview](./html2md.md) - Comprehensive guide to the HTML to Markdown converter
- [html2md Guide](./html2md_guide.md) - Detailed usage guide with examples
- [html2md Test Suite](./html2md_test_suite.md) - Documentation for the comprehensive test suite

## Quick Navigation

### Common Workflows

- **First-time setup**: Install requirements using
  `pip install -r requirements.txt`
- **Basic file combination**: Use
  `python tools/m1f.py -s ./your_project -o ./combined.txt`
- **File extraction**: Use
  `python tools/s1f.py -i ./combined.txt -d ./extracted_files`
- **Check token count**: Use `python tools/token_counter.py ./combined.txt`
- **Convert HTML to Markdown**: Use
  `python tools/html2md.py --source-dir ./html --destination-dir ./markdown`

### Key Concepts

- **Separator Styles**: Different formats for separating files in the combined
  output ([details](./m1f.md#separator-styles))
- **File Filtering**: Include/exclude specific files using patterns
  ([details](./m1f.md#command-line-options))
- **Security**: Scan for secrets before combining files
  ([details](./m1f.md#security-check))
- **Content Selection**: Extract specific content using CSS selectors
  ([details](./html2md.md#content-selection))

## Project Overview

m1f is a comprehensive toolkit designed to help you work more efficiently
with Large Language Models (LLMs) by managing context. These tools solve core
challenges when working with AI assistants: providing comprehensive context
efficiently and converting web content to LLM-friendly formats.

The toolset allows you to:

- Combine multiple project files into a single reference file (perfect for
  providing context to LLMs)
- Extract individual files from a combined file (restore original files with
  their structure intact)
- Convert HTML documentation to clean Markdown format
- Estimate token usage for LLM context planning
- Optimize your use of AI context windows by selecting only the most relevant
  files
