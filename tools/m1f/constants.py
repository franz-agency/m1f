"""
Constants used throughout the m1f application.
"""

from typing import Set, List

# Default directories to exclude
DEFAULT_EXCLUDED_DIRS: Set[str] = {
    "vendor",
    "node_modules",
    "build",
    "dist",
    "cache",
    ".git",
    ".svn",
    ".hg",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    ".coverage",
    ".eggs",
    "htmlcov",
    ".idea",
    ".vscode",
}

# Default files to exclude
DEFAULT_EXCLUDED_FILES: Set[str] = {
    "LICENSE.md",
    "package-lock.json",
    "composer.lock",
    "poetry.lock",
    "Pipfile.lock",
    "yarn.lock",
}

# Maximum symlink depth to prevent infinite loops
MAX_SYMLINK_DEPTH: int = 40

# Buffer size for file reading
READ_BUFFER_SIZE: int = 8192

# Boundary marker prefix for machine-readable format
MACHINE_READABLE_BOUNDARY_PREFIX: str = "PYMK1F"

# Token encoding name for tiktoken
TOKEN_ENCODING_NAME: str = "cl100k_base" 