"""Allow the s1f package to be run as a module."""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main()) 