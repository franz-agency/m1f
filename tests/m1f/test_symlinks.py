#!/usr/bin/env python3
"""
Tests for symlink handling in m1f.py.

These tests create symlinks at runtime, test the symlink handling functionality,
and clean up afterwards.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
import shutil
import subprocess
import platform

# Add the parent directory to sys.path to import m1f
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from tools.m1f import _detect_symlink_cycles


class TestSymlinkHandling(unittest.TestCase):
    """Test symlink handling in m1f."""

    def setUp(self):
        """Set up temporary directory structure with symlinks for testing."""
        # Skip on platforms that don't support symlinks (e.g., Windows without admin)
        self.can_create_symlinks = True
        
        # Create a temporary directory for the test
        self.temp_dir = tempfile.mkdtemp(prefix="m1f_symlink_test_")
        self.original_dir = os.getcwd()
        
        # Create test directory structure
        self.source_dir = Path(self.temp_dir) / "source"
        self.source_dir.mkdir()
        
        # Create a few subdirectories
        self.dir1 = self.source_dir / "dir1"
        self.dir1.mkdir()
        
        self.dir2 = self.source_dir / "dir2"
        self.dir2.mkdir()
        
        self.dir3 = self.dir1 / "dir3"
        self.dir3.mkdir()
        
        # Create some test files
        self.file1 = self.dir1 / "file1.txt"
        self.file1.write_text("This is file1.txt")
        
        self.file2 = self.dir2 / "file2.txt"
        self.file2.write_text("This is file2.txt")
        
        self.file3 = self.dir3 / "file3.txt"
        self.file3.write_text("This is file3.txt")
        
        # Try to create the symlinks
        try:
            # Create a symlink to dir3 from dir2
            self.symlink_dir = self.dir2 / "symlink_to_dir3"
            os.symlink(str(self.dir3), str(self.symlink_dir), target_is_directory=True)
            
            # Create a symlink to file1 from dir2
            self.symlink_file = self.dir2 / "symlink_to_file1.txt"
            os.symlink(str(self.file1), str(self.symlink_file))
            
            # Create a circular symlink
            self.circular_dir = self.dir3 / "circular"
            os.symlink(str(self.dir1), str(self.circular_dir), target_is_directory=True)
        except (OSError, PermissionError) as e:
            print(f"Warning: Could not create symlinks - {e}")
            self.can_create_symlinks = False
    
    def tearDown(self):
        """Clean up the temporary directory after the test."""
        # Change back to the original directory before removing temporary directory
        os.chdir(self.original_dir)
        
        # Clean up
        try:
            shutil.rmtree(self.temp_dir)
        except (OSError, PermissionError) as e:
            print(f"Warning: Could not clean up temporary directory - {e}")
            
    def test_detect_symlink_cycles(self):
        """Test the _detect_symlink_cycles function."""
        if not self.can_create_symlinks:
            self.skipTest("Symlink creation not supported on this platform or user doesn't have permission")
        
        # Test a non-symlink (should not find cycle)
        is_cycle, visited = _detect_symlink_cycles(self.file1)
        self.assertFalse(is_cycle)
        
        # Test a normal symlink (should not find cycle)
        is_cycle, visited = _detect_symlink_cycles(self.symlink_file)
        self.assertFalse(is_cycle)
        
        # Test a directory symlink (should not find cycle)
        is_cycle, visited = _detect_symlink_cycles(self.symlink_dir)
        self.assertFalse(is_cycle)
        
        # Test a circular symlink (should find cycle)
        is_cycle, visited = _detect_symlink_cycles(self.circular_dir)
        self.assertTrue(is_cycle)
        
    def test_m1f_with_symlinks(self):
        """Test m1f.py with --include-symlinks flag."""
        if not self.can_create_symlinks:
            self.skipTest("Symlink creation not supported on this platform or user doesn't have permission")
        
        # Change to the temp directory
        os.chdir(self.temp_dir)
        
        # Use subprocess to run m1f.py with and without --include-symlinks
        
        # 1. First without --include-symlinks (should exclude symlinks)
        output_file1 = Path(self.temp_dir) / "output_no_symlinks.txt"
        result = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).parent.parent.parent / "tools" / "m1f.py"),
                "--source-directory", str(self.source_dir),
                "--output-file", str(output_file1),
                "--force"
            ],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Check the output file exists
        self.assertTrue(output_file1.exists())
        
        # Read content to ensure symlinks weren't included
        content = output_file1.read_text()
        self.assertIn("file1.txt", content)  # Normal file should be included
        self.assertIn("file2.txt", content)  # Normal file should be included
        self.assertIn("file3.txt", content)  # Normal file should be included
        self.assertNotIn("symlink_to_file1.txt", content)  # Symlink file should be excluded
        
        # 2. Now with --include-symlinks (should include non-circular symlinks)
        output_file2 = Path(self.temp_dir) / "output_with_symlinks.txt"
        result = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).parent.parent.parent / "tools" / "m1f.py"),
                "--source-directory", str(self.source_dir),
                "--output-file", str(output_file2),
                "--force",
                "--include-symlinks",
                "--verbose"  # Added for debugging
            ],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Check the output file exists
        self.assertTrue(output_file2.exists())
        
        # Read content to ensure normal symlinks were included but circular ones weren't
        content = output_file2.read_text()
        self.assertIn("file1.txt", content)  # Normal file should be included
        self.assertIn("file2.txt", content)  # Normal file should be included
        self.assertIn("file3.txt", content)  # Normal file should be included
        self.assertIn("symlink_to_file1.txt", content)  # Symlink file should be included
        
        # Print lines containing file3.txt for debugging
        print("\nLines containing file3.txt:")
        file3_paths = []
        for i, line in enumerate(content.splitlines()):
            if "file3.txt" in line:
                print(f"Line {i+1}: {line[:100]}...")
                # If the line contains "FILE: " it's a file path in the header
                if "FILE: " in line:
                    file_path = line.split("FILE: ")[1].split()[0]
                    if file_path not in file3_paths:
                        file3_paths.append(file_path)
        
        print(f"Unique file3.txt paths: {file3_paths}")
        
        # Nach unserer Änderung sollte file3.txt nur einmal erscheinen, da Dateien jetzt
        # anhand ihres physischen Speicherorts dedupliziert werden
        self.assertEqual(len(file3_paths), 1, f"Expected exactly 1 path to file3.txt, but got {len(file3_paths)}: {file3_paths}")
        
        # Prüfen, dass einer der möglichen Pfade vorhanden ist
        expected_paths = ["dir1/dir3/file3.txt", "dir2/symlink_to_dir3/file3.txt"]
        self.assertTrue(any(path in file3_paths[0] for path in expected_paths), 
                        f"Expected one of {expected_paths} in {file3_paths[0]}")


if __name__ == "__main__":
    unittest.main() 