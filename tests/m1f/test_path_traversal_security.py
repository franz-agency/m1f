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
Test path traversal security fixes.
"""

import pytest
from pathlib import Path
import argparse
import tempfile
import os

from tools.m1f.config import Config
from tools.m1f.utils import validate_path_traversal


class TestPathTraversalSecurity:
    """Test path traversal security in config handling."""

    def _create_test_args(self, **overrides):
        """Create test argparse.Namespace with all required attributes."""
        defaults = {
            "source_directory": [],
            "input_file": None,
            "output_file": "output.txt",
            "input_include_files": None,
            "preset_files": None,
            "add_timestamp": False,
            "force": False,
            "verbose": False,
            "separator_style": "Standard",
            "line_ending": "lf",
            "exclude_paths": [],
            "excludes": [],
            "exclude_paths_file": None,
            "include_paths_file": None,
            "include_extensions": [],
            "exclude_extensions": [],
            "include_dot_paths": False,
            "include_binary_files": False,
            "max_file_size": None,
            "minimal_output": False,
            "skip_output_file": False,
            "filename_mtime_hash": False,
            "create_archive": False,
            "disable_presets": False,
            "preset_group": None,
            "disable_security_check": False,
            "quiet": False,
        }
        # Handle source_directory as a list
        if 'source_directory' in overrides:
            overrides['source_directory'] = [overrides['source_directory']]
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def test_validate_path_traversal_valid_path(self):
        """Test that valid paths within base directory are allowed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            # Valid path within base directory
            valid_path = base_path / "subdir" / "file.txt"

            result = validate_path_traversal(valid_path, base_path)
            assert result == valid_path.resolve()

    def test_validate_path_traversal_outside_base(self):
        """Test that paths outside base directory are rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            # Try to traverse outside
            malicious_path = base_path / ".." / ".." / "etc" / "passwd"

            with pytest.raises(ValueError) as exc_info:
                validate_path_traversal(malicious_path, base_path)

            assert "Path traversal detected" in str(exc_info.value)

    def test_config_blocks_traversal_source_dir(self):
        """Test that Config blocks path traversal in source directory."""
        # Create mock args with path traversal attempt
        args = self._create_test_args(source_directory="../../../etc")

        # This should raise ValueError for path traversal
        with pytest.raises(ValueError) as exc_info:
            Config.from_args(args)

        assert "Path traversal detected" in str(exc_info.value)

    def test_config_builder_blocks_traversal_input_file(self):
        """Test that Config blocks path traversal in input file."""
        args = self._create_test_args(input_file="../../sensitive/data.txt")

        with pytest.raises(ValueError) as exc_info:
            Config.from_args(args)

        assert "Path traversal detected" in str(exc_info.value)

    def test_config_allows_output_file_outside_cwd(self):
        """Test that Config allows output files outside current directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Output paths should be allowed outside the base directory
            args = self._create_test_args(
                source_directory=".", output_file=f"{tmpdir}/output.txt"
            )

            # This should NOT raise an error
            config = Config.from_args(args)
            assert str(config.output.output_file) == f"{tmpdir}/output.txt"

    def test_config_builder_blocks_traversal_include_files(self):
        """Test that Config blocks path traversal in include files."""
        args = self._create_test_args(
            input_include_files=["../../../etc/shadow", "../../private/keys.txt"]
        )

        with pytest.raises(ValueError) as exc_info:
            Config.from_args(args)

        assert "Path traversal detected" in str(exc_info.value)

    def test_config_builder_blocks_traversal_preset_files(self):
        """Test that Config blocks path traversal in preset files."""
        args = self._create_test_args(
            preset_files=["../../../../home/user/.ssh/id_rsa"]
        )

        with pytest.raises(ValueError) as exc_info:
            Config.from_args(args)

        assert "Path traversal detected" in str(exc_info.value)

    def test_symbolic_link_traversal_blocked(self):
        """Test that symbolic links cannot be used for path traversal."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Create a symbolic link that points outside
            link_path = base_path / "evil_link"
            target_path = Path("/etc/passwd")

            # Only create symlink if we can (might fail on some systems)
            try:
                link_path.symlink_to(target_path)

                # The resolved path should be blocked
                with pytest.raises(ValueError) as exc_info:
                    validate_path_traversal(link_path, base_path)

                assert "Path traversal detected" in str(exc_info.value)
            except OSError:
                # Skip test if we can't create symlinks
                pytest.skip("Cannot create symbolic links on this system")
