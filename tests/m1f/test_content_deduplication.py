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

"""Test content deduplication functionality."""

import pytest
from pathlib import Path
import subprocess
import sys

from tools.m1f.cli import create_parser, parse_args
from tools.m1f.config import Config


def test_cli_help_includes_deduplication_option():
    """Test that the CLI help includes the deduplication option."""
    parser = create_parser()
    help_text = parser.format_help()
    assert "--allow-duplicate-files" in help_text
    assert "Allow files with identical content" in help_text


def test_deduplication_enabled_by_default():
    """Test that content deduplication is enabled by default."""
    parser = create_parser()
    args = parser.parse_args(["-s", ".", "-o", "test.txt"])
    config = Config.from_args(args)
    assert config.output.enable_content_deduplication is True


def test_allow_duplicate_files_cli_argument():
    """Test that --allow-duplicate-files disables deduplication."""
    parser = create_parser()
    args = parser.parse_args(["-s", ".", "-o", "test.txt", "--allow-duplicate-files"])
    config = Config.from_args(args)
    assert config.output.enable_content_deduplication is False


def test_deduplication_behavior(tmp_path):
    """Test that deduplication actually works."""
    # Create test files with duplicate content
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file3 = tmp_path / "file3.txt"

    duplicate_content = "This is duplicate content"
    unique_content = "This is unique content"

    file1.write_text(duplicate_content)
    file2.write_text(duplicate_content)
    file3.write_text(unique_content)

    output_file = tmp_path / "output.txt"

    # Test with deduplication enabled (default)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.m1f",
            "-s",
            str(tmp_path),
            "-o",
            str(output_file),
            "--include-extensions",
            ".txt",
            "--excludes",
            "output*.txt",
            "*.log",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output_content = output_file.read_text()

    # Should only have one instance of duplicate content
    assert output_content.count(duplicate_content) == 1
    assert output_content.count(unique_content) == 1

    # Test with deduplication disabled
    output_file2 = tmp_path / "output2.txt"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.m1f",
            "-s",
            str(tmp_path),
            "-o",
            str(output_file2),
            "--include-extensions",
            ".txt",
            "--excludes",
            "output*.txt",
            "*.log",
            "--allow-duplicate-files",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output_content2 = output_file2.read_text()

    # Should have two instances of duplicate content
    assert output_content2.count(duplicate_content) == 2
    assert output_content2.count(unique_content) == 1
