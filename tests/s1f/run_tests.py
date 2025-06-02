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
Run tests for the s1f.py script.

This script sets up the Python path and runs pytest for the s1f test suite.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the parent directory to Python path for importing the tools modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def main():
    """Run the pytest test suite for s1f.py."""
    # Determine the directory of this script
    script_dir = Path(__file__).parent

    # Ensure we have the output directory with test files
    output_dir = script_dir / "output"
    if not output_dir.exists() or not list(output_dir.glob("*.txt")):
        print("Error: Test files are missing from the output directory.")
        print("Please run the following commands to generate test files:")
        print(
            "python tools/m1f.py --source-directory tests/m1f/source --output-file tests/s1f/output/standard.txt --separator-style Standard --force"
        )
        print(
            "python tools/m1f.py --source-directory tests/m1f/source --output-file tests/s1f/output/detailed.txt --separator-style Detailed --force"
        )
        print(
            "python tools/m1f.py --source-directory tests/m1f/source --output-file tests/s1f/output/markdown.txt --separator-style Markdown --force"
        )
        print(
            "python tools/m1f.py --source-directory tests/m1f/source --output-file tests/s1f/output/machinereadable.txt --separator-style MachineReadable --force"
        )
        return 1

    # Create the extracted directory if it doesn't exist
    extracted_dir = script_dir / "extracted"
    extracted_dir.mkdir(exist_ok=True)

    # Run pytest with verbose output
    print(f"Running tests from {script_dir}")
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-xvs",  # verbose output, stop on first failure
            os.path.join(script_dir, "test_s1f.py"),
        ]
    ).returncode


if __name__ == "__main__":
    sys.exit(main())
