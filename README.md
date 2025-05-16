# FUFTools

A collection of Python utility tools by [Franz und Franz](https://franz.agency)
for LLMs and AI that make life easier.

## Overview

FUFTools is an open-source suite of Python utilities designed with modularity
and scalability in mind. Each tool follows best practices and is thoroughly
documented. These tools aim to simplify common tasks and workflows when working
with Large Language Models and Artificial Intelligence.

The Python scripts are located in the `tools/` directory.

## Setup

1. **Create and activate a virtual environment:**

   ```bash
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On macOS/Linux
   source .venv/bin/activate
   ```

2. **Install dependencies:** The project uses `black` for code formatting and
   `pymarkdownlnt` for linting Markdown files. These and other dependencies
   (like `tiktoken` for `token_counter.py`) are listed in `requirements.txt`.

   ```bash
   pip install -r requirements.txt
   pip install black pymarkdownlnt
   ```

_(Note: `requirements.txt` will be updated to include `black` and
`pymarkdownlnt`)_

## Available Tools

All tools are located in the `tools/` directory.

### tools/makeonefile.py

A utility that combines the content of multiple text files from a specified
directory and its subdirectories into a single output file. Each file's content
is preceded by a separator showing metadata such as the file path, modification
date, size, type, and a SHA256 checksum for integrity.

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
- **Customization**:
  - Control over line endings (LF or CRLF) for script-generated separators
  - Verbose mode for detailed logging
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

#### Usage

Basic command using a source directory:

```bash
python tools/makeonefile.py --source-directory /path/to/your/code \
  --output-file /path/to/combined_output.txt
```

Using an input file containing paths to process (one per line):

```bash
python tools/makeonefile.py -i filelist.txt -o combined_output.txt
```

Example `filelist.txt`:

```
/home/user/project/src/main.py
/home/user/project/tests
/home/user/project/README.md
```

Using MachineReadable style with verbose logging for detailed output:

```bash
python tools/makeonefile.py -s ./my_project -o ./output/bundle.m1f \
  --separator-style MachineReadable --force --verbose
```

Creating a combined file and a backup zip archive:

```bash
python tools/makeonefile.py -s ./source_code -o ./dist/combined.txt \
  --create-archive --archive-type zip
```

Concatenating files without any separators between them:

```bash
python tools/makeonefile.py -s ./source_code -o ./dist/seamless.txt \
  --separator-style None
```

Excluding specific paths using a file:

```bash
python tools/makeonefile.py -s ./my_project -o ./combined.txt \
  --exclude-paths-file ./exclude_list.txt
```

When you run the script, it will:

1. Create the combined output file (e.g., `combined_output.txt`)
2. Generate a log file with the same name (e.g., `combined_output.log`)
   containing all processing information
3. Display the execution time at the end (e.g.,
   `Total execution time: 1m 45.67s`)

The log file will include:

- All files processed
- Files excluded or skipped (with reasons)
- Warning and error messages
- Final summary with token count and execution time

**Note**: When using `--input-file`, if a parent directory is included in the
list, any child paths will be automatically excluded. For example, if both
`/home/user/project` and `/home/user/project/src` are listed, only files under
`/home/user/project` will be processed.

### Input File Format

The input file should be a plain text file with one file or directory path per
line. Empty lines are ignored. Example:

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
- The most specific (deepest) parent directory is used
- This ensures no duplicate content in the output

For example, with these paths in the input file:

```
/path/to/project
/path/to/project/src/utils
/path/to/project/src/main.py
```

Only files under `/path/to/project` will be processed, and the other two paths
will be ignored as they're already covered by the parent directory.

For all available options, run:

```bash
python tools/makeonefile.py --help
```

#### Notable Command Line Options

| Option                   | Description                                                                                       |
| ------------------------ | ------------------------------------------------------------------------------------------------- |
| `-s, --source-directory` | Path to the directory containing files to process                                                 |
| `-i, --input-file`       | Path to a file containing a list of files/directories to process                                  |
| `-o, --output-file`      | Path for the combined output file (also determines the log file name)                             |
| `-f, --force`            | Force overwrite of existing output file without prompting                                         |
| `-t, --add-timestamp`    | Add a timestamp (\_YYYYMMDD_HHMMSS) to the output filename                                        |
| `--exclude-paths-file`   | Path to a file containing exact paths to exclude                                                  |
| `-v, --verbose`          | Enable verbose logging (more detailed log output)                                                 |
| `--separator-style`      | Style of separators between files (`Standard`, `Detailed`, `Markdown`, `MachineReadable`, `None`) |
| `--create-archive`       | Create a backup archive of processed files                                                        |
| `--archive-type`         | Type of archive to create (`zip` or `tar.gz`)                                                     |

### Exclude Paths File Format

When using the `--exclude-paths-file` option, the file should contain one path
per line. Paths are matched exactly as written, and empty lines and lines
starting with `#` are ignored (treated as comments).

Example of an exclude paths file:

```
# This is a comment
myproject/dir1/dir2

# Another directory to exclude
myproject/dir3/dir4

# A specific file
dir4
```

In this example:

- The path `myproject/dir1/dir2` will be excluded exactly as written
- The path `myproject/dir3/dir4` will be excluded exactly as written
- The path `dir4` will only exclude a file or directory named exactly `dir4` at
  the root level

Important: Unlike directory name-based exclusion, the path-based exclusion
matches exactly. So, for example, if you list `dir4` in the exclude file, it
will not exclude `myproject/dir4` or other paths that contain `dir4` as a
substring.

### MachineReadable Format

The MachineReadable format is designed for automated parsing and uses unique
boundary markers with a consistent pattern:

```
# PYMAKEONEFILE-BOUNDARY-99C5F740A78D4ABC82E3F9882D5A281E
# FILE: relative/path.ext
# PYMAKEONEFILE-BOUNDARY-99C5F740A78D4ABC82E3F9882D5A281E
# METADATA: {"modified": "2023-01-01 12:00:00", "type": ".ext", "size_bytes": 1234, "checksum_sha256": "abc..."}
# PYMAKEONEFILE-BOUNDARY-99C5F740A78D4ABC82E3F9882D5A281E

[file content]

# PYMAKEONEFILE-BOUNDARY-99C5F740A78D4ABC82E3F9882D5A281E
# END FILE
# PYMAKEONEFILE-BOUNDARY-99C5F740A78D4ABC82E3F9882D5A281E
```

This format ensures reliable parsing with unique boundary markers that won't
appear in regular files. The JSON metadata includes modification date, file
type, size in bytes, and SHA256 checksum for data integrity verification. It's
particularly suitable for use with LLMs and automated tools, as it uses familiar
comment syntax with consistent boundaries.

### tools/splitfiles.py

A utility that splits a single input file (previously created by
`tools/makeonefile.py`) back into multiple files, recreating the original
directory structure within a specified destination directory. It also verifies
file integrity using SHA256 checksums if they are present in the file headers.

#### Features

- Parses combined files generated by `tools/makeonefile.py`.
- Supports all separator styles: 'Standard', 'Detailed', 'Markdown', and
  'MachineReadable'.
- Recreates the original directory structure based on paths found in separators.
- Verifies file integrity by comparing calculated SHA256 checksums of extracted
  content against checksums stored in the headers (if available, primarily with
  'MachineReadable' style).
- Option to set file timestamps to original (default, if available from
  'MachineReadable' metadata) or current system time using `--timestamp-mode`.
- Option to force overwrite of existing files in the destination directory.
- Verbose mode for detailed operational logging.
- Secure path handling to prevent writing outside the destination directory.

#### Usage

Basic command:

```bash
python tools/splitfiles.py --input-file /path/to/combined_output.txt \
  --destination-directory /path/to/output_folder
```

Splitting a MachineReadable file with force overwrite and verbose output:

```bash
python tools/splitfiles.py -i ./output/bundle.m1f -d ./extracted_project -f -v
```

Using original timestamps (default behavior if available, or explicitly):

```bash
python tools/splitfiles.py -i bundle.m1f -d extracted --timestamp-mode original
```

Using current system timestamps for all extracted files:

```bash
python tools/splitfiles.py -i bundle.m1f -d extracted --timestamp-mode current
```

For all options, run:

```bash
python tools/splitfiles.py --help
```

### tools/token_counter.py

A utility to count the approximate number of tokens in a given text file,
similar to how OpenAI's language models count tokens. This is useful for
estimating API usage costs or understanding context window limits.

#### Features

- Uses OpenAI's `tiktoken` library for accurate tokenization.
- Supports various encodings used by OpenAI models (e.g., `cl100k_base` for
  gpt-4/gpt-3.5-turbo, `p50k_base`).
- Command-line interface for easy integration into workflows.
- Handles different file types (txt, md, py, php, etc.) by reading their text
  content.
- Provides informative output, including the encoding used.
- Includes error handling for file not found and encoding issues.

#### Usage

Basic command (uses `cl100k_base` encoding by default):

```bash
python tools/token_counter.py /path/to/your/file.txt
```

Specify a different encoding:

```bash
python tools/token_counter.py /path/to/your/file.txt --encoding p50k_base
```

For all options, run:

```bash
python tools/token_counter.py --help
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
# (requirements.txt will be updated)
# or individually:
pip install tiktoken black pymarkdownlnt
```

## Coming Soon

Additional Python tools are under development and will be added to this
repository in the future.

## License

This project is licensed under the MIT License. See the [LICENSE.md](LICENSE.md)
file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
