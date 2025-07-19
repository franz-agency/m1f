# Copyright 2025 Franz und Franz GmbH
# SPDX-License-Identifier: Apache-2.0

"""
Single source of truth for m1f version information.

This file is the only place where the version number should be updated.
All other files should import from here.
"""

__version__ = "3.5.0"
__version_info__ = tuple(int(x) for x in __version__.split(".")[:3])
