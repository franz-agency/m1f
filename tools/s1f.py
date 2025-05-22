#!/usr/bin/env python3
"""Main entry point for s1f - Split One File."""

import sys
from s1f.cli import main

# Provide compatibility for tests that import s1f module directly
main = main

if __name__ == "__main__":
    sys.exit(main()) 