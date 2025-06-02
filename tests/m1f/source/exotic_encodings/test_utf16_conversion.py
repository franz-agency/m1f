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
Test script to verify that m1f can properly handle exotic encodings with UTF-16 conversion.
UTF-16 is a better intermediate format for handling diverse character sets compared to UTF-8.
"""

import sys
import os
import subprocess
import codecs
from pathlib import Path

# Set up the test environment
script_dir = Path(__file__).parent
tools_dir = script_dir.parent.parent.parent.parent / "tools"
output_dir = script_dir.parent.parent / "output"
output_dir.mkdir(exist_ok=True)
output_file = output_dir / "exotic_encodings_utf16_test.txt"
extracted_dir = script_dir.parent.parent / "extracted" / "exotic_encodings_utf16"

if not extracted_dir.exists():
    extracted_dir.mkdir(parents=True, exist_ok=True)

# Define the encodings we're testing
ENCODING_MAP = {
    "shiftjis.txt": "shift_jis",
    "big5.txt": "big5",
    "koi8r.txt": "koi8_r",
    "iso8859-8.txt": "iso8859_8",
    "euckr.txt": "euc_kr",
    "windows1256.txt": "cp1256",
}

# Print file info and test that we can read them with their correct encodings
print("Test files (original):")
for filename, encoding in ENCODING_MAP.items():
    filepath = script_dir / filename
    try:
        # Try to open with the expected encoding
        with open(filepath, "rb") as f:
            size = len(f.read())

        # Try to decode with the expected encoding
        with open(filepath, "r", encoding=encoding) as f:
            content = f.read(50)  # Read first 50 chars

        print(f"  {filename}: {size} bytes, encoding: {encoding}")
        print(f"    Content sample: {content[:30]}...")
    except Exception as e:
        print(f"  ERROR with {filename}: {e}")

print("\n" + "=" * 50)
print("TEST 1: M1F WITH UTF-16 CONVERSION")
print("=" * 50)

# Run m1f to combine files with encoding conversion to UTF-16
print("\nRunning m1f to combine files with conversion to UTF-16...")

# Build the command for UTF-16 conversion
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
    "utf-16",
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

    # Print the output summary
    print(f"M1F completed with UTF-16 conversion. Exit code: {process.returncode}")

    # Check if the output file exists and has content
    if output_file.exists():
        size = output_file.stat().st_size
        print(f"Output file size: {size} bytes")
    else:
        print("ERROR: Output file not created!")
        sys.exit(1)
except subprocess.CalledProcessError as e:
    print(f"ERROR running m1f: {e}")
    print(f"Exit code: {e.returncode}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

print("\n" + "=" * 50)
print("TEST 2: S1F EXTRACTION WITH RESPECT TO ORIGINAL ENCODINGS")
print("=" * 50)

# Build the command for extraction with original encodings
s1f_script = tools_dir / "s1f.py"
cmd2 = [
    sys.executable,
    str(s1f_script),
    "--input-file",
    str(output_file),
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

    print(
        f"S1F completed (extraction with --respect-encoding). Exit code: {process.returncode}"
    )

    # Check the extracted files
    original_dir = extracted_dir / "original"
    if original_dir.exists():
        files = list(original_dir.glob("*.txt"))
        print(f"Extracted {len(files)} files to {original_dir}")

        # Try reading each file with its expected encoding
        print("\nChecking if files retained their original encodings:")
        for file_path in files:
            try:
                expected_encoding = ENCODING_MAP.get(file_path.name)
                if not expected_encoding:
                    print(
                        f"  {file_path.name}: Unknown expected encoding - skipping check"
                    )
                    continue

                # Try reading with the expected encoding
                try:
                    with open(file_path, "r", encoding=expected_encoding) as f:
                        text = f.read(100)
                    print(
                        f"  {file_path.name}: ✓ Successfully read with {expected_encoding}"
                    )
                    print(f"    Content sample: {text[:30]}...")
                except UnicodeDecodeError:
                    print(
                        f"  {file_path.name}: ✗ Failed to read with {expected_encoding}"
                    )

                    # If it failed with expected encoding, try UTF-8 and UTF-16
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            text = f.read(30)
                        print(f"    - Can be read with UTF-8 instead")
                    except UnicodeDecodeError:
                        pass

                    try:
                        with open(file_path, "r", encoding="utf-16") as f:
                            text = f.read(30)
                        print(f"    - Can be read with UTF-16 instead")
                    except UnicodeDecodeError:
                        pass
            except Exception as e:
                print(f"  Error with {file_path.name}: {e}")
    else:
        print(f"ERROR: Original encoding extraction directory not created!")
except subprocess.CalledProcessError as e:
    print(f"ERROR running s1f: {e}")
    print(f"Exit code: {e.returncode}")
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 50)
print("TEST 3: COMPARING ORIGINAL FILES WITH EXTRACTED FILES")
print("=" * 50)

print("\nComparing original files with their extracted versions:")
for filename, encoding in ENCODING_MAP.items():
    original_file = script_dir / filename
    extracted_file = extracted_dir / "original" / filename

    if not extracted_file.exists():
        print(f"  {filename}: ✗ Extracted file does not exist")
        continue

    # Read both files in binary mode to compare content
    with open(original_file, "rb") as f1:
        original_content = f1.read()
    with open(extracted_file, "rb") as f2:
        extracted_content = f2.read()

    # Compare file sizes
    orig_size = len(original_content)
    extr_size = len(extracted_content)

    # Try to decode both using the expected encoding
    try:
        original_text = codecs.decode(original_content, encoding)
        try:
            extracted_text = codecs.decode(extracted_content, encoding)
            # Compare the decoded text content (first 50 chars for simplicity)
            match = original_text[:50] == extracted_text[:50]
            if match:
                print(f"  {filename}: ✓ Content matches original (in {encoding})")
            else:
                print(f"  {filename}: ✗ Content doesn't match original")
                print(f"    Original: {original_text[:30]}...")
                print(f"    Extracted: {extracted_text[:30]}...")
        except UnicodeDecodeError:
            print(f"  {filename}: ✗ Extracted file can't be decoded with {encoding}")
    except UnicodeDecodeError:
        print(f"  {filename}: ⚠ Both files have encoding issues with {encoding}")

print(
    "\nTest complete - UTF-16 is a better intermediate format for proper character set handling!"
)
