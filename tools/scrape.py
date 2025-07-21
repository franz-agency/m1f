#!/usr/bin/env python3
# Copyright 2025 Franz und Franz GmbH
# SPDX-License-Identifier: Apache-2.0

"""Wrapper script for m1f-scrape module."""

import sys
import os

# Add the tools directory to Python path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrape_tool.cli import main

if __name__ == "__main__":
    main()
