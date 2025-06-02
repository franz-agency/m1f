# Auto Bundle Guide

The auto_bundle scripts automatically create and update m1f bundles for different aspects of your project. They support both a simple mode with predefined bundles and an advanced mode using YAML configuration.

## Overview

The auto_bundle scripts are available in two versions:
- **Bash**: `scripts/auto_bundle.sh` (Linux/macOS)
- **PowerShell**: `scripts/auto_bundle.ps1` (Windows)

Both scripts provide identical functionality and support two operation modes:
1. **Simple Mode**: Uses hardcoded bundle definitions
2. **Advanced Mode**: Uses `.m1f.config.yml` for flexible configuration

## Installation

### Prerequisites

**For Simple Mode:**
- Python 3.x
- m1f tool installed

**For Advanced Mode (additional):**
- PyYAML (`pip install pyyaml`)
- `.m1f.config.yml` configuration file

## Usage

### Basic Commands

**Bash (Linux/macOS):**
```bash
# Create all bundles
./scripts/auto_bundle.sh

# Create specific bundle
./scripts/auto_bundle.sh docs

# Force simple mode
./scripts/auto_bundle.sh --simple

# Show help
./scripts/auto_bundle.sh --help
```

**PowerShell (Windows):**
```powershell
# Create all bundles
.\scripts\auto_bundle.ps1

# Create specific bundle
.\scripts\auto_bundle.ps1 docs

# Force simple mode
.\scripts\auto_bundle.ps1 -Simple

# Show help
.\scripts\auto_bundle.ps1 -Help
```

## Operation Modes

### Simple Mode

Simple mode uses predefined bundle configurations and creates a standard directory structure:

```
.m1f/
├── docs/
│   ├── manual.m1f.txt      # All documentation
│   └── api_docs.m1f.txt    # API docs (if docs/ exists)
├── src/
│   ├── source.m1f.txt      # Source code (no tests)
│   └── tools.m1f.txt       # Tools directory (if exists)
├── tests/
│   ├── tests.m1f.txt       # Test structure
│   └── test_inventory.txt  # List of test files
└── complete/
    └── project.m1f.txt     # Complete project bundle
```

**Default Bundles:**
- `docs`: Documentation files (.md, .rst, .txt)
- `src`: Source code files (.py, excluding tests)
- `tests`: Test files structure
- `complete`: Complete project snapshot

### Advanced Mode

Advanced mode uses a YAML configuration file (`.m1f.config.yml`) for flexible bundle definitions.

**Key Features:**
- Custom bundle definitions
- Conditional bundles (enabled_if_exists)
- Priority-based bundling for AI/LLM contexts
- Global settings and exclusions
- Custom output paths and separator styles

## Configuration File Format

The `.m1f.config.yml` file structure:

```yaml
# Bundle definitions
bundles:
  bundle_name:
    description: "Bundle description"
    output: "path/to/output.m1f.txt"
    sources:
      - path: "source/directory"
        include_extensions: [".py", ".js"]
        include_patterns: ["**/test_*.py"]
        excludes: ["**/node_modules/**"]
    separator_style: "Detailed"
    priority: "high"
    enabled_if_exists: "conditional/path"
    filename_mtime_hash: true

# Global settings
global:
  global_excludes:
    - "**/.git/**"
    - "**/node_modules/**"
  defaults:
    minimal_output: true
    force_overwrite: true

# AI/LLM optimization
ai_optimization:
  token_limits:
    claude: 200000
    gpt4: 128000
  context_priority:
    - "docs"
    - "src"
    - "tests"
  usage_hints:
    docs: "Start here for project understanding"
    src: "Core implementation details"
```

## Bundle Configuration Options

### Source Options

- `path`: Source directory (relative to project root)
- `include_extensions`: List of file extensions to include
- `include_patterns`: Glob patterns for files to include
- `excludes`: List of glob patterns to exclude

### Output Options

- `output`: Output file path (relative to project root)
- `separator_style`: Style for file separators (Standard, Detailed, Markdown)
- `filename_mtime_hash`: Include file modification time and hash
- `minimal_output`: Minimize output verbosity

### Control Options

- `enabled`: Boolean to enable/disable bundle
- `enabled_if_exists`: Only create bundle if path exists
- `priority`: Priority level for AI context (high, medium, low)

## AI/LLM Optimization

The advanced mode includes features specifically for AI/LLM usage:

### Token Management

Configure token limits for different models:
```yaml
ai_optimization:
  token_limits:
    claude: 200000
    gpt4: 128000
    default: 100000
```

### Context Priority

Define bundle loading priority for optimal context usage:
```yaml
ai_optimization:
  context_priority:
    - "docs"      # First: understand the project
    - "src"       # Second: core implementation
    - "tools"     # Third: specific tools
    - "complete"  # Last resort: everything
```

### Usage Hints

Provide guidance for each bundle:
```yaml
ai_optimization:
  usage_hints:
    docs: "Start here to understand project structure"
    src: "Core implementation details"
    tests: "Test structure (reference only when debugging)"
```

## Examples

### Creating a Custom Bundle

Add to `.m1f.config.yml`:
```yaml
bundles:
  frontend:
    description: "Frontend code bundle"
    output: ".m1f/frontend/ui.m1f.txt"
    sources:
      - path: "src/frontend"
        include_extensions: [".js", ".jsx", ".css"]
        excludes: ["**/node_modules/**", "**/dist/**"]
    separator_style: "Detailed"
    priority: "high"
```

### Conditional Bundle

Create bundle only if directory exists:
```yaml
bundles:
  mobile:
    description: "Mobile app code"
    output: ".m1f/mobile/app.m1f.txt"
    sources:
      - path: "mobile/"
        include_extensions: [".swift", ".kt", ".java"]
    enabled_if_exists: "mobile/"
```

### Pattern-Based Bundle

Include files matching specific patterns:
```yaml
bundles:
  configs:
    description: "Configuration files"
    output: ".m1f/configs/settings.m1f.txt"
    sources:
      - path: "."
        include_patterns:
          - "**/*.config.js"
          - "**/config/*.yml"
          - ".env*"
    separator_style: "Standard"
```

## Best Practices

1. **Start Simple**: Use simple mode for basic projects
2. **Customize Gradually**: Move to advanced mode as needs grow
3. **Prioritize Bundles**: Set appropriate priorities for AI contexts
4. **Use Conditionals**: Enable bundles only when relevant
5. **Exclude Wisely**: Prevent large/irrelevant files from bloating bundles
6. **Document Purpose**: Use clear descriptions for each bundle

## Troubleshooting

### Common Issues

**"Config file not found"**
- Ensure `.m1f.config.yml` exists in project root
- Check file permissions

**"PyYAML not installed"**
- Install with: `pip install pyyaml`
- Script falls back to simple mode if unavailable

**"Bundle creation failed"**
- Check source paths exist
- Verify include/exclude patterns
- Ensure output directory is writable

### Mode Detection

The script automatically detects which mode to use:
1. Checks for `.m1f.config.yml`
2. Verifies Python and PyYAML availability
3. Falls back to simple mode if requirements not met

Use `--simple` (bash) or `-Simple` (PowerShell) to force simple mode.

## Integration with m1f Workflow

### With File Watchers

Use with `watch_and_bundle.sh` for automatic updates:
```bash
./scripts/watch_and_bundle.sh
```

### In CI/CD Pipelines

```yaml
# Example GitHub Actions
- name: Create m1f bundles
  run: ./scripts/auto_bundle.sh
```

### With AI Tools

Reference bundles in AI prompts:
```
Please review the documentation in .m1f/docs/manual.m1f.txt
and the source code in .m1f/src/source.m1f.txt
```

## Output Structure

### Bundle Info File

Each run creates/updates `.m1f/BUNDLE_INFO.md` with:
- Generation timestamp
- Available bundles list
- Usage examples
- Update instructions

### Statistics

Both modes display bundle statistics:
- Number of files per bundle
- Total size of each bundle
- Execution time

## Advanced Features

### Global Exclusions

Define exclusions that apply to all bundles:
```yaml
global:
  global_excludes:
    - "**/.git/**"
    - "**/build/**"
    - "**/*.log"
```

### Custom Separator Styles

Choose from:
- `Standard`: Simple file separators
- `Detailed`: Include file metadata
- `Markdown`: Markdown-friendly format

### File Metadata

Enable `filename_mtime_hash` for:
- File modification timestamps
- File content hashes
- Change tracking

## Migration from v1 to v2

If you were using the old `auto_bundle_v2.sh`:
1. The functionality is now integrated into `auto_bundle.sh`
2. Your `.m1f.config.yml` continues to work
3. Simple mode provides backward compatibility
4. No changes needed to existing workflows

## See Also

- [m1f Documentation](m1f.md)
- [m1f Presets Guide](m1f_presets.md)
- [M1F Development Workflow](m1f_development_workflow.md)