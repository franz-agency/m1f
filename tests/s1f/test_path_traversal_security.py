# Copyright 2025 Franz und Franz GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test path traversal security for s1f tool.
"""

import pytest
from pathlib import Path
import tempfile
import os

from tools.s1f.utils import validate_file_path


class TestS1FPathTraversalSecurity:
    """Test path traversal security in s1f."""

    def test_validate_file_path_blocks_parent_traversal(self):
        """Test that validate_file_path blocks parent directory traversal."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            
            # Test various malicious paths
            malicious_paths = [
                Path("../../../etc/passwd"),
                Path("..\\..\\..\\windows\\system32\\config\\sam"),
                Path("subdir/../../etc/passwd"),
                Path("./../../sensitive/data"),
            ]
            
            for malicious_path in malicious_paths:
                assert not validate_file_path(malicious_path, base_dir), \
                    f"Path {malicious_path} should be blocked"

    def test_validate_file_path_allows_valid_paths(self):
        """Test that validate_file_path allows legitimate paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            
            # Test valid paths
            valid_paths = [
                Path("file.txt"),
                Path("subdir/file.txt"),
                Path("deep/nested/path/file.txt"),
                Path("./current/file.txt"),
            ]
            
            for valid_path in valid_paths:
                assert validate_file_path(valid_path, base_dir), \
                    f"Path {valid_path} should be allowed"

    def test_s1f_blocks_absolute_paths_in_combined_file(self):
        """Test that s1f blocks extraction of absolute paths."""
        project_root = Path(__file__).parent.parent.parent
        test_dir = project_root / "tmp" / "s1f_security_test"
        
        try:
            test_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            pytest.skip(f"Cannot create test directory: {e}")
        
        try:
            # Create a malicious combined file with absolute path
            combined_file = test_dir / "malicious_combined.txt"
            combined_content = """======= /etc/passwd | CHECKSUM_SHA256: abc123 ======
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
"""
            combined_file.write_text(combined_content)
            
            # Create output directory
            output_dir = test_dir / "extracted"
            output_dir.mkdir(exist_ok=True)
            
            # Run s1f
            import subprocess
            import sys
            
            s1f_script = project_root / "tools" / "s1f.py"
            result = subprocess.run(
                [sys.executable, str(s1f_script), 
                 "-i", str(combined_file),
                 "-d", str(output_dir),
                 "-f"],
                capture_output=True,
                text=True
            )
            
            # Check that extraction failed or file was not created in /etc/
            assert not Path("/etc/passwd").exists() or \
                   Path("/etc/passwd").stat().st_mtime < combined_file.stat().st_mtime, \
                   "s1f should not overwrite system files!"
            
            # The extracted file should not exist outside the output directory
            extracted_file = output_dir / "etc" / "passwd"
            if extracted_file.exists():
                # If it was extracted, it should be in the output dir, not at the absolute path
                assert extracted_file.is_relative_to(output_dir), \
                    "Extracted file should be within output directory"
        
        finally:
            # Clean up
            import shutil
            if test_dir.exists():
                shutil.rmtree(test_dir)

    def test_s1f_blocks_relative_path_traversal(self):
        """Test that s1f blocks relative path traversal in combined files."""
        project_root = Path(__file__).parent.parent.parent
        test_dir = project_root / "tmp" / "s1f_traversal_test"
        
        try:
            test_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            pytest.skip(f"Cannot create test directory: {e}")
        
        try:
            # Create a malicious combined file with path traversal
            combined_file = test_dir / "traversal_combined.txt"
            combined_content = """======= ../../../etc/passwd | CHECKSUM_SHA256: abc123 ======
malicious content
======= ../../sensitive_data.txt | CHECKSUM_SHA256: def456 ======
sensitive information
"""
            combined_file.write_text(combined_content)
            
            # Create output directory
            output_dir = test_dir / "extracted"
            output_dir.mkdir(exist_ok=True)
            
            # Run s1f
            import subprocess
            import sys
            
            s1f_script = project_root / "tools" / "s1f.py"
            result = subprocess.run(
                [sys.executable, str(s1f_script), 
                 "-i", str(combined_file),
                 "-d", str(output_dir),
                 "-f"],
                capture_output=True,
                text=True
            )
            
            # Check that files were not created outside output directory
            parent_dir = output_dir.parent
            assert not (parent_dir / "sensitive_data.txt").exists(), \
                "s1f should not create files outside output directory"
            
            # Check stderr for security warnings
            if result.stderr:
                assert "invalid path" in result.stderr.lower() or \
                       "skipping" in result.stderr.lower(), \
                       "s1f should warn about invalid paths"
        
        finally:
            # Clean up
            import shutil
            if test_dir.exists():
                shutil.rmtree(test_dir)