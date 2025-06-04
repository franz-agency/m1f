#!/usr/bin/env python3
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
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent

def get_python_version():
    """Extract version from _version.py."""
    version_file = PROJECT_ROOT / "tools" / "_version.py"
    with open(version_file, "r", encoding="utf-8") as f:
        content = f.read()
        match = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', content, re.MULTILINE)
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
    try:
        # Get Python version
        python_version = get_python_version()
        print(f"Python version: {python_version}")
        
        # Update package.json
        old_npm_version = update_package_json(python_version)
        print(f"Updated package.json: {old_npm_version} → {python_version}")
        
        print("\nVersion sync complete!")
        print(f"All files now use version: {python_version}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())