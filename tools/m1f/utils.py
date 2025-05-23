"""
Utility functions for m1f.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Union


def format_duration(seconds: float) -> str:
    """Format duration in seconds to a human-readable string."""
    if seconds < 60:
        return f"{seconds:.2f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.2f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.2f} hours"


def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def calculate_checksum(content: str) -> str:
    """Calculate SHA-256 checksum of content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def is_binary_file(file_path: Path) -> bool:
    """Check if a file is likely binary based on its content."""
    # Common binary extensions
    binary_extensions = {
        # Images
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".tiff",
        ".tif",
        ".ico",
        ".webp",
        ".svgz",
        # Audio
        ".mp3",
        ".wav",
        ".ogg",
        ".flac",
        ".aac",
        ".wma",
        ".m4a",
        # Video
        ".mp4",
        ".avi",
        ".mkv",
        ".mov",
        ".wmv",
        ".flv",
        ".webm",
        ".mpeg",
        ".mpg",
        # Archives
        ".zip",
        ".rar",
        ".7z",
        ".tar",
        ".gz",
        ".bz2",
        ".xz",
        ".jar",
        ".war",
        ".ear",
        # Executables
        ".exe",
        ".dll",
        ".so",
        ".dylib",
        ".bin",
        ".msi",
        ".pdb",
        ".lib",
        ".o",
        ".obj",
        ".pyc",
        ".pyo",
        ".class",
        # Documents
        ".pdf",
        ".doc",
        ".ppt",
        ".xls",
        # Databases
        ".db",
        ".sqlite",
        ".mdb",
        ".accdb",
        ".dbf",
        ".dat",
        # Fonts
        ".ttf",
        ".otf",
        ".woff",
        ".woff2",
        ".eot",
        # Others
        ".iso",
        ".img",
        ".vhd",
        ".vhdx",
        ".vmdk",
        ".bak",
        ".tmp",
        ".lock",
        ".swo",
        ".swp",
    }

    # Check by extension first
    if file_path.suffix.lower() in binary_extensions:
        return True

    # Try reading first few bytes
    try:
        with open(file_path, "rb") as f:
            # Read first 1024 bytes
            chunk = f.read(1024)

            # Check for null bytes
            if b"\0" in chunk:
                return True

            # Try to decode as UTF-8
            try:
                chunk.decode("utf-8")
                return False
            except UnicodeDecodeError:
                return True

    except Exception:
        # If we can't read the file, assume it's binary
        return True


def normalize_path(path: Union[str, Path]) -> Path:
    """Normalize a path to use forward slashes and resolve it."""
    return Path(path).resolve()


def is_hidden_path(path: Path) -> bool:
    """Check if a path (file or directory) is hidden."""
    # Check if any part of the path starts with a dot
    for part in path.parts:
        if part.startswith(".") and part not in (".", ".."):
            return True
    return False


def get_relative_path(file_path: Path, base_path: Path) -> str:
    """Get relative path from base path, handling edge cases."""
    try:
        return str(file_path.relative_to(base_path))
    except ValueError:
        # If file is not under base path, return absolute path
        return str(file_path)


def parse_file_size(size_str: str) -> int:
    """Parse a file size string and return size in bytes.

    Supports formats like:
    - 1024 (bytes)
    - 10KB, 10K
    - 1.5MB, 1.5M
    - 2GB, 2G
    - 500TB, 500T

    Args:
        size_str: String representation of file size

    Returns:
        Size in bytes

    Raises:
        ValueError: If the size string cannot be parsed
    """
    if not size_str:
        raise ValueError("Empty size string")

    # Remove whitespace and convert to uppercase
    size_str = size_str.strip().upper()

    # Match number followed by optional unit
    pattern = r"^(\d+(?:\.\d+)?)\s*([KMGTB]?B?)?$"
    match = re.match(pattern, size_str)

    if not match:
        raise ValueError(f"Invalid size format: {size_str}")

    number = float(match.group(1))
    unit = match.group(2) or ""

    # Handle unit suffixes
    multipliers = {
        "": 1,
        "B": 1,
        "K": 1024,
        "KB": 1024,
        "M": 1024**2,
        "MB": 1024**2,
        "G": 1024**3,
        "GB": 1024**3,
        "T": 1024**4,
        "TB": 1024**4,
    }

    if unit not in multipliers:
        raise ValueError(f"Unknown size unit: {unit}")

    return int(number * multipliers[unit])
