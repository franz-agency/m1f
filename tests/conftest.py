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

"""Global pytest configuration and fixtures for the entire test suite."""

from __future__ import annotations

import sys
import shutil
import tempfile
import gc
import time
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

# Add colorama imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.shared.colors import warning

if TYPE_CHECKING:
    from collections.abc import Iterator, Callable


# Add the tools directory to path to import the modules
TOOLS_DIR = Path(__file__).parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))


@pytest.fixture(scope="session")
def tools_dir() -> Path:
    """Path to the tools directory."""
    return TOOLS_DIR


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Path to the test data directory."""
    return Path(__file__).parent


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    """Create a temporary directory for test files."""
    # Use project's tmp directory instead of system temp
    project_tmp = Path(__file__).parent.parent / "tmp" / "test_temp"

    # Ensure the directory exists
    try:
        project_tmp.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as e:
        pytest.skip(f"Cannot create test directory in project tmp: {e}")

    # Create a unique subdirectory for this test
    import uuid

    test_dir = project_tmp / f"test_{uuid.uuid4().hex[:8]}"
    test_dir.mkdir(exist_ok=True)

    try:
        yield test_dir
    finally:
        # Clean up with Windows-specific handling
        if test_dir.exists():
            _safe_cleanup_directory(test_dir)


@pytest.fixture
def isolated_filesystem() -> Iterator[Path]:
    """
    Create an isolated filesystem for testing.

    This ensures tests don't interfere with each other by providing
    a clean temporary directory that's automatically cleaned up.
    """
    # Use project's tmp directory instead of system temp
    project_tmp = Path(__file__).parent.parent / "tmp" / "test_isolated"

    # Ensure the directory exists
    try:
        project_tmp.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as e:
        pytest.skip(f"Cannot create test directory in project tmp: {e}")

    # Create a unique subdirectory for this test
    import uuid

    test_dir = project_tmp / f"test_{uuid.uuid4().hex[:8]}"
    test_dir.mkdir(exist_ok=True)

    original_cwd = Path.cwd()
    try:
        # Change to the temporary directory
        import os

        os.chdir(test_dir)
        yield test_dir
    finally:
        # Restore original working directory
        os.chdir(original_cwd)
        # Clean up with Windows-specific handling
        if test_dir.exists():
            _safe_cleanup_directory(test_dir)


@pytest.fixture
def create_test_file(temp_dir: Path) -> Callable[[str, str, str | None], Path]:
    """
    Factory fixture to create test files.

    Args:
        relative_path: Path relative to temp_dir
        content: File content
        encoding: File encoding (defaults to utf-8)

    Returns:
        Path to the created file
    """

    def _create_file(
        relative_path: str, content: str = "test content", encoding: str | None = None
    ) -> Path:
        file_path = temp_dir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding=encoding or "utf-8")
        return file_path

    return _create_file


@pytest.fixture
def create_test_directory_structure(
    temp_dir: Path,
) -> Callable[[dict[str, str | dict]], Path]:
    """
    Create a directory structure with files from a dictionary.

    Example:
        {
            "file1.txt": "content1",
            "subdir/file2.py": "content2",
            "nested": {
                "deep": {
                    "file3.md": "content3"
                }
            }
        }
    """

    def _create_structure(
        structure: dict[str, str | dict], base_path: Path | None = None
    ) -> Path:
        if base_path is None:
            base_path = temp_dir

        for name, content in structure.items():
            path = base_path / name
            if isinstance(content, dict):
                path.mkdir(parents=True, exist_ok=True)
                _create_structure(content, path)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                if isinstance(content, bytes):
                    path.write_bytes(content)
                else:
                    path.write_text(content, encoding="utf-8")

        return base_path

    return _create_structure


@pytest.fixture(autouse=True)
def cleanup_logging():
    """Automatically clean up logging handlers after each test."""
    yield

    # Clean up any logging handlers that might interfere with tests
    import logging

    # Get all loggers that might have been created
    for logger_name in ["m1f", "s1f"]:
        logger = logging.getLogger(logger_name)

        # Remove and close all handlers
        for handler in logger.handlers[:]:
            if hasattr(handler, "close"):
                handler.close()
            logger.removeHandler(handler)

        # Clear the logger's handler list
        logger.handlers.clear()

        # Reset logger level
        logger.setLevel(logging.WARNING)


@pytest.fixture(autouse=True)
def cleanup_file_handles():
    """Automatically clean up file handles after each test (Windows specific)."""
    yield

    # Force garbage collection to close any remaining file handles
    # This is especially important on Windows where file handles can prevent deletion
    if sys.platform.startswith("win"):
        gc.collect()
        # Give a small delay for Windows to release handles
        time.sleep(0.01)


@pytest.fixture
def capture_logs():
    """Capture log messages for testing."""
    import logging
    from io import StringIO

    class LogCapture:
        def __init__(self):
            self.stream = StringIO()
            self.handler = logging.StreamHandler(self.stream)
            self.handler.setFormatter(
                logging.Formatter("%(levelname)s:%(name)s:%(message)s")
            )
            self.loggers = []

        def capture(self, logger_name: str, level: int = logging.DEBUG) -> LogCapture:
            """Start capturing logs for a specific logger."""
            logger = logging.getLogger(logger_name)
            logger.addHandler(self.handler)
            logger.setLevel(level)
            self.loggers.append(logger)
            return self

        def get_output(self) -> str:
            """Get captured log output."""
            return self.stream.getvalue()

        def clear(self):
            """Clear captured output."""
            self.stream.truncate(0)
            self.stream.seek(0)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            # Remove handler from all loggers
            for logger in self.loggers:
                logger.removeHandler(self.handler)
            self.handler.close()

    return LogCapture()


# Platform-specific helpers
@pytest.fixture
def is_windows() -> bool:
    """Check if running on Windows."""
    return sys.platform.startswith("win")


def _safe_cleanup_directory(directory: Path, max_retries: int = 5) -> None:
    """
    Safely clean up a directory with Windows-specific handling.

    Windows can have file handle issues that prevent immediate deletion.
    This function retries with increasing delays and forces garbage collection.
    """
    import os
    import time

    for attempt in range(max_retries):
        try:
            # Force garbage collection to close any remaining file handles
            gc.collect()

            # On Windows, try to remove read-only attributes that might prevent deletion
            if sys.platform.startswith("win"):
                _remove_readonly_attributes(directory)

            shutil.rmtree(directory)
            return
        except (OSError, PermissionError) as e:
            if attempt == max_retries - 1:
                # Final attempt failed, log warning but don't raise
                warning(f"Could not clean up test directory {directory}: {e}")
                return

            # Wait with exponential backoff
            delay = 0.1 * (2**attempt)
            time.sleep(delay)

            # Force garbage collection again
            gc.collect()


def _remove_readonly_attributes(directory: Path) -> None:
    """
    Remove read-only attributes from files and directories on Windows.

    This helps with cleanup when files are marked as read-only.
    """
    import os
    import stat

    if not sys.platform.startswith("win"):
        return

    try:
        for root, dirs, files in os.walk(directory):
            # Remove read-only flag from files
            for file in files:
                file_path = Path(root) / file
                try:
                    file_path.chmod(stat.S_IWRITE | stat.S_IREAD)
                except (OSError, PermissionError):
                    pass  # Ignore errors, best effort

            # Remove read-only flag from directories
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                try:
                    dir_path.chmod(stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
                except (OSError, PermissionError):
                    pass  # Ignore errors, best effort
    except (OSError, PermissionError):
        pass  # Ignore errors, best effort


@pytest.fixture
def path_separator() -> str:
    """Get the platform-specific path separator."""
    import os

    return os.path.sep


# Async support fixtures (for s1f async functionality)
@pytest.fixture
def anyio_backend():
    """Configure async backend for testing."""
    return "asyncio"


# Mark for different test categories
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "requires_git: Tests that require git")
    config.addinivalue_line("markers", "encoding: Encoding-related tests")
