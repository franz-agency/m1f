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
    setup_logging
)

__all__ = [
    # Colors module exports
    'Colors',
    'ColoredFormatter',
    'ColoredHelpFormatter',
    'COLORAMA_AVAILABLE',
    'success',
    'error',
    'warning',
    'info',
    'header',
    'setup_logging',
    # Existing exports (if available)
    'PromptLoader',
    'load_prompt',
    'format_prompt',
    'load_config_file',
    'save_config_file',
    'ensure_path',
    'get_project_root',
]

__version__ = "0.1.0"