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