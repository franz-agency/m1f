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

# Documentation file extensions
DOCUMENTATION_EXTENSIONS: Set[str] = {
    # Man pages
    ".1",
    ".1st",
    ".2",
    ".3",
    ".4",
    ".5",
    ".6",
    ".7",
    ".8",
    # Documentation formats
    ".adoc",
    ".asciidoc",
    ".changelog",
    ".changes",
    ".creole",
    ".faq",
    ".feature",
    ".help",
    ".history",
    ".info",
    ".lhs",
    ".litcoffee",
    ".ltx",
    ".man",
    ".markdown",
    ".markdown2",
    ".md",
    ".mdown",
    ".mdtxt",
    ".mdtext",
    ".mdwn",
    ".mdx",
    ".me",
    ".mkd",
    ".mkdn",
    ".mkdown",
    ".ms",
    ".news",
    ".nfo",
    ".notes",
    ".org",
    ".pod",
    ".pod6",
    ".qmd",
    ".rd",
    ".rdoc",
    ".readme",
    ".release",
    ".rmd",
    ".roff",
    ".rst",
    ".rtf",
    ".story",
    ".t",
    ".tex",
    ".texi",
    ".texinfo",
    ".text",
    ".textile",
    ".todo",
    ".tr",
    ".txt",
    ".wiki",
}

# Documentation extensions that are typically UTF-8 encoded
UTF8_PREFERRED_EXTENSIONS: Set[str] = {
    # Markdown variants
    ".md",
    ".markdown",
    ".markdown2",
    ".mdown",
    ".mdtxt",
    ".mdtext",
    ".mdwn",
    ".mdx",
    ".mkd",
    ".mkdn",
    ".mkdown",
    ".rmd",
    ".qmd",
    # Plain text
    ".txt",
    ".text",
    ".readme",
    ".changelog",
    ".changes",
    ".todo",
    ".notes",
    ".history",
    ".news",
    ".release",
    # Structured text formats
    ".rst",
    ".asciidoc",
    ".adoc",
    ".org",
    ".textile",
    ".creole",
    ".wiki",
    # Developer documentation
    ".pod",
    ".pod6",
    ".rdoc",
    ".rd",
    # Code documentation
    ".lhs",
    ".litcoffee",
    # Other UTF-8 common formats
    ".faq",
    ".help",
    ".info",
    ".feature",
    ".story",
}

# ANSI color codes
ANSI_COLORS = {
    "HEADER": "\033[95m",
    "BLUE": "\033[94m",
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "RED": "\033[91m",
    "RESET": "\033[0m",
    "BOLD": "\033[1m",
}
