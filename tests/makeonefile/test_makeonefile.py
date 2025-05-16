#!/usr/bin/env python3
"""
Tests for the makeonefile.py script.

This test suite verifies the functionality of the makeonefile.py script by:
1. Setting up a test directory with various file types
2. Running the script with different configurations
3. Validating the output files match expected behavior
"""

import os
import sys
import json
import shutil
import time
import pytest
import subprocess
import argparse
import logging
import platform
from pathlib import Path

# Add the tools directory to path to import the makeonefile module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))
import makeonefile

# Test constants
TEST_DIR = Path(__file__).parent
SOURCE_DIR = TEST_DIR / "source"
OUTPUT_DIR = TEST_DIR / "output"
EXCLUDE_PATHS_FILE = TEST_DIR / "exclude_paths.txt"

# Platform detection for platform-specific path handling
IS_WINDOWS = platform.system() == "Windows"
PATH_SEP = os.path.sep  # \ on Windows, / on Unix


# Helper function to run makeonefile with specific arguments for testing
def run_makeonefile(arg_list):
    """
    Run makeonefile.main() with the specified command line arguments.
    This works by temporarily replacing sys.argv with our test arguments
    and patching sys.exit to prevent test termination.

    Args:
        arg_list: List of command line arguments to pass to main()

    Returns:
        None, but main() will execute with the provided arguments
    """
    # Save original argv and exit function
    original_argv = sys.argv.copy()
    original_exit = sys.exit

    # Define a custom exit function that just records the exit code
    def mock_exit(code=0):
        if code != 0:
            print(f"WARNING: Script exited with non-zero exit code: {code}")
        return code

    try:
        # Replace argv with our test arguments, adding script name at position 0
        sys.argv = ["makeonefile.py"] + arg_list
        # Patch sys.exit to prevent test termination
        sys.exit = mock_exit
        # Call main which will parse sys.argv internally
        makeonefile.main()
    finally:
        # Restore original argv and exit function
        sys.argv = original_argv
        sys.exit = original_exit


class TestMakeOneFile:
    """Test cases for the makeonefile.py script."""

    @classmethod
    def setup_class(cls):
        """Setup test environment once before all tests."""
        # Print test environment information
        print(f"\nRunning tests for makeonefile.py")
        print(f"Python version: {sys.version}")
        print(f"Test directory: {TEST_DIR}")
        print(f"Source directory: {SOURCE_DIR}")

    def setup_method(self):
        """Setup test environment before each test."""
        # Close any open logging handlers that might keep files locked
        logger = logging.getLogger("makeonefile")
        if logger.handlers:
            for handler in logger.handlers:
                handler.close()
            logger.handlers = []

        # Wait a brief moment to ensure files are released
        time.sleep(0.1)

        # Ensure the output directory exists and is empty
        if OUTPUT_DIR.exists():
            # Delete files individually to handle locked files
            for file_path in OUTPUT_DIR.glob("*"):
                if file_path.is_file():
                    try:
                        file_path.unlink()
                    except PermissionError:
                        print(
                            f"Warning: Could not delete {file_path} during setup. File is still in use."
                        )
                    except Exception as e:
                        print(f"Error deleting {file_path} during setup: {e}")

            # Try to remove empty directories
            try:
                for dir_path in [p for p in OUTPUT_DIR.glob("*") if p.is_dir()]:
                    try:
                        shutil.rmtree(dir_path)
                    except Exception as e:
                        print(f"Error removing directory {dir_path} during setup: {e}")
            except Exception as e:
                print(f"Error cleaning output directory: {e}")
        else:
            # Create the output directory if it doesn't exist
            OUTPUT_DIR.mkdir(exist_ok=True)

    def teardown_method(self):
        """Clean up after each test."""
        # Close any open logging handlers that might keep files locked
        # This is necessary because the makeonefile script sets up file handlers for logging
        logger = logging.getLogger("makeonefile")
        if logger.handlers:
            for handler in logger.handlers:
                handler.close()
            logger.handlers = []

        # Wait a brief moment to ensure files are released
        time.sleep(0.1)

        # Remove output files for a clean slate between tests
        for file_path in OUTPUT_DIR.glob("*"):
            if file_path.is_file():
                try:
                    file_path.unlink()
                except PermissionError:
                    # Skip files that are still locked
                    print(
                        f"Warning: Could not delete {file_path}. File is still in use."
                    )
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")

    def test_basic_execution(self):
        """Test basic execution of the script."""
        output_file = OUTPUT_DIR / "basic_output.txt"

        # Run the script programmatically
        run_makeonefile(
            [
                "--source-directory",
                str(SOURCE_DIR),
                "--output-file",
                str(output_file),
                "--force",
            ]
        )

        # Verify outputs
        assert output_file.exists(), "Output file was not created"
        assert output_file.stat().st_size > 0, "Output file is empty"

        # Check that accompanying files were created
        assert (OUTPUT_DIR / "basic_output.log").exists(), "Log file not created"
        assert (
            OUTPUT_DIR / "basic_output_filelist.txt"
        ).exists(), "Filelist not created"
        assert (OUTPUT_DIR / "basic_output_dirlist.txt").exists(), "Dirlist not created"

        # Verify excluded directories are not in the output
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "node_modules" not in content, "node_modules should be excluded"
            assert ".git" not in content, "Git directory should be excluded"

    def test_include_dot_files(self):
        """Test inclusion of dot files."""
        output_file = OUTPUT_DIR / "dot_files_included.txt"

        # Run with dot files included
        run_makeonefile(
            [
                "--source-directory",
                str(SOURCE_DIR),
                "--output-file",
                str(output_file),
                "--include-dot-files",
                "--force",
            ]
        )

        # Verify dot files are included
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            # Use platform-agnostic path checking for .hidden directory
            # Check for .hidden directory using platform-specific path separators
            hidden_path = ".hidden"
            assert hidden_path in content, "Dot files should be included"
            # Check for the contents of the hidden file
            assert (
                "SECRET_KEY=test_secret_key_12345" in content
            ), "Hidden file contents should be included"

    def test_exclude_paths_file(self):
        """Test excluding paths from a file."""
        output_file = OUTPUT_DIR / "excluded_paths.txt"

        # Run with exclude paths file
        run_makeonefile(
            [
                "--source-directory",
                str(SOURCE_DIR),
                "--output-file",
                str(output_file),
                "--exclude-paths-file",
                str(EXCLUDE_PATHS_FILE),
                "--force",
            ]
        )

        # Verify excluded paths are not in the output
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            # Check the file names which should be excluded, not the full paths
            assert "FILE: index.php" not in content, "index.php should be excluded"
            assert "FILE: png.png" not in content, "png.png should be excluded"

    def test_separator_styles(self):
        """Test different separator styles."""
        styles = ["Standard", "Detailed", "Markdown", "MachineReadable", "None"]

        for style in styles:
            output_file = OUTPUT_DIR / f"separator_{style.lower()}.txt"

            # Run with specific separator style
            run_makeonefile(
                [
                    "--source-directory",
                    str(SOURCE_DIR),
                    "--output-file",
                    str(output_file),
                    "--separator-style",
                    style,
                    "--force",
                ]
            )

            # Verify the output file exists and has content
            assert output_file.exists(), f"Output file for {style} style not created"
            assert (
                output_file.stat().st_size > 0
            ), f"Output file for {style} style is empty"

            # For MachineReadable style, verify it has JSON metadata
            if style == "MachineReadable":
                with open(output_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    assert (
                        "# METADATA:" in content
                    ), "MachineReadable style should include metadata"
                    assert (
                        '{"modified":' in content
                    ), "MachineReadable style should have JSON metadata"

    def test_timestamp_in_filename(self):
        """Test adding timestamp to output filename."""
        # Run with timestamp option
        run_makeonefile(
            [
                "--source-directory",
                str(SOURCE_DIR),
                "--output-file",
                str(OUTPUT_DIR / "timestamp_test.txt"),
                "--add-timestamp",
                "--force",
            ]
        )

        # Check if a file with timestamp exists
        timestamp_files = list(OUTPUT_DIR.glob("timestamp_test_*.txt"))
        assert len(timestamp_files) > 0, "No file with timestamp was created"

        # The filename should contain numbers for date/time
        filename = timestamp_files[0].name
        assert "_20" in filename, "Timestamp not found in filename"

    def test_additional_excludes(self):
        """Test excluding additional directories."""
        output_file = OUTPUT_DIR / "additional_excludes.txt"

        # Run with additional excludes
        run_makeonefile(
            [
                "--source-directory",
                str(SOURCE_DIR),
                "--output-file",
                str(output_file),
                "--additional-excludes",
                "docs",
                "images",
                "--force",
            ]
        )

        # Verify excluded dirs are not in the output
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            # Using platform-agnostic approach to check for excluded directories
            assert "FILE: docs" not in content, "docs directory should be excluded"
            assert "FILE: images" not in content, "images directory should be excluded"

    def test_create_archive_zip(self):
        """Test creating a zip archive of processed files."""
        output_file = OUTPUT_DIR / "archive_test.txt"

        # Run with archive creation
        run_makeonefile(
            [
                "--source-directory",
                str(SOURCE_DIR),
                "--output-file",
                str(output_file),
                "--create-archive",
                "--archive-type",
                "zip",
                "--force",
            ]
        )

        # Verify archive was created
        archive_file = OUTPUT_DIR / "archive_test_backup.zip"
        assert archive_file.exists(), "Zip archive was not created"
        assert archive_file.stat().st_size > 0, "Zip archive is empty"

        # Check the content of the archive (would need zipfile module)
        import zipfile

        with zipfile.ZipFile(archive_file, "r") as zip_ref:
            file_list = zip_ref.namelist()
            assert len(file_list) > 0, "Zip archive contains no files"

            # Check for at least one expected file
            found_python_file = False
            for file_path in file_list:
                if file_path.endswith(".py"):
                    found_python_file = True
                    break
            assert found_python_file, "No Python files found in the archive"

    def test_create_archive_tar(self):
        """Test creating a tar.gz archive of processed files."""
        output_file = OUTPUT_DIR / "archive_tar_test.txt"

        # Run with tar.gz archive creation
        run_makeonefile(
            [
                "--source-directory",
                str(SOURCE_DIR),
                "--output-file",
                str(output_file),
                "--create-archive",
                "--archive-type",
                "tar.gz",
                "--force",
            ]
        )

        # Verify archive was created
        archive_file = OUTPUT_DIR / "archive_tar_test_backup.tar.gz"
        assert archive_file.exists(), "Tar.gz archive was not created"
        assert archive_file.stat().st_size > 0, "Tar.gz archive is empty"

        # Check the content of the archive
        import tarfile

        with tarfile.open(archive_file, "r:gz") as tar_ref:
            file_list = tar_ref.getnames()
            assert len(file_list) > 0, "Tar archive contains no files"

    def test_line_ending_option(self):
        """Test specifying line ending format."""
        # Test both LF and CRLF options
        for ending in ["LF", "CRLF"]:
            output_file = OUTPUT_DIR / f"line_ending_{ending.lower()}.txt"

            run_makeonefile(
                [
                    "--source-directory",
                    str(SOURCE_DIR),
                    "--output-file",
                    str(output_file),
                    "--line-ending",
                    ending.lower(),
                    "--force",
                ]
            )

            # Verify output file exists
            assert (
                output_file.exists()
            ), f"Output file for {ending} line endings not created"

    def test_command_line_execution(self):
        """Test executing the script as a command line tool."""
        output_file = OUTPUT_DIR / "cli_execution.txt"

        # Run the script as a subprocess
        script_path = Path(__file__).parent.parent.parent / "tools" / "makeonefile.py"
        result = subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--source-directory",
                str(SOURCE_DIR),
                "--output-file",
                str(output_file),
                "--force",
                "--verbose",
            ],
            capture_output=True,
            text=True,
        )

        # Check that the script executed successfully
        assert result.returncode == 0, f"Script failed with error: {result.stderr}"

        # Verify output file was created
        assert output_file.exists(), "Output file not created from CLI execution"
        assert output_file.stat().st_size > 0, "Output file is empty from CLI execution"

    def test_input_paths_file(self):
        """Test processing files from an input paths file rather than source directory."""
        output_file = OUTPUT_DIR / "input_paths.txt"
        input_file = TEST_DIR / "input_paths.txt"

        # Run with input paths file
        run_makeonefile(
            [
                "--input-file",
                str(input_file),
                "--output-file",
                str(output_file),
                "--force",
            ]
        )

        # Verify only specified files are included
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "hello.py" in content, "hello.py should be included"
            assert "utils.py" in content, "utils.py should be included"
            assert "README.md" in content, "README.md should be included"
            assert "index.php" not in content, "index.php should not be included"

    def test_unicode_handling(self):
        """Test handling of Unicode characters in files."""
        output_file = OUTPUT_DIR / "unicode_test.txt"

        # Create a temporary input paths file specifically for the Unicode test
        temp_input_file = OUTPUT_DIR / "temp_unicode_input.txt"
        with open(temp_input_file, "w", encoding="utf-8") as f:
            # Use a path that's relative to the test directory
            f.write(f"../source/docs/unicode_sample.md")

        # Run with the temp input paths file
        run_makeonefile(
            [
                "--input-file",
                str(temp_input_file),
                "--output-file",
                str(output_file),
                "--force",
            ]
        )

        # Verify Unicode content is preserved
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Grüße aus München!" in content, "German Unicode not preserved"
            assert "你好，世界！" in content, "Chinese Unicode not preserved"
            assert "こんにちは世界！" in content, "Japanese Unicode not preserved"
            assert "😀 🚀" in content, "Emojis not preserved"

    def test_edge_cases(self):
        """Test handling of edge cases like HTML with comments, fake separators, etc."""
        output_file = OUTPUT_DIR / "edge_case_test.txt"

        # Create a temporary input paths file specifically for the edge case test
        temp_input_file = OUTPUT_DIR / "temp_edge_case_input.txt"
        with open(temp_input_file, "w", encoding="utf-8") as f:
            # Use a path that's relative to the test directory
            f.write(f"../source/code/edge_case.html")

        # Run with the temp input paths file
        run_makeonefile(
            [
                "--input-file",
                str(temp_input_file),
                "--output-file",
                str(output_file),
                "--force",
            ]
        )

        # Verify edge case content is handled correctly
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert (
                "<!-- Comment with special characters: < > & " in content
            ), "HTML comments not preserved"
            assert "fake/separator.txt" in content, "Fake separator text not preserved"

    def test_large_file_handling(self):
        """Test processing of large files."""
        output_file = OUTPUT_DIR / "large_file_test.txt"

        # Create a temporary input paths file specifically for the large file test
        temp_input_file = OUTPUT_DIR / "temp_large_file_input.txt"
        with open(temp_input_file, "w", encoding="utf-8") as f:
            # Use a path that's relative to the test directory
            f.write(f"../source/code/large_sample.txt")

        # Measure execution time for performance testing
        start_time = time.time()

        # Run with the temp input paths file
        run_makeonefile(
            [
                "--input-file",
                str(temp_input_file),
                "--output-file",
                str(output_file),
                "--force",
            ]
        )

        execution_time = time.time() - start_time

        # Verify large file was processed successfully
        assert output_file.exists(), "Output file not created"
        assert output_file.stat().st_size > 0, "Output file is empty"

        # Log performance information
        print(f"Large file processing time: {execution_time:.2f} seconds")

        # Basic verification of content
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Large Sample Text File" in content, "File header missing"

            # Check for code patterns that would indicate the file was processed correctly
            assert (
                "This is a large sample text file" in content
            ), "File description missing"
            assert (
                "Generate a large amount of text content" in content
            ), "Content generation comment missing"

            # Check for the long string of 'a' characters (checking for at least 100 consecutive 'a's)
            # We don't check for the exact 3000 characters as the content might be truncated in display
            assert "a" * 100 in content, "Long string of 'a' characters is missing"

    def test_include_binary_files(self):
        """Test inclusion of binary files."""
        # Test 1: Without --include-binary-files (default behavior - binary files should be excluded)
        output_file_excluded = OUTPUT_DIR / "binary_excluded.txt"

        # Create a temporary input paths file pointing to a binary file
        temp_input_file = OUTPUT_DIR / "temp_binary_input.txt"
        with open(temp_input_file, "w", encoding="utf-8") as f:
            # Using the png.png file which exists in the test source
            f.write(f"../source/docs/png.png")

        # Run without include-binary-files flag
        run_makeonefile(
            [
                "--input-file",
                str(temp_input_file),
                "--output-file",
                str(output_file_excluded),
                "--force",
            ]
        )

        # Verify binary file was excluded by default
        with open(output_file_excluded, "r", encoding="utf-8") as f:
            content = f.read()
            assert "png.png" not in content, "Binary file should be excluded by default"

        # Test 2: With --include-binary-files flag
        output_file_included = OUTPUT_DIR / "binary_included.txt"

        # Run with include-binary-files flag
        run_makeonefile(
            [
                "--input-file",
                str(temp_input_file),
                "--output-file",
                str(output_file_included),
                "--include-binary-files",
                "--force",
            ]
        )

        # Verify binary file was included
        with open(output_file_included, "r", encoding="utf-8") as f:
            content = f.read()
            assert (
                "png.png" in content
            ), "Binary file should be included with --include-binary-files flag"

        # Additional check: Verify that some binary content is present
        # This might include some non-printable characters or PNG header bytes like "PNG" signature
        with open(output_file_included, "rb") as f:
            binary_content = f.read()
            # Check for PNG signature or some binary content
            assert (
                b"PNG" in binary_content
            ), "PNG signature should be present in binary content"

    def test_no_default_excludes(self):
        """Test disabling default directory exclusions."""
        output_file = OUTPUT_DIR / "no_default_excludes.txt"

        # Run with --no-default-excludes flag
        run_makeonefile(
            [
                "--source-directory",
                str(SOURCE_DIR),
                "--output-file",
                str(output_file),
                "--no-default-excludes",
                "--force",
            ]
        )

        # Verify normally excluded directories are now included
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            # Check for content from normally excluded directories
            assert "node_modules" in content, "node_modules should be included when using --no-default-excludes"
            assert ".git" in content, "Git directory should be included when using --no-default-excludes"
            
            # Verify log message indicates default exclusions are disabled
            log_file = output_file.with_name(f"{output_file.stem}.log")
            with open(log_file, 'r', encoding='utf-8') as log:
                log_content = log.read()
                assert "Default directory exclusions are disabled" in log_content, "Log should indicate default exclusions are disabled"

    def test_include_extensions(self):
        """Test including only specific file extensions."""
        output_file = OUTPUT_DIR / "include_extensions.txt"

        # Run with --include-extensions to include only .txt and .json files
        run_makeonefile(
            [
                "--source-directory",
                str(SOURCE_DIR / "file_extensions_test"),
                "--output-file",
                str(output_file),
                "--include-extensions",
                ".txt",
                ".json",
                "--force",
            ]
        )

        # Verify only specified extensions are included
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "test.txt" in content, ".txt files should be included"
            assert "test.json" in content, ".json files should be included"
            assert "test.md" not in content, ".md files should not be included"
            assert "test.py" not in content, ".py files should not be included"
            assert "test.log" not in content, ".log files should not be included"
            assert "test.tmp" not in content, ".tmp files should not be included"

    def test_exclude_extensions(self):
        """Test excluding specific file extensions."""
        output_file = OUTPUT_DIR / "exclude_extensions.txt"

        # Run with --exclude-extensions to exclude .log and .tmp files
        run_makeonefile(
            [
                "--source-directory",
                str(SOURCE_DIR / "file_extensions_test"),
                "--output-file",
                str(output_file),
                "--exclude-extensions",
                ".log",
                ".tmp",
                "--force",
            ]
        )

        # Verify specified extensions are excluded
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "test.txt" in content, ".txt files should be included"
            assert "test.json" in content, ".json files should be included"
            assert "test.md" in content, ".md files should be included"
            assert "test.py" in content, ".py files should be included"
            assert "test.log" not in content, ".log files should be excluded"
            assert "test.tmp" not in content, ".tmp files should be excluded"

    def test_extension_filtering_without_dot(self):
        """Test extension filtering when extensions are provided without leading dots."""
        output_file = OUTPUT_DIR / "extension_no_dots.txt"

        # Run with extensions specified without dots
        run_makeonefile(
            [
                "--source-directory",
                str(SOURCE_DIR / "file_extensions_test"),
                "--output-file",
                str(output_file),
                "--include-extensions",
                "txt",
                "json",
                "--force",
            ]
        )

        # Verify the behavior is the same as if dots were included
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "test.txt" in content, ".txt files should be included when specified without dot"
            assert "test.json" in content, ".json files should be included when specified without dot"
            assert "test.md" not in content, ".md files should not be included"

    def test_no_default_excludes_with_additional_excludes(self):
        """Test combining --no-default-excludes with --additional-excludes."""
        output_file = OUTPUT_DIR / "no_default_with_additional.txt"

        # Run with --no-default-excludes but add some specific excludes
        run_makeonefile(
            [
                "--source-directory",
                str(SOURCE_DIR),
                "--output-file",
                str(output_file),
                "--no-default-excludes",
                "--additional-excludes",
                "node_modules",
                "--force",
            ]
        )

        # Verify default excluded directories are included except those specified
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "node_modules" not in content, "node_modules should be excluded by --additional-excludes"
            assert ".git" in content, "Git directory should be included (no default excludes)"
            
            # Verify the dirlist and filelist don't contain node_modules
            filelist_path = output_file.with_name(f"{output_file.stem}_filelist.txt")
            with open(filelist_path, 'r', encoding='utf-8') as fl:
                filelist_content = fl.read()
                assert "node_modules" not in filelist_content, "node_modules should not be in file list"

    def test_combined_extension_filters(self):
        """Test combining include and exclude extension filters."""
        output_file = OUTPUT_DIR / "combined_extension_filters.txt"

        # Run with both include and exclude extensions
        run_makeonefile(
            [
                "--source-directory",
                str(SOURCE_DIR / "file_extensions_test"),
                "--output-file",
                str(output_file),
                "--include-extensions",
                ".txt",
                ".json",
                ".log",
                "--exclude-extensions",
                ".log",
                "--force",
            ]
        )

        # Verify the exclude filter takes precedence over include
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "test.txt" in content, ".txt files should be included"
            assert "test.json" in content, ".json files should be included"
            assert "test.log" not in content, ".log files should be excluded despite being in include list"
            assert "test.md" not in content, ".md files should not be included"
            assert "test.py" not in content, ".py files should not be included"
            assert "test.tmp" not in content, ".tmp files should not be included"


# Run the tests when the script is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
