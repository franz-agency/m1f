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
    async def test_async_file_extraction(
        self,
        create_combined_file,
        temp_dir
    ):
        """Test async file extraction capabilities."""
        # Create a set of files
        test_files = {
            f"file{i}.txt": f"Content of file {i}\n" * 100
            for i in range(10)
        }
        
        combined_file = create_combined_file(test_files, "Standard")
        extract_dir = temp_dir / "async_extract"
        
        # Import s1f modules directly for async testing
        from s1f.core import S1FExtractor
        from s1f.config import ExtractionConfig
        
        # Create config
        config = ExtractionConfig(
            input_file=combined_file,
            destination_directory=extract_dir,
            force_overwrite=True,
            verbose=True,
        )
        
        # Run extraction
        extractor = S1FExtractor(config)
        result = await extractor.extract_async()
        
        # Verify all files were extracted
        assert result.success
        assert result.extracted_count == len(test_files)
        
        for filename in test_files:
            extracted_file = extract_dir / filename
            assert extracted_file.exists()
            assert extracted_file.read_text() == test_files[filename]
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_concurrent_file_writing(
        self,
        temp_dir
    ):
        """Test concurrent file writing functionality."""
        from s1f.writers import AsyncFileWriter
        from s1f.models import ExtractedFile
        
        # Create test files to write
        files = [
            ExtractedFile(
                path=temp_dir / f"concurrent_{i}.txt",
                content=f"Concurrent content {i}",
                metadata=None
            )
            for i in range(20)
        ]
        
        # Write files concurrently
        writer = AsyncFileWriter()
        results = await writer.write_files_async(files)
        
        # Verify all files were written
        assert len(results) == len(files)
        assert all(result.success for result in results)
        
        for i, file in enumerate(files):
            assert file.path.exists()
            assert file.path.read_text() == f"Concurrent content {i}"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_async_error_handling(
        self,
        create_combined_file,
        temp_dir
    ):
        """Test error handling in async operations."""
        # Create a file with problematic path
        test_files = {
            "normal.txt": "Normal content",
            "/invalid/path/file.txt": "This should fail",
        }
        
        combined_file = create_combined_file(test_files)
        extract_dir = temp_dir / "error_test"
        
        from s1f.core import S1FExtractor
        from s1f.config import ExtractionConfig
        
        config = ExtractionConfig(
            input_file=combined_file,
            destination_directory=extract_dir,
            force_overwrite=True,
        )
        
        extractor = S1FExtractor(config)
        result = await extractor.extract_async()
        
        # Should handle errors gracefully
        assert result.extracted_count >= 1  # At least normal.txt
        assert result.error_count >= 1  # At least the invalid path
        
        # Normal file should be extracted
        assert (extract_dir / "normal.txt").exists()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_large_file_async_extraction(
        self,
        create_combined_file,
        temp_dir
    ):
        """Test async extraction of large files."""
        # Create large files
        large_content = "x" * (1024 * 1024)  # 1MB per file
        test_files = {
            f"large_{i}.txt": large_content
            for i in range(5)
        }
        
        combined_file = create_combined_file(test_files)
        extract_dir = temp_dir / "large_async"
        
        from s1f.core import S1FExtractor
        from s1f.config import ExtractionConfig
        
        config = ExtractionConfig(
            input_file=combined_file,
            destination_directory=extract_dir,
            force_overwrite=True,
        )
        
        # Time the async extraction
        import time
        start_time = time.time()
        
        extractor = S1FExtractor(config)
        result = await extractor.extract_async()
        
        elapsed = time.time() - start_time
        
        # Verify extraction
        assert result.success
        assert result.extracted_count == len(test_files)
        
        # Check that files were written correctly
        for filename in test_files:
            file_path = extract_dir / filename
            assert file_path.exists()
            assert file_path.stat().st_size == len(large_content)
        
        print(f"Async extraction took {elapsed:.2f} seconds")
    
    @pytest.mark.unit
    def test_async_fallback_to_sync(
        self,
        monkeypatch,
        create_combined_file,
        temp_dir
    ):
        """Test fallback to sync operations when async is not available."""
        # Mock aiofiles to not be available
        import sys
        monkeypatch.setattr("sys.modules", {
            **sys.modules,
            "aiofiles": None,
        })
        
        test_files = {
            "test.txt": "Test content",
        }
        
        combined_file = create_combined_file(test_files)
        
        # This should work even without aiofiles
        from s1f.cli import main
        
        # Mock sys.argv
        monkeypatch.setattr("sys.argv", [
            "s1f",
            "--input-file", str(combined_file),
            "--destination-directory", str(temp_dir),
            "--force",
        ])
        
        # Should complete successfully using sync fallback
        try:
            main()
        except SystemExit as e:
            assert e.code == 0
        
        # Verify file was extracted
        assert (temp_dir / "test.txt").exists()
        assert (temp_dir / "test.txt").read_text() == "Test content" 