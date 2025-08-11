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
Shared logging utilities for all m1f tools.

This module provides common logging functionality to ensure
consistency across all tools and avoid code duplication.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

from .colors import ColoredFormatter, Colors, COLORAMA_AVAILABLE


@dataclass
class LoggingConfig:
    """Common logging configuration."""

    verbose: bool = False
    quiet: bool = False
    log_file: Optional[Path] = None
    log_level: Optional[str] = None  # Can override with specific level

    def get_level(self) -> int:
        """Get the logging level based on configuration."""
        if self.quiet:
            return logging.CRITICAL + 1  # Suppress all output
        elif self.log_level:
            return getattr(logging, self.log_level.upper(), logging.INFO)
        elif self.verbose:
            return logging.DEBUG
        else:
            return logging.INFO


@dataclass
class LoggerManager:
    """Manages loggers and handlers for applications.

    This class provides a unified way to configure logging across
    all m1f tools, handling console and file output consistently.
    """

    config: Union[LoggingConfig, Any]  # Can be LoggingConfig or tool-specific config
    output_file_path: Optional[Path] = None
    _loggers: Dict[str, logging.Logger] = field(default_factory=dict, init=False)
    _handlers: list[logging.Handler] = field(default_factory=list, init=False)
    _setup_complete: bool = field(default=False, init=False)

    def __post_init__(self):
        """Initialize the logger manager."""
        if not self._setup_complete:
            self._setup()
            self._setup_complete = True

    def _get_config_value(self, attr: str, default: Any = None) -> Any:
        """Get a configuration value, handling different config types."""
        # Handle nested config (e.g., config.logging.verbose)
        if hasattr(self.config, "logging"):
            logging_config = getattr(self.config, "logging")
            if hasattr(logging_config, attr):
                return getattr(logging_config, attr)

        # Handle direct config attributes
        if hasattr(self.config, attr):
            return getattr(self.config, attr)

        return default

    def _get_log_level(self) -> int:
        """Determine the logging level from configuration."""
        quiet = self._get_config_value("quiet", False)
        verbose = self._get_config_value("verbose", False)
        log_level = self._get_config_value("log_level")

        if quiet:
            return logging.CRITICAL + 1  # Suppress all output
        elif log_level:
            return getattr(logging, log_level.upper(), logging.INFO)
        elif verbose:
            return logging.DEBUG
        else:
            return logging.INFO

    def _setup(self) -> None:
        """Set up the logging configuration."""
        level = self._get_log_level()

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # Remove any existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Create console handler if not quiet
        quiet = self._get_config_value("quiet", False)
        if not quiet:
            console_handler = self._create_console_handler(level)
            root_logger.addHandler(console_handler)
            self._handlers.append(console_handler)

        # Create file handler if path is provided
        log_file = self._get_config_value("log_file") or self.output_file_path
        if log_file and not quiet:
            file_handler = self._create_file_handler(log_file, level)
            if file_handler:
                root_logger.addHandler(file_handler)
                self._handlers.append(file_handler)

    def _create_console_handler(self, level: int) -> logging.StreamHandler:
        """Create a console handler with colored output if available."""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        # Use ColoredFormatter from shared.colors
        formatter = ColoredFormatter("%(levelname)-8s: %(message)s")
        handler.setFormatter(formatter)
        return handler

    def _create_file_handler(
        self, file_path: Path, level: int
    ) -> Optional[logging.FileHandler]:
        """Create a file handler for logging to a file.

        Args:
            file_path: Path to the log file
            level: Logging level

        Returns:
            FileHandler or None if creation fails
        """
        try:
            # Ensure parent directory exists
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            handler = logging.FileHandler(file_path, mode="a", encoding="utf-8")
            handler.setLevel(level)

            # Use simple formatter for files (no colors)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)-8s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            return handler
        except Exception as e:
            # Log error to console if possible
            logging.error(f"Failed to create file handler: {e}")
            return None

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance.

        Args:
            name: Logger name (usually __name__)

        Returns:
            Configured logger instance
        """
        if name not in self._loggers:
            logger = logging.getLogger(name)
            self._loggers[name] = logger
        return self._loggers[name]

    async def cleanup(self) -> None:
        """Clean up logging handlers."""
        for handler in self._handlers:
            handler.close()
        self._handlers.clear()

    @asynccontextmanager
    async def managed_logger(self, name: str):
        """Context manager for getting a logger that auto-cleans up.

        Args:
            name: Logger name

        Yields:
            Logger instance
        """
        logger = self.get_logger(name)
        try:
            yield logger
        finally:
            # Cleanup is handled by the cleanup() method
            pass


# Global logger manager instance (can be initialized by each tool)
_global_manager: Optional[LoggerManager] = None


def setup_logging(
    config: Optional[Union[LoggingConfig, Any]] = None,
    verbose: bool = False,
    quiet: bool = False,
    log_file: Optional[Path] = None,
) -> LoggerManager:
    """Set up logging configuration for a tool.

    This is the main entry point for configuring logging in any m1f tool.

    Args:
        config: Configuration object (can be tool-specific or LoggingConfig)
        verbose: Enable verbose logging (used if config is None)
        quiet: Suppress output (used if config is None)
        log_file: Log file path (used if config is None)

    Returns:
        LoggerManager instance
    """
    global _global_manager

    # Create config if not provided
    if config is None:
        config = LoggingConfig(verbose=verbose, quiet=quiet, log_file=log_file)

    # Create and store manager
    _global_manager = LoggerManager(config)
    return _global_manager


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    This is a convenience function that can be called from anywhere
    after setup_logging has been called.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    if _global_manager:
        return _global_manager.get_logger(name)
    else:
        # Return a basic logger if not set up
        return logging.getLogger(name)


def configure_logging(
    verbose: bool = False,
    quiet: bool = False,
    log_file: Optional[Path] = None,
    log_level: Optional[str] = None,
) -> None:
    """Configure logging with basic parameters.

    This is a simple interface for tools that don't need
    the full LoggerManager functionality.

    Args:
        verbose: Enable verbose output
        quiet: Suppress all but error messages
        log_file: Optional log file path
        log_level: Specific log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    config = LoggingConfig(
        verbose=verbose, quiet=quiet, log_file=log_file, log_level=log_level
    )
    setup_logging(config)


# Re-export commonly used logging levels for convenience
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL
