#!/usr/bin/env python3
# Copyright 2025 Franz und Franz GmbH
# SPDX-License-Identifier: Apache-2.0

"""
HTML to Markdown converter - wrapper script.
"""

if __name__ == "__main__":
    # Try absolute imports first (for module execution), fall back to relative
    try:
        from tools.html2md_tool.cli import main
    except ImportError:
        # Fallback for direct script execution
        from html2md_tool.cli import main

    main()
