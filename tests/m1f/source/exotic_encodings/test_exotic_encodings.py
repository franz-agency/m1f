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
Test script to verify that m1f can handle exotic encodings.
"""

import sys
import os
import subprocess
from pathlib import Path

# Set up the test environment
script_dir = Path(__file__).parent
tools_dir = script_dir.parent.parent.parent.parent / "tools"
output_dir = script_dir.parent.parent / "output"
output_dir.mkdir(exist_ok=True)
output_file = output_dir / "exotic_encodings_test.txt"

# Define the encodings we're testing
ENCODING_MAP = {
    "shiftjis.txt": "shift_jis",
    "big5.txt": "big5",
    "koi8r.txt": "koi8_r",
    "iso8859-8.txt": "iso8859_8",
    "euckr.txt": "euc_kr",
    "windows1256.txt": "cp1256",
}

# Print file info
print("Test files:")
for filename, encoding in ENCODING_MAP.items():
    filepath = script_dir / filename
    try:
        # Try to open with the expected encoding
        with open(filepath, "rb") as f:
            size = len(f.read())
        print(f"  {filename}: {size} bytes, expected encoding: {encoding}")
    except Exception as e:
        print(f"  ERROR with {filename}: {e}")

# Run m1f to combine files with encoding conversion
print("\nRunning m1f to combine files with encoding conversion to UTF-8...")

# Build the command
m1f_script = tools_dir / "m1f.py"
cmd = [
    sys.executable,
    str(m1f_script),
    "--source-directory",
    str(script_dir),
    "--output-file",
    str(output_file),
    "--separator-style",
    "MachineReadable",
    "--convert-to-charset",
    "utf-8",
    "--force",
    "--verbose",
    "--include-extensions",
    ".txt",
]
cmd += ["--exclude-extensions", ".utf8"]  # Exclude .utf8 files

print(f"Running command: {' '.join(cmd)}")

try:
    # Run the command
    process = subprocess.run(cmd, capture_output=True, text=True, check=True)

    # Print the output
    print(f"\nCommand output:")
    print(process.stdout[:500])  # Print first 500 chars of stdout
    if process.stderr:
        print(f"\nErrors:")
        print(process.stderr[:500])  # Print first 500 chars of stderr

    print(f"\nM1F completed. Exit code: {process.returncode}")

    # Check if the output file exists and has content
    if output_file.exists():
        size = output_file.stat().st_size
        print(f"Output file size: {size} bytes")

        # Print first few lines of the output file
        with open(output_file, "r", encoding="utf-8") as f:
            print("\nFirst 200 characters of the output file:")
            print(f.read(200))
    else:
        print("ERROR: Output file not created!")
except subprocess.CalledProcessError as e:
    print(f"ERROR running m1f: {e}")
    print(f"Exit code: {e.returncode}")
    print(f"Output: {e.stdout[:200]}")
    print(f"Error: {e.stderr[:200]}")
except Exception as e:
    print(f"ERROR: {e}")

print("\nTest complete!")
