# m1f - Make One File

A powerful suite of tools for working efficiently with Large Language Models
(LLMs) and AI, developed by [Franz und Franz](https://franz.agency).

## What is m1f?

m1f ("Make One File") and s1f ("Split One File") are specialized Python
utilities designed to:

1. **Combine multiple project files into a single reference file** - perfect for
   providing context to LLMs
2. **Extract individual files from a combined file** - restore original files
   with their structure intact

These tools help solve a core challenge when working with AI assistants:
**providing comprehensive context efficiently**.

## Why Use m1f?

### Optimized for AI Interaction

- **Better Context Management**: Provide LLMs with exactly the files they need
  to understand your project
- **Token Optimization**: Include only relevant files to make the most of your
  context window
- **Flexible Formatting**: Choose from multiple separator styles optimized for
  machine readability
- **Smart Filtering**: Include/exclude files by extension, path, or pattern
- **Structure Preservation**: Maintain file relationships and metadata
- **Versioning Support**: Generate unique filenames based on content hash for
  tracking changes

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

Combines multiple files into a single file with rich metadata and customizable
formatting.

**Key Features:**

- Multiple input sources (directories or file lists)
- Smart file filtering and deduplication
- Customizable separator styles for different use cases
- Token counting for LLM context planning
- Comprehensive metadata for each file
- Versioning support through content hashing

#### Command Line Options for m1f.py

| Option                   | Description                                                                                                                                                                                                                               |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `-s, --source-directory` | Path to the directory containing files to process                                                                                                                                                                                         |
| `-i, --input-file`       | Path to a file containing a list of files/directories to process                                                                                                                                                                          |
| `-o, --output-file`      | Path for the combined output file                                                                                                                                                                                                         |
| `-f, --force`            | Force overwrite of existing output file without prompting                                                                                                                                                                                 |
| `-t, --add-timestamp`    | Add a timestamp (\_YYYYMMDD_HHMMSS) to the output filename. Useful for versioning and preventing accidental overwrite of previous output files                                                                                            |
| `--filename-mtime-hash`  | Append a hash of file modification timestamps to the filename. The hash is created using all filenames and their modification dates, enabling caching mechanisms. Hash only changes when files are added/removed or their content changes |
| `--include-extensions`   | Space-separated list of file extensions to include (e.g., `--include-extensions .py .js .html` will only process files with these extensions)                                                                                             |
| `--exclude-extensions`   | Space-separated list of file extensions to exclude (e.g., `--exclude-extensions .log .tmp .bak` will skip these file types)                                                                                                               |
| `--exclude-paths-file`   | Path to file containing paths or patterns to exclude. Supports both exact path lists and gitignore-style pattern formats. Can use a .gitignore file directly                                                                              |
| `--no-default-excludes`  | Disable default directory exclusions. By default, the following directories are excluded: vendor, node_modules, build, dist, cache, .git, .svn, .hg, **pycache**                                                                          |
| `--excludes`             | Space-separated list of paths to exclude. Supports directory names, exact file paths, and gitignore-style patterns (e.g., `--excludes logs "config/settings.json" "*.log" "build/" "!important.log"`)                                     |
| `--include-dot-paths`    | Include files and directories that start with a dot (e.g., .gitignore, .hidden/). By default, all dot files and directories are excluded.                                                                                                 |
| `--include-binary-files` | Attempt to include files with binary extensions                                                                                                                                                                                           |
| `--separator-style`      | Style of separators between files (`Standard`, `Detailed`, `Markdown`, `MachineReadable`, `None`)                                                                                                                                         |
| `--line-ending`          | Line ending for script-generated separators (`lf` or `crlf`)                                                                                                                                                                              |
| `--convert-to-charset`   | Convert all files to the specified character encoding (`utf-8` [default], `utf-16`, `utf-16-le`, `utf-16-be`, `ascii`, `latin-1`, `cp1252`). The original encoding is automatically detected and included in the metadata when using compatible separator styles |
| `--abort-on-encoding-error` | Abort processing if encoding conversion errors occur. Without this flag, characters that cannot be represented will be replaced                                                                                                         |
| `-v, --verbose`          | Enable verbose logging                                                                                                                                                                                                                    |
| `--minimal-output`       | Generate only the combined output file (no auxiliary files)                                                                                                                                                                               |
| `--skip-output-file`     | Execute operations but skip writing the final output file                                                                                                                                                                                 |
| `-q, --quiet`            | Suppress all console output                                                                                                                                                                                                               |
| `--create-archive`       | Create a backup archive of all processed files                                                                                                                                                                                            |
| `--archive-type`         | Type of archive to create (`zip` or `tar.gz`)                                                                                                                                                                                             |

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
python tools/m1f.py \
  --input-file ./file_list.txt -o ./dist/seamless.txt \
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

Including dot files and directories:

```bash
python tools/m1f.py -s ./project -o ./with_dotfiles.txt \
  --include-dot-paths
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

Using a .gitignore file for exclusion patterns:

```bash
python tools/m1f.py -s ./my_project -o ./combined.txt \
  --exclude-paths-file ./.gitignore
```

Using gitignore-style patterns directly in the command line:

```bash
python tools/m1f.py -s ./my_project -o ./combined.txt \
  --excludes "*.log" "build/" "!important.log"
```

Skipping file generation while only creating metadata files:

```bash
python tools/m1f.py -s ./huge_project -o ./analysis.txt \
  --skip-output-file
```

Converting files to a different character encoding:

```bash
python tools/m1f.py -s ./project -o ./utf8_only.txt \
  --convert-to-charset utf-8
```

Converting files with strict error handling:

```bash
python tools/m1f.py -s ./project -o ./strict_conversion.txt \
  --convert-to-charset utf-8 --abort-on-encoding-error
```

Versioning with content hash based on included files:

```bash
python tools/m1f.py -s ./project -o ./snapshots/project.txt \
  --filename-mtime-hash
```

### Output Files

By default, `m1f.py` creates several output files to provide comprehensive information about the processed files:

1. **Primary output file** - The combined file specified by `--output-file` containing all processed files with separators
2. **Log file** - A `.log` file with the same base name as the output file, containing detailed processing information
3. **File list** - A `_filelist.txt` file containing the paths of all included files
4. **Directory list** - A `_dirlist.txt` file containing all unique directories from the included files
5. **Archive file** - An optional backup archive (zip or tar.gz) if `--create-archive` is specified

To create only the primary output file and skip the auxiliary files, use the `--minimal-output` option:

```bash
# Create only the combined output file without any auxiliary files
python tools/m1f.py -s ./src -o ./combined.txt --minimal-output
```

For situations where you want the auxiliary files (logs, lists) but not the primary output file, use `--skip-output-file`:

```bash
# Generate logs and file lists but skip writing the actual combined file
python tools/m1f.py -s ./huge_project -o ./analysis.txt --skip-output-file
```

### s1f (Split One File) - `tools/s1f.py`

Extracts individual files from a combined file, recreating the original
directory structure.

**Key Features:**

- Preserves original file paths and timestamps
- Verifies file integrity with SHA256 checksums
- Supports all m1f separator styles
- Simple and secure extraction process

#### Command Line Options for s1f.py

| Option                        | Description                                                                                                                                      |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `-i, --input-file`            | Path to the combined input file                                                                                                                  |
| `-d, --destination-directory` | Directory where extracted files will be saved                                                                                                    |
| `-f, --force`                 | Force overwrite of existing files without prompting                                                                                              |
| `-v, --verbose`               | Enable verbose output                                                                                                                            |
| `--timestamp-mode`            | How to set file timestamps (`original` or `current`). Original preserves timestamps from when files were combined, current uses the current time |
| `--ignore-checksum`           | Skip checksum verification for MachineReadable files. Useful when files were intentionally modified after being combined                         |
| `--respect-encoding`          | Try to use the original file encoding when writing extracted files. If enabled and original encoding information is available, files will be written using that encoding instead of UTF-8 |

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

Preserving original file encodings:

```bash
python tools/s1f.py -i ./with_encodings.txt -d ./extracted_files \
  --respect-encoding
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

| Option           | Description                                         |
| ---------------- | --------------------------------------------------- |
| `file_path`      | Path to the text file to analyze                    |
| `-e, --encoding` | The tiktoken encoding to use (default: cl100k_base) |

#### Usage Example

```bash
python tools/token_counter.py combined_output.txt
```

With specific encoding:

```bash
python tools/token_counter.py myfile.txt -e p50k_base
```

### Input File Format

The input file for m1f.py should be a plain text file with one file or directory
path per line. Empty lines and lines starting with `#` are ignored:

```
# This is a comment
/home/user/project/README.md

# Directory (will be processed recursively)
/home/user/project/src

# Another file
/home/user/project/requirements.txt
```

### Path Deduplication

When processing the input file, the script automatically handles path
deduplication:

- If a parent directory is included, all its children are excluded
- Parent directories have priority over their subdirectories
- This prevents duplicate content and ensures efficient processing

For example, if an input file contains both `/project/src` and
`/project/src/utils`, only `/project/src` will be processed, and
`/project/src/utils` will be ignored because it's already covered by the parent
directory.

### Exclude Paths File Format

When using the `--exclude-paths-file` option, the file can be in one of two
formats:

1. **Exact Path List** - One path per line, matched exactly as written:

```
# Exclude these exact paths
/path/to/project/node_modules
/path/to/project/temp/cache.json
/path/to/project/logs
```

2. **Gitignore Pattern Format** - Standard .gitignore patterns with wildcards
   and pattern matching:

```
# Ignore all .log files
*.log

# Ignore build directories
build/
dist/

# Ignore node_modules directory
node_modules/

# Ignore but track specific files
!important.log
```

The system automatically detects which format is being used based on the file
content or name. If the file is named `.gitignore` or contains patterns with
wildcards (`*`), negation (`!`), or directory markers (`/`), it will be
processed using gitignore rules.

### Gitignore Pattern Support

Both `--excludes` and `--exclude-paths-file` options support gitignore-style
patterns:

- **Wildcards**: `*.log` matches all files with .log extension
- **Directory exclusions**: `build/` excludes the build directory and all its
  contents
- **Negation patterns**: `!important.log` includes a specific file even if it
  matches another pattern

Some examples of using patterns with `--excludes`:

```bash
# Exclude all log files except important.log
python tools/m1f.py -s ./project -o ./output.txt --excludes "*.log" "!important.log"

# Exclude build and dist directories plus all temporary files
python tools/m1f.py -s ./project -o ./output.txt --excludes "build/" "dist/" "*.tmp"
```

### Integration with AI Tools

The m1f toolset works seamlessly with:

- **Visual Studio Code**: Reference the generated file using `@filename` in
  extensions like GitHub Copilot
- **Cursor**: Use `@filename` in the chat to add context
- **ChatGPT & Claude**: Upload the generated file to provide comprehensive
  context
- **Custom AI applications**: Process the machine-readable format
  programmatically

## Separator Styles

The `--separator-style` option allows you to choose how files are separated in
the combined output file. Each style is designed for specific use cases, from
human readability to automated parsing.

### Standard Style

A simple, concise separator that shows the file path and optional checksum:

```
======= path/to/file.py | CHECKSUM_SHA256: abcdef1234567890... ======
```

**Best for:**

- Quick reference and navigation when reviewing code
- Minimizing overhead while still providing clear file boundaries
- Situations where you want to keep separators compact

### Detailed Style (Default)

A more comprehensive separator that includes file metadata:

```
========================================================================================
== FILE: path/to/file.py
== DATE: 2023-06-15 14:30:21 | SIZE: 2.50 KB | TYPE: .py
== CHECKSUM_SHA256: abcdef1234567890...
========================================================================================
```

**Best for:**

- Code review and analysis where file metadata is important
- Documentation that needs to preserve timestamp and size information
- Default choice for most use cases (good balance of information and
  readability)

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

```

**Best for:**
- Creating documentation that will be rendered in Markdown viewers
- Sharing code snippets that benefit from syntax highlighting
- Generating readable reports that might be included in wikis or other Markdown-based systems

### MachineReadable Style

A robust format designed for reliable automated parsing and processing. It uses unique boundary markers with UUIDs and structured JSON metadata:

```

--- PYMK1F_BEGIN_FILE_METADATA_BLOCK_12345678-1234-1234-1234-123456789abc ---
METADATA_JSON: { "original_filepath": "path/to/file.py", "original_filename":
"file.py", "timestamp_utc_iso": "2023-06-15T14:30:21Z", "type": ".py",
"size_bytes": 2560, "checksum_sha256": "abcdef1234567890..." } ---
PYMK1F_END_FILE_METADATA_BLOCK_12345678-1234-1234-1234-123456789abc --- ---
PYMK1F_BEGIN_FILE_CONTENT_BLOCK_12345678-1234-1234-1234-123456789abc ---

# File content here

--- PYMK1F_END_FILE_CONTENT_BLOCK_12345678-1234-1234-1234-123456789abc ---

```

**Best for:**
- Working with automated tools that need to parse and extract file content
- Integration with the `s1f.py` tool for reliable file extraction
- Ensuring file integrity with checksums and complete metadata
- Programmatic processing of the combined file
- LLM prompt engineering that requires structured data

### None Style

Files are concatenated directly without any separators between them:

```

// Content of file1.js console.log("Hello"); // Content of file2.js
console.log("World");

````

**Best for:**
- Creating bundled output like combining CSS or JavaScript files
- Generating files where separators would interfere with the content
- Concatenating files that are meant to be used together as a single unit
- Minimizing token usage in LLM interactions

### Choosing the Right Style

The best separator style depends on your specific use case:

- For reading and reviewing code: **Detailed** or **Standard**
- For documentation in Markdown format: **Markdown**
- For automated processing and extraction: **MachineReadable**
- For file bundling with no separators: **None**

## Additional Notes

### Binary File Handling

While the script can include binary files using the `--include-binary-files` option, these are read as text (UTF-8 with error ignoring). This can result in garbled/unreadable content in the output and significantly increase file size. This feature is primarily intended for files that might be misidentified as binary or for specific edge cases.

### Encoding Behavior

The script uses UTF-8 as the default encoding for reading and writing files. When using `--convert-to-charset`, the original encoding of each file is automatically detected and recorded in the file metadata (for compatible separator styles like `Detailed`, `Markdown`, and `MachineReadable`). This enables converting from the source encoding to the target encoding.

The following encodings are supported for conversion: UTF-8 (default), UTF-16, UTF-16-LE, UTF-16-BE, ASCII, Latin-1 (ISO-8859-1), and CP1252 (Windows-1252).

When extracting files with s1f, you can use the `--respect-encoding` option to restore files with their original encoding (if that information was recorded during combination with m1f).

### Line Ending Behavior

The `--line-ending` option only affects the line endings generated by the script (in separators and blank lines), not those in the original files. The line endings of original files remain unchanged.

### Archive Creation

When `--create-archive` is used, the archive will contain all files selected for inclusion in the main output file, using their relative paths within the archive. The archive is named based on the output file; for example, if `output.txt` is created, the archive will be `output_backup.zip` (or .tar.gz).

### Performance Considerations

For extremely large directories with tens of thousands of files or very large individual files, the script might take some time to process.

### Project Website

For more information and updates, visit the official project website: [https://m1f.dev](https://m1f.dev)

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
- `chardet`: Optional, for character encoding detection.

You can install all Python dependencies using:

```bash
pip install -r requirements.txt
```

## License

This project is licensed under the MIT License. See the [LICENSE.md](LICENSE.md)
file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.