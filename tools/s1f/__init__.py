"""
s1f - Split One File
====================

A modern Python tool to split a combined file (created by m1f) back into individual files.
"""

try:
    from tools._version import __version__, __version_info__
except ImportError:
    try:
        from .._version import __version__, __version_info__
    except ImportError:
        # Fallback when running as standalone script
        __version__ = "3.9.0"
        __version_info__ = (3, 9, 0)

__author__ = "Franz und Franz (https://franz.agency)"
__project__ = "https://m1f.dev"

from .exceptions import S1FError
from .cli import main

__all__ = [
    "S1FError",
    "main",
    "__version__",
    "__version_info__",
    "__author__",
    "__project__",
]
