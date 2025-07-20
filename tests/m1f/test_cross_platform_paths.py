#!/usr/bin/env python3
# Copyright 2025 Franz und Franz GmbH
# SPDX-License-Identifier: Apache-2.0

"""Integration test to verify path separators in actual bundle files."""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

import pytest

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ..base_test import BaseM1FTest


class TestCrossPlatformPaths(BaseM1FTest):
    """Test cross-platform path handling in m1f and s1f."""

    @pytest.mark.integration
    def test_bundle_creation_and_extraction(self, run_m1f, temp_dir):
        """Test that bundles contain forward slashes and extract correctly."""
        # Create test files in nested directories
        source_dir = temp_dir / "source"
        (source_dir / "src" / "components").mkdir(parents=True)
        (source_dir / "src" / "main.py").write_text("# Main file\nprint('Hello')\n")
        (source_dir / "src" / "components" / "ui.py").write_text(
            "# UI component\nclass Button: pass\n"
        )
        (source_dir / "docs").mkdir()
        (source_dir / "docs" / "README.md").write_text(
            "# Documentation\nTest project\n"
        )

        # Create output file path
        output_file = temp_dir / "test_bundle.txt"

        # Run m1f to create bundle
        exit_code, log_output = run_m1f(["-s", str(source_dir), "-o", str(output_file)])
        assert exit_code == 0, f"m1f failed with exit code {exit_code}: {log_output}"

        # Read the bundle and check for path separators
        bundle_content = output_file.read_text()

        # Check that paths use forward slashes
        assert "src/main.py" in bundle_content, "Expected 'src/main.py' in bundle"
        assert (
            "src/components/ui.py" in bundle_content
        ), "Expected 'src/components/ui.py' in bundle"
        assert "docs/README.md" in bundle_content, "Expected 'docs/README.md' in bundle"

        # Ensure no backslashes in file paths (except in file content)
        lines = bundle_content.split("\n")
        for line in lines:
            # Check lines that look like file separators
            if line.startswith("===") and "FILE:" in line:
                assert "\\" not in line, f"Found backslash in separator line: {line}"

        # Test s1f extraction using subprocess
        extract_dir = temp_dir / "extracted"
        extract_dir.mkdir()

        import subprocess

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.s1f",
                str(output_file),
                "-d",
                str(extract_dir),
                "-f",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"s1f failed: {result.stderr}"

        # Verify files were extracted correctly
        assert (extract_dir / "src" / "main.py").exists(), "src/main.py not extracted"
        assert (
            extract_dir / "src" / "components" / "ui.py"
        ).exists(), "src/components/ui.py not extracted"
        assert (
            extract_dir / "docs" / "README.md"
        ).exists(), "docs/README.md not extracted"

        # Verify content matches
        assert (
            extract_dir / "src" / "main.py"
        ).read_text() == "# Main file\nprint('Hello')\n"
        assert (
            extract_dir / "src" / "components" / "ui.py"
        ).read_text() == "# UI component\nclass Button: pass\n"
        assert (
            extract_dir / "docs" / "README.md"
        ).read_text() == "# Documentation\nTest project\n"

    @pytest.mark.integration
    def test_separator_styles(self, run_m1f, temp_dir):
        """Test that all separator styles use forward slashes in paths."""
        # Create a simple test file
        source_dir = temp_dir / "source"
        source_dir.mkdir()
        (source_dir / "test.txt").write_text("Test content")

        separator_styles = ["Standard", "Detailed", "Markdown", "MachineReadable"]

        for style in separator_styles:
            output_file = temp_dir / f"bundle_{style.lower()}.txt"

            # Run m1f with specific separator style
            exit_code, log_output = run_m1f(
                [
                    "-s",
                    str(source_dir),
                    "-o",
                    str(output_file),
                    "--separator-style",
                    style,
                ]
            )
            assert (
                exit_code == 0
            ), f"m1f failed for {style} with exit code {exit_code}: {log_output}"

            # Check bundle content
            bundle_content = output_file.read_text()

            # For any style, the path should not contain backslashes
            if style == "MachineReadable":
                # In machine readable format, check the JSON metadata
                assert (
                    '"original_filepath": "test.txt"' in bundle_content
                    or '"original_filepath":"test.txt"' in bundle_content
                ), f"Path not found in {style} format"
            else:
                # For other styles, just ensure no backslashes in paths
                lines = bundle_content.split("\n")
                for line in lines:
                    # Skip actual file content lines
                    if "FILE:" in line or "test.txt" in line.lower():
                        assert (
                            "\\" not in line
                        ), f"Found backslash in {style} style: {line}"
