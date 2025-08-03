#!/usr/bin/env python3
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
Tests for symlink deduplication handling in m1f.

Tests the three scenarios:
1. With --allow-duplicate-files: All symlinks preserved with their paths
2. Without --allow-duplicate-files + symlink points INSIDE: Symlink excluded
3. Without --allow-duplicate-files + symlink points OUTSIDE: Symlink included
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
import subprocess
import platform

# Add the parent directory to sys.path to import m1f
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestSymlinkDeduplication(unittest.TestCase):
    """Test symlink deduplication logic in m1f."""

    def setUp(self):
        """Set up test directory structure with internal and external symlinks."""
        # Skip on platforms that don't support symlinks
        self.can_create_symlinks = True

        # Create a temporary directory for the test
        self.temp_dir = tempfile.mkdtemp(prefix="m1f_symlink_dedup_test_")
        self.original_dir = os.getcwd()

        # Create test directory structure
        self.source_dir = Path(self.temp_dir) / "source"
        self.source_dir.mkdir(parents=True)

        self.external_dir = Path(self.temp_dir) / "external"
        self.external_dir.mkdir(parents=True)

        # Create files in source directory
        self.file1 = self.source_dir / "file1.txt"
        self.file1.write_text("Content of file1")

        self.subdir = self.source_dir / "subdir"
        self.subdir.mkdir()
        self.file2 = self.subdir / "file2.txt"
        self.file2.write_text("Content of file2")

        # Create file in external directory
        self.file3 = self.external_dir / "file3.txt"
        self.file3.write_text("Content of file3")

        try:
            # Create internal symlink (points to file within source)
            self.symlink_internal = self.source_dir / "symlink_internal.txt"
            self.symlink_internal.symlink_to(self.file1)

            # Create external symlink (points to file outside source)
            self.symlink_external = self.source_dir / "symlink_external.txt"
            self.symlink_external.symlink_to(self.file3)

        except (OSError, NotImplementedError):
            self.can_create_symlinks = False

    def tearDown(self):
        """Clean up temporary directories."""
        os.chdir(self.original_dir)
        try:
            import shutil

            shutil.rmtree(self.temp_dir)
        except Exception:
            pass

    def test_symlinks_with_allow_duplicates(self):
        """Test that with --allow-duplicate-files, all symlinks are included."""
        if not self.can_create_symlinks:
            self.skipTest("Symlink creation not supported")

        os.chdir(self.temp_dir)

        output_file = Path(self.temp_dir) / "output_allow_dupes.txt"
        result = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).parent.parent.parent / "tools" / "m1f.py"),
                "--source-directory",
                str(self.source_dir),
                "--output-file",
                str(output_file),
                "--force",
                "--include-symlinks",
                "--allow-duplicate-files",
            ],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, f"m1f failed: {result.stderr}")

        content = output_file.read_text()

        # All files should be included
        self.assertIn("file1.txt", content)
        self.assertIn("file2.txt", content)

        # Both symlinks should be included with --allow-duplicate-files
        self.assertIn(
            "symlink_internal.txt",
            content,
            "Internal symlink should be included with --allow-duplicate-files",
        )
        self.assertIn(
            "symlink_external.txt", content, "External symlink should be included"
        )

        # The external target content should be included via the symlink
        # (file3.txt won't appear as a separate entry since it's outside source dir)
        self.assertIn("Content of file3", content)

    def test_symlinks_without_allow_duplicates(self):
        """Test that without --allow-duplicate-files, only external symlinks are included."""
        if not self.can_create_symlinks:
            self.skipTest("Symlink creation not supported")

        os.chdir(self.temp_dir)

        output_file = Path(self.temp_dir) / "output_no_dupes.txt"
        result = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).parent.parent.parent / "tools" / "m1f.py"),
                "--source-directory",
                str(self.source_dir),
                "--output-file",
                str(output_file),
                "--force",
                "--include-symlinks",
                # NOT including --allow-duplicate-files
            ],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, f"m1f failed: {result.stderr}")

        content = output_file.read_text()

        # Original files should be included
        self.assertIn("file1.txt", content)
        self.assertIn("file2.txt", content)

        # Internal symlink should NOT be included (points to file1.txt which is already included)
        self.assertNotIn(
            "symlink_internal.txt",
            content,
            "Internal symlink should NOT be included without --allow-duplicate-files",
        )

        # External symlink SHOULD be included (points outside source directory)
        self.assertIn(
            "symlink_external.txt",
            content,
            "External symlink should be included even without --allow-duplicate-files",
        )

        # The external target content should be included via the symlink
        # (file3.txt won't appear as a separate entry since it's outside source dir)
        self.assertIn("Content of file3", content)

    def test_no_symlinks_flag(self):
        """Test that without --include-symlinks, no symlinks are included."""
        if not self.can_create_symlinks:
            self.skipTest("Symlink creation not supported")

        os.chdir(self.temp_dir)

        output_file = Path(self.temp_dir) / "output_no_symlinks.txt"
        result = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).parent.parent.parent / "tools" / "m1f.py"),
                "--source-directory",
                str(self.source_dir),
                "--output-file",
                str(output_file),
                "--force",
                # NOT including --include-symlinks
            ],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, f"m1f failed: {result.stderr}")

        content = output_file.read_text()

        # Original files should be included
        self.assertIn("file1.txt", content)
        self.assertIn("file2.txt", content)

        # No symlinks should be included
        self.assertNotIn("symlink_internal.txt", content)
        self.assertNotIn("symlink_external.txt", content)

        # External file should not be included either
        self.assertNotIn("file3.txt", content)


if __name__ == "__main__":
    unittest.main()
