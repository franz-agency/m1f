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
import sys
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from pathlib import Path

# Use unified colorama module
from ..shared.colors import Colors, ColoredFormatter as BaseColoredFormatter, COLORAMA_AVAILABLE


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
    "INFO": LogLevel("INFO", logging.INFO, Colors.GREEN if COLORAMA_AVAILABLE else None),
    "WARNING": LogLevel(
        "WARNING", logging.WARNING, Colors.YELLOW if COLORAMA_AVAILABLE else None
    ),
    "ERROR": LogLevel("ERROR", logging.ERROR, Colors.RED if COLORAMA_AVAILABLE else None),
    "CRITICAL": LogLevel(
        "CRITICAL", logging.CRITICAL, Colors.RED + Colors.BOLD if COLORAMA_AVAILABLE else None
    ),
}


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


class LoggerManager:
    """Manages logging configuration and logger instances."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.loggers: Dict[str, logging.Logger] = {}
        self._setup_root_logger()

    def _setup_root_logger(self):
        """Setup the root logger with appropriate handlers."""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG if self.verbose else logging.INFO)

        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if self.verbose else logging.INFO)

        # Set formatter
        if COLORAMA_AVAILABLE:
            formatter = ColoredFormatter("%(levelname)-8s: %(message)s")
        else:
            formatter = logging.Formatter("%(levelname)-8s: %(message)s")

        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger with the given name."""
        if name not in self.loggers:
            logger = logging.getLogger(name)
            self.loggers[name] = logger
        return self.loggers[name]

    async def cleanup(self):
        """Cleanup logging resources."""
        # Nothing to cleanup for now, but might be needed in the future
        pass


def setup_logging(config) -> LoggerManager:
    """Setup logging based on configuration."""
    return LoggerManager(verbose=config.verbose)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
