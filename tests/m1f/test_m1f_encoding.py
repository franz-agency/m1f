"""Encoding-related tests for m1f."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from ..base_test import BaseM1FTest


class TestM1FEncoding(BaseM1FTest):
    """Tests for m1f encoding handling."""

    @pytest.mark.unit
    @pytest.mark.encoding
    def test_encoding_conversion_utf8(self, run_m1f, create_test_file, temp_dir):
        """Test encoding conversion from various encodings to UTF-8."""
        # Create files with different encodings
        test_files = [
            ("utf8.txt", "UTF-8 content: Hello 世界", "utf-8"),
            ("latin1.txt", "Latin-1 content: café", "latin-1"),
            ("utf16.txt", "UTF-16 content: привет", "utf-16"),
        ]

        source_dir = temp_dir / "encoding_test"
        source_dir.mkdir()

        print(f"\n=== DEBUG: Creating test files in {source_dir} ===")
        created_files = []
        for filename, content, encoding in test_files:
            file_path = source_dir / filename
            file_path.write_text(content, encoding=encoding)
            file_size = file_path.stat().st_size
            print(f"Created {filename}: {file_size} bytes, encoding={encoding}")
            created_files.append(file_path)

        # List all files in directory
        print(f"\n=== DEBUG: Files in source directory ===")
        for f in source_dir.iterdir():
            print(f"  {f.name}: {f.stat().st_size} bytes")

        output_file = temp_dir / "encoding_output.txt"

        # Run with UTF-8 target encoding (default) with verbose output
        print(f"\n=== DEBUG: Running m1f with verbose output ===")
        exit_code, log_output = run_m1f(
            [
                "--source-directory",
                str(source_dir),
                "--output-file",
                str(output_file),
                "--include-binary-files",
                "--force",
                "--verbose",
            ]
        )

        print(f"\n=== DEBUG: m1f output ===")
        print(log_output)

        assert exit_code == 0

        # Verify all content is properly encoded in UTF-8
        content = output_file.read_text(encoding="utf-8")
        
        print(f"\n=== DEBUG: Output file size: {output_file.stat().st_size} bytes ===")
        print(f"\n=== DEBUG: Checking for content in output ===")
        
        # Check what files are mentioned in the output
        for filename in ["utf8.txt", "latin1.txt", "utf16.txt"]:
            if filename in content:
                print(f"  ✓ Found {filename} in output")
            else:
                print(f"  ✗ {filename} NOT found in output")

        assert "UTF-8 content: Hello 世界" in content
        assert "Latin-1 content: café" in content
        assert "UTF-16 content: привет" in content

    @pytest.mark.unit
    @pytest.mark.encoding
    def test_target_encoding_option(self, run_m1f, create_test_file, temp_dir):
        """Test specifying target encoding for output."""
        # Create a file with special characters
        test_content = "Special chars: áéíóú ñ €"
        test_file = create_test_file("special.txt", test_content)

        # Test different target encodings
        encodings = ["utf-8", "latin-1", "cp1252"]

        for target_encoding in encodings:
            output_file = temp_dir / f"output_{target_encoding}.txt"

            exit_code, _ = run_m1f(
                [
                    "--source-directory",
                    str(test_file.parent),
                    "--output-file",
                    str(output_file),
                    "--convert-to-charset",
                    target_encoding,
                    "--force",
                ]
            )

            # Skip if encoding not supported on this system
            if exit_code != 0:
                continue

            # Read with the target encoding to verify
            try:
                content = output_file.read_text(encoding=target_encoding)
                # Basic check that file is readable in target encoding
                assert "FILE:" in content or "==== FILE:" in content
            except UnicodeDecodeError:
                pytest.fail(f"Output file not properly encoded in {target_encoding}")

    @pytest.mark.unit
    @pytest.mark.encoding
    def test_encoding_errors_handling(self, run_m1f, temp_dir):
        """Test handling of encoding errors."""
        source_dir = temp_dir / "encoding_errors"
        source_dir.mkdir()

        # Create a file with mixed/broken encoding
        broken_file = source_dir / "broken.txt"
        # Write raw bytes that will cause encoding issues
        broken_file.write_bytes(
            b"Valid UTF-8: Hello\n" b"Invalid UTF-8: \xff\xfe\n" b"More valid text\n"
        )

        output_file = temp_dir / "encoding_errors_output.txt"

        # Run m1f - should handle encoding errors gracefully
        exit_code, _ = run_m1f(
            [
                "--source-directory",
                str(source_dir),
                "--output-file",
                str(output_file),
                "--include-binary-files",
                "--force",
            ]
        )

        # Should succeed despite encoding issues
        assert exit_code == 0
        assert output_file.exists()

        # Check that valid content is preserved
        content = output_file.read_text(encoding="utf-8", errors="replace")
        assert "Valid UTF-8: Hello" in content
        assert "More valid text" in content

    @pytest.mark.unit
    @pytest.mark.encoding
    def test_machinereadable_encoding_metadata(
        self, run_m1f, create_test_file, temp_dir
    ):
        """Test that MachineReadable format includes encoding metadata."""
        # Create files with different encodings
        source_dir = temp_dir / "encoding_metadata"
        source_dir.mkdir()

        files = [
            ("utf8.txt", "UTF-8 text", "utf-8"),
            ("latin1.txt", "Latin-1 text", "latin-1"),
        ]

        for filename, content, encoding in files:
            (source_dir / filename).write_text(content, encoding=encoding)

        output_file = temp_dir / "encoding_metadata.txt"

        # Run with MachineReadable separator
        exit_code, _ = run_m1f(
            [
                "--source-directory",
                str(source_dir),
                "--output-file",
                str(output_file),
                "--separator-style",
                "MachineReadable",
                "--include-binary-files",
                "--force",
            ]
        )

        assert exit_code == 0

        # Check that encoding information is in metadata
        content = output_file.read_text()
        assert '"encoding":' in content
        # Should detect and record the original encodings
        assert '"utf-8"' in content or '"utf8"' in content

    @pytest.mark.unit
    @pytest.mark.encoding
    def test_bom_handling(self, run_m1f, temp_dir):
        """Test handling of Byte Order Mark (BOM) in files."""
        source_dir = temp_dir / "bom_test"
        source_dir.mkdir()

        # Create file with UTF-8 BOM
        bom_file = source_dir / "with_bom.txt"
        bom_file.write_bytes(b"\xef\xbb\xbf" + "BOM file content".encode("utf-8"))

        # Create file without BOM
        no_bom_file = source_dir / "no_bom.txt"
        no_bom_file.write_text("No BOM file content")

        output_file = temp_dir / "bom_output.txt"

        exit_code, _ = run_m1f(
            [
                "--source-directory",
                str(source_dir),
                "--output-file",
                str(output_file),
                "--include-binary-files",
                "--force",
            ]
        )

        assert exit_code == 0

        # Both files should be processed correctly
        content = output_file.read_text()
        assert "BOM file content" in content
        assert "No BOM file content" in content

        # The BOM should not appear as content
        assert "\ufeff" not in content  # BOM as Unicode character

    @pytest.mark.unit
    @pytest.mark.encoding
    def test_exotic_encodings(self, run_m1f, temp_dir):
        """Test handling of less common encodings."""
        source_dir = temp_dir / "exotic_encodings"
        source_dir.mkdir()

        # Test various encodings if available
        test_encodings = [
            ("japanese.txt", "日本語テキスト", "shift_jis"),
            ("chinese.txt", "中文文本", "gb2312"),
            ("korean.txt", "한국어 텍스트", "euc-kr"),
            ("cyrillic.txt", "Русский текст", "koi8-r"),
        ]

        created_files = []
        for filename, content, encoding in test_encodings:
            try:
                file_path = source_dir / filename
                file_path.write_text(content, encoding=encoding)
                created_files.append((filename, content))
            except (LookupError, UnicodeEncodeError):
                # Skip if encoding not available on this system
                continue

        if not created_files:
            pytest.skip("No exotic encodings available on this system")

        output_file = temp_dir / "exotic_output.txt"

        exit_code, _ = run_m1f(
            [
                "--source-directory",
                str(source_dir),
                "--output-file",
                str(output_file),
                "--include-binary-files",
                "--force",
            ]
        )

        assert exit_code == 0

        # Verify content is preserved
        content = output_file.read_text(encoding="utf-8")
        for filename, expected_content in created_files:
            assert (
                expected_content in content
            ), f"Content from {filename} not properly converted"

    @pytest.mark.integration
    @pytest.mark.encoding
    def test_mixed_encodings_in_directory(
        self, run_m1f, create_test_directory_structure, temp_dir
    ):
        """Test processing directory with mixed file encodings."""
        # Create a complex structure with different encodings
        source_dir = temp_dir / "mixed_encodings"
        source_dir.mkdir()

        # UTF-8 files
        (source_dir / "readme.md").write_text(
            "# Project README\nUTF-8 encoded", encoding="utf-8"
        )

        # Latin-1 files
        (source_dir / "legacy.txt").write_text(
            "Legacy file: café, naïve", encoding="latin-1"
        )

        # Create subdirectory with more files
        subdir = source_dir / "src"
        subdir.mkdir()
        (subdir / "main.py").write_text(
            "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\nprint('Hello')",
            encoding="utf-8",
        )

        output_file = temp_dir / "mixed_output.txt"

        exit_code, log_output = run_m1f(
            [
                "--source-directory",
                str(source_dir),
                "--output-file",
                str(output_file),
                "--include-binary-files",
                "--verbose",
                "--force",
            ]
        )

        assert exit_code == 0

        # Verify all files are included with correct content
        content = output_file.read_text(encoding="utf-8")

        assert "# Project README" in content
        assert "UTF-8 encoded" in content
        assert "Legacy file: café, naïve" in content
        assert "#!/usr/bin/env python3" in content
        assert "print('Hello')" in content
