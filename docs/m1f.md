# m1f (Make One File)

A modern, high-performance tool that combines multiple files into a single file
with rich metadata, content deduplication, and async I/O support.

## Overview

The m1f tool (v2.0.0) solves a common challenge when working with LLMs:
providing sufficient context without exceeding token limits. Built with Python
3.10+ and modern architecture patterns, it creates optimized reference files
from multiple sources while automatically handling duplicates and providing
comprehensive metadata.

## Key Features

- **Content Deduplication**: Automatically detects and skips duplicate files
  based on SHA256 checksums
- **Async I/O**: High-performance file operations with concurrent processing
- **Type Safety**: Full type annotations throughout the codebase
- **Modern Architecture**: Modular package structure with clean separation of
  concerns
- **Smart Filtering**: Advanced file filtering with size limits, extensions, and
  patterns
- **Symlink Support**: Intelligent symlink handling with cycle detection
- **Professional Security**: Integration with detect-secrets for sensitive data
  detection
- **Colorized Output**: Beautiful console output with progress indicators

## Quick Start

```bash
# Basic usage with a source directory
python -m tools.m1f -s ./your_project -o ./combined.txt

# Include only specific file types
python -m tools.m1f -s ./your_project -o ./combined.txt --include-extensions .py .js .md

# Exclude specific directories
python -m tools.m1f -s ./your_project -o ./combined.txt --excludes "node_modules/" "build/" "dist/"

# Filter by file size (new in v2.0.0)
python -m tools.m1f -s ./your_project -o ./combined.txt --max-file-size 50KB
```

## Command Line Options

| Option                      | Description                                                                                                                                                                                                                                                      |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `-s, --source-directory`    | Path to the directory containing files to process                                                                                                                                                                                                                |
| `-i, --input-file`          | Path to a file containing a list of files/directories to process. Can be used together with --source-directory to resolve relative paths in the input file against the source directory                                                                          |
| `-o, --output-file`         | Path for the combined output file                                                                                                                                                                                                                                |
| `-f, --force`               | Force overwrite of existing output file without prompting                                                                                                                                                                                                        |
| `-t, --add-timestamp`       | Add a timestamp (\_YYYYMMDD_HHMMSS) to the output filename. Useful for versioning and preventing accidental overwrite of previous output files                                                                                                                   |
| `--filename-mtime-hash`     | Append a hash of file modification timestamps to the filename. The hash is created using all filenames and their modification dates, enabling caching mechanisms. Hash only changes when files are added/removed or their content changes                        |
| `--include-extensions`      | Space-separated list of file extensions to include (e.g., `--include-extensions .py .js .html` will only process files with these extensions)                                                                                                                    |
| `--exclude-extensions`      | Space-separated list of file extensions to exclude (e.g., `--exclude-extensions .log .tmp .bak` will skip these file types)                                                                                                                                      |
| `--max-file-size`           | Skip files larger than the specified size (e.g., `--max-file-size 50KB` will exclude files over 50 kilobytes). Supports units: B, KB, MB, GB, TB. Useful for filtering out large generated files, logs, or binary data when merging text files for LLM context   |
| `--exclude-paths-file`      | Path to file containing paths or patterns to exclude. Supports both exact path lists and gitignore-style pattern formats. Can use a .gitignore file directly                                                                                                     |
| `--no-default-excludes`     | Disable default directory exclusions. By default, the following directories are excluded: vendor, node_modules, build, dist, cache, .git, .svn, .hg, \***\*pycache\*\***                                                                                         |
| `--excludes`                | Space-separated list of paths to exclude. Supports directory names, exact file paths, and gitignore-style patterns (e.g., `--excludes logs "config/settings.json" "*.log" "build/" "!important.log"`)                                                            |
| `--include-dot-paths`       | Include files and directories that start with a dot (e.g., .gitignore, .hidden/). By default, all dot files and directories are excluded.                                                                                                                        |
| `--include-binary-files`    | Attempt to include files with binary extensions                                                                                                                                                                                                                  |
| `--remove-scraped-metadata` | Remove scraped metadata (URL, timestamp) from HTML2MD files during processing. Automatically detects and removes metadata blocks at the end of markdown files created by HTML scraping tools                                                                     |
| `--separator-style`         | Style of separators between files (`Standard`, `Detailed`, `Markdown`, `MachineReadable`, `None`)                                                                                                                                                                |
| `--line-ending`             | Line ending for script-generated separators (`lf` or `crlf`)                                                                                                                                                                                                     |
| `--convert-to-charset`      | Convert all files to the specified character encoding (`utf-8` [default], `utf-16`, `utf-16-le`, `utf-16-be`, `ascii`, `latin-1`, `cp1252`). The original encoding is automatically detected and included in the metadata when using compatible separator styles |
| `--abort-on-encoding-error` | Abort processing if encoding conversion errors occur. Without this flag, characters that cannot be represented will be replaced                                                                                                                                  |
| `-v, --verbose`             | Enable verbose logging. Without this flag, only summary information is shown, and detailed file-by-file logs are written to the log file instead of the console                                                                                                  |
| `--minimal-output`          | Generate only the combined output file (no auxiliary files)                                                                                                                                                                                                      |
| `--skip-output-file`        | Execute operations but skip writing the final output file                                                                                                                                                                                                        |
| `-q, --quiet`               | Suppress all console output                                                                                                                                                                                                                                      |
| `--create-archive`          | Create a backup archive of all processed files                                                                                                                                                                                                                   |
| `--archive-type`            | Type of archive to create (`zip` or `tar.gz`)                                                                                                                                                                                                                    |
| `--security-check`          | Scan files for secrets before merging (`abort`, `skip`, `warn`)                                                                                                                                                                                                  |

## Usage Examples

### Basic Operations

```bash
# Basic command using a source directory
python -m tools.m1f --source-directory /path/to/your/code \
  --output-file /path/to/combined_output.txt

# Using an input file containing paths to process (one per line)
python -m tools.m1f -i filelist.txt -o combined_output.txt

# Using both source directory and input file together
python -m tools.m1f -s ./source_code -i ./file_list.txt -o ./combined.txt

# Remove scraped metadata from HTML2MD files (new in v2.0.0)
python -m tools.m1f -s ./scraped_docs -o ./clean_docs.txt \
  --include-extensions .md --remove-scraped-metadata
```

### Advanced Operations

```bash
# Using MachineReadable style with verbose logging
python -m tools.m1f -s ./my_project -o ./output/bundle.m1f.txt \
  --separator-style MachineReadable --force --verbose

# Creating a combined file and a backup zip archive
python -m tools.m1f -s ./source_code -o ./dist/combined.txt \
  --create-archive --archive-type zip

# Only include text files under 50KB to avoid large generated files
python -m tools.m1f -s ./project -o ./text_only.txt \
  --max-file-size 50KB --include-extensions .py .js .md .txt .json

# Handle symlinks with cycle detection (new in v2.0.0)
python -m tools.m1f -s ./project -o ./output.txt \
  --include-symlinks --verbose
```

## Security Check

The `--security-check` option scans files for potential secrets using
`detect-secrets` if the library is installed. When secrets are detected you can
decide how the script proceeds:

- `abort` – stop processing immediately and do not create the output file.
- `skip` – omit files that contain secrets from the final output.
- `warn` – include all files but print a summary warning at the end.

If `detect-secrets` is not available, a simplified pattern-based scan is used as
a fallback.

## Output Files

By default, `m1f.py` creates several output files to provide comprehensive
information about the processed files:

1. **Primary output file** - The combined file specified by `--output-file`
   containing all processed files with separators
2. **Log file** - A `.log` file with the same base name as the output file,
   containing detailed processing information
3. **File list** - A `_filelist.txt` file containing the paths of all included
   files
4. **Directory list** - A `_dirlist.txt` file containing all unique directories
   from the included files
5. **Archive file** - An optional backup archive (zip or tar.gz) if
   `--create-archive` is specified

To create only the primary output file and skip the auxiliary files, use the
`--minimal-output` option:

```bash
# Create only the combined output file without any auxiliary files
python tools/m1f.py -s ./src -o ./combined.txt --minimal-output
```

## Common Use Cases

### Documentation Compilation

```bash
# Create a complete documentation bundle from all markdown files
python tools/m1f.py -s ./docs -o ./doc_bundle.m1f.txt --include-extensions .md
```

### Code Review Preparation

```bash
# Bundle specific components for code review
python tools/m1f.py -i code_review_files.txt -o ./review_bundle.m1f.txt
```

### WordPress Development

```bash
# Combine theme or plugin files for AI analysis
python tools/m1f.py -s ./wp-content/themes/my-theme -o ./theme_context.m1f.txt \
  --include-extensions .php .js .css --exclude-paths-file ./exclude_build_files.txt
```

### Project Knowledge Base

```bash
# Create a searchable knowledge base from project documentation
python tools/m1f.py -s ./project -o ./knowledge_base.m1f.txt \
  --include-extensions .md .txt .rst --minimal-output
```

### HTML2MD Integration

```bash
# Combine scraped markdown files and remove metadata
python tools/m1f.py -s ./scraped_content -o ./clean_content.m1f.txt \
  --include-extensions .md --remove-scraped-metadata

# Merge multiple scraped websites into a clean documentation bundle
python tools/m1f.py -s ./web_content -o ./web_docs.m1f.txt \
  --include-extensions .md --remove-scraped-metadata --separator-style Markdown
```

## Separator Styles

The `--separator-style` option allows you to choose how files are separated in
the combined output file. Each style is designed for specific use cases, from
human readability to automated parsing.

### Standard Style

A simple, concise separator that shows the file path and optional checksum:

```
======= path/to/file.py | CHECKSUM_SHA256: abcdef1234567890... ======
```

### Detailed Style (Default)

A more comprehensive separator that includes file metadata:

```
========================================================================================
== FILE: path/to/file.py
== DATE: 2023-06-15 14:30:21 | SIZE: 2.50 KB | TYPE: .py
== CHECKSUM_SHA256: abcdef1234567890...
========================================================================================
```

### Markdown Style

Formats the metadata as Markdown with proper code blocks, using the file
extension to set syntax highlighting:

````markdown
## path/to/file.py

**Date Modified:** 2023-06-15 14:30:21 | **Size:** 2.50 KB | **Type:** .py |
**Checksum (SHA256):** abcdef1234567890...

```python
# File content starts here
def example():
    return "Hello, world!"
```
````

### MachineReadable Style

A robust format designed for reliable automated parsing and processing:

```text
--- PYMK1F_BEGIN_FILE_METADATA_BLOCK_12345678-1234-1234-1234-123456789abc ---
METADATA_JSON:
{
    "original_filepath": "path/to/file.py",
    "original_filename": "file.py",
    "timestamp_utc_iso": "2023-06-15T14:30:21Z",
    "type": ".py",
    "size_bytes": 2560,
    "checksum_sha256": "abcdef1234567890..."
}
--- PYMK1F_END_FILE_METADATA_BLOCK_12345678-1234-1234-1234-123456789abc ---
--- PYMK1F_BEGIN_FILE_CONTENT_BLOCK_12345678-1234-1234-1234-123456789abc ---

# File content here

--- PYMK1F_END_FILE_CONTENT_BLOCK_12345678-1234-1234-1234-123456789abc ---
```

### None Style

Files are concatenated directly without any separators between them.

## Additional Notes

### Binary File Handling

While the script can include binary files using the `--include-binary-files`
option, these are read as text (UTF-8 with error ignoring). This can result in
garbled/unreadable content in the output and significantly increase file size.

### Encoding Behavior

The script uses UTF-8 as the default encoding for reading and writing files.
When using `--convert-to-charset`, the original encoding of each file is
automatically detected and recorded in the file metadata.

### Line Ending Behavior

The `--line-ending` option only affects the line endings generated by the script
(in separators and blank lines), not those in the original files. The line
endings of original files remain unchanged.

### Archive Creation

When `--create-archive` is used, the archive will contain all files selected for
inclusion in the main output file, using their relative paths within the
archive.

### Architecture (v2.0.0)

The m1f tool has been completely rewritten as a modular Python package:

```
tools/m1f/
├── __init__.py          # Package initialization
├── cli.py               # Command-line interface
├── core.py              # Main orchestration logic
├── config.py            # Configuration management
├── constants.py         # Constants and enums
├── exceptions.py        # Custom exceptions
├── file_processor.py    # File handling with async I/O
├── encoding_handler.py  # Smart encoding detection
├── security_scanner.py  # Secret detection integration
├── output_writer.py     # Output generation
├── archive_creator.py   # Archive functionality
├── separator_generator.py # Separator formatting
├── logging.py           # Structured logging
└── utils.py             # Utility functions
```

### Performance Considerations

With the new async I/O architecture, m1f can handle large projects more
efficiently:

- Concurrent file reading and processing
- Memory-efficient streaming for large files
- Smart caching to avoid redundant operations
- Content deduplication saves space and processing time

For extremely large directories with tens of thousands of files or very large
individual files, the script might take some time to process.
