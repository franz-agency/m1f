# Auto Bundle Guide

The m1f auto-bundle feature allows you to automatically create and manage multiple m1f bundles through a YAML configuration file. This is perfect for projects that need different bundle configurations for various purposes (documentation, source code, tests, etc.).

## Overview

Auto-bundle is a built-in m1f subcommand that reads a `.m1f.config.yml` file from your project root and creates multiple bundles based on the configuration. It supports:

- Multiple bundle definitions in a single configuration
- Conditional bundle creation based on file/directory existence
- Global settings and exclusions
- Custom output paths and processing options
- Integration with m1f presets

## Usage

### Basic Commands

```bash
# Create all bundles defined in .m1f.config.yml
python -m tools.m1f auto-bundle

# Create a specific bundle
python -m tools.m1f auto-bundle docs

# List available bundles
python -m tools.m1f auto-bundle --list

# Verbose output
python -m tools.m1f auto-bundle --verbose

# Quiet mode (suppress output)
python -m tools.m1f auto-bundle --quiet
```

### Using the m1f-update Alias

If you have set up the m1f aliases (see [Development Workflow](04_m1f_development_workflow.md)), you can use the convenient `m1f-update` command from anywhere:

```bash
# Create all bundles
m1f-update

# Create specific bundle
m1f-update docs

# List available bundles
m1f-update --list
```

The `m1f-update` alias automatically handles virtual environment activation and runs the auto-bundle command.

## Configuration File Format

The auto-bundle feature requires a `.m1f.config.yml` file in your project root. Here's the structure:

```yaml
# Global settings that apply to all bundles
global:
  # Global exclusions applied to all bundles
  global_excludes:
    - "**/*.pyc"
    - "**/__pycache__/**"
    - "**/node_modules/**"
    - "**/.git/**"
    
  # Default settings for all bundles
  defaults:
    minimal_output: true
    force_overwrite: true
    max_file_size: "10MB"

# Bundle definitions
bundles:
  # Each bundle has a unique name
  bundle_name:
    # Required fields
    description: "Description of this bundle"
    output: "path/to/output.txt"
    
    # Sources configuration
    sources:
      - path: "source/directory"
        include_extensions: [".py", ".js"]
        excludes: ["test_*.py"]
        
    # Optional fields
    enabled: true                    # Enable/disable bundle
    enabled_if_exists: "some/path"   # Only create if path exists
    separator_style: "Detailed"      # Output format
    preset: "presets/custom.yml"     # Custom preset file
    preset_group: "development"      # Preset group to use
    exclude_paths_file: ".gitignore" # Additional exclude file
    include_paths_file: "includes.txt" # Include patterns file
    filename_mtime_hash: true        # Add file hash to output
    minimal_output: false            # Override global setting
```

## Bundle Configuration Options

### Basic Options

- **description**: Human-readable description of the bundle
- **output**: Output file path (relative to project root)
- **sources**: List of source configurations

### Source Configuration

Each source in the `sources` list can have:

```yaml
sources:
  - path: "."                        # Directory to process
    include_extensions: [".py"]      # Only include these extensions
    excludes: ["**/test_*"]         # Exclude patterns
    include_files: ["README.md"]     # Specific files to include
```

### Control Options

- **enabled**: Boolean to enable/disable the bundle (default: true)
- **enabled_if_exists**: Only create bundle if this path exists
- **separator_style**: One of "Standard", "Detailed", "Markdown", "MachineReadable", "None"
- **preset**: Path to m1f preset file for custom processing
- **preset_group**: Specific preset group to use from the preset file

### File Filtering

- **exclude_paths_file**: File(s) containing exclude patterns (can be string or list)
- **include_paths_file**: File(s) containing include patterns (can be string or list)
- **global_excludes**: Patterns to exclude from all bundles (defined in global section)

## Examples

### Basic Documentation Bundle

```yaml
bundles:
  docs:
    description: "All documentation files"
    output: ".m1f/docs/documentation.txt"
    sources:
      - path: "."
        include_extensions: [".md", ".rst", ".txt"]
        excludes: ["**/node_modules/**", "**/tests/**"]
    separator_style: "Markdown"
```

### Source Code Bundle with Multiple Paths

```yaml
bundles:
  source-code:
    description: "Application source code"
    output: ".m1f/src/code.txt"
    sources:
      - path: "src"
        include_extensions: [".py", ".js", ".ts"]
      - path: "lib"
        include_extensions: [".py"]
        excludes: ["**/test_*.py"]
      - path: "scripts"
        include_files: ["deploy.sh", "build.sh"]
```

### Conditional Bundle

```yaml
bundles:
  mobile-app:
    description: "Mobile application code"
    output: ".m1f/mobile/app.txt"
    enabled_if_exists: "mobile/"  # Only create if mobile/ directory exists
    sources:
      - path: "mobile"
        include_extensions: [".swift", ".kt", ".java"]
```

### Bundle with Presets

```yaml
bundles:
  web-frontend:
    description: "Frontend code with minification"
    output: ".m1f/frontend/bundle.txt"
    sources:
      - path: "frontend"
        include_extensions: [".js", ".jsx", ".css", ".scss"]
    preset: "presets/web-project.m1f-presets.yml"
    preset_group: "production"
```

### Using Multiple Exclude Files

```yaml
global:
  global_excludes:
    - "**/*.log"
    - "**/*.tmp"
    
bundles:
  clean-project:
    description: "Project without generated files"
    output: ".m1f/clean/project.txt"
    sources:
      - path: "."
    exclude_paths_file:
      - ".gitignore"
      - ".m1fignore"
      - "custom-excludes.txt"
```

## Best Practices

### 1. Organize Bundles by Purpose

Create focused bundles for specific use cases:

```yaml
bundles:
  # For understanding the project
  overview:
    description: "Project overview and documentation"
    output: ".m1f/overview.txt"
    sources:
      - path: "."
        include_files: ["README.md", "CONTRIBUTING.md", "LICENSE"]
      - path: "docs"
        include_extensions: [".md"]
        
  # For development work
  dev-code:
    description: "Development source code"
    output: ".m1f/dev-code.txt"
    sources:
      - path: "src"
        include_extensions: [".py", ".js"]
        excludes: ["**/test_*"]
```

### 2. Use Conditional Bundles

Avoid errors by making bundles conditional:

```yaml
bundles:
  tests:
    description: "Test suite"
    output: ".m1f/tests.txt"
    enabled_if_exists: "tests/"  # Skip if no tests directory
    sources:
      - path: "tests"
```

### 3. Leverage Global Settings

Define common settings once:

```yaml
global:
  defaults:
    minimal_output: true
    force_overwrite: true
    separator_style: "Detailed"
    
  global_excludes:
    - "**/.git/**"
    - "**/node_modules/**"
    - "**/__pycache__/**"
    - "**/*.pyc"
```

### 4. Create AI/LLM-Optimized Bundles

Structure bundles for effective AI context:

```yaml
bundles:
  # High-priority context
  ai-context-core:
    description: "Core project context for AI"
    output: ".m1f/ai/core-context.txt"
    sources:
      - path: "."
        include_files: ["README.md", "pyproject.toml", "package.json"]
      - path: "docs"
        include_extensions: [".md"]
        excludes: ["**/api-reference/**"]
    separator_style: "Markdown"
    
  # Detailed implementation
  ai-context-impl:
    description: "Implementation details for AI"
    output: ".m1f/ai/implementation.txt"
    sources:
      - path: "src"
        include_extensions: [".py", ".js"]
        excludes: ["**/test_*", "**/migrations/**"]
```

### 5. Use Descriptive Names and Descriptions

Make it clear what each bundle contains:

```yaml
bundles:
  frontend-react-components:
    description: "React component library source code"
    # ... vs ...
  frontend:
    description: "Frontend files"
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
- name: Create m1f bundles
  run: |
    python -m pip install pyyaml
    python -m tools.m1f auto-bundle
    
- name: Upload bundles
  uses: actions/upload-artifact@v3
  with:
    name: m1f-bundles
    path: .m1f/
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit
python -m tools.m1f auto-bundle --quiet
git add .m1f/
```

## Troubleshooting

### Common Issues

**"No auto-bundle configuration found"**
- Ensure `.m1f.config.yml` exists in your project root
- Check file name is exactly `.m1f.config.yml`

**"Failed to load config: "**
- Verify YAML syntax is correct
- Install PyYAML: `pip install pyyaml`

**"Bundle 'x' not found in configuration"**
- Run `python -m tools.m1f auto-bundle --list` to see available bundles
- Check bundle name spelling

**"Command failed: "**
- Check source paths exist
- Verify file permissions
- Ensure output directory can be created

### Debugging

Use verbose mode to see detailed output:

```bash
python -m tools.m1f auto-bundle --verbose
```

This will show:
- Which directories are being created
- The exact m1f commands being executed
- Any errors or warnings

## See Also

- [m1f Documentation](00_m1f.md)
- [m1f CLI Reference](07_cli_reference.md)
- [m1f Presets Guide](02_m1f_presets.md)
- [M1F Development Workflow](04_m1f_development_workflow.md)