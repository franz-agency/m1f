# m1f CLI Reference

This is a comprehensive reference for all command-line parameters and flags
available in m1f v3.2.0.

## Synopsis

```bash
m1f [-h] [--version] [-s DIR] [-i FILE] -o FILE
    [--input-include-files [FILE ...]]
    [--separator-style {Standard,Detailed,Markdown,MachineReadable,None}]
    [--line-ending {lf,crlf}] [-t] [--filename-mtime-hash]
    [--excludes [PATTERN ...]] [--exclude-paths-file FILE ...]
    [--include-paths-file FILE ...]
    [--include-extensions [EXT ...]] [--exclude-extensions [EXT ...]]
    [--include-dot-paths] [--include-binary-files] [--include-symlinks]
    [--max-file-size SIZE] [--no-default-excludes]
    [--remove-scraped-metadata]
    [--convert-to-charset {utf-8,utf-16,utf-16-le,utf-16-be,ascii,latin-1,cp1252}]
    [--abort-on-encoding-error] [--no-prefer-utf8-for-text-files]
    [--security-check {error,warn,skip}]
    [--create-archive] [--archive-type {zip,tar.gz}] [-f]
    [--minimal-output] [--skip-output-file] [--allow-duplicate-files]
    [-v] [-q]
    [--preset FILE [FILE ...]] [--preset-group GROUP]
    [--disable-presets]
```

## General Options

### `--help`, `-h`

Show help message and exit.

### `--version`

Show program version and exit. Current version: v3.2.0

## Input/Output Options

### `--source-directory DIR`, `-s DIR`

Path to the directory containing files to combine. Can be used multiple times to
process multiple directories.

### `--input-file FILE`, `-i FILE`

Path to a text file containing a list of files/directories to process, one per
line. These files are explicitly included and bypass all filter rules.

**Note**: At least one of `-s` (source directory) or `-i` (input file) must be
specified. When using `-i` alone, relative paths in the input file are resolved
relative to the current working directory. When both `-s` and `-i` are used,
relative paths in the input file are resolved relative to the source directory.

Example input file:

```
# Comments are supported
src/main.py          # Relative to source directory
/absolute/path.txt   # Absolute path
docs/**/*.md         # Glob patterns supported
```

**Merging multiple file lists with Bash**:

```bash
# Create temporary merged file
cat files1.txt files2.txt files3.txt > merged_files.txt
m1f -s . -i merged_files.txt -o output.txt

# Or use process substitution (Linux/Mac)
m1f -s . -i <(cat files1.txt files2.txt files3.txt) -o output.txt

# Remove duplicates while merging
m1f -s . -i <(cat files1.txt files2.txt | sort -u) -o output.txt
```

### `--output-file FILE`, `-o FILE` (REQUIRED)

Path where the combined output file will be created. This is the only required
parameter.

### `--input-include-files [FILE ...]`

Files to include at the beginning of the output. The first file is treated as an
introduction/header.

## Output Formatting

### `--separator-style {Standard,Detailed,Markdown,MachineReadable,None}`

Format of the separator between files. Default: `Detailed`

- **Standard**: Simple separator with filename
- **Detailed**: Includes file metadata (date, size, type, checksum)
- **Markdown**: Markdown-formatted headers and metadata
- **MachineReadable**: JSON metadata blocks for programmatic parsing
- **None**: No separators (files concatenated directly)

### `--line-ending {lf,crlf}`

Line ending style for generated content. Default: `lf`

- **lf**: Unix/Linux/Mac style (\n)
- **crlf**: Windows style (\r\n)

### `--add-timestamp`, `-t`

Add timestamp to output filename in format `_YYYYMMDD_HHMMSS`.

### `--filename-mtime-hash`

Add hash of file modification times to output filename. Useful for
cache-busting.

## File Filtering

### `--excludes [PATTERN ...]`

Paths, directories, or glob patterns to exclude. Supports wildcards.

Example: `--excludes "*/tests/*" "*.pyc" "node_modules/"`

### `--exclude-paths-file FILE ...`

File(s) containing paths to exclude (supports gitignore format). Each pattern on
a new line. Multiple files can be specified and will be merged. Non-existent
files are skipped gracefully.

Examples:

```bash
# Single file
m1f -s . -o output.txt --exclude-paths-file .gitignore

# Multiple files
m1f -s . -o output.txt --exclude-paths-file .gitignore .m1fignore custom-excludes.txt
```

### `--include-paths-file FILE ...`

File(s) containing patterns to include (supports gitignore format). When
specified, only files matching these patterns will be included (whitelist mode).
Multiple files can be specified and will be merged. Non-existent files are
skipped gracefully.

**Processing Order**:

1. Files from `-i` (input-file) are always included, bypassing all filters
2. Files from `-s` (source directory) are filtered by include patterns first
3. Then exclude patterns are applied

**Path Resolution**: Same as `-i` - relative paths are resolved relative to the
source directory (`-s`).

Example include file:

```
# Include all Python files
*.py
# Include specific directories
src/**/*
api/**/*
# Exclude tests even if they match above
!test_*.py
```

Examples:

```bash
# Single file
m1f -s . -o output.txt --include-paths-file important-files.txt

# Multiple files
m1f -s . -o output.txt --include-paths-file core-files.txt api-files.txt

# Combined with input file (input file takes precedence)
m1f -s . -i explicit-files.txt -o output.txt --include-paths-file patterns.txt
```

### `--include-extensions [EXT ...]`

Only include files with these extensions. Extensions should include the dot.

Example: `--include-extensions .py .js .md`

### `--exclude-extensions [EXT ...]`

Exclude files with these extensions.

Example: `--exclude-extensions .pyc .pyo`

### `--include-dot-paths`

Include files and directories starting with a dot (hidden files). By default,
these are excluded.

### `--include-binary-files`

Attempt to include binary files. Use with caution as this may produce unreadable
output.

### `--include-symlinks`

Follow symbolic links. Be careful of infinite loops!

### `--max-file-size SIZE`

Skip files larger than specified size. Supports KB, MB, GB suffixes.

Examples: `10KB`, `1.5MB`, `2GB`

### `--no-default-excludes`

Disable default exclusions. By default, m1f excludes:

- `.git/`, `.svn/`, `.hg/`
- `node_modules/`, `venv/`, `.venv/`
- `__pycache__/`, `*.pyc`
- `.DS_Store`, `Thumbs.db`

### `--remove-scraped-metadata`

Remove scraped metadata (URL, timestamp) from HTML2MD files during processing.
Useful when processing scraped content.

## Character Encoding

### `--convert-to-charset {utf-8,utf-16,utf-16-le,utf-16-be,ascii,latin-1,cp1252}`

Convert all files to specified encoding. Default behavior is to detect and
preserve original encoding.

### `--abort-on-encoding-error`

Abort if encoding conversion fails. By default, files with encoding errors are
skipped with a warning.

### `--no-prefer-utf8-for-text-files`

Disable UTF-8 preference for text files (.md, .txt, .rst) when encoding is
ambiguous. By default, m1f prefers UTF-8 encoding for these file types when
chardet detects windows-1252 with less than 95% confidence, as these files often
contain UTF-8 emojis or special characters.

## Security Options

### `--security-check {error,warn,skip}`

Check for sensitive information in files using detect-secrets.

- **error**: Stop processing if secrets are found (default in v3.2)
- **warn**: Include files but show warnings
- **skip**: Disable security scanning (not recommended)

## Archive Options

### `--create-archive`

Create backup archive of processed files in addition to the combined output.

### `--archive-type {zip,tar.gz}`

Type of archive to create. Default: `zip`

## Output Control

### `--force`, `-f`

Force overwrite of existing output file without prompting.

### `--minimal-output`

Only create the combined file (no auxiliary files like file lists or directory
structure).

### `--skip-output-file`

Skip creating the main output file. Useful when only creating an archive.

### `--allow-duplicate-files`

Allow files with identical content to be included in the output. By default, m1f
deduplicates files based on their content checksum to save space and tokens.
With this flag, all files are included even if they have identical content.

### `--verbose`, `-v`

Enable verbose output with detailed processing information.

### `--quiet`, `-q`

Suppress all console output except errors.

## Preset Configuration

### `--preset FILE [FILE ...]`

Load preset configuration file(s) for file-specific processing. Multiple files
are merged in order.

### `--preset-group GROUP`

Use a specific preset group from the configuration file.

### `--disable-presets`

Disable all preset processing, even if preset files are specified.

## Exit Codes

- **0**: Success
- **1**: General error (M1FError base)
- **2**: File not found (FileNotFoundError)
- **3**: Permission denied (PermissionError)
- **4**: Encoding error (EncodingError)
- **5**: Configuration error (ConfigurationError)
- **6**: Validation error (ValidationError)
- **7**: Security check failed (SecurityError)
- **8**: Archive creation failed (ArchiveError)
- **130**: Operation cancelled by user (Ctrl+C)

## Environment Variables

**Note**: The following environment variables are documented for future
implementation but are not currently supported in v3.2.0:

- `M1F_DEFAULT_PRESET` - Path to default preset file (not implemented)
- `M1F_SECURITY_CHECK` - Default security check mode (not implemented)
- `M1F_MAX_FILE_SIZE` - Default maximum file size limit (not implemented)

## Subcommands

### `auto-bundle`

Create multiple m1f bundles based on a YAML configuration file
(`.m1f.config.yml`).

```bash
# Create all bundles
m1f auto-bundle

# Create specific bundle
m1f auto-bundle BUNDLE_NAME

# List available bundles
m1f auto-bundle --list

# With options
m1f auto-bundle --verbose
m1f auto-bundle --quiet
```

**Note**: The `m1f-update` command is a convenient alias for `m1f auto-bundle`
that can be used interchangeably:

```bash
# These are equivalent:
m1f auto-bundle
m1f-update

# With specific bundle:
m1f auto-bundle code
m1f-update code
```

**Options:**

- `BUNDLE_NAME`: Name of specific bundle to create (optional)
- `--list`: List available bundles from configuration
- `--verbose`, `-v`: Enable verbose output
- `--quiet`, `-q`: Suppress all console output

See the [Auto Bundle Guide](20_auto_bundle_guide.md) for detailed configuration
instructions.

## Notes

1. **Module Invocation**: You can use either `m1f` or `python -m tools.m1f`, or
   set up the `m1f` alias as described in the development workflow.

2. **Input Requirements**: At least one of `-s` (source directory) or `-i`
   (input file) must be specified. If neither is provided, m1f will show an
   error message.

3. **Gitignore**: m1f respects .gitignore files by default unless
   `--no-default-excludes` is used.

4. **Performance**: For large projects, use `--include-extensions` to limit
   processing to specific file types.
