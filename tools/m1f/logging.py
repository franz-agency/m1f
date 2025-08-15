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
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from .config import Config, LoggingConfig
from shared.logging import (
    LoggerManager as SharedLoggerManager,
    setup_logging as shared_setup_logging,
    get_logger as shared_get_logger,
)

# Use unified colorama module for warnings
try:
    from shared.colors import warning
except ImportError:
    import os
    import sys

    sys.path.insert(
        0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    from tools.shared.colors import warning


class LoggerManager(SharedLoggerManager):
    """M1F-specific logger manager that extends the shared LoggerManager."""

    def __init__(self, config: LoggingConfig, output_file_path: Optional[Path] = None):
        """Initialize the M1F logger manager.

        Args:
            config: M1F logging configuration
            output_file_path: Optional output file path for log files
        """
        super().__init__(config, output_file_path)
        self._config = config  # Store m1f config separately

    def _create_file_handler(
        self, file_path: Path, level: int
    ) -> Optional[logging.FileHandler]:
        """Create a file handler for logging to disk with M1F-specific logic."""
        # M1F-specific behavior: create .log file next to output file
        if self.output_file_path:
            log_file_path = self.output_file_path.with_suffix(".log")

            # Ensure log file doesn't overwrite output file
            if log_file_path == self.output_file_path:
                return None
        else:
            log_file_path = Path(file_path)

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
            warning(f"Could not create log file at {log_file_path}: {e}")
            return None

    def set_output_file(self, output_path: Path) -> None:
        """Set the output file path and create file handler if needed."""
        self.output_file_path = output_path

        # Add file handler if not already present
        quiet = self._get_config_value("quiet", False)
        if not quiet and not any(
            isinstance(h, logging.FileHandler) for h in self._handlers
        ):
            file_handler = self._create_file_handler(output_path, logging.DEBUG)
            if file_handler:
                logging.getLogger().addHandler(file_handler)
                self._handlers.append(file_handler)


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
        # Fallback to shared get_logger if not initialized
        return shared_get_logger(name)

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
