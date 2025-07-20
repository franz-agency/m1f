# m1f Documentation

Welcome to the m1f project documentation. This directory contains comprehensive
guides, references, and examples for all tools in the m1f toolkit.

**Current Version: 3.6.0** | [Changelog](99_CHANGELOG.md)

## Table of Contents

### 📚 Core Tool Documentation

#### m1f (Make One File)

The main tool that combines multiple files into a single reference file with
content deduplication.

- [**m1f Overview**](01_m1f/00_m1f.md) - Complete guide with features, usage
  examples, and architecture
- [**Quick Reference**](01_m1f/01_quick_reference.md) - Common commands and
  patterns for quick lookup
- [**CLI Reference**](01_m1f/02_cli_reference.md) - Complete command-line
  parameter reference
- [**Troubleshooting Guide**](01_m1f/03_troubleshooting.md) - Common issues and
  their solutions
- [**Security Best Practices**](01_m1f/40_security_best_practices.md) - Security
  guidelines and protective measures

#### s1f (Split One File)

Extracts individual files from a combined file with preserved structure.

- [**s1f Documentation**](02_s1f/20_s1f.md) - Complete guide for file extraction
  tool

#### Web Tools

Professional web scraping and conversion tools.

- [**Webscraper**](04_scrape/40_webscraper.md) - Download websites for offline
  viewing and processing
- [**HTML to Markdown Converter**](03_html2md/30_html2md.md) - Comprehensive
  HTML to Markdown conversion guide
- [**HTML2MD Usage Guide**](03_html2md/31_html2md_guide.md) - Detailed usage
  examples and patterns
- [**HTML2MD Workflow Guide**](03_html2md/32_html2md_workflow_guide.md) -
  Advanced workflows and automation
- [**HTML2MD Test Suite**](03_html2md/33_html2md_test_suite.md) - Testing
  documentation and examples
- [**Scraper Backends**](04_scrape/41_html2md_scraper_backends.md) - Backend
  options for web scraping

#### Utility Tools

- [**Token Counter**](99_misc/98_token_counter.md) - Estimate token usage for
  LLM context planning

### 🎯 Advanced Features

#### Preset System

File-specific processing rules and configurations.

- [**Preset System Guide**](01_m1f/10_m1f_presets.md) - Complete preset system
  documentation
- [**Per-File Type Settings**](01_m1f/11_preset_per_file_settings.md) -
  Fine-grained file processing control
- [**Preset Reference**](01_m1f/12_preset_reference.md) - Complete reference
  with all settings and features

#### Auto-Bundle & Configuration

Automated project bundling for AI/LLM consumption.

- [**Auto Bundle Guide**](01_m1f/20_auto_bundle_guide.md) - Automatic bundling
  with configuration files
- [**Configuration Examples**](01_m1f/25_m1f_config_examples.md) - Real-world
  configuration examples
- [**Default Excludes Guide**](01_m1f/26_default_excludes_guide.md) -
  Understanding default exclusion patterns

#### AI Integration

Work efficiently with Claude and other LLMs.

- [**Claude + m1f Workflows**](01_m1f/30_claude_workflows.md) - Turn Claude into
  your personal m1f expert
- [**Claude Code Integration**](01_m1f/31_claude_code_integration.md) - Optional
  AI-powered tool automation

### 🔧 Development

- [**Development Workflow**](01_m1f/21_development_workflow.md) - Best practices
  for development with m1f
- [**Version Management**](05_development/55_version_management.md) - Version
  management and release process
- [**Git Hooks Setup**](05_development/56_git_hooks_setup.md) - Automated
  bundling with git hooks
- [**Version 3.2 Features**](01_m1f/41_version_3_2_features.md) - Feature
  documentation and migration guide

### 📖 Additional Resources

- [**m1f Section Overview**](01_m1f/README.md) - Overview of m1f documentation
  section
- [**Development Section Overview**](05_development/README.md) - Overview of
  development documentation
- [**Full Changelog**](99_CHANGELOG.md) - Complete project history and version
  details

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/Karrtii/m1f.git
cd m1f

# Install tools
./scripts/install.sh  # On Windows: ./scripts/install.ps1
```

### Basic Usage

```bash
# Combine files
m1f -s ./your_project -o ./combined.txt

# Extract files
m1f-s1f -i ./combined.txt -d ./extracted_files

# Check token count
m1f-token-counter ./combined.txt

# Download website
m1f-scrape https://example.com -o ./html

# Convert HTML to Markdown
m1f-html2md convert ./html ./markdown
```

### Using Auto-Bundle

```bash
# Create all configured bundles
m1f auto-bundle

# List available bundles
m1f auto-bundle --list

# Create specific bundle
m1f auto-bundle documentation
```

## Navigation Tips

- **New to m1f?** Start with the [m1f Overview](01_m1f/00_m1f.md) and
  [Quick Reference](01_m1f/01_quick_reference.md)
- **Setting up automation?** Check the
  [Auto Bundle Guide](01_m1f/20_auto_bundle_guide.md) and
  [Configuration Examples](01_m1f/25_m1f_config_examples.md)
- **Working with AI?** See [Claude Workflows](01_m1f/30_claude_workflows.md) for
  optimal LLM integration
- **Need help?** Visit the [Troubleshooting Guide](01_m1f/03_troubleshooting.md)

## Project Overview

m1f is a comprehensive toolkit designed to help you work more efficiently with
Large Language Models (LLMs) by managing context. Built with modern Python 3.10+
architecture, it features:

- **Async I/O** for high performance
- **Type hints** throughout the codebase
- **Modular design** for easy extension
- **Security-first** approach with built-in protections
- **Cross-platform** compatibility (Windows, macOS, Linux)

Whether you're bundling code for AI analysis, creating documentation packages,
or managing large codebases, m1f provides the tools you need to work
efficiently.
