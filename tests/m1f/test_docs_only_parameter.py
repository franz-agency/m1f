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

"""Tests for --docs-only parameter functionality."""

from __future__ import annotations

from pathlib import Path

import pytest

from ..base_test import BaseM1FTest


class TestDocsOnlyParameter(BaseM1FTest):
    """Test --docs-only parameter functionality."""

    @pytest.fixture
    def test_files_dir(self, temp_dir):
        """Create test files with various extensions."""
        files_dir = temp_dir / "test_docs_only"
        files_dir.mkdir()
        
        # Documentation files (should be included)
        doc_files = [
            "README.md",
            "guide.txt",
            "api.rst",
            "manual.adoc",
            "CHANGELOG.md",
            "notes.mkd",
            "tutorial.markdown",
            "help.1",  # man page
            "config.5",  # man page section 5
            "overview.pod",
            "reference.rdoc",
            "docs.textile",
            "content.creole",
            "info.mediawiki",
            "book.texi",
            "index.nfo",
            "faq.diz",
            "story.1st",
            "changes.changelog",
        ]
        
        # Non-documentation files (should be excluded)
        non_doc_files = [
            "script.py",
            "app.js",
            "style.css",
            "config.json",
            "data.xml",
            "image.png",
            "video.mp4",
            "binary.exe",
            "archive.zip",
            "database.db",
        ]
        
        # Create documentation files
        for filename in doc_files:
            file_path = files_dir / filename
            file_path.write_text(f"Documentation content in {filename}\n")
        
        # Create non-documentation files
        for filename in non_doc_files:
            file_path = files_dir / filename
            file_path.write_text(f"Non-doc content in {filename}\n")
        
        return files_dir

    @pytest.mark.unit
    def test_docs_only_basic(self, run_m1f, test_files_dir, temp_dir):
        """Test basic --docs-only functionality."""
        output_file = temp_dir / "docs_only_output.txt"
        
        # Run m1f with --docs-only
        exit_code, log_output = run_m1f(
            [
                "--source-directory",
                str(test_files_dir),
                "--output-file",
                str(output_file),
                "--docs-only",
                "--force",
            ]
        )
        
        # Verify success
        assert exit_code == 0, f"m1f failed with exit code {exit_code}"
        assert output_file.exists(), "Output file was not created"
        
        # Read output content
        content = output_file.read_text()
        
        # Check that documentation files are included
        assert "README.md" in content
        assert "guide.txt" in content
        assert "api.rst" in content
        assert "manual.adoc" in content
        assert "CHANGELOG.md" in content
        assert "help.1" in content
        assert "config.5" in content
        
        # Check that non-documentation files are excluded
        assert "script.py" not in content
        assert "app.js" not in content
        assert "style.css" not in content
        assert "config.json" not in content
        assert "image.png" not in content

    @pytest.mark.unit
    def test_docs_only_with_include_extensions_intersection(self, run_m1f, test_files_dir, temp_dir):
        """Test that --docs-only and --include-extensions create an intersection."""
        output_file = temp_dir / "docs_intersection_output.txt"
        
        # Run m1f with both --docs-only and --include-extensions
        # This should only include files that are BOTH documentation files AND have .md extension
        exit_code, log_output = run_m1f(
            [
                "--source-directory",
                str(test_files_dir),
                "--output-file",
                str(output_file),
                "--docs-only",
                "--include-extensions", ".md", ".txt",  # Only these doc extensions
                "--force",
            ]
        )
        
        # Verify success
        assert exit_code == 0, f"m1f failed with exit code {exit_code}"
        
        # Read output content
        content = output_file.read_text()
        
        # Check that only .md and .txt documentation files are included
        assert "README.md" in content
        assert "guide.txt" in content
        assert "CHANGELOG.md" in content
        
        # Other documentation files should be excluded due to extension filter
        assert "api.rst" not in content
        assert "manual.adoc" not in content
        assert "help.1" not in content
        
        # Non-documentation files should definitely be excluded
        assert "script.py" not in content
        assert "app.js" not in content

    @pytest.mark.unit
    def test_docs_only_with_excludes(self, run_m1f, test_files_dir, temp_dir):
        """Test --docs-only with exclude patterns."""
        output_file = temp_dir / "docs_exclude_output.txt"
        
        # Run m1f with --docs-only and excludes
        exit_code, log_output = run_m1f(
            [
                "--source-directory",
                str(test_files_dir),
                "--output-file",
                str(output_file),
                "--docs-only",
                "--excludes", "**/CHANGELOG*", "**/changes.*",  # Exclude changelog files
                "--force",
            ]
        )
        
        # Verify success
        assert exit_code == 0, f"m1f failed with exit code {exit_code}"
        
        # Read output content
        content = output_file.read_text()
        
        # Check that documentation files are included
        assert "README.md" in content
        assert "guide.txt" in content
        
        # CHANGELOG files should be excluded due to exclude pattern
        assert "CHANGELOG.md" not in content
        assert "changes.changelog" not in content

    @pytest.mark.unit
    def test_docs_only_file_count(self, run_m1f, test_files_dir, temp_dir):
        """Test that --docs-only correctly counts documentation files."""
        output_file = temp_dir / "docs_count_output.txt"
        info_file = output_file.with_suffix('.info')
        
        # Run m1f with --docs-only
        exit_code, log_output = run_m1f(
            [
                "--source-directory",
                str(test_files_dir),
                "--output-file",
                str(output_file),
                "--docs-only",
                "--force",
            ]
        )
        
        # Verify success
        assert exit_code == 0, f"m1f failed with exit code {exit_code}"
        
        # Check info file for file count
        if info_file.exists():
            info_content = info_file.read_text()
            # Should have processed 19 documentation files
            assert "19" in info_content or "Files Processed: 19" in log_output

    @pytest.mark.unit
    def test_docs_only_empty_directory(self, run_m1f, temp_dir):
        """Test --docs-only with directory containing no documentation files."""
        # Create directory with only non-doc files
        source_dir = temp_dir / "no_docs"
        source_dir.mkdir()
        
        (source_dir / "app.py").write_text("Python code")
        (source_dir / "style.css").write_text("CSS styles")
        (source_dir / "data.json").write_text('{"key": "value"}')
        
        output_file = temp_dir / "no_docs_output.txt"
        
        # Run m1f with --docs-only
        exit_code, log_output = run_m1f(
            [
                "--source-directory",
                str(source_dir),
                "--output-file",
                str(output_file),
                "--docs-only",
                "--force",
            ]
        )
        
        # Should still succeed but with empty or minimal output
        assert exit_code == 0, f"m1f failed with exit code {exit_code}"
        
        if output_file.exists():
            content = output_file.read_text()
            # Should not contain any of the non-doc files
            assert "app.py" not in content
            assert "style.css" not in content
            assert "data.json" not in content

    @pytest.mark.integration
    def test_docs_only_real_project_structure(self, run_m1f, m1f_source_dir, temp_dir):
        """Test --docs-only on the actual m1f test source directory."""
        output_file = temp_dir / "real_docs_output.txt"
        
        # Use the actual test source directory which has various file types
        exit_code, log_output = run_m1f(
            [
                "--source-directory",
                str(m1f_source_dir / "docs"),
                "--output-file",
                str(output_file),
                "--docs-only",
                "--force",
            ]
        )
        
        # Verify success
        assert exit_code == 0, f"m1f failed with exit code {exit_code}"
        assert output_file.exists(), "Output file was not created"
        
        # Read output content
        content = output_file.read_text()
        
        # Should include markdown files
        assert "README.md" in content
        
        # Should exclude image files
        assert "png.png" not in content