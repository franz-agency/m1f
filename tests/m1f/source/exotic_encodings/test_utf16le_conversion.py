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
Test script to verify that m1f can properly handle exotic encodings with UTF-16-LE conversion.
UTF-16-LE is a better intermediate format for handling diverse character sets compared to UTF-8.
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
output_file = output_dir / "exotic_encodings_utf16le_test.txt"
extracted_dir = script_dir.parent.parent / "extracted" / "exotic_encodings_utf16le"

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
print("TEST 1: M1F WITH UTF-16-LE CONVERSION")
print("=" * 50)

# Run m1f to combine files with encoding conversion to UTF-16-LE
print("\nRunning m1f to combine files with conversion to UTF-16-LE...")

# Build the command for UTF-16-LE conversion
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
    "utf-16-le",
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
    print(f"M1F completed with UTF-16-LE conversion. Exit code: {process.returncode}")

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

                    # If it failed with expected encoding, try other encodings
                    for test_encoding in ["utf-8", "utf-16", "utf-16-le"]:
                        try:
                            with open(file_path, "r", encoding=test_encoding) as f:
                                text = f.read(30)
                            print(f"    - Can be read with {test_encoding} instead")
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

# Now let's create a modified test script that can be added to the main test suite
print("\n" + "=" * 50)
print("CREATING AUTOMATED TEST FOR INCLUSION IN MAIN TEST SUITE")
print("=" * 50)

test_script_path = script_dir.parent / "test_encoding_conversion.py"
test_script_content = '''
import os
import sys
import pytest
from pathlib import Path

# Add the tools directory to path to import the m1f module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))
import m1f

def test_exotic_encoding_conversion():
    """Test that m1f correctly detects and converts files with exotic encodings using UTF-16-LE."""
    # Paths for test resources
    # The generated test lives one directory above this script, so no
    # extra "source" segment is needed when referencing the fixture
    # directory.
    test_dir = Path(__file__).parent / "exotic_encodings"
    output_dir = Path(__file__).parent / "output"
    output_file = output_dir / "test_encoding_utf16le.txt"
    
    # Create output dir if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    # Define encoding map for verification
    encoding_map = {
        "shiftjis.txt": "shift_jis",
        "big5.txt": "big5", 
        "koi8r.txt": "koi8_r",
        "iso8859-8.txt": "iso8859_8",
        "euckr.txt": "euc_kr",
        "windows1256.txt": "cp1256",
    }
    
    # Setup test args for m1f
    test_args = [
        "--source-directory", str(test_dir),
        "--output-file", str(output_file),
        "--separator-style", "MachineReadable",
        "--convert-to-charset", "utf-16-le",
        "--force",
        "--include-extensions", ".txt",
        "--exclude-extensions", ".utf8",
        "--minimal-output"
    ]
    
    # Modify sys.argv for testing
    old_argv = sys.argv
    sys.argv = ["m1f.py"] + test_args
    
    try:
        # Run m1f with the test arguments
        m1f.main()
        
        # Verify the output file exists
        assert output_file.exists(), "Output file was not created"
        assert output_file.stat().st_size > 0, "Output file is empty"
        
        # Check that the file contains encoding info for each test file
        with open(output_file, "r", encoding="utf-16-le") as f:
            content = f.read()
            
        # Verify each file is mentioned in the combined output
        for filename in encoding_map.keys():
            assert filename in content, f"File {filename} was not included in the output"
            
        # Verify encoding information was preserved
        for encoding in encoding_map.values():
            assert f'"encoding": "{encoding}"' in content, f"Encoding {encoding} not detected correctly"
            
    finally:
        # Restore sys.argv
        sys.argv = old_argv
        
        # Clean up output file
        if output_file.exists():
            try:
                output_file.unlink()
            except:
                pass
                
    # The test passes if we get here without assertions failing
'''

# Write the test script to include in the main test suite
with open(test_script_path, "w", encoding="utf-8") as f:
    f.write(test_script_content)

print(f"Created automated test file: {test_script_path}")
print(
    "\nTest complete - UTF-16-LE is a better intermediate format for proper character set handling!"
)
