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

"""Script to check test failures and provide a summary."""

import subprocess
import sys

# Run pytest to get failures
print("Running pytest to identify failures...")
result = subprocess.run(
    [
        sys.executable,
        "-m",
        "pytest",
        "tests/",
        "--tb=no",  # No traceback
        "-v",  # Verbose
        "--no-header",
        "-q",  # Quiet
    ],
    capture_output=True,
    text=True,
)

# Parse output for failures
lines = result.stdout.split("\n")
failures = []
for line in lines:
    if "FAILED" in line or "ERROR" in line:
        failures.append(line.strip())

print("\n" + "=" * 80)
print("TEST FAILURE SUMMARY")
print("=" * 80)

if failures:
    print(f"\nTotal failures found: {len(failures)}\n")
    for i, failure in enumerate(failures, 1):
        print(f"{i}. {failure}")
else:
    print("\nNo failures found! All tests passed.")

print("\n" + "=" * 80)

# Run specific checks for known issues
print("\nKNOWN ISSUES:")
print("-" * 40)
print("1. test_large_file_handling - Creates 10MB file, slow and memory intensive")
print("2. test_no_default_excludes_with_excludes - Issue with .git directory inclusion")
print(
    "3. Filename hash tests - May have issues with specific filename format expectations"
)
print("4. Encoding conversion - May have issues with character encoding detection")
