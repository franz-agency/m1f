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

"""Test to verify path separators are handled correctly across platforms."""

import os
import sys
from pathlib import Path

import pytest

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.m1f.utils import get_relative_path
from tools.s1f.utils import convert_to_posix_path


class TestPathSeparators:
    """Test path separator handling across platforms."""

    @pytest.mark.unit
    def test_m1f_path_normalization(self, tmp_path):
        """Test that m1f always produces forward slashes."""
        # Use tmp_path for platform-appropriate paths
        base_path = tmp_path / "project"
        base_path.mkdir()

        # Test normal relative path
        file_path = base_path / "src" / "main.py"
        file_path.parent.mkdir(parents=True)
        file_path.touch()

        result = get_relative_path(file_path, base_path)
        assert result == "src/main.py", f"Expected 'src/main.py', got '{result}'"

        # Test nested path
        file_path = base_path / "src" / "components" / "ui" / "button.js"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch()

        result = get_relative_path(file_path, base_path)
        assert (
            result == "src/components/ui/button.js"
        ), f"Expected 'src/components/ui/button.js', got '{result}'"

        # Test path not under base (should return absolute with forward slashes)
        other_path = tmp_path / "other" / "location" / "file.txt"
        other_path.parent.mkdir(parents=True)
        other_path.touch()

        result = get_relative_path(other_path, base_path)
        # Result should always use forward slashes
        assert (
            "/" in result and "\\" not in result
        ), f"Expected forward slashes in '{result}'"

    @pytest.mark.unit
    def test_s1f_path_conversion(self):
        """Test that s1f correctly converts paths."""
        # Test Windows-style paths
        result = convert_to_posix_path("src\\main.py")
        assert result == "src/main.py", f"Expected 'src/main.py', got '{result}'"

        # Test already normalized paths
        result = convert_to_posix_path("src/main.py")
        assert result == "src/main.py", f"Expected 'src/main.py', got '{result}'"

        # Test mixed separators
        result = convert_to_posix_path("src\\components/ui\\button.js")
        assert (
            result == "src/components/ui/button.js"
        ), f"Expected 'src/components/ui/button.js', got '{result}'"

        # Test None input
        result = convert_to_posix_path(None)
        assert result == "", f"Expected empty string, got '{result}'"

    @pytest.mark.unit
    def test_path_object_behavior(self):
        """Test how Path objects handle separators."""
        # Create path with forward slashes
        path_str = "src/components/ui/button.js"
        path_obj = Path(path_str)

        # Verify that as_posix always gives forward slashes
        assert "/" in path_obj.as_posix(), "as_posix() should contain forward slashes"
        assert (
            "\\" not in path_obj.as_posix()
        ), "as_posix() should not contain backslashes"

    @pytest.mark.unit
    @pytest.mark.skipif(os.name != "nt", reason="Windows-specific test")
    def test_windows_paths(self, tmp_path):
        """Test Windows-specific path handling."""
        # Test with actual Windows paths
        base_path = tmp_path / "project"
        base_path.mkdir()

        file_path = base_path / "src" / "main.py"
        file_path.parent.mkdir()
        file_path.touch()

        result = get_relative_path(file_path, base_path)
        assert result == "src/main.py", f"Expected 'src/main.py', got '{result}'"

        # Test that Windows paths are converted to forward slashes in bundles
        assert "/" in result and "\\" not in result

    @pytest.mark.unit
    def test_path_conversion_edge_cases(self):
        """Test edge cases in path conversion."""
        # Test Windows-style paths conversion (works on all platforms)
        result = convert_to_posix_path("C:\\Users\\test\\file.txt")
        assert (
            result == "C:/Users/test/file.txt"
        ), f"Expected 'C:/Users/test/file.txt', got '{result}'"

        # Test UNC paths
        result = convert_to_posix_path("\\\\server\\share\\file.txt")
        assert (
            result == "//server/share/file.txt"
        ), f"Expected '//server/share/file.txt', got '{result}'"

        # Test paths with multiple consecutive separators
        result = convert_to_posix_path("path\\\\to\\\\\\file.txt")
        assert (
            result == "path//to///file.txt"
        ), f"Expected 'path//to///file.txt', got '{result}'"
