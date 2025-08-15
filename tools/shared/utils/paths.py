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
Path utilities for m1f tools
"""

from pathlib import Path
from typing import Union, List, Optional, Generator
import os
import logging

from m1f.file_operations import (
    safe_exists,
    safe_is_dir,
)


def ensure_path(path: Union[str, Path], create_parents: bool = False) -> Path:
    """
    Ensure a path is a Path object and optionally create parent directories.

    Args:
        path: Path string or Path object
        create_parents: If True, create parent directories if they don't exist

    Returns:
        Path object
    """
    path = Path(path)

    if create_parents and path.parent != path:
        path.parent.mkdir(parents=True, exist_ok=True)

    return path


def get_project_root(start_path: Optional[Union[str, Path]] = None) -> Optional[Path]:
    """
    Find the project root by looking for marker files.

    Searches for: .git, pyproject.toml, setup.py, package.json

    Args:
        start_path: Path to start searching from (default: current directory)

    Returns:
        Project root path or None if not found
    """
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path)

    # Marker files that indicate project root
    markers = [".git", "pyproject.toml", "setup.py", "package.json", ".m1f"]

    current = start_path.absolute()

    logger = logging.getLogger(__name__)

    while current != current.parent:
        for marker in markers:
            if safe_exists(current / marker, logger):
                return current
        current = current.parent

    return None


def find_files(
    root: Union[str, Path],
    pattern: str = "*",
    recursive: bool = True,
    include_hidden: bool = False,
    exclude_dirs: Optional[List[str]] = None,
) -> Generator[Path, None, None]:
    """
    Find files matching a pattern.

    Args:
        root: Root directory to search
        pattern: Glob pattern (e.g., "*.py", "**/*.md")
        recursive: Search recursively
        include_hidden: Include hidden files/directories
        exclude_dirs: Directory names to exclude (e.g., ['node_modules', '.git'])

    Yields:
        Matching file paths
    """
    root = Path(root)

    if exclude_dirs is None:
        exclude_dirs = []

    # Use rglob for recursive search, glob for non-recursive
    glob_method = root.rglob if recursive else root.glob

    logger = logging.getLogger(__name__)

    for path in glob_method(pattern):
        # Skip directories
        if safe_is_dir(path, logger):
            continue

        # Skip hidden files if requested
        if not include_hidden and any(part.startswith(".") for part in path.parts):
            continue

        # Skip excluded directories
        if any(excluded in path.parts for excluded in exclude_dirs):
            continue

        yield path


def relative_to_cwd(path: Union[str, Path]) -> Path:
    """
    Get path relative to current working directory if possible.

    Args:
        path: Path to convert

    Returns:
        Relative path if under cwd, otherwise absolute path
    """
    path = Path(path).absolute()
    cwd = Path.cwd()

    try:
        return path.relative_to(cwd)
    except ValueError:
        # Path is not under cwd
        return path


def expand_path(path: Union[str, Path]) -> Path:
    """
    Expand user home directory and environment variables in path.

    Args:
        path: Path to expand

    Returns:
        Expanded path
    """
    if isinstance(path, str):
        # Expand environment variables
        path = os.path.expandvars(path)

    path = Path(path)

    # Expand user home directory
    return path.expanduser()


def is_safe_path(path: Union[str, Path], base_dir: Union[str, Path]) -> bool:
    """
    Check if a path is safe (doesn't escape base directory).

    Args:
        path: Path to check
        base_dir: Base directory that path should be under

    Returns:
        True if path is under base_dir
    """
    path = Path(path).resolve()
    base_dir = Path(base_dir).resolve()

    try:
        path.relative_to(base_dir)
        return True
    except ValueError:
        return False
