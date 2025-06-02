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

"""Utility functions for s1f."""

import hashlib
import os
from pathlib import Path, PureWindowsPath
from typing import Optional, Union
from datetime import datetime, timezone
import re


def convert_to_posix_path(path_str: Optional[str]) -> str:
    """Convert a path string to use forward slashes."""
    if path_str is None:
        return ""
    return str(path_str).replace("\\", "/")


def calculate_sha256(content: bytes) -> str:
    """Calculate SHA256 checksum of the given bytes."""
    return hashlib.sha256(content).hexdigest()


def parse_iso_timestamp(timestamp_str: str) -> datetime:
    """Parse ISO timestamp string to datetime object.

    Handles both 'Z' suffix and explicit timezone offset formats.
    """
    if timestamp_str.endswith("Z"):
        # Replace 'Z' with '+00:00' for UTC
        timestamp_str = timestamp_str[:-1] + "+00:00"

    return datetime.fromisoformat(timestamp_str)


def normalize_line_endings(content: str, target: str = "\n") -> str:
    """Normalize line endings in content.

    Args:
        content: The content to normalize
        target: The target line ending ("\n", "\r\n", or "\r")

    Returns:
        Content with normalized line endings
    """
    # First normalize all to \n
    content = content.replace("\r\n", "\n").replace("\r", "\n")

    # Then convert to target if different
    if target != "\n":
        content = content.replace("\n", target)

    return content


def get_line_ending_style(content: str) -> str:
    """Detect the predominant line ending style in content.

    Returns:
        One of: "LF", "CRLF", "CR", or "MIXED"
    """
    lf_count = content.count("\n") - content.count("\r\n")
    crlf_count = content.count("\r\n")
    cr_count = content.count("\r") - content.count("\r\n")

    if lf_count > 0 and crlf_count == 0 and cr_count == 0:
        return "LF"
    elif crlf_count > 0 and lf_count == 0 and cr_count == 0:
        return "CRLF"
    elif cr_count > 0 and lf_count == 0 and crlf_count == 0:
        return "CR"
    elif lf_count + crlf_count + cr_count > 0:
        return "MIXED"
    else:
        return "NONE"


def validate_file_path(path: Path, base_dir: Path) -> bool:
    """Validate that a file path is safe and within the base directory.

    Args:
        path: The path to validate
        base_dir: The base directory that should contain the path

    Returns:
        True if the path is valid and safe, False otherwise
    """
    try:
        # Resolve the path (but don't require it to exist)
        resolved_path = (base_dir / path).resolve()

        # Check if it's within the base directory
        resolved_path.relative_to(base_dir.resolve())

        # Check for suspicious patterns
        if ".." in path.parts:
            return False

        return True
    except ValueError:
        # relative_to() raises ValueError if path is not relative to base_dir
        return False


def format_size(size_bytes: int) -> str:
    """Format size in bytes to human-readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def clean_encoding_name(encoding: str) -> str:
    """Clean up encoding name by removing error indicators."""
    if not encoding:
        return ""
    return encoding.split(" (with conversion errors)")[0].strip()


def is_binary_content(content: bytes, sample_size: int = 8192) -> bool:
    """Check if content appears to be binary.

    Args:
        content: The content to check
        sample_size: Number of bytes to sample

    Returns:
        True if content appears to be binary, False otherwise
    """
    # Sample the beginning of the content
    sample = content[:sample_size]

    # Check for null bytes (common in binary files)
    if b"\x00" in sample:
        return True

    # Check for high ratio of non-printable characters
    non_printable = sum(1 for byte in sample if byte < 32 and byte not in (9, 10, 13))

    if len(sample) > 0:
        ratio = non_printable / len(sample)
        return ratio > 0.3

    return False
