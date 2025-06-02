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
    "LICENSE",
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
