#!/usr/bin/env python3
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

from m1f.cli import create_parser, parse_args
from m1f.config import Config
from m1f.core import FileCombiner
from m1f.exceptions import M1FError
from m1f.logging import setup_logging, get_logger


__version__ = "2.1.0"
__author__ = "Franz und Franz (https://franz.agency)"
__project__ = "https://m1f.dev"


async def async_main() -> int:
    """Async main function for the application."""
    try:
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
