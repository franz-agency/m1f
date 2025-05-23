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
                    # Use the real M1F Standard format
                    import hashlib
                    # The combined file should have proper line ending for formatting
                    file_content = content if content.endswith("\n") else content + "\n"
                    # And checksum should be calculated for the content as written (with newline)
                    content_bytes = file_content.encode('utf-8')
                    checksum = hashlib.sha256(content_bytes).hexdigest()
                    f.write(f"======= {filepath} | CHECKSUM_SHA256: {checksum} ======\n")
                    f.write(file_content)
                    
                elif separator_style == "Detailed":
                    # Use the real M1F Detailed format
                    import hashlib
                    # The combined file should have proper line ending for formatting
                    file_content = content if content.endswith("\n") else content + "\n"
                    # And checksum should be calculated for the content as written (with newline)
                    content_bytes = file_content.encode('utf-8')
                    checksum = hashlib.sha256(content_bytes).hexdigest()
                    f.write("=" * 88 + "\n")
                    f.write(f"== FILE: {filepath}\n")
                    f.write(f"== DATE: 2024-01-01 00:00:00 | SIZE: {len(content_bytes)} B | TYPE: {Path(filepath).suffix}\n")
                    f.write("== ENCODING: utf-8\n")
                    f.write(f"== CHECKSUM_SHA256: {checksum}\n")
                    f.write("=" * 88 + "\n")
                    f.write(file_content)
                    
                elif separator_style == "Markdown":
                    # Use the real M1F Markdown format
                    import hashlib
                    file_content = content if content.endswith("\n") else content + "\n"
                    content_bytes = file_content.encode('utf-8')
                    checksum = hashlib.sha256(content_bytes).hexdigest()
                    file_extension = Path(filepath).suffix.lstrip('.')  # Remove leading dot
                    
                    f.write(f"## {Path(filepath).name}\n")
                    f.write(f"**Date Modified:** 2024-01-01 00:00:00 | **Size:** {len(content_bytes)} B | ")
                    f.write(f"**Type:** {Path(filepath).suffix} | **Encoding:** utf-8 | ")
                    f.write(f"**Checksum (SHA256):** {checksum}\n\n")
                    f.write(f"```{file_extension}{file_content}```\n\n")
                    
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
    import sys
    from pathlib import Path
    
    # Add tools directory to path to import s1f script
    tools_dir = str(Path(__file__).parent.parent.parent / "tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    
    # Import from the s1f.py script, not the package
    import importlib.util
    s1f_script_path = Path(__file__).parent.parent.parent / "tools" / "s1f.py"
    spec = importlib.util.spec_from_file_location("s1f_script", s1f_script_path)
    s1f_script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(s1f_script)
    main = s1f_script.main
    
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
        # Get the path to the s1f.py script
        s1f_script = Path(__file__).parent.parent.parent / "tools" / "s1f.py"
        return subprocess.run(
            [sys.executable, str(s1f_script)] + args,
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
    
    return _run_cli


@pytest.fixture
def create_m1f_output(temp_dir) -> Callable[[dict[str, str], str], Path]:
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
        
        # Import and run m1f directly  
        import sys
        from pathlib import Path
        
        # Add tools directory to path
        tools_dir = str(Path(__file__).parent.parent.parent / "tools")
        if tools_dir not in sys.path:
            sys.path.insert(0, tools_dir)
            
        import subprocess
        m1f_script = Path(__file__).parent.parent.parent / "tools" / "m1f.py"
        
        result = subprocess.run([
            sys.executable, str(m1f_script),
            "--source-directory", str(source_dir),
            "--output-file", str(output_file),
            "--separator-style", separator_style,
            "--force",
        ], capture_output=True, text=True)
        
        exit_code = result.returncode
        
        if exit_code != 0:
            raise RuntimeError(f"Failed to create m1f output with {separator_style}")
        
        return output_file
    
    return _create_output 