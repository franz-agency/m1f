# m1f Preset System Complete Reference

This document provides a comprehensive reference for the m1f preset system,
including all available settings, clarifications, and advanced usage patterns.

## Table of Contents

- [Quick Start](#quick-start)
- [Preset File Format](#preset-file-format)
- [All Available Settings](#all-available-settings)
- [Available Actions](#available-actions)
- [Pattern Matching](#pattern-matching)
- [Processing Order](#processing-order)
- [Important Clarifications](#important-clarifications)
- [Advanced Features](#advanced-features)
- [Examples](#examples)
- [Debugging and Best Practices](#debugging-and-best-practices)

## Quick Start

The m1f preset system allows you to define file-specific processing rules and
configurations. Here's a minimal example:

```yaml
# my-preset.yml
web_assets:
  description: "Process web assets"
  presets:
    javascript:
      extensions: [".js", ".jsx"]
      actions: ["minify", "strip_comments"]
```

Use it with:

```bash
# Module invocation (recommended)
m1f -s ./src -o bundle.txt --preset my-preset.yml

# Direct command invocation (if installed)
m1f -s ./src -o bundle.txt --preset my-preset.yml
```

## Preset File Format

### Modern Format (Recommended)

```yaml
# Group name - can be selected with --preset-group
group_name:
  description: "Optional description of this preset group"
  enabled: true # Can disable entire group
  priority: 10 # Higher numbers are processed first (default: 0)

  presets:
    # Preset name (for internal reference)
    preset_name:
      patterns: ["*.js", "*.jsx"] # Glob patterns
      extensions: [".js", ".jsx"] # Extension matching (with or without dot)
      actions:
        - minify
        - strip_comments
        - compress_whitespace

      # Per-file overrides
      security_check: "warn" # error, skip, warn
      max_file_size: "500KB"
      include_dot_paths: true
      include_binary_files: false
      remove_scraped_metadata: true

      # Custom processor with arguments
      custom_processor: "truncate"
      processor_args:
        max_lines: 100
        add_marker: true

# Global settings (apply to all groups)
globals:
  global_settings:
    # Input/Output settings (NEW in v3.2.0)
    source_directory: "./src"
    input_file: "files_to_process.txt"
    output_file: "bundle.txt"
    input_include_files:
      - "README.md"
      - "INTRO.txt"

    # Output control (NEW in v3.2.0)
    add_timestamp: true
    filename_mtime_hash: false
    force: false
    minimal_output: false
    skip_output_file: false

    # Archive settings (NEW in v3.2.0)
    create_archive: false
    archive_type: "zip" # zip or tar.gz

    # Runtime behavior (NEW in v3.2.0)
    verbose: false
    quiet: false

    # Default file processing
    security_check: "warn"
    max_file_size: "1MB"

    # Per-extension settings
    extensions:
      .py:
        security_check: "error"
        max_file_size: "2MB"
      .env:
        security_check: "skip"
        actions: ["redact_secrets"]
```

## All Available Settings

### Group-Level Settings

| Setting       | Type    | Default | Description                     |
| ------------- | ------- | ------- | ------------------------------- |
| `description` | string  | none    | Human-readable description      |
| `enabled`     | boolean | true    | Enable/disable this group       |
| `priority`    | integer | 0       | Processing order (higher first) |

### Global Settings (NEW in v3.2.0)

These settings can be specified in the `global_settings` section and override
CLI defaults:

#### Input/Output Settings

| Setting               | Type        | Default | Description                                 |
| --------------------- | ----------- | ------- | ------------------------------------------- |
| `source_directory`    | string      | none    | Source directory path                       |
| `input_file`          | string      | none    | Input file listing paths to process         |
| `output_file`         | string      | none    | Output file path                            |
| `input_include_files` | string/list | []      | Files to include at beginning (intro files) |

#### Output Control Settings

| Setting                 | Type    | Default | Description                          |
| ----------------------- | ------- | ------- | ------------------------------------ |
| `add_timestamp`         | boolean | false   | Add timestamp to output filename     |
| `filename_mtime_hash`   | boolean | false   | Add hash of file mtimes to filename  |
| `force`                 | boolean | false   | Force overwrite existing output file |
| `minimal_output`        | boolean | false   | Only create main output file         |
| `skip_output_file`      | boolean | false   | Skip creating main output file       |
| `allow_duplicate_files` | boolean | false   | Allow duplicate content (v3.2)       |

#### Archive Settings

| Setting          | Type    | Default | Description                       |
| ---------------- | ------- | ------- | --------------------------------- |
| `create_archive` | boolean | false   | Create backup archive of files    |
| `archive_type`   | string  | "zip"   | Archive format: "zip" or "tar.gz" |

#### Runtime Settings

| Setting   | Type    | Default | Description                 |
| --------- | ------- | ------- | --------------------------- |
| `verbose` | boolean | false   | Enable verbose output       |
| `quiet`   | boolean | false   | Suppress all console output |

#### File Processing Settings

| Setting                        | Type    | Default | Description                         |
| ------------------------------ | ------- | ------- | ----------------------------------- |
| `encoding`                     | string  | "utf-8" | Target encoding for all files       |
| `separator_style`              | string  | none    | File separator style                |
| `line_ending`                  | string  | "lf"    | Line ending style (lf/crlf)         |
| `security_check`               | string  | "warn"  | How to handle secrets               |
| `max_file_size`                | string  | none    | Maximum file size to process        |
| `enable_content_deduplication` | boolean | true    | Enable content deduplication (v3.2) |
| `prefer_utf8_for_text_files`   | boolean | true    | Prefer UTF-8 for text files (v3.2)  |

### Preset-Level Settings

| Setting                   | Type    | Default | Description                                 |
| ------------------------- | ------- | ------- | ------------------------------------------- |
| `patterns`                | list    | []      | Glob patterns to match files                |
| `extensions`              | list    | []      | File extensions to match                    |
| `actions`                 | list    | []      | Processing actions to apply                 |
| `security_check`          | string  | "warn"  | How to handle secrets                       |
| `max_file_size`           | string  | none    | Maximum file size to process                |
| `include_dot_paths`       | boolean | false   | Include hidden files                        |
| `include_binary_files`    | boolean | false   | Process binary files                        |
| `remove_scraped_metadata` | boolean | false   | Remove HTML2MD metadata                     |
| `custom_processor`        | string  | none    | Name of custom processor                    |
| `processor_args`          | dict    | {}      | Arguments for custom processor              |
| `line_ending`             | string  | "lf"    | Convert line endings (lf, crlf)             |
| `separator_style`         | string  | none    | Override default separator style            |
| `include_metadata`        | boolean | true    | Include file metadata in output             |
| `max_lines`               | integer | none    | Truncate file after N lines                 |
| `strip_tags`              | list    | []      | HTML tags to remove (for strip_tags action) |
| `preserve_tags`           | list    | []      | HTML tags to preserve when stripping        |

## Available Actions

### Built-in Actions

1. **`minify`** - Remove unnecessary whitespace and formatting

   - Reduces file size
   - Maintains functionality
   - Best for: JS, CSS, HTML

2. **`strip_tags`** - Remove HTML/XML tags

   - Extracts text content only
   - Preserves text between tags
   - Best for: HTML, XML, Markdown with HTML

3. **`strip_comments`** - Remove code comments

   - Removes single and multi-line comments
   - Language-aware (JS, Python, CSS, etc.)
   - Best for: Production code bundles

4. **`compress_whitespace`** - Reduce multiple spaces/newlines

   - Converts multiple spaces to single space
   - Reduces multiple newlines to double newline
   - Best for: Documentation, logs

5. **`remove_empty_lines`** - Remove blank lines
   - Removes lines with only whitespace
   - Keeps single blank lines between sections
   - Best for: Clean documentation

### Custom Processors

Currently implemented:

1. **`truncate`** - Limit file length

   ```yaml
   custom_processor: "truncate"
   processor_args:
     max_lines: 100
     max_chars: 10000
     add_marker: true # Add "... truncated ..." marker
   ```

2. **`redact_secrets`** - Remove sensitive data

   ```yaml
   custom_processor: "redact_secrets"
   processor_args:
     patterns:
       - '(?i)(api[_-]?key|secret|password|token)\\s*[:=]\\s*["\\']?[\\w-]+["\\']?'
       - '(?i)bearer\\s+[\\w-]+'
     replacement: "[REDACTED]"
   ```

3. **`extract_functions`** - Extract function definitions
   ```yaml
   custom_processor: "extract_functions"
   processor_args:
     languages: ["python", "javascript"]
     include_docstrings: true
   ```

Note: Other processors mentioned in examples (like `extract_code_cells`) are
illustrative and would need to be implemented.

## Pattern Matching

### Pattern Types

1. **Extension Matching**

   ```yaml
   extensions: [".py", ".pyx", "py"] # All are equivalent
   ```

2. **Glob Patterns**

   ```yaml
   patterns:
     - "*.test.js" # All test files
     - "src/**/*.js" # All JS in src/
   ```

3. **Combined Matching**
   ```yaml
   # File must match BOTH extension AND pattern
   extensions: [".js"]
   patterns: ["src/**/*"]
   ```

## Processing Order

1. **Group Priority** - Higher priority groups are checked first
2. **Preset Order** - Within a group, presets are checked in definition order
3. **First Match Wins** - First matching preset is applied
4. **Action Order** - Actions are applied in the order listed

### Setting Precedence

1. CLI arguments (highest priority)
2. Preset-specific settings
3. Global per-extension settings
4. Global default settings
5. m1f defaults (lowest priority)

**Note**: CLI arguments ALWAYS override preset values.

## Important Clarifications

### Pattern Matching Limitations

**Exclude patterns with `!` prefix are not supported in preset patterns**. To
exclude files:

1. **Use Global Settings** (Recommended):

   ```yaml
   globals:
     global_settings:
       exclude_patterns: ["*.min.js", "*.map", "dist/**/*"]
   ```

2. **Use CLI Arguments**:
   ```bash
   m1f -s . -o out.txt --exclude-patterns "*.min.js" "*.map"
   ```

### Settings Hierarchy

Understanding where settings can be applied:

1. **Global Settings Level** (`globals.global_settings`):

   - `include_patterns` / `exclude_patterns`
   - `include_extensions` / `exclude_extensions`
   - All general m1f settings

2. **Preset Level** (individual presets):

   - `patterns` and `extensions` (for matching)
   - `actions` (processing actions)
   - Override settings like `security_check`

3. **Extension-Specific Global Settings**
   (`globals.global_settings.extensions.{ext}`):
   - All preset-level settings per extension

### Common Misconceptions

1. **Exclude Patterns in Presets**

   ❌ **Incorrect**:

   ```yaml
   presets:
     my_preset:
       exclude_patterns: ["*.min.js"] # Doesn't work here
   ```

   ✅ **Correct**:

   ```yaml
   globals:
     global_settings:
       exclude_patterns: ["*.min.js"] # Works here
   ```

2. **Actions vs Settings**

   **Actions** (go in `actions` list):

   - `minify`, `strip_tags`, `strip_comments`, etc.

   **Settings** (separate fields):

   - `strip_tags: ["script", "style"]` (configuration)
   - `max_lines: 100` (configuration)

## Advanced Features

### Conditional Enabling

To conditionally enable/disable preset groups:

```yaml
production:
  enabled: false # Manually disable this group
  presets:
    minify_all:
      extensions: [".js", ".css", ".html"]
      actions: ["minify"]
```

**Note**: The `enabled_if_exists` feature is only available in auto-bundle
configurations (`.m1f.config.yml`), not in preset files.

### Multiple Preset Files

```bash
# Files are merged in order (later files override earlier ones)
m1f -s . -o out.txt \
  --preset base.yml \
  --preset project.yml \
  --preset overrides.yml
```

### Preset Locations

1. **Project presets**: `./presets/*.m1f-presets.yml`
2. **Local preset**: `./.m1f-presets.yml`
3. **User presets**: `~/m1f/*.m1f-presets.yml`
4. **Specified presets**: Via `--preset` flag

### Complete Parameter Control (v3.2.0+)

Starting with v3.2.0, ALL m1f parameters can be controlled via presets:

```yaml
# production.m1f-presets.yml
production:
  description: "Production build configuration"

  global_settings:
    # Define all inputs/outputs
    source_directory: "./src"
    output_file: "dist/bundle.txt"
    input_include_files: ["README.md", "LICENSE"]

    # Enable production features
    add_timestamp: true
    create_archive: true
    archive_type: "tar.gz"
    force: true

    # Production optimizations
    minimal_output: true
    quiet: true

    # File processing
    separator_style: "MachineReadable"
    encoding: "utf-8"
    security_check: "error"
```

Usage comparison:

**Before v3.2.0** (long command):

```bash
m1f -s ./src -o dist/bundle.txt \
  --input-include-files README.md LICENSE \
  --add-timestamp --create-archive --archive-type tar.gz \
  --force --minimal-output --quiet \
  --separator-style MachineReadable \
  --security-check error
```

**After v3.2.0** (simple command):

```bash
m1f --preset production.m1f-presets.yml -o output.txt
```

## Examples

### Web Development Preset

```yaml
web_development:
  description: "Modern web development bundle"

  presets:
    # Minify production assets
    production_assets:
      patterns: ["dist/**/*", "build/**/*"]
      extensions: [".js", ".css"]
      actions: ["minify", "strip_comments"]

    # Source code - keep readable
    source_code:
      patterns: ["src/**/*"]
      extensions: [".js", ".jsx", ".ts", ".tsx"]
      actions: ["strip_comments"]
      security_check: "error"

    # Documentation
    docs:
      extensions: [".md", ".mdx"]
      actions: ["compress_whitespace", "remove_empty_lines"]

    # Configuration files
    config:
      patterns: ["*.json", "*.yml", "*.yaml"]
      security_check: "error"
      custom_processor: "redact_secrets"
```

### Data Science Preset

```yaml
data_science:
  presets:
    # Large data files - truncate
    data_files:
      extensions: [".csv", ".json", ".parquet"]
      max_file_size: "100KB"
      custom_processor: "truncate"
      processor_args:
        max_lines: 1000

    # Scripts - full content
    scripts:
      extensions: [".py", ".r", ".jl"]
      actions: ["strip_comments"]
```

### Multiple Environment Presets

```yaml
# environments.m1f-presets.yml
development:
  priority: 10
  global_settings:
    source_directory: "./src"
    output_file: "dev-bundle.txt"
    verbose: true
    include_dot_paths: true
    security_check: "warn"

staging:
  priority: 20
  global_settings:
    source_directory: "./src"
    output_file: "stage-bundle.txt"
    create_archive: true
    security_check: "error"

production:
  priority: 30
  global_settings:
    source_directory: "./dist"
    output_file: "prod-bundle.txt"
    minimal_output: true
    quiet: true
    create_archive: true
    archive_type: "tar.gz"
```

Use with `--preset-group`:

```bash
# Development build
m1f --preset environments.yml --preset-group development

# Production build
m1f --preset environments.yml --preset-group production
```

## Debugging and Best Practices

### Debugging Tips

1. **Verbose Mode**

   ```bash
   m1f -s . -o out.txt --preset my.yml --verbose
   ```

   Shows which preset is applied to each file and processing details.

2. **Check What's Applied**

   ```bash
   m1f -s . -o out.txt --preset my.yml --verbose 2>&1 | grep "Applying preset"
   ```

3. **Validate YAML**

   ```bash
   python -c "import yaml; yaml.safe_load(open('my-preset.yml'))"
   ```

4. **Test Small First** Create a test directory with a few files to verify
   preset behavior before running on large codebases.

### Best Practices

1. **Start Simple** - Begin with basic actions, add complexity as needed
2. **Test Thoroughly** - Use verbose mode to verify behavior
3. **Layer Presets** - Use multiple files for base + overrides
4. **Document Presets** - Add descriptions to groups and complex presets
5. **Version Control** - Keep presets in your repository
6. **Performance First** - Apply expensive actions only where needed
7. **Use Priority Wisely** - Higher priority groups are checked first

### Common Issues

1. **Preset not applied**

   - Check pattern matching
   - Verify preset group is enabled
   - Use verbose mode to debug

2. **Wrong action order**

   - Actions are applied sequentially
   - Order matters (e.g., minify before strip_comments)

3. **Performance issues**
   - Limit expensive actions to necessary files
   - Use `max_file_size` to skip large files
   - Consider `minimal_output` mode

## Version Information

This documentation is accurate as of m1f version 3.2.0.
