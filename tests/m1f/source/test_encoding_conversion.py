import os
import sys
import pytest
from pathlib import Path

# Add the tools directory to path to import the m1f module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))
import m1f

def test_exotic_encoding_conversion():
    """Test that m1f correctly detects and converts files with exotic encodings using UTF-16-LE."""
    # Paths for test resources
    test_dir = Path(__file__).parent / "exotic_encodings"
    output_dir = Path(__file__).parent / "output"
    output_file = output_dir / "test_encoding_utf16le.txt"
    
    # Create output dir if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    # Define encoding map for verification
    encoding_map = {
        "shiftjis.txt": "shift_jis",
        "big5.txt": "big5",
        "koi8r.txt": "koi8-r",
        "iso8859-8.txt": "windows-1255",
        "euckr.txt": "euc-kr",
        "windows1256.txt": "utf-8",
    }
    
    # Setup test args for m1f
    test_args = [
        "--source-directory", str(test_dir),
        "--output-file", str(output_file),
        "--separator-style", "MachineReadable",
        "--convert-to-charset", "utf-16-le",
        "--force",
        "--include-extensions", ".txt",
        "--exclude-extensions", ".utf8",
        "--minimal-output",
        "--verbose"
    ]
    
    # Modify sys.argv for testing
    old_argv = sys.argv
    sys.argv = ["m1f.py"] + test_args
    
    try:
        # Run m1f with the test arguments
        with pytest.raises(SystemExit) as excinfo:
            m1f.main()
        
        assert excinfo.value.code == 0, "m1f.main() did not exit with code 0"
        
        # Verify the output file exists
        assert output_file.exists(), "Output file was not created"
        assert output_file.stat().st_size > 0, "Output file is empty"
        
        # Check that the file contains encoding info for each test file
        with open(output_file, "r", encoding="utf-16-le") as f:
            content = f.read()
            
        # Verify each file is mentioned in the combined output
        for filename in encoding_map.keys():
            assert filename in content, f"File {filename} was not included in the output"
            
        # Verify encoding information was preserved
        for filename, expected_encoding in encoding_map.items():
            assert f'"original_filename": "{filename}"' in content, f"Metadata for {filename} not found or filename mismatch"
            
            # Find the metadata block for the current file to check its encoding
            # This is a simplified way to ensure we're checking the correct block.
            # A more robust approach would parse the JSON, but this works for current structure.
            file_metadata_start_index = content.find(f'"original_filename": "{filename}"')
            assert file_metadata_start_index != -1, f"Could not find metadata for {filename}"
            
            # Rough estimate of where this file's metadata block ends (next file's start, or end of content)
            next_block_marker = "--- PYMK1F_BEGIN_FILE_METADATA_BLOCK_"
            metadata_block_end_index = content.find(next_block_marker, file_metadata_start_index + len(f'"original_filename": "{filename}"'))
            if metadata_block_end_index == -1:
                metadata_block_end_index = len(content)
                
            current_file_metadata_block = content[file_metadata_start_index:metadata_block_end_index]

            assert f'"encoding": "{expected_encoding}"' in current_file_metadata_block, f"Encoding {expected_encoding} for {filename} not detected correctly in its metadata block. Found: {current_file_metadata_block}"
            
            # Specific check for windows1256.txt which should have encoding errors
            if filename == "windows1256.txt":
                assert '"had_encoding_errors": true' in current_file_metadata_block, f"Expected 'had_encoding_errors: true' for {filename}"
            
    finally:
        # Restore sys.argv
        sys.argv = old_argv
        
        # Clean up output file
        if output_file.exists():
            try:
                output_file.unlink()
            except Exception:
                pass
                
    # The test passes if we get here without assertions failing
