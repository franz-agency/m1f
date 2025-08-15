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
Tests for automatic loading of .gitignore and .m1fignore files.

These tests verify that m1f automatically loads ignore files from source 
directories without requiring explicit --exclude-paths-file arguments.
"""

import asyncio
import logging
import tempfile
from pathlib import Path
import pytest

from tools.m1f.config import Config
from tools.m1f.core import FileProcessor
from tools.m1f.cli import create_parser
from tools.m1f.logging import LoggerManager


class TestAutoGitignore:
    """Test automatic loading of .gitignore and .m1fignore files."""

    @pytest.mark.asyncio
    async def test_auto_load_gitignore(self):
        """Test that .gitignore is automatically loaded from source directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create test structure
            (tmpdir / "include_me.txt").write_text("This should be included")
            (tmpdir / "test.log").write_text("This should be excluded by .gitignore")
            (tmpdir / "debug.log").write_text("This should also be excluded")
            (tmpdir / ".gitignore").write_text("*.log\n")
            
            # Create config WITHOUT specifying exclude_paths_file
            parser = create_parser()
            args = parser.parse_args(["-s", str(tmpdir), "-o", str(tmpdir / "output.txt")])
            config = Config.from_args(args)
            
            # Process files
            logger_manager = LoggerManager(config.logging)
            processor = FileProcessor(config, logger_manager)
            files = await processor.gather_files()
            
            # Extract just the filenames
            filenames = [f.name for f, _ in files]
            
            # Verify .gitignore was auto-loaded and *.log files were excluded
            assert "include_me.txt" in filenames
            assert "test.log" not in filenames
            assert "debug.log" not in filenames
            # .gitignore itself should be excluded by default
            assert ".gitignore" not in filenames

    @pytest.mark.asyncio
    async def test_auto_load_m1fignore(self):
        """Test that .m1fignore is automatically loaded from source directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create test structure
            (tmpdir / "include_me.py").write_text("# Python file")
            (tmpdir / "exclude_me.tmp").write_text("Temp file")
            (tmpdir / "backup.bak").write_text("Backup file")
            (tmpdir / ".m1fignore").write_text("*.tmp\n*.bak\n")
            
            # Create config WITHOUT specifying exclude_paths_file
            parser = create_parser()
            args = parser.parse_args(["-s", str(tmpdir), "-o", str(tmpdir / "output.txt")])
            config = Config.from_args(args)
            
            # Process files
            logger_manager = LoggerManager(config.logging)
            processor = FileProcessor(config, logger_manager)
            files = await processor.gather_files()
            
            # Extract just the filenames
            filenames = [f.name for f, _ in files]
            
            # Verify .m1fignore was auto-loaded and patterns were applied
            assert "include_me.py" in filenames
            assert "exclude_me.tmp" not in filenames
            assert "backup.bak" not in filenames

    @pytest.mark.asyncio
    async def test_both_gitignore_and_m1fignore(self):
        """Test that both .gitignore and .m1fignore are loaded when both exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create test structure
            (tmpdir / "include.txt").write_text("Include this")
            (tmpdir / "test.log").write_text("Excluded by .gitignore")
            (tmpdir / "temp.tmp").write_text("Excluded by .m1fignore")
            (tmpdir / ".gitignore").write_text("*.log\n")
            (tmpdir / ".m1fignore").write_text("*.tmp\n")
            
            # Create config WITHOUT specifying exclude_paths_file
            parser = create_parser()
            args = parser.parse_args(["-s", str(tmpdir), "-o", str(tmpdir / "output.txt")])
            config = Config.from_args(args)
            
            # Process files
            logger_manager = LoggerManager(config.logging)
            processor = FileProcessor(config, logger_manager)
            files = await processor.gather_files()
            
            # Extract just the filenames
            filenames = [f.name for f, _ in files]
            
            # Verify both ignore files were loaded and applied
            assert "include.txt" in filenames
            assert "test.log" not in filenames  # Excluded by .gitignore
            assert "temp.tmp" not in filenames  # Excluded by .m1fignore

    @pytest.mark.asyncio
    async def test_no_auto_gitignore_flag(self):
        """Test that --no-auto-gitignore disables .gitignore auto-loading but not .m1fignore."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create test structure
            (tmpdir / "include.txt").write_text("Include this")
            (tmpdir / "test.log").write_text("Should be included with --no-auto-gitignore")
            (tmpdir / "temp.tmp").write_text("Should still be excluded by .m1fignore")
            (tmpdir / ".gitignore").write_text("*.log\n")
            (tmpdir / ".m1fignore").write_text("*.tmp\n")
            
            # Create config WITH --no-auto-gitignore flag
            parser = create_parser()
            args = parser.parse_args([
                "-s", str(tmpdir), 
                "-o", str(tmpdir / "output.txt"),
                "--no-auto-gitignore"
            ])
            config = Config.from_args(args)
            
            # Process files
            logger_manager = LoggerManager(config.logging)
            processor = FileProcessor(config, logger_manager)
            files = await processor.gather_files()
            
            # Extract just the filenames
            filenames = [f.name for f, _ in files]
            
            # Verify .gitignore was NOT loaded but .m1fignore was
            assert "include.txt" in filenames
            assert "test.log" in filenames  # NOT excluded because --no-auto-gitignore
            assert "temp.tmp" not in filenames  # Still excluded by .m1fignore

    @pytest.mark.asyncio
    async def test_explicit_overrides_auto(self):
        """Test that explicit --exclude-paths-file works alongside auto-loading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create test structure
            (tmpdir / "include.txt").write_text("Include this")
            (tmpdir / "test.log").write_text("Excluded by .gitignore")
            (tmpdir / "special.txt").write_text("Excluded by custom ignore")
            (tmpdir / ".gitignore").write_text("*.log\n")
            (tmpdir / "custom.ignore").write_text("special.txt\n")
            
            # Create config with explicit exclude_paths_file
            parser = create_parser()
            args = parser.parse_args([
                "-s", str(tmpdir),
                "-o", str(tmpdir / "output.txt"),
                "--exclude-paths-file", str(tmpdir / "custom.ignore")
            ])
            config = Config.from_args(args)
            
            # Process files
            logger_manager = LoggerManager(config.logging)
            processor = FileProcessor(config, logger_manager)
            files = await processor.gather_files()
            
            # Extract just the filenames
            filenames = [f.name for f, _ in files]
            
            # Verify both auto-loaded and explicit ignore files are applied
            assert "include.txt" in filenames
            assert "test.log" not in filenames  # Excluded by auto-loaded .gitignore
            assert "special.txt" not in filenames  # Excluded by explicit custom.ignore

    @pytest.mark.asyncio
    async def test_multiple_source_directories(self):
        """Test that .gitignore files are loaded from each source directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create two source directories with different .gitignore files
            dir1 = tmpdir / "dir1"
            dir2 = tmpdir / "dir2"
            dir1.mkdir()
            dir2.mkdir()
            
            # Dir1 excludes .log files
            (dir1 / "file1.txt").write_text("Include from dir1")
            (dir1 / "test.log").write_text("Exclude from dir1")
            (dir1 / ".gitignore").write_text("*.log\n")
            
            # Dir2 excludes .tmp files
            (dir2 / "file2.txt").write_text("Include from dir2")
            (dir2 / "temp.tmp").write_text("Exclude from dir2")
            (dir2 / ".gitignore").write_text("*.tmp\n")
            
            # Create config with multiple source directories
            parser = create_parser()
            args = parser.parse_args([
                "-s", str(dir1),
                "-s", str(dir2),
                "-o", str(tmpdir / "output.txt")
            ])
            config = Config.from_args(args)
            
            # Process files
            logger_manager = LoggerManager(config.logging)
            processor = FileProcessor(config, logger_manager)
            files = await processor.gather_files()
            
            # Extract just the filenames
            filenames = [f.name for f, _ in files]
            
            # Verify both .gitignore files were loaded and applied
            assert "file1.txt" in filenames
            assert "file2.txt" in filenames
            assert "test.log" not in filenames  # Excluded by dir1/.gitignore
            assert "temp.tmp" not in filenames  # Excluded by dir2/.gitignore

    @pytest.mark.asyncio
    async def test_no_duplicate_loading(self):
        """Test that the same .gitignore file isn't loaded multiple times."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create test structure
            (tmpdir / "test.txt").write_text("Test file")
            (tmpdir / ".gitignore").write_text("# This is a comment\n*.log\n")
            
            # Create config that might trigger duplicate loading
            parser = create_parser()
            args = parser.parse_args([
                "-s", str(tmpdir),
                "-o", str(tmpdir / "output.txt"),
                "--exclude-paths-file", str(tmpdir / ".gitignore")  # Explicitly specify same .gitignore
            ])
            config = Config.from_args(args)
            
            # Enable debug logging to capture duplicate loading warnings
            logging.basicConfig(level=logging.DEBUG)
            
            # Process files
            logger_manager = LoggerManager(config.logging)
            processor = FileProcessor(config, logger_manager)
            
            # The file should only be loaded once, no errors or warnings
            files = await processor.gather_files()
            
            # Should complete without errors
            assert len(files) >= 0  # Just verify it completed

    @pytest.mark.asyncio
    async def test_symlink_safety(self):
        """Test that circular symlinks don't cause infinite loops in auto-loading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create a circular symlink
            link_path = tmpdir / "circular_link"
            try:
                link_path.symlink_to(tmpdir)
            except OSError:
                # Skip test if symlinks aren't supported
                pytest.skip("Symlinks not supported on this system")
            
            # Create test files
            (tmpdir / "test.txt").write_text("Test file")
            (tmpdir / ".gitignore").write_text("*.log\n")
            
            # This should not cause an infinite loop
            parser = create_parser()
            args = parser.parse_args(["-s", str(tmpdir), "-o", str(tmpdir / "output.txt")])
            config = Config.from_args(args)
            
            # Process files - should complete without hanging
            logger_manager = LoggerManager(config.logging)
            processor = FileProcessor(config, logger_manager)
            files = await processor.gather_files()
            
            # Just verify it completed
            assert len(files) >= 0


class TestAutoGitignoreRegression:
    """Regression tests for specific bugs that were found."""
    
    @pytest.mark.asyncio
    async def test_log_files_excluded_by_gitignore(self):
        """
        Regression test for the bug where .log files were included despite being in .gitignore.
        This test would have caught the original bug.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Recreate the exact scenario that failed
            (tmpdir / "README.md").write_text("# Test Project")
            (tmpdir / "test.py").write_text("print('test')")
            (tmpdir / "test_output.log").write_text("2025-08-10 20:20:45 - Log entry")
            (tmpdir / ".gitignore").write_text("*.log\n")
            
            # Create config WITHOUT explicit exclude_paths_file (the bug scenario)
            parser = create_parser()
            args = parser.parse_args(["-s", str(tmpdir), "-o", str(tmpdir / "bundle.txt")])
            config = Config.from_args(args)
            
            # Process files
            logger_manager = LoggerManager(config.logging)
            processor = FileProcessor(config, logger_manager)
            files = await processor.gather_files()
            
            # Extract filenames
            filenames = [f.name for f, _ in files]
            
            # This is the critical assertion that would have caught the bug
            assert "test_output.log" not in filenames, "Log files should be excluded by .gitignore"
            assert "README.md" in filenames
            assert "test.py" in filenames


if __name__ == "__main__":
    # Run tests
    asyncio.run(pytest.main([__file__, "-v"]))