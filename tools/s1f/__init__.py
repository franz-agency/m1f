"""
s1f - Split One File
====================

A modern Python tool to split a combined file (created by m1f) back into individual files.
"""

from .._version import __version__, __version_info__

__author__ = "Franz und Franz (https://franz.agency)"
__project__ = "https://m1f.dev"

from .exceptions import S1FError
from .cli import main

__all__ = ["S1FError", "main", "__version__", "__version_info__", "__author__", "__project__"]
