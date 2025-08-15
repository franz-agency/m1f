#!/usr/bin/env python3
# Copyright 2025 Franz und Franz GmbH
# SPDX-License-Identifier: Apache-2.0

"""Wrapper script for m1f-scrape module."""

import sys

# Try absolute imports first (for module execution), fall back to relative
try:
    from tools.scrape_tool.cli import main
except ImportError:
    # Fallback for direct script execution
    from scrape_tool.cli import main

if __name__ == "__main__":
    sys.exit(main())
