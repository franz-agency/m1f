# Copyright 2025 Franz und Franz GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Command-line interface for m1f.
"""

import argparse
import sys
from typing import Optional, NoReturn

from . import __version__

# Try to import colorama for colored help
try:
    from colorama import Fore, Style, init

    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False


class ColoredHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Custom help formatter with colors if available."""

    def _format_action_invocation(self, action: argparse.Action) -> str:
        """Format action with colors."""
        parts = super()._format_action_invocation(action)

        if COLORAMA_AVAILABLE:
            # Color the option names
            parts = parts.replace("-", f"{Fore.CYAN}-")
            parts = f"{parts}{Style.RESET_ALL}"

        return parts

    def _format_usage(self, usage: str, actions, groups, prefix: Optional[str]) -> str:
        """Format usage line with colors."""
        result = super()._format_usage(usage, actions, groups, prefix)

        if COLORAMA_AVAILABLE and result:
            # Highlight the program name
            prog_name = self._prog
            colored_prog = f"{Fore.GREEN}{prog_name}{Style.RESET_ALL}"
            result = result.replace(prog_name, colored_prog, 1)

        return result


class CustomArgumentParser(argparse.ArgumentParser):
    """Custom argument parser with better error messages."""

    def error(self, message: str) -> NoReturn:
        """Display error message with colors if available."""
        error_msg = f"ERROR: {message}"

        if COLORAMA_AVAILABLE:
            error_msg = f"{Fore.RED}ERROR: {message}{Style.RESET_ALL}"

        self.print_usage(sys.stderr)
        print(f"\n{error_msg}", file=sys.stderr)
        print(f"\nFor detailed help, use: {self.prog} --help", file=sys.stderr)
        self.exit(2)


def create_parser() -> CustomArgumentParser:
    """Create and configure the argument parser."""

    description = """m1f - Make One File
====================

Combines the content of multiple text files into a single output file with metadata.
Optionally creates a backup archive (zip or tar.gz) of the processed files.

Perfect for:
• Providing context to Large Language Models (LLMs)
• Creating bundled documentation
• Making machine-parseable bundles for later splitting
• Creating backups of processed files"""

    epilog = """Examples:
  %(prog)s --source-directory ./src --output-file combined.txt
  %(prog)s -s /path/to/project -o bundle.md -t --separator-style Markdown
  %(prog)s -i file_list.txt -o output.txt --create-archive --archive-type tar.gz
  %(prog)s -s ./docs -o docs.txt --include-extensions .md .rst .txt
  %(prog)s -s ./project -o all.txt --no-default-excludes --include-dot-paths
  %(prog)s -s ./src -o code.txt --security-check warn --quiet
  %(prog)s -s ./files -o small-files.txt --max-file-size 50KB
  %(prog)s auto-bundle                         # Create all bundles from .m1f.config.yml
  %(prog)s auto-bundle docs                    # Create only the 'docs' bundle
  %(prog)s auto-bundle --list                  # List available bundles"""

    parser = CustomArgumentParser(
        prog="m1f",
        description=description,
        epilog=epilog,
        formatter_class=ColoredHelpFormatter,
        add_help=True,
    )

    # Add version argument
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show program version and exit",
    )

    # Input/Output group
    io_group = parser.add_argument_group("Input/Output Options")

    io_group.add_argument(
        "-s",
        "--source-directory",
        type=str,
        metavar="DIR",
        help="Path to the directory containing files to combine",
    )

    io_group.add_argument(
        "-i",
        "--input-file",
        type=str,
        metavar="FILE",
        help="Path to a text file containing a list of files/directories to process",
    )

    io_group.add_argument(
        "-o",
        "--output-file",
        type=str,
        required=True,
        metavar="FILE",
        help="Path where the combined output file will be created",
    )

    io_group.add_argument(
        "--input-include-files",
        type=str,
        nargs="*",
        metavar="FILE",
        help="Files to include at the beginning of the output (first file is treated as intro)",
    )

    # Output formatting group
    format_group = parser.add_argument_group("Output Formatting")

    format_group.add_argument(
        "--separator-style",
        choices=["Standard", "Detailed", "Markdown", "MachineReadable", "None"],
        default="Detailed",
        help="Format of the separator between files (default: Detailed)",
    )

    format_group.add_argument(
        "--line-ending",
        choices=["lf", "crlf"],
        default="lf",
        help="Line ending style for generated content (default: lf)",
    )

    format_group.add_argument(
        "-t",
        "--add-timestamp",
        action="store_true",
        help="Add timestamp to output filename",
    )

    format_group.add_argument(
        "--filename-mtime-hash",
        action="store_true",
        help="Add hash of file modification times to output filename",
    )

    # File filtering group
    filter_group = parser.add_argument_group("File Filtering")

    filter_group.add_argument(
        "--excludes",
        type=str,
        nargs="*",
        default=[],
        metavar="PATTERN",
        help="Paths, directories, or patterns to exclude",
    )

    filter_group.add_argument(
        "--exclude-paths-file",
        type=str,
        nargs="+",
        metavar="FILE",
        help="File(s) containing paths to exclude (supports gitignore format, multiple files merged)",
    )

    filter_group.add_argument(
        "--include-paths-file",
        type=str,
        nargs="+",
        metavar="FILE",
        help="File(s) containing paths to include (supports gitignore format, multiple files merged)",
    )

    filter_group.add_argument(
        "--include-extensions",
        type=str,
        nargs="*",
        metavar="EXT",
        help="Only include files with these extensions",
    )

    filter_group.add_argument(
        "--exclude-extensions",
        type=str,
        nargs="*",
        metavar="EXT",
        help="Exclude files with these extensions",
    )

    filter_group.add_argument(
        "--include-dot-paths",
        action="store_true",
        help="Include files and directories starting with a dot",
    )

    filter_group.add_argument(
        "--include-binary-files",
        action="store_true",
        help="Attempt to include binary files (use with caution)",
    )

    filter_group.add_argument(
        "--include-symlinks",
        action="store_true",
        help="Follow symbolic links (careful of cycles!)",
    )

    filter_group.add_argument(
        "--max-file-size",
        type=str,
        metavar="SIZE",
        help="Skip files larger than specified size (e.g. 10KB, 1MB, 5.5GB)",
    )

    filter_group.add_argument(
        "--no-default-excludes",
        action="store_true",
        help="Disable default exclusions (node_modules, .git, etc.)",
    )

    filter_group.add_argument(
        "--remove-scraped-metadata",
        action="store_true",
        help="Remove scraped metadata (URL, timestamp) from HTML2MD files during processing",
    )

    # Encoding group
    encoding_group = parser.add_argument_group("Character Encoding")

    encoding_group.add_argument(
        "--convert-to-charset",
        type=str,
        choices=[
            "utf-8",
            "utf-16",
            "utf-16-le",
            "utf-16-be",
            "ascii",
            "latin-1",
            "cp1252",
        ],
        help="Convert all files to specified encoding",
    )

    encoding_group.add_argument(
        "--abort-on-encoding-error",
        action="store_true",
        help="Abort if encoding conversion fails",
    )

    # Security group
    security_group = parser.add_argument_group("Security Options")

    security_group.add_argument(
        "--security-check",
        choices=["abort", "skip", "warn"],
        help="Check for sensitive information in files",
    )

    # Archive group
    archive_group = parser.add_argument_group("Archive Options")

    archive_group.add_argument(
        "--create-archive",
        action="store_true",
        help="Create backup archive of processed files",
    )

    archive_group.add_argument(
        "--archive-type",
        choices=["zip", "tar.gz"],
        default="zip",
        help="Type of archive to create (default: zip)",
    )

    # Output control group
    control_group = parser.add_argument_group("Output Control")

    control_group.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force overwrite of existing output file",
    )

    control_group.add_argument(
        "--minimal-output",
        action="store_true",
        help="Only create the combined file (no auxiliary files)",
    )

    control_group.add_argument(
        "--skip-output-file",
        action="store_true",
        help="Skip creating the main output file",
    )

    control_group.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    control_group.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress all console output"
    )

    # Preset configuration group
    preset_group = parser.add_argument_group("Preset Configuration")

    preset_group.add_argument(
        "--preset",
        type=str,
        nargs="+",
        dest="preset_files",
        metavar="FILE",
        help="Preset configuration file(s) for file-specific processing",
    )

    preset_group.add_argument(
        "--preset-group",
        type=str,
        metavar="GROUP",
        help="Specific preset group to use from the configuration",
    )

    preset_group.add_argument(
        "--disable-presets",
        action="store_true",
        help="Disable all preset processing",
    )

    return parser


def parse_args(
    parser: argparse.ArgumentParser, args: Optional[list[str]] = None
) -> argparse.Namespace:
    """Parse command-line arguments."""
    parsed_args = parser.parse_args(args)

    # Validate that at least one input source is provided
    if not parsed_args.source_directory and not parsed_args.input_file:
        parser.error(
            "At least one of -s/--source-directory or -i/--input-file is required"
        )

    # Validate conflicting options
    if parsed_args.quiet and parsed_args.verbose:
        parser.error("Cannot use --quiet and --verbose together")

    return parsed_args
