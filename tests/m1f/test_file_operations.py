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
Tests for the file_operations module that provides safe file operations
with permission error handling.
"""

import os
import tempfile
import stat
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
import sys

# Add the tools directory to the path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from tools.m1f.file_operations import (
    safe_exists,
    safe_is_dir,
    safe_is_file,
    safe_stat,
    safe_open,
    safe_mkdir,
    safe_walk,
    safe_read_text,
    safe_write_text,
    safe_iterdir,
    safe_glob,
    safe_is_symlink,
    safe_resolve,
    handle_permission_errors,
)


class TestSafeFileOperations:
    """Test suite for safe file operations."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for testing."""
        logger = Mock()
        logger.warning = Mock()
        logger.debug = Mock()
        return logger

    @pytest.fixture
    def permission_denied_file(self, temp_dir):
        """Create a file with no permissions."""
        file_path = temp_dir / "no_access.txt"
        file_path.write_text("test content")
        # Remove all permissions
        os.chmod(file_path, 0o000)
        yield file_path
        # Restore permissions for cleanup
        try:
            os.chmod(file_path, 0o644)
        except:
            pass

    @pytest.fixture
    def permission_denied_dir(self, temp_dir):
        """Create a directory with no permissions."""
        dir_path = temp_dir / "no_access_dir"
        dir_path.mkdir()
        (dir_path / "file.txt").write_text("content")
        # Remove all permissions
        os.chmod(dir_path, 0o000)
        yield dir_path
        # Restore permissions for cleanup
        try:
            os.chmod(dir_path, 0o755)
        except:
            pass

    def test_safe_exists_with_accessible_path(self, temp_dir):
        """Test safe_exists with an accessible path."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")

        assert safe_exists(test_file) is True
        assert safe_exists(temp_dir) is True
        assert safe_exists(temp_dir / "nonexistent.txt") is False

    def test_safe_exists_with_permission_error(self, mock_logger):
        """Test safe_exists with permission error."""
        with patch("pathlib.Path.exists", side_effect=PermissionError("Access denied")):
            result = safe_exists("/some/path", logger=mock_logger)
            assert result is False
            mock_logger.warning.assert_called_once()
            assert "Permission denied" in str(mock_logger.warning.call_args)

    def test_safe_is_dir_with_accessible_path(self, temp_dir):
        """Test safe_is_dir with accessible paths."""
        test_dir = temp_dir / "subdir"
        test_dir.mkdir()
        test_file = temp_dir / "file.txt"
        test_file.write_text("content")

        assert safe_is_dir(test_dir) is True
        assert safe_is_dir(test_file) is False
        assert safe_is_dir(temp_dir / "nonexistent") is False

    def test_safe_is_dir_with_permission_error(self, mock_logger):
        """Test safe_is_dir with permission error."""
        with patch("pathlib.Path.is_dir", side_effect=PermissionError("Access denied")):
            result = safe_is_dir("/some/path", logger=mock_logger)
            assert result is False
            mock_logger.warning.assert_called_once()

    def test_safe_is_file_with_accessible_path(self, temp_dir):
        """Test safe_is_file with accessible paths."""
        test_file = temp_dir / "file.txt"
        test_file.write_text("content")
        test_dir = temp_dir / "subdir"
        test_dir.mkdir()

        assert safe_is_file(test_file) is True
        assert safe_is_file(test_dir) is False
        assert safe_is_file(temp_dir / "nonexistent") is False

    def test_safe_is_file_with_permission_error(self, mock_logger):
        """Test safe_is_file with permission error."""
        with patch(
            "pathlib.Path.is_file", side_effect=PermissionError("Access denied")
        ):
            result = safe_is_file("/some/path", logger=mock_logger)
            assert result is False
            mock_logger.warning.assert_called_once()

    def test_safe_stat_with_accessible_path(self, temp_dir):
        """Test safe_stat with accessible path."""
        test_file = temp_dir / "file.txt"
        test_file.write_text("content")

        stat_result = safe_stat(test_file)
        assert stat_result is not None
        assert stat_result.st_size == 7  # "content" is 7 bytes

    def test_safe_stat_with_permission_error(self, mock_logger):
        """Test safe_stat with permission error."""
        with patch("pathlib.Path.stat", side_effect=PermissionError("Access denied")):
            result = safe_stat("/some/path", logger=mock_logger)
            assert result is None
            mock_logger.warning.assert_called_once()

    def test_safe_open_for_reading(self, temp_dir, mock_logger):
        """Test safe_open context manager for reading."""
        test_file = temp_dir / "file.txt"
        test_file.write_text("test content")

        with safe_open(test_file, "r", logger=mock_logger) as f:
            assert f is not None
            content = f.read()
            assert content == "test content"

    def test_safe_open_for_writing(self, temp_dir, mock_logger):
        """Test safe_open context manager for writing."""
        test_file = temp_dir / "output.txt"

        with safe_open(test_file, "w", logger=mock_logger) as f:
            assert f is not None
            f.write("new content")

        assert test_file.read_text() == "new content"

    def test_safe_open_with_permission_error(self, mock_logger):
        """Test safe_open with permission error."""
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            with safe_open("/some/path", "r", logger=mock_logger) as f:
                assert f is None
            mock_logger.warning.assert_called_once()

    def test_safe_mkdir_creates_directory(self, temp_dir, mock_logger):
        """Test safe_mkdir creates directory successfully."""
        new_dir = temp_dir / "new_dir"
        result = safe_mkdir(new_dir, logger=mock_logger)

        assert result is True
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_safe_mkdir_with_parents(self, temp_dir, mock_logger):
        """Test safe_mkdir creates parent directories."""
        nested_dir = temp_dir / "level1" / "level2" / "level3"
        result = safe_mkdir(nested_dir, logger=mock_logger, parents=True)

        assert result is True
        assert nested_dir.exists()
        assert nested_dir.is_dir()

    def test_safe_mkdir_with_permission_error(self, mock_logger):
        """Test safe_mkdir with permission error."""
        with patch("pathlib.Path.mkdir", side_effect=PermissionError("Access denied")):
            result = safe_mkdir("/some/path", logger=mock_logger)
            assert result is False
            mock_logger.warning.assert_called_once()

    def test_safe_walk_traverses_directory(self, temp_dir, mock_logger):
        """Test safe_walk traverses directory tree."""
        # Create directory structure
        (temp_dir / "dir1").mkdir()
        (temp_dir / "dir1" / "file1.txt").write_text("content1")
        (temp_dir / "dir2").mkdir()
        (temp_dir / "dir2" / "file2.txt").write_text("content2")
        (temp_dir / "file3.txt").write_text("content3")

        walked_paths = []
        for root, dirs, files in safe_walk(temp_dir, logger=mock_logger):
            walked_paths.append((root, sorted(dirs), sorted(files)))

        assert len(walked_paths) > 0
        # Check root directory
        root_entry = next((p for p in walked_paths if Path(p[0]) == temp_dir), None)
        assert root_entry is not None
        assert "dir1" in root_entry[1]
        assert "dir2" in root_entry[1]
        assert "file3.txt" in root_entry[2]

    def test_safe_walk_skips_inaccessible(self, temp_dir, mock_logger):
        """Test safe_walk skips inaccessible directories."""
        # Create accessible directory
        (temp_dir / "accessible").mkdir()
        (temp_dir / "accessible" / "file.txt").write_text("content")

        # Mock permission error for specific path
        original_exists = safe_exists

        def mock_exists(path, logger=None):
            if "inaccessible" in str(path):
                return False
            return original_exists(path, logger)

        with patch("tools.m1f.file_operations.safe_exists", side_effect=mock_exists):
            walked_paths = list(safe_walk(temp_dir, logger=mock_logger))
            assert len(walked_paths) > 0

    def test_safe_read_text_reads_file(self, temp_dir, mock_logger):
        """Test safe_read_text reads file content."""
        test_file = temp_dir / "file.txt"
        test_file.write_text("test content", encoding="utf-8")

        content = safe_read_text(test_file, logger=mock_logger)
        assert content == "test content"

    def test_safe_read_text_with_permission_error(self, mock_logger):
        """Test safe_read_text with permission error."""
        with patch(
            "pathlib.Path.read_text", side_effect=PermissionError("Access denied")
        ):
            result = safe_read_text("/some/path", logger=mock_logger)
            assert result is None
            mock_logger.warning.assert_called_once()

    def test_safe_write_text_writes_file(self, temp_dir, mock_logger):
        """Test safe_write_text writes file content."""
        test_file = temp_dir / "output.txt"

        result = safe_write_text(test_file, "new content", logger=mock_logger)
        assert result is True
        assert test_file.read_text() == "new content"

    def test_safe_write_text_with_permission_error(self, mock_logger):
        """Test safe_write_text with permission error."""
        with patch(
            "pathlib.Path.write_text", side_effect=PermissionError("Access denied")
        ):
            result = safe_write_text("/some/path", "content", logger=mock_logger)
            assert result is False
            mock_logger.warning.assert_called_once()

    def test_safe_iterdir_iterates_directory(self, temp_dir, mock_logger):
        """Test safe_iterdir iterates over directory contents."""
        # Create files and directories
        (temp_dir / "file1.txt").write_text("content1")
        (temp_dir / "file2.txt").write_text("content2")
        (temp_dir / "subdir").mkdir()

        items = list(safe_iterdir(temp_dir, logger=mock_logger))
        item_names = [item.name for item in items]

        assert "file1.txt" in item_names
        assert "file2.txt" in item_names
        assert "subdir" in item_names

    def test_safe_iterdir_with_permission_error(self, mock_logger):
        """Test safe_iterdir with permission error."""
        with patch(
            "pathlib.Path.iterdir", side_effect=PermissionError("Access denied")
        ):
            items = list(safe_iterdir("/some/path", logger=mock_logger))
            assert items == []
            mock_logger.warning.assert_called_once()

    def test_safe_glob_matches_patterns(self, temp_dir, mock_logger):
        """Test safe_glob matches file patterns."""
        # Create test files
        (temp_dir / "test1.txt").write_text("content")
        (temp_dir / "test2.txt").write_text("content")
        (temp_dir / "other.md").write_text("content")

        matches = list(safe_glob("*.txt", root=temp_dir, logger=mock_logger))
        match_names = [m.name for m in matches]

        assert "test1.txt" in match_names
        assert "test2.txt" in match_names
        assert "other.md" not in match_names

    def test_safe_glob_with_permission_error(self, mock_logger):
        """Test safe_glob with permission error."""
        with patch("pathlib.Path.glob", side_effect=PermissionError("Access denied")):
            matches = list(safe_glob("*.txt", root="/some/path", logger=mock_logger))
            assert matches == []
            mock_logger.warning.assert_called_once()

    def test_safe_is_symlink(self, temp_dir, mock_logger):
        """Test safe_is_symlink checks for symbolic links."""
        regular_file = temp_dir / "regular.txt"
        regular_file.write_text("content")

        symlink_file = temp_dir / "link.txt"
        try:
            symlink_file.symlink_to(regular_file)
            assert safe_is_symlink(symlink_file, logger=mock_logger) is True
        except OSError:
            # Skip test on systems that don't support symlinks
            pytest.skip("Symlinks not supported on this system")

        assert safe_is_symlink(regular_file, logger=mock_logger) is False

    def test_safe_is_symlink_with_permission_error(self, mock_logger):
        """Test safe_is_symlink with permission error."""
        with patch(
            "pathlib.Path.is_symlink", side_effect=PermissionError("Access denied")
        ):
            result = safe_is_symlink("/some/path", logger=mock_logger)
            assert result is False
            mock_logger.warning.assert_called_once()

    def test_safe_resolve(self, temp_dir, mock_logger):
        """Test safe_resolve resolves paths."""
        test_file = temp_dir / "file.txt"
        test_file.write_text("content")

        resolved = safe_resolve(test_file, logger=mock_logger)
        assert resolved is not None
        assert resolved.is_absolute()

    def test_safe_resolve_with_permission_error(self, mock_logger):
        """Test safe_resolve with permission error."""
        with patch(
            "pathlib.Path.resolve", side_effect=PermissionError("Access denied")
        ):
            result = safe_resolve("/some/path", logger=mock_logger)
            assert result is None
            mock_logger.warning.assert_called_once()

    def test_handle_permission_errors_decorator(self, mock_logger):
        """Test handle_permission_errors decorator."""

        @handle_permission_errors(
            fallback_return=False, log_message="Failed to access {path}"
        )
        def test_function(path, logger=None):
            if "fail" in str(path):
                raise PermissionError("Access denied")
            return True

        # Test successful case
        assert test_function("/good/path", logger=mock_logger) is True

        # Test permission error case
        assert test_function("/fail/path", logger=mock_logger) is False
        mock_logger.warning.assert_called_once()

    def test_handle_permission_errors_with_os_error(self, mock_logger):
        """Test decorator handles OS errors with errno 13."""

        @handle_permission_errors(fallback_return=None)
        def test_function(path, logger=None):
            e = OSError("Permission denied")
            e.errno = 13  # EACCES
            raise e

        result = test_function("/some/path", logger=mock_logger)
        assert result is None
        mock_logger.warning.assert_called_once()

    def test_os_error_errno_1_handling(self, mock_logger):
        """Test handling of OS error with errno 1 (EPERM)."""
        with patch("pathlib.Path.exists") as mock_exists:
            e = OSError("Operation not permitted")
            e.errno = 1  # EPERM
            mock_exists.side_effect = e

            result = safe_exists("/some/path", logger=mock_logger)
            assert result is False
            mock_logger.warning.assert_called_once()

    def test_os_error_other_errno_reraises(self):
        """Test that OS errors with other errno values are re-raised."""
        with patch("pathlib.Path.exists") as mock_exists:
            e = OSError("Some other error")
            e.errno = 2  # ENOENT (not a permission error)
            mock_exists.side_effect = e

            with pytest.raises(OSError) as exc_info:
                safe_exists("/some/path")
            assert exc_info.value.errno == 2


class TestIntegrationWithCore:
    """Test integration of safe operations with core m1f functionality."""

    def test_core_uses_safe_operations(self):
        """Verify that core.py imports and uses safe operations."""
        from tools.m1f.core import FileCombiner
        from tools.m1f.config import Config

        # Check that safe operations are imported
        import tools.m1f.core as core_module

        assert hasattr(core_module, "safe_exists")
        assert hasattr(core_module, "safe_mkdir")
        assert hasattr(core_module, "safe_open")

    def test_file_processor_uses_safe_operations(self):
        """Verify that file_processor.py imports and uses safe operations."""
        from tools.m1f.file_processor import FileProcessor

        # Check that safe operations are imported
        import tools.m1f.file_processor as fp_module

        assert hasattr(fp_module, "safe_exists")
        assert hasattr(fp_module, "safe_is_dir")
        assert hasattr(fp_module, "safe_is_file")
        assert hasattr(fp_module, "safe_read_text")
        assert hasattr(fp_module, "safe_walk")


class TestRealPermissionScenarios:
    """Test with real permission-denied scenarios (requires Unix-like system)."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for testing."""
        logger = Mock()
        logger.warning = Mock()
        logger.debug = Mock()
        return logger

    @pytest.mark.skipif(
        sys.platform.startswith("win"), reason="Unix-specific permissions"
    )
    def test_real_permission_denied_file(self, temp_dir, mock_logger):
        """Test with a real file that has no read permissions."""
        test_file = temp_dir / "no_read.txt"
        test_file.write_text("secret")
        os.chmod(test_file, 0o000)

        try:
            # These should return False/None instead of raising exceptions
            assert (
                safe_exists(test_file, mock_logger) is True
            )  # File exists even if not readable
            assert safe_read_text(test_file, mock_logger) is None
            # Note: stat() may still work even with chmod 000 because the owner can read metadata
        finally:
            # Restore permissions for cleanup
            os.chmod(test_file, 0o644)

    @pytest.mark.skipif(
        sys.platform.startswith("win"), reason="Unix-specific permissions"
    )
    def test_real_permission_denied_directory(self, temp_dir, mock_logger):
        """Test with a real directory that has no permissions."""
        test_dir = temp_dir / "no_access"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("content")
        os.chmod(test_dir, 0o000)

        try:
            # Directory exists but we can't access its contents
            assert safe_exists(test_dir, mock_logger) is True
            assert safe_is_dir(test_dir, mock_logger) is True

            # But we can't iterate or read files inside
            items = list(safe_iterdir(test_dir, mock_logger))
            assert items == []  # Should be empty due to permission error

            # Can't read files inside
            assert safe_read_text(test_dir / "file.txt", mock_logger) is None
        finally:
            # Restore permissions for cleanup
            os.chmod(test_dir, 0o755)

    @pytest.mark.skipif(
        sys.platform.startswith("win"), reason="Unix-specific permissions"
    )
    def test_safe_walk_with_mixed_permissions(self, temp_dir, mock_logger):
        """Test safe_walk with some accessible and some inaccessible directories."""
        # Create directory structure
        (temp_dir / "accessible").mkdir()
        (temp_dir / "accessible" / "file1.txt").write_text("content1")

        (temp_dir / "restricted").mkdir()
        (temp_dir / "restricted" / "file2.txt").write_text("content2")

        (temp_dir / "another").mkdir()
        (temp_dir / "another" / "file3.txt").write_text("content3")

        # Remove permissions from one directory
        os.chmod(temp_dir / "restricted", 0o000)

        try:
            # Walk should skip the restricted directory
            walked_dirs = []
            walked_files = []
            for root, dirs, files in safe_walk(temp_dir, logger=mock_logger):
                walked_dirs.extend(dirs)
                walked_files.extend(files)

            # Should have walked accessible directories
            assert "accessible" in walked_dirs or "another" in walked_dirs
            # Files in accessible directories should be found
            assert any("file1.txt" in f or "file3.txt" in f for f in walked_files)
        finally:
            # Restore permissions
            os.chmod(temp_dir / "restricted", 0o755)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
