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
Sync version between Python and package.json.

This script reads the version from tools/_version.py and updates package.json
to match, ensuring version consistency across the project.

Usage:
    python scripts/sync_version.py
"""

import json
import os
import re
import sys
import argparse
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent


def get_python_version():
    """Extract version from _version.py."""
    version_file = PROJECT_ROOT / "tools" / "_version.py"
    with open(version_file, "r", encoding="utf-8") as f:
        content = f.read()
        match = re.search(
            r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', content, re.MULTILINE
        )
        if match:
            return match.group(1)
        else:
            raise RuntimeError("Unable to find version string in _version.py")


def update_package_json(version):
    """Update version in package.json."""
    package_file = PROJECT_ROOT / "package.json"
    with open(package_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    old_version = data.get("version", "unknown")
    data["version"] = version

    with open(package_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")  # Add newline at end of file

    return old_version


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Sync version between Python and package.json",
        epilog="""
This script ensures version consistency across the m1f project by:
  1. Reading the version from tools/_version.py (source of truth)
  2. Updating package.json to match the Python version

Examples:
  # Sync versions
  %(prog)s
  
  # Check current versions without syncing
  %(prog)s --check
  
  # Show verbose output
  %(prog)s --verbose

Version Management:
  The version in tools/_version.py is the single source of truth.
  All other version references should be synchronized from this file.
  
  To change the version:
  1. Update tools/_version.py
  2. Run this script to sync package.json
  3. Commit both changes together
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--check", action="store_true", help="Check versions without updating (dry run)"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )

    args = parser.parse_args()

    try:
        # Get Python version
        python_version = get_python_version()
        if args.verbose or args.check:
            print(f"Python version (tools/_version.py): {python_version}")

        # Get current package.json version
        package_file = PROJECT_ROOT / "package.json"
        with open(package_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            npm_version = data.get("version", "unknown")

        if args.check:
            # Check mode - just display versions
            print(f"package.json version: {npm_version}")
            if python_version == npm_version:
                print("\n✓ Versions are in sync!")
                return 0
            else:
                print(f"\n✗ Version mismatch detected!")
                print(f"  Python:  {python_version}")
                print(f"  npm:     {npm_version}")
                return 1

        # Update package.json
        if python_version != npm_version:
            old_npm_version = update_package_json(python_version)
            print(f"Updated package.json: {old_npm_version} → {python_version}")
            print("\n✓ Version sync complete!")
        else:
            print("✓ Versions already in sync!")

        if args.verbose:
            print(f"\nAll files now use version: {python_version}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
