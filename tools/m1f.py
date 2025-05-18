#!/usr/bin/env python3
"""
===========================
m1f - Make One File
===========================

SYNOPSIS
========
Combines the content of multiple text files from a specified directory or a list
of paths into a single output file. Each file's content is preceded by a
separator showing metadata. Optionally, it can also create a backup archive
(zip or tar.gz) of all processed files.

DESCRIPTION
===========
This script helps consolidate multiple source code files or text documents
into a single file, which is useful for:

- Providing context to Large Language Models (LLMs) for code understanding
- Creating bundled documentation for review or reference
- Making a machine-parseable bundle for later splitting (using s1f.py)
- Creating a backup archive of the processed files alongside the combined text file

KEY FEATURES
============
- Recursive file scanning in a source directory or processing a list of paths from an input file.
- Customizable separators between file contents ('Standard', 'Detailed', 'Markdown', 'MachineReadable', 'None').
- The 'MachineReadable' style uses unique boundary markers and JSON metadata for robust parsing.
- The 'None' style concatenates files without any separators or newlines between them.
- Output filename customization:
  - Option to add a timestamp to the output filename (_YYYYMMDD_HHMMSS) with `--add-timestamp`.
  - Option to include a content hash based on files and their modification times with `--filename-mtime-hash`.
- Smart file filtering:
  - Exclusion of common project directories (e.g., 'node_modules', '.git', 'build').
  - Exclusion of binary files by default (based on extension).
  - Inclusion/exclusion by file extension with `--include-extensions` and `--exclude-extensions`.
  - Option to include dot-files (e.g., '.gitignore') and binary files.
  - Case-insensitive exclusion of additional specified directory names.
  - Exclusion of specific paths from a file, with exact path matching.
- Control over line endings (LF or CRLF) for script-generated separators.
- Multiple output modes:
  - Full output with all auxiliary files (default).
  - Minimal output mode with `--minimal-output` (only create the combined file).
  - Skip the output file with `--skip-output-file` (generate only logs and auxiliary files).
  - Quiet mode with `--quiet` (suppress all console output).
- Verbose mode for detailed logging with `--verbose`.
- Prompts for overwriting an existing output file unless `--force` is used.
- Estimates and displays the token count of the combined output file using tiktoken.
- Optional creation of a zip or tar.gz archive containing all processed files, named after the output file with a `_backup` suffix.
- Creates a log file with the same name as the output file but with a `.log` extension, capturing all processing information.
- Generates two additional output files: one with all included file paths (_filelist.txt) and another with all unique directories (_dirlist.txt).
- Measures and reports the total execution time for performance monitoring.

REQUIREMENTS
============
- Python 3.7+ (due to `pathlib` usage, f-strings, and json module usage)
- Standard Python libraries only (argparse, datetime, json, logging, os, pathlib, shutil, sys, zipfile, tarfile).
- tiktoken (for token counting of the output file)

INSTALLATION
============
No special installation is needed. Just download the script (`m1f.py`)
and ensure it has execute permissions if you want to run it directly
(e.g., `chmod +x m1f.py` on Linux/macOS).

USAGE
=====
Basic command:
  python tools/m1f.py --source-directory /path/to/your/code --output-file /path/to/combined_output.txt

Using MachineReadable style and creating a zip archive:
  python tools/m1f.py -s ./my_project -o ./output/bundle.m1f.txt --separator-style MachineReadable --create-archive --archive-type zip

With more options including tar.gz archive:
  python tools/m1f.py -s ./my_project -o ./output/bundle.md -t --separator-style Markdown --force --verbose --additional-excludes "temp" "docs_old" --create-archive --archive-type tar.gz

With exclude paths file:
  python tools/m1f.py -s ./my_project -o ./output/bundle.txt --exclude-paths-file ./exclude_list.txt

Skip writing the output file but generate auxiliary files:
  python tools/m1f.py -s ./my_project -o ./auxiliary_only.txt --skip-output-file --verbose

With filename content hash for versioning:
  python tools/m1f.py -s ./my_project -o ./output/bundle.txt --filename-mtime-hash

Including only specific file extensions:
  python tools/m1f.py -s ./src -o ./dist/code_only.txt --include-extensions .py .js .ts .jsx .tsx

Excluding specific file extensions:
  python tools/m1f.py -s ./docs -o ./dist/docs.txt --exclude-extensions .tmp .bak .log

Minimal output mode (only create combined file):
  python tools/m1f.py -s ./src -o ./combined.txt --minimal-output

Quiet mode (no console output):
  python tools/m1f.py -s ./src -o ./combined.txt --quiet --force

For all options, run:
  python tools/m1f.py --help

NOTES
=====
- Path Exclusion File: When using `--exclude-paths-file`, the file should contain one path per line. Paths are matched exactly as written. For example, if the file contains:
  ```
  my_project/dir1/dir2
  my_project/dir3/file.txt
  some_file.txt
  ```
  Only these exact paths will be excluded. A path like `other_project/some_file.txt` would not be excluded. Empty lines and lines starting with '#' are ignored as comments.

- MachineReadable Format: This format is designed for automated splitting and LLM compatibility.
  It uses unique UUID-based boundary markers with clear JSON metadata:
  ```
  --- PYMK1F_BEGIN_FILE_METADATA_BLOCK_{UUID} ---
  METADATA_JSON:
  {
      "original_filepath": "relative/path.ext",
      "original_filename": "path.ext",
      "timestamp_utc_iso": "2023-01-01T12:00:00Z",
      "type": ".ext",
      "size_bytes": 1234,
      "checksum_sha256": "abc..."
  }
  --- PYMK1F_END_FILE_METADATA_BLOCK_{UUID} ---
  --- PYMK1F_BEGIN_FILE_CONTENT_BLOCK_{UUID} ---

  [file content]

  --- PYMK1F_END_FILE_CONTENT_BLOCK_{UUID} ---
  ```
  This format ensures reliable automated parsing with unique identifiers for each file block,
  while keeping the metadata in a structured JSON format that's easy for programs to consume.
- Binary Files: While the script can attempt to include binary files using the
  `--include-binary-files` flag, the content will be read as text (UTF-8 with
  error ignoring). This can result in garbled/unreadable content in the output
  and significantly increase file size. This feature is generally for including
  files that might be misidentified as binary or for specific edge cases.
- Performance: For extremely large directories with tens of thousands of files or
  very large individual files, the script might take some time to process.
- Encoding: The script attempts to read files as UTF-8 and writes the output file
  as UTF-8. Files with other encodings might not be handled perfectly, especially
  if they contain characters not representable in UTF-8 or if `errors='ignore'`
  has to discard characters.
- Line Endings of Source Files: The script preserves the original line endings of
  the content from the source files. The `--line-ending` option only affects the
  separators and blank lines *generated by this script*.
- Archive Creation: If `--create-archive` is used, the archive will contain all files
  that were selected for inclusion in the main combined text file, using their
  relative paths within the archive. The archive is named based on the output file,
  e.g., if `output.txt` is created, the archive will be `output_backup.zip` (or .tar.gz).

AUTHOR
======
Franz und Franz (https://franz.agency)
Project: https://m1f.dev

VERSION
=======
2.0.0
"""

import argparse
import datetime
import hashlib
import json
import logging
import os
import sys
import time  # Added for time measurement
import uuid  # Added for UUID generation
from pathlib import Path
from typing import List, Set, Tuple, Optional
import tiktoken  # Added for token counting
import zipfile  # Added for archive creation
import tarfile  # Added for archive creation

# --- Logger Setup ---
logger = logging.getLogger("makeonefile")
file_handler = None  # Will be set in configure_logging_settings

# --- Global Definitions ---

DEFAULT_EXCLUDED_DIR_NAMES = [
    "vendor",
    "node_modules",
    "build",
    "dist",
    "cache",
    ".git",  # Explicitly add common VCS directories
    ".svn",
    ".hg",
    "__pycache__",
]

BINARY_FILE_EXTENSIONS = {
    # Images
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".tiff",
    ".tif",
    ".ico",
    ".webp",
    ".svgz",
    # Audio
    ".mp3",
    ".wav",
    ".ogg",
    ".flac",
    ".aac",
    ".wma",
    ".m4a",
    # Video
    ".mp4",
    ".avi",
    ".mkv",
    ".mov",
    ".wmv",
    ".flv",
    ".webm",
    ".mpeg",
    ".mpg",
    # Executables and compiled code
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".bin",
    ".msi",
    ".pdb",
    ".lib",
    ".o",
    ".obj",
    ".pyc",
    ".pyo",
    ".class",
    # Archives
    ".zip",
    ".rar",
    ".7z",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".jar",
    ".war",
    ".ear",
    ".cab",
    # Binary documents
    ".pdf",
    ".doc",
    ".ppt",  # Note: .docx, .xlsx, .pptx are XML-based (zip archives)
    # Databases & Data Files
    ".db",
    ".sqlite",
    ".mdb",
    ".accdb",
    ".dbf",
    ".dat",  # .dat is generic
    # Fonts
    ".ttf",
    ".otf",
    ".woff",
    ".woff2",
    ".eot",
    # Proprietary design formats
    ".psd",
    ".ai",
    ".indd",
    ".xd",
    ".fig",
    # Virtualization & Disk Images
    ".iso",
    ".img",
    ".vhd",
    ".vhdx",
    ".vmdk",
    # Other common binary types
    ".bak",
    ".tmp",
    ".lock",
    ".swo",
    ".swp",
}

# Line Ending Constants
LF = "\n"
CRLF = "\r\n"


# --- Token Counting Function ---
def _count_tokens_in_file_content(
    file_path_str: str, encoding_name: str = "cl100k_base"
) -> int:
    """
    Reads a file and counts the number of tokens using a specified tiktoken encoding.

    Args:
        file_path_str (str): The path to the file.
        encoding_name (str): The name of the encoding to use (e.g., "cl100k_base", "p50k_base").
                             "cl100k_base" is the encoding used by gpt-4, gpt-3.5-turbo.

    Returns:
        int: The number of tokens in the file.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        Exception: For other issues like encoding errors or tiktoken issues.
    """
    if not os.path.exists(file_path_str):
        # This check is somewhat redundant if called after file creation,
        # but good for a generic helper.
        raise FileNotFoundError(f"Error: File not found at {file_path_str}")

    try:
        with open(file_path_str, "r", encoding="utf-8") as f:
            text_content = f.read()
    except UnicodeDecodeError:
        logger.debug(
            f"UTF-8 decoding failed for {file_path_str}, trying with error replacement."
        )
        with open(file_path_str, "rb") as f:
            byte_content = f.read()
        text_content = byte_content.decode("utf-8", errors="replace")
    except Exception as e:
        raise Exception(f"Error reading file {file_path_str} for token counting: {e}")

    try:
        encoding = tiktoken.get_encoding(encoding_name)
        tokens = encoding.encode(text_content)
        return len(tokens)
    except Exception as e:
        raise Exception(
            f"Error using tiktoken: {e}. Ensure tiktoken is installed and encoding_name is valid."
        )


# --- Helper Functions ---


def _generate_filename_content_hash(files_to_process: list[tuple[Path, str]]) -> str:
    """
    Generates a SHA256 hash from the count, names, and modification timestamps of the given files.

    Args:
        files_to_process: A list of tuples, where each tuple contains (absolute_path, relative_path).

    Returns:
        A short (12-character) hex digest of the hash, or an empty string if no files.
    """
    if not files_to_process:
        return ""

    file_count = len(files_to_process)
    relative_paths = []
    timestamps = []

    # Ensure relative_paths are strings for consistent processing
    for abs_path, rel_path_obj in files_to_process:
        relative_paths.append(str(rel_path_obj)) # rel_path_obj could be Path or str
        try:
            mtime = os.path.getmtime(abs_path)
            timestamps.append(str(mtime))
        except OSError as e:
            logger.warning(f"Could not get mtime for {abs_path}: {e}. Using placeholder for hash.")
            # To ensure hash changes if a file's mtime becomes unreadable or file is inaccessible
            timestamps.append(f"ERROR_MTIME_{str(rel_path_obj)}")


    # Sort components for consistent hash order
    relative_paths.sort()
    timestamps.sort() # Timestamps are now strings, some might be error placeholders
    
    # Construct a representative string
    hash_input_parts = []
    hash_input_parts.append(f"count:{file_count}")
    hash_input_parts.append(f"names:{','.join(relative_paths)}")
    hash_input_parts.append(f"mtimes:{','.join(timestamps)}") # Timestamps list might be empty if all errored
    
    combined_info_str = ";".join(hash_input_parts)
    
    hash_obj = hashlib.sha256(combined_info_str.encode("utf-8"))
    return hash_obj.hexdigest()[:12] # Return first 12 chars of the hash


def get_file_size_formatted(size_in_bytes: int) -> str:
    """Formats file size into a human-readable string (Bytes, KB, MB)."""
    if size_in_bytes < 1024:
        return f"{size_in_bytes} Bytes"
    elif size_in_bytes < (1024 * 1024):  # Less than 1 MB
        return f"{size_in_bytes / 1024:.2f} KB"
    else:  # 1 MB or more
        return f"{size_in_bytes / (1024 * 1024):.2f} MB"


def get_file_separator(
    file_info: Path, relative_path: str, style: str, linesep: str
) -> str:
    """
    Generates the file separator string based on the chosen style.

    Args:
        file_info: Path object for the file.
        relative_path: Relative path string of the file from the source directory.
        style: The separator style ('Standard', 'Detailed', 'Markdown', 'MachineReadable').
        linesep: The line separator string (LF or CRLF) to use.

    Returns:
        The formatted separator string.
    """
    stat_info = file_info.stat()
    mod_time = datetime.datetime.fromtimestamp(stat_info.st_mtime)
    mod_date_str = mod_time.strftime("%Y-%m-%d %H:%M:%S")
    file_size_bytes = stat_info.st_size
    file_size_hr = get_file_size_formatted(file_size_bytes)
    file_ext = file_info.suffix.lower() if file_info.suffix else "[no extension]"

    # Calculate checksum for all styles that will use it in the header
    checksum_sha256 = ""
    if style in ["Standard", "Detailed", "Markdown", "MachineReadable"]:
        try:
            # Read content once for checksum. This content is also written later.
            content_for_checksum = file_info.read_text(
                encoding="utf-8", errors="ignore"
            )
            checksum_sha256 = hashlib.sha256(
                content_for_checksum.encode("utf-8")
            ).hexdigest()
        except Exception as e:
            logger.warning(
                f"Could not read file {file_info} for checksum calculation: {e}. Checksum will be empty or not included."
            )
            checksum_sha256 = (
                "[CHECKSUM_ERROR]"  # Indicate error clearly if it was attempted
            )

    if style == "None":
        # Return an empty string as separator when 'None' style is selected
        return ""
    elif style == "Standard":
        if checksum_sha256 and checksum_sha256 != "[CHECKSUM_ERROR]":
            return (
                f"======= {relative_path} | CHECKSUM_SHA256: {checksum_sha256} ======"
            )
        else:
            return f"======= {relative_path} ======"
    elif style == "Detailed":
        separator_lines = [
            "========================================================================================",
            f"== FILE: {relative_path}",
            f"== DATE: {mod_date_str} | SIZE: {file_size_hr} | TYPE: {file_ext}",
        ]
        if checksum_sha256 and checksum_sha256 != "[CHECKSUM_ERROR]":
            separator_lines.append(f"== CHECKSUM_SHA256: {checksum_sha256}")
        separator_lines.append(
            "========================================================================================"
        )
        return linesep.join(separator_lines)
    elif style == "Markdown":
        md_lang_hint = (
            file_info.suffix[1:]
            if file_info.suffix and len(file_info.suffix) > 1
            else ""
        )
        metadata_line = f"**Date Modified:** {mod_date_str} | **Size:** {file_size_hr} | **Type:** {file_ext}"
        if checksum_sha256 and checksum_sha256 != "[CHECKSUM_ERROR]":
            metadata_line += f" | **Checksum (SHA256):** {checksum_sha256}"
        separator_lines = [
            f"## {relative_path}",
            metadata_line,
            "",  # Empty line before code block
            f"```{md_lang_hint}",
        ]
        return linesep.join(separator_lines)
    elif style == "MachineReadable":
        # Generate a unique UUID for this file block
        file_uuid = str(uuid.uuid4())

        # Create metadata for the file
        meta = {
            "original_filepath": str(relative_path),
            "original_filename": os.path.basename(relative_path),
            "timestamp_utc_iso": datetime.datetime.fromtimestamp(
                stat_info.st_mtime, tz=datetime.timezone.utc
            )
            .isoformat()
            .replace("+00:00", "Z"),
            "type": file_ext,
            "size_bytes": file_size_bytes,
            "checksum_sha256": (
                checksum_sha256 if checksum_sha256 != "[CHECKSUM_ERROR]" else ""
            ),
        }

        json_meta = json.dumps(meta, indent=4)

        # Create the new format with UUIDs for metadata and content blocks
        separator_lines = [
            f"--- PYMK1F_BEGIN_FILE_METADATA_BLOCK_{file_uuid} ---",
            "METADATA_JSON:",
            json_meta,
            f"--- PYMK1F_END_FILE_METADATA_BLOCK_{file_uuid} ---",
            f"--- PYMK1F_BEGIN_FILE_CONTENT_BLOCK_{file_uuid} ---",
        ]
        return linesep.join(separator_lines)
    else:  # Should not happen due to argparse choices
        logger.warning(f"Unknown separator style '{style}'. Falling back to basic.")
        return f"--- {relative_path} ---"


def get_closing_separator(style: str, linesep: str) -> str | None:
    """
    Generates the closing separator string, if any.

    Args:
        style: The separator style.
        linesep: The line separator string (LF or CRLF) to use.

    Returns:
        The closing separator string, or None if no closing separator is needed.
    """
    if style == "None":
        return ""
    elif style == "Markdown":
        return "```"
    elif style == "MachineReadable":
        # The file_uuid is automatically added when writing the file in _write_combined_data
        # We just return a simple closing marker. The UUID from the opening marker will be reused.
        return "--- PYMK1F_END_FILE_CONTENT_BLOCK_{{file_uuid}} ---"
    return None


# --- Refactored Helper Functions for main() ---


def _configure_logging_settings(
    verbose: bool, chosen_linesep: str, output_file_path: Optional[Path] = None,
    minimal_output: bool = False, quiet: bool = False
) -> None:
    """Configures logging level based on verbosity and sets up file logging.

    Args:
        verbose: Whether to enable verbose (DEBUG) logging
        chosen_linesep: The line separator being used (LF or CRLF)
        output_file_path: The output file path, used to create a parallel log file
        minimal_output: If True, no log file will be created
        quiet: If True, suppress all console output
    """
    # If quiet mode is enabled, disable all logging to console
    if quiet:
        # Set the root logger level to ERROR (only critical errors will show)
        logging.getLogger().setLevel(logging.ERROR)
        # Remove any existing console handlers
        for handler in logging.getLogger().handlers[:]:
            if isinstance(handler, logging.StreamHandler) and handler.stream in (sys.stdout, sys.stderr):
                logging.getLogger().removeHandler(handler)
        return
    
    # Set the root logger level based on verbosity
    log_level = logging.DEBUG if verbose else logging.INFO
    # logging.getLogger().setLevel(log_level) # Don't set root logger level here for file logging part

    # Configure file logging for the specific "makeonefile" logger
    logger_instance = logging.getLogger("makeonefile")
    logger_instance.setLevel(log_level) # Set level on our specific logger

    # Remove any old instance of our specific file handler from our logger if we are reconfiguring
    global file_handler # Ensure we are referencing the global one
    if file_handler in logger_instance.handlers:
        logger_instance.removeHandler(file_handler)
        file_handler.close()
        file_handler = None # Explicitly reset before potential new assignment

    # Configure file logging if an output path is provided and minimal_output is False
    # The guard "file_handler is None" is important if this function could be called multiple times
    # with the intent to ADD a handler if one isn't already set for this module.
    if output_file_path and file_handler is None and not minimal_output:
        log_file_path = output_file_path.with_suffix(".log")
        try:
            new_file_handler = logging.FileHandler(log_file_path, mode="w", encoding="utf-8")
            new_file_handler.setLevel(log_level)
            new_file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)-8s: %(message)s"))
            logger_instance.addHandler(new_file_handler)
            file_handler = new_file_handler # Store the new handler globally for this module
        except Exception as e:
            # Use the module-level logger to log this error, it will go to console via basicConfig.
            logger.error(f"Failed to create log file at {log_file_path}: {e}")

    if verbose:
        logger.debug("Verbose mode enabled.")
        logger.debug(f"Using line ending: {'LF' if chosen_linesep == LF else 'CRLF'}")
        if minimal_output:
            logger.debug("Minimal output mode enabled - no auxiliary files will be created.")
        

def _resolve_and_validate_source_path(source_directory_str: str) -> Path:
    """Resolves and validates the source directory path."""
    try:
        source_dir = Path(source_directory_str).resolve(strict=True)
        if not source_dir.is_dir():
            logger.error(f"Source path '{source_dir}' is not a directory.")
            sys.exit(1)
        return source_dir
    except FileNotFoundError:
        logger.error(f"Source directory '{source_directory_str}' not found.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error resolving source directory '{source_directory_str}': {e}")
        sys.exit(1)


def _prepare_output_file_path(output_file_str: str, add_timestamp: bool) -> Path:
    """Prepares the output file path, including timestamp if requested."""
    output_file_path = Path(output_file_str).resolve()
    if add_timestamp:
        timestamp = datetime.datetime.now().strftime("_%Y%m%d_%H%M%S")
        output_file_path = output_file_path.with_name(
            f"{output_file_path.stem}{timestamp}{output_file_path.suffix}"
        )
        logger.debug(f"Output filename with timestamp: {output_file_path.name}")
    return output_file_path


def _handle_output_file_overwrite_and_creation(
    output_file_path: Path, force: bool, chosen_linesep: str
) -> None:
    """Handles output file existence, overwrite confirmation, and parent directory creation."""
    if output_file_path.exists() and output_file_path.is_file():
        if force:
            logger.warning(
                f"Output file '{output_file_path}' exists. Overwriting due to --force."
            )
            try:
                output_file_path.unlink()
            except Exception as e:
                logger.error(
                    f"Could not remove existing output file '{output_file_path}': {e}"
                )
                sys.exit(1)
        else:
            try:
                confirmation = input(
                    f"Output file '{output_file_path}' already exists. Overwrite? (y/N): "
                )
                if confirmation.lower() != "y":
                    logger.info("Operation cancelled by user.")
                    sys.exit(0)
                output_file_path.unlink()
                logger.debug(f"Overwriting existing output file '{output_file_path}'.")
            except KeyboardInterrupt:
                logger.info(f"{chosen_linesep}Operation cancelled by user (Ctrl+C).")
                sys.exit(0)
            except Exception as e:
                logger.error(
                    f"Could not remove existing output file '{output_file_path}': {e}"
                )
                sys.exit(1)
    elif output_file_path.exists() and not output_file_path.is_file():
        logger.error(
            f"Output path '{output_file_path}' exists but is not a file (e.g., it's a directory)."
        )
        sys.exit(1)

    try:
        output_file_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(
            f"Could not create output directory '{output_file_path.parent}': {e}"
        )
        sys.exit(1)


def _build_exclusion_set(additional_excludes: list[str], use_default_excludes: bool = True) -> set[str]:
    """Builds the set of lowercased directory names to exclude.
    
    Args:
        additional_excludes: Additional directory names to exclude
        use_default_excludes: Whether to include the default excluded directory names
        
    Returns:
        Set of directory names to exclude (all lowercase)
    """
    all_excluded_dir_names_lower = set()
    
    if use_default_excludes:
        all_excluded_dir_names_lower = {name.lower() for name in DEFAULT_EXCLUDED_DIR_NAMES}
        
    all_excluded_dir_names_lower.update(name.lower() for name in additional_excludes)
    
    logger.debug(
        f"Effective excluded directory names (case-insensitive): {sorted(list(all_excluded_dir_names_lower))}"
    )
    return all_excluded_dir_names_lower


def _deduplicate_paths(path_objects: List[Path]) -> List[Path]:
    """
    Deduplicate paths by removing any paths that are children of other paths in the list.

    Args:
        path_objects: List of Path objects to deduplicate

    Returns:
        List of Path objects with no child paths if their parent is already in the list
    """
    if not path_objects:
        return []

    # Sort by path length (shortest first) to ensure we process parent directories first
    path_objects.sort(key=lambda p: len(p.parts))

    # Keep track of paths to include (initially all)
    include_paths = set(path_objects)

    # Check each path to see if it's a child of any other path
    for i, path in enumerate(path_objects):
        # Skip if already excluded
        if path not in include_paths:
            continue

        # Check against all other paths
        for other_path in path_objects[i + 1 :]:
            # If this path is a parent of another path, exclude the child
            try:
                # Use str path comparison for Python 3.7+ compatibility (instead of is_relative_to from 3.9+)
                other_path_str = str(other_path.absolute())
                path_str = str(path.absolute())

                # Check if other_path is a subpath of path (e.g., path="/a/b", other_path="/a/b/c")
                # Ensure it's not just a common prefix (e.g., path="/a/b", other_path="/a/b_ext")
                if (
                    len(other_path_str) > len(path_str)
                    and other_path_str.startswith(path_str)
                    and other_path_str[len(path_str)] == os.sep
                ):
                    include_paths.discard(other_path)
            except (ValueError, RuntimeError):
                # Handle potential path resolution issues
                continue

    return sorted(include_paths)


def _process_paths_from_input_file(input_file_path: Path) -> List[Path]:
    """
    Process a file containing paths (one per line) and return a list of Path objects.

    Args:
        input_file_path: Path to the input file containing paths to process

    Returns:
        List of deduplicated paths with proper parent-child handling
    """
    paths = []
    input_file_dir = input_file_path.parent

    try:
        with open(input_file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue  # Skip empty lines and comments

                path_obj = Path(line)
                # If the path is relative (doesn't have a root), make it relative to the input file's directory
                if not path_obj.is_absolute():
                    path_obj = (input_file_dir / path_obj).resolve()
                else:
                    path_obj = path_obj.expanduser().resolve()

                paths.append(path_obj)

        # Deduplicate paths (keep parents, remove children)
        return _deduplicate_paths(paths)
    except Exception as e:
        logger.error(f"Error processing input file: {e}")
        return []


def _load_exclude_paths_from_file(exclude_paths_file: str) -> Set[str]:
    """Load paths to exclude from a file.

    Args:
        exclude_paths_file: Path to a file containing paths to exclude (one per line).
            Format: Each line contains a single path to exclude. The paths are matched exactly
            as written. Empty lines and lines starting with '#' are treated as comments and ignored.
            Example file content:
                # This is a comment
                dir1/dir2
                project/file.txt

    Returns:
        A set of normalized paths to exclude
    """
    exclude_paths = set()
    if not exclude_paths_file:
        return exclude_paths

    try:
        exclude_file_path = Path(exclude_paths_file).resolve()
        if not exclude_file_path.exists():
            logger.warning(f"Exclude paths file not found: {exclude_file_path}")
            return exclude_paths

        with open(exclude_file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):  # Skip empty lines and comments
                    # Normalize path (OS-appropriate path separators)
                    normalized_path = str(Path(line))
                    exclude_paths.add(normalized_path)

        logger.info(
            f"Loaded {len(exclude_paths)} paths to exclude from {exclude_file_path}"
        )
    except Exception as e:
        logger.error(f"Error loading exclude paths file: {e}")

    return exclude_paths


def _is_file_excluded(
    file_path: Path, args: argparse.Namespace, all_excluded_dir_names_lower: Set[str]
) -> bool:
    """Checks if a file should be excluded based on various criteria."""
    # Check if the path is in the exclude paths list
    if hasattr(args, "exclude_paths") and args.exclude_paths:
        rel_path_str = str(
            file_path.relative_to(args.source_base_dir)
            if hasattr(args, "source_base_dir")
            else file_path
        )
        if rel_path_str in args.exclude_paths:
            if args.verbose:
                logger.debug(
                    f"Excluding path (exact match from exclude file): {rel_path_str}"
                )
            return True

    if not args.include_dot_files and file_path.name.startswith("."):
        if args.verbose:
            logger.debug(f"Excluding dot file: {file_path}")
        return True

    if (
        not args.include_binary_files
        and file_path.suffix.lower() in BINARY_FILE_EXTENSIONS
    ):
        if args.verbose:
            logger.debug(
                f"Excluding binary file: {file_path} (extension: {file_path.suffix.lower()})"
            )
        return True
    
    # Check if the file extension is in the exclude-extensions list
    if hasattr(args, "exclude_extensions") and args.exclude_extensions:
        if file_path.suffix.lower() in args.exclude_extensions:
            if args.verbose:
                logger.debug(
                    f"Excluding file with extension filter: {file_path} (extension: {file_path.suffix.lower()})"
                )
            return True
    
    # Check if include-extensions is set and this file's extension is not in the list
    if hasattr(args, "include_extensions") and args.include_extensions:
        if file_path.suffix.lower() not in args.include_extensions:
            if args.verbose:
                logger.debug(
                    f"Excluding file not matching include extension filter: {file_path} (extension: {file_path.suffix.lower()})"
                )
            return True

    # Check if any parent directory is in the global exclude list
    # This iterates from file_path.parent up to the root.
    p = file_path.parent
    while p != p.parent:  # Stop when p is the root (e.g. '/' or 'C:\')
        if p.name and p.name.lower() in all_excluded_dir_names_lower:
            if args.verbose:
                logger.debug(
                    f"Excluding file '{file_path}' because parent directory '{p.name}' (path: {p}) is in exclude list."
                )
            return True
        # p.parent of root is root itself, so this condition handles termination.
        if p == p.parent:
            break
        p = p.parent
    return False


def _gather_files_to_process(
    source_dir: Path,
    args: argparse.Namespace,
    all_excluded_dir_names_lower: Set[str],
    input_paths: Optional[List[Path]] = None,
    ignore_symlinks: bool = True,
) -> List[Tuple[Path, str]]:
    """
    Gather files to process, either from a source directory or from a list of input paths.

    Args:
        source_dir: The source directory (used when not using input paths)
        args: Command line arguments
        all_excluded_dir_names_lower: Set of directory names to exclude (lowercase)
        input_paths: Optional list of paths from input file

    Returns:
        List of tuples containing (file_path, relative_path)
    """
    files_to_process = []
    # Use a set to track absolute paths of files already added to avoid duplicates
    # especially when using --input-file which might list overlapping paths or individual files within listed dirs.
    added_file_absolute_paths: Set[str] = set()

    if input_paths is not None:
        logger.info(
            f"Processing {len(input_paths)} unique path(s) from input file '{args.input_file}'..."
        )
        for (
            item_path
        ) in input_paths:  # Each item_path is an absolute, resolved, deduplicated path
            if (
                not item_path.exists()
            ):  # Should be rare due to prior checks but good for safety
                logger.warning(f"Path from input file no longer exists: {item_path}")
                continue

            if item_path.is_file():
                abs_path_str = str(item_path.resolve())
                if abs_path_str in added_file_absolute_paths:
                    if args.verbose:
                        logger.debug(f"Skipping already added file: {item_path}")
                    continue
                if not _is_file_excluded(item_path, args, all_excluded_dir_names_lower):
                    files_to_process.append((item_path, item_path.name))
                    added_file_absolute_paths.add(abs_path_str)
                # else: _is_file_excluded logs if verbose

            elif item_path.is_dir():
                # Check if the directory itself is in the excluded names list
                if item_path.name.lower() in all_excluded_dir_names_lower:
                    if args.verbose:
                        logger.debug(
                            f"Skipping directory '{item_path}' from input list as its name is excluded."
                        )
                    continue

                if args.verbose:
                    logger.debug(f"Scanning directory from input file: {item_path}")
                for file_path_in_dir in item_path.rglob("*"):
                    if file_path_in_dir.is_file():
                        abs_path_str = str(file_path_in_dir.resolve())
                        if abs_path_str in added_file_absolute_paths:
                            if args.verbose:
                                logger.debug(
                                    f"Skipping already added file: {file_path_in_dir}"
                                )
                            continue
                        if not _is_file_excluded(
                            file_path_in_dir, args, all_excluded_dir_names_lower
                        ):
                            relative_path = file_path_in_dir.relative_to(item_path)
                            files_to_process.append(
                                (file_path_in_dir, str(relative_path))
                            )
                            added_file_absolute_paths.add(abs_path_str)
                        # else: _is_file_excluded logs if verbose
    else:
        # Original directory walking logic
        logger.info(f"Scanning files in '{source_dir}'...")
        if args.verbose:
            logger.debug(
                f"  Exclusion settings: include_dot_files={args.include_dot_files}, "
                f"include_binary_files={args.include_binary_files}"
            )
            logger.debug(
                f"  Excluded directory names (case-insensitive): {sorted(list(all_excluded_dir_names_lower))}"
            )

        for root, dirs, files in os.walk(source_dir):
            root_path = Path(root)

            # Skip excluded directories
            dirs[:] = [d for d in dirs if d.lower() not in all_excluded_dir_names_lower]

            # Skip symlink directories if ignore_symlinks is True
            if ignore_symlinks:
                dirs[:] = [d for d in dirs if not (root_path / d).is_symlink()]

            for file in files:
                file_path = root_path / file
                if _is_file_excluded(file_path, args, all_excluded_dir_names_lower):
                    continue

                # Skip symlinks if ignore_symlinks is True
                if ignore_symlinks and file_path.is_symlink():
                    logger.debug(f"Skipping symlink: {file_path}")
                    continue

                relative_path = file_path.relative_to(source_dir)
                files_to_process.append((file_path, str(relative_path)))

    return sorted(files_to_process, key=lambda x: str(x[1]).lower())


def _write_file_paths_list(
    output_file_path: Path, files_to_process: list[tuple[Path, str]], minimal_output: bool = False
):
    """
    Writes a list of file paths to a text file.

    Args:
        output_file_path: The path to use as the base for the file list output file.
        files_to_process: List of (file_path, relative_path) tuples to write to the file.
        minimal_output: If True, no file list will be created

    Returns:
        Path to the created file list or None if minimal_output is True.
    """
    if minimal_output:
        logger.debug("Skipping file paths list creation (minimal output mode)")
        return None
        
    file_list_path = output_file_path.with_name(f"{output_file_path.stem}_filelist.txt")

    logger.info(f"Writing file paths list to {file_list_path}")

    # Extract unique relative paths and sort them
    unique_paths = sorted(set(rel_path for _, rel_path in files_to_process))

    with open(file_list_path, "w", encoding="utf-8") as f:
        for rel_path in unique_paths:
            f.write(f"{rel_path}\n")

    logger.info(f"Wrote {len(unique_paths)} file paths to {file_list_path}")
    return file_list_path


def _write_directory_paths_list(
    output_file_path: Path, files_to_process: list[tuple[Path, str]], minimal_output: bool = False
):
    """
    Writes a list of unique directory paths to a text file.

    This function extracts all unique directories from the list of processed files,
    including all parent directories in the path hierarchy. For example, if a file is
    located at 'src/components/Button.js', both 'src' and 'src/components' will be
    included in the directory list. The directories are sorted alphabetically in the
    output file.

    Args:
        output_file_path: The path to use as the base for the directory list output file.
            The output will be named '{output_file_stem}_dirlist.txt'.
        files_to_process: List of (file_path, relative_path) tuples to extract directories from.
            Only the relative_path part is used to determine directories.
        minimal_output: If True, no directory list will be created

    Returns:
        Path to the created directory list file or None if minimal_output is True.
    """
    if minimal_output:
        logger.debug("Skipping directory paths list creation (minimal output mode)")
        return None
        
    dir_list_path = output_file_path.with_name(f"{output_file_path.stem}_dirlist.txt")

    logger.info(f"Writing directory paths list to {dir_list_path}")

    # Extract unique directory paths and sort them
    unique_dirs = set()

    for _, rel_path in files_to_process:
        # Get the parent directory of each file
        path_obj = Path(rel_path)
        # Add all parent directories
        current_path = path_obj.parent
        while str(current_path) != ".":
            unique_dirs.add(str(current_path))
            current_path = current_path.parent

    # Sort the directories alphabetically
    sorted_dirs = sorted(unique_dirs)

    with open(dir_list_path, "w", encoding="utf-8") as f:
        for dir_path in sorted_dirs:
            f.write(f"{dir_path}\n")

    logger.info(f"Wrote {len(sorted_dirs)} unique directory paths to {dir_list_path}")
    return dir_list_path


def _write_combined_data(
    output_file_path: Path,
    files_to_process: list[tuple[Path, str]],
    args: argparse.Namespace,
    chosen_linesep: str,
) -> int:
    """Writes the combined file data to the output file and returns the count of processed files."""
    total_files = len(files_to_process)
    logger.info(f"Processing {total_files} file(s) for inclusion...")
    file_counter = 0
    try:
        with open(output_file_path, "w", encoding="utf-8") as outfile:
            for file_info, rel_path_str in files_to_process:
                file_counter += 1
                logger.debug(
                    f"Processing file ({file_counter}/{total_files}): {file_info.name} (Rel: {rel_path_str})"
                )

                separator_text = get_file_separator(
                    file_info, rel_path_str, args.separator_style, chosen_linesep
                )

                # For MachineReadable, we need to extract the UUID from the separator text
                current_file_uuid = None
                if args.separator_style == "MachineReadable":
                    # Extract the UUID from the separator text
                    import re

                    uuid_match = re.search(
                        r"PYMK1F_BEGIN_FILE_METADATA_BLOCK_([a-f0-9-]+)", separator_text
                    )
                    current_file_uuid = (
                        uuid_match.group(1) if uuid_match else str(uuid.uuid4())
                    )
                    outfile.write(separator_text)
                elif args.separator_style == "None":
                    # For None style, don't add any separator or newline
                    pass
                else:
                    outfile.write(separator_text + chosen_linesep)

                # Add an additional blank line for Standard and Detailed styles
                # after their header and before the actual file content begins.
                if args.separator_style in ["Standard", "Detailed"]:
                    outfile.write(chosen_linesep)

                content = ""  # Initialize content to ensure it's defined
                try:
                    content = file_info.read_text(encoding="utf-8", errors="ignore")
                    outfile.write(content)
                except Exception as e:
                    error_message = (
                        f"[ERROR: UNABLE TO READ FILE '{file_info}'. REASON: {e}]"
                    )
                    logger.warning(error_message)
                    outfile.write(error_message + chosen_linesep)

                # Ensure content block is followed by a newline if it didn't originally have one,
                # for styles where the closing separator doesn't already handle this.
                if (
                    args.separator_style != "MachineReadable"
                    and content
                    and not content.endswith(("\n", "\r"))
                ):
                    outfile.write(chosen_linesep)
                # No special handling needed here if content is empty, as the subsequent
                # closing_separator and inter-file newlines will still be added correctly.

                closing_separator_text = get_closing_separator(
                    args.separator_style, chosen_linesep
                )
                if closing_separator_text:
                    # For MachineReadable, insert the UUID into the closing separator
                    if args.separator_style == "MachineReadable" and current_file_uuid:
                        closing_separator_text = closing_separator_text.replace(
                            "{{file_uuid}}", current_file_uuid
                        )

                    # Write the closing separator
                    outfile.write(closing_separator_text + chosen_linesep)

                # Add a separating newline IF this is not the last file.
                # This serves as the blank line between file entries for all styles except "None".
                if file_counter < total_files and args.separator_style != "None":
                    outfile.write(chosen_linesep)
        return file_counter
    except IOError as e:
        logger.error(f"An I/O error occurred writing to '{output_file_path}': {e}")
        if file_handler:
            file_handler.close()
        sys.exit(1)  # Exit with error for IO issues
    except Exception as e:
        logger.error(
            f"An unexpected error occurred during file processing: {e}", exc_info=True
        )
        if file_handler:
            file_handler.close()
        sys.exit(1)  # Exit with an error code


# --- Archive Creation Function ---


def _create_archive(
    output_file_path: Path,
    files_to_process: list[tuple[Path, str]],
    archive_type: str,
    verbose_logging: bool,
) -> None:
    """
    Creates an archive (zip or tar.gz) of the processed files.

    Args:
        output_file_path: The path to the main combined output file (used for naming the archive).
        files_to_process: A list of tuples, where each tuple contains:
                          - Path: The absolute Path object of the file to add.
                          - str: The relative path string to use for the file within the archive.
        archive_type: The type of archive to create ('zip' or 'tar.gz').
        verbose_logging: Boolean indicating if verbose logging is enabled.
    """
    if not files_to_process:
        logger.info("No files to archive. Skipping archive creation.")
        return

    base_name = output_file_path.stem
    archive_suffix = ".zip" if archive_type == "zip" else ".tar.gz"
    archive_file_name = f"{base_name}_backup{archive_suffix}"
    archive_file_path = output_file_path.with_name(archive_file_name)

    logger.info(f"Creating '{archive_type}' archive at: '{archive_file_path}'")

    try:
        if archive_type == "zip":
            with zipfile.ZipFile(archive_file_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for abs_path, rel_path_in_archive in files_to_process:
                    if verbose_logging:
                        logger.debug(
                            f"Adding to zip: {abs_path} as {rel_path_in_archive}"
                        )
                    zf.write(abs_path, arcname=rel_path_in_archive)
        elif archive_type == "tar.gz":
            with tarfile.open(archive_file_path, "w:gz") as tf:
                for abs_path, rel_path_in_archive in files_to_process:
                    if verbose_logging:
                        logger.debug(
                            f"Adding to tar.gz: {abs_path} as {rel_path_in_archive}"
                        )
                    tf.add(abs_path, arcname=rel_path_in_archive)
        else:
            logger.error(
                f"Unsupported archive type: {archive_type}. Skipping archive creation."
            )
            return

        logger.info(
            f"Successfully created archive '{archive_file_path}' with {len(files_to_process)} file(s)."
        )

    except FileNotFoundError as e:
        logger.error(
            f"Error creating archive '{archive_file_path}': A file to be added was not found. {e}"
        )
    except PermissionError as e:
        logger.error(
            f"Error creating archive '{archive_file_path}': Permission denied. {e}"
        )
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while creating archive '{archive_file_path}': {e}",
            exc_info=verbose_logging,
        )


# --- Main Script Logic ---


def main():
    """
    Main function to parse arguments and orchestrate the file combination process.
    """
    # Start timing the execution
    start_time = time.time()
    parser = argparse.ArgumentParser(
        description="Combines the content of multiple text files into a single output file, with metadata. "
        "Optionally, creates a backup archive (zip or tar.gz) of the processed files. "
        "Useful for code reviews, documentation bundling, or sharing multiple files as one.",
        epilog="""Examples:
  %(prog)s --source-directory "./src" --output-file "combined_files.txt"
  %(prog)s -s "/home/user/projects/my_app" -o "/tmp/app_bundle.md" -t --separator-style Markdown --force
  %(prog)s -s . -o archive.txt --additional-excludes "docs_archive" "test_data" --include-dot-files --line-ending crlf
  %(prog)s -s ./config_files --include-dot-files --include-binary-files -o all_configs.txt --verbose
  %(prog)s -i ./file_list.txt -o bundle.all --create-archive --archive-type tar.gz
  %(prog)s -s ./src -o bundle.txt --include-extensions .txt .json .md --exclude-extensions .tmp
  %(prog)s -s ./project -o all_files.txt --no-default-excludes
  %(prog)s -s ./src -o combined.txt --minimal-output
  %(prog)s -s ./src -o combined.txt --quiet
  %(prog)s -s ./src -o combined.txt --skip-output-file""",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # Input source options are defined in a mutually exclusive group below
    parser.add_argument(
        "-o",
        "--output-file",
        type=str,
        required=True,
        help="Path where the combined output file will be created.",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force overwrite of output file without prompting.",
    )
    parser.add_argument(
        "-t",
        "--add-timestamp",
        action="store_true",
        help="Add a timestamp (_yyyyMMdd_HHmmss) to the output filename.",
    )
    parser.add_argument(
        "--filename-mtime-hash",
        action="store_true",
        help="Append a hash of all included file modification timestamps to the output filename. "
             "This helps version the output based on source file mtime changes.",
    )

    parser.add_argument(
        "--additional-excludes",
        type=str,
        nargs="*",
        default=[],
        metavar="DIR_NAME",
        help="Space-separated list of additional directory NAMES to exclude (e.g., 'obj', 'debug'). Case-insensitive.",
    )
    parser.add_argument(
        "--no-default-excludes",
        action="store_true",
        help="Disable the default directory exclusions. This allows including content from directories like 'node_modules', '.git', etc.",
    )
    parser.add_argument(
        "--include-extensions",
        type=str,
        nargs="*",
        metavar="EXT",
        help="Space-separated list of file extensions to include (e.g., '.txt', '.json'). Only files with these extensions will be included.",
    )
    parser.add_argument(
        "--exclude-extensions",
        type=str,
        nargs="*",
        metavar="EXT",
        help="Space-separated list of file extensions to exclude (e.g., '.tmp', '.log').",
    )
    parser.add_argument(
        "--exclude-paths-file",
        type=str,
        help="Path to a file containing exact paths to exclude (one per line). Paths are matched exactly as written. Empty lines and lines starting with '#' are ignored.",
    )
    parser.add_argument(
        "--include-dot-files",
        action="store_true",
        help="Include files that start with a dot (e.g., .gitignore). Dot directories (e.g. .git) are generally excluded by default_excluded_dir_names.",
    )
    parser.add_argument(
        "--include-binary-files",
        action="store_true",
        help="Attempt to include files with binary extensions. Content may be unreadable. Use with caution.",
    )
    parser.add_argument(
        "--separator-style",
        choices=["Standard", "Detailed", "Markdown", "MachineReadable", "None"],
        default="Detailed",
        help="Format of the separator between files. \n"
        "  'Standard': Simple path display.\n"
        "  'Detailed': Path, date, size, type (default).\n"
        "  'Markdown': Markdown H2 for path, metadata, and code block.\n"
        "  'MachineReadable': Uses unique boundary markers and JSON for robust splitting.\n"
        "  'None': No separator, files are concatenated without any information between them.",
    )
    parser.add_argument(
        "--line-ending",
        choices=["lf", "crlf"],
        default="lf",
        help="Line ending for script-generated separators/newlines. 'lf' (Unix) or 'crlf' (Windows). Default: lf. Does not change line endings of original file content.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output (DEBUG level logging).",
    )
    parser.add_argument(
        "--minimal-output",
        action="store_true",
        help="Generate only the combined output file, without any auxiliary files (no log file, file list, or directory list).",
    )
    parser.add_argument(
        "--skip-output-file",
        action="store_true",
        help="Execute all operations (logs, additional files, etc.) but skip writing the final .m1f.txt output file.",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress all console output. Script will run silently except for critical errors.",
    )
    parser.add_argument(
        "--create-archive",
        action="store_true",
        help="Create a backup archive (zip or tar.gz) of all processed files.",
    )
    parser.add_argument(
        "--archive-type",
        choices=["zip", "tar.gz"],
        default="zip",
        help="Type of archive to create if --create-archive is specified. Default: zip.",
    )

    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "-s",
        "--source-directory",
        type=str,
        help="Path to the directory containing the files to be combined.",
    )
    input_group.add_argument(
        "-i",
        "--input-file",
        type=str,
        help="Path to a text file containing a list of files and directories to process (one per line).",
    )

    args = parser.parse_args()

    # Process and normalize include/exclude extensions if provided
    if hasattr(args, "include_extensions") and args.include_extensions:
        # Normalize extensions to lowercase and ensure they start with a dot
        args.include_extensions = {
            ext.lower() if ext.startswith(".") else f".{ext.lower()}" 
            for ext in args.include_extensions
        }
        logger.debug(f"Including only files with extensions: {args.include_extensions}")
    
    if hasattr(args, "exclude_extensions") and args.exclude_extensions:
        # Normalize extensions to lowercase and ensure they start with a dot
        args.exclude_extensions = {
            ext.lower() if ext.startswith(".") else f".{ext.lower()}" 
            for ext in args.exclude_extensions
        }
        logger.debug(f"Excluding files with extensions: {args.exclude_extensions}")

    # Load exclude paths from file if specified
    if hasattr(args, "exclude_paths_file") and args.exclude_paths_file:
        args.exclude_paths = _load_exclude_paths_from_file(args.exclude_paths_file)
    else:
        args.exclude_paths = set()

    chosen_linesep = LF if args.line_ending == "lf" else CRLF

    output_file_path = _prepare_output_file_path(args.output_file, args.add_timestamp)

    # Configure logging with the output file path and quiet/verbose flags
    _configure_logging_settings(
        args.verbose, chosen_linesep, output_file_path, args.minimal_output, args.quiet
    )

    # Process input file if provided, otherwise use source directory
    input_paths = None
    if hasattr(args, "input_file") and args.input_file:
        input_file_path = Path(args.input_file).resolve()
        if not input_file_path.exists() or not input_file_path.is_file():
            logger.error(f"Input file not found: {input_file_path}")
            sys.exit(1)
        input_paths = _process_paths_from_input_file(input_file_path)
        logger.info(f"Found {len(input_paths)} paths to process from input file")

        # Use the first path's parent as the base directory for relative paths
        source_dir = input_paths[0].parent if input_paths else Path.cwd()
    else:
        source_dir = _resolve_and_validate_source_path(args.source_directory)

    # Set source base directory for path exclusion matching
    args.source_base_dir = source_dir

    # If we're not skipping the output file, handle overwrite prompting
    if not args.skip_output_file:
        # Handle prompting for overwrite in quiet mode
        if args.quiet and not args.force and output_file_path.exists():
            # In quiet mode with no force flag, exit if file exists
            sys.exit(1)  # Exit silently without warning

        # Output file path was already prepared for logging setup
        _handle_output_file_overwrite_and_creation(
            output_file_path, args.force, chosen_linesep
        )

    all_excluded_dir_names_lower = _build_exclusion_set(
        args.additional_excludes, 
        not args.no_default_excludes  # If --no-default-excludes is set, pass False here
    )
    
    if args.no_default_excludes:
        logger.info("Default directory exclusions are disabled.")
    
    files_to_process = _gather_files_to_process(
        source_dir,
        args,
        all_excluded_dir_names_lower,
        input_paths,
        ignore_symlinks=True,
    )

    # ---- START: Modification for filename-mtime-hash ----
    if args.filename_mtime_hash and files_to_process:
        logger.debug("Generating content hash for included files (count, names, mtimes)...")
        content_hash = _generate_filename_content_hash(files_to_process)
        if content_hash:
            output_file_path_obj = Path(args.output_file) # Original output file arg
            new_stem = f"{output_file_path_obj.stem}_{content_hash}"
            
            # Update args.output_file so that _prepare_output_file_path and logging use the hashed name
            args.output_file = str(output_file_path_obj.with_name(f"{new_stem}{output_file_path_obj.suffix}"))
            logger.info(f"Output filename will include content hash: {Path(args.output_file).name}")
        else:
            # This case should ideally not be reached if files_to_process is not empty,
            # as _generate_filename_content_hash is designed to return a hash even if mtimes fail.
            # It would only return empty if files_to_process was empty, but that's checked before.
            logger.warning("Could not generate content hash. Filename will not be modified by hash.")
    
    # Re-prepare output file path if it was modified by mtime hash, and apply execution timestamp if requested.
    # This ensures logging and overwrite checks use the potentially fully modified name.
    output_file_path = _prepare_output_file_path(args.output_file, args.add_timestamp)
    
    # Re-configure logging if the output_file_path has changed due to mtime_hash
    # This is crucial if the initial _configure_logging_settings was called with a non-hashed name.
    # We need to remove the old file handler if it exists and was based on a different name.
    global file_handler
    if file_handler:
        logging.getLogger().removeHandler(file_handler)
        file_handler.close()
        file_handler = None # Reset to allow reinitialization
    
    _configure_logging_settings(
        args.verbose, chosen_linesep, output_file_path, args.minimal_output, args.quiet
    )
    # ---- END: Modification for filename-mtime-hash ----
    

    if not files_to_process:
        logger.warning(f"No files found matching the criteria in '{source_dir}'.")
        
        # Only create the empty output file if we're not skipping output
        if not args.skip_output_file:
            try:
                with open(output_file_path, "w", encoding="utf-8") as f:
                    f.write(f"# No files processed from {source_dir}{chosen_linesep}")
                logger.info(
                    f"Empty output file (with a note) created at '{output_file_path}'."
                )
            except Exception as e:
                logger.error(
                    f"Could not create empty output file '{output_file_path}': {e}"
                )
                sys.exit(1)
        else:
            logger.info("Skipping output file creation as requested.")
            
        sys.exit(0)

    # Only create the output file if not skipping
    processed_count = 0
    if not args.skip_output_file:
        processed_count = _write_combined_data(
            output_file_path, files_to_process, args, chosen_linesep
        )
        logger.info(
            f"Successfully combined {processed_count} file(s) into '{output_file_path}'."
        )
    else:
        # Still count the files even if we're not writing them
        processed_count = len(files_to_process)
        logger.info(
            f"Found {processed_count} file(s) that would be processed, but skipped writing output file as requested."
        )

    # Write the list of file paths to a separate file, unless in minimal output mode
    if not args.minimal_output:
        file_list_path = _write_file_paths_list(output_file_path, files_to_process)

        # Write the list of directories to a separate file, unless in minimal output mode
        dir_list_path = _write_directory_paths_list(output_file_path, files_to_process)

    # --- Token Counting for Output File ---
    if not args.skip_output_file and processed_count > 0 and not args.minimal_output:  # Only count tokens if files were processed, output wasn't skipped, and not in minimal output mode
        try:
            logger.info(f"Attempting to count tokens in '{output_file_path.name}'...")
            # Defaulting to "cl100k_base" as it's common for GPT models
            token_count = _count_tokens_in_file_content(str(output_file_path))
            logger.info(
                f"The output file '{output_file_path.name}' contains approximately {token_count} tokens (using 'cl100k_base' encoding)."
            )
        except FileNotFoundError:
            # Should ideally not happen if _write_combined_data was successful
            logger.warning(
                f"Could not count tokens: Output file '{output_file_path.name}' not found after creation."
            )
        except Exception as e:
            logger.warning(f"Could not count tokens for '{output_file_path.name}': {e}")
            logger.warning(
                "  To enable token counting, please ensure 'tiktoken' library is installed (e.g., 'pip install tiktoken')."
            )
    elif output_file_path.exists() and not args.skip_output_file and not args.minimal_output:  # An empty note file might have been created
        logger.info(
            f"Output file '{output_file_path.name}' was created but is empty or contains no processed files; skipping token count."
        )

    # --- Archive Creation ---
    if args.create_archive and processed_count > 0:
        logger.info("Archive creation requested.")
        _create_archive(
            output_file_path,
            files_to_process,  # Pass the list of (abs_path, rel_path) tuples
            args.archive_type,
            args.verbose,
        )
    elif args.create_archive and processed_count == 0:
        logger.info(
            "Archive creation requested, but no files were processed. Skipping archive creation."
        )

    # Calculate and log the execution time
    end_time = time.time()
    execution_time = end_time - start_time
    # Format time as minutes and seconds if over 60 seconds, otherwise just seconds
    if execution_time >= 60:
        minutes, seconds = divmod(execution_time, 60)
        time_str = f"{int(minutes)}m {seconds:.2f}s"
    else:
        time_str = f"{execution_time:.2f}s"
    logger.info(f"Total execution time: {time_str}")

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Print newline so the prompt isn't on the same line as ^C
        print(f"{LF}Operation cancelled by user.", file=sys.stderr)
        sys.exit(130)  # Standard exit code for Ctrl+C
    except SystemExit as e:
        # Catch sys.exit() calls to ensure they propagate correctly
        sys.exit(e.code)
    except Exception as e:
        # Fallback for any unexpected errors not caught in main()
        logger.critical(f"An unexpected critical error occurred: {e}", exc_info=True)
        sys.exit(1)
