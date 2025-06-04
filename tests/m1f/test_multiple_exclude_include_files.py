"""
Test multiple exclude and include files functionality.
"""

import pytest
from pathlib import Path
import tempfile
import shutil

import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.m1f.config import (
    Config,
    FilterConfig,
    OutputConfig,
    EncodingConfig,
    SecurityConfig,
    ArchiveConfig,
    LoggingConfig,
    PresetConfig,
)
from tools.m1f.file_processor import FileProcessor
from tools.m1f.logging import LoggerManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # Create test files
        (tmp_path / "file1.py").write_text("# Python file 1")
        (tmp_path / "file2.py").write_text("# Python file 2")
        (tmp_path / "file3.txt").write_text("Text file")
        (tmp_path / "exclude_me.py").write_text("# Should be excluded")
        (tmp_path / "include_me.py").write_text("# Should be included")
        (tmp_path / "secret.key").write_text("SECRET_KEY")

        # Create subdirectory with files
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "sub_file.py").write_text("# Subdir file")

        # Create exclude files
        (tmp_path / ".gitignore").write_text("*.key\nexclude_me.py")
        (tmp_path / "extra_excludes.txt").write_text("file3.txt")

        # Create include files
        (tmp_path / "includes.txt").write_text("include_me.py\nsubdir/sub_file.py")
        (tmp_path / "more_includes.txt").write_text("file1.py")

        yield tmp_path


class TestMultipleExcludeIncludeFiles:
    """Test multiple exclude and include files functionality."""

    @pytest.mark.asyncio
    async def test_single_exclude_file(self, temp_dir):
        """Test with a single exclude file."""
        config = Config(
            source_directory=temp_dir,
            input_file=None,
            input_include_files=[],
            output=OutputConfig(output_file=temp_dir / "output.txt"),
            filter=FilterConfig(exclude_paths_file=str(temp_dir / ".gitignore")),
            encoding=EncodingConfig(),
            security=SecurityConfig(),
            archive=ArchiveConfig(),
            logging=LoggingConfig(),
            preset=PresetConfig(),
        )

        logger_manager = LoggerManager(config.logging)
        processor = FileProcessor(config, logger_manager)
        files = await processor.gather_files()

        # Should exclude secret.key and exclude_me.py
        file_names = [f[0].name for f in files]
        assert "secret.key" not in file_names
        assert "exclude_me.py" not in file_names
        assert "file1.py" in file_names
        assert "file2.py" in file_names
        assert "file3.txt" in file_names

    @pytest.mark.asyncio
    async def test_multiple_exclude_files(self, temp_dir):
        """Test with multiple exclude files."""
        config = Config(
            source_directory=temp_dir,
            input_file=None,
            input_include_files=[],
            output=OutputConfig(output_file=temp_dir / "output.txt"),
            filter=FilterConfig(
                exclude_paths_file=[
                    str(temp_dir / ".gitignore"),
                    str(temp_dir / "extra_excludes.txt"),
                ]
            ),
            encoding=EncodingConfig(),
            security=SecurityConfig(),
            archive=ArchiveConfig(),
            logging=LoggingConfig(),
            preset=PresetConfig(),
        )

        logger_manager = LoggerManager(config.logging)
        processor = FileProcessor(config, logger_manager)
        files = await processor.gather_files()

        # Should exclude everything from both files
        file_names = [f[0].name for f in files]
        assert "secret.key" not in file_names
        assert "exclude_me.py" not in file_names
        assert "file3.txt" not in file_names  # Excluded by extra_excludes.txt
        assert "file1.py" in file_names
        assert "file2.py" in file_names

    @pytest.mark.asyncio
    async def test_single_include_file(self, temp_dir):
        """Test with a single include file."""
        config = Config(
            source_directory=temp_dir,
            input_file=None,
            input_include_files=[],
            output=OutputConfig(output_file=temp_dir / "output.txt"),
            filter=FilterConfig(include_paths_file=str(temp_dir / "includes.txt")),
            encoding=EncodingConfig(),
            security=SecurityConfig(),
            archive=ArchiveConfig(),
            logging=LoggingConfig(),
            preset=PresetConfig(),
        )

        logger_manager = LoggerManager(config.logging)
        processor = FileProcessor(config, logger_manager)
        files = await processor.gather_files()

        # Should only include files in the include list
        file_names = sorted([f[0].name for f in files])
        assert file_names == ["include_me.py", "sub_file.py"]

    @pytest.mark.asyncio
    async def test_multiple_include_files(self, temp_dir):
        """Test with multiple include files."""
        config = Config(
            source_directory=temp_dir,
            input_file=None,
            input_include_files=[],
            output=OutputConfig(output_file=temp_dir / "output.txt"),
            filter=FilterConfig(
                include_paths_file=[
                    str(temp_dir / "includes.txt"),
                    str(temp_dir / "more_includes.txt"),
                ]
            ),
            encoding=EncodingConfig(),
            security=SecurityConfig(),
            archive=ArchiveConfig(),
            logging=LoggingConfig(),
            preset=PresetConfig(),
        )

        logger_manager = LoggerManager(config.logging)
        processor = FileProcessor(config, logger_manager)
        files = await processor.gather_files()

        # Should include files from both include files
        file_names = sorted([f[0].name for f in files])
        assert file_names == ["file1.py", "include_me.py", "sub_file.py"]

    @pytest.mark.asyncio
    async def test_exclude_and_include_together(self, temp_dir):
        """Test with both exclude and include files."""
        config = Config(
            source_directory=temp_dir,
            input_file=None,
            input_include_files=[],
            output=OutputConfig(output_file=temp_dir / "output.txt"),
            filter=FilterConfig(
                include_paths_file=[
                    str(temp_dir / "includes.txt"),
                    str(temp_dir / "more_includes.txt"),
                ],
                exclude_paths_file=str(temp_dir / ".gitignore"),
            ),
            encoding=EncodingConfig(),
            security=SecurityConfig(),
            archive=ArchiveConfig(),
            logging=LoggingConfig(),
            preset=PresetConfig(),
        )

        logger_manager = LoggerManager(config.logging)
        processor = FileProcessor(config, logger_manager)
        files = await processor.gather_files()

        # Include list takes precedence, then excludes are applied
        file_names = sorted([f[0].name for f in files])
        # include_me.py, file1.py and sub_file.py are in include lists
        # Neither are in exclude lists, so all should be included
        assert file_names == ["file1.py", "include_me.py", "sub_file.py"]

    @pytest.mark.asyncio
    async def test_input_file_bypasses_filters(self, temp_dir):
        """Test that files from -i bypass all filters."""
        # Create input file listing specific files
        input_file = temp_dir / "input_files.txt"
        input_file.write_text("exclude_me.py\nsecret.key\nfile1.py")

        config = Config(
            source_directory=temp_dir,
            input_file=input_file,
            input_include_files=[],
            output=OutputConfig(output_file=temp_dir / "output.txt"),
            filter=FilterConfig(
                exclude_paths_file=str(temp_dir / ".gitignore"),
                include_paths_file=str(temp_dir / "includes.txt"),
            ),
            encoding=EncodingConfig(),
            security=SecurityConfig(),
            archive=ArchiveConfig(),
            logging=LoggingConfig(),
            preset=PresetConfig(),
        )

        logger_manager = LoggerManager(config.logging)
        processor = FileProcessor(config, logger_manager)
        files = await processor.gather_files()

        # Files from input file should bypass all filters
        file_names = sorted([f[0].name for f in files])
        # exclude_me.py and secret.key would normally be excluded
        assert "exclude_me.py" in file_names
        assert "secret.key" in file_names
        assert "file1.py" in file_names

    @pytest.mark.asyncio
    async def test_nonexistent_files_skipped(self, temp_dir):
        """Test that non-existent files are gracefully skipped."""
        config = Config(
            source_directory=temp_dir,
            input_file=None,
            input_include_files=[],
            output=OutputConfig(output_file=temp_dir / "output.txt"),
            filter=FilterConfig(
                exclude_paths_file=[
                    str(temp_dir / ".gitignore"),
                    str(temp_dir / "does_not_exist.txt"),  # This doesn't exist
                ]
            ),
            encoding=EncodingConfig(),
            security=SecurityConfig(),
            archive=ArchiveConfig(),
            logging=LoggingConfig(),
            preset=PresetConfig(),
        )

        logger_manager = LoggerManager(config.logging)
        processor = FileProcessor(config, logger_manager)
        files = await processor.gather_files()

        # Should still work with the existing .gitignore file
        file_names = [f[0].name for f in files]
        assert "secret.key" not in file_names
        assert "exclude_me.py" not in file_names
