# m1f - Make One File

A powerful suite of tools for working efficiently with Large Language Models (LLMs) and AI, developed by [Franz und Franz](https://franz.agency).

## What is m1f?

m1f ("Make One File") and s1f ("Split One File") are specialized Python utilities designed to:

1. **Combine multiple project files into a single reference file** - perfect for providing context to LLMs
2. **Extract individual files from a combined file** - restore original files with their structure intact

These tools help solve a core challenge when working with AI assistants: **providing comprehensive context efficiently**.

## Why Use m1f?

### Optimized for AI Interaction

- **Better Context Management**: Provide LLMs with exactly the files they need to understand your project
- **Token Optimization**: Include only relevant files to make the most of your context window
- **Flexible Formatting**: Choose from multiple separator styles optimized for machine readability
- **Smart Filtering**: Include/exclude files by extension, path, or pattern
- **Structure Preservation**: Maintain file relationships and metadata

### Common Use Cases

#### Documentation Compilation
```bash
# Create a complete documentation bundle from all markdown files
python tools/makeonefile.py -s ./docs -o ./doc_bundle.m1f.txt --include-extensions .md
```

#### Code Review Preparation
```bash
# Bundle specific components for code review
python tools/makeonefile.py -i code_review_files.txt -o ./review_bundle.m1f.txt
```

#### WordPress Development
```bash
# Combine theme or plugin files for AI analysis
python tools/makeonefile.py -s ./wp-content/themes/my-theme -o ./theme_context.m1f.txt \
  --include-extensions .php .js .css --exclude-paths-file ./exclude_build_files.txt
```

#### Project Knowledge Base
```bash
# Create a searchable knowledge base from project documentation
python tools/makeonefile.py -s ./project -o ./knowledge_base.m1f.txt \
  --include-extensions .md .txt .rst --minimal-output
```

## The m1f Toolset

### m1f (Make One File) - `tools/makeonefile.py`

Combines multiple files into a single file with rich metadata and customizable formatting.

**Key Features:**
- Multiple input sources (directories or file lists)
- Smart file filtering and deduplication
- Customizable separator styles for different use cases
- Token counting for LLM context planning
- Comprehensive metadata for each file

### s1f (Split One File) - `tools/splitfiles.py`

Extracts individual files from a combined file, recreating the original directory structure.

**Key Features:**
- Preserves original file paths and timestamps
- Verifies file integrity with SHA256 checksums
- Supports all m1f separator styles
- Simple and secure extraction process

### token_counter.py

Estimates token usage for LLM context planning.

**Key Features:**
- Uses OpenAI's tiktoken library for accurate estimates
- Supports different encoding schemes
- Helps optimize context usage

## Setup

1. **Create and activate a virtual environment:**

   ```bash
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On macOS/Linux
   source .venv/bin/activate
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

## Detailed Tool Documentation

### m1f (Make One File)

A utility that combines content from multiple files into a single output file with rich metadata.

#### Features

- **Multiple Input Sources**:
  - Recursive file scanning in a source directory
  - Process files and directories from an input file list
  - Automatic deduplication of paths (parent directories take precedence)
- **Flexible Output**:
  - Customizable separators between file contents: 'Standard', 'Detailed',
    'Markdown', 'MachineReadable', and 'None'
  - The 'MachineReadable' style uses unique boundary markers and JSON metadata
    (including path, modification date, type, size in bytes, and SHA256
    checksum) for robust parsing and splitting
  - The 'None' style concatenates files without any separators or newlines
    between them, creating a seamless combined file
  - SHA256 checksum included in headers for all styles (except 'None') to help
    ensure data integrity
  - Option to add a timestamp to the output filename
- **Smart Filtering**:
  - Exclusion of common project directories (e.g., node_modules, .git, build)
  - Exclusion of binary files by default
  - Option to include dot-files and binary files
  - Case-insensitive exclusion of additional specified directory names
  - Exclusion of specific paths from a file with exact path matching
  - Filter by file extensions with include/exclude patterns
  - Option to disable default directory exclusions
- **Customization**:
  - Control over line endings (LF or CRLF) for script-generated separators
  - Verbose mode for detailed logging
  - Minimal output mode (only create the combined file, no auxiliary files)
  - Quiet mode (suppress all console output)
  - Prompts for overwriting existing output file unless `--force` is used
- **Token Counting**:
  - Estimates and displays the token count of the combined output file using
    tiktoken.
- **Archiving (Optional)**:
  - Create a backup archive (zip or tar.gz) of all processed files.
  - Archive is named after the output file with a `_backup` suffix (e.g.,
    `combined_output_backup.zip`).
- **Logging**:
  - Automatically creates a log file with the same name as the output file but
    with a `.log` extension (e.g., `combined_output.log` for
    `combined_output.txt`).
  - The log file captures all processing information, warnings, and errors.
- **Additional Output Files**:
  - Generates a file list in `{output_file_stem}_filelist.txt` containing all
    included files sorted alphabetically.
  - Creates a directory list in `{output_file_stem}_dirlist.txt` containing all
    unique directories (sorted) where the included files are located.
- **Performance Monitoring**:
  - Measures and reports the total execution time at the end of processing.
  - For longer runs, time is displayed in minutes and seconds format.

#### Usage Examples

Basic command using a source directory:

```bash
python tools/makeonefile.py --source-directory /path/to/your/code \
  --output-file /path/to/combined_output.txt
```

Using an input file containing paths to process (one per line):

```bash
python tools/makeonefile.py -i filelist.txt -o combined_output.txt
```

Using MachineReadable style with verbose logging for detailed output:

```bash
python tools/makeonefile.py -s ./my_project -o ./output/bundle.m1f.txt \
  --separator-style MachineReadable --force --verbose
```

#### AI Optimization Examples

**WordPress Theme Context for AI:**
```bash
# Create a context file for your WordPress theme
python tools/makeonefile.py -s ./wp-content/themes/my-theme \
  -o ./ai-context/theme.m1f.txt \
  --include-extensions .php .css .js --separator-style MachineReadable
```

Then in your AI chat: `@ai-context/theme.m1f.txt`

**Documentation Compilation:**
```bash
# Combine all markdown documentation
python tools/makeonefile.py -s ./docs -o ./docs-bundle.md \
  --include-extensions .md --separator-style None
```

**Project Analysis Context:**
```bash
# Create a focused context file for specific components
python tools/makeonefile.py -i important_files.txt \
  -o ./ai-context/feature.m1f.txt \
  --separator-style Markdown --minimal-output
```

### s1f (Split One File)

A utility that splits a single combined file back into multiple files, recreating the original directory structure.

#### Features

- Parses combined files generated by `tools/makeonefile.py`.
- Supports all separator styles: 'Standard', 'Detailed', 'Markdown', and
  'MachineReadable'.
- Properly extracts original file paths from all separator formats, ensuring
  consistent behavior.
- Recreates the original directory structure based on paths found in separators.
- Verifies file integrity by comparing calculated SHA256 checksums of extracted
  content against checksums stored in the headers (if available).
- All separator styles correctly extract and preserve the original file paths,
  ensuring the reconstructed directory structure matches the original.
- Option to set file timestamps to original (default, if available from
  metadata) or current system time using `--timestamp-mode`.
- Option to force overwrite of existing files in the destination directory.
- Verbose mode for detailed operational logging.
- Secure path handling to prevent writing outside the destination directory.

#### Usage Examples

Basic command:

```bash
python tools/splitfiles.py --input-file /path/to/combined_output.txt \
  --destination-directory /path/to/output_folder
```

Splitting a MachineReadable file with force overwrite and verbose output:

```bash
python tools/splitfiles.py -i ./output/bundle.m1f.txt -d ./extracted_project -f -v
```

### Integration with AI Tools

The m1f toolset works seamlessly with:

- **Visual Studio Code**: Reference the generated file using `@filename` in extensions like GitHub Copilot
- **Cursor**: Use `@filename` in the chat to add context
- **ChatGPT & Claude**: Upload the generated file to provide comprehensive context
- **Custom AI applications**: Process the machine-readable format programmatically

## Requirements

- Python 3.7+
- Standard Python libraries (includes `argparse`, `datetime`, `hashlib`, `json`,
  `logging`, `os`, `pathlib`, `re`, `sys` across the tools).
- `tiktoken`: For the `tools/token_counter.py` script.
- `black`: For code formatting.
- `pymarkdownlnt`: For linting Markdown files.

You can install all Python dependencies using:

```bash
pip install -r requirements.txt
```

## License

This project is licensed under the MIT License. See the [LICENSE.md](LICENSE.md)
file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
