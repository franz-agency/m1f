#!/usr/bin/env python3
"""
Bump version in _version.py and sync across the project.

This script updates the version in tools/_version.py and then runs sync_version.py
to update package.json.

Usage:
    python scripts/bump_version.py [major|minor|patch|<version>]

Examples:
    python scripts/bump_version.py patch        # 3.1.0 → 3.1.1
    python scripts/bump_version.py minor        # 3.1.0 → 3.2.0
    python scripts/bump_version.py major        # 3.1.0 → 4.0.0
    python scripts/bump_version.py 3.2.0-beta1 # 3.1.0 → 3.2.0-beta1
"""

import re
import subprocess
import sys
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent


def get_current_version():
    """Extract current version from _version.py."""
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


def parse_version(version):
    """Parse version string into components."""
    # Handle versions with pre-release tags
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)(.*)$", version)
    if match:
        major, minor, patch, pre = match.groups()
        return int(major), int(minor), int(patch), pre
    else:
        raise ValueError(f"Invalid version format: {version}")


def bump_version(current_version, bump_type):
    """Bump version according to the specified type."""
    major, minor, patch, pre = parse_version(current_version)

    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        if pre:
            # If we have a pre-release, just bump to the release version
            return f"{major}.{minor}.{patch}"
        else:
            return f"{major}.{minor}.{patch + 1}"
    else:
        # Assume it's a specific version
        return bump_type


def update_version_file(new_version):
    """Update version in _version.py."""
    version_file = PROJECT_ROOT / "tools" / "_version.py"
    with open(version_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Update version string
    content = re.sub(
        r'^__version__\s*=\s*[\'"][^\'"]*[\'"]',
        f'__version__ = "{new_version}"',
        content,
        flags=re.MULTILINE,
    )

    # Update version_info tuple
    major, minor, patch, _ = parse_version(new_version)
    content = re.sub(
        r"^__version_info__\s*=.*$",
        f'__version_info__ = tuple(int(x) for x in __version__.split(".")[:3])',
        content,
        flags=re.MULTILINE,
    )

    with open(version_file, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    """Main function."""
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help", "help"]:
        print(__doc__)
        return 0 if sys.argv[1:] else 1

    bump_type = sys.argv[1]

    try:
        # Get current version
        current_version = get_current_version()
        print(f"Current version: {current_version}")

        # Calculate new version
        new_version = bump_version(current_version, bump_type)
        print(f"New version: {new_version}")

        if current_version == new_version:
            print("Version unchanged.")
            return 0

        # Update version file
        update_version_file(new_version)
        print(f"Updated _version.py")

        # Sync with package.json
        sync_script = PROJECT_ROOT / "scripts" / "sync_version.py"
        result = subprocess.run(
            [sys.executable, str(sync_script)], capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"Error syncing version: {result.stderr}")
            return 1

        print(f"\nVersion bumped successfully: {current_version} → {new_version}")
        print("\nNext steps:")
        print("1. Review the changes")
        print(
            "2. Commit with: git commit -am 'chore: bump version to {}'".format(
                new_version
            )
        )
        print("3. Tag with: git tag v{}".format(new_version))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
