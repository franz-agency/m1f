#!/usr/bin/env python3
"""Setup script for the m1f tools suite."""

import os
import re
from pathlib import Path
from setuptools import setup, find_packages

# Read version from tools/_version.py
version_file = Path(__file__).parent / "tools" / "_version.py"
with open(version_file, "r", encoding="utf-8") as f:
    version_match = re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE
    )
    if version_match:
        version = version_match.group(1)
    else:
        raise RuntimeError("Unable to find version string in _version.py")

setup(
    name="m1f",
    version=version,
    description="m1f - Make One File - Combine multiple text files into a single output file",
    author="Franz und Franz",
    author_email="office@franz.agency",
    url="https://m1f.dev",
    packages=find_packages(where="tools"),
    package_dir={"": "tools"},
    py_modules=[
        "m1f",
        "m1f_claude",
        "m1f_claude_runner",
        "m1f_help",
        "m1f_init",
        "m1f_update",
        "token_counter",
        "s1f",
        "_version",
    ],
    entry_points={
        "console_scripts": [
            # Core tools
            "m1f=m1f:main",
            "s1f=s1f.cli:main",
            "m1f-html2md=html2md_tool.cli:main",
            "m1f-scrape=scrape_tool.cli:main",
            "m1f-research=research.cli:main",
            # Utility tools
            "m1f-claude=m1f_claude:main",
            "m1f-help=m1f_help:main",
            "m1f-init=m1f_init:main",
            "m1f-token-counter=token_counter:main",
            "m1f-update=m1f_update:main",
            # Alias for backwards compatibility
            "m1f-s1f=s1f.cli:main",
        ],
    },
    python_requires=">=3.10",
    install_requires=[
        "pathspec>=0.11.0",
        "tiktoken>=0.5.0",
        "colorama>=0.4.6",
    ],
    extras_require={
        "full": [
            "chardet>=5.0.0",
            "detect-secrets>=1.4.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
