# s1f (Split One File)

A modern file extraction tool with async I/O that reconstructs original files from combined archives with full metadata preservation.

## Overview

The s1f tool (v2.0.0) is the counterpart to m1f, designed to extract and reconstruct
original files from a combined file. Built with Python 3.10+ and modern async architecture,
it ensures reliable extraction with checksum verification and proper encoding handling.

## Key Features

- **Async I/O**: High-performance concurrent file writing
- **Smart Parser Framework**: Automatic format detection with dedicated parsers
- **Type Safety**: Full type annotations throughout the codebase
- **Modern Architecture**: Clean modular design with dependency injection
- **Checksum Verification**: SHA256 integrity checking with line ending normalization
- **Encoding Support**: Intelligent encoding detection and conversion
- **Error Recovery**: Graceful fallbacks and detailed error reporting
- **Progress Tracking**: Real-time extraction statistics

## Quick Start

```bash
# Basic extraction
python -m tools.s1f -i ./combined.txt -d ./extracted_files

# Force overwrite of existing files
python -m tools.s1f -i ./combined.txt -d ./extracted_files -f

# Verbose output to see detailed extraction progress
python -m tools.s1f -i ./combined.txt -d ./extracted_files -v

# Extract with specific encoding (new in v2.0.0)
python -m tools.s1f -i ./combined.txt -d ./extracted_files --target-encoding utf-16-le
```

## Architecture

S1F v2.0.0 features a modern, modular architecture:

```
tools/s1f/
├── __init__.py       # Package initialization
├── __main__.py       # Entry point for module execution
├── cli.py            # Command-line interface
├── config.py         # Configuration management
├── core.py           # Core extraction logic with async I/O
├── exceptions.py     # Custom exceptions
├── logging.py        # Structured logging
├── models.py         # Data models (ExtractedFile, etc.)
├── parsers.py        # Abstract parser framework
├── utils.py          # Utility functions
└── writers.py        # Output writers (file, stdout)
```

### Key Components

- **Async I/O**: Concurrent file operations for better performance
- **Parser Framework**: Extensible system for handling different file formats
- **Type Safety**: Full type hints and dataclass models
- **Clean Architecture**: Separation of concerns with dependency injection

## Command Line Options

| Option                        | Description                                                                                                                                                                                                   |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `-i, --input-file`            | Path to the combined input file                                                                                                                                                                               |
| `-d, --destination-directory` | Directory where extracted files will be saved                                                                                                                                                                 |
| `-f, --force`                 | Force overwrite of existing files without prompting                                                                                                                                                           |
| `-v, --verbose`               | Enable verbose output                                                                                                                                                                                         |
| `--timestamp-mode`            | How to set file timestamps (`original` or `current`). Original preserves timestamps from when files were combined, current uses the current time                                                              |
| `--ignore-checksum`           | Skip checksum verification for MachineReadable files. Useful when files were intentionally modified after being combined                                                                                      |
| `--respect-encoding`          | Try to use the original file encoding when writing extracted files. If enabled and original encoding information is available, files will be written using that encoding instead of UTF-8                     |
| `--target-encoding`           | Explicitly specify the character encoding to use for all extracted files (e.g., `utf-8`, `latin-1`, `utf-16-le`). This overrides the `--respect-encoding` option and any encoding information in the metadata |

## Usage Examples

### Basic Operations

```bash
# Basic command
python -m tools.s1f --input-file /path/to/combined_output.txt \
  --destination-directory /path/to/output_folder

# Splitting a MachineReadable file with force overwrite and verbose output
python -m tools.s1f -i ./output/bundle.m1f.txt -d ./extracted_project -f -v
```

### Advanced Operations

```bash
# Using current system time for timestamps
python -m tools.s1f -i ./combined_file.txt -d ./extracted_files \
  --timestamp-mode current

# Preserving original file encodings
python -m tools.s1f -i ./with_encodings.txt -d ./extracted_files \
  --respect-encoding

# Using a specific encoding for all extracted files
python -m tools.s1f -i ./combined_file.txt -d ./extracted_files \
  --target-encoding utf-8

# Ignoring checksum verification (when files were intentionally modified)
python -m tools.s1f -i ./modified_bundle.m1f.txt -d ./extracted_files \
  --ignore-checksum
```

## Supported File Formats

The s1f tool can extract files from combined files created with any of the m1f
separator styles:

- **Standard Style** - Simple separators with file paths and checksums
- **Detailed Style** - Comprehensive separators with full metadata
- **Markdown Style** - Formatted with Markdown syntax for documentation
- **MachineReadable Style** - Structured format with JSON metadata and UUID
  boundaries
- **None Style** - Files combined without separators (limited extraction
  capability)

For the most reliable extraction, use files created with the MachineReadable
separator style, as these contain complete metadata and checksums for
verification.

## Common Workflows

### Extract and Verify

This workflow is useful when you want to ensure the integrity of extracted
files:

```bash
# Step 1: Extract the files with verification
python -m tools.s1f -i ./project_bundle.m1f.txt -d ./extracted_project -v

# Step 2: Check for any checksum errors in the output
# If any errors are reported, consider using --ignore-checksum if appropriate
```

### Multiple Extraction Targets

When you need to extract the same combined file to different locations:

```bash
# Extract for development
python -m tools.s1f -i ./project.m1f.txt -d ./dev_workspace

# Extract for backup with original timestamps
python -m tools.s1f -i ./project.m1f.txt -d ./backup --timestamp-mode original
```

## Performance

S1F v2.0.0 includes significant performance improvements:

- **Async I/O**: Concurrent file writing for 3-5x faster extraction on SSDs
- **Optimized Parsing**: Efficient line-by-line processing with minimal memory usage
- **Smart Buffering**: Adaptive buffer sizes based on file characteristics

## Error Handling

The tool provides comprehensive error handling:

- **Checksum Verification**: Automatic integrity checking with clear error messages
- **Encoding Fallbacks**: Graceful handling of encoding issues with multiple fallback strategies
- **Permission Errors**: Clear reporting of file system permission issues
- **Partial Recovery**: Continue extraction even if individual files fail
