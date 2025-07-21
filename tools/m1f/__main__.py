# Copyright 2025 Franz und Franz GmbH
# SPDX-License-Identifier: Apache-2.0

"""Entry point for m1f when run as a module."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Set Windows-specific event loop policy to avoid debug messages
if sys.platform.startswith("win"):
    # This prevents "RuntimeError: Event loop is closed" messages on Windows
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from tools.m1f import main


if __name__ == "__main__":
    sys.exit(main())
