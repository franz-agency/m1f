# Per-File-Type Settings in m1f Presets

The m1f preset system supports fine-grained control over processing settings on
a per-file-type basis. This allows you to apply different rules to different
file types within the same bundle.

## Overview

You can override almost any m1f setting for specific file extensions or
patterns. This is particularly useful for:

- Disabling security checks for documentation while keeping them for code
- Setting different size limits for CSS vs PHP files
- Applying different processing rules based on file type
- Handling sensitive files differently from public files

## Supported Per-File Settings

The following settings can be overridden on a per-file basis:

### Processing Settings

- `actions` - List of processing actions (minify, strip_comments, etc.)
- `strip_tags` - HTML tags to remove
- `preserve_tags` - HTML tags to preserve
- `separator_style` - Override separator style for specific files
- `include_metadata` - Whether to include file metadata
- `max_lines` - Truncate after N lines

### Security & Filtering

- `security_check` - Override security scanning (`"abort"`, `"skip"`, `"warn"`,
  `null`)
- `max_file_size` - File-specific size limit (e.g., `"50KB"`, `"5MB"`)
- `remove_scraped_metadata` - Remove HTML2MD metadata for specific files
- `include_dot_paths` - Include hidden files for this type
- `include_binary_files` - Include binary files for this type

### Custom Processing

- `custom_processor` - Name of custom processor to use
- `processor_args` - Arguments for the custom processor

## Configuration Methods

### Method 1: Global Extension Settings

Define defaults for all files of a specific extension:

```yaml
my_project:
  global_settings:
    # Default settings for all files
    security_check: "abort"
    max_file_size: "1MB"

    # Extension-specific overrides
    extensions:
      .md:
        security_check: null # Disable for markdown
        remove_scraped_metadata: true
        max_file_size: "500KB"

      .php:
        security_check: "abort" # Keep strict for PHP
        max_file_size: "5MB"
        actions: [strip_comments]

      .css:
        max_file_size: "50KB" # Strict limit for CSS
        actions: [minify, strip_comments]

      .env:
        security_check: "abort"
        include_dot_paths: true # Include .env files
        max_file_size: "10KB"
```

### Method 2: Preset-Specific Settings

Define settings for files matching specific patterns:

```yaml
my_project:
  presets:
    documentation:
      extensions: [".md", ".rst", ".txt"]
      patterns: ["docs/**/*", "README*"]
      security_check: null # No security check
      remove_scraped_metadata: true
      max_file_size: "1MB"

    sensitive_files:
      extensions: [".env", ".key", ".pem"]
      patterns: ["config/**/*", "secrets/**/*"]
      security_check: "abort"
      max_file_size: "50KB"
      include_dot_paths: true

    vendor_code:
      patterns: ["vendor/**/*", "node_modules/**/*"]
      security_check: null # Don't check third-party code
      max_file_size: "100KB" # Only include small files
      actions: [] # No processing
```

## Real-World Examples

### Example 1: Web Project with Mixed Content

```yaml
web_project:
  global_settings:
    # Defaults
    security_check: "warn"
    max_file_size: "2MB"

    extensions:
      # Documentation - relaxed rules
      .md:
        security_check: null
        remove_scraped_metadata: true
        actions: [remove_empty_lines]

      # Frontend - strict size limits
      .css:
        max_file_size: "50KB"
        security_check: "skip"
        actions: [minify]

      .js:
        max_file_size: "100KB"
        security_check: "warn"
        actions: [strip_comments, compress_whitespace]

      # Backend - larger files, strict security
      .php:
        max_file_size: "5MB"
        security_check: "abort"
        actions: [strip_comments]

      # Data files - very different handling
      .sql:
        max_file_size: "10MB"
        security_check: null
        max_lines: 1000 # Truncate large dumps
```

### Example 2: Documentation Project

```yaml
documentation:
  global_settings:
    # Default: include everything for docs
    security_check: null
    remove_scraped_metadata: true

    extensions:
      # Markdown files
      .md:
        actions: [remove_empty_lines]
        separator_style: "Markdown"

      # Code examples in docs
      .py:
        max_lines: 50 # Keep examples short
        actions: [strip_comments]

      # Config examples
      .json:
        actions: [compress_whitespace]
        max_lines: 30

      # Log file examples
      .log:
        max_file_size: "100KB"
        max_lines: 100
```

### Example 3: Security-Focused Configuration

```yaml
secure_project:
  global_settings:
    # Very strict by default
    security_check: "abort"
    abort_on_encoding_error: true

    extensions:
      # Public documentation - can be relaxed
      .md:
        security_check: null

      # Code files - different levels
      .js:
        security_check: "warn" # Client-side code

      .php:
        security_check: "abort" # Server-side code

      .env:
        security_check: "abort"
        max_file_size: "10KB" # Env files should be small

      # Config files - careful handling
      .json:
        security_check: "warn"
        actions: [custom]
        custom_processor: "redact_secrets"
```

## Priority and Precedence

When multiple settings could apply to a file, they are resolved in this order:

1. **File-specific preset settings** (highest priority)
   - Settings in a preset that matches the file
2. **Global extension settings**
   - Settings in `global_settings.extensions`
3. **Global defaults** (lowest priority)
   - Settings in `global_settings`

Example:

```yaml
my_project:
  global_settings:
    max_file_size: "1MB" # Default for all

    extensions:
      .js:
        max_file_size: "500KB" # Override for JS files

  presets:
    vendor_js:
      patterns: ["vendor/**/*.js"]
      max_file_size: "2MB" # Override for vendor JS (highest priority)
```

## Best Practices

1. **Start with sensible defaults** in `global_settings`
2. **Use extension settings** for broad file-type rules
3. **Use presets** for location or context-specific overrides
4. **Document your choices** with comments
5. **Test incrementally** with `--verbose` to see which rules apply

## Limitations

- Settings cascade down but don't merge collections (e.g., `actions` lists
  replace, not extend)
- Some settings only make sense for certain file types
- Binary file detection happens before preset processing

## See Also

- [Preset System Guide](02_m1f_presets.md) - General preset documentation
- [Preset Template](../../presets/template-all-settings.m1f-presets.yml) - Complete
  example with all settings
- [Use Case Examples](../../presets/example-use-cases.m1f-presets.yml) - Real-world
  scenarios
