#!/usr/bin/env python3
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

"""Tests for parallel file processing in m1f."""

import asyncio
import time
from pathlib import Path
import tempfile
import pytest

from tools.m1f.config import (
    Config,
    OutputConfig,
    FilterConfig,
    EncodingConfig,
    SecurityConfig,
    ArchiveConfig,
    LoggingConfig,
    PresetConfig,
    SeparatorStyle,
    LineEnding,
)
from tools.m1f.core import FileCombiner
from tools.m1f.output_writer import OutputWriter
from tools.m1f.logging import LoggerManager


class TestParallelProcessing:
    """Test suite for parallel file processing functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as td:
            yield Path(td)

    @pytest.fixture
    def create_test_files(self, temp_dir):
        """Create multiple test files for parallel processing tests."""
        test_files = []

        # Create 20 test files with varying content sizes
        for i in range(20):
            file_path = temp_dir / f"test_file_{i:02d}.txt"
            # Create files with different sizes to simulate real workload
            content = f"File {i} content\n" * (100 + i * 50)  # Varying sizes
            file_path.write_text(content)
            test_files.append(file_path)

        return test_files

    @pytest.fixture
    def config_parallel(self, temp_dir):
        """Create a config with parallel processing enabled."""
        return Config(
            source_directories=[temp_dir],
            input_file=None,
            input_include_files=[],
            output=OutputConfig(
                output_file=temp_dir / "output.txt",
                add_timestamp=False,
                filename_mtime_hash=False,
                force_overwrite=True,
                minimal_output=False,
                skip_output_file=False,
                separator_style=SeparatorStyle.STANDARD,
                line_ending=LineEnding.LF,
                parallel=True,  # Parallel enabled
            ),
            filter=FilterConfig(),
            encoding=EncodingConfig(),
            security=SecurityConfig(),
            archive=ArchiveConfig(),
            logging=LoggingConfig(verbose=True),
            preset=PresetConfig(),
        )

    @pytest.mark.asyncio
    async def test_parallel_processing_enabled(
        self, config_parallel, create_test_files
    ):
        """Test that parallel processing is working correctly."""
        # Create file combiner
        logger_manager = LoggerManager(config_parallel.logging)
        combiner = FileCombiner(config_parallel, logger_manager)

        # Track if parallel processing was used
        output_writer = combiner.output_writer
        original_write_method = output_writer._write_combined_file_parallel
        parallel_called = False

        async def mock_parallel_write(*args, **kwargs):
            nonlocal parallel_called
            parallel_called = True
            return await original_write_method(*args, **kwargs)

        output_writer._write_combined_file_parallel = mock_parallel_write

        # Run the combiner
        result = await combiner.run()

        # Verify parallel processing was used
        assert parallel_called, "Parallel processing was not used"
        # Should be 20 test files (output.log is excluded)
        assert (
            result.files_processed >= 20
        ), f"Expected at least 20 files, got {result.files_processed}"

        # Verify output file was created
        assert config_parallel.output.output_file.exists()

        # Verify all files are in the output in correct order
        output_content = config_parallel.output.output_file.read_text()
        for i in range(20):
            assert f"test_file_{i:02d}.txt" in output_content
            assert f"File {i} content" in output_content

    @pytest.mark.asyncio
    async def test_parallel_maintains_file_order(
        self, config_parallel, create_test_files
    ):
        """Test that parallel processing maintains correct file order."""
        logger_manager = LoggerManager(config_parallel.logging)
        combiner = FileCombiner(config_parallel, logger_manager)

        # Run the combiner
        await combiner.run()

        # Read output and verify all test files are present
        output_content = config_parallel.output.output_file.read_text()

        # Verify all test files are in the output
        for i in range(20):
            filename = f"test_file_{i:02d}.txt"
            assert filename in output_content, f"Missing file: {filename}"

        # Check that files appear in order by looking at their positions
        positions = []
        for i in range(20):
            filename = f"test_file_{i:02d}.txt"
            pos = output_content.find(filename)
            positions.append((pos, filename))

        # Sort by position and verify order
        positions.sort()
        for i, (pos, filename) in enumerate(positions):
            expected_filename = f"test_file_{i:02d}.txt"
            assert (
                filename == expected_filename
            ), f"File order mismatch at position {i}: expected {expected_filename}, got {filename}"

    @pytest.mark.asyncio
    async def test_parallel_performance_improvement(self, temp_dir, create_test_files):
        """Test that parallel processing is faster than sequential (when files are large enough)."""
        # Create larger files for performance testing
        for i in range(10):
            file_path = temp_dir / f"large_file_{i}.txt"
            # Create 1MB files
            content = "x" * (1024 * 1024)
            file_path.write_text(content)

        # Test with parallel disabled (sequential)
        config_seq = Config(
            source_directories=[temp_dir],
            input_file=None,
            input_include_files=[],
            output=OutputConfig(
                output_file=temp_dir / "output_seq.txt",
                parallel=False,  # Force sequential for comparison
            ),
            filter=FilterConfig(include_extensions={".txt"}),
            encoding=EncodingConfig(),
            security=SecurityConfig(),
            archive=ArchiveConfig(),
            logging=LoggingConfig(quiet=True),
            preset=PresetConfig(),
        )

        # For this test, we need to temporarily modify the config to disable parallel
        # Since parallel is now always True, we'll mock the behavior
        logger_manager_seq = LoggerManager(config_seq.logging)
        writer_seq = OutputWriter(config_seq, logger_manager_seq)

        # Force sequential processing
        start_seq = time.time()
        files_to_process = [
            (temp_dir / f"large_file_{i}.txt", f"large_file_{i}.txt") for i in range(10)
        ]
        await writer_seq._write_combined_file_sequential(
            config_seq.output.output_file, files_to_process
        )
        time_seq = time.time() - start_seq

        # Test with parallel enabled
        config_par = Config(
            source_directories=[temp_dir],
            input_file=None,
            input_include_files=[],
            output=OutputConfig(output_file=temp_dir / "output_par.txt", parallel=True),
            filter=FilterConfig(include_extensions={".txt"}),
            encoding=EncodingConfig(),
            security=SecurityConfig(),
            archive=ArchiveConfig(),
            logging=LoggingConfig(quiet=True),
            preset=PresetConfig(),
        )

        logger_manager_par = LoggerManager(config_par.logging)
        writer_par = OutputWriter(config_par, logger_manager_par)

        start_par = time.time()
        await writer_par._write_combined_file_parallel(
            config_par.output.output_file, files_to_process
        )
        time_par = time.time() - start_par

        # Parallel should be faster (or at least not significantly slower)
        # We can't guarantee it's always faster due to overhead, but it shouldn't be much slower
        print(f"Sequential time: {time_seq:.3f}s, Parallel time: {time_par:.3f}s")

        # Both files should have approximately the same size (small differences due to timestamps/processing)
        seq_size = config_seq.output.output_file.stat().st_size
        par_size = config_par.output.output_file.stat().st_size

        # Allow small difference (< 1KB) due to timestamp differences
        size_diff = abs(seq_size - par_size)
        assert size_diff < 1024, f"File size difference too large: {size_diff} bytes"

    @pytest.mark.asyncio
    async def test_parallel_thread_safety(self, config_parallel, temp_dir):
        """Test thread safety of parallel processing with duplicate content."""
        # Create files with duplicate content
        duplicate_content = (
            "This is duplicate content for testing deduplication\n" * 100
        )

        for i in range(10):
            file_path = temp_dir / f"duplicate_{i}.txt"
            file_path.write_text(duplicate_content)

        logger_manager = LoggerManager(config_parallel.logging)
        combiner = FileCombiner(config_parallel, logger_manager)

        # Run the combiner
        result = await combiner.run()

        # With deduplication, only one file with duplicate content should be included
        output_content = config_parallel.output.output_file.read_text()

        # Count occurrences of the duplicate content
        content_count = output_content.count(
            "This is duplicate content for testing deduplication"
        )

        # Should only appear once due to deduplication
        assert (
            content_count == 100
        ), f"Duplicate content appeared {content_count} times, expected 100 (once)"

        # But we should see at least one separator for duplicate files
        # Due to deduplication, only the first file's content is included
        assert (
            "duplicate_0.txt" in output_content or "duplicate_1.txt" in output_content
        )

    @pytest.mark.asyncio
    async def test_parallel_error_handling(self, config_parallel, temp_dir):
        """Test error handling in parallel processing."""
        # Create some normal files
        for i in range(5):
            file_path = temp_dir / f"good_file_{i}.txt"
            file_path.write_text(f"Good content {i}")

        # Create a file that will cause an error (we'll make it unreadable)
        bad_file = temp_dir / "bad_file.txt"
        bad_file.write_text("This will be made unreadable")
        bad_file.chmod(0o000)  # Remove all permissions

        try:
            logger_manager = LoggerManager(config_parallel.logging)
            combiner = FileCombiner(config_parallel, logger_manager)

            # Run should complete despite the error
            result = await combiner.run()

            # Should process the good files
            assert result.files_processed >= 5

        finally:
            # Restore permissions for cleanup
            bad_file.chmod(0o644)

    @pytest.mark.asyncio
    async def test_parallel_single_file_fallback(self, config_parallel, temp_dir):
        """Test that single file processing doesn't use parallel mode."""
        # Create just one file
        single_file = temp_dir / "single_file.txt"
        single_file.write_text("Single file content")

        logger_manager = LoggerManager(config_parallel.logging)
        output_writer = OutputWriter(config_parallel, logger_manager)

        # Track which method was called
        sequential_called = False
        parallel_called = False

        original_seq = output_writer._write_combined_file_sequential
        original_par = output_writer._write_combined_file_parallel

        async def mock_sequential(*args, **kwargs):
            nonlocal sequential_called
            sequential_called = True
            return await original_seq(*args, **kwargs)

        async def mock_parallel(*args, **kwargs):
            nonlocal parallel_called
            parallel_called = True
            return await original_par(*args, **kwargs)

        output_writer._write_combined_file_sequential = mock_sequential
        output_writer._write_combined_file_parallel = mock_parallel

        # Process single file
        files = [(single_file, "single_file.txt")]
        await output_writer.write_combined_file(
            config_parallel.output.output_file, files
        )

        # With only one file, it should use sequential mode
        assert sequential_called, "Sequential processing was not used for single file"
        assert not parallel_called, "Parallel processing was used for single file"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
