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

"""File writers for s1f."""

import asyncio
import os
from pathlib import Path
from typing import List, Optional, Tuple
import threading
import logging
from datetime import datetime

from .config import Config
from .models import ExtractedFile, ExtractionResult
from .utils import (
    validate_file_path,
    calculate_sha256,
    clean_encoding_name,
    format_size,
    normalize_line_endings,
)
from .exceptions import FileWriteError, ChecksumMismatchError

# Try absolute imports first (for module execution), fall back to relative
try:
    from tools.m1f.file_operations import (
        safe_exists,
        safe_mkdir,
        safe_open,
        safe_write_text,
        safe_read_text,
    )
except ImportError:
    # Fallback for direct script execution
    from ..m1f.file_operations import (
        safe_exists,
        safe_mkdir,
        safe_open,
        safe_write_text,
        safe_read_text,
    )

try:
    import aiofiles

    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False


class FileWriter:
    """Handles writing extracted files to disk."""

    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self._counter_lock = asyncio.Lock()  # For thread-safe counter updates
        self._write_semaphore = asyncio.Semaphore(
            10
        )  # Limit concurrent writes to prevent "too many open files"

    async def write_files(
        self, extracted_files: List[ExtractedFile]
    ) -> ExtractionResult:
        """Write all extracted files to the destination directory."""
        result = ExtractionResult()

        self.logger.info(
            f"Writing {len(extracted_files)} extracted file(s) to '{self.config.destination_directory}'..."
        )

        # Create tasks for concurrent file writing if async is available
        if AIOFILES_AVAILABLE:
            tasks = [
                self._write_file_async(file_data, result)
                for file_data in extracted_files
            ]
            # Gather results and handle exceptions properly
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check for exceptions in results
            for i, result_or_exc in enumerate(results):
                if isinstance(result_or_exc, Exception):
                    # An exception occurred during file writing
                    file_data = extracted_files[i]
                    async with self._counter_lock:
                        result.files_failed += 1
                    logger.error(
                        f"Failed to write file {file_data.relative_path}: {result_or_exc}"
                    )
        else:
            # Fallback to synchronous writing
            for file_data in extracted_files:
                await self._write_file_sync(file_data, result)

        return result

    async def _write_file_async(
        self, file_data: ExtractedFile, result: ExtractionResult
    ):
        """Write a single file asynchronously."""
        async with self._write_semaphore:  # Limit concurrent file operations
            try:
                output_path = await self._prepare_output_path(file_data)
                if output_path is None:
                    async with self._counter_lock:
                        result.files_failed += 1
                    return

                # Check if file exists
                is_overwrite = safe_exists(output_path, logger=self.logger)

                if is_overwrite and not self.config.force_overwrite:
                    if not await self._confirm_overwrite_async(output_path):
                        self.logger.info(f"Skipping existing file '{output_path}'")
                        return

                # Determine encoding
                encoding = self._determine_encoding(file_data)

                # Write the file
                content_bytes = await self._encode_content(
                    file_data.content, encoding, file_data.path
                )

                # Use safe_open for the aiofiles case
                # Note: We need to handle this differently since safe_open doesn't support async
                # For now, keep the aiofiles.open but add error handling
                try:
                    async with aiofiles.open(output_path, "wb") as f:
                        await f.write(content_bytes)
                except PermissionError as e:
                    self.logger.warning(
                        f"Permission denied writing to '{output_path}': {e}"
                    )
                    async with self._counter_lock:
                        result.files_failed += 1
                    return

                # Update result with thread-safe counter increment
                async with self._counter_lock:
                    if is_overwrite:
                        result.files_overwritten += 1
                        self.logger.debug(f"Overwrote file: {output_path}")
                    else:
                        result.files_created += 1
                        self.logger.debug(f"Created file: {output_path}")

                # Set file timestamp
                await self._set_file_timestamp(output_path, file_data)

                # Verify checksum if needed
                if (
                    not self.config.ignore_checksum
                    and file_data.metadata.checksum_sha256
                ):
                    await self._verify_checksum_async(output_path, file_data)

            except Exception as e:
                self.logger.error(f"Failed to write file '{file_data.path}': {e}")
                async with self._counter_lock:
                    result.files_failed += 1

    async def _write_file_sync(
        self, file_data: ExtractedFile, result: ExtractionResult
    ):
        """Write a single file synchronously (fallback when aiofiles not available)."""
        try:
            output_path = await self._prepare_output_path(file_data)
            if output_path is None:
                async with self._counter_lock:
                    result.files_failed += 1
                return

            # Check if file exists
            is_overwrite = safe_exists(output_path, logger=self.logger)

            if is_overwrite and not self.config.force_overwrite:
                if not self._confirm_overwrite_sync(output_path):
                    self.logger.info(f"Skipping existing file '{output_path}'")
                    return

            # Determine encoding
            encoding = self._determine_encoding(file_data)

            # Write the file
            content_bytes = await self._encode_content(
                file_data.content, encoding, file_data.path
            )
            # Use safe file operations for sync write
            try:
                output_path.write_bytes(content_bytes)
            except PermissionError as e:
                self.logger.warning(
                    f"Permission denied writing to '{output_path}': {e}"
                )
                async with self._counter_lock:
                    result.files_failed += 1
                return

            # Update result with thread-safe counter increment
            async with self._counter_lock:
                if is_overwrite:
                    result.files_overwritten += 1
                    self.logger.debug(f"Overwrote file: {output_path}")
                else:
                    result.files_created += 1
                    self.logger.debug(f"Created file: {output_path}")

            # Set file timestamp
            await self._set_file_timestamp(output_path, file_data)

            # Verify checksum if needed
            if not self.config.ignore_checksum and file_data.metadata.checksum_sha256:
                self._verify_checksum_sync(output_path, file_data)

        except Exception as e:
            self.logger.error(f"Failed to write file '{file_data.path}': {e}")
            async with self._counter_lock:
                result.files_failed += 1

    async def _prepare_output_path(self, file_data: ExtractedFile) -> Optional[Path]:
        """Prepare the output path for a file."""
        relative_path = Path(file_data.path)

        # Validate path security
        if not validate_file_path(relative_path, self.config.destination_directory):
            self.logger.error(
                f"Skipping file '{file_data.path}' due to invalid path components"
            )
            return None

        output_path = self.config.destination_directory / relative_path

        # Create parent directories
        if not safe_mkdir(
            output_path.parent, logger=self.logger, parents=True, exist_ok=True
        ):
            self.logger.error(
                f"Failed to create directory for '{file_data.path}': Permission denied"
            )
            return None

        self.logger.debug(f"Preparing to write: {output_path}")
        return output_path

    def _determine_encoding(self, file_data: ExtractedFile) -> str:
        """Determine the encoding to use for writing a file."""
        # Priority 1: Explicit target encoding from config
        if self.config.target_encoding:
            return self.config.target_encoding

        # Priority 2: Original encoding if respect_encoding is True
        if self.config.respect_encoding and file_data.metadata.encoding:
            clean_encoding = clean_encoding_name(file_data.metadata.encoding)

            # Validate encoding
            try:
                "test".encode(clean_encoding)
                return clean_encoding
            except (LookupError, UnicodeError):
                self.logger.warning(
                    f"Original encoding '{clean_encoding}' for file '{file_data.path}' "
                    f"is not recognized. Falling back to UTF-8."
                )

        # Default: UTF-8
        return "utf-8"

    async def _encode_content(
        self, content: str, encoding: str, file_path: str
    ) -> bytes:
        """Encode content with the specified encoding."""
        try:
            return content.encode(encoding, errors="strict")
        except UnicodeEncodeError:
            self.logger.warning(
                f"Cannot strictly encode file '{file_path}' with {encoding}. "
                f"Using replacement mode which may lose some characters."
            )
            return content.encode(encoding, errors="replace")

    async def _confirm_overwrite_async(self, path: Path) -> bool:
        """Asynchronously confirm file overwrite (returns True for now)."""
        # In async mode, we can't easily do interactive input
        # So we follow the force_overwrite setting
        return self.config.force_overwrite

    def _confirm_overwrite_sync(self, path: Path) -> bool:
        """Synchronously confirm file overwrite."""
        if self.config.force_overwrite:
            return True

        try:
            response = input(f"Output file '{path}' already exists. Overwrite? (y/N): ")
            return response.lower() == "y"
        except KeyboardInterrupt:
            self.logger.info("\nOperation cancelled by user (Ctrl+C).")
            raise

    async def _set_file_timestamp(self, path: Path, file_data: ExtractedFile):
        """Set file modification timestamp if configured."""
        if (
            self.config.timestamp_mode == "original"
            and file_data.metadata.modified is not None
        ):
            try:
                # Convert datetime to timestamp
                mod_time = file_data.metadata.modified.timestamp()
                access_time = mod_time

                # Use asyncio to run in executor for non-blocking
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    None, os.utime, path, (access_time, mod_time)
                )

                self.logger.debug(
                    f"Set original modification time for '{path}' to "
                    f"{file_data.metadata.modified}"
                )
            except Exception as e:
                self.logger.warning(
                    f"Could not set original modification time for '{path}': {e}"
                )

    async def _verify_checksum_async(self, path: Path, file_data: ExtractedFile):
        """Verify file checksum asynchronously."""
        try:
            # Calculate checksum using chunks to avoid loading entire file into memory
            import hashlib

            sha256_hash = hashlib.sha256()

            # Use aiofiles but add permission error handling
            try:
                async with aiofiles.open(path, "rb") as f:
                    while chunk := await f.read(8192):  # Read in 8KB chunks
                        sha256_hash.update(chunk)
            except PermissionError as e:
                self.logger.warning(
                    f"Permission denied reading '{path}' for checksum verification: {e}"
                )
                return

            calculated_checksum = sha256_hash.hexdigest()
            expected_checksum = file_data.metadata.checksum_sha256

            if calculated_checksum != expected_checksum:
                # Check if difference is due to line endings
                await self._check_line_ending_difference(
                    path, file_data, calculated_checksum, expected_checksum
                )
            else:
                self.logger.debug(f"Checksum VERIFIED for file '{path}'")

        except Exception as e:
            self.logger.warning(f"Error during checksum verification for '{path}': {e}")

    def _verify_checksum_sync(self, path: Path, file_data: ExtractedFile):
        """Verify file checksum synchronously."""
        try:
            # Use safe file operations for reading
            try:
                content_bytes = path.read_bytes()
            except PermissionError as e:
                self.logger.warning(f"Permission denied reading '{path}': {e}")
                return
            calculated_checksum = calculate_sha256(content_bytes)
            expected_checksum = file_data.metadata.checksum_sha256

            if calculated_checksum != expected_checksum:
                # Check if difference is due to line endings
                self._check_line_ending_difference_sync(
                    path, file_data, calculated_checksum, expected_checksum
                )
            else:
                self.logger.debug(f"Checksum VERIFIED for file '{path}'")

        except Exception as e:
            self.logger.warning(f"Error during checksum verification for '{path}': {e}")

    async def _check_line_ending_difference(
        self, path: Path, file_data: ExtractedFile, calculated: str, expected: str
    ):
        """Check if checksum difference is due to line endings."""
        # Normalize line endings and recalculate
        normalized_content = normalize_line_endings(file_data.content, "\n")
        normalized_bytes = normalized_content.encode("utf-8")
        normalized_checksum = calculate_sha256(normalized_bytes)

        if normalized_checksum == expected:
            self.logger.debug(
                f"Checksum difference for '{path}' appears to be due to "
                f"line ending normalization"
            )
        else:
            self.logger.warning(
                f"CHECKSUM MISMATCH for file '{path}'. "
                f"Expected: {expected}, Calculated: {calculated}. "
                f"The file content may be corrupted or was altered."
            )

    def _check_line_ending_difference_sync(
        self, path: Path, file_data: ExtractedFile, calculated: str, expected: str
    ):
        """Check if checksum difference is due to line endings (sync version)."""
        # Same logic as async version
        normalized_content = normalize_line_endings(file_data.content, "\n")
        normalized_bytes = normalized_content.encode("utf-8")
        normalized_checksum = calculate_sha256(normalized_bytes)

        if normalized_checksum == expected:
            self.logger.debug(
                f"Checksum difference for '{path}' appears to be due to "
                f"line ending normalization"
            )
        else:
            self.logger.warning(
                f"CHECKSUM MISMATCH for file '{path}'. "
                f"Expected: {expected}, Calculated: {calculated}. "
                f"The file content may be corrupted or was altered."
            )
