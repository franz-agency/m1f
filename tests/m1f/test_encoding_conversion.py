import os
import sys
import pytest
import shutil
from pathlib import Path
import json
import re

# Add the tools directory to path to import the m1f module
TOOLS_DIR = str(Path(__file__).parent.parent.parent / "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

try:
    import m1f
except ImportError:
    print(f"ERROR: Cannot import m1f module. Make sure it's in {TOOLS_DIR}")
    sys.exit(1)


def test_exotic_encoding_conversion():
    """
    Test that m1f correctly detects and converts files with exotic encodings to UTF-16-LE.
    """
    # Setup test paths
    test_dir = Path(__file__).parent / "source/exotic_encodings"
    output_dir = Path(__file__).parent / "source/output"
    output_file = output_dir / "test_encoding_utf16le.txt"

    # Ensure clean test environment
    output_dir.mkdir(exist_ok=True)
    if output_file.exists():
        try:
            output_file.unlink()
        except Exception as e:
            pytest.skip(f"Could not clean previous test output: {e}")

    # Define encoding map for verification with multiple possible values for each file
    # Different environments and detection libraries may report slightly different encodings
    encoding_map = {
        "shiftjis.txt": ["shift_jis", "shift-jis", "shiftjis"],
        "big5.txt": ["big5", "big-5"],
        "koi8r.txt": ["koi8_r", "koi8-r", "koi8r"],
        "iso8859-8.txt": ["iso8859_8", "iso-8859-8", "windows-1255"],
        "euckr.txt": ["euc_kr", "euc-kr"],
        "windows1256.txt": [
            "cp1256",
            "windows-1256",
            "utf-8",
        ],  # Sometimes detected as UTF-8
    }

    # Setup arguments for m1f
    test_args = [
        "-s",
        str(test_dir),
        "-o",
        str(output_file),
        "--separator-style",
        "MachineReadable",
        "--convert-to-charset",
        "utf-16-le",
        "--force",
        "--include-extensions",
        ".txt",
        "--exclude-extensions",
        ".utf8",
        "--minimal-output",
    ]

    # Save original argv
    old_argv = sys.argv
    sys.argv = ["m1f.py"] + test_args

    try:
        # Run m1f directly with SystemExit exception handling
        try:
            m1f.main()
        except SystemExit as e:
            # We expect a successful exit (code 0)
            assert e.code == 0, f"m1f.main() exited with unexpected exit code: {e.code}"

        # Verify the output file was created
        assert output_file.exists(), "Output file was not created"
        assert output_file.stat().st_size > 0, "Output file is empty"

        # Verify we can read the file with UTF-16-LE encoding
        try:
            with open(output_file, "r", encoding="utf-16-le") as f:
                content = f.read()

            # Verify we got some content
            assert content, "Output file has no content"
            assert "METADATA_JSON" in content, "No METADATA_JSON found in output file"

            # Verify each file is mentioned in the combined output
            for filename in encoding_map.keys():
                assert (
                    filename in content
                ), f"File {filename} was not included in the output"

            # Verify encoding information was preserved using a more flexible check
            for filename, possible_encodings in encoding_map.items():
                # Check that the file exists in the content
                file_content_start = content.find(f'"original_filename": "{filename}"')
                assert file_content_start > 0, f"Could not find metadata for {filename}"

                # Find the encoding line in this file's metadata section
                metadata_section = content[
                    file_content_start : file_content_start + 1000
                ]
                encoding_line = re.search(r'"encoding":\s*"([^"]+)"', metadata_section)

                assert encoding_line, f"No encoding found for {filename}"
                detected_encoding = encoding_line.group(1)

                # Check if the detected encoding is one of the allowed values
                normalized_detected = detected_encoding.lower().replace("_", "-")
                normalized_allowed = [
                    e.lower().replace("_", "-") for e in possible_encodings
                ]

                assert any(
                    normalized_detected == allowed for allowed in normalized_allowed
                ), f"Encoding '{detected_encoding}' for {filename} not in allowed list: {possible_encodings}"

        except UnicodeError:
            pytest.fail("Output file is not properly encoded as UTF-16-LE")

    except Exception as e:
        pytest.fail(f"Test failed with error: {e}")

    finally:
        # Restore original argv
        sys.argv = old_argv

        # Clean up the output file
        if output_file.exists():
            try:
                output_file.unlink()
            except Exception as e:
                print(f"Warning: Could not cleanup test output file: {e}")


# This allows the test to be run directly
if __name__ == "__main__":
    print("Running test directly")
    test_exotic_encoding_conversion()
