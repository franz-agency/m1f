#!/usr/bin/env python3
# Copyright 2025 Franz und Franz GmbH
# SPDX-License-Identifier: Apache-2.0

"""
HTML to Markdown converter - wrapper script.
"""

import sys
import os
from pathlib import Path

if __name__ == "__main__":
    # Add the parent directory to sys.path for proper imports
    script_dir = Path(__file__).parent
    parent_dir = script_dir.parent

    # Try different import strategies based on execution context
    try:
        # First try as if we're in the m1f package
        from html2md_tool.cli import main
    except ImportError:
        try:
            # Try adding parent to path and importing
            if str(parent_dir) not in sys.path:
                sys.path.insert(0, str(parent_dir))
            from html2md_tool.cli import main
        except ImportError:
            # Fallback for direct script execution
            if str(script_dir) not in sys.path:
                sys.path.insert(0, str(script_dir))
            from html2md_tool.cli import main

    main()
