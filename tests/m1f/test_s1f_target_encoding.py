#!/usr/bin/env python3
"""
Test script for s1f.py's new --target-encoding parameter.
This tests that we can explicitly specify the output encoding regardless of the original encoding.
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

# Add parent directory to path so we can import tools directly
sys.path.append(str(Path(__file__).parent.parent.parent))
from tools import m1f, s1f

def test_target_encoding():
    """Test the --target-encoding parameter of s1f.py."""
    # Setup test directories
    script_dir = Path(__file__).parent
    test_output_dir = script_dir / "output"
    test_output_dir.mkdir(exist_ok=True)
    
    # Create a temporary file with mixed-encoding content
    test_content = "Hello with special chars: äöüß привет こんにちは 你好"
    combined_file = test_output_dir / "encoding_test.txt"
    
    # Write the temporary file using UTF-8 encoding first
    with open(combined_file, "w", encoding="utf-8") as f:
        # Add a detailed separator for our test file
        separator = """========================================================================================
== FILE: test_file.txt
== DATE: 2023-06-15 14:30:21 | SIZE: 2.50 KB | TYPE: .txt
== ENCODING: latin-1 (with conversion errors)
========================================================================================

"""
        f.write(separator + test_content)
    
    # Use s1f to extract with various encoding options
    extract_base_dir = script_dir / "extracted" / "encoding_test"
    
    # Test case 1: Default behavior (UTF-8 output)
    extract_dir_default = extract_base_dir / "default"
    try:
        subprocess.run([
            sys.executable,
            str(Path(__file__).parent.parent.parent / "tools" / "s1f.py"),
            "--input-file", str(combined_file),
            "--destination-directory", str(extract_dir_default),
            "--force"
        ], check=True)
        
        # Verify the output file exists and is UTF-8 encoded
        extracted_file = extract_dir_default / "test_file.txt"
        assert extracted_file.exists(), "Extracted file does not exist"
        
        # Try to open with UTF-8 encoding (should succeed)
        with open(extracted_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert content == test_content, "Content mismatch in default UTF-8 mode"
        
        # Try to open with Latin-1 (might fail with some characters)
        try:
            with open(extracted_file, "r", encoding="latin-1") as f:
                latin1_content = f.read()
            # If we read it as Latin-1, it will be different from the original
            assert latin1_content != test_content, "File should be in UTF-8, not Latin-1"
        except UnicodeDecodeError:
            # Expected error when trying to read UTF-8 as Latin-1
            pass
    except Exception as e:
        assert False, f"Default extraction failed: {e}"
    
    # Test case 2: --respect-encoding flag
    # This should use Latin-1 because we faked that in the metadata
    extract_dir_respect = extract_base_dir / "respect_encoding"
    try:
        subprocess.run([
            sys.executable,
            str(Path(__file__).parent.parent.parent / "tools" / "s1f.py"),
            "--input-file", str(combined_file),
            "--destination-directory", str(extract_dir_respect),
            "--force",
            "--respect-encoding"
        ], check=True)
        
        # Verify the output file exists
        extracted_file = extract_dir_respect / "test_file.txt"
        assert extracted_file.exists(), "Extracted file does not exist"
        
        # Try to read with Latin-1 (should succeed if respect-encoding worked)
        try:
            with open(extracted_file, "r", encoding="latin-1") as f:
                content = f.read()
            
            # Content might be mangled now since we're using Latin-1 for a UTF-8 source
            # So we just check the file is different from the UTF-8 version
            with open(extract_dir_default / "test_file.txt", "r", encoding="utf-8") as f:
                utf8_content = f.read()
            
            # Compare binary data since the text representations might be invalid
            with open(extracted_file, "rb") as f:
                latin1_binary = f.read()
            with open(extract_dir_default / "test_file.txt", "rb") as f:
                utf8_binary = f.read()
                
            # The encodings should produce different binary content
            assert latin1_binary != utf8_binary, "Respect-encoding mode didn't change the encoding"
        except Exception as e:
            assert False, f"Reading Latin-1 file failed: {e}"
    except Exception as e:
        assert False, f"Respect-encoding extraction failed: {e}"
    
    # Test case 3: Explicit --target-encoding parameter overrides metadata
    extract_dir_target = extract_base_dir / "target_encoding"
    try:
        subprocess.run([
            sys.executable,
            str(Path(__file__).parent.parent.parent / "tools" / "s1f.py"),
            "--input-file", str(combined_file),
            "--destination-directory", str(extract_dir_target),
            "--force",
            "--respect-encoding",  # This would normally use latin-1 from metadata
            "--target-encoding", "utf-16-le"  # But this should override it
        ], check=True)
        
        # Verify the output file exists
        extracted_file = extract_dir_target / "test_file.txt"
        assert extracted_file.exists(), "Extracted file does not exist"
        
        # Try to read with UTF-16-LE (should succeed if target-encoding worked)
        try:
            with open(extracted_file, "r", encoding="utf-16-le") as f:
                content = f.read()
                assert content == test_content, "Content mismatch in target-encoding mode"
            
            # Using a different encoding should fail or produce incorrect results
            try:
                with open(extracted_file, "r", encoding="utf-8") as f:
                    utf8_content = f.read()
                # UTF-16-LE read as UTF-8 should result in gibberish or errors
                assert utf8_content != test_content, "File should be in UTF-16-LE, not UTF-8"
            except UnicodeDecodeError:
                # Expected error when trying to read UTF-16-LE as UTF-8
                pass
        except Exception as e:
            assert False, f"Reading UTF-16-LE file failed: {e}"
    except Exception as e:
        assert False, f"Target-encoding extraction failed: {e}"
        
    print("\nAll tests passed! The --target-encoding parameter works correctly.")

if __name__ == "__main__":
    test_target_encoding() 