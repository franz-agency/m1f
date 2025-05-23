#!/usr/bin/env python3
"""Simple test to debug no-default-excludes behavior"""

import sys
import subprocess
from pathlib import Path

# Get paths
test_dir = Path(__file__).parent
source_dir = test_dir / "source"
output_dir = test_dir / "output"
output_dir.mkdir(exist_ok=True)

# Test 1: Run with --no-default-excludes only
output1 = output_dir / "debug_no_default.txt"
cmd1 = [
    sys.executable, "-m", "m1f",
    "--source-directory", str(source_dir),
    "--output-file", str(output1),
    "--no-default-excludes",
    "--force"
]
print("Running Test 1:", " ".join(cmd1))
result1 = subprocess.run(cmd1, capture_output=True, text=True)
print(f"Exit code: {result1.returncode}")
if result1.returncode == 0 and output1.exists():
    content1 = output1.read_text()
    print(f"Output file size: {len(content1)} bytes")
    print(f"Contains 'placeholder.txt': {'placeholder.txt' in content1}")
    print(f"Contains '.git': {'.git' in content1}")
    print(f"Contains 'node_modules': {'node_modules' in content1}")
else:
    print(f"Error: {result1.stderr}")

print("\n" + "="*50 + "\n")

# Test 2: Run with --no-default-excludes and --excludes node_modules
output2 = output_dir / "debug_no_default_with_excludes.txt"
cmd2 = [
    sys.executable, "-m", "m1f",
    "--source-directory", str(source_dir),
    "--output-file", str(output2),
    "--no-default-excludes",
    "--excludes", "node_modules",
    "--force"
]
print("Running Test 2:", " ".join(cmd2))
result2 = subprocess.run(cmd2, capture_output=True, text=True)
print(f"Exit code: {result2.returncode}")
if result2.returncode == 0 and output2.exists():
    content2 = output2.read_text()
    print(f"Output file size: {len(content2)} bytes")
    print(f"Contains 'placeholder.txt': {'placeholder.txt' in content2}")
    print(f"Contains '.git': {'.git' in content2}")
    print(f"Contains 'node_modules': {'node_modules' in content2}")
else:
    print(f"Error: {result2.stderr}") 