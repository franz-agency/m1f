"""Basic functionality tests for s1f."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from ..base_test import BaseS1FTest


class TestS1FBasic(BaseS1FTest):
    """Basic s1f functionality tests."""
    
    @pytest.mark.unit
    @pytest.mark.parametrize("separator_style", ["Standard", "Detailed", "Markdown", "MachineReadable"])
    def test_extract_separator_styles(
        self,
        run_s1f,
        create_combined_file,
        s1f_extracted_dir,
        separator_style
    ):
        """Test extracting files from different separator styles."""
        # Create test files
        test_files = {
            "src/main.py": "#!/usr/bin/env python3\nprint('Hello')",
            "src/utils.py": "def helper():\n    return 42",
            "README.md": "# Project\n\nDescription",
        }
        
        # Create combined file
        combined_file = create_combined_file(test_files, separator_style)
        
        # Run s1f
        exit_code, log_output = run_s1f([
            "--input-file", str(combined_file),
            "--destination-directory", str(s1f_extracted_dir),
            "--force",
            "--verbose",
        ])
        
        assert exit_code == 0, f"s1f failed with exit code {exit_code}"
        
        # Verify files were extracted
        for filepath, expected_content in test_files.items():
            extracted_file = s1f_extracted_dir / filepath
            assert extracted_file.exists(), f"File {filepath} not extracted"
            
            actual_content = extracted_file.read_text()
            assert actual_content == expected_content, \
                f"Content mismatch for {filepath}"
    
    @pytest.mark.unit
    def test_force_overwrite(
        self,
        run_s1f,
        create_combined_file,
        s1f_extracted_dir
    ):
        """Test force overwriting existing files."""
        test_files = {
            "test.txt": "New content",
        }
        
        # Create existing file
        existing_file = s1f_extracted_dir / "test.txt"
        existing_file.parent.mkdir(parents=True, exist_ok=True)
        existing_file.write_text("Old content")
        
        # Create combined file
        combined_file = create_combined_file(test_files)
        
        # Run without force (should fail or skip)
        exit_code, _ = run_s1f([
            "--input-file", str(combined_file),
            "--destination-directory", str(s1f_extracted_dir),
        ])
        
        # Content should remain old
        assert existing_file.read_text() == "Old content"
        
        # Run with force
        exit_code, _ = run_s1f([
            "--input-file", str(combined_file),
            "--destination-directory", str(s1f_extracted_dir),
            "--force",
        ])
        
        assert exit_code == 0
        
        # Content should be updated
        assert existing_file.read_text() == "New content"
    
    @pytest.mark.unit
    def test_timestamp_modes(
        self,
        run_s1f,
        create_combined_file,
        s1f_extracted_dir
    ):
        """Test different timestamp modes."""
        test_files = {
            "file1.txt": "Content 1",
            "file2.txt": "Content 2",
        }
        
        # Create combined file with MachineReadable format (includes timestamps)
        combined_file = create_combined_file(test_files, "MachineReadable")
        
        # Test current timestamp mode
        before = time.time()
        
        exit_code, _ = run_s1f([
            "--input-file", str(combined_file),
            "--destination-directory", str(s1f_extracted_dir),
            "--timestamp-mode", "current",
            "--force",
        ])
        
        after = time.time()
        
        assert exit_code == 0
        
        # Check timestamps are current
        for filename in test_files:
            file_path = s1f_extracted_dir / filename
            mtime = file_path.stat().st_mtime
            assert before <= mtime <= after + 1, \
                f"Timestamp for {filename} not in expected range"
    
    @pytest.mark.unit
    def test_verbose_output(
        self,
        run_s1f,
        create_combined_file,
        s1f_extracted_dir,
        capture_logs
    ):
        """Test verbose logging output."""
        test_files = {
            "test.txt": "Test content",
        }
        
        combined_file = create_combined_file(test_files)
        
        with capture_logs.capture("s1f") as log_capture:
            exit_code, _ = run_s1f([
                "--input-file", str(combined_file),
                "--destination-directory", str(s1f_extracted_dir),
                "--verbose",
                "--force",
            ])
        
        assert exit_code == 0
        
        log_output = log_capture.get_output()
        assert log_output, "No verbose log output captured"
        assert "DEBUG" in log_output or "INFO" in log_output, \
            "Expected debug/info level messages in verbose mode"
    
    @pytest.mark.unit
    def test_help_message(self, s1f_cli_runner):
        """Test help message display."""
        result = s1f_cli_runner(["--help"])
        
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()
        assert "--input-file" in result.stdout
        assert "--destination-directory" in result.stdout
        assert "extract files" in result.stdout.lower()
    
    @pytest.mark.unit
    def test_version_display(self, s1f_cli_runner):
        """Test version display."""
        result = s1f_cli_runner(["--version"])
        
        assert result.returncode == 0
        assert "s1f" in result.stdout.lower()
        # Should contain a version number pattern
        import re
        assert re.search(r"\d+\.\d+", result.stdout), \
            "Version number not found in output"
    
    @pytest.mark.unit
    def test_cli_argument_compatibility(self, s1f_cli_runner, create_combined_file, temp_dir):
        """Test both old and new CLI argument styles."""
        test_files = {"test.txt": "Test content"}
        combined_file = create_combined_file(test_files)
        
        # Test old style arguments
        result_old = s1f_cli_runner([
            "--input-file", str(combined_file),
            "--destination-directory", str(temp_dir / "old_style"),
            "--force",
        ])
        
        assert result_old.returncode == 0
        assert (temp_dir / "old_style" / "test.txt").exists()
        
        # Test new style positional arguments (if supported)
        result_new = s1f_cli_runner([
            str(combined_file),
            str(temp_dir / "new_style"),
            "--force",
        ])
        
        # Check if new style is supported
        if result_new.returncode == 0:
            assert (temp_dir / "new_style" / "test.txt").exists()
    
    @pytest.mark.integration
    def test_extract_from_m1f_output(
        self,
        create_m1f_output,
        run_s1f,
        s1f_extracted_dir
    ):
        """Test extracting from real m1f output files."""
        # Create files to combine
        test_files = {
            "src/app.py": "from utils import helper\nprint(helper())",
            "src/utils.py": "def helper():\n    return 'Hello from utils'",
            "docs/README.md": "# Documentation\n\nProject docs",
        }
        
        # Test each separator style
        for style in ["Standard", "Detailed", "Markdown", "MachineReadable"]:
            # Create m1f output
            m1f_output = create_m1f_output(test_files, style)
            
            # Extract with s1f
            extract_dir = s1f_extracted_dir / style.lower()
            exit_code, _ = run_s1f([
                "--input-file", str(m1f_output),
                "--destination-directory", str(extract_dir),
                "--force",
            ])
            
            assert exit_code == 0, f"Failed to extract {style} format"
            
            # Verify all files extracted correctly
            for filepath, expected_content in test_files.items():
                extracted_file = extract_dir / filepath
                assert extracted_file.exists(), \
                    f"File {filepath} not extracted from {style} format"
                assert extracted_file.read_text() == expected_content, \
                    f"Content mismatch for {filepath} in {style} format" 