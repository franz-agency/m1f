"""
Shared utilities for m1f tools

This module contains common functionality used across multiple m1f tools:
- Prompt loading and management
- Configuration utilities
- Common helper functions
"""

from .prompts.loader import PromptLoader, load_prompt, format_prompt
from .config.loader import load_config_file, save_config_file
from .utils.paths import ensure_path, get_project_root

__all__ = [
    'PromptLoader',
    'load_prompt',
    'format_prompt',
    'load_config_file',
    'save_config_file',
    'ensure_path',
    'get_project_root',
]

__version__ = "0.1.0"