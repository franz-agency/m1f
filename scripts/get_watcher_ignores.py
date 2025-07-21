#!/usr/bin/env python3
"""
Helper script to extract watcher ignore paths from .m1f.config.yml

This script provides ignore patterns in different formats for file watchers:
- Standard format: One pattern per line
- --regex: POSIX regex for grep
- --fswatch: Exclude arguments for fswatch (macOS)
- --inotify: Pattern for inotifywait (Linux)
"""
import os
import sys
import fnmatch
import re
import argparse
from pathlib import Path

# Default ignore patterns if no config is found
DEFAULT_PATTERNS = [
    ".m1f/",
    ".git/",
    ".venv/",
    "__pycache__/",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".DS_Store",
    "*.log",
    "tmp/",
    "temp/",
]


def load_gitignore_patterns(project_root):
    """Load patterns from .gitignore and .m1fignore files"""
    patterns = []

    for ignore_file in [".gitignore", ".m1fignore"]:
        ignore_path = project_root / ignore_file
        if ignore_path.exists():
            try:
                with open(ignore_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        # Skip comments and empty lines
                        if line and not line.startswith("#"):
                            patterns.append(line)
            except Exception:
                pass

    return patterns


def glob_to_regex(pattern):
    """Convert glob pattern to regex, handling common cases"""
    # Handle directory patterns
    if pattern.endswith("/"):
        pattern = pattern[:-1] + "/**"

    # Convert glob to regex
    regex = fnmatch.translate(pattern)

    # Handle ** for recursive matching
    regex = regex.replace(".*/", "(.*/)?")

    # Remove the \Z that fnmatch adds
    if regex.endswith("\\Z"):
        regex = regex[:-2]

    return regex


def get_ignore_patterns():
    """Get combined ignore patterns from config and ignore files"""
    project_root = Path(__file__).parent.parent
    config_path = project_root / ".m1f.config.yml"

    patterns = []

    # Try to load from config
    if config_path.exists():
        try:
            import yaml

            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            # Get global excludes
            global_excludes = config.get("global", {}).get("global_excludes", [])
            patterns.extend(global_excludes)

            # Get watcher-specific patterns (if they exist)
            watcher_config = config.get("global", {}).get("watcher", {})
            ignored_paths = watcher_config.get("ignored_paths", [])
            patterns.extend(ignored_paths)

        except Exception as e:
            # Fall back to defaults if config loading fails
            sys.stderr.write(f"Warning: Could not load config: {e}\n")
            patterns = DEFAULT_PATTERNS.copy()
    else:
        patterns = DEFAULT_PATTERNS.copy()

    # Add patterns from .gitignore and .m1fignore
    gitignore_patterns = load_gitignore_patterns(project_root)
    patterns.extend(gitignore_patterns)

    # Normalize patterns
    normalized = []
    for pattern in patterns:
        # Remove leading **/ for better compatibility
        if pattern.startswith("**/"):
            normalized.append(pattern[3:])
        else:
            normalized.append(pattern)

    # Remove duplicates while preserving order
    seen = set()
    unique_patterns = []
    for pattern in normalized:
        if pattern not in seen:
            seen.add(pattern)
            unique_patterns.append(pattern)

    return unique_patterns


def patterns_to_regex(patterns):
    """Convert patterns to a single regex for grep/inotify"""
    regex_parts = []
    for pattern in patterns:
        try:
            regex = glob_to_regex(pattern)
            regex_parts.append(regex)
        except Exception:
            # If conversion fails, try simple escaping
            escaped = re.escape(pattern).replace(r"\*", ".*")
            regex_parts.append(escaped)

    return "(" + "|".join(regex_parts) + ")"


def patterns_to_fswatch(patterns):
    """Convert patterns to fswatch exclude arguments"""
    excludes = []
    for pattern in patterns:
        # fswatch uses ERE (Extended Regular Expression)
        if "*" in pattern or "?" in pattern or "[" in pattern:
            # Convert glob to regex for fswatch
            try:
                regex = glob_to_regex(pattern)
                excludes.append(f"--exclude '{regex}'")
            except Exception:
                # Fallback to simple pattern
                excludes.append(f"--exclude '{pattern}'")
        else:
            # Plain string patterns
            excludes.append(f"--exclude '{pattern}'")

    return " ".join(excludes)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Extract watcher ignore paths from .m1f.config.yml",
        epilog="""
Examples:
  # Get patterns as a list (default)
  %(prog)s
  
  # Get patterns as regex for grep
  %(prog)s --regex
  
  # Get patterns for fswatch on macOS
  %(prog)s --fswatch
  
  # Get patterns for inotifywait on Linux
  %(prog)s --inotify
  
  # Debug mode - show all patterns with count
  %(prog)s --debug

This script reads ignore patterns from:
  1. .m1f.config.yml (global.global_excludes and global.watcher.ignored_paths)
  2. .gitignore file
  3. .m1fignore file
  4. Falls back to default patterns if no config is found

The patterns are normalized and duplicates are removed while preserving order.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Create mutually exclusive group for output formats
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--regex",
        action="store_true",
        help="Output as a single POSIX regex pattern for grep (e.g., '(pattern1|pattern2|...)')",
    )
    output_group.add_argument(
        "--fswatch",
        action="store_true",
        help="Output as fswatch exclude arguments for macOS (e.g., --exclude 'pattern1' --exclude 'pattern2')",
    )
    output_group.add_argument(
        "--inotify",
        action="store_true",
        help="Output as inotify exclude pattern for Linux (similar to --regex)",
    )
    output_group.add_argument(
        "--debug",
        action="store_true",
        help="Debug mode: show all patterns with their count and source information",
    )

    args = parser.parse_args()

    # Get the ignore patterns
    patterns = get_ignore_patterns()
    if not patterns:
        patterns = DEFAULT_PATTERNS

    # Output based on selected format
    if args.regex:
        # Output as regex pattern for grep
        print(patterns_to_regex(patterns))
    elif args.fswatch:
        # Output as fswatch exclude arguments
        print(patterns_to_fswatch(patterns))
    elif args.inotify:
        # Output as inotify exclude pattern (similar to regex)
        print(patterns_to_regex(patterns))
    elif args.debug:
        # Debug mode: show all patterns with their sources
        print("# Ignore patterns for file watchers")
        print("# Total patterns:", len(patterns))
        print()
        for pattern in patterns:
            print(pattern)
    else:
        # Default: one pattern per line
        for pattern in patterns:
            print(pattern)


if __name__ == "__main__":
    main()
