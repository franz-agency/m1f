# m1f Preset System Documentation

The m1f preset system allows you to define file-specific processing rules,
enabling different handling for different file types within the same bundle.

## Overview

Instead of applying the same settings to all files, presets let you:

- Minify HTML files while preserving source code formatting
- Strip comments from production code but keep them in documentation
- Apply different separator styles for different file types
- Truncate large data files while keeping full source code
- **NEW**: Override security checks and size limits per file type
- **NEW**: Integrate with auto-bundling for intelligent project organization

## Quick Start

1. **Use a built-in preset**:

   ```bash
   python tools/m1f.py -s ./my-project -o bundle.txt --preset presets/wordpress.m1f-presets.yml
   ```

2. **Specify a preset group**:

   ```bash
   python tools/m1f.py -s ./site -o bundle.txt --preset presets/web-project.m1f-presets.yml --preset-group frontend
   ```

3. **Use multiple preset files**:
   ```bash
   python tools/m1f.py -s . -o bundle.txt --preset company-presets.yml project-presets.yml
   ```

## Preset Configuration File

Preset files are YAML documents that define processing rules:

```yaml
# Group name
my_project:
  description: "Processing rules for my project"
  enabled: true
  priority: 10 # Higher priority groups are checked first
  base_path: "src" # Optional base path for patterns

  presets:
    # Preset for Python files
    python:
      extensions: [".py"]
      patterns:
        - "*.py"
        - "lib/**/*.py"
      actions:
        - strip_comments
        - remove_empty_lines
      separator_style: "Detailed"
      include_metadata: true

    # Preset for HTML files
    html:
      extensions: [".html", ".htm"]
      actions:
        - minify
        - strip_tags
      strip_tags: ["script", "style"]
      preserve_tags: ["pre", "code"]
      max_lines: 500 # Truncate after 500 lines

    # Default preset for unmatched files
    default:
      actions: []
      include_metadata: true
```

## Available Actions

### Built-in Actions

1. **`minify`** - Reduces file size by removing unnecessary whitespace

   - HTML: Removes comments, compresses whitespace
   - CSS: Removes comments, compresses rules
   - JS: Basic minification (removes comments and newlines)

2. **`strip_tags`** - Removes HTML tags

   - Use `strip_tags` to list tags to remove
   - Use `preserve_tags` to protect specific tags

3. **`strip_comments`** - Removes comments based on file type

   - Python: Removes # comments (preserves docstrings)
   - JS/Java/C/C++: Removes // and /\* \*/ comments

4. **`compress_whitespace`** - Normalizes whitespace

   - Replaces multiple spaces with single space
   - Reduces multiple newlines to double newline

5. **`remove_empty_lines`** - Removes all empty lines

6. **`custom`** - Apply custom processor
   - Specify processor with `custom_processor`
   - Pass arguments with `processor_args`

### Built-in Custom Processors

1. **`truncate`** - Limit content length

   ```yaml
   actions:
     - custom
   custom_processor: "truncate"
   processor_args:
     max_chars: 1000
   ```

2. **`redact_secrets`** - Remove sensitive data

   ```yaml
   actions:
     - custom
   custom_processor: "redact_secrets"
   processor_args:
     patterns:
       - '(?i)api[_-]?key\s*[:=]\s*["\']?[\w-]+["\']?'
   ```

3. **`extract_functions`** - Extract only function definitions (Python)
   ```yaml
   actions:
     - custom
   custom_processor: "extract_functions"
   ```

## Preset Options

### File Matching

- **`extensions`**: List of file extensions (e.g., `[".py", ".js"]`)
- **`patterns`**: Glob patterns for matching files (e.g., `["src/**/*.py"]`)

### Processing Options

- **`actions`**: List of processing actions to apply
- **`strip_tags`**: HTML tags to remove
- **`preserve_tags`**: HTML tags to keep when stripping
- **`separator_style`**: Override default separator ("Standard", "Detailed",
  "Markdown", "None")
- **`include_metadata`**: Whether to include file metadata (default: true)
- **`max_lines`**: Truncate file after N lines

### Custom Processing

- **`custom_processor`**: Name of custom processor
- **`processor_args`**: Arguments for custom processor

## Examples

### WordPress Project

```yaml
wordpress:
  description: "WordPress project processing"

  presets:
    php:
      extensions: [".php"]
      actions:
        - strip_comments
        - remove_empty_lines

    config:
      patterns: ["wp-config*.php", ".env*"]
      actions:
        - custom
      custom_processor: "redact_secrets"

    sql:
      extensions: [".sql"]
      actions:
        - strip_comments
      max_lines: 1000 # Truncate large dumps
```

### Frontend Project

```yaml
frontend:
  description: "React/Vue/Angular project"

  presets:
    components:
      extensions: [".jsx", ".tsx", ".vue"]
      actions:
        - strip_comments
        - compress_whitespace

    styles:
      extensions: [".css", ".scss"]
      actions:
        - minify
      # Note: exclude_patterns is available in global_settings, not in presets

    images:
      extensions: [".png", ".jpg", ".svg"]
      actions:
        - custom
      custom_processor: "truncate"
      processor_args:
        max_chars: 50 # Just filename
```

### Documentation Project

```yaml
documentation:
  description: "Documentation processing"

  presets:
    markdown:
      extensions: [".md", ".mdx"]
      actions:
        - remove_empty_lines
      separator_style: "Markdown"

    code_examples:
      patterns: ["examples/**/*"]
      actions:
        - strip_comments
      max_lines: 50 # Keep examples concise
```

## Priority and Selection

When multiple preset groups are loaded:

1. Groups are checked by priority (highest first)
2. Within a group, presets are checked in order:
   - Extension matches
   - Pattern matches
   - Default preset
3. First matching preset is used
4. If no preset matches, standard m1f processing applies

## Command Line Usage

```bash
# Use single preset file
python tools/m1f.py -s . -o out.txt --preset my-presets.yml

# Use specific group
python tools/m1f.py -s . -o out.txt --preset presets.yml --preset-group backend

# Multiple preset files (merged in order)
python tools/m1f.py -s . -o out.txt --preset base.yml project.yml

# Disable all presets
python tools/m1f.py -s . -o out.txt --preset presets.yml --disable-presets
```

## Complete List of Supported Settings

### Global Settings

These apply to all files unless overridden:

```yaml
global_settings:
  # Encoding and formatting
  encoding: "utf-8"
  separator_style: "Detailed"
  line_ending: "lf"

  # Include/exclude patterns
  include_patterns: ["src/**/*", "lib/**/*"]
  exclude_patterns: ["*.min.js", "*.map"]
  include_extensions: [".py", ".js", ".md"]
  exclude_extensions: [".log", ".tmp"]

  # File filtering
  include_dot_paths: false
  include_binary_files: false
  include_symlinks: false
  no_default_excludes: false
  max_file_size: "10MB"
  
  # Exclude/include file(s) - can be single file or list
  exclude_paths_file: ".gitignore"
  # Or multiple files:
  # exclude_paths_file:
  #   - ".gitignore"
  #   - ".m1f-exclude"
  #   - "custom-excludes.txt"
  
  # Include file(s) for whitelist mode
  # include_paths_file: "important-files.txt"
  # Or multiple files:
  # include_paths_file:
  #   - "core-files.txt"
  #   - "api-files.txt"

  # Processing options
  remove_scraped_metadata: true
  abort_on_encoding_error: false

  # Security
  security_check: "warn" # abort, skip, warn
```

### Extension-Specific Settings

All file-specific settings can now be overridden per extension in
global_settings or in individual presets:

```yaml
global_settings:
  extensions:
    .md:
      actions: [remove_empty_lines]
      security_check: null # Disable security checks for markdown
      remove_scraped_metadata: true
    .php:
      actions: [strip_comments]
      security_check: "abort" # Strict security for PHP
      max_file_size: "5MB"
    .css:
      actions: [minify]
      max_file_size: "50KB" # Stricter size limit for CSS
    .log:
      include_dot_paths: true # Include hidden log files
      max_file_size: "100KB"

presets:
  sensitive_code:
    extensions: [".env", ".key", ".pem"]
    security_check: "abort"
    include_binary_files: false

  documentation:
    extensions: [".md", ".txt", ".rst"]
    security_check: null # No security check for docs
    remove_scraped_metadata: true
```

## Advanced Examples

### Security Check per File Type

Disable security checks for documentation but keep them for code:

```yaml
security_example:
  global_settings:
    security_check: "abort" # Default: strict

    extensions:
      .md:
        security_check: null # Disable for markdown
      .txt:
        security_check: null # Disable for text
      .rst:
        security_check: null # Disable for reStructuredText
      .php:
        security_check: "abort" # Keep strict for PHP
      .js:
        security_check: "warn" # Warn only for JS
      .env:
        security_check: "abort" # Very strict for env files
```

### Size Limits per File Type

Different size limits for different file types:

```yaml
size_limits:
  global_settings:
    max_file_size: "1MB" # Default limit

    extensions:
      .css:
        max_file_size: "50KB" # Stricter for CSS
      .js:
        max_file_size: "100KB" # JavaScript limit
      .php:
        max_file_size: "5MB" # More lenient for PHP
      .sql:
        max_file_size: "10MB" # Large SQL dumps allowed
      .log:
        max_file_size: "500KB" # Log file limit

  presets:
    # Override for specific patterns
    vendor_files:
      patterns: ["vendor/**/*", "node_modules/**/*"]
      max_file_size: "10KB" # Very small for vendor files
```

### Different Processing by Location

Process files differently based on their location:

```yaml
conditional:
  presets:
    # Production files - minify and strip
    production:
      patterns: ["dist/**/*", "build/**/*"]
      actions: [minify, strip_comments]

    # Development files - keep readable
    development:
      patterns: ["src/**/*", "dev/**/*"]
      actions: [remove_empty_lines]

    # Vendor files - skip processing
    vendor:
      patterns: ["vendor/**/*", "node_modules/**/*"]
      actions: [] # No processing
```

### Combining Multiple Presets

You can load multiple preset files that build on each other:

```bash
python tools/m1f.py -s . -o bundle.txt \
  --preset base-rules.yml \
  --preset project-specific.yml \
  --preset production-overrides.yml
```

## Creating Custom Presets

1. **Start with a template**:

   ```bash
   # Use the comprehensive template with all available settings
   cp presets/template-all-settings.m1f-presets.yml my-project.m1f-presets.yml

   # Or start from a simpler example
   cp presets/web-project.m1f-presets.yml my-project.m1f-presets.yml
   ```

2. **Customize for your project**:

   - Identify file types needing special handling
   - Choose appropriate actions
   - Test with a small subset first

3. **Tips**:
   - Use `max_lines` for generated or data files
   - Apply `minify` only to production builds
   - Keep `preserve_tags` for code examples in HTML
   - Use high priority for project-specific rules

## Integration with CI/CD

```yaml
# GitHub Actions example
- name: Create bundle with presets
  run: |
    python tools/m1f.py \
      -s . \
      -o release-bundle.txt \
      --preset .github/release-presets.yml \
      --preset-group production
```

## Troubleshooting

### Preset not applying

- Check file extension includes the dot (`.py` not `py`)
- Verify pattern matches with `--verbose` flag
- Ensure preset group is enabled

### Wrong preset selected

- Check priority values (higher = checked first)
- Use specific patterns over broad extensions
- Use `--preset-group` to target specific group

### Processing errors

- Some actions may not work on all file types
- Binary files skip most processing
- Use `--verbose` to see which presets are applied

## Auto-Bundling Integration

The preset system integrates seamlessly with the auto-bundling scripts:

### Using Presets with Auto-Bundle

1. **With VS Code Tasks**:

   - Use the "Auto Bundle: With Preset" task
   - Select your preset file and optional group
   - The bundle will apply file-specific processing

2. **With Scripts**:

   ```bash
   # Use preset-based bundling script
   ./scripts/auto_bundle.py all

   # Focus on specific area with presets
   ./scripts/auto_bundle.py focus wordpress

   # Use custom preset
   ./scripts/auto_bundle.py preset my-preset.yml frontend
   ```

3. **Available Preset Bundles**:
   - `wordpress` - Theme and plugin development
   - `web-project` - Frontend/backend web projects
   - `documentation` - Documentation-focused bundles
   - Custom presets in `presets/` directory

### Benefits

- **Intelligent Filtering**: Each preset knows which files to include
- **Optimized Processing**: Apply minification only where beneficial
- **Security Control**: Different security levels for different file types
- **Size Management**: Appropriate size limits per file type

See the [Auto Bundle Guide](06_auto_bundle_guide.md) for more details on the
bundling system.

## See Also

- [**Preset System Complete Reference**](./10_preset_reference.md) -
  Comprehensive reference with all settings, undocumented features, and advanced
  patterns
- [**Per-File Settings Guide**](./03_m1f_preset_per_file_settings.md) - Deep
  dive into per-file processing
- [**Auto Bundle Guide**](./06_auto_bundle_guide.md) - Automated bundling with
  presets
