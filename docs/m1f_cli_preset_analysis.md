# m1f CLI Parameters vs Preset System Analysis

## Overview

This document analyzes all m1f CLI parameters and their support in the preset
system.

## CLI Parameters Analysis

### Input/Output Options

| Parameter                | Description                          | Preset Support   | Notes             |
| ------------------------ | ------------------------------------ | ---------------- | ----------------- |
| `-s, --source-directory` | Path to directory containing files   | ❌ Not supported | Runtime parameter |
| `-i, --input-file`       | Path to file with list of files/dirs | ❌ Not supported | Runtime parameter |
| `-o, --output-file`      | Output file path                     | ❌ Not supported | Runtime parameter |
| `--input-include-files`  | Files to include at beginning        | ❌ Not supported | Runtime parameter |

### Output Formatting

| Parameter               | Description                       | Preset Support   | Notes                           |
| ----------------------- | --------------------------------- | ---------------- | ------------------------------- |
| `--separator-style`     | Format of separator between files | ✅ Supported     | Can be set globally or per-file |
| `--line-ending`         | Line ending style (lf/crlf)       | ✅ Supported     | Global setting only             |
| `-t, --add-timestamp`   | Add timestamp to filename         | ❌ Not supported | Runtime parameter               |
| `--filename-mtime-hash` | Add hash of mtimes to filename    | ❌ Not supported | Runtime parameter               |

### File Filtering

| Parameter                   | Description                   | Preset Support         | Notes                        |
| --------------------------- | ----------------------------- | ---------------------- | ---------------------------- |
| `--excludes`                | Paths/patterns to exclude     | ✅ Partially supported | Global exclude_patterns only |
| `--exclude-paths-file`      | File with paths to exclude    | ❌ Not supported       | Could be useful in presets   |
| `--include-extensions`      | Include only these extensions | ✅ Supported           | Global setting               |
| `--exclude-extensions`      | Exclude these extensions      | ✅ Supported           | Global setting               |
| `--include-dot-paths`       | Include dot files/dirs        | ❌ Not supported       | Could be useful in presets   |
| `--include-binary-files`    | Include binary files          | ❌ Not supported       | Could be useful in presets   |
| `--include-symlinks`        | Follow symlinks               | ❌ Not supported       | Could be useful in presets   |
| `--max-file-size`           | Skip large files              | ❌ Not supported       | Could be useful in presets   |
| `--no-default-excludes`     | Disable default exclusions    | ❌ Not supported       | Could be useful in presets   |
| `--remove-scraped-metadata` | Remove HTML2MD metadata       | ❌ Not supported       | Could be useful in presets   |

### Character Encoding

| Parameter                   | Description              | Preset Support   | Notes                      |
| --------------------------- | ------------------------ | ---------------- | -------------------------- |
| `--convert-to-charset`      | Target encoding          | ✅ Supported     | Global encoding setting    |
| `--abort-on-encoding-error` | Abort on encoding errors | ❌ Not supported | Could be useful in presets |

### Security Options

| Parameter          | Description              | Preset Support   | Notes                      |
| ------------------ | ------------------------ | ---------------- | -------------------------- |
| `--security-check` | Check for sensitive info | ❌ Not supported | Could be useful in presets |

### Archive Options

| Parameter          | Description                 | Preset Support   | Notes             |
| ------------------ | --------------------------- | ---------------- | ----------------- |
| `--create-archive` | Create backup archive       | ❌ Not supported | Runtime parameter |
| `--archive-type`   | Archive format (zip/tar.gz) | ❌ Not supported | Runtime parameter |

### Output Control

| Parameter            | Description               | Preset Support   | Notes             |
| -------------------- | ------------------------- | ---------------- | ----------------- |
| `-f, --force`        | Force overwrite           | ❌ Not supported | Runtime parameter |
| `--minimal-output`   | Only create combined file | ❌ Not supported | Runtime parameter |
| `--skip-output-file` | Skip main output file     | ❌ Not supported | Runtime parameter |
| `-v, --verbose`      | Verbose output            | ❌ Not supported | Runtime parameter |
| `-q, --quiet`        | Suppress output           | ❌ Not supported | Runtime parameter |

### Preset Configuration

| Parameter           | Description           | Preset Support | Notes                 |
| ------------------- | --------------------- | -------------- | --------------------- |
| `--preset`          | Preset config files   | N/A            | This loads presets    |
| `--preset-group`    | Specific preset group | N/A            | This selects presets  |
| `--disable-presets` | Disable all presets   | N/A            | This disables presets |

## Currently Supported in Presets

### Global Settings (GlobalSettings class)

- `encoding` - Target encoding (maps to --convert-to-charset)
- `separator_style` - Default separator style (maps to --separator-style)
- `line_ending` - Line ending style (maps to --line-ending)
- `include_patterns` - Include glob patterns (partial)
- `exclude_patterns` - Exclude glob patterns (partial --excludes)
- `include_extensions` - Include file extensions (maps to --include-extensions)
- `exclude_extensions` - Exclude file extensions (maps to --exclude-extensions)
- `extension_settings` - Per-extension defaults

### File Presets (FilePreset class)

- `patterns` - Glob patterns for matching files
- `extensions` - File extensions to match
- `actions` - Processing actions (minify, strip_tags, etc.)
- `strip_tags` - HTML tags to strip
- `preserve_tags` - Tags to preserve
- `separator_style` - Override separator for specific files
- `include_metadata` - Whether to include metadata
- `max_lines` - Truncate after N lines
- `custom_processor` - Custom processing function
- `processor_args` - Arguments for custom processor

## Missing Parameters That Should Be Added

### High Priority (Commonly Used)

1. **`include_dot_paths`** - Should be in GlobalSettings
2. **`include_binary_files`** - Should be in GlobalSettings
3. **`max_file_size`** - Should be in GlobalSettings
4. **`no_default_excludes`** - Should be in GlobalSettings
5. **`remove_scraped_metadata`** - Should be in GlobalSettings or FilePreset
6. **`security_check`** - Should be in GlobalSettings
7. **`abort_on_encoding_error`** - Should be in GlobalSettings

### Medium Priority (Useful for Specific Cases)

1. **`include_symlinks`** - Should be in GlobalSettings
2. **`exclude_paths_file`** - Could reference a file in GlobalSettings

### Low Priority (Runtime Specific)

These parameters are inherently runtime-specific and don't make sense in
presets:

- Source/input/output paths
- Timestamps and hashes
- Archive creation
- Force overwrite
- Verbose/quiet modes
- Minimal output options

## Recommended Additions to Preset System

### 1. Update GlobalSettings class

```python
@dataclass
class GlobalSettings:
    # Existing fields...

    # New fields to add:
    include_dot_paths: bool = False
    include_binary_files: bool = False
    include_symlinks: bool = False
    max_file_size: Optional[str] = None  # e.g., "10MB"
    no_default_excludes: bool = False
    remove_scraped_metadata: bool = False
    security_check: Optional[str] = None  # "abort", "skip", "warn"
    abort_on_encoding_error: bool = False
    exclude_paths_file: Optional[str] = None  # Path to exclusion file
```

### 2. Update FilePreset class

```python
@dataclass
class FilePreset:
    # Existing fields...

    # New fields to add:
    remove_scraped_metadata: bool = False  # Per-file override
    max_file_size: Optional[str] = None  # Per-file size limit
```

### 3. Update preset loading logic

The preset system needs to:

- Apply global settings to the FileProcessor configuration
- Merge preset settings with CLI arguments (CLI takes precedence)
- Support loading exclude patterns from files referenced in presets

## Conclusion

The preset system currently supports about 30% of the meaningful CLI parameters.
Adding support for the high-priority parameters would increase this to about
70%, making presets much more powerful for common use cases like:

- Documentation processing (remove metadata, exclude binaries)
- Code bundling (include dot files, security checks)
- Large project processing (file size limits, custom exclusions)

The remaining 30% are runtime-specific parameters that appropriately remain as
CLI-only options.
