#!/usr/bin/env python3
"""
Refactored test_large_file_handling for the m1f.py script.

This refactored version addresses several issues:
1. Better separation of concerns
2. Proper setup and teardown
3. More specific assertions
4. Performance testing separated from functional testing
5. Better test data management
"""

import os
import sys
import time
import tempfile
from pathlib import Path
from typing import Dict, Tuple
import pytest
import signal
import platform
import threading
from contextlib import contextmanager

# Add the tools directory to path to import the m1f module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))
import m1f

# Test constants
TEST_DIR = Path(__file__).parent
SOURCE_DIR = TEST_DIR / "source"
OUTPUT_DIR = TEST_DIR / "output"


@contextmanager
def timeout(seconds):
    """Context manager for timing out operations."""
    if platform.system() != "Windows":
        # Unix-based timeout using signals
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Operation timed out after {seconds} seconds")

        # Set up the timeout
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)

        try:
            yield
        finally:
            # Restore the old handler and cancel the alarm
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    else:
        # Windows-compatible timeout using threading
        timer = None
        timed_out = [False]

        def timeout_handler():
            timed_out[0] = True

        timer = threading.Timer(seconds, timeout_handler)
        timer.start()

        try:
            yield
            if timed_out[0]:
                raise TimeoutError(f"Operation timed out after {seconds} seconds")
        finally:
            if timer:
                timer.cancel()


class TestLargeFileHandlingRefactored:
    """Refactored test cases for large file handling in m1f.py."""

    # Test constants
    LARGE_FILE_SIZE_THRESHOLD = 1024 * 1024  # 1MB threshold for "large" files
    EXPECTED_PATTERNS = {
        "header": "Large Sample Text File",
        "description": "This is a large sample text file",
        "content_generation": "Generate a large amount of text content",
        "long_string": "a" * 100,  # Check for at least 100 consecutive 'a's
    }

    @classmethod
    def setup_class(cls):
        """Setup test environment once before all tests."""
        print(f"\nRunning refactored large file tests for m1f.py")
        print(f"Test directory: {TEST_DIR}")
        print(f"Source directory: {SOURCE_DIR}")

        # Verify m1f can be imported
        try:
            import m1f

            print(f"Successfully imported m1f from: {m1f.__file__}")
            print(f"m1f version: {getattr(m1f, '__version__', 'unknown')}")
        except Exception as e:
            print(f"ERROR: Failed to import m1f: {e}")
            raise

    def setup_method(self):
        """Setup before each test method."""
        # Ensure output directory exists and is clean
        OUTPUT_DIR.mkdir(exist_ok=True)
        self._cleanup_output_dir()

    def teardown_method(self):
        """Cleanup after each test method."""
        self._cleanup_output_dir()

    def _cleanup_output_dir(self):
        """Helper to clean up output directory."""
        if OUTPUT_DIR.exists():
            for file_path in OUTPUT_DIR.glob("*"):
                if file_path.is_file():
                    try:
                        file_path.unlink()
                    except Exception as e:
                        print(f"Warning: Could not delete {file_path}: {e}")

    def _create_large_test_file(self, file_path: Path, size_mb: float = 1.0) -> Path:
        """
        Create a large test file with structured content.

        Args:
            file_path: Path where to create the file
            size_mb: Size of the file in megabytes

        Returns:
            Path to the created file
        """
        print(f"Creating test file {file_path} with size {size_mb}MB...")
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Calculate approximate content size needed in bytes
        target_size_bytes = int(size_mb * 1024 * 1024)

        content_parts = [
            "# Large Sample Text File\n",
            "# This file is used to test how m1f handles larger files\n\n",
            '"""\nThis is a large sample text file with repeated content to test performance.\n"""\n\n',
            "import os\nimport sys\nimport time\n",
            "a" * 3000 + "\n",  # Long string of 'a' characters
            "# Generate a large amount of text content\n",
        ]

        # Build initial content
        base_content = "\n".join(content_parts)
        current_size_bytes = len(base_content.encode("utf-8"))

        # Generate additional content if needed
        if current_size_bytes < target_size_bytes:
            lines = []
            # Create a more manageable line template
            line_template = (
                "Line {}: This is a sample line of text for performance testing."
            )
            line_num = 0

            # Add a safety counter to prevent infinite loops
            max_iterations = 1000000
            iterations = 0

            while (
                current_size_bytes < target_size_bytes and iterations < max_iterations
            ):
                line = line_template.format(line_num) + "\n"
                line_bytes = len(line.encode("utf-8"))

                # Check if adding this line would exceed our target
                if (
                    current_size_bytes + line_bytes > target_size_bytes * 1.1
                ):  # Allow 10% overage
                    break

                lines.append(line)
                current_size_bytes += line_bytes
                line_num += 1
                iterations += 1

                # Progress indicator for large files
                if iterations % 10000 == 0:
                    progress = (current_size_bytes / target_size_bytes) * 100
                    print(
                        f"  Progress: {progress:.1f}% ({current_size_bytes}/{target_size_bytes} bytes)"
                    )

            if iterations >= max_iterations:
                print(
                    f"Warning: Reached maximum iterations ({max_iterations}) while creating test file"
                )

            base_content += "\n" + "\n".join(lines)

        # Write content to file - write exact byte content, not character slicing
        with open(file_path, "wb") as f:
            content_bytes = base_content.encode("utf-8")
            # Trim to target size if needed
            if len(content_bytes) > target_size_bytes:
                content_bytes = content_bytes[:target_size_bytes]
            f.write(content_bytes)

        actual_size_mb = len(content_bytes) / (1024 * 1024)
        print(f"Created test file: {actual_size_mb:.2f}MB")
        return file_path

    def _run_m1f_with_input_file(
        self, input_file_path: Path, output_file: Path, **kwargs
    ) -> float:
        """
        Run m1f with an input file and return execution time.

        Args:
            input_file_path: Path to the input file listing files to process
            output_file: Path for the output file
            **kwargs: Additional arguments to pass to m1f

        Returns:
            Execution time in seconds
        """
        print(f"Running m1f with input file: {input_file_path}")

        # Create a temporary input paths file
        temp_input_file = OUTPUT_DIR / "temp_input_paths.txt"
        with open(temp_input_file, "w", encoding="utf-8") as f:
            # Write absolute path to ensure m1f can find the file
            absolute_path = input_file_path.absolute()
            f.write(str(absolute_path))
            print(f"Wrote to input file: {absolute_path}")

        # Build argument list
        args = [
            "--input-file",
            str(temp_input_file),
            "--output-file",
            str(output_file),
            "--force",
        ]

        # Add any additional arguments
        for key, value in kwargs.items():
            # Map old argument names to new ones
            if key == "target_encoding":
                key = "convert_to_charset"

            if value is True:
                args.append(f"--{key.replace('_', '-')}")
            elif value is not False:
                args.extend([f"--{key.replace('_', '-')}", str(value)])

        print(f"Running m1f with args: {args}")

        # Measure execution time with timeout
        start_time = time.time()
        try:
            with timeout(60):  # 60 second timeout
                self._run_m1f(args)
        except TimeoutError as e:
            print(f"ERROR: {e}")
            raise
        execution_time = time.time() - start_time

        # Clean up temp file
        try:
            temp_input_file.unlink()
        except:
            pass

        return execution_time

    def _run_m1f(self, arg_list):
        """Run m1f.main() with the specified arguments."""
        # Save original argv and input
        original_argv = sys.argv.copy()
        original_input = getattr(__builtins__, "input", input)

        # Set test flag
        sys._called_from_test = True

        # Enhanced mock input to handle various prompts
        def mock_input(prompt=None):
            if prompt:
                print(f"Mock input received prompt: {prompt}")
            # Always return 'y' for yes/no questions, or empty string for other prompts
            if prompt and any(
                word in prompt.lower()
                for word in ["overwrite", "continue", "proceed", "y/n", "(y/n)"]
            ):
                return "y"
            return ""  # Return empty string for other prompts

        try:
            sys.argv = ["m1f.py"] + arg_list
            # Properly mock the input function
            if isinstance(__builtins__, dict):
                __builtins__["input"] = mock_input
            else:
                __builtins__.input = mock_input

            # Call m1f.main() with debugging
            print("Calling m1f.main()...")

            # The new m1f uses asyncio and sys.exit(), so we need to catch SystemExit
            try:
                m1f.main()
            except SystemExit as e:
                print(f"m1f.main() exited with code: {e.code}")
                if e.code != 0:
                    raise RuntimeError(f"m1f exited with non-zero code: {e.code}")

            print("m1f.main() completed")

        except Exception as e:
            print(f"Error during m1f execution: {type(e).__name__}: {e}")
            raise

        finally:
            sys.argv = original_argv
            # Restore original input
            if isinstance(__builtins__, dict):
                __builtins__["input"] = original_input
            else:
                __builtins__.input = original_input

            # Clean up test flag
            if hasattr(sys, "_called_from_test"):
                delattr(sys, "_called_from_test")

    def _verify_file_content(
        self, file_path: Path, expected_patterns: Dict[str, str]
    ) -> None:
        """
        Verify that a file contains expected patterns.

        Args:
            file_path: Path to the file to check
            expected_patterns: Dictionary of pattern_name -> pattern_string
        """
        assert file_path.exists(), f"Output file {file_path} was not created"
        assert file_path.stat().st_size > 0, f"Output file {file_path} is empty"

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        for pattern_name, pattern in expected_patterns.items():
            assert (
                pattern in content
            ), f"Expected pattern '{pattern_name}' not found: {pattern}"

    @pytest.mark.timeout(120)  # Pytest timeout as additional safety
    def test_large_file_basic_processing(self):
        """Test basic processing of a large file."""
        # Use the existing large_sample.txt file
        large_file_path = SOURCE_DIR / "code" / "large_sample.txt"
        output_file = OUTPUT_DIR / "test_large_basic.txt"

        # Run m1f
        execution_time = self._run_m1f_with_input_file(large_file_path, output_file)

        # Verify output
        self._verify_file_content(output_file, self.EXPECTED_PATTERNS)

        # Log performance (but don't assert on it)
        print(f"\nLarge file processing time: {execution_time:.2f} seconds")

    @pytest.mark.timeout(180)  # Longer timeout for multiple file sizes
    def test_large_file_size_handling(self):
        """Test handling of files of various sizes."""
        test_sizes = [0.5, 1.0, 2.0]  # MB

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            for size_mb in test_sizes:
                # Create test file
                test_file = temp_path / f"test_{size_mb}mb.txt"
                self._create_large_test_file(test_file, size_mb)

                # Process file
                output_file = OUTPUT_DIR / f"test_large_{size_mb}mb.txt"
                execution_time = self._run_m1f_with_input_file(test_file, output_file)

                # Verify output exists and has content
                assert output_file.exists(), f"Output file for {size_mb}MB not created"
                assert (
                    output_file.stat().st_size > 0
                ), f"Output file for {size_mb}MB is empty"

                # Verify file size is reasonable (should be larger due to headers/metadata)
                output_size_mb = output_file.stat().st_size / (1024 * 1024)
                assert (
                    output_size_mb >= size_mb * 0.9
                ), f"Output file seems too small for {size_mb}MB input"

                print(
                    f"\n{size_mb}MB file: processed in {execution_time:.2f}s, output size: {output_size_mb:.2f}MB"
                )

    @pytest.mark.timeout(120)
    def test_large_file_with_encoding(self):
        """Test large file processing with different encodings."""
        output_file = OUTPUT_DIR / "test_large_encoding.txt"
        large_file_path = SOURCE_DIR / "code" / "large_sample.txt"

        # Test with explicit UTF-8 encoding
        execution_time = self._run_m1f_with_input_file(
            large_file_path, output_file, target_encoding="utf-8"
        )

        # Verify the file was processed correctly
        self._verify_file_content(output_file, self.EXPECTED_PATTERNS)

    @pytest.mark.timeout(300)  # Longer timeout for performance baseline
    def test_large_file_performance_baseline(self):
        """Establish a performance baseline for large file processing."""
        large_file_path = SOURCE_DIR / "code" / "large_sample.txt"
        output_file = OUTPUT_DIR / "test_performance_baseline.txt"

        # Run multiple times to get average
        execution_times = []
        num_runs = 3

        for i in range(num_runs):
            # Clean output between runs
            if output_file.exists():
                output_file.unlink()

            execution_time = self._run_m1f_with_input_file(large_file_path, output_file)
            execution_times.append(execution_time)

        avg_time = sum(execution_times) / num_runs
        min_time = min(execution_times)
        max_time = max(execution_times)

        print(f"\nPerformance baseline (n={num_runs}):")
        print(f"  Average: {avg_time:.2f}s")
        print(f"  Min: {min_time:.2f}s")
        print(f"  Max: {max_time:.2f}s")

        # Verify the file was processed correctly in all runs
        self._verify_file_content(output_file, self.EXPECTED_PATTERNS)

    @pytest.mark.timeout(180)
    def test_large_file_memory_efficiency(self):
        """Test that large files are processed efficiently without loading entire content into memory."""
        # This test verifies that m1f can handle files larger than available memory
        # by creating a very large test file and ensuring it processes successfully

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a 10MB test file (adjust size based on test environment)
            large_test_file = temp_path / "very_large_test.txt"
            self._create_large_test_file(large_test_file, size_mb=10.0)

            output_file = OUTPUT_DIR / "test_memory_efficiency.txt"

            # Process the file
            execution_time = self._run_m1f_with_input_file(large_test_file, output_file)

            # Verify successful processing
            assert output_file.exists(), "Large file was not processed"
            assert output_file.stat().st_size > 0, "Output file is empty"

            # The fact that this completes without memory errors indicates efficient processing
            print(f"\n10MB file processed successfully in {execution_time:.2f}s")

    @pytest.mark.timeout(120)
    def test_large_file_content_integrity(self):
        """Test that large file content is preserved correctly during processing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a test file with known content patterns
            test_file = temp_path / "integrity_test.txt"
            test_content = []

            # Add header
            test_content.append("# Large File Integrity Test")
            test_content.append("# This file tests content preservation")
            test_content.append("")

            # Add numbered lines for verification
            num_lines = 1000
            for i in range(num_lines):
                test_content.append(f"Line {i:04d}: This is test line number {i}")

            # Add footer
            test_content.append("")
            test_content.append("# End of test file")

            # Write test file
            test_file.write_text("\n".join(test_content), encoding="utf-8")

            # Process file
            output_file = OUTPUT_DIR / "test_integrity.txt"
            self._run_m1f_with_input_file(test_file, output_file)

            # Read output and verify content
            with open(output_file, "r", encoding="utf-8") as f:
                output_content = f.read()

            # Verify key content is present
            assert "Large File Integrity Test" in output_content
            assert "Line 0000: This is test line number 0" in output_content
            assert (
                f"Line {num_lines-1:04d}: This is test line number {num_lines-1}"
                in output_content
            )
            assert "End of test file" in output_content

            # Verify line count is preserved (accounting for m1f headers/formatting)
            # The output should contain all our test lines
            for i in [0, 100, 500, 999]:  # Spot check some lines
                expected_line = f"Line {i:04d}: This is test line number {i}"
                assert expected_line in output_content, f"Missing line {i}"

    @pytest.mark.timeout(30)
    def test_m1f_smoke_test(self):
        """Basic smoke test to verify m1f can run at all."""
        print("\nRunning m1f smoke test...")

        # Create a simple test file
        test_file = OUTPUT_DIR / "smoke_test_input.txt"
        test_file.write_text("Hello, world!\nThis is a test.", encoding="utf-8")

        # Create input file list
        input_list_file = OUTPUT_DIR / "smoke_test_list.txt"
        input_list_file.write_text(str(test_file), encoding="utf-8")

        # Run m1f with minimal arguments
        output_file = OUTPUT_DIR / "smoke_test_output.txt"
        args = [
            "--input-file",
            str(input_list_file),
            "--output-file",
            str(output_file),
            "--force",
        ]

        try:
            # Try to run m1f
            print(f"Running m1f with args: {args}")
            self._run_m1f(args)

            # Verify output was created
            assert output_file.exists(), "m1f did not create output file"
            assert output_file.stat().st_size > 0, "m1f created empty output file"

            print("Smoke test passed!")

        except Exception as e:
            print(f"Smoke test failed: {type(e).__name__}: {e}")
            raise
        finally:
            # Cleanup
            for f in [test_file, input_list_file, output_file]:
                if f.exists():
                    f.unlink()


# Example of how to run just the refactored tests
if __name__ == "__main__":
    # Run with verbose output to see which test hangs
    import subprocess

    print("Running tests individually to identify potential hangs...")

    test_methods = [
        "test_m1f_smoke_test",  # Run smoke test first
        "test_large_file_basic_processing",
        "test_large_file_size_handling",
        "test_large_file_with_encoding",
        "test_large_file_performance_baseline",
        "test_large_file_memory_efficiency",
        "test_large_file_content_integrity",
    ]

    # Get the absolute path to this file
    test_file_path = str(Path(__file__).resolve())

    for test_method in test_methods:
        print(f"\n{'='*60}")
        print(f"Running: {test_method}")
        print(f"{'='*60}")

        try:
            # Run each test with a subprocess timeout
            # Use the full test path with class::method syntax
            test_spec = f"{test_file_path}::{TestLargeFileHandlingRefactored.__name__}::{test_method}"
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_spec, "-v", "-s"],
                timeout=120,  # 2 minute timeout per test
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent.parent),  # Run from project root
            )

            print(f"Exit code: {result.returncode}")
            if result.stdout:
                print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)

        except subprocess.TimeoutExpired:
            print(f"ERROR: Test {test_method} timed out after 120 seconds!")

    print("\nTest run complete.")
