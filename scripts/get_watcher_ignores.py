#!/usr/bin/env python3
"""
Helper script to extract watcher ignore paths from .m1f.config.yml
"""
import os
import sys
import yaml
from pathlib import Path


def get_ignore_patterns():
    """Get combined ignore patterns from config"""
    config_path = Path(__file__).parent.parent / ".m1f.config.yml"

    if not config_path.exists():
        # Return default patterns if no config
        return [".m1f/", ".git/", ".venv/", "__pycache__/", "*.pyc"]

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        ignore_patterns = []

        # Get watcher ignored paths
        watcher_config = config.get("global", {}).get("watcher", {})
        ignored_paths = watcher_config.get("ignored_paths", [])
        ignore_patterns.extend(ignored_paths)

        # Add global excludes
        global_excludes = config.get("global", {}).get("global_excludes", [])
        for pattern in global_excludes:
            # Convert glob patterns to simpler forms for the watcher
            if pattern.startswith("**/"):
                # Remove leading **/ for watcher compatibility
                ignore_patterns.append(pattern[3:])
            else:
                ignore_patterns.append(pattern)

        # Remove duplicates while preserving order
        seen = set()
        unique_patterns = []
        for pattern in ignore_patterns:
            if pattern not in seen:
                seen.add(pattern)
                unique_patterns.append(pattern)

        return unique_patterns

    except Exception as e:
        # Return default patterns on error
        return [".m1f/", ".git/", ".venv/", "__pycache__/", "*.pyc"]


if __name__ == "__main__":
    patterns = get_ignore_patterns()

    # Output format depends on argument
    if len(sys.argv) > 1 and sys.argv[1] == "--regex":
        # Output as regex pattern for grep
        escaped = [p.replace(".", r"\.").replace("*", ".*") for p in patterns]
        print("(" + "|".join(escaped) + ")")
    elif len(sys.argv) > 1 and sys.argv[1] == "--fswatch":
        # Output as fswatch exclude arguments
        for pattern in patterns:
            print(f"--exclude '{pattern}'")
    elif len(sys.argv) > 1 and sys.argv[1] == "--inotify":
        # Output as inotify exclude pattern
        print("(" + "|".join(patterns) + ")")
    else:
        # Default: one pattern per line
        for pattern in patterns:
            print(pattern)
