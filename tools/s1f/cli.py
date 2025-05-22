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


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="s1f - Split combined files back into original files",
        epilog=f"Project home: {__project__}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Support both positional and option-style arguments for backward compatibility
    # Option-style (for backward compatibility)
    parser.add_argument(
        "-i",
        "--input-file",
        type=Path,
        dest="input_file_opt",
        help="Path to the combined file (m1f output)",
    )

    parser.add_argument(
        "-d",
        "--destination-directory",
        type=Path,
        dest="destination_directory_opt",
        help="Directory where files will be extracted",
    )

    # Positional arguments (new style)
    parser.add_argument(
        "input_file",
        type=Path,
        nargs="?",
        help="Path to the combined file (m1f output)",
    )

    parser.add_argument(
        "destination_directory",
        type=Path,
        nargs="?",
        help="Directory where files will be extracted",
    )

    # Optional arguments
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Overwrite existing files without prompting",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output for debugging",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"s1f {__version__}",
        help="Show version information and exit",
    )

    # Timestamp handling
    timestamp_group = parser.add_mutually_exclusive_group()
    timestamp_group.add_argument(
        "--timestamp-mode",
        choices=["original", "current"],
        default="original",
        help="How to set file timestamps (default: %(default)s)",
    )

    # Checksum handling
    parser.add_argument(
        "--ignore-checksum",
        action="store_true",
        help="Skip checksum verification",
    )

    # Encoding handling
    encoding_group = parser.add_argument_group("encoding options")
    encoding_group.add_argument(
        "--respect-encoding",
        action="store_true",
        help="Write files using their original encoding (when available)",
    )

    encoding_group.add_argument(
        "--target-encoding",
        type=str,
        help="Force all files to be written with this encoding (e.g., 'utf-8', 'latin-1')",
    )

    return parser


def validate_args(args: argparse.Namespace) -> None:
    """Validate command-line arguments."""
    # Handle backward compatibility for option-style arguments
    if args.input_file_opt:
        args.input_file = args.input_file_opt
    if args.destination_directory_opt:
        args.destination_directory = args.destination_directory_opt

    # Ensure required arguments are provided
    if not args.input_file:
        raise ConfigurationError("Missing required argument: input_file")
    if not args.destination_directory:
        raise ConfigurationError("Missing required argument: destination_directory")

    # Check if input file exists
    if not args.input_file.exists():
        raise ConfigurationError(f"Input file does not exist: {args.input_file}")

    if not args.input_file.is_file():
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

        # Create and run file splitter
        splitter = FileSplitter(config, logger_manager)
        result, exit_code = await splitter.split_file()

        # Cleanup
        await logger_manager.cleanup()

        return exit_code

    except ConfigurationError as e:
        print(f"Error: {e}", file=sys.stderr)
        return e.exit_code
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Main entry point."""
    return asyncio.run(async_main(argv))


if __name__ == "__main__":
    sys.exit(main())
