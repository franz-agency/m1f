"""
s1f - Split One File
====================

A modern Python tool to split a combined file (created by m1f) back into individual files.
"""

__version__ = "3.0.0"
__author__ = "Franz und Franz (https://franz.agency)"
__project__ = "https://m1f.dev"

from .exceptions import S1FError
from .cli import main

__all__ = ["S1FError", "main", "__version__", "__author__", "__project__"] 