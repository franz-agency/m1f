#!/usr/bin/env python3
# Copyright 2025 Franz und Franz GmbH
# SPDX-License-Identifier: Apache-2.0

"""Main entry point for s1f - Split One File."""

import sys

# Try absolute imports first (for module execution), fall back to relative
try:
    from s1f.cli import main
except ImportError:
    # Fallback for direct script execution
    from s1f.cli import main

if __name__ == "__main__":
    sys.exit(main())
