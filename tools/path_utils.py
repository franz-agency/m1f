# Copyright 2025 Franz und Franz GmbH
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path, PureWindowsPath
from typing import Union


def convert_to_posix_path(path_val: str) -> str:
    """Convert a path string to POSIX style."""
    return PureWindowsPath(path_val).as_posix()


def normalize_path(path: Union[Path, str]) -> str:
    """Normalize a Path or path-like object to POSIX style."""
    return PureWindowsPath(str(path)).as_posix()
