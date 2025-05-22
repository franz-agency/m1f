"""Base test classes and utilities for the test suite."""

from __future__ import annotations

import hashlib
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterable


class BaseToolTest(ABC):
    """Base class for tool testing with common utilities."""
    
    @abstractmethod
    def tool_name(self) -> str:
        """Return the name of the tool being tested."""
        ...
    
    def calculate_file_hash(self, file_path: Path, algorithm: str = "sha256") -> str:
        """
        Calculate hash of a file.
        
        Args:
            file_path: Path to the file
            algorithm: Hash algorithm to use
            
        Returns:
            Hex string of the file hash
        """
        hasher = hashlib.new(algorithm)
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def verify_file_content(
        self, 
        file_path: Path, 
        expected_content: str | bytes,
        encoding: str | None = "utf-8"
    ) -> bool:
        """
        Verify file content matches expected.
        
        Args:
            file_path: Path to file to verify
            expected_content: Expected content
            encoding: File encoding (None for binary)
            
        Returns:
            True if content matches
        """
        if isinstance(expected_content, str) and encoding:
            actual_content = file_path.read_text(encoding=encoding)
            return actual_content == expected_content
        else:
            actual_content = file_path.read_bytes()
            if isinstance(expected_content, str):
                expected_content = expected_content.encode(encoding or "utf-8")
            return actual_content == expected_content
    
    def verify_file_structure(
        self, 
        base_path: Path, 
        expected_structure: dict[str, str | dict],
        allow_extra: bool = True
    ) -> tuple[bool, list[str]]:
        """
        Verify directory structure matches expected.
        
        Args:
            base_path: Base directory to check
            expected_structure: Expected structure dict
            allow_extra: Whether to allow extra files
            
        Returns:
            Tuple of (success, list of error messages)
        """
        errors = []
        
        def check_structure(
            current_path: Path, 
            structure: dict[str, str | dict], 
            prefix: str = ""
        ):
            for name, content in structure.items():
                full_path = current_path / name
                display_path = f"{prefix}{name}"
                
                if isinstance(content, dict):
                    # Directory
                    if not full_path.is_dir():
                        errors.append(f"Missing directory: {display_path}")
                    else:
                        check_structure(full_path, content, f"{display_path}/")
                else:
                    # File
                    if not full_path.is_file():
                        errors.append(f"Missing file: {display_path}")
                    elif content and not self.verify_file_content(full_path, content):
                        errors.append(f"Content mismatch: {display_path}")
            
            if not allow_extra:
                # Check for unexpected files
                expected_names = set(structure.keys())
                actual_names = {p.name for p in current_path.iterdir()}
                extra = actual_names - expected_names
                if extra:
                    for name in extra:
                        errors.append(f"Unexpected item: {prefix}{name}")
        
        check_structure(base_path, expected_structure)
        return len(errors) == 0, errors
    
    def wait_for_file_operations(self, timeout: float = 0.1):
        """Wait for file operations to complete."""
        time.sleep(timeout)
    
    def assert_files_equal(
        self, 
        file1: Path, 
        file2: Path, 
        encoding: str | None = "utf-8"
    ):
        """Assert two files have identical content."""
        if encoding:
            content1 = file1.read_text(encoding=encoding)
            content2 = file2.read_text(encoding=encoding)
        else:
            content1 = file1.read_bytes()
            content2 = file2.read_bytes()
        
        assert content1 == content2, f"Files differ: {file1} vs {file2}"
    
    def assert_file_contains(
        self, 
        file_path: Path, 
        expected_content: str | list[str],
        encoding: str = "utf-8"
    ):
        """Assert file contains expected content."""
        content = file_path.read_text(encoding=encoding)
        
        if isinstance(expected_content, str):
            expected_content = [expected_content]
        
        for expected in expected_content:
            assert expected in content, f"'{expected}' not found in {file_path}"
    
    def assert_file_not_contains(
        self, 
        file_path: Path, 
        unexpected_content: str | list[str],
        encoding: str = "utf-8"
    ):
        """Assert file does not contain unexpected content."""
        content = file_path.read_text(encoding=encoding)
        
        if isinstance(unexpected_content, str):
            unexpected_content = [unexpected_content]
        
        for unexpected in unexpected_content:
            assert unexpected not in content, f"'{unexpected}' found in {file_path}"
    
    def get_file_list(
        self, 
        directory: Path, 
        pattern: str = "**/*",
        exclude_dirs: bool = True
    ) -> list[Path]:
        """
        Get list of files in directory.
        
        Args:
            directory: Directory to scan
            pattern: Glob pattern
            exclude_dirs: Whether to exclude directories
            
        Returns:
            List of file paths
        """
        files = list(directory.glob(pattern))
        if exclude_dirs:
            files = [f for f in files if f.is_file()]
        return sorted(files)
    
    def compare_file_lists(
        self, 
        list1: Iterable[Path], 
        list2: Iterable[Path],
        compare_relative: bool = True
    ) -> tuple[set[Path], set[Path], set[Path]]:
        """
        Compare two file lists.
        
        Args:
            list1: First list of files
            list2: Second list of files
            compare_relative: Whether to compare relative paths
            
        Returns:
            Tuple of (only_in_list1, only_in_list2, in_both)
        """
        if compare_relative:
            # Find common base path
            all_paths = list(list1) + list(list2)
            if all_paths:
                import os
                common_base = Path(os.path.commonpath([str(p) for p in all_paths]))
                set1 = {p.relative_to(common_base) for p in list1}
                set2 = {p.relative_to(common_base) for p in list2}
            else:
                set1 = set()
                set2 = set()
        else:
            set1 = set(list1)
            set2 = set(list2)
        
        only_in_list1 = set1 - set2
        only_in_list2 = set2 - set1
        in_both = set1 & set2
        
        return only_in_list1, only_in_list2, in_both


class BaseM1FTest(BaseToolTest):
    """Base class for m1f tests."""
    
    def tool_name(self) -> str:
        return "m1f"
    
    def verify_m1f_output(
        self, 
        output_file: Path,
        expected_files: list[Path] | None = None,
        expected_separator_style: str = "Standard"
    ) -> bool:
        """
        Verify m1f output file.
        
        Args:
            output_file: Path to the output file
            expected_files: List of expected files in output
            expected_separator_style: Expected separator style
            
        Returns:
            True if output is valid
        """
        assert output_file.exists(), f"Output file {output_file} does not exist"
        assert output_file.stat().st_size > 0, f"Output file {output_file} is empty"
        
        content = output_file.read_text(encoding="utf-8")
        
        # Check for separator style markers
        style_markers = {
            "Standard": "FILE:",
            "Detailed": "==== FILE:",
            "Markdown": "```",
            "MachineReadable": "PYMK1F_BEGIN_FILE_METADATA_BLOCK",
        }
        
        if expected_separator_style in style_markers:
            marker = style_markers[expected_separator_style]
            assert marker in content, f"Expected {expected_separator_style} marker not found"
        
        # Check for expected files
        if expected_files:
            for file_path in expected_files:
                assert str(file_path) in content or file_path.name in content, \
                    f"Expected file {file_path} not found in output"
        
        return True


class BaseS1FTest(BaseToolTest):
    """Base class for s1f tests."""
    
    def tool_name(self) -> str:
        return "s1f"
    
    def verify_extraction(
        self,
        original_dir: Path,
        extracted_dir: Path,
        expected_count: int | None = None
    ) -> tuple[int, int, int]:
        """
        Verify extracted files match originals.
        
        Args:
            original_dir: Original source directory
            extracted_dir: Directory where files were extracted
            expected_count: Expected number of files
            
        Returns:
            Tuple of (matching_count, missing_count, different_count)
        """
        original_files = self.get_file_list(original_dir)
        extracted_files = self.get_file_list(extracted_dir)
        
        if expected_count is not None:
            assert len(extracted_files) == expected_count, \
                f"Expected {expected_count} files, found {len(extracted_files)}"
        
        matching = 0
        missing = 0
        different = 0
        
        for orig_file in original_files:
            rel_path = orig_file.relative_to(original_dir)
            extracted_file = extracted_dir / rel_path
            
            if not extracted_file.exists():
                missing += 1
            elif self.calculate_file_hash(orig_file) == self.calculate_file_hash(extracted_file):
                matching += 1
            else:
                different += 1
        
        return matching, missing, different 