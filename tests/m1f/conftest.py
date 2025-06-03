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

"""M1F-specific test configuration and fixtures."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable


@pytest.fixture
def m1f_source_dir() -> Path:
    """Path to the m1f test source directory."""
    return Path(__file__).parent / "source"


@pytest.fixture
def m1f_output_dir() -> Path:
    """Path to the m1f test output directory."""
    path = Path(__file__).parent / "output"
    path.mkdir(exist_ok=True)
    return path


@pytest.fixture
def m1f_extracted_dir() -> Path:
    """Path to the m1f extracted directory."""
    path = Path(__file__).parent / "extracted"
    path.mkdir(exist_ok=True)
    return path


@pytest.fixture
def exclude_paths_file() -> Path:
    """Path to the exclude paths file."""
    return Path(__file__).parent / "exclude_paths.txt"


@pytest.fixture
def create_m1f_test_structure(
    create_test_directory_structure,
) -> Callable[[dict[str, str | dict]], Path]:
    """
    Create a test directory structure specifically for m1f testing.

    This wraps the generic fixture to add m1f-specific defaults.
    """

    def _create_structure(structure: dict[str, str | dict] | None = None) -> Path:
        # Default test structure if none provided
        if structure is None:
            structure = {
                "src": {
                    "main.py": "#!/usr/bin/env python3\nprint('Hello, World!')",
                    "utils.py": "def helper():\n    return 42",
                },
                "tests": {
                    "test_main.py": "import pytest\n\ndef test_main():\n    assert True",
                },
                "docs": {
                    "README.md": "# Test Project\n\nThis is a test.",
                },
                ".gitignore": "*.pyc\n__pycache__/\n.pytest_cache/",
                "requirements.txt": "pytest>=7.0.0\nblack>=22.0.0",
            }

        return create_test_directory_structure(structure)

    return _create_structure


@pytest.fixture
def run_m1f(monkeypatch, capture_logs):
    """
    Run m1f.main() with the specified command line arguments.

    This fixture properly handles sys.argv manipulation and cleanup.
    """
    import sys
    from pathlib import Path

    # Add tools directory to path to import m1f script
    tools_dir = str(Path(__file__).parent.parent.parent / "tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)

    # Import from the m1f.py script, not the package
    import importlib.util

    m1f_script_path = Path(__file__).parent.parent.parent / "tools" / "m1f.py"
    spec = importlib.util.spec_from_file_location("m1f_script", m1f_script_path)
    m1f_script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m1f_script)
    main = m1f_script.main

    def _run_m1f(args: list[str], auto_confirm: bool = True) -> tuple[int, str]:
        """
        Run m1f with given arguments.

        Args:
            args: Command line arguments
            auto_confirm: Whether to auto-confirm prompts

        Returns:
            Tuple of (exit_code, log_output)
        """
        # Capture logs - use root logger since m1f configures the root logger
        log_capture = capture_logs.capture("")

        # Mock user input if needed
        if auto_confirm:
            monkeypatch.setattr("builtins.input", lambda _: "y")

        # Set up argv
        monkeypatch.setattr("sys.argv", ["m1f"] + args)

        # Capture exit code
        exit_code = 0
        try:
            main()
        except SystemExit as e:
            exit_code = e.code if e.code is not None else 0

        return exit_code, log_capture.get_output()

    return _run_m1f


@pytest.fixture
def m1f_cli_runner():
    """
    Create a CLI runner for m1f that captures output.

    This is useful for testing the command-line interface.
    """
    import subprocess
    import sys

    def _run_cli(args: list[str]) -> subprocess.CompletedProcess:
        """Run m1f as a subprocess."""
        # Get the path to the m1f.py script
        m1f_script = Path(__file__).parent.parent.parent / "tools" / "m1f.py"
        return subprocess.run(
            [sys.executable, str(m1f_script)] + args,
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )

    return _run_cli
