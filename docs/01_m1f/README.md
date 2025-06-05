# m1f Documentation

Welcome to the m1f (Make One File) documentation. This tool combines multiple
text files into a single output file, perfect for providing context to Large
Language Models (LLMs) and creating bundled documentation.

## Table of Contents

### Core Documentation

- [**01_m1f.md**](00_m1f.md) - Main documentation with features, usage examples,
  and architecture
- [**07_cli_reference.md**](./07_cli_reference.md) - Complete command-line
  parameter reference
- [**08_troubleshooting.md**](./08_troubleshooting.md) - Common issues and
  solutions
- [**09_quick_reference.md**](./09_quick_reference.md) - Quick command reference
  and common patterns

### Preset System

- [**02_m1f_presets.md**](./02_m1f_presets.md) - Comprehensive preset system
  guide
- [**03_m1f_preset_per_file_settings.md**](./03_m1f_preset_per_file_settings.md) -
  Advanced per-file processing configuration
- [**10_preset_reference.md**](./10_preset_reference.md) - Complete preset
  reference with all settings and features
- [**11_preset_system_clarifications.md**](./11_preset_system_clarifications.md) -
  Important clarifications and common misconceptions

### Workflows and Integration

- [**04_m1f_development_workflow.md**](./04_m1f_development_workflow.md) - Best
  practices for development workflows
- [**05_claude_code_integration.md**](./05_claude_code_integration.md) -
  Integration with Claude Code for AI-assisted development
- [**06_auto_bundle_guide.md**](./06_auto_bundle_guide.md) - Automated bundling
  with configuration files

## Quick Start

```bash
# Basic usage
python tools/m1f.py -s ./your_project -o ./combined.txt

# With file type filtering
python tools/m1f.py -s ./src -o code.txt --include-extensions .py .js

# Using presets
python tools/m1f.py -s . -o bundle.txt --preset wordpress.m1f-presets.yml
```

For detailed information, start with the [main documentation](00_m1f.md) or jump
to the [quick reference](./09_quick_reference.md) for common commands.
