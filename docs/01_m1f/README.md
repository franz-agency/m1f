# m1f Documentation

Welcome to the m1f (Make One File) documentation. This tool combines multiple
text files into a single output file, perfect for providing context to Large
Language Models (LLMs) and creating bundled documentation.

## What's New in v3.2

- **Enhanced Security**: Path traversal protection, SSRF prevention, automatic
  robots.txt compliance
- **Performance**: Parallel file processing enabled by default (3-5x faster)
- **Flexibility**: Control content deduplication and UTF-8 encoding preferences
- **Reliability**: Improved error handling and security scanning

See the [v3.2 Features Guide](./41_version_3_2_features.md) for details.

## Table of Contents

### Getting Started

- [**00_m1f.md**](00_m1f.md) - Main documentation with features, usage examples,
  and architecture
- [**01_quick_reference.md**](./01_quick_reference.md) - Quick command reference
  and common patterns
- [**02_cli_reference.md**](./02_cli_reference.md) - Complete command-line
  parameter reference
- [**03_troubleshooting.md**](./03_troubleshooting.md) - Common issues and
  solutions

### Preset System

- [**10_m1f_presets.md**](./10_m1f_presets.md) - Comprehensive preset system
  guide
- [**11_preset_per_file_settings.md**](./11_preset_per_file_settings.md) -
  Advanced per-file processing configuration
- [**12_preset_reference.md**](./12_preset_reference.md) - Complete preset
  reference with all settings, features, and clarifications

### Features & Tools

- [**20_auto_bundle_guide.md**](./20_auto_bundle_guide.md) - Automated bundling
  with configuration files
- [**21_development_workflow.md**](./21_development_workflow.md) - Best
  practices for development workflows

### AI Integration

- [**30_claude_workflows.md**](./30_claude_workflows.md) - Working with Claude
  and LLMs
- [**31_claude_code_integration.md**](./31_claude_code_integration.md) -
  Integration with Claude Code for AI-assisted development

### Advanced Topics

- [**40_security_best_practices.md**](./40_security_best_practices.md) -
  Security guidelines and protective measures
- [**41_version_3_2_features.md**](./41_version_3_2_features.md) - Comprehensive
  v3.2 feature documentation and migration guide

## Quick Start

```bash
# Basic usage (parallel processing is automatic in v3.2)
m1f -s ./your_project -o ./combined.txt

# With file type filtering
m1f -s ./src -o code.txt --include-extensions .py .js

# Using presets
m1f -s . -o bundle.txt --preset wordpress.m1f-presets.yml

# v3.2 features: Allow duplicate files + custom encoding
m1f -s ./legacy -o output.txt --allow-duplicate-files --no-prefer-utf8-for-text-files

# Security scanning with warning mode
m1f -s ./src -o bundle.txt --security-check warn
```

For detailed information, start with the [main documentation](00_m1f.md) or jump
to the [quick reference](./01_quick_reference.md) for common commands.
