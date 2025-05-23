#!/usr/bin/env python3
"""Script to check test failures and provide a summary."""

import subprocess
import sys

# Run pytest to get failures
print("Running pytest to identify failures...")
result = subprocess.run([
    sys.executable, "-m", "pytest",
    "tests/",
    "--tb=no",  # No traceback
    "-v",       # Verbose
    "--no-header",
    "-q"        # Quiet
], capture_output=True, text=True)

# Parse output for failures
lines = result.stdout.split('\n')
failures = []
for line in lines:
    if 'FAILED' in line or 'ERROR' in line:
        failures.append(line.strip())

print("\n" + "="*80)
print("TEST FAILURE SUMMARY")
print("="*80)

if failures:
    print(f"\nTotal failures found: {len(failures)}\n")
    for i, failure in enumerate(failures, 1):
        print(f"{i}. {failure}")
else:
    print("\nNo failures found! All tests passed.")

print("\n" + "="*80)

# Run specific checks for known issues
print("\nKNOWN ISSUES:")
print("-"*40)
print("1. test_large_file_handling - Creates 10MB file, slow and memory intensive")
print("2. test_no_default_excludes_with_excludes - Issue with .git directory inclusion")
print("3. Filename hash tests - May have issues with specific filename format expectations")
print("4. Encoding conversion - May have issues with character encoding detection") 