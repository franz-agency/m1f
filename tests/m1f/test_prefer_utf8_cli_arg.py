"""Test for prefer_utf8_for_text_files CLI argument."""

import pytest
from pathlib import Path
import sys
import subprocess

from tools.m1f.cli import create_parser, parse_args
from tools.m1f.config import Config


def test_cli_help_includes_prefer_utf8_option():
    """Test that the CLI help includes the new option."""
    parser = create_parser()
    help_text = parser.format_help()
    assert "--no-prefer-utf8-for-text-files" in help_text
    assert "Disable UTF-8 preference for text files" in help_text


def test_prefer_utf8_default_value():
    """Test that prefer_utf8_for_text_files defaults to True."""
    parser = create_parser()
    args = parser.parse_args(["-s", ".", "-o", "test.txt"])
    config = Config.from_args(args)
    assert config.encoding.prefer_utf8_for_text_files is True


def test_no_prefer_utf8_cli_argument():
    """Test that --no-prefer-utf8-for-text-files sets the value to False."""
    parser = create_parser()
    args = parser.parse_args(["-s", ".", "-o", "test.txt", "--no-prefer-utf8-for-text-files"])
    config = Config.from_args(args)
    assert config.encoding.prefer_utf8_for_text_files is False


def test_m1f_runs_with_no_prefer_utf8_flag(tmp_path):
    """Test that m1f runs successfully with the new flag."""
    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, world!")
    
    output_file = tmp_path / "output.txt"
    
    # Run m1f with the new flag
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.m1f",
            "-s",
            str(tmp_path),
            "-o",
            str(output_file),
            "--no-prefer-utf8-for-text-files",
        ],
        capture_output=True,
        text=True,
    )
    
    # Check that it ran successfully
    assert result.returncode == 0
    assert output_file.exists()