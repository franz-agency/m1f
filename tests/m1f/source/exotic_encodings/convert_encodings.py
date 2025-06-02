#!/usr/bin/env python3
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
Convert the text files to their respective exotic encodings.
This script reads the UTF-8 files and saves them with the target encodings.
"""

import os
from pathlib import Path

# Define the file-to-encoding mappings
ENCODING_MAP = {
    "shiftjis.txt": "shift_jis",
    "big5.txt": "big5",
    "koi8r.txt": "koi8_r",
    "iso8859-8.txt": "iso8859_8",
    "euckr.txt": "euc_kr",
    "windows1256.txt": "cp1256",
}

# Get the directory containing this script
script_dir = Path(__file__).parent

# Process each file
for filename, encoding in ENCODING_MAP.items():
    filepath = script_dir / filename

    # Read the content (currently in UTF-8)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Create a backup with .utf8 extension
    with open(f"{filepath}.utf8", "w", encoding="utf-8") as f:
        f.write(content)

    # Save with the target encoding
    with open(filepath, "w", encoding=encoding) as f:
        f.write(content)

    print(f"Converted {filename} to {encoding}")

print("All files converted successfully.")
