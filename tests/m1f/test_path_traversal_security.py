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
            "allow_external": False,
        }
        # Handle source_directory as a list
        if "source_directory" in overrides:
            overrides["source_directory"] = [overrides["source_directory"]]
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
            output_file_path = Path(tmpdir) / "output.txt"
            args = self._create_test_args(
                source_directory=".", output_file=str(output_file_path)
            )

            # This should NOT raise an error
            config = Config.from_args(args)
            # Compare resolved paths for platform independence
            assert config.output.output_file.resolve() == output_file_path.resolve()

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

    def test_allow_external_flag_enables_external_access(self):
        """Test that --allow-external flag allows accessing external directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file outside the working directory  
            external_path = Path(tmpdir) / "external_project"
            external_path.mkdir()
            (external_path / "test.txt").write_text("test content")
            
            # With allow_external=True, this should work
            args = self._create_test_args(
                source_directory=str(external_path),
                allow_external=True
            )
            
            # This should NOT raise an error
            config = Config.from_args(args)
            assert config.source_directories[0].resolve() == external_path.resolve()

    def test_allow_external_flag_still_blocks_malicious_patterns(self):
        """Test that --allow-external still blocks excessive path traversal patterns."""
        # Even with allow_external=True, excessive traversal should be blocked
        malicious_path = "../../../../../../../etc/passwd"
        args = self._create_test_args(
            source_directory=malicious_path,
            allow_external=True
        )
        
        with pytest.raises(ValueError) as exc_info:
            Config.from_args(args)
        
        assert "Path traversal detected" in str(exc_info.value)
        assert "suspicious '..' patterns" in str(exc_info.value)

    def test_allow_external_flag_affects_all_input_paths(self):
        """Test that --allow-external affects source dirs, input files, and include files."""
        # Use paths that are not in temp directories to avoid default temp exceptions
        home_dir = Path.home()
        external_path = home_dir / "test_external_m1f"  # This should not exist and be outside cwd
        
        args = self._create_test_args(
            source_directory=str(external_path),
            input_file=str(external_path / "input.txt"),
            input_include_files=[str(external_path / "include.txt")],
            allow_external=True
        )
        
        # Should work with allow_external=True (even if paths don't exist, validation should pass)
        config = Config.from_args(args)
        assert config.source_directories[0].resolve() == external_path.resolve()
        assert config.input_file.resolve() == (external_path / "input.txt").resolve()
        assert config.input_include_files[0].resolve() == (external_path / "include.txt").resolve()

    def test_allow_external_false_by_default(self):
        """Test that allow_external is False by default (secure by default)."""
        # Use /opt/external_project which should not exist and be outside cwd,
        # and is not in the temp directory exceptions
        external_path = Path("/opt/external_project_m1f")
        
        # Without allow_external flag, external access should be blocked
        args = self._create_test_args(source_directory=str(external_path))
        
        # This should raise an error due to path traversal protection
        with pytest.raises(ValueError) as exc_info:
            Config.from_args(args)
        
        assert "Path traversal detected" in str(exc_info.value)

    def test_validate_path_traversal_allow_external_parameter(self):
        """Test the allow_external parameter in validate_path_traversal function directly."""
        # Use /opt/external which should not be in any exception lists
        base_path = Path.cwd()
        external_path = Path("/opt/external_validation")
        
        # Without allow_external, should fail
        with pytest.raises(ValueError):
            validate_path_traversal(external_path, base_path, allow_external=False)
        
        # With allow_external, should succeed
        result = validate_path_traversal(external_path, base_path, allow_external=True)
        assert result == external_path.resolve()
