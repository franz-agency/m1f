"""Advanced functionality tests for m1f."""

from __future__ import annotations

import zipfile
import tarfile
from pathlib import Path

import pytest

from ..base_test import BaseM1FTest


class TestM1FAdvanced(BaseM1FTest):
    """Advanced m1f functionality tests."""

    @pytest.mark.integration
    def test_create_archive_zip(self, run_m1f, create_m1f_test_structure, temp_dir):
        """Test creating a ZIP archive."""
        # Create test structure
        source_dir = create_m1f_test_structure()
        output_file = temp_dir / "output.txt"

        # Run with archive creation
        exit_code, _ = run_m1f(
            [
                "--source-directory",
                str(source_dir),
                "--output-file",
                str(output_file),
                "--create-archive",
                "--archive-type",
                "zip",
                "--force",
            ]
        )

        assert exit_code == 0

        # Check that archive was created (named with _backup suffix)
        archive_file = output_file.parent / f"{output_file.stem}_backup.zip"
        assert archive_file.exists(), "ZIP archive not created"
        assert archive_file.stat().st_size > 0, "ZIP archive is empty"

        # Verify archive contents
        with zipfile.ZipFile(archive_file, "r") as zf:
            names = zf.namelist()
            assert len(names) > 0, "ZIP archive has no files"

            # Check for expected files
            assert any("main.py" in name for name in names)
            assert any("README.md" in name for name in names)

    @pytest.mark.integration
    def test_create_archive_tar(self, run_m1f, create_m1f_test_structure, temp_dir):
        """Test creating a TAR.GZ archive."""
        source_dir = create_m1f_test_structure()
        output_file = temp_dir / "output.txt"

        # Run with tar archive creation
        exit_code, _ = run_m1f(
            [
                "--source-directory",
                str(source_dir),
                "--output-file",
                str(output_file),
                "--create-archive",
                "--archive-type",
                "tar.gz",
                "--force",
            ]
        )

        assert exit_code == 0

        # Check that archive was created (named with _backup suffix)
        archive_file = output_file.parent / f"{output_file.stem}_backup.tar.gz"
        assert archive_file.exists(), "TAR.GZ archive not created"
        assert archive_file.stat().st_size > 0, "TAR.GZ archive is empty"

        # Verify archive contents
        with tarfile.open(archive_file, "r:gz") as tf:
            members = tf.getmembers()
            assert len(members) > 0, "TAR archive has no files"

            # Check for expected files
            names = [m.name for m in members]
            assert any("main.py" in name for name in names)
            assert any("README.md" in name for name in names)

    @pytest.mark.unit
    def test_gitignore_pattern_support(
        self, run_m1f, create_test_directory_structure, temp_dir
    ):
        """Test support for gitignore pattern format."""
        # Create test structure with patterns to match
        test_structure = {
            "include.txt": "This should be included",
            "log1.log": "This log file should be excluded",
            "log2.log": "Another log file to exclude",
            "build": {
                "build_file.txt": "Should be excluded by build/ pattern",
            },
            "temp": {
                "temp_file.txt": "Should be excluded by temp/ pattern",
            },
            "important.txt": "This should be included despite pattern",
            ".gitignore": "*.log\nbuild/\ntemp/\n!important.txt",
        }

        source_dir = create_test_directory_structure(test_structure)
        output_file = temp_dir / "gitignore_test.txt"

        # Create gitignore file
        gitignore_file = temp_dir / "test.gitignore"
        gitignore_file.write_text("*.log\nbuild/\ntemp/\n")

        # Run with gitignore patterns
        exit_code, _ = run_m1f(
            [
                "--source-directory",
                str(source_dir),
                "--output-file",
                str(output_file),
                "--exclude-paths-file",
                str(gitignore_file),
                "--force",
            ]
        )

        assert exit_code == 0

        # Verify patterns were applied
        content = output_file.read_text()

        # Should include
        assert "include.txt" in content
        assert "important.txt" in content

        # Should exclude
        assert "log1.log" not in content
        assert "log2.log" not in content
        assert "build_file.txt" not in content
        assert "temp_file.txt" not in content

    @pytest.mark.unit
    def test_include_extensions(
        self, run_m1f, create_test_directory_structure, temp_dir
    ):
        """Test including only specific file extensions."""
        test_structure = {
            "file1.py": "Python file",
            "file2.txt": "Text file",
            "file3.md": "Markdown file",
            "file4.js": "JavaScript file",
            "file5.py": "Another Python file",
        }

        source_dir = create_test_directory_structure(test_structure)
        output_file = temp_dir / "include_extensions.txt"

        # Include only .py and .md files
        exit_code, _ = run_m1f(
            [
                "--source-directory",
                str(source_dir),
                "--output-file",
                str(output_file),
                "--include-extensions",
                "py",
                "md",
                "--force",
            ]
        )

        assert exit_code == 0

        content = output_file.read_text()

        # Should include
        assert "file1.py" in content
        assert "file3.md" in content
        assert "file5.py" in content

        # Should exclude
        assert "file2.txt" not in content
        assert "file4.js" not in content

    @pytest.mark.unit
    def test_exclude_extensions(
        self, run_m1f, create_test_directory_structure, temp_dir
    ):
        """Test excluding specific file extensions."""
        test_structure = {
            "file1.py": "Python file",
            "file2.txt": "Text file",
            "file3.md": "Markdown file",
            "file4.log": "Log file",
            "file5.tmp": "Temp file",
        }

        source_dir = create_test_directory_structure(test_structure)
        output_file = temp_dir / "exclude_extensions.txt"

        # Exclude .log and .tmp files
        exit_code, _ = run_m1f(
            [
                "--source-directory",
                str(source_dir),
                "--output-file",
                str(output_file),
                "--exclude-extensions",
                "log",
                "tmp",
                "--force",
            ]
        )

        assert exit_code == 0

        content = output_file.read_text()

        # Should include
        assert "file1.py" in content
        assert "file2.txt" in content
        assert "file3.md" in content

        # Should exclude
        assert "file4.log" not in content
        assert "file5.tmp" not in content

    @pytest.mark.unit
    def test_combined_extension_filters(
        self, run_m1f, create_test_directory_structure, temp_dir
    ):
        """Test combining include and exclude extension filters."""
        test_structure = {
            "main.py": "Main Python file",
            "test.py": "Test Python file",
            "backup.py.bak": "Backup file",
            "data.json": "JSON data",
            "config.yaml": "YAML config",
            "notes.txt": "Text notes",
        }

        source_dir = create_test_directory_structure(test_structure)
        output_file = temp_dir / "combined_filters.txt"

        # Include only .py files but exclude .bak
        exit_code, _ = run_m1f(
            [
                "--source-directory",
                str(source_dir),
                "--output-file",
                str(output_file),
                "--include-extensions",
                "py",
                "--exclude-extensions",
                "bak",
                "--force",
            ]
        )

        assert exit_code == 0

        content = output_file.read_text()

        # Should include only .py files
        assert "main.py" in content
        assert "test.py" in content

        # Should exclude everything else
        assert "backup.py.bak" not in content
        assert "data.json" not in content
        assert "config.yaml" not in content
        assert "notes.txt" not in content

    @pytest.mark.unit
    def test_input_paths_file(self, run_m1f, create_test_directory_structure, temp_dir):
        """Test using an input paths file."""
        # Create test structure
        test_structure = {
            "dir1": {
                "file1.txt": "File 1",
                "file2.txt": "File 2",
            },
            "dir2": {
                "file3.txt": "File 3",
                "file4.txt": "File 4",
            },
            "dir3": {
                "file5.txt": "File 5",
            },
        }

        source_dir = create_test_directory_structure(test_structure)

        # Create input paths file (only include dir1 and dir3)
        input_paths = temp_dir / "input_paths.txt"
        input_paths.write_text(f"{source_dir / 'dir1'}\n{source_dir / 'dir3'}\n")

        output_file = temp_dir / "input_paths_output.txt"

        exit_code, _ = run_m1f(
            [
                "--input-file",
                str(input_paths),
                "--output-file",
                str(output_file),
                "--force",
            ]
        )

        assert exit_code == 0

        content = output_file.read_text()

        # Should include files from dir1 and dir3
        assert "file1.txt" in content
        assert "file2.txt" in content
        assert "file5.txt" in content

        # Should exclude files from dir2
        assert "file3.txt" not in content
        assert "file4.txt" not in content

    @pytest.mark.unit
    def test_input_paths_with_glob(
        self, run_m1f, create_test_directory_structure, temp_dir
    ):
        """Test glob patterns in input paths."""
        test_structure = {
            "src": {
                "module1.py": "Module 1",
                "module2.py": "Module 2",
                "test_module1.py": "Test 1",
            },
            "docs": {
                "readme.md": "README",
                "api.md": "API docs",
            },
            "config.json": "Config",
        }

        source_dir = create_test_directory_structure(test_structure)
        output_file = temp_dir / "glob_output.txt"

        # Create input file with glob pattern
        input_file = temp_dir / "glob_patterns.txt"
        input_file.write_text(str(source_dir / "src" / "*.py"))

        # Use glob to include only .py files in src
        exit_code, _ = run_m1f(
            [
                "--input-file",
                str(input_file),
                "--output-file",
                str(output_file),
                "--force",
            ]
        )

        assert exit_code == 0

        content = output_file.read_text()

        # Should include all .py files from src
        assert "module1.py" in content
        assert "module2.py" in content
        assert "test_module1.py" in content

        # Should exclude other files
        assert "readme.md" not in content
        assert "config.json" not in content

    @pytest.mark.unit
    def test_filename_mtime_hash(self, run_m1f, create_test_file, temp_dir):
        """Test filename contains hash of file mtimes."""
        # Create test files with specific mtimes
        import time

        source_dir = temp_dir / "hash_test_source"
        source_dir.mkdir()

        # Create files with known mtimes
        file1 = source_dir / "file1.txt"
        file1.write_text("Content 1")

        time.sleep(0.1)  # Ensure different mtime

        file2 = source_dir / "file2.txt"
        file2.write_text("Content 2")

        # First run
        output_base = "hash_test"
        exit_code, _ = run_m1f(
            [
                "--source-directory",
                str(source_dir),
                "--output-file",
                str(temp_dir / f"{output_base}.txt"),
                "--filename-mtime-hash",
                "--force",
            ]
        )

        assert exit_code == 0

        # Find the created file with hash (excluding auxiliary files)
        output_files = [
            f
            for f in temp_dir.glob(f"{output_base}_*.txt")
            if not f.name.endswith(("_filelist.txt", "_dirlist.txt"))
        ]
        assert len(output_files) == 1, "Expected one output file with hash"

        # Extract hash from filename (format: base_hash_.txt)
        filename_parts = output_files[0].stem.split("_")
        first_hash = filename_parts[-2]  # The hash is the second-to-last part
        assert len(first_hash) == 12, "Hash should be 12 characters"

        # Run again without changes - hash should be the same
        exit_code, _ = run_m1f(
            [
                "--source-directory",
                str(source_dir),
                "--output-file",
                str(temp_dir / f"{output_base}_second.txt"),
                "--filename-mtime-hash",
                "--force",
            ]
        )

        second_files = [
            f
            for f in temp_dir.glob(f"{output_base}_second_*.txt")
            if not f.name.endswith(("_filelist.txt", "_dirlist.txt"))
        ]
        second_hash = second_files[0].stem.split("_")[-2]

        assert first_hash == second_hash, "Hash should be same for unchanged files"

        # Modify a file and run again - hash should change
        file1.write_text("Modified content")

        exit_code, _ = run_m1f(
            [
                "--source-directory",
                str(source_dir),
                "--output-file",
                str(temp_dir / f"{output_base}_third.txt"),
                "--filename-mtime-hash",
                "--force",
            ]
        )

        third_files = [
            f
            for f in temp_dir.glob(f"{output_base}_third_*.txt")
            if not f.name.endswith(("_filelist.txt", "_dirlist.txt"))
        ]
        third_hash = third_files[0].stem.split("_")[-2]

        assert first_hash != third_hash, "Hash should change when file is modified"

    @pytest.mark.unit
    def test_no_default_excludes(
        self, run_m1f, create_test_directory_structure, temp_dir
    ):
        """Test disabling default excludes."""
        test_structure = {
            ".git": {
                "config": "Git config",
                "HEAD": "ref: refs/heads/main",
            },
            "__pycache__": {
                "module.cpython-39.pyc": b"Python bytecode",
            },
            "node_modules": {
                "package": {
                    "index.js": "module.exports = {}",
                },
            },
            "regular_file.txt": "Regular content",
        }

        source_dir = create_test_directory_structure(test_structure)

        # First test with default excludes (should exclude .git, etc.)
        output_default = temp_dir / "with_default_excludes.txt"
        exit_code, _ = run_m1f(
            [
                "--source-directory",
                str(source_dir),
                "--output-file",
                str(output_default),
                "--force",
            ]
        )

        assert exit_code == 0

        default_content = output_default.read_text()
        assert "regular_file.txt" in default_content
        assert ".git" not in default_content
        assert "__pycache__" not in default_content
        assert "node_modules" not in default_content

        # Now test without default excludes
        output_no_default = temp_dir / "no_default_excludes.txt"
        exit_code, _ = run_m1f(
            [
                "--source-directory",
                str(source_dir),
                "--output-file",
                str(output_no_default),
                "--no-default-excludes",
                "--force",
            ]
        )

        assert exit_code == 0

        no_default_content = output_no_default.read_text()
        assert "regular_file.txt" in no_default_content
        assert "Git config" in no_default_content  # .git included
        assert "module.exports" in no_default_content  # node_modules included

    @pytest.mark.unit
    def test_large_file_handling(self, run_m1f, create_test_file, temp_dir):
        """Test handling of files with size limit.

        Tests that files larger than a specified limit are skipped.
        """
        # Create a small file (5KB - below limit)
        small_content = "x" * (5 * 1024)  # 5KB
        small_file = create_test_file("small_file.txt", small_content)

        # Create a large file (15KB - above limit)
        large_content = "y" * (15 * 1024)  # 15KB
        large_file = create_test_file("large_file.txt", large_content)

        output_file = temp_dir / "size_limit_output.txt"

        # Run with 10KB size limit
        exit_code, output = run_m1f(
            [
                "--source-directory",
                str(small_file.parent),
                "--output-file",
                str(output_file),
                "--max-file-size",
                "10KB",
                "--force",
            ]
        )

        assert exit_code == 0
        assert output_file.exists()

        # Read the output content
        output_content = output_file.read_text()

        # Small file should be included
        assert "small_file.txt" in output_content
        assert small_content in output_content

        # Large file should be mentioned in file list but content not included
        assert "large_file.txt" in output_content  # Should be in file list
        assert large_content not in output_content  # Content should not be included

    @pytest.mark.unit
    def test_include_binary_files(
        self, run_m1f, create_test_directory_structure, temp_dir
    ):
        """Test including binary files."""
        # Create test structure with binary files
        test_structure = {
            "text.txt": "Text content",
            "image.png": b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR",
            "data.bin": b"\x00\x01\x02\x03\x04\x05",
        }

        source_dir = create_test_directory_structure(test_structure)

        # Test without binary files (default)
        output_no_binary = temp_dir / "no_binary.txt"
        exit_code, _ = run_m1f(
            [
                "--source-directory",
                str(source_dir),
                "--output-file",
                str(output_no_binary),
                "--force",
            ]
        )

        assert exit_code == 0

        content_no_binary = output_no_binary.read_text()
        assert "text.txt" in content_no_binary
        assert "Text content" in content_no_binary
        # Binary files should be noted but content excluded
        assert "image.png" in content_no_binary
        assert "PNG" not in content_no_binary  # Binary content not included

        # Test with binary files included
        output_with_binary = temp_dir / "with_binary.txt"
        exit_code, _ = run_m1f(
            [
                "--source-directory",
                str(source_dir),
                "--output-file",
                str(output_with_binary),
                "--include-binary-files",
                "--force",
            ]
        )

        assert exit_code == 0

        # With binary files, they should be base64 encoded or similar
        # The exact format depends on the separator style
        assert output_with_binary.stat().st_size > output_no_binary.stat().st_size
