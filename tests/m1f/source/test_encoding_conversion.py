
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
    # The generated test lives one directory above this script, so no
    # extra "source" segment is needed when referencing the fixture
    # directory.
    test_dir = Path(__file__).parent / "exotic_encodings"
    output_dir = Path(__file__).parent / "output"
    output_file = output_dir / "test_encoding_utf16le.txt"
    
    # Create output dir if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    # Define encoding map for verification
    encoding_map = {
        "shiftjis.txt": "shift_jis",
        "big5.txt": "big5", 
        "koi8r.txt": "koi8_r",
        "iso8859-8.txt": "iso8859_8",
        "euckr.txt": "euc_kr",
        "windows1256.txt": "cp1256",
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
        "--minimal-output"
    ]
    
    # Modify sys.argv for testing
    old_argv = sys.argv
    sys.argv = ["m1f.py"] + test_args
    
    try:
        # Run m1f with the test arguments
        m1f.main()
        
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
        for encoding in encoding_map.values():
            assert f'"encoding": "{encoding}"' in content, f"Encoding {encoding} not detected correctly"
            
    finally:
        # Restore sys.argv
        sys.argv = old_argv
        
        # Clean up output file
        if output_file.exists():
            try:
                output_file.unlink()
            except:
                pass
                
    # The test passes if we get here without assertions failing
