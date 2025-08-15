"""
Shared utilities for m1f tools

This module contains common functionality used across multiple m1f tools:
- Prompt loading and management
- Configuration utilities
- Common helper functions
- Unified colorama support
"""

# Import existing modules with error handling
try:
    from .prompts.loader import PromptLoader, load_prompt, format_prompt
except ImportError:
    PromptLoader = None
    load_prompt = None
    format_prompt = None

try:
    from .config.loader import load_config_file, save_config_file
except ImportError:
    load_config_file = None
    save_config_file = None

try:
    from .utils.paths import ensure_path, get_project_root
except ImportError:
    ensure_path = None
    get_project_root = None

# Import colors module
from .colors import (
    Colors,
    ColoredFormatter,
    ColoredHelpFormatter,
    COLORAMA_AVAILABLE,
    success,
    error,
    warning,
    info,
    header,
)

# Import CLI utilities
try:
    from .cli import CustomArgumentParser, ArgumentBuilder, BaseCLI, SubcommandCLI
except ImportError:
    CustomArgumentParser = None
    ArgumentBuilder = None
    BaseCLI = None
    SubcommandCLI = None

# Import logging utilities
try:
    from .logging import (
        LoggingConfig,
        LoggerManager,
        setup_logging,
        get_logger,
        configure_logging,
    )
except ImportError:
    LoggingConfig = None
    LoggerManager = None
    setup_logging = None
    get_logger = None
    configure_logging = None

__all__ = [
    # Colors module exports
    "Colors",
    "ColoredFormatter",
    "ColoredHelpFormatter",
    "COLORAMA_AVAILABLE",
    "success",
    "error",
    "warning",
    "info",
    "header",
    # CLI module exports
    "CustomArgumentParser",
    "ArgumentBuilder",
    "BaseCLI",
    "SubcommandCLI",
    # Logging module exports
    "LoggingConfig",
    "LoggerManager",
    "setup_logging",
    "get_logger",
    "configure_logging",
    # Existing exports (if available)
    "PromptLoader",
    "load_prompt",
    "format_prompt",
    "load_config_file",
    "save_config_file",
    "ensure_path",
    "get_project_root",
]

__version__ = "0.1.0"
