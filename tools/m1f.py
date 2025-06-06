#!/usr/bin/env python3
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
m1f - Make One File (Refactored Version)
========================================

A modern Python tool to combine multiple text files into a single output file.

This is a refactored version using modern Python best practices:
- Type hints throughout (Python 3.10+ style)
- Dataclasses for configuration
- Better separation of concerns
- Dependency injection
- No global state
- Async I/O for better performance
- Structured logging
"""

import asyncio
import sys
from pathlib import Path
from typing import NoReturn

# Try absolute imports first (for module execution), fall back to relative
try:
    from tools.m1f.cli import create_parser, parse_args
    from tools.m1f.config import Config
    from tools.m1f.core import FileCombiner
    from tools.m1f.exceptions import M1FError
    from tools.m1f.logging import setup_logging, get_logger
    from tools.m1f.auto_bundle import AutoBundler
except ImportError:
    # Fallback for direct script execution
    from m1f.cli import create_parser, parse_args
    from m1f.config import Config
    from m1f.core import FileCombiner
    from m1f.exceptions import M1FError
    from m1f.logging import setup_logging, get_logger
    from m1f.auto_bundle import AutoBundler


try:
    from _version import __version__, __version_info__
except ImportError:
    # Fallback for when running as a script
    __version__ = "3.2.0"
    __version_info__ = (3, 2, 0)

__author__ = "Franz und Franz (https://franz.agency)"
__project__ = "https://m1f.dev"


async def async_main() -> int:
    """Async main function for the application."""
    try:
        # Check if we're running auto-bundle command
        if len(sys.argv) > 1 and sys.argv[1] == "auto-bundle":
            # Handle auto-bundle subcommand
            import argparse

            parser = argparse.ArgumentParser(
                prog="m1f auto-bundle", description="Auto-bundle functionality for m1f"
            )
            parser.add_argument(
                "bundle_name", nargs="?", help="Name of specific bundle to create"
            )
            parser.add_argument(
                "--list", action="store_true", help="List available bundles"
            )
            parser.add_argument(
                "--group",
                "-g",
                type=str,
                help="Only create bundles from specified group",
            )
            parser.add_argument(
                "-v", "--verbose", action="store_true", help="Enable verbose output"
            )
            parser.add_argument(
                "-q", "--quiet", action="store_true", help="Suppress all console output"
            )

            # Parse auto-bundle args
            args = parser.parse_args(sys.argv[2:])

            # Create and run auto-bundler
            bundler = AutoBundler(Path.cwd(), verbose=args.verbose, quiet=args.quiet)
            success = bundler.run(
                bundle_name=args.bundle_name,
                list_bundles=args.list,
                bundle_group=args.group,
            )
            return 0 if success else 1

        # Regular m1f execution
        # Parse command line arguments
        parser = create_parser()
        args = parse_args(parser)

        # Create configuration from arguments
        config = Config.from_args(args)

        # Setup logging
        logger_manager = setup_logging(config)
        logger = get_logger(__name__)

        try:
            # Create and run the file combiner
            combiner = FileCombiner(config, logger_manager)
            result = await combiner.run()

            # Log execution summary
            logger.info(f"Total execution time: {result.execution_time}")
            logger.info(f"Processed {result.files_processed} files")

            return 0

        finally:
            # Ensure proper cleanup
            await logger_manager.cleanup()

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        return 130  # Standard exit code for Ctrl+C

    except M1FError as e:
        # Our custom exceptions
        logger = get_logger(__name__)
        logger.error(f"{e.__class__.__name__}: {e}")
        return e.exit_code

    except Exception as e:
        # Unexpected errors
        logger = get_logger(__name__)
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        return 1


def main() -> NoReturn:
    """Entry point for the application."""
    exit_code = asyncio.run(async_main())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
