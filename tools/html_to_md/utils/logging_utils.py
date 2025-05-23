"""Logging configuration and utilities."""

import logging
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(f"html_to_md.{name}")


def configure_logging(
    verbose: bool = False,
    quiet: bool = False,
    log_file: Optional[Path] = None,
    use_rich: bool = True
) -> None:
    """Configure logging for the application.
    
    Args:
        verbose: Enable debug logging
        quiet: Suppress all console output
        log_file: Optional log file path
        use_rich: Use rich console handler for pretty output
    """
    # Root logger for html_to_md
    root_logger = logging.getLogger("html_to_md")
    root_logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if not quiet:
        if use_rich:
            console = Console(stderr=True)
            handler = RichHandler(
                console=console,
                show_path=verbose,
                rich_tracebacks=True,
                tracebacks_show_locals=verbose
            )
        else:
            handler = logging.StreamHandler(sys.stderr)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
        
        handler.setLevel(logging.DEBUG if verbose else logging.INFO)
        root_logger.addHandler(handler)
    
    # File handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)


def get_progress() -> Progress:
    """Get a configured Rich progress bar.
    
    Returns:
        Configured Progress instance
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=Console(stderr=True)
    ) 