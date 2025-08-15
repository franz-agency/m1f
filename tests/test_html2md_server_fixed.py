#!/usr/bin/env python3
# Copyright 2025 Franz und Franz GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Comprehensive test suite for mf1-html2md converter using the test server.
Tests various HTML structures, edge cases, and conversion options.
"""

import os
import sys
import pytest
import pytest_asyncio
import asyncio
import aiohttp
import subprocess
import time
import tempfile
import shutil
import socket
from pathlib import Path

# Optional import for enhanced process management
try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    psutil = None
    HAS_PSUTIL = False
from pathlib import Path
from typing import Dict, List, Optional
import json
import yaml
import platform
import signal
from contextlib import contextmanager

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.html2md_tool import HTML2MDConverter, ConversionOptions
