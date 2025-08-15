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

"""Command-line interface for s1f."""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional, Sequence

from . import __version__, __project__
from .config import Config
from .core import FileSplitter
from .logging import setup_logging
from .exceptions import ConfigurationError

# Try absolute imports first (for module execution), fall back to relative
try:
    from m1f.file_operations import safe_exists, safe_is_file
except (ImportError, ValueError):
    # Fallback for direct script execution or when running as main module
    import sys
    from pathlib import Path

    # Add parent directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from m1f.file_operations import safe_exists, safe_is_file

# Use unified colorama module
try:
    from shared.colors import (
        Colors,
        ColoredHelpFormatter,
        error,
        COLORAMA_AVAILABLE,
    )
    from shared.cli import CustomArgumentParser
except ImportError:
    try:
        from shared.colors import (
            Colors,
            ColoredHelpFormatter,
            error,
            COLORAMA_AVAILABLE,
        )
        from shared.cli import CustomArgumentParser
    except ImportError:
        COLORAMA_AVAILABLE = False

        # Fallback
        def error(msg):
            print(f"Error: {msg}", file=sys.stderr)

        class ColoredHelpFormatter(argparse.RawDescriptionHelpFormatter):
            pass

        # Fallback CustomArgumentParser
        class CustomArgumentParser(argparse.ArgumentParser):
            """Custom argument parser with better error messages."""

            def error(self, message: str) -> None:
                """Display error message with colors if available."""
                error_msg = f"ERROR: {message}"

                if COLORAMA_AVAILABLE:
                    error_msg = f"{Colors.RED}ERROR: {message}{Colors.RESET}"

                self.print_usage(sys.stderr)
                print(f"\n{error_msg}", file=sys.stderr)
                print(f"\nFor detailed help, use: {self.prog} --help", file=sys.stderr)
                self.exit(2)


def create_argument_parser() -> CustomArgumentParser:
    """Create and configure the argument parser."""
    description = """m1f-s1f - Split One File
=====================

Extract files from m1f bundles back to their original structure.
Preserves file metadata, encodings, and directory hierarchy.

Perfect for:
• Extracting files from m1f archives
• Recovering original project structure
• Inspecting bundle contents
• Converting between encodings"""

    epilog = f"""Examples:
  %(prog)s archive.m1f.txt ./output/
  %(prog)s --list archive.m1f.txt
  %(prog)s archive.m1f.txt ./output/ --respect-encoding
  %(prog)s bundle.txt ./extracted/ --force
  
For more information, see the documentation.
Project home: {__project__}"""

    parser = CustomArgumentParser(
        prog="m1f-s1f",
        description=description,
        epilog=epilog,
        formatter_class=ColoredHelpFormatter,
        add_help=True,
    )

    # Add version argument first
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show program version and exit",
    )

    # Positional arguments
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the m1f bundle file",
    )

    parser.add_argument(
        "destination_directory",
        type=Path,
        nargs="?",
        help="Directory where files will be extracted",
    )

    # Extraction options group
    extract_group = parser.add_argument_group("Extraction Options")
    extract_group.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Overwrite existing files without prompting",
    )
    extract_group.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="List files in the archive without extracting",
    )
    extract_group.add_argument(
        "--timestamp-mode",
        choices=["original", "current"],
        default="original",
        help="How to set file timestamps (default: original)",
    )
    extract_group.add_argument(
        "--ignore-checksum",
        action="store_true",
        help="Skip checksum verification during extraction",
    )

    # Encoding options group
    encoding_group = parser.add_argument_group("Encoding Options")
    encoding_group.add_argument(
        "--respect-encoding",
        action="store_true",
        help="Write files using their original encoding when available",
    )
    encoding_group.add_argument(
        "--target-encoding",
        type=str,
        metavar="ENCODING",
        help="Force all files to be written with this encoding (e.g., utf-8, latin-1)",
    )

    # Output control group
    output_group = parser.add_argument_group("Output Control")
    output_group.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output for debugging",
    )

    return parser


def validate_args(args: argparse.Namespace) -> None:
    """Validate command-line arguments."""
    # Ensure required arguments are provided
    if not args.input_file:
        raise ConfigurationError("Missing required argument: input_file")
    if not args.list and not args.destination_directory:
        raise ConfigurationError("Missing required argument: destination_directory")

    # Check if input file exists
    if not safe_exists(args.input_file):
        raise ConfigurationError(f"Input file does not exist: {args.input_file}")

    if not safe_is_file(args.input_file):
        raise ConfigurationError(f"Input path is not a file: {args.input_file}")

    # Validate encoding options
    if args.target_encoding and args.respect_encoding:
        raise ConfigurationError(
            "Cannot use both --target-encoding and --respect-encoding"
        )

    # Validate target encoding if specified
    if args.target_encoding:
        try:
            # Test if the encoding is valid
            "test".encode(args.target_encoding)
        except LookupError:
            raise ConfigurationError(f"Unknown encoding: {args.target_encoding}")


async def async_main(argv: Optional[Sequence[str]] = None) -> int:
    """Async main entry point."""
    # Parse arguments
    parser = create_argument_parser()
    args = parser.parse_args(argv)

    try:
        # Validate arguments
        validate_args(args)

        # Create configuration
        config = Config.from_args(args)

        # Setup logging
        logger_manager = setup_logging(config)

        # Create file splitter
        splitter = FileSplitter(config, logger_manager)

        # Run in list mode or extraction mode
        if args.list:
            result, exit_code = await splitter.list_files()
        else:
            result, exit_code = await splitter.split_file()

        # Cleanup
        await logger_manager.cleanup()

        return exit_code

    except ConfigurationError as e:
        error(str(e))
        return e.exit_code
    except KeyboardInterrupt:
        error("Operation cancelled by user.")
        return 130
    except Exception as e:
        error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Main entry point."""
    return asyncio.run(async_main(argv))


if __name__ == "__main__":
    sys.exit(main())
