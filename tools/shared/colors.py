"""
Unified colorama module for all m1f tools.

This module provides a consistent interface for colored terminal output
across all m1f tools, with graceful fallback when colorama is not available.
"""

import logging
import argparse
import sys
from typing import Optional, Any

# Try to import colorama
try:
    from colorama import Fore, Back, Style, init
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False


class Colors:
    """
    Unified color constants for all m1f tools.
    Falls back to empty strings when colorama is not available.
    """
    
    # Store original values for re-enabling
    _enabled = True
    
    @classmethod
    def _init_colors(cls):
        """Initialize color values based on availability and enabled state"""
        if COLORAMA_AVAILABLE and cls._enabled:
            # Foreground colors
            cls.BLACK = Fore.BLACK
            cls.RED = Fore.RED
            cls.GREEN = Fore.GREEN
            cls.YELLOW = Fore.YELLOW
            cls.BLUE = Fore.BLUE
            cls.MAGENTA = Fore.MAGENTA
            cls.CYAN = Fore.CYAN
            cls.WHITE = Fore.WHITE
            
            # Bright colors
            cls.BRIGHT_BLACK = Fore.LIGHTBLACK_EX
            cls.BRIGHT_RED = Fore.LIGHTRED_EX
            cls.BRIGHT_GREEN = Fore.LIGHTGREEN_EX
            cls.BRIGHT_YELLOW = Fore.LIGHTYELLOW_EX
            cls.BRIGHT_BLUE = Fore.LIGHTBLUE_EX
            cls.BRIGHT_MAGENTA = Fore.LIGHTMAGENTA_EX
            cls.BRIGHT_CYAN = Fore.LIGHTCYAN_EX
            cls.BRIGHT_WHITE = Fore.LIGHTWHITE_EX
            
            # Background colors
            cls.BG_BLACK = Back.BLACK
            cls.BG_RED = Back.RED
            cls.BG_GREEN = Back.GREEN
            cls.BG_YELLOW = Back.YELLOW
            cls.BG_BLUE = Back.BLUE
            cls.BG_MAGENTA = Back.MAGENTA
            cls.BG_CYAN = Back.CYAN
            cls.BG_WHITE = Back.WHITE
            
            # Styles
            cls.BOLD = Style.BRIGHT
            cls.DIM = Style.DIM
            cls.NORMAL = Style.NORMAL
            cls.RESET = Style.RESET_ALL
            cls.RESET_ALL = Style.RESET_ALL
        else:
            # Set all to empty strings
            for attr in ['BLACK', 'RED', 'GREEN', 'YELLOW', 'BLUE', 'MAGENTA', 'CYAN', 'WHITE',
                        'BRIGHT_BLACK', 'BRIGHT_RED', 'BRIGHT_GREEN', 'BRIGHT_YELLOW',
                        'BRIGHT_BLUE', 'BRIGHT_MAGENTA', 'BRIGHT_CYAN', 'BRIGHT_WHITE',
                        'BG_BLACK', 'BG_RED', 'BG_GREEN', 'BG_YELLOW', 'BG_BLUE',
                        'BG_MAGENTA', 'BG_CYAN', 'BG_WHITE',
                        'BOLD', 'DIM', 'NORMAL', 'RESET', 'RESET_ALL']:
                setattr(cls, attr, '')
    
    @classmethod
    def disable(cls):
        """Disable colors (useful for non-TTY output or when requested)"""
        cls._enabled = False
        cls._init_colors()
    
    @classmethod
    def enable(cls):
        """Re-enable colors if colorama is available"""
        cls._enabled = True
        cls._init_colors()
    
    @classmethod
    def is_enabled(cls) -> bool:
        """Check if colors are currently enabled"""
        return cls._enabled and COLORAMA_AVAILABLE


# Initialize colors on module load
Colors._init_colors()


class ColoredFormatter(logging.Formatter):
    """
    Custom logging formatter with colored output.
    Used consistently across all m1f tools.
    """
    
    LEVEL_COLORS = {
        "DEBUG": Colors.CYAN,
        "INFO": Colors.GREEN,
        "WARNING": Colors.YELLOW,
        "ERROR": Colors.RED,
        "CRITICAL": Colors.RED + Colors.BOLD,
    }
    
    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        """Initialize formatter with optional format strings"""
        super().__init__(fmt or "%(levelname)-8s: %(message)s", datefmt)
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""
        # Save original levelname
        original_levelname = record.levelname
        
        # Apply color if available
        if Colors.is_enabled():
            color = self.LEVEL_COLORS.get(record.levelname, "")
            reset = Colors.RESET if color else ""
            record.levelname = f"{color}{record.levelname}{reset}"
        
        # Format the record
        result = super().format(record)
        
        # Restore original levelname
        record.levelname = original_levelname
        
        return result


class ColoredHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """
    Custom argparse help formatter with colored output.
    Used consistently across all m1f tools.
    """
    
    def _format_action_invocation(self, action: argparse.Action) -> str:
        """Format action with colors"""
        parts = super()._format_action_invocation(action)
        
        if Colors.is_enabled():
            # Color the option names
            parts = parts.replace("-", f"{Colors.CYAN}-")
            parts = f"{parts}{Colors.RESET}"
        
        return parts
    
    def _format_usage(self, usage: str, actions, groups, prefix: Optional[str]) -> str:
        """Format usage line with colors"""
        result = super()._format_usage(usage, actions, groups, prefix)
        
        if Colors.is_enabled() and result:
            # Highlight the program name
            prog_name = self._prog
            colored_prog = f"{Colors.GREEN}{prog_name}{Colors.RESET}"
            result = result.replace(prog_name, colored_prog, 1)
        
        return result


# Utility functions for consistent output across tools
def success(message: str, file=None) -> None:
    """Print a success message in green"""
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}", file=file or sys.stdout)


def error(message: str, file=None) -> None:
    """Print an error message in red"""
    print(f"{Colors.RED}❌ Error: {message}{Colors.RESET}", file=file or sys.stderr)


def warning(message: str, file=None) -> None:
    """Print a warning message in yellow"""
    print(f"{Colors.YELLOW}⚠️  Warning: {message}{Colors.RESET}", file=file or sys.stdout)


def info(message: str, file=None) -> None:
    """Print an info message in cyan"""
    print(f"{Colors.CYAN}ℹ️  {message}{Colors.RESET}", file=file or sys.stdout)


def header(title: str, subtitle: Optional[str] = None, file=None) -> None:
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{title}{Colors.RESET}", file=file or sys.stdout)
    if subtitle:
        print(f"{Colors.DIM}{subtitle}{Colors.RESET}\n", file=file or sys.stdout)
    else:
        print(file=file or sys.stdout)


def setup_logging(level: int = logging.INFO, 
                  fmt: Optional[str] = None,
                  colored: bool = True) -> logging.Logger:
    """
    Set up logging with optional colored output.
    Returns the root logger.
    """
    # Remove existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Use colored formatter if requested and available
    if colored and Colors.is_enabled():
        formatter = ColoredFormatter(fmt)
    else:
        formatter = logging.Formatter(fmt or "%(levelname)-8s: %(message)s")
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    root_logger.setLevel(level)
    
    return root_logger


# Auto-disable colors if not in a TTY
if not sys.stdout.isatty():
    Colors.disable()