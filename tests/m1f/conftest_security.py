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
Shared test infrastructure for security tests.
"""
import tempfile
import shutil
from pathlib import Path
from contextlib import contextmanager


@contextmanager
def isolated_test_directory():
    """Create an isolated temporary directory for tests."""
    temp_dir = None
    try:
        # Create a unique temporary directory
        temp_dir = tempfile.mkdtemp(prefix="m1f_security_test_")
        temp_path = Path(temp_dir)
        
        # Create standard subdirectories
        source_dir = temp_path / "source"
        output_dir = temp_path / "output"
        source_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        yield temp_path, source_dir, output_dir
        
    finally:
        # Clean up the temporary directory
        if temp_dir and Path(temp_dir).exists():
            try:
                shutil.rmtree(temp_dir)
            except (OSError, PermissionError):
                # Best effort cleanup - ignore errors
                pass


def create_test_file(base_dir: Path, relative_path: str, content: str) -> Path:
    """Create a test file with proper directory structure."""
    file_path = base_dir / relative_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return file_path


def ensure_test_isolation():
    """Ensure tests are properly isolated from each other."""
    import logging
    
    # Reset logging state
    logger = logging.getLogger()
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        if hasattr(handler, 'close'):
            handler.close()
    
    # Reset logging level
    logger.setLevel(logging.WARNING)
