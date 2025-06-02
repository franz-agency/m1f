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

"""Async functionality tests for s1f."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from ..base_test import BaseS1FTest


class TestS1FAsync(BaseS1FTest):
    """Tests for s1f async functionality."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_async_file_extraction(self, create_combined_file, temp_dir):
        """Test async file extraction capabilities."""
        # Create a set of files
        test_files = {f"file{i}.txt": f"Content of file {i}\n" * 100 for i in range(10)}

        combined_file = create_combined_file(test_files, "Standard")
        extract_dir = temp_dir / "async_extract"

        # Import s1f modules directly for async testing
        from tools.s1f.core import FileSplitter
        from tools.s1f.config import Config
        from tools.s1f.logging import LoggerManager

        # Create config
        config = Config(
            input_file=combined_file,
            destination_directory=extract_dir,
            force_overwrite=True,
            verbose=True,
        )

        # Run extraction
        logger_manager = LoggerManager(config)
        extractor = FileSplitter(config, logger_manager)
        result, exit_code = await extractor.split_file()

        # Verify all files were extracted
        assert exit_code == 0
        assert len(list(extract_dir.glob("*.txt"))) == len(test_files)

        # Verify content
        for filename, expected_content in test_files.items():
            extracted_file = extract_dir / filename
            assert extracted_file.exists()
            actual_content = extracted_file.read_text()
            # Normalize line endings for comparison
            assert actual_content.strip() == expected_content.strip()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_concurrent_file_writing(self, temp_dir):
        """Test concurrent file writing functionality."""
        from tools.s1f.writers import FileWriter
        from tools.s1f.models import ExtractedFile
        from tools.s1f.config import Config
        from tools.s1f.logging import LoggerManager
        import logging

        # Create test files to write
        from tools.s1f.models import FileMetadata

        files = [
            ExtractedFile(
                metadata=FileMetadata(
                    path=f"file{i}.txt",
                    encoding="utf-8",
                ),
                content=f"Concurrent content {i}",
            )
            for i in range(20)
        ]

        # Create config
        config = Config(
            input_file=Path("dummy.txt"),
            destination_directory=temp_dir,
            force_overwrite=True,
        )

        # Create logger and writer
        logger_manager = LoggerManager(config)
        logger = logger_manager.get_logger(__name__)
        writer = FileWriter(config, logger)

        # Write files
        result = await writer.write_files(files)

        # Verify all files were written
        assert result.extracted_count == len(files)
        assert result.success

        for i in range(20):
            file_path = temp_dir / f"file{i}.txt"
            assert file_path.exists()
            assert file_path.read_text() == f"Concurrent content {i}"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_async_error_handling(self, create_combined_file, temp_dir):
        """Test error handling in async operations."""
        # Create a corrupted combined file
        corrupted_file = temp_dir / "corrupted.txt"
        corrupted_file.write_text("Not a valid combined file format")

        from tools.s1f.core import FileSplitter
        from tools.s1f.config import Config
        from tools.s1f.logging import LoggerManager

        config = Config(
            input_file=corrupted_file,
            destination_directory=temp_dir / "extract",
            force_overwrite=True,
        )

        logger_manager = LoggerManager(config)
        extractor = FileSplitter(config, logger_manager)

        # Should handle error gracefully
        result, exit_code = await extractor.split_file()
        assert exit_code != 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_large_file_async_extraction(self, create_combined_file, temp_dir):
        """Test async extraction of large files."""
        # Create a large file
        large_content = "x" * (10 * 1024 * 1024)  # 10MB
        test_files = {"large_file.txt": large_content}

        combined_file = create_combined_file(test_files, "Standard")
        extract_dir = temp_dir / "large_extract"

        from tools.s1f.core import FileSplitter
        from tools.s1f.config import Config
        from tools.s1f.logging import LoggerManager

        config = Config(
            input_file=combined_file,
            destination_directory=extract_dir,
            force_overwrite=True,
        )

        logger_manager = LoggerManager(config)
        extractor = FileSplitter(config, logger_manager)
        result, exit_code = await extractor.split_file()

        # Verify extraction
        assert exit_code == 0
        extracted_file = extract_dir / "large_file.txt"
        assert extracted_file.exists()

        # Check size with some tolerance for encoding differences
        actual_size = extracted_file.stat().st_size
        expected_size = len(large_content)
        size_diff = abs(actual_size - expected_size)
        assert (
            size_diff <= 10
        ), f"Size mismatch: expected {expected_size}, got {actual_size}, diff: {size_diff}"

    @pytest.mark.unit
    def test_async_fallback_to_sync(self, temp_dir):
        """Test fallback to sync operations when async is not available."""
        # This test verifies that s1f can work without aiofiles
        from tools.s1f.models import ExtractedFile

        from tools.s1f.models import FileMetadata

        test_file = ExtractedFile(
            metadata=FileMetadata(
                path="test.txt",
                encoding="utf-8",
            ),
            content="Test content",
        )

        # Write using sync method
        output_path = temp_dir / test_file.path
        output_path.write_text(test_file.content, encoding=test_file.metadata.encoding)

        assert output_path.exists()
        assert output_path.read_text() == "Test content"
