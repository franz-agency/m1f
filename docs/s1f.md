# s1f (Split One File)

Extracts individual files from a combined file, recreating the original directory structure.

## Overview

The s1f tool is the counterpart to m1f, designed to extract and reconstruct the original files from a combined file. This tool is essential for workflows where you need to retrieve individual files after analysis or when sharing combined files with collaborators.

## Key Features

- Preserves original file paths and timestamps
- Verifies file integrity with SHA256 checksums
- Supports all m1f separator styles
- Simple and secure extraction process

## Quick Start

```bash
# Basic extraction
python tools/s1f.py -i ./combined.txt -d ./extracted_files

# Force overwrite of existing files
python tools/s1f.py -i ./combined.txt -d ./extracted_files -f

# Verbose output to see detailed extraction progress
python tools/s1f.py -i ./combined.txt -d ./extracted_files -v
```

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
python tools/s1f.py --input-file /path/to/combined_output.txt \
  --destination-directory /path/to/output_folder

# Splitting a MachineReadable file with force overwrite and verbose output
python tools/s1f.py -i ./output/bundle.m1f.txt -d ./extracted_project -f -v
```

### Advanced Operations

```bash
# Using current system time for timestamps
python tools/s1f.py -i ./combined_file.txt -d ./extracted_files \
  --timestamp-mode current

# Preserving original file encodings
python tools/s1f.py -i ./with_encodings.txt -d ./extracted_files \
  --respect-encoding

# Using a specific encoding for all extracted files
python tools/s1f.py -i ./combined_file.txt -d ./extracted_files \
  --target-encoding utf-8

# Ignoring checksum verification (when files were intentionally modified)
python tools/s1f.py -i ./modified_bundle.m1f.txt -d ./extracted_files \
  --ignore-checksum
```

## Supported File Formats

The s1f tool can extract files from combined files created with any of the m1f separator styles:

- **Standard Style** - Simple separators with file paths and checksums
- **Detailed Style** - Comprehensive separators with full metadata
- **Markdown Style** - Formatted with Markdown syntax for documentation
- **MachineReadable Style** - Structured format with JSON metadata and UUID boundaries
- **None Style** - Files combined without separators (limited extraction capability)

For the most reliable extraction, use files created with the MachineReadable separator style, as these contain complete metadata and checksums for verification.

## Common Workflows

### Extract and Verify

This workflow is useful when you want to ensure the integrity of extracted files:

```bash
# Step 1: Extract the files with verification
python tools/s1f.py -i ./project_bundle.m1f.txt -d ./extracted_project -v

# Step 2: Check for any checksum errors in the output
# If any errors are reported, consider using --ignore-checksum if appropriate
```

### Multiple Extraction Targets

When you need to extract the same combined file to different locations:

```bash
# Extract for development
python tools/s1f.py -i ./project.m1f.txt -d ./dev_workspace

# Extract for backup with original timestamps
python tools/s1f.py -i ./project.m1f.txt -d ./backup --timestamp-mode original
``` 