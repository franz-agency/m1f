"""Basic functionality tests for m1f."""

from __future__ import annotations

from pathlib import Path

import pytest

from ..base_test import BaseM1FTest


class TestM1FBasic(BaseM1FTest):
    """Basic m1f functionality tests."""
    
    @pytest.mark.unit
    def test_basic_execution(
        self, 
        run_m1f, 
        m1f_source_dir, 
        m1f_output_dir,
        temp_dir
    ):
        """Test basic execution of m1f."""
        output_file = temp_dir / "basic_output.txt"
        
        # Run m1f
        exit_code, log_output = run_m1f([
            "--source-directory", str(m1f_source_dir),
            "--output-file", str(output_file),
            "--force",
        ])
        
        # Verify success
        assert exit_code == 0, f"m1f failed with exit code {exit_code}"
        
        # Verify output files
        assert output_file.exists(), "Output file was not created"
        assert output_file.stat().st_size > 0, "Output file is empty"
        
        # Check accompanying files
        log_file = output_file.with_suffix('.log')
        filelist = output_file.parent / f"{output_file.stem}_filelist.txt"
        dirlist = output_file.parent / f"{output_file.stem}_dirlist.txt"
        
        assert log_file.exists(), "Log file not created"
        assert filelist.exists(), "Filelist not created" 
        assert dirlist.exists(), "Dirlist not created"
        
        # Verify excluded directories are not in output
        self.assert_file_not_contains(output_file, ["node_modules", ".git"])
    
    @pytest.mark.unit
    def test_include_dot_paths(
        self,
        run_m1f,
        m1f_source_dir,
        temp_dir
    ):
        """Test inclusion of dot files and directories."""
        output_file = temp_dir / "dot_paths_included.txt"
        
        # Run with dot files included
        exit_code, _ = run_m1f([
            "--source-directory", str(m1f_source_dir),
            "--output-file", str(output_file),
            "--include-dot-paths",
            "--force",
        ])
        
        assert exit_code == 0
        
        # Verify dot files are included
        self.assert_file_contains(
            output_file, 
            [".hidden", "SECRET_KEY=test_secret_key_12345"]
        )
    
    @pytest.mark.unit
    def test_exclude_paths_file(
        self,
        run_m1f,
        m1f_source_dir,
        exclude_paths_file,
        temp_dir
    ):
        """Test excluding paths from a file."""
        output_file = temp_dir / "excluded_paths.txt"
        
        # Run with exclude paths file
        exit_code, _ = run_m1f([
            "--source-directory", str(m1f_source_dir),
            "--output-file", str(output_file),
            "--exclude-paths-file", str(exclude_paths_file),
            "--force",
        ])
        
        assert exit_code == 0
        
        # Verify excluded paths are not in the output
        self.assert_file_not_contains(
            output_file,
            ["FILE: index.php", "FILE: png.png"]
        )
    
    @pytest.mark.unit
    def test_separator_styles(
        self,
        run_m1f,
        m1f_source_dir,
        temp_dir
    ):
        """Test different separator styles."""
        test_cases = [
            ("Standard", "FILE:"),
            ("Detailed", "==== FILE:"),
            ("Markdown", "```"),
            ("MachineReadable", "PYMK1F_BEGIN_FILE_METADATA_BLOCK"),
        ]
        
        for style, expected_marker in test_cases:
            output_file = temp_dir / f"separator_{style.lower()}.txt"
            
            exit_code, _ = run_m1f([
                "--source-directory", str(m1f_source_dir),
                "--output-file", str(output_file),
                "--separator-style", style,
                "--force",
            ])
            
            assert exit_code == 0, f"Failed with separator style {style}"
            
            # Verify the correct separator style is used
            assert self.verify_m1f_output(
                output_file, 
                expected_separator_style=style
            )
    
    @pytest.mark.unit
    def test_timestamp_in_filename(
        self,
        run_m1f,
        create_test_file,
        temp_dir
    ):
        """Test adding timestamp to output filename."""
        # Create test structure
        test_file = create_test_file("test.txt", "test content")
        base_name = "timestamped_output"
        
        exit_code, _ = run_m1f([
            "--source-directory", str(test_file.parent),
            "--output-file", str(temp_dir / f"{base_name}.txt"),
            "--add-timestamp",
            "--force",
        ])
        
        assert exit_code == 0
        
        # Check that a file with timestamp was created
        output_files = list(temp_dir.glob(f"{base_name}_*.txt"))
        assert len(output_files) == 1, "Expected one output file with timestamp"
        
        # Verify timestamp format (YYYYMMDD_HHMMSS)
        import re
        timestamp_pattern = r"_\d{8}_\d{6}\.txt$"
        assert re.search(timestamp_pattern, output_files[0].name), \
            "Output filename doesn't match timestamp pattern"
    
    @pytest.mark.unit
    @pytest.mark.parametrize("line_ending,expected", [
        ("unix", b"\n"),
        ("windows", b"\r\n"),
        ("preserve", None),  # Will check that it preserves original
    ])
    def test_line_ending_option(
        self,
        run_m1f,
        create_test_file,
        temp_dir,
        line_ending,
        expected
    ):
        """Test line ending conversion options."""
        # Create test file with specific line endings
        test_content = "Line 1\nLine 2\nLine 3"
        test_file = create_test_file("test.txt", test_content)
        output_file = temp_dir / f"line_ending_{line_ending}.txt"
        
        exit_code, _ = run_m1f([
            "--source-directory", str(test_file.parent),
            "--output-file", str(output_file),
            "--line-ending", line_ending,
            "--force",
        ])
        
        assert exit_code == 0
        
        if expected is not None:
            # Read as binary to check line endings
            content = output_file.read_bytes()
            
            # Check that the expected line ending is present
            assert expected in content, \
                f"Expected line ending not found for {line_ending}"
            
            # Check that the wrong line ending is not present
            wrong_ending = b"\r\n" if expected == b"\n" else b"\n"
            # Allow for the case where \r\n contains \n
            if expected == b"\n":
                assert b"\r\n" not in content, \
                    f"Unexpected CRLF found for {line_ending}"
    
    @pytest.mark.unit
    def test_force_overwrite(
        self,
        run_m1f,
        create_test_file,
        temp_dir
    ):
        """Test force overwrite option."""
        test_file = create_test_file("test.txt", "test content")
        output_file = temp_dir / "output.txt"
        
        # Create existing output file
        output_file.write_text("existing content")
        
        # Run without force (should fail)
        exit_code, _ = run_m1f([
            "--source-directory", str(test_file.parent),
            "--output-file", str(output_file),
        ], auto_confirm=False)
        
        # Should exit with error
        assert exit_code != 0
        
        # Run with force (should succeed)
        exit_code, _ = run_m1f([
            "--source-directory", str(test_file.parent),
            "--output-file", str(output_file),
            "--force",
        ])
        
        assert exit_code == 0
        
        # Verify file was overwritten
        content = output_file.read_text()
        assert "test content" in content
        assert "existing content" not in content
    
    @pytest.mark.integration
    def test_verbose_logging(
        self,
        run_m1f,
        create_test_file,
        temp_dir,
        capture_logs
    ):
        """Test verbose logging output."""
        test_file = create_test_file("test.txt", "test content")
        output_file = temp_dir / "verbose_output.txt"
        
        with capture_logs.capture("m1f") as log_capture:
            exit_code, _ = run_m1f([
                "--source-directory", str(test_file.parent),
                "--output-file", str(output_file),
                "--verbose",
                "--force",
            ])
        
        assert exit_code == 0
        
        # Check that verbose logging produced output
        log_output = log_capture.get_output()
        assert log_output, "No verbose log output captured"
        assert "DEBUG" in log_output or "INFO" in log_output, \
            "Expected debug/info level messages in verbose mode"
    
    @pytest.mark.unit
    def test_help_message(self, m1f_cli_runner):
        """Test help message display."""
        result = m1f_cli_runner(["--help"])
        
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()
        assert "--source-directory" in result.stdout
        assert "--output-file" in result.stdout
        assert "combine multiple files" in result.stdout.lower()
    
    @pytest.mark.unit
    def test_version_display(self, m1f_cli_runner):
        """Test version display."""
        result = m1f_cli_runner(["--version"])
        
        assert result.returncode == 0
        assert "m1f" in result.stdout.lower()
        # Should contain a version number pattern
        import re
        assert re.search(r"\d+\.\d+", result.stdout), \
            "Version number not found in output" 