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
Safe file operations module for m1f.

Provides permission-error-safe wrappers for common file operations with consistent
logging and error handling.
"""

from __future__ import annotations

import os
import stat
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Generator, Optional, Union, TypeVar, Dict

PathLike = Union[str, Path]
F = TypeVar("F", bound=Callable[..., Any])


def handle_permission_errors(
    fallback_return: Any = None, log_message: Optional[str] = None
) -> Callable[[F], F]:
    """
    Decorator to handle permission errors in functions.

    Args:
        fallback_return: Value to return when PermissionError occurs
        log_message: Custom log message template. Use {path} and {error} placeholders.

    Returns:
        Decorated function that handles permission errors gracefully
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except PermissionError as e:
                # Try to extract path from args for logging
                path = None
                if args and hasattr(args[0], "__fspath__"):
                    path = args[0]
                elif "path" in kwargs:
                    path = kwargs["path"]
                elif args:
                    path = args[0]

                logger = kwargs.get("logger")
                if logger and log_message:
                    message = log_message.format(path=path, error=e)
                    logger.warning(message)
                elif logger:
                    logger.warning(f"Permission denied accessing '{path}': {e}")

                return fallback_return
            except OSError as e:
                # Handle other OS errors that might be permission-related
                if e.errno in (13, 1):  # EACCES, EPERM
                    path = None
                    if args and hasattr(args[0], "__fspath__"):
                        path = args[0]
                    elif "path" in kwargs:
                        path = kwargs["path"]
                    elif args:
                        path = args[0]

                    logger = kwargs.get("logger")
                    if logger:
                        logger.warning(f"Permission denied accessing '{path}': {e}")
                    return fallback_return
                raise

        return wrapper

    return decorator


def safe_exists(path: PathLike, logger: Optional[Any] = None) -> bool:
    """
    Check if a path exists, returning False on permission errors.

    Args:
        path: Path to check
        logger: Optional logger for warning messages

    Returns:
        True if path exists and is accessible, False otherwise
    """
    try:
        return Path(path).exists()
    except PermissionError as e:
        if logger:
            logger.warning(f"Permission denied checking existence of '{path}': {e}")
        return False
    except OSError as e:
        if e.errno in (13, 1):  # EACCES, EPERM
            if logger:
                logger.warning(f"Permission denied checking existence of '{path}': {e}")
            return False
        raise


def safe_is_dir(path: PathLike, logger: Optional[Any] = None) -> bool:
    """
    Check if a path is a directory, returning False on permission errors.

    Args:
        path: Path to check
        logger: Optional logger for warning messages

    Returns:
        True if path is a directory and accessible, False otherwise
    """
    try:
        return Path(path).is_dir()
    except PermissionError as e:
        if logger:
            logger.warning(f"Permission denied checking if '{path}' is directory: {e}")
        return False
    except OSError as e:
        if e.errno in (13, 1):  # EACCES, EPERM
            if logger:
                logger.warning(
                    f"Permission denied checking if '{path}' is directory: {e}"
                )
            return False
        raise


def safe_is_file(path: PathLike, logger: Optional[Any] = None) -> bool:
    """
    Check if a path is a file, returning False on permission errors.

    Args:
        path: Path to check
        logger: Optional logger for warning messages

    Returns:
        True if path is a file and accessible, False otherwise
    """
    try:
        return Path(path).is_file()
    except PermissionError as e:
        if logger:
            logger.warning(f"Permission denied checking if '{path}' is file: {e}")
        return False
    except OSError as e:
        if e.errno in (13, 1):  # EACCES, EPERM
            if logger:
                logger.warning(f"Permission denied checking if '{path}' is file: {e}")
            return False
        raise


def safe_stat(path: PathLike, logger: Optional[Any] = None) -> Optional[os.stat_result]:
    """
    Get path statistics, returning None on permission errors.

    Args:
        path: Path to stat
        logger: Optional logger for warning messages

    Returns:
        os.stat_result if accessible, None otherwise
    """
    try:
        return Path(path).stat()
    except PermissionError as e:
        if logger:
            logger.warning(f"Permission denied accessing stats for '{path}': {e}")
        return None
    except OSError as e:
        if e.errno in (13, 1):  # EACCES, EPERM
            if logger:
                logger.warning(f"Permission denied accessing stats for '{path}': {e}")
            return None
        raise


@contextmanager
def safe_open(
    path: PathLike, mode: str = "r", logger: Optional[Any] = None, **kwargs
) -> Generator[Optional[Any], None, None]:
    """
    Context manager for safely opening files with permission error handling.

    Args:
        path: Path to open
        mode: File mode (same as built-in open)
        logger: Optional logger for warning messages
        **kwargs: Additional arguments passed to open()

    Yields:
        File object if successful, None if permission denied
    """
    try:
        with open(path, mode, **kwargs) as f:
            yield f
    except PermissionError as e:
        if logger:
            logger.warning(f"Permission denied opening '{path}' in mode '{mode}': {e}")
        yield None
    except OSError as e:
        if e.errno in (13, 1):  # EACCES, EPERM
            if logger:
                logger.warning(
                    f"Permission denied opening '{path}' in mode '{mode}': {e}"
                )
            yield None
        else:
            raise


def safe_mkdir(
    path: PathLike,
    logger: Optional[Any] = None,
    parents: bool = False,
    exist_ok: bool = False,
    **kwargs,
) -> bool:
    """
    Create directory safely, returning False on permission errors.

    Args:
        path: Directory path to create
        logger: Optional logger for warning messages
        parents: If True, create parent directories as needed
        exist_ok: If True, don't raise error if directory exists
        **kwargs: Additional arguments passed to mkdir()

    Returns:
        True if directory was created or already exists, False on permission error
    """
    try:
        Path(path).mkdir(parents=parents, exist_ok=exist_ok, **kwargs)
        return True
    except PermissionError as e:
        if logger:
            logger.warning(f"Permission denied creating directory '{path}': {e}")
        return False
    except OSError as e:
        if e.errno in (13, 1):  # EACCES, EPERM
            if logger:
                logger.warning(f"Permission denied creating directory '{path}': {e}")
            return False
        raise


def safe_walk(
    path: PathLike, logger: Optional[Any] = None, **kwargs
) -> Generator[tuple[str, list[str], list[str]], None, None]:
    """
    Walk directory tree safely, skipping inaccessible directories.

    Args:
        path: Root directory to walk
        logger: Optional logger for warning messages
        **kwargs: Additional arguments passed to os.walk()

    Yields:
        Tuples of (dirpath, dirnames, filenames) for accessible directories
    """
    try:
        for root, dirs, files in os.walk(path, **kwargs):
            # Filter out directories we can't access
            # IMPORTANT: We must modify dirs in-place so os.walk sees the changes
            # and doesn't traverse into excluded directories
            dirs_to_remove = []
            for dirname in dirs:
                dir_path = Path(root) / dirname
                if not safe_exists(dir_path, logger):
                    dirs_to_remove.append(dirname)
                    if logger:
                        logger.debug(f"Skipping inaccessible directory: {dir_path}")

            # Remove inaccessible directories from the original list
            for dirname in dirs_to_remove:
                dirs.remove(dirname)

            # Filter out files we can't access
            accessible_files = []
            for filename in files:
                file_path = Path(root) / filename
                if safe_exists(file_path, logger):
                    accessible_files.append(filename)
                elif logger:
                    logger.debug(f"Skipping inaccessible file: {file_path}")

            # Return the original dirs list (now filtered) so modifications propagate
            yield root, dirs, accessible_files
    except PermissionError as e:
        if logger:
            logger.warning(f"Permission denied walking directory '{path}': {e}")
        return
    except OSError as e:
        if e.errno in (13, 1):  # EACCES, EPERM
            if logger:
                logger.warning(f"Permission denied walking directory '{path}': {e}")
            return
        raise


def safe_read_text(
    path: PathLike, logger: Optional[Any] = None, encoding: str = "utf-8", **kwargs
) -> Optional[str]:
    """
    Read text file safely, returning None on permission errors.

    Args:
        path: File path to read
        logger: Optional logger for warning messages
        encoding: Text encoding to use
        **kwargs: Additional arguments passed to Path.read_text()

    Returns:
        File content as string if successful, None on permission error
    """
    try:
        return Path(path).read_text(encoding=encoding, **kwargs)
    except PermissionError as e:
        if logger:
            logger.warning(f"Permission denied reading '{path}': {e}")
        return None
    except OSError as e:
        if e.errno in (13, 1):  # EACCES, EPERM
            if logger:
                logger.warning(f"Permission denied reading '{path}': {e}")
            return None
        raise


def safe_write_text(
    path: PathLike,
    content: str,
    logger: Optional[Any] = None,
    encoding: str = "utf-8",
    **kwargs,
) -> bool:
    """
    Write text file safely, returning False on permission errors.

    Args:
        path: File path to write
        content: Text content to write
        logger: Optional logger for warning messages
        encoding: Text encoding to use
        **kwargs: Additional arguments passed to Path.write_text()

    Returns:
        True if write successful, False on permission error
    """
    try:
        Path(path).write_text(content, encoding=encoding, **kwargs)
        return True
    except PermissionError as e:
        if logger:
            logger.warning(f"Permission denied writing to '{path}': {e}")
        return False
    except OSError as e:
        if e.errno in (13, 1):  # EACCES, EPERM
            if logger:
                logger.warning(f"Permission denied writing to '{path}': {e}")
            return False
        raise


def safe_iterdir(
    path: PathLike, logger: Optional[Any] = None
) -> Generator[Path, None, None]:
    """
    Iterate over directory contents safely, skipping inaccessible items.

    Args:
        path: Directory path to iterate
        logger: Optional logger for warning messages

    Yields:
        Path objects for accessible directory contents
    """
    try:
        path_obj = Path(path)
        for item in path_obj.iterdir():
            if safe_exists(item, logger):
                yield item
            elif logger:
                logger.debug(f"Skipping inaccessible item: {item}")
    except PermissionError as e:
        if logger:
            logger.warning(f"Permission denied iterating directory '{path}': {e}")
        return
    except OSError as e:
        if e.errno in (13, 1):  # EACCES, EPERM
            if logger:
                logger.warning(f"Permission denied iterating directory '{path}': {e}")
            return
        raise


def safe_glob(
    pattern: str, root: Optional[PathLike] = None, logger: Optional[Any] = None
) -> Generator[Path, None, None]:
    """
    Glob pattern matching with permission error handling.

    Args:
        pattern: Glob pattern to match
        root: Root directory for relative patterns
        logger: Optional logger for warning messages

    Yields:
        Path objects matching the pattern that are accessible
    """
    try:
        if root:
            root_path = Path(root)
            for match in root_path.glob(pattern):
                if safe_exists(match, logger):
                    yield match
        else:
            for match in Path().glob(pattern):
                if safe_exists(match, logger):
                    yield match
    except PermissionError as e:
        if logger:
            logger.warning(f"Permission denied during glob pattern '{pattern}': {e}")
        return
    except OSError as e:
        if e.errno in (13, 1):  # EACCES, EPERM
            if logger:
                logger.warning(
                    f"Permission denied during glob pattern '{pattern}': {e}"
                )
            return
        raise


def safe_is_symlink(path: PathLike, logger: Optional[Any] = None) -> bool:
    """
    Check if a path is a symbolic link, returning False on permission errors.

    Args:
        path: Path to check
        logger: Optional logger for warning messages

    Returns:
        True if path is a symlink and accessible, False otherwise
    """
    try:
        return Path(path).is_symlink()
    except PermissionError as e:
        if logger:
            logger.warning(f"Permission denied checking if '{path}' is symlink: {e}")
        return False
    except OSError as e:
        if e.errno in (13, 1):  # EACCES, EPERM
            if logger:
                logger.warning(
                    f"Permission denied checking if '{path}' is symlink: {e}"
                )
            return False
        raise


def safe_resolve(path: PathLike, logger: Optional[Any] = None) -> Optional[Path]:
    """
    Resolve a path safely, returning None on permission errors.

    Args:
        path: Path to resolve
        logger: Optional logger for warning messages

    Returns:
        Resolved Path if successful, None on permission error
    """
    try:
        return Path(path).resolve()
    except PermissionError as e:
        if logger:
            logger.warning(f"Permission denied resolving '{path}': {e}")
        return None
    except OSError as e:
        if e.errno in (13, 1):  # EACCES, EPERM
            if logger:
                logger.warning(f"Permission denied resolving '{path}': {e}")
            return None
        raise


# Export commonly used functions for easy importing
__all__ = [
    "handle_permission_errors",
    "safe_exists",
    "safe_is_dir",
    "safe_is_file",
    "safe_stat",
    "safe_open",
    "safe_mkdir",
    "safe_walk",
    "safe_read_text",
    "safe_write_text",
    "safe_iterdir",
    "safe_glob",
    "safe_is_symlink",
    "safe_resolve",
]
