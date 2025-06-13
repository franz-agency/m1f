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
Setup script for the m1f tool.
"""

import os
import re
from setuptools import setup, find_packages

# Read version from _version.py
version_file = os.path.join(os.path.dirname(__file__), "_version.py")
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
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "m1f=m1f:main",
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
