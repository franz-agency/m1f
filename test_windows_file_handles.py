#!/usr/bin/env python3
"""
Test script to validate Windows file handle cleanup fixes.

This script creates multiple test scenarios that previously caused
WinError 32 permission errors and verifies they now work correctly.
"""

import asyncio
import gc
import os
import sys
import tempfile
import time
from pathlib import Path
import shutil

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent / "tools"))

from m1f.config import Config, OutputConfig, FilterConfig, EncodingConfig, SecurityConfig, ArchiveConfig, LoggingConfig, PresetConfig
from m1f.core import FileCombiner
from m1f.logging import LoggerManager


def test_file_handle_cleanup():
    """Test that file handles are properly cleaned up on Windows."""
    print("Testing Windows file handle cleanup...")
    
    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp(prefix="test_file_handles_"))
    
    try:
        # Create test files
        print(f"Creating test files in {temp_dir}")
        for i in range(10):
            test_file = temp_dir / f"test_{i:02d}.txt"
            test_file.write_text(f"Test content {i}\n" * 100)
        
        # Create config for parallel processing
        config = Config(
            source_directories=[temp_dir],
            input_file=None,
            input_include_files=[],
            output=OutputConfig(
                output_file=temp_dir / "output.txt",
                parallel=True,
                force_overwrite=True,
            ),
            filter=FilterConfig(),
            encoding=EncodingConfig(),
            security=SecurityConfig(),
            archive=ArchiveConfig(),
            logging=LoggingConfig(quiet=True),
            preset=PresetConfig(),
        )
        
        # Run combiner
        print("Running file combiner with parallel processing...")
        logger_manager = LoggerManager(config.logging)
        combiner = FileCombiner(config, logger_manager)
        
        async def run_test():
            result = await combiner.run()
            print(f"Processed {result.files_processed} files")
            return result
        
        # Run the test
        result = asyncio.run(run_test())
        
        # Force garbage collection
        gc.collect()
        time.sleep(0.1)  # Give Windows time to release handles
        
        # Try to remove files immediately - this would fail with WinError 32 before the fix
        print("Testing immediate file deletion (this would fail with WinError 32 before fix)...")
        for i in range(10):
            test_file = temp_dir / f"test_{i:02d}.txt"
            try:
                test_file.unlink()
                print(f"OK Successfully deleted {test_file.name}")
            except PermissionError as e:
                print(f"FAIL Failed to delete {test_file.name}: {e}")
                return False
        
        # Try to remove output file
        output_file = temp_dir / "output.txt"
        if output_file.exists():
            try:
                output_file.unlink()
                print(f"OK Successfully deleted {output_file.name}")
            except PermissionError as e:
                print(f"FAIL Failed to delete {output_file.name}: {e}")
                return False
        
        print("OK All file handles properly cleaned up!")
        return True
        
    except Exception as e:
        print(f"FAIL Test failed with error: {e}")
        return False
    finally:
        # Clean up temp directory
        try:
            if temp_dir.exists():
                # Force garbage collection before cleanup
                gc.collect()
                time.sleep(0.1)
                
                # Remove read-only attributes on Windows
                if sys.platform.startswith("win"):
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            try:
                                file_path = Path(root) / file
                                file_path.chmod(0o666)
                            except:
                                pass
                        for dir_name in dirs:
                            try:
                                dir_path = Path(root) / dir_name
                                dir_path.chmod(0o777)
                            except:
                                pass
                
                shutil.rmtree(temp_dir)
                print(f"OK Cleaned up temporary directory {temp_dir}")
        except Exception as e:
            print(f"Warning: Could not clean up {temp_dir}: {e}")


def test_encoding_detection_cleanup():
    """Test that encoding detection properly releases file handles."""
    print("\nTesting encoding detection file handle cleanup...")
    
    temp_dir = Path(tempfile.mkdtemp(prefix="test_encoding_handles_"))
    
    try:
        # Create test files with different encodings
        test_files = []
        
        # UTF-8 file
        utf8_file = temp_dir / "utf8_test.txt"
        utf8_file.write_text("Hello, 世界! 🌍", encoding="utf-8")
        test_files.append(utf8_file)
        
        # Latin-1 file
        latin1_file = temp_dir / "latin1_test.txt"
        latin1_file.write_text("Café résumé naïve", encoding="latin-1")
        test_files.append(latin1_file)
        
        # Binary file
        binary_file = temp_dir / "binary_test.bin"
        binary_file.write_bytes(b"\\x00\\x01\\x02\\x03" * 100)
        test_files.append(binary_file)
        
        # Create config
        config = Config(
            source_directories=[temp_dir],
            input_file=None,
            input_include_files=[],
            output=OutputConfig(
                output_file=temp_dir / "output.txt",
                force_overwrite=True,
            ),
            filter=FilterConfig(include_binary_files=True),
            encoding=EncodingConfig(target_charset="utf-8"),
            security=SecurityConfig(),
            archive=ArchiveConfig(),
            logging=LoggingConfig(quiet=True),
            preset=PresetConfig(),
        )
        
        # Run processing
        print("Running encoding detection and file processing...")
        logger_manager = LoggerManager(config.logging)
        combiner = FileCombiner(config, logger_manager)
        
        async def run_encoding_test():
            result = await combiner.run()
            print(f"Processed {result.files_processed} files with encoding detection")
            return result
        
        result = asyncio.run(run_encoding_test())
        
        # Force garbage collection
        gc.collect()
        time.sleep(0.1)
        
        # Try to delete files immediately
        print("Testing immediate file deletion after encoding detection...")
        for test_file in test_files:
            try:
                test_file.unlink()
                print(f"OK Successfully deleted {test_file.name}")
            except PermissionError as e:
                print(f"FAIL Failed to delete {test_file.name}: {e}")
                return False
        
        # Try to delete output file
        output_file = temp_dir / "output.txt"
        if output_file.exists():
            try:
                output_file.unlink()
                print(f"OK Successfully deleted {output_file.name}")
            except PermissionError as e:
                print(f"FAIL Failed to delete {output_file.name}: {e}")
                return False
        
        print("OK Encoding detection file handles properly cleaned up!")
        return True
        
    except Exception as e:
        print(f"FAIL Encoding test failed with error: {e}")
        return False
    finally:
        # Clean up
        try:
            if temp_dir.exists():
                gc.collect()
                time.sleep(0.1)
                shutil.rmtree(temp_dir)
                print(f"OK Cleaned up encoding test directory {temp_dir}")
        except Exception as e:
            print(f"Warning: Could not clean up {temp_dir}: {e}")


def main():
    """Run all Windows file handle tests."""
    print("Windows File Handle Cleanup Test Suite")
    print("=" * 50)
    print(f"Platform: {sys.platform}")
    print(f"Python: {sys.version}")
    
    if not sys.platform.startswith("win"):
        print("Note: These tests are designed for Windows but will run on other platforms")
    
    print()
    
    success = True
    
    # Test 1: Basic file handle cleanup
    success &= test_file_handle_cleanup()
    
    # Test 2: Encoding detection cleanup
    success &= test_encoding_detection_cleanup()
    
    print("\n" + "=" * 50)
    if success:
        print("OK All Windows file handle tests passed!")
        print("OK WinError 32 permission errors should be resolved")
        return 0
    else:
        print("FAIL Some tests failed - WinError 32 issues may still exist")
        return 1


if __name__ == "__main__":
    exit(main())