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
- **Versioning Support**: Generate unique filenames based on content hash for tracking changes

### Common Use Cases

#### Documentation Compilation
```bash
# Create a complete documentation bundle from all markdown files
python tools/m1f.py -s ./docs -o ./doc_bundle.m1f.txt --include-extensions .md
```

#### Code Review Preparation
```bash
# Bundle specific components for code review
python tools/m1f.py -i code_review_files.txt -o ./review_bundle.m1f.txt
```

#### WordPress Development
```bash
# Combine theme or plugin files for AI analysis
python tools/m1f.py -s ./wp-content/themes/my-theme -o ./theme_context.m1f.txt \
  --include-extensions .php .js .css --exclude-paths-file ./exclude_build_files.txt
```

#### Project Knowledge Base
```bash
# Create a searchable knowledge base from project documentation
python tools/m1f.py -s ./project -o ./knowledge_base.m1f.txt \
  --include-extensions .md .txt .rst --minimal-output
```

#### Automated Documentation Versioning
```bash
# Create version-controlled documentation with content hash
python tools/m1f.py -s ./docs -o ./snapshots/docs.m1f.txt \
  --filename-mtime-hash --add-timestamp
```

## The m1f Toolset

### m1f (Make One File) - `tools/m1f.py`

Combines multiple files into a single file with rich metadata and customizable formatting.

**Key Features:**
- Multiple input sources (directories or file lists)
- Smart file filtering and deduplication
- Customizable separator styles for different use cases
- Token counting for LLM context planning
- Comprehensive metadata for each file
- Versioning support through content hashing

#### Command Line Options

| Option                   | Description                                                      |
| ------------------------ | ---------------------------------------------------------------- |
| `-s, --source-directory` | Path to the directory containing files to process                |
| `-i, --input-file`       | Path to a file containing a list of files/directories to process |
| `-o, --output-file`      | Path for the combined output file                                |
| `-f, --force`            | Force overwrite of existing output file without prompting        |
| `-t, --add-timestamp`    | Add a timestamp (\_YYYYMMDD_HHMMSS) to the output filename       |
| `--filename-mtime-hash`  | Append a hash of file modification timestamps to the filename    |
| `--include-extensions`   | Space-separated list of file extensions to include               |
| `--exclude-extensions`   | Space-separated list of file extensions to exclude               |
| `--exclude-paths-file`   | Path to file containing exact paths to exclude                   |
| `--no-default-excludes`  | Disable default directory exclusions                             |
| `--additional-excludes`  | Space-separated list of additional directory names to exclude    |
| `--include-dot-files`    | Include files that start with a dot (e.g., .gitignore)           |
| `--include-binary-files` | Attempt to include files with binary extensions                  |
| `--separator-style`      | Style of separators between files (`Standard`, `Detailed`, `Markdown`, `MachineReadable`, `None`) |
| `--line-ending`          | Line ending for script-generated separators (`lf` or `crlf`)     |
| `-v, --verbose`          | Enable verbose logging                                           |
| `--minimal-output`       | Generate only the combined output file (no auxiliary files)      |
| `--skip-output-file`     | Execute operations but skip writing the final output file        |
| `-q, --quiet`            | Suppress all console output                                      |
| `--create-archive`       | Create a backup archive of all processed files                   |
| `--archive-type`         | Type of archive to create (`zip` or `tar.gz`)                    |

#### Usage Examples

Basic command using a source directory:

```bash
python tools/m1f.py --source-directory /path/to/your/code \
  --output-file /path/to/combined_output.txt
```

Using an input file containing paths to process (one per line):

```bash
python tools/m1f.py -i filelist.txt -o combined_output.txt
```

Using MachineReadable style with verbose logging:

```bash
python tools/m1f.py -s ./my_project -o ./output/bundle.m1f.txt \
  --separator-style MachineReadable --force --verbose
```

Creating a combined file and a backup zip archive:

```bash
python tools/m1f.py -s ./source_code -o ./dist/combined.txt \
  --create-archive --archive-type zip
```

Concatenating files without any separators:

```bash
python tools/m1f.py -s ./source_code -o ./dist/seamless.txt \
  --separator-style None
```

Including only specific file extensions:

```bash
python tools/m1f.py -s ./src -o ./dist/code_only.txt \
  --include-extensions .py .js .ts .jsx .tsx
```

Concatenating all CSS files from a directory (for bundling):

```bash
python tools/m1f.py -s ./path/to/css_project_folder -o ./output/bundle.css \
  --include-extensions .css --separator-style None --force -t
```

Concatenating all JavaScript files:

```bash
python tools/m1f.py -s ./path/to/js_project_folder -o ./output/bundle.js \
  --include-extensions .js --separator-style None --force -t
```

Excluding specific file extensions:

```bash
python tools/m1f.py -s ./docs -o ./dist/docs.txt \
  --exclude-extensions .tmp .bak .log
```

Including content from typically excluded directories:

```bash
python tools/m1f.py -s ./project -o ./all_files.txt \
  --no-default-excludes
```

Generating only the combined file with no auxiliary files:

```bash
python tools/m1f.py -s ./src -o ./combined.txt \
  --minimal-output
```

Running with no console output (for scripts/automation):

```bash
python tools/m1f.py -s ./src -o ./combined.txt \
  --quiet --force
```

Excluding specific paths using a file:

```bash
python tools/m1f.py -s ./my_project -o ./combined.txt \
  --exclude-paths-file ./exclude_list.txt
```

Versioning with content hash based on included files:

```bash
python tools/m1f.py -s ./project -o ./snapshots/project.txt \
  --filename-mtime-hash
```

Skipping file generation while only creating metadata files:

```bash
python tools/m1f.py -s ./huge_project -o ./analysis.txt \
  --skip-output-file
```

### s1f (Split One File) - `tools/s1f.py`

Extracts individual files from a combined file, recreating the original directory structure.

**Key Features:**
- Preserves original file paths and timestamps
- Verifies file integrity with SHA256 checksums
- Supports all m1f separator styles
- Simple and secure extraction process

#### Command Line Options

| Option                        | Description                                              |
| ----------------------------- | -------------------------------------------------------- |
| `-i, --input-file`            | Path to the combined input file                          |
| `-d, --destination-directory` | Directory where extracted files will be saved            |
| `-f, --force`                 | Force overwrite of existing files without prompting      |
| `-v, --verbose`               | Enable verbose output                                    |
| `--timestamp-mode`            | How to set file timestamps (`original` or `current`)     |
| `--ignore-checksum`           | Skip checksum verification for MachineReadable files     |

#### Usage Examples

Basic command:

```bash
python tools/s1f.py --input-file /path/to/combined_output.txt \
  --destination-directory /path/to/output_folder
```

Splitting a MachineReadable file with force overwrite and verbose output:

```bash
python tools/s1f.py -i ./output/bundle.m1f.txt -d ./extracted_project -f -v
```

Using current system time for timestamps:

```bash
python tools/s1f.py -i ./combined_file.txt -d ./extracted_files \
  --timestamp-mode current
```

Ignoring checksum verification (when files were intentionally modified):

```bash
python tools/s1f.py -i ./modified_bundle.m1f.txt -d ./extracted_files \
  --ignore-checksum
```

### token_counter.py - Token Estimation Tool

Estimates token usage for LLM context planning.

**Key Features:**
- Uses OpenAI's tiktoken library for accurate estimates
- Supports different encoding schemes
- Helps optimize context usage

#### Command Line Options

| Option                | Description                                      |
| --------------------- | ------------------------------------------------ |
| `file_path`           | Path to the text file to analyze                 |
| `-e, --encoding`      | The tiktoken encoding to use (default: cl100k_base) |

#### Usage Example

```bash
python tools/token_counter.py combined_output.txt
```

With specific encoding:

```bash
python tools/token_counter.py myfile.txt -e p50k_base
```

### Input File Format

The input file for m1f.py should be a plain text file with one file or directory path per line. Empty lines and lines starting with `#` are ignored:

```
# This is a comment
/home/user/project/README.md

# Directory (will be processed recursively)
/home/user/project/src

# Another file
/home/user/project/requirements.txt
```

### Path Deduplication

When processing the input file, the script automatically handles path deduplication:

- If a parent directory is included, all its children are excluded
- Parent directories have priority over their subdirectories
- This prevents duplicate content and ensures efficient processing

For example, if an input file contains both `/project/src` and `/project/src/utils`, only `/project/src` will be processed, and `/project/src/utils` will be ignored because it's already covered by the parent directory.

### Exclude Paths File Format

When using the `--exclude-paths-file` option, the file should contain one path per line. Paths are matched exactly as written, and empty lines and lines starting with `#` are treated as comments.

Example of an exclude paths file:
```
# Exclude these exact paths
/path/to/project/node_modules
/path/to/project/temp/cache.json
/path/to/project/logs
```

### Integration with AI Tools

The m1f toolset works seamlessly with:

- **Visual Studio Code**: Reference the generated file using `@filename` in extensions like GitHub Copilot
- **Cursor**: Use `@filename` in the chat to add context
- **ChatGPT & Claude**: Upload the generated file to provide comprehensive context
- **Custom AI applications**: Process the machine-readable format programmatically

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
