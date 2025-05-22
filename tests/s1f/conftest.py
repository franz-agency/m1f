"""S1F-specific test configuration and fixtures."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    import subprocess


@pytest.fixture
def s1f_output_dir() -> Path:
    """Path to the s1f test output directory."""
    path = Path(__file__).parent / "output"
    path.mkdir(exist_ok=True)
    return path


@pytest.fixture
def s1f_extracted_dir() -> Path:
    """Path to the s1f extracted directory."""
    path = Path(__file__).parent / "extracted"
    path.mkdir(exist_ok=True)
    return path


@pytest.fixture(autouse=True)
def cleanup_extracted_dir(s1f_extracted_dir):
    """Automatically clean up extracted directory before and after tests."""
    # Clean before test
    import shutil
    if s1f_extracted_dir.exists():
        shutil.rmtree(s1f_extracted_dir)
    s1f_extracted_dir.mkdir(exist_ok=True)
    
    yield
    
    # Clean after test
    if s1f_extracted_dir.exists():
        shutil.rmtree(s1f_extracted_dir)
    s1f_extracted_dir.mkdir(exist_ok=True)


@pytest.fixture
def create_combined_file(temp_dir: Path) -> Callable[[dict[str, str], str, str], Path]:
    """
    Create a combined file in different formats for testing s1f extraction.
    
    Args:
        files: Dict of relative_path -> content
        separator_style: Style of separator to use
        filename: Output filename
        
    Returns:
        Path to created combined file
    """
    def _create_file(
        files: dict[str, str], 
        separator_style: str = "Standard",
        filename: str = "combined.txt"
    ) -> Path:
        output_file = temp_dir / filename
        
        with open(output_file, "w", encoding="utf-8") as f:
            for filepath, content in files.items():
                if separator_style == "Standard":
                    f.write(f"FILE: {filepath}\n")
                    f.write(f"{'=' * 40}\n")
                    f.write(content)
                    if not content.endswith("\n"):
                        f.write("\n")
                    f.write(f"{'=' * 40}\n\n")
                    
                elif separator_style == "Detailed":
                    f.write(f"==== FILE: {filepath} ====\n")
                    f.write(f"---- Size: {len(content)} bytes ----\n")
                    f.write(f"---- Lines: {len(content.splitlines())} ----\n")
                    f.write(f"{'=' * 50}\n")
                    f.write(content)
                    if not content.endswith("\n"):
                        f.write("\n")
                    f.write(f"{'=' * 50}\n\n")
                    
                elif separator_style == "Markdown":
                    f.write(f"## File: `{filepath}`\n\n")
                    f.write("```\n")
                    f.write(content)
                    if not content.endswith("\n"):
                        f.write("\n")
                    f.write("```\n\n")
                    
                elif separator_style == "MachineReadable":
                    import json
                    import uuid
                    file_id = str(uuid.uuid4())
                    
                    metadata = {
                        "original_filepath": filepath,
                        "original_filename": Path(filepath).name,
                        "timestamp_utc_iso": "2024-01-01T00:00:00Z",
                        "type": Path(filepath).suffix,
                        "size_bytes": len(content.encode("utf-8")),
                        "encoding": "utf-8",
                    }
                    
                    f.write(f"--- PYMK1F_BEGIN_FILE_METADATA_BLOCK_{file_id} ---\n")
                    f.write("METADATA_JSON:\n")
                    f.write(json.dumps(metadata, indent=4))
                    f.write("\n")
                    f.write(f"--- PYMK1F_END_FILE_METADATA_BLOCK_{file_id} ---\n")
                    f.write(f"--- PYMK1F_BEGIN_FILE_CONTENT_BLOCK_{file_id} ---\n")
                    f.write(content)
                    if not content.endswith("\n"):
                        f.write("\n")
                    f.write(f"--- PYMK1F_END_FILE_CONTENT_BLOCK_{file_id} ---\n\n")
        
        return output_file
    
    return _create_file


@pytest.fixture
def run_s1f(monkeypatch, capture_logs):
    """
    Run s1f.main() with the specified command line arguments.
    
    This fixture properly handles sys.argv manipulation and cleanup.
    """
    from s1f.cli import main
    
    def _run_s1f(args: list[str]) -> tuple[int, str]:
        """
        Run s1f with given arguments.
        
        Args:
            args: Command line arguments
            
        Returns:
            Tuple of (exit_code, log_output)
        """
        # Capture logs
        log_capture = capture_logs.capture("s1f")
        
        # Set up argv
        monkeypatch.setattr("sys.argv", ["s1f"] + args)
        
        # Capture exit code
        exit_code = 0
        try:
            main()
        except SystemExit as e:
            exit_code = e.code if e.code is not None else 0
        
        return exit_code, log_capture.get_output()
    
    return _run_s1f


@pytest.fixture
def s1f_cli_runner():
    """
    Create a CLI runner for s1f that captures output.
    
    This is useful for testing the command-line interface.
    """
    import subprocess
    import sys
    
    def _run_cli(args: list[str]) -> subprocess.CompletedProcess:
        """Run s1f as a subprocess."""
        return subprocess.run(
            [sys.executable, "-m", "s1f"] + args,
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
    
    return _run_cli


@pytest.fixture
def create_m1f_output(run_m1f, temp_dir) -> Callable[[dict[str, str], str], Path]:
    """
    Create an m1f output file for s1f testing.
    
    This uses the actual m1f tool to create realistic test files.
    """
    def _create_output(
        files: dict[str, str],
        separator_style: str = "Standard"
    ) -> Path:
        # Create source directory with files
        source_dir = temp_dir / "m1f_source"
        source_dir.mkdir(exist_ok=True)
        
        for filepath, content in files.items():
            file_path = source_dir / filepath
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
        
        # Run m1f to create combined file
        output_file = temp_dir / f"m1f_output_{separator_style.lower()}.txt"
        
        exit_code, _ = run_m1f([
            "--source-directory", str(source_dir),
            "--output-file", str(output_file),
            "--separator-style", separator_style,
            "--force",
        ])
        
        if exit_code != 0:
            raise RuntimeError(f"Failed to create m1f output with {separator_style}")
        
        return output_file
    
    return _create_output 