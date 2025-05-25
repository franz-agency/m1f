"""Entry point for m1f when run as a module."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.m1f import main


if __name__ == "__main__":
    sys.exit(main())