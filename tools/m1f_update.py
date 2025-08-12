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

"""Wrapper for m1f-update command that calls m1f auto-bundle."""

import sys
from m1f.cli import main as m1f_main


def main():
    """Run m1f auto-bundle command."""
    # Insert 'auto-bundle' as the first argument
    sys.argv = [sys.argv[0], "auto-bundle"] + sys.argv[1:]
    return m1f_main()


if __name__ == "__main__":
    main()
