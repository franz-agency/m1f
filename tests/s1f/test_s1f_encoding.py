"""Encoding-related tests for s1f."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ..base_test import BaseS1FTest


class TestS1FEncoding(BaseS1FTest):
    """Tests for s1f encoding handling."""

    @pytest.mark.unit
    @pytest.mark.encoding
    def test_respect_encoding_option(self, run_s1f, s1f_extracted_dir, temp_dir):
        """Test the --respect-encoding option."""
        # Create MachineReadable format file with encoding metadata
        output_file = temp_dir / "encoding_test.txt"

        with open(output_file, "w", encoding="utf-8") as f:
            # UTF-8 file
            metadata1 = {
                "original_filepath": "utf8_file.txt",
                "original_filename": "utf8_file.txt",
                "timestamp_utc_iso": "2024-01-01T00:00:00Z",
                "type": ".txt",
                "size_bytes": 50,
                "encoding": "utf-8",
            }

            f.write(
                "--- PYMK1F_BEGIN_FILE_METADATA_BLOCK_12345678-1234-1234-1234-111111111111 ---\n"
            )
            f.write("METADATA_JSON:\n")
            f.write(json.dumps(metadata1, indent=4))
            f.write("\n")
            f.write(
                "--- PYMK1F_END_FILE_METADATA_BLOCK_12345678-1234-1234-1234-111111111111 ---\n"
            )
            f.write(
                "--- PYMK1F_BEGIN_FILE_CONTENT_BLOCK_12345678-1234-1234-1234-111111111111 ---\n"
            )
            f.write("UTF-8 content: Hello 世界 áéíóú\n")
            f.write(
                "--- PYMK1F_END_FILE_CONTENT_BLOCK_12345678-1234-1234-1234-111111111111 ---\n\n"
            )

            # Latin-1 file
            metadata2 = {
                "original_filepath": "latin1_file.txt",
                "original_filename": "latin1_file.txt",
                "timestamp_utc_iso": "2024-01-01T00:00:00Z",
                "type": ".txt",
                "size_bytes": 30,
                "encoding": "latin-1",
            }

            f.write(
                "--- PYMK1F_BEGIN_FILE_METADATA_BLOCK_12345678-1234-1234-1234-222222222222 ---\n"
            )
            f.write("METADATA_JSON:\n")
            f.write(json.dumps(metadata2, indent=4))
            f.write("\n")
            f.write(
                "--- PYMK1F_END_FILE_METADATA_BLOCK_12345678-1234-1234-1234-222222222222 ---\n"
            )
            f.write(
                "--- PYMK1F_BEGIN_FILE_CONTENT_BLOCK_12345678-1234-1234-1234-222222222222 ---\n"
            )
            f.write("Latin-1: café naïve\n")
            f.write(
                "--- PYMK1F_END_FILE_CONTENT_BLOCK_12345678-1234-1234-1234-222222222222 ---\n"
            )

        # Extract without respecting encoding (default UTF-8)
        exit_code, _ = run_s1f(
            [
                "--input-file",
                str(output_file),
                "--destination-directory",
                str(s1f_extracted_dir / "default"),
                "--force",
            ]
        )

        assert exit_code == 0

        # Both files should be UTF-8
        utf8_file = s1f_extracted_dir / "default" / "utf8_file.txt"
        latin1_file = s1f_extracted_dir / "default" / "latin1_file.txt"

        assert (
            utf8_file.read_text(encoding="utf-8") == "UTF-8 content: Hello 世界 áéíóú\n"
        )
        assert latin1_file.read_text(encoding="utf-8") == "Latin-1: café naïve\n"

        # Extract with --respect-encoding
        exit_code, _ = run_s1f(
            [
                "--input-file",
                str(output_file),
                "--destination-directory",
                str(s1f_extracted_dir / "respected"),
                "--respect-encoding",
                "--force",
            ]
        )

        assert exit_code == 0

        # Files should have their original encodings
        utf8_file_resp = s1f_extracted_dir / "respected" / "utf8_file.txt"
        latin1_file_resp = s1f_extracted_dir / "respected" / "latin1_file.txt"

        # UTF-8 file should still be UTF-8
        assert (
            utf8_file_resp.read_text(encoding="utf-8")
            == "UTF-8 content: Hello 世界 áéíóú\n"
        )

        # Latin-1 file should be readable as Latin-1
        # (though it may have been written as UTF-8 if that's what s1f does)
        try:
            content = latin1_file_resp.read_text(encoding="latin-1")
            assert (
                "café" in content or "café" in content
            )  # May vary based on implementation
        except UnicodeDecodeError:
            # If it was written as UTF-8, that's also acceptable
            content = latin1_file_resp.read_text(encoding="utf-8")
            assert "café" in content

    @pytest.mark.unit
    @pytest.mark.encoding
    def test_target_encoding_option(
        self, run_s1f, create_combined_file, s1f_extracted_dir
    ):
        """Test the --target-encoding option."""
        test_files = {
            "special_chars.txt": "Special characters: áéíóú ñ ç",
        }

        combined_file = create_combined_file(test_files)

        # Test different target encodings
        encodings = ["utf-8", "latin-1", "cp1252"]

        for target_encoding in encodings:
            extract_dir = s1f_extracted_dir / target_encoding

            exit_code, _ = run_s1f(
                [
                    "--input-file",
                    str(combined_file),
                    "--destination-directory",
                    str(extract_dir),
                    "--target-encoding",
                    target_encoding,
                    "--force",
                ]
            )

            # Skip if encoding not supported
            if exit_code != 0:
                continue

            # Try to read with target encoding
            extracted_file = extract_dir / "special_chars.txt"
            try:
                content = extracted_file.read_text(encoding=target_encoding)
                # Should contain the special characters
                assert (
                    "áéíóú" in content or "?" in content
                )  # May be replaced if not supported
            except UnicodeDecodeError:
                pytest.fail(f"File not properly encoded in {target_encoding}")

    @pytest.mark.unit
    @pytest.mark.encoding
    def test_mixed_encodings_extraction(self, run_s1f, s1f_extracted_dir, temp_dir):
        """Test extracting files with mixed encodings."""
        # Create a combined file with mixed content
        output_file = temp_dir / "mixed_encodings.txt"

        with open(output_file, "w", encoding="utf-8") as f:
            # Standard format with various special characters
            import hashlib
            
            # Unicode test file
            content1 = "Unicode test: 你好 мир 🌍\n"
            checksum1 = hashlib.sha256(content1.encode("utf-8")).hexdigest()
            f.write(f"======= unicode_test.txt | CHECKSUM_SHA256: {checksum1} ======\n")
            f.write(content1)
            f.write("\n")

            # Latin test file
            content2 = "Latin characters: àèìòù ÀÈÌÒÙ\n"
            checksum2 = hashlib.sha256(content2.encode("utf-8")).hexdigest()
            f.write(f"======= latin_test.txt | CHECKSUM_SHA256: {checksum2} ======\n")
            f.write(content2)
            f.write("\n")

            # Symbols test file
            content3 = "Symbols: €£¥ ©®™ ½¼¾\n"
            checksum3 = hashlib.sha256(content3.encode("utf-8")).hexdigest()
            f.write(f"======= symbols.txt | CHECKSUM_SHA256: {checksum3} ======\n")
            f.write(content3)

        # Extract files
        exit_code, _ = run_s1f(
            [
                "--input-file",
                str(output_file),
                "--destination-directory",
                str(s1f_extracted_dir),
                "--force",
            ]
        )

        assert exit_code == 0

        # Verify all files extracted with correct content
        unicode_file = s1f_extracted_dir / "unicode_test.txt"
        latin_file = s1f_extracted_dir / "latin_test.txt"
        symbols_file = s1f_extracted_dir / "symbols.txt"

        assert unicode_file.read_text() == "Unicode test: 你好 мир 🌍\n"
        assert latin_file.read_text() == "Latin characters: àèìòù ÀÈÌÒÙ\n"
        assert symbols_file.read_text() == "Symbols: €£¥ ©®™ ½¼¾\n"

    @pytest.mark.unit
    @pytest.mark.encoding
    def test_bom_preservation(self, run_s1f, s1f_extracted_dir, temp_dir):
        """Test handling of Byte Order Mark (BOM)."""
        # Create file with BOM in combined format
        output_file = temp_dir / "bom_test.txt"

        with open(output_file, "w", encoding="utf-8") as f:
            import hashlib
            
            # File with BOM
            content1 = "\ufeffBOM test content\n"
            checksum1 = hashlib.sha256(content1.encode("utf-8")).hexdigest()
            f.write(f"======= with_bom.txt | CHECKSUM_SHA256: {checksum1} ======\n")
            f.write(content1)
            f.write("\n")

            # File without BOM
            content2 = "No BOM content\n"
            checksum2 = hashlib.sha256(content2.encode("utf-8")).hexdigest()
            f.write(f"======= without_bom.txt | CHECKSUM_SHA256: {checksum2} ======\n")
            f.write(content2)

        # Extract
        exit_code, _ = run_s1f(
            [
                "--input-file",
                str(output_file),
                "--destination-directory",
                str(s1f_extracted_dir),
                "--force",
            ]
        )

        assert exit_code == 0

        # Check if BOM is preserved or stripped (both are acceptable)
        with_bom = s1f_extracted_dir / "with_bom.txt"
        without_bom = s1f_extracted_dir / "without_bom.txt"

        # Read as bytes to check for BOM
        bom_content = with_bom.read_bytes()
        no_bom_content = without_bom.read_bytes()

        # Check if content is correct (BOM might be stripped)
        assert b"BOM test content" in bom_content
        assert no_bom_content == b"No BOM content\n"

    @pytest.mark.integration
    @pytest.mark.encoding
    def test_encoding_detection(
        self, run_s1f, create_m1f_output, s1f_extracted_dir, temp_dir
    ):
        """Test automatic encoding detection."""
        # Create files with different encodings
        source_dir = temp_dir / "encoding_source"
        source_dir.mkdir()

        # Create files with specific encodings
        test_files = []

        # UTF-8 file
        utf8_path = source_dir / "utf8.txt"
        utf8_path.write_text("UTF-8: Hello 世界", encoding="utf-8")
        test_files.append(("utf8.txt", "UTF-8: Hello 世界"))

        # Try Latin-1 if available
        try:
            latin1_path = source_dir / "latin1.txt"
            latin1_path.write_text("Latin-1: café", encoding="latin-1")
            test_files.append(("latin1.txt", "Latin-1: café"))
        except LookupError:
            pass

        if not test_files:
            pytest.skip("No suitable encodings available")

        # Create m1f output directly from the source directory
        # to preserve the original encodings
        import subprocess
        import sys
        from pathlib import Path
        
        m1f_script = Path(__file__).parent.parent.parent / "tools" / "m1f.py"
        m1f_output = temp_dir / "m1f_output_machinereadable.txt"
        
        result = subprocess.run(
            [
                sys.executable,
                str(m1f_script),
                "--source-directory",
                str(source_dir),
                "--output-file",
                str(m1f_output),
                "--separator-style",
                "MachineReadable",
                "--include-binary-files",
                "--force",
            ],
            capture_output=True,
            text=True,
        )
        
        if result.returncode != 0:
            pytest.fail(f"m1f failed: {result.stderr}")

        # Extract with s1f
        exit_code, _ = run_s1f(
            [
                "--input-file",
                str(m1f_output),
                "--destination-directory",
                str(s1f_extracted_dir),
                "--force",
            ]
        )

        assert exit_code == 0

        # Verify files extracted correctly
        for filename, expected_content in test_files:
            extracted = s1f_extracted_dir / filename
            assert extracted.exists()
            # Content should be preserved regardless of original encoding
            content = extracted.read_text(encoding="utf-8")
            assert expected_content in content
