"""Integration and CLI tests for m1f."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from ..base_test import BaseM1FTest


class TestM1FIntegration(BaseM1FTest):
    """Integration tests for m1f."""
    
    @pytest.mark.integration
    def test_command_line_execution(
        self,
        m1f_cli_runner,
        m1f_source_dir,
        temp_dir
    ):
        """Test executing m1f from command line."""
        output_file = temp_dir / "cli_output.txt"
        
        result = m1f_cli_runner([
            "--source-directory", str(m1f_source_dir),
            "--output-file", str(output_file),
            "--force",
            "--verbose",
        ])
        
        # Check successful execution
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        
        # Check outputs created
        assert output_file.exists()
        assert (output_file.parent / f"{output_file.stem}.log").exists()
        assert (output_file.parent / f"{output_file.stem}_filelist.txt").exists()
        assert (output_file.parent / f"{output_file.stem}_dirlist.txt").exists()
        
        # Check verbose output
        assert result.stdout or result.stderr, "No output from verbose mode"
    
    @pytest.mark.integration
    def test_input_paths_file_integration(
        self,
        run_m1f,
        create_test_directory_structure,
        temp_dir
    ):
        """Test using input paths file with various path formats."""
        # Create test structure
        structure = {
            "project1": {
                "src": {
                    "main.py": "print('Project 1')",
                    "utils.py": "# Utils for project 1",
                },
                "docs": {
                    "README.md": "# Project 1",
                },
            },
            "project2": {
                "lib": {
                    "core.py": "# Core library",
                },
                "tests": {
                    "test_core.py": "# Tests",
                },
            },
            "shared": {
                "config.json": '{"shared": true}',
            },
        }
        
        base_dir = create_test_directory_structure(structure)
        
        # Create input paths file with different path types
        input_paths = temp_dir / "paths.txt"
        input_paths.write_text(f"""
# Comments should be ignored
{base_dir / 'project1' / 'src'}
{base_dir / 'project2' / 'lib' / 'core.py'}
{base_dir / 'shared'}

# Blank lines should be ignored

# Glob patterns
{base_dir / 'project1' / 'docs' / '*.md'}
""")
        
        output_file = temp_dir / "paths_integration.txt"
        
        exit_code, _ = run_m1f([
            "--input-paths-file", str(input_paths),
            "--output-file", str(output_file),
            "--force",
        ])
        
        assert exit_code == 0
        
        content = output_file.read_text()
        
        # Should include specified paths
        assert "main.py" in content
        assert "utils.py" in content
        assert "core.py" in content
        assert "config.json" in content
        assert "README.md" in content
        
        # Should not include excluded paths
        assert "test_core.py" not in content
    
    @pytest.mark.integration
    def test_multiple_glob_patterns(
        self,
        run_m1f,
        create_test_directory_structure,
        temp_dir
    ):
        """Test using multiple glob patterns."""
        structure = {
            "src": {
                "module1.py": "# Module 1",
                "module2.py": "# Module 2",
                "test_module1.py": "# Test 1",
                "test_module2.py": "# Test 2",
                "config.yaml": "# Config",
            },
            "docs": {
                "api.md": "# API",
                "guide.md": "# Guide",
                "internal.txt": "# Internal",
            },
            "scripts": {
                "build.sh": "#!/bin/bash",
                "deploy.py": "# Deploy script",
            },
        }
        
        base_dir = create_test_directory_structure(structure)
        output_file = temp_dir / "glob_patterns.txt"
        
        # Use multiple glob patterns
        exit_code, _ = run_m1f([
            "--input-paths",
            str(base_dir / "src" / "module*.py"),
            str(base_dir / "docs" / "*.md"),
            str(base_dir / "scripts" / "*.py"),
            "--output-file", str(output_file),
            "--force",
        ])
        
        assert exit_code == 0
        
        content = output_file.read_text()
        
        # Should include matched files
        assert "module1.py" in content
        assert "module2.py" in content
        assert "api.md" in content
        assert "guide.md" in content
        assert "deploy.py" in content
        
        # Should exclude non-matched files
        assert "test_module1.py" not in content
        assert "config.yaml" not in content
        assert "internal.txt" not in content
        assert "build.sh" not in content
    
    @pytest.mark.integration
    def test_gitignore_with_excludes_combination(
        self,
        run_m1f,
        create_test_directory_structure,
        temp_dir
    ):
        """Test combining gitignore patterns with explicit excludes."""
        structure = {
            ".gitignore": """
*.log
build/
temp/
""",
            "src": {
                "main.py": "# Main",
                "debug.log": "Debug log",
                "error.log": "Error log",
            },
            "build": {
                "output.txt": "Build output",
            },
            "temp": {
                "cache.txt": "Cache",
            },
            "docs": {
                "README.md": "# README",
                "notes.txt": "Notes",
            },
        }
        
        base_dir = create_test_directory_structure(structure)
        output_file = temp_dir / "combined_excludes.txt"
        
        # Run with gitignore and additional excludes
        exit_code, _ = run_m1f([
            "--source-directory", str(base_dir),
            "--output-file", str(output_file),
            "--use-gitignore",
            "--excludes", "*.txt",
            "--force",
        ])
        
        assert exit_code == 0
        
        content = output_file.read_text()
        
        # Should include
        assert "main.py" in content
        assert "README.md" in content
        
        # Should exclude (from gitignore)
        assert "debug.log" not in content
        assert "error.log" not in content
        assert "Build output" not in content
        assert "Cache" not in content
        
        # Should exclude (from --excludes)
        assert "notes.txt" not in content
    
    @pytest.mark.integration
    def test_complex_filtering_scenario(
        self,
        run_m1f,
        create_test_directory_structure,
        temp_dir
    ):
        """Test complex filtering with multiple options."""
        structure = {
            "project": {
                "src": {
                    "main.py": "# Main app",
                    "utils.py": "# Utilities",
                    "test_main.py": "# Tests",
                    "config.json": '{"app": "config"}',
                    "README.md": "# Source readme",
                },
                "docs": {
                    "api.md": "# API docs",
                    "guide.pdf": b"PDF content",
                    "examples.py": "# Examples",
                },
                "build": {
                    "output.txt": "Build output",
                },
                ".git": {
                    "config": "Git config",
                },
                "data": {
                    "sample.csv": "a,b,c\n1,2,3",
                    "cache.tmp": "Temp cache",
                },
            },
        }
        
        base_dir = create_test_directory_structure(structure)
        output_file = temp_dir / "complex_filter.txt"
        
        # Complex filtering
        exit_code, _ = run_m1f([
            "--source-directory", str(base_dir),
            "--output-file", str(output_file),
            "--include-extensions", "py", "md",  # Only Python and Markdown
            "--exclude-extensions", "tmp",       # But not temp files
            "--excludes", "test_*",              # Exclude test files
            "--no-default-excludes",             # Include .git
            "--force",
        ])
        
        assert exit_code == 0
        
        content = output_file.read_text()
        
        # Should include
        assert "main.py" in content
        assert "utils.py" in content
        assert "README.md" in content
        assert "api.md" in content
        assert "examples.py" in content
        
        # Should exclude
        assert "test_main.py" not in content  # Excluded by pattern
        assert "config.json" not in content    # Not in include extensions
        assert "guide.pdf" not in content      # Not in include extensions
        assert "sample.csv" not in content     # Not in include extensions
        assert "cache.tmp" not in content      # Excluded extension
        assert "output.txt" not in content     # Not in include extensions
        
        # .git included (no default excludes)
        assert "Git config" in content
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_performance_with_many_files(
        self,
        run_m1f,
        create_test_file,
        temp_dir
    ):
        """Test performance with many small files."""
        source_dir = temp_dir / "many_files"
        source_dir.mkdir()
        
        # Create many small files
        num_files = 100
        for i in range(num_files):
            subdir = source_dir / f"dir_{i // 10}"
            subdir.mkdir(exist_ok=True)
            create_test_file(
                f"many_files/dir_{i // 10}/file_{i}.txt",
                f"Content of file {i}\n" * 10
            )
        
        output_file = temp_dir / "many_files_output.txt"
        
        import time
        start_time = time.time()
        
        exit_code, _ = run_m1f([
            "--source-directory", str(source_dir),
            "--output-file", str(output_file),
            "--force",
        ])
        
        elapsed = time.time() - start_time
        
        assert exit_code == 0
        assert output_file.exists()
        
        # Check all files are included
        content = output_file.read_text()
        for i in range(num_files):
            assert f"file_{i}.txt" in content
        
        # Performance check (should be reasonably fast)
        assert elapsed < 30, f"Processing {num_files} files took too long: {elapsed:.2f}s"
        
        print(f"Processed {num_files} files in {elapsed:.2f} seconds")
    
    @pytest.mark.integration
    def test_archive_creation_integration(
        self,
        run_m1f,
        create_test_directory_structure,
        temp_dir
    ):
        """Test archive creation with various options."""
        structure = {
            "src": {
                "main.py": "# Main",
                "lib": {
                    "utils.py": "# Utils",
                },
            },
            "docs": {
                "README.md": "# Docs",
            },
            "tests": {
                "test_main.py": "# Tests",
            },
        }
        
        base_dir = create_test_directory_structure(structure)
        
        # Test ZIP archive with filtering
        output_zip = temp_dir / "filtered.txt"
        exit_code, _ = run_m1f([
            "--source-directory", str(base_dir),
            "--output-file", str(output_zip),
            "--create-archive", "zip",
            "--exclude-extensions", "py",
            "--force",
        ])
        
        assert exit_code == 0
        
        # Check archive created
        zip_file = output_zip.with_suffix('.zip')
        assert zip_file.exists()
        
        # Verify archive contents
        import zipfile
        with zipfile.ZipFile(zip_file, 'r') as zf:
            names = zf.namelist()
            # Only README.md should be in archive (Python files excluded)
            assert any("README.md" in name for name in names)
            assert not any(".py" in name for name in names) 