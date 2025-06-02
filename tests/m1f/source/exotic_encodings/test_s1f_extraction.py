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
Test script to verify that s1f properly extracts files with their original encodings.
"""

import sys
import os
import subprocess
from pathlib import Path

# Set up the test environment
script_dir = Path(__file__).parent
tools_dir = script_dir.parent.parent.parent.parent / "tools"
output_dir = script_dir.parent.parent / "output"
extracted_dir = script_dir.parent.parent / "extracted" / "exotic_encodings"

if not extracted_dir.exists():
    extracted_dir.mkdir(parents=True, exist_ok=True)

# Input file created by m1f
input_file = output_dir / "exotic_encodings_test.txt"

# Define the encodings we're testing
ENCODING_MAP = {
    "shiftjis.txt": "shift_jis",
    "big5.txt": "big5",
    "koi8r.txt": "koi8_r",
    "iso8859-8.txt": "iso8859_8",
    "euckr.txt": "euc_kr",
    "windows1256.txt": "cp1256",
}

print(f"Input file: {input_file}")
print(f"Extraction directory: {extracted_dir}")

# First test: normal extraction (UTF-8 output)
print("\nTest 1: Normal extraction (all files extracted as UTF-8)")
print("----------------------------------------")

# Build the command for normal extraction
s1f_script = tools_dir / "s1f.py"
cmd1 = [
    sys.executable,
    str(s1f_script),
    "--input-file",
    str(input_file),
    "--destination-directory",
    str(extracted_dir / "utf8"),
    "--force",
    "--verbose",
]

print(f"Running command: {' '.join(cmd1)}")

try:
    # Run the command
    process = subprocess.run(cmd1, capture_output=True, text=True, check=True)

    # Print the output
    print(f"\nCommand output:")
    print(process.stdout[:300])  # Print first 300 chars of stdout
    if process.stderr:
        print(f"\nErrors:")
        print(process.stderr[:300])  # Print first 300 chars of stderr

    print(f"\nS1F completed (UTF-8 extraction). Exit code: {process.returncode}")

    # Check the extracted files
    utf8_dir = extracted_dir / "utf8"
    if utf8_dir.exists():
        files = list(utf8_dir.glob("*.txt"))
        print(f"Extracted {len(files)} files to {utf8_dir}")

        # Print info about the first few bytes of each file
        for file_path in files:
            try:
                with open(file_path, "rb") as f:
                    content = f.read(50)  # Read first 50 bytes

                print(f"  {file_path.name}: {len(content)} bytes")
                # Try reading with UTF-8
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        text = f.read(100)
                    print(f"    UTF-8 reading: success, first 50 chars: {text[:50]}")
                except UnicodeDecodeError:
                    print(f"    UTF-8 reading: failed - not valid UTF-8")
            except Exception as e:
                print(f"  Error with {file_path.name}: {e}")
    else:
        print(f"ERROR: UTF-8 extraction directory not created!")
except subprocess.CalledProcessError as e:
    print(f"ERROR running s1f (UTF-8 extraction): {e}")
    print(f"Exit code: {e.returncode}")
    print(f"Output: {e.stdout[:200]}")
    print(f"Error: {e.stderr[:200]}")
except Exception as e:
    print(f"ERROR: {e}")

# Second test: extraction with respect to original encodings
print("\nTest 2: Extraction with --respect-encoding")
print("----------------------------------------")

# Build the command for extraction with original encodings
cmd2 = [
    sys.executable,
    str(s1f_script),
    "--input-file",
    str(input_file),
    "--destination-directory",
    str(extracted_dir / "original"),
    "--respect-encoding",
    "--force",
    "--verbose",
]

print(f"Running command: {' '.join(cmd2)}")

try:
    # Run the command
    process = subprocess.run(cmd2, capture_output=True, text=True, check=True)

    # Print the output
    print(f"\nCommand output:")
    print(process.stdout[:300])  # Print first 300 chars of stdout
    if process.stderr:
        print(f"\nErrors:")
        print(process.stderr[:300])  # Print first 300 chars of stderr

    print(
        f"\nS1F completed (original encoding extraction). Exit code: {process.returncode}"
    )

    # Check the extracted files
    original_dir = extracted_dir / "original"
    if original_dir.exists():
        files = list(original_dir.glob("*.txt"))
        print(f"Extracted {len(files)} files to {original_dir}")

        # Try reading each file with its expected encoding
        for file_path in files:
            try:
                with open(file_path, "rb") as f:
                    content = f.read(50)  # Read first 50 bytes

                print(f"  {file_path.name}: {len(content)} bytes")

                # Try reading with expected encoding if we know it
                expected_encoding = ENCODING_MAP.get(file_path.name)
                if expected_encoding:
                    try:
                        with open(file_path, "r", encoding=expected_encoding) as f:
                            text = f.read(100)
                        print(
                            f"    {expected_encoding} reading: success, first 50 chars: {text[:50]}"
                        )
                    except UnicodeDecodeError:
                        print(
                            f"    {expected_encoding} reading: failed - not valid {expected_encoding}"
                        )

                # Try reading with UTF-8 to see if that works too
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        text = f.read(100)
                    print(f"    UTF-8 reading: success, first 50 chars: {text[:50]}")
                except UnicodeDecodeError:
                    print(f"    UTF-8 reading: failed - not valid UTF-8")
            except Exception as e:
                print(f"  Error with {file_path.name}: {e}")
    else:
        print(f"ERROR: Original encoding extraction directory not created!")
except subprocess.CalledProcessError as e:
    print(f"ERROR running s1f (original encoding extraction): {e}")
    print(f"Exit code: {e.returncode}")
    print(f"Output: {e.stdout[:200]}")
    print(f"Error: {e.stderr[:200]}")
except Exception as e:
    print(f"ERROR: {e}")

print("\nTest complete!")
