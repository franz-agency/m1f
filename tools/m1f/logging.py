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
Logging configuration for m1f.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from contextlib import asynccontextmanager

from .config import Config, LoggingConfig


@dataclass
class LoggerManager:
    """Manages loggers and handlers for the application."""

    config: LoggingConfig
    output_file_path: Optional[Path] = None
    _loggers: Dict[str, logging.Logger] = None
    _handlers: list[logging.Handler] = None

    def __post_init__(self):
        self._loggers = {}
        self._handlers = []
        self._setup()

    def _setup(self) -> None:
        """Set up the logging configuration."""
        # Determine logging level
        if self.config.quiet:
            level = logging.CRITICAL + 1  # Suppress all output
        elif self.config.verbose:
            level = logging.DEBUG
        else:
            level = logging.INFO

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # Remove any existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Create console handler if not quiet
        if not self.config.quiet:
            console_handler = self._create_console_handler(level)
            root_logger.addHandler(console_handler)
            self._handlers.append(console_handler)

        # Create file handler if output path is provided
        if self.output_file_path and not self.config.quiet:
            file_handler = self._create_file_handler(self.output_file_path, level)
            if file_handler:
                root_logger.addHandler(file_handler)
                self._handlers.append(file_handler)

    def _create_console_handler(self, level: int) -> logging.StreamHandler:
        """Create a console handler with colored output if available."""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        # Try to use colorama for colored output
        try:
            from colorama import Fore, Style, init

            init(autoreset=True)

            class ColoredFormatter(logging.Formatter):
                """Custom formatter with colors."""

                COLORS = {
                    "DEBUG": Fore.CYAN,
                    "INFO": Fore.GREEN,
                    "WARNING": Fore.YELLOW,
                    "ERROR": Fore.RED,
                    "CRITICAL": Fore.RED + Style.BRIGHT,
                }

                def format(self, record: logging.LogRecord) -> str:
                    color = self.COLORS.get(record.levelname, "")
                    reset = Style.RESET_ALL if color else ""
                    record.levelname = f"{color}{record.levelname}{reset}"
                    return super().format(record)

            formatter = ColoredFormatter("%(levelname)-8s: %(message)s")
        except ImportError:
            # Fallback to simple formatter
            formatter = logging.Formatter("%(levelname)-8s: %(message)s")

        handler.setFormatter(formatter)
        return handler

    def _create_file_handler(
        self, output_path: Path, level: int
    ) -> Optional[logging.FileHandler]:
        """Create a file handler for logging to disk."""
        log_file_path = output_path.with_suffix(".log")

        # Ensure log file doesn't overwrite output file
        if log_file_path == output_path:
            return None

        try:
            # Ensure parent directory exists
            log_file_path.parent.mkdir(parents=True, exist_ok=True)

            handler = logging.FileHandler(
                log_file_path, mode="w", encoding="utf-8", delay=False
            )
            handler.setLevel(level)

            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)-8s: %(message)s"
            )
            handler.setFormatter(formatter)

            return handler

        except Exception as e:
            # Log to console if file handler creation fails
            print(f"Warning: Could not create log file at {log_file_path}: {e}")
            return None

    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger with the given name."""
        if name not in self._loggers:
            logger = logging.getLogger(name)
            self._loggers[name] = logger
        return self._loggers[name]

    def set_output_file(self, output_path: Path) -> None:
        """Set the output file path and create file handler if needed."""
        self.output_file_path = output_path

        # Add file handler if not already present
        if not self.config.quiet and not any(
            isinstance(h, logging.FileHandler) for h in self._handlers
        ):
            file_handler = self._create_file_handler(output_path, logging.DEBUG)
            if file_handler:
                logging.getLogger().addHandler(file_handler)
                self._handlers.append(file_handler)

    async def cleanup(self) -> None:
        """Clean up all handlers and loggers."""
        # Remove and close all handlers
        root_logger = logging.getLogger()

        for handler in self._handlers:
            root_logger.removeHandler(handler)
            if hasattr(handler, "close"):
                handler.close()

        self._handlers.clear()
        self._loggers.clear()

        # Shutdown logging
        logging.shutdown()


# Module-level logger manager instance
_logger_manager: Optional[LoggerManager] = None


def setup_logging(config: Config) -> LoggerManager:
    """Set up logging for the application."""
    global _logger_manager

    if _logger_manager is not None:
        # Clean up existing manager
        import asyncio

        asyncio.create_task(_logger_manager.cleanup())

    _logger_manager = LoggerManager(config.logging)
    return _logger_manager


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    if _logger_manager is None:
        # Fallback to basic logger if not initialized
        return logging.getLogger(name)

    return _logger_manager.get_logger(name)


@asynccontextmanager
async def logging_context(config: Config, output_path: Optional[Path] = None):
    """Context manager for logging setup and cleanup."""
    manager = setup_logging(config)

    if output_path:
        manager.set_output_file(output_path)

    try:
        yield manager
    finally:
        await manager.cleanup()
