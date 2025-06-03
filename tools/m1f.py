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
except ImportError:
    # Fallback for direct script execution
    from m1f.cli import create_parser, parse_args
    from m1f.config import Config
    from m1f.core import FileCombiner
    from m1f.exceptions import M1FError
    from m1f.logging import setup_logging, get_logger


__version__ = "3.0.0"
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
