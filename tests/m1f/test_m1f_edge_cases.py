"""Edge case and special scenario tests for m1f."""

from __future__ import annotations

import shutil
import time
from pathlib import Path

import pytest

from ..base_test import BaseM1FTest


class TestM1FEdgeCases(BaseM1FTest):
    """Tests for edge cases and special scenarios in m1f."""

    @pytest.mark.unit
    def test_unicode_handling(self, run_m1f, create_test_file, temp_dir):
        """Test handling of Unicode characters in files."""
        # Create files with various Unicode content
        source_dir = temp_dir / "unicode_test"
        source_dir.mkdir()

        test_files = [
            ("german.txt", "Grüße aus München!"),
            ("chinese.txt", "你好，世界！"),
            ("japanese.txt", "こんにちは世界！"),
            ("emoji.txt", "😀 🚀 🎉 ✨"),
            ("mixed.txt", "Hello мир 世界 🌍"),
        ]

        for filename, content in test_files:
            create_test_file(f"unicode_test/{filename}", content)

        output_file = temp_dir / "unicode_output.txt"

        exit_code, _ = run_m1f(
            [
                "--source-directory",
                str(source_dir),
                "--output-file",
                str(output_file),
                "--force",
            ]
        )

        assert exit_code == 0

        # Verify Unicode content is preserved
        content = output_file.read_text(encoding="utf-8")

        for _, expected_content in test_files:
            assert (
                expected_content in content
            ), f"Unicode content '{expected_content}' not preserved"

    @pytest.mark.unit
    def test_edge_case_html_with_fake_separators(
        self, run_m1f, create_test_file, temp_dir
    ):
        """Test handling of HTML with comments and fake separator patterns."""
        # Create HTML file with tricky content
        html_content = """<!DOCTYPE html>
<html>
<head>
    <!-- Comment with special characters: < > & " ' -->
    <title>Test Page</title>
</head>
<body>
    <!-- This looks like a separator but isn't -->
    <p>FILE: fake/separator.txt</p>
    <p>========================================</p>
    <p>This might confuse the s1f parser</p>
    <p>========================================</p>
    
    <!-- Another fake separator -->
    <pre>
==== FILE: another/fake.txt ====
This is not a real file separator
====================================
    </pre>
</body>
</html>"""

        test_file = create_test_file("edge_case.html", html_content)
        output_file = temp_dir / "edge_case_output.txt"

        exit_code, _ = run_m1f(
            [
                "--source-directory",
                str(test_file.parent),
                "--output-file",
                str(output_file),
                "--force",
            ]
        )

        assert exit_code == 0

        # Verify content is preserved correctly
        content = output_file.read_text()
        assert "<!-- Comment with special characters: < > & " in content
        assert "fake/separator.txt" in content
        assert "This might confuse the s1f parser" in content

    @pytest.mark.unit
    def test_empty_files_and_directories(
        self, run_m1f, create_test_directory_structure, temp_dir
    ):
        """Test handling of empty files and directories."""
        structure = {
            "empty.txt": "",
            "empty_dir": {},
            "dir_with_empty_file": {
                "empty_inside.txt": "",
            },
            "normal.txt": "Normal content",
        }

        source_dir = create_test_directory_structure(structure)
        output_file = temp_dir / "empty_test.txt"

        exit_code, _ = run_m1f(
            [
                "--source-directory",
                str(source_dir),
                "--output-file",
                str(output_file),
                "--force",
            ]
        )

        assert exit_code == 0

        # Check that empty files are included
        content = output_file.read_text()
        assert "empty.txt" in content
        assert "empty_inside.txt" in content
        assert "normal.txt" in content

        # Check dirlist
        dirlist = output_file.parent / f"{output_file.stem}_dirlist.txt"
        dirlist_content = dirlist.read_text()
        assert "empty_dir" in dirlist_content
        assert "dir_with_empty_file" in dirlist_content

    @pytest.mark.unit
    def test_symlinks(self, run_m1f, create_test_file, temp_dir, is_windows):
        """Test handling of symbolic links."""
        if is_windows:
            pytest.skip("Symlink test requires Unix-like system")

        source_dir = temp_dir / "symlink_test"
        source_dir.mkdir()

        # Create regular file
        target_file = create_test_file("symlink_test/target.txt", "Target content")

        # Create symlink
        symlink = source_dir / "link.txt"
        symlink.symlink_to(target_file)

        output_file = temp_dir / "symlink_output.txt"

        exit_code, _ = run_m1f(
            [
                "--source-directory",
                str(source_dir),
                "--output-file",
                str(output_file),
                "--force",
            ]
        )

        assert exit_code == 0

        # Both files should be included
        content = output_file.read_text()
        assert "target.txt" in content
        assert "link.txt" in content
        assert "Target content" in content

    @pytest.mark.unit
    def test_special_filenames(self, run_m1f, create_test_file, temp_dir):
        """Test handling of files with special names."""
        source_dir = temp_dir / "special_names"
        source_dir.mkdir()

        # Create files with special names
        special_files = [
            ("file with spaces.txt", "Content with spaces"),
            ("file-with-dashes.txt", "Content with dashes"),
            ("file_with_underscores.txt", "Content with underscores"),
            ("file.multiple.dots.txt", "Content with dots"),
            ("@special#chars%.txt", "Content with special chars"),
            ("file(with)[brackets]{braces}.txt", "Content with brackets"),
        ]

        for filename, content in special_files:
            file_path = source_dir / filename
            file_path.write_text(content)

        output_file = temp_dir / "special_names_output.txt"

        exit_code, _ = run_m1f(
            [
                "--source-directory",
                str(source_dir),
                "--output-file",
                str(output_file),
                "--force",
            ]
        )

        assert exit_code == 0

        # Verify all files are included
        content = output_file.read_text()
        for filename, file_content in special_files:
            assert filename in content, f"File '{filename}' not found"
            assert file_content in content, f"Content for '{filename}' not found"

    @pytest.mark.unit
    def test_nested_directory_depth(
        self, run_m1f, create_test_directory_structure, temp_dir
    ):
        """Test handling of deeply nested directory structures."""
        # Create deeply nested structure
        structure = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "level5": {
                                "level6": {
                                    "deep.txt": "Deep file content",
                                }
                            }
                        }
                    }
                }
            },
            "shallow.txt": "Shallow file content",
        }

        source_dir = create_test_directory_structure(structure)
        output_file = temp_dir / "nested_output.txt"

        exit_code, _ = run_m1f(
            [
                "--source-directory",
                str(source_dir),
                "--output-file",
                str(output_file),
                "--force",
            ]
        )

        assert exit_code == 0

        # Verify both shallow and deep files are included
        content = output_file.read_text()
        assert "shallow.txt" in content
        assert "deep.txt" in content
        assert "Deep file content" in content
        assert "Shallow file content" in content

    @pytest.mark.unit
    def test_gitignore_edge_cases(
        self, run_m1f, create_test_directory_structure, temp_dir
    ):
        """Test edge cases in gitignore pattern matching."""
        structure = {
            ".gitignore": """
# Comments should be ignored
*.log
!important.log
build/
**/temp/
*.tmp

# Negation patterns
!keep.tmp

# Directory patterns
node_modules/
.git/

# Wildcards
test_*.py
!test_keep.py
""",
            "debug.log": "Debug log",
            "important.log": "Important log",
            "file.tmp": "Temp file",
            "keep.tmp": "Keep this temp",
            "test_remove.py": "Remove this test",
            "test_keep.py": "Keep this test",
            "build": {
                "output.txt": "Build output",
            },
            "src": {
                "temp": {
                    "cache.txt": "Cache file",
                },
                "main.py": "Main source",
            },
        }

        source_dir = create_test_directory_structure(structure)
        output_file = temp_dir / "gitignore_edge_output.txt"

        # Run with actual gitignore file
        exit_code, _ = run_m1f(
            [
                "--source-directory",
                str(source_dir),
                "--output-file",
                str(output_file),
                "--use-gitignore",
                "--force",
            ]
        )

        assert exit_code == 0

        content = output_file.read_text()

        # Should be excluded
        assert "debug.log" not in content
        assert "file.tmp" not in content
        assert "test_remove.py" not in content
        assert "Build output" not in content
        assert "Cache file" not in content

        # Should be included (negation patterns)
        assert "important.log" in content
        assert "keep.tmp" in content
        assert "test_keep.py" in content
        assert "Main source" in content

    @pytest.mark.unit
    def test_concurrent_file_modifications(
        self, run_m1f, create_test_file, temp_dir, monkeypatch
    ):
        """Test handling when files are modified during processing."""
        source_dir = temp_dir / "concurrent_test"
        source_dir.mkdir()

        # Create initial files
        file1 = create_test_file("concurrent_test/file1.txt", "Initial content 1")
        file2 = create_test_file("concurrent_test/file2.txt", "Initial content 2")

        # Mock to simulate file change during processing
        original_open = open
        call_count = 0

        def mock_open(file, *args, **kwargs):
            nonlocal call_count
            call_count += 1

            # Modify file2 after file1 is read
            if call_count == 2 and str(file).endswith("file1.txt"):
                file2.write_text("Modified content 2")

            return original_open(file, *args, **kwargs)

        monkeypatch.setattr("builtins.open", mock_open)

        output_file = temp_dir / "concurrent_output.txt"

        # Run m1f
        exit_code, _ = run_m1f(
            [
                "--source-directory",
                str(source_dir),
                "--output-file",
                str(output_file),
                "--force",
            ]
        )

        assert exit_code == 0

        # The output should contain the content as it was when read
        content = output_file.read_text()
        assert "Initial content 1" in content

    @pytest.mark.unit
    def test_circular_directory_references(self, run_m1f, temp_dir, is_windows):
        """Test handling of circular directory references (symlinks)."""
        if is_windows:
            pytest.skip("Circular symlink test requires Unix-like system")

        source_dir = temp_dir / "circular_test"
        source_dir.mkdir()

        # Create subdirectory
        subdir = source_dir / "subdir"
        subdir.mkdir()

        # Create circular symlink
        circular_link = subdir / "circular"
        circular_link.symlink_to(source_dir)

        # Create a test file
        create_test_file("circular_test/test.txt", "Test content")

        output_file = temp_dir / "circular_output.txt"

        # Run m1f - should handle circular reference gracefully
        exit_code, _ = run_m1f(
            [
                "--source-directory",
                str(source_dir),
                "--output-file",
                str(output_file),
                "--force",
            ]
        )

        # Should complete without infinite loop
        assert exit_code == 0

        # Should include the test file
        content = output_file.read_text()
        assert "test.txt" in content
        assert "Test content" in content
