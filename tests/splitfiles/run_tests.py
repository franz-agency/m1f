#!/usr/bin/env python3
"""
Run tests for the splitfiles.py script.

This script sets up the Python path and runs pytest for the splitfiles test suite.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the parent directory to Python path for importing the tools modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def main():
    """Run the pytest test suite for splitfiles.py."""
    # Determine the directory of this script
    script_dir = Path(__file__).parent

    # Ensure we have the output directory with test files
    output_dir = script_dir / "output"
    if not output_dir.exists() or not list(output_dir.glob("*.txt")):
        print("Error: Test files are missing from the output directory.")
        print("Please run the following commands to generate test files:")
        print(
            "python tools/m1f.py --source-directory tests/m1f/source --output-file tests/splitfiles/output/standard.txt --separator-style Standard --force"
        )
        print(
            "python tools/m1f.py --source-directory tests/m1f/source --output-file tests/splitfiles/output/detailed.txt --separator-style Detailed --force"
        )
        print(
            "python tools/m1f.py --source-directory tests/m1f/source --output-file tests/splitfiles/output/markdown.txt --separator-style Markdown --force"
        )
        print(
            "python tools/m1f.py --source-directory tests/m1f/source --output-file tests/splitfiles/output/machinereadable.txt --separator-style MachineReadable --force"
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
            os.path.join(script_dir, "test_splitfiles.py"),
        ]
    ).returncode


if __name__ == "__main__":
    sys.exit(main())
