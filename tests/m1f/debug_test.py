#!/usr/bin/env python3
"""Debug script to test --no-default-excludes behavior"""

import sys
import tempfile
from pathlib import Path

# Add the tools directory to path to import the m1f module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from m1f.cli import get_parser
from m1f.config import Config


def test_no_default_excludes():
    """Test how the no-default-excludes flag affects configuration"""

    # Test 1: Default behavior
    parser = get_parser()
    args1 = parser.parse_args(["--source-directory", ".", "--output-file", "test.txt"])
    config1 = Config.from_args(args1)
    print("Test 1 - Default behavior:")
    print(f"  no_default_excludes: {config1.filter.no_default_excludes}")
    print(f"  exclude_dirs: {config1.filter.exclude_dirs}")
    print()

    # Test 2: With --no-default-excludes
    args2 = parser.parse_args(
        [
            "--source-directory",
            ".",
            "--output-file",
            "test.txt",
            "--no-default-excludes",
        ]
    )
    config2 = Config.from_args(args2)
    print("Test 2 - With --no-default-excludes:")
    print(f"  no_default_excludes: {config2.filter.no_default_excludes}")
    print(f"  exclude_dirs: {config2.filter.exclude_dirs}")
    print()

    # Test 3: With --no-default-excludes and --excludes
    args3 = parser.parse_args(
        [
            "--source-directory",
            ".",
            "--output-file",
            "test.txt",
            "--no-default-excludes",
            "--excludes",
            "node_modules",
        ]
    )
    config3 = Config.from_args(args3)
    print("Test 3 - With --no-default-excludes and --excludes node_modules:")
    print(f"  no_default_excludes: {config3.filter.no_default_excludes}")
    print(f"  exclude_dirs: {config3.filter.exclude_dirs}")
    print()


if __name__ == "__main__":
    test_no_default_excludes()
