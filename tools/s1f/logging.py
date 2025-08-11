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

"""Logging configuration for s1f."""

import logging
from typing import Optional
from pathlib import Path

# Try different import strategies for shared logging
try:
    from ..shared.logging import (
        LoggerManager as SharedLoggerManager,
        setup_logging as shared_setup_logging,
        get_logger as shared_get_logger,
    )
except ImportError:
    import os
    import sys

    sys.path.insert(
        0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    from tools.shared.logging import (
        LoggerManager as SharedLoggerManager,
        setup_logging as shared_setup_logging,
        get_logger as shared_get_logger,
    )

# Use unified colorama module for legacy compatibility
try:
    # Try absolute import first (when running as installed package)
    from tools.shared.colors import (
        Colors,
        ColoredFormatter as BaseColoredFormatter,
        COLORAMA_AVAILABLE,
    )
except ImportError:
    # Try relative import (when running from within package)
    try:
        from ..shared.colors import (
            Colors,
            ColoredFormatter as BaseColoredFormatter,
            COLORAMA_AVAILABLE,
        )
    except ImportError:
        # Fallback: define minimal stubs if colors module is not available
        COLORAMA_AVAILABLE = False

        class Colors:
            BLUE = ""
            GREEN = ""
            YELLOW = ""
            RED = ""
            BOLD = ""
            RESET = ""

        class BaseColoredFormatter(logging.Formatter):
            pass


# Legacy log level configuration - kept for backward compatibility
from dataclasses import dataclass


@dataclass
class LogLevel:
    """Log level configuration."""

    name: str
    value: int
    color: Optional[str] = None


LOG_LEVELS = {
    "DEBUG": LogLevel(
        "DEBUG", logging.DEBUG, Colors.BLUE if COLORAMA_AVAILABLE else None
    ),
    "INFO": LogLevel(
        "INFO", logging.INFO, Colors.GREEN if COLORAMA_AVAILABLE else None
    ),
    "WARNING": LogLevel(
        "WARNING", logging.WARNING, Colors.YELLOW if COLORAMA_AVAILABLE else None
    ),
    "ERROR": LogLevel(
        "ERROR", logging.ERROR, Colors.RED if COLORAMA_AVAILABLE else None
    ),
    "CRITICAL": LogLevel(
        "CRITICAL",
        logging.CRITICAL,
        Colors.RED + Colors.BOLD if COLORAMA_AVAILABLE else None,
    ),
}


# Legacy ColoredFormatter - kept for backward compatibility
class ColoredFormatter(BaseColoredFormatter):
    """Custom formatter that adds color to log messages."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with colors if available."""
        if COLORAMA_AVAILABLE:
            # Get the appropriate color for the log level
            level_name = record.levelname
            if level_name in LOG_LEVELS and LOG_LEVELS[level_name].color:
                color = LOG_LEVELS[level_name].color
                record.levelname = f"{color}{level_name}{Colors.RESET}"

        return super().format(record)


class LoggerManager(SharedLoggerManager):
    """S1F-specific logger manager that extends the shared LoggerManager."""

    def __init__(self, verbose: bool = False):
        """Initialize the S1F logger manager.

        Args:
            verbose: Enable verbose logging
        """

        # Create a simple config object for compatibility with shared LoggerManager
        class SimpleConfig:
            def __init__(self, verbose: bool):
                self.verbose = verbose
                self.quiet = False
                self.log_file = None
                self.log_level = None

        config = SimpleConfig(verbose)
        super().__init__(config)
        self.verbose = verbose  # Store for backward compatibility

        # Legacy attribute for backward compatibility
        self.loggers = self._loggers

    async def cleanup(self):
        """Cleanup logging resources."""
        await super().cleanup()


def setup_logging(config) -> LoggerManager:
    """Setup logging based on configuration."""
    return LoggerManager(verbose=config.verbose)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    # Use shared get_logger for consistency
    return shared_get_logger(name)
