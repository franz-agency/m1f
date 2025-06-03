# m1f Preset System Complete Reference

This document provides a comprehensive reference for the m1f preset system,
including all available settings, undocumented features, and advanced usage
patterns.

## Preset File Format

### Modern Format (Recommended)

```yaml
# Group name - can be selected with --preset-group
group_name:
  description: "Optional description of this preset group"
  enabled: true # Can disable entire group
  priority: 10 # Higher numbers are processed first (default: 0)
  base_path: "src" # Optional base path for all patterns in this group

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
      security_check: "warn" # abort, skip, warn
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
    # Default file processing
    security_check: "warn"
    max_file_size: "1MB"

    # Per-extension settings
    extensions:
      .py:
        security_check: "abort"
        max_file_size: "2MB"
      .env:
        security_check: "skip"
        actions: ["redact_secrets"]
```

### Legacy Format (docs-bundle.yml style)

```yaml
# Simple processor definition
name: "docs-bundle"
description: "Optimizes markdown files"
processors:
  remove_empty_lines:
    extensions: [".md", ".txt"]
```

## All Available Settings

### Group-Level Settings

| Setting             | Type    | Default | Description                     |
| ------------------- | ------- | ------- | ------------------------------- |
| `description`       | string  | none    | Human-readable description      |
| `enabled`           | boolean | true    | Enable/disable this group       |
| `priority`          | integer | 0       | Processing order (higher first) |
| `base_path`         | string  | none    | Base path for pattern matching  |
| `enabled_if_exists` | string  | none    | Only enable if this path exists |

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
       - '(?i)(api[_-]?key|secret|password|token)\\s*[:=]\\s*["\']?[\\w-]+["\']?'
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
     # Note: Exclude patterns with "!" are not currently supported
   ```

3. **Combined Matching**
   ```yaml
   # File must match BOTH extension AND pattern
   extensions: [".js"]
   patterns: ["src/**/*"]
   ```

### Base Path Behavior

```yaml
group_name:
  base_path: "src"
  presets:
    example:
      patterns: ["components/*.js"] # Actually matches: src/components/*.js
```

## Processing Order

1. **Group Priority** - Higher priority groups are checked first
2. **Preset Order** - Within a group, presets are checked in definition order
3. **First Match Wins** - First matching preset is applied
4. **Action Order** - Actions are applied in the order listed

## Global Settings

### Structure

```yaml
globals:
  global_settings:
    # Default settings for all files
    security_check: "warn"
    max_file_size: "1MB"

    # Per-extension overrides
    extensions:
      .py:
        security_check: "abort"
        max_file_size: "2MB"
        actions: ["strip_comments"]
      .env:
        security_check: "skip"
        actions: ["redact_secrets"]
```

### Setting Precedence

1. CLI arguments (highest priority)
2. Preset-specific settings
3. Global per-extension settings
4. Global default settings
5. m1f defaults (lowest priority)

## Advanced Features

### Conditional Presets

```yaml
production:
  enabled_if_exists: ".env.production" # Only active in production
  presets:
    minify_all:
      extensions: [".js", ".css", ".html"]
      actions: ["minify", "strip_comments"]
```

### Multiple Preset Files

```bash
# Files are merged in order (later files override earlier ones)
python tools/m1f.py -s . -o out.txt \
  --preset base.yml \
  --preset project.yml \
  --preset overrides.yml
```

### Preset Locations

1. **Project presets**: `./presets/*.m1f-presets.yml`
2. **Local preset**: `./.m1f-presets.yml`
3. **User presets**: `~/.m1f/*.m1f-presets.yml`
4. **Specified presets**: Via `--preset` flag

## Debugging Presets

### Verbose Mode

```bash
python tools/m1f.py -s . -o out.txt --preset my.yml --verbose
```

Shows:

- Which preset is applied to each file
- Which actions are performed
- Processing time for each action

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
      security_check: "abort"

    # Documentation
    docs:
      extensions: [".md", ".mdx"]
      actions: ["compress_whitespace", "remove_empty_lines"]

    # Configuration files
    config:
      patterns: ["*.json", "*.yml", "*.yaml"]
      security_check: "abort"
      custom_processor: "redact_secrets"
```

### Data Science Preset

```yaml
data_science:
  presets:
    # Notebooks - extract code cells only (Note: extract_code_cells is an example)
    notebooks:
      extensions: [".ipynb"]
      custom_processor: "extract_code_cells" # This processor would need to be implemented

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

## Best Practices

1. **Start Simple** - Begin with basic actions, add complexity as needed
2. **Test Thoroughly** - Use verbose mode to verify behavior
3. **Layer Presets** - Use multiple files for base + overrides
4. **Document Presets** - Add descriptions to groups and complex presets
5. **Version Control** - Keep presets in your repository
6. **Performance First** - Apply expensive actions only where needed

## Migration from Legacy Format

If you have old `processors` format presets:

```yaml
# Old format
processors:
  remove_empty_lines:
    extensions: [".md"]

# Convert to new format
my_group:
  presets:
    markdown_files:
      extensions: [".md"]
      actions: ["remove_empty_lines"]
```
