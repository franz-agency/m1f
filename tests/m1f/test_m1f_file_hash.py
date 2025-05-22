"""Filename mtime hash functionality tests for m1f."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from ..base_test import BaseM1FTest


class TestM1FFileHash(BaseM1FTest):
    """Tests for filename mtime hash functionality."""
    
    def _get_hash_from_filename(self, filename: str) -> str | None:
        """Extract the hash from a filename like base_<hash>.txt."""
        # Look for pattern like base_12345678.txt
        parts = filename.split('_')
        if len(parts) >= 2:
            # Get the part after the last underscore and before the extension
            last_part = parts[-1]
            if '.' in last_part:
                hash_part = last_part.split('.')[0]
                # Check if it looks like a hash (8 hex characters)
                if len(hash_part) == 8 and all(c in '0123456789abcdef' for c in hash_part):
                    return hash_part
        return None
    
    @pytest.mark.unit
    def test_filename_mtime_hash_basic(
        self,
        run_m1f,
        create_test_file,
        temp_dir
    ):
        """Test basic filename mtime hash functionality."""
        source_dir = temp_dir / "hash_test"
        source_dir.mkdir()
        
        # Create test files
        file1 = create_test_file("hash_test/file1.txt", "Content 1")
        file2 = create_test_file("hash_test/file2.txt", "Content 2")
        
        base_name = "hash_output"
        
        # Run with hash option
        exit_code, _ = run_m1f([
            "--source-directory", str(source_dir),
            "--output-file", str(temp_dir / f"{base_name}.txt"),
            "--add-filename-mtime-hash",
            "--force",
        ])
        
        assert exit_code == 0
        
        # Find the output file with hash
        output_files = list(temp_dir.glob(f"{base_name}_*.txt"))
        assert len(output_files) == 1, "Expected one output file with hash"
        
        # Extract and verify hash
        hash1 = self._get_hash_from_filename(output_files[0].name)
        assert hash1 is not None, "No hash found in filename"
        assert len(hash1) == 8, "Hash should be 8 characters"
    
    @pytest.mark.unit 
    def test_filename_mtime_hash_consistency(
        self,
        run_m1f,
        create_test_file,
        temp_dir
    ):
        """Test that hash remains consistent for unchanged files."""
        source_dir = temp_dir / "hash_consistency"
        source_dir.mkdir()
        
        # Create files with specific mtimes
        file1 = create_test_file("hash_consistency/file1.txt", "Content A")
        file2 = create_test_file("hash_consistency/file2.txt", "Content B")
        
        # Set specific mtimes
        mtime1 = time.time() - 3600  # 1 hour ago
        mtime2 = time.time() - 1800  # 30 minutes ago
        os.utime(file1, (mtime1, mtime1))
        os.utime(file2, (mtime2, mtime2))
        
        # First run
        base_name = "consistency"
        exit_code, _ = run_m1f([
            "--source-directory", str(source_dir),
            "--output-file", str(temp_dir / f"{base_name}_run1.txt"),
            "--add-filename-mtime-hash",
            "--force",
        ])
        
        assert exit_code == 0
        
        # Get first hash
        run1_files = list(temp_dir.glob(f"{base_name}_run1_*.txt"))
        hash1 = self._get_hash_from_filename(run1_files[0].name)
        
        # Second run without changes
        exit_code, _ = run_m1f([
            "--source-directory", str(source_dir),
            "--output-file", str(temp_dir / f"{base_name}_run2.txt"),
            "--add-filename-mtime-hash",
            "--force",
        ])
        
        # Get second hash
        run2_files = list(temp_dir.glob(f"{base_name}_run2_*.txt"))
        hash2 = self._get_hash_from_filename(run2_files[0].name)
        
        assert hash1 == hash2, "Hash should be consistent for unchanged files"
    
    @pytest.mark.unit
    def test_filename_mtime_hash_changes_on_modification(
        self,
        run_m1f,
        create_test_file,
        temp_dir
    ):
        """Test that hash changes when files are modified."""
        source_dir = temp_dir / "hash_changes"
        source_dir.mkdir()
        
        # Create initial files
        file1 = create_test_file("hash_changes/file1.txt", "Initial content")
        
        # First run
        base_name = "changes"
        exit_code, _ = run_m1f([
            "--source-directory", str(source_dir),
            "--output-file", str(temp_dir / f"{base_name}_before.txt"),
            "--add-filename-mtime-hash",
            "--force",
        ])
        
        before_files = list(temp_dir.glob(f"{base_name}_before_*.txt"))
        hash_before = self._get_hash_from_filename(before_files[0].name)
        
        # Modify file
        time.sleep(0.1)  # Ensure mtime changes
        file1.write_text("Modified content")
        
        # Second run
        exit_code, _ = run_m1f([
            "--source-directory", str(source_dir),
            "--output-file", str(temp_dir / f"{base_name}_after.txt"),
            "--add-filename-mtime-hash",
            "--force",
        ])
        
        after_files = list(temp_dir.glob(f"{base_name}_after_*.txt"))
        hash_after = self._get_hash_from_filename(after_files[0].name)
        
        assert hash_before != hash_after, "Hash should change when file is modified"
    
    @pytest.mark.unit
    def test_filename_mtime_hash_with_file_operations(
        self,
        run_m1f,
        create_test_file,
        temp_dir
    ):
        """Test hash changes with various file operations."""
        source_dir = temp_dir / "hash_operations"
        source_dir.mkdir()
        
        # Initial state
        file1 = create_test_file("hash_operations/file1.txt", "File 1")
        file2 = create_test_file("hash_operations/file2.txt", "File 2")
        
        # Get initial hash
        exit_code, _ = run_m1f([
            "--source-directory", str(source_dir),
            "--output-file", str(temp_dir / "ops_initial.txt"),
            "--add-filename-mtime-hash",
            "--force",
        ])
        
        initial_files = list(temp_dir.glob("ops_initial_*.txt"))
        hash_initial = self._get_hash_from_filename(initial_files[0].name)
        
        # Test 1: Add a file
        time.sleep(0.1)
        file3 = create_test_file("hash_operations/file3.txt", "File 3")
        
        exit_code, _ = run_m1f([
            "--source-directory", str(source_dir),
            "--output-file", str(temp_dir / "ops_added.txt"),
            "--add-filename-mtime-hash",
            "--force",
        ])
        
        added_files = list(temp_dir.glob("ops_added_*.txt"))
        hash_added = self._get_hash_from_filename(added_files[0].name)
        assert hash_initial != hash_added, "Hash should change when file is added"
        
        # Test 2: Remove a file
        file3.unlink()
        
        exit_code, _ = run_m1f([
            "--source-directory", str(source_dir),
            "--output-file", str(temp_dir / "ops_removed.txt"),
            "--add-filename-mtime-hash",
            "--force",
        ])
        
        removed_files = list(temp_dir.glob("ops_removed_*.txt"))
        hash_removed = self._get_hash_from_filename(removed_files[0].name)
        assert hash_added != hash_removed, "Hash should change when file is removed"
        
        # Test 3: Rename a file
        file1.rename(source_dir / "renamed.txt")
        
        exit_code, _ = run_m1f([
            "--source-directory", str(source_dir),
            "--output-file", str(temp_dir / "ops_renamed.txt"),
            "--add-filename-mtime-hash",
            "--force",
        ])
        
        renamed_files = list(temp_dir.glob("ops_renamed_*.txt"))
        hash_renamed = self._get_hash_from_filename(renamed_files[0].name)
        assert hash_removed != hash_renamed, "Hash should change when file is renamed"
    
    @pytest.mark.unit
    def test_filename_mtime_hash_with_timestamp(
        self,
        run_m1f,
        create_test_file,
        temp_dir
    ):
        """Test combining hash with timestamp option."""
        source_dir = temp_dir / "hash_timestamp"
        source_dir.mkdir()
        
        create_test_file("hash_timestamp/test.txt", "Test content")
        
        base_name = "combined"
        
        # Run with both hash and timestamp
        exit_code, _ = run_m1f([
            "--source-directory", str(source_dir),
            "--output-file", str(temp_dir / f"{base_name}.txt"),
            "--add-filename-mtime-hash",
            "--add-timestamp",
            "--force",
        ])
        
        assert exit_code == 0
        
        # Find output file
        output_files = list(temp_dir.glob(f"{base_name}_*.txt"))
        assert len(output_files) == 1, "Expected one output file"
        
        filename = output_files[0].name
        
        # Check format: base_YYYYMMDD_HHMMSS_hash.txt
        import re
        pattern = r"^combined_\d{8}_\d{6}_[0-9a-f]{8}\.txt$"
        assert re.match(pattern, filename), \
            f"Filename '{filename}' doesn't match expected pattern"
    
    @pytest.mark.unit
    def test_filename_mtime_hash_empty_directory(
        self,
        run_m1f,
        temp_dir
    ):
        """Test hash behavior with empty directory."""
        source_dir = temp_dir / "empty_hash"
        source_dir.mkdir()
        
        # Run on empty directory
        exit_code, _ = run_m1f([
            "--source-directory", str(source_dir),
            "--output-file", str(temp_dir / "empty.txt"),
            "--add-filename-mtime-hash",
            "--force",
        ])
        
        assert exit_code == 0
        
        # Should still create output with hash
        output_files = list(temp_dir.glob("empty_*.txt"))
        assert len(output_files) == 1, "Expected output file even for empty directory"
        
        hash_empty = self._get_hash_from_filename(output_files[0].name)
        assert hash_empty is not None, "Should generate hash even for empty directory"
    
    @pytest.mark.unit
    def test_filename_mtime_hash_error_handling(
        self,
        run_m1f,
        create_test_file,
        temp_dir,
        monkeypatch
    ):
        """Test hash generation with mtime errors."""
        source_dir = temp_dir / "hash_errors"
        source_dir.mkdir()
        
        file1 = create_test_file("hash_errors/file1.txt", "Content")
        file2 = create_test_file("hash_errors/file2.txt", "Content")
        
        # Mock os.path.getmtime to fail for one file
        original_getmtime = os.path.getmtime
        
        def faulty_getmtime(path):
            if str(path).endswith("file2.txt"):
                raise OSError("Cannot get mtime")
            return original_getmtime(path)
        
        monkeypatch.setattr("os.path.getmtime", faulty_getmtime)
        
        # Should still generate output (with partial hash)
        exit_code, _ = run_m1f([
            "--source-directory", str(source_dir),
            "--output-file", str(temp_dir / "error.txt"),
            "--add-filename-mtime-hash",
            "--force",
        ])
        
        # Should complete (possibly with warnings)
        assert exit_code == 0
        
        # Should still generate output file with hash
        output_files = list(temp_dir.glob("error_*.txt"))
        assert len(output_files) == 1, "Should create output despite mtime errors" 