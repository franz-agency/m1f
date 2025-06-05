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

"""Core file splitter functionality for s1f."""

import time
from pathlib import Path
from typing import List, Optional, Tuple
import logging

from .config import Config
from .models import ExtractedFile, ExtractionResult
from .parsers import CombinedFileParser
from .writers import FileWriter
from .utils import format_size, is_binary_content
from .exceptions import FileParsingError, S1FError
from .logging import LoggerManager


class FileSplitter:
    """Main class for splitting combined files back into individual files."""

    def __init__(self, config: Config, logger_manager: LoggerManager):
        self.config = config
        self.logger_manager = logger_manager
        self.logger = logger_manager.get_logger(__name__)
        self.parser = CombinedFileParser(self.logger)
        self.writer = FileWriter(config, self.logger)

    async def list_files(self) -> Tuple[ExtractionResult, int]:
        """List files in the combined file without extracting.

        Returns:
            Tuple of (ExtractionResult, exit_code)
        """
        start_time = time.time()

        try:
            # Read the input file
            content = await self._read_input_file()

            # Parse the content
            self.logger.info("Parsing combined file...")
            extracted_files = self.parser.parse(content)

            if not extracted_files:
                self.logger.error("No files found in the combined file.")
                return ExtractionResult(), 2

            # Display file list
            print(
                f"\nFound {len(extracted_files)} file(s) in {self.config.input_file}:\n"
            )

            total_size = 0
            for i, file in enumerate(extracted_files, 1):
                meta = file.metadata
                # Build info line
                info_parts = [f"{i:4d}. {meta.path}"]
                
                # Only add size if available
                if meta.size_bytes:
                    size_str = format_size(meta.size_bytes)
                    info_parts.append(f"[{size_str}]")

                if meta.encoding:
                    info_parts.append(f"Encoding: {meta.encoding}")

                if meta.type:
                    info_parts.append(f"Type: {meta.type}")

                print("  ".join(info_parts))

                if meta.size_bytes:
                    total_size += meta.size_bytes

            print(f"\nTotal size: {format_size(total_size)}")

            result = ExtractionResult(
                files_created=0,
                files_overwritten=0,
                files_failed=0,
                execution_time=time.time() - start_time,
            )

            return result, 0

        except S1FError as e:
            self.logger.error(f"Error: {e}")
            return (
                ExtractionResult(execution_time=time.time() - start_time),
                e.exit_code,
            )
        except KeyboardInterrupt:
            self.logger.info("\nOperation cancelled by user.")
            return ExtractionResult(execution_time=time.time() - start_time), 130
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            if self.config.verbose:
                import traceback

                self.logger.debug(traceback.format_exc())
            return ExtractionResult(execution_time=time.time() - start_time), 1

    async def split_file(self) -> Tuple[ExtractionResult, int]:
        """Split the combined file into individual files.

        Returns:
            Tuple of (ExtractionResult, exit_code)
        """
        start_time = time.time()

        try:
            # Read the input file
            content = await self._read_input_file()

            # Parse the content
            self.logger.info("Parsing combined file...")
            extracted_files = self.parser.parse(content)

            if not extracted_files:
                self.logger.error("No files found in the combined file.")
                return ExtractionResult(), 2

            self.logger.info(f"Found {len(extracted_files)} file(s) to extract")

            # Ensure destination directory exists
            self.config.destination_directory.mkdir(parents=True, exist_ok=True)

            # Write the files
            result = await self.writer.write_files(extracted_files)

            # Set execution time
            result.execution_time = time.time() - start_time

            # Log summary
            self._log_summary(result)

            # Determine exit code
            if result.files_failed > 0:
                exit_code = 1
            else:
                exit_code = 0

            return result, exit_code

        except S1FError as e:
            self.logger.error(f"Error: {e}")
            return (
                ExtractionResult(execution_time=time.time() - start_time),
                e.exit_code,
            )
        except KeyboardInterrupt:
            self.logger.info("\nOperation cancelled by user.")
            return ExtractionResult(execution_time=time.time() - start_time), 130
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            if self.config.verbose:
                import traceback

                self.logger.debug(traceback.format_exc())
            return ExtractionResult(execution_time=time.time() - start_time), 1

    async def _read_input_file(self) -> str:
        """Read the input file content."""
        if not self.config.input_file.exists():
            raise FileParsingError(
                f"Input file '{self.config.input_file}' does not exist.",
                str(self.config.input_file),
            )

        try:
            # First, try to detect if the file is binary
            sample_bytes = self.config.input_file.read_bytes()[:8192]
            if is_binary_content(sample_bytes):
                raise FileParsingError(
                    f"Input file '{self.config.input_file}' appears to be binary.",
                    str(self.config.input_file),
                )

            # Try to read with UTF-8 first
            try:
                content = self.config.input_file.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                # Try with latin-1 as fallback (can decode any byte sequence)
                self.logger.warning(
                    f"Failed to decode '{self.config.input_file}' as UTF-8, "
                    f"trying latin-1 encoding..."
                )
                content = self.config.input_file.read_text(encoding="latin-1")

            # Check if the file is empty
            if not content.strip():
                raise FileParsingError(
                    f"Input file '{self.config.input_file}' is empty.",
                    str(self.config.input_file),
                )

            file_size = self.config.input_file.stat().st_size
            self.logger.info(
                f"Read input file '{self.config.input_file}' "
                f"({format_size(file_size)})"
            )

            return content

        except (IOError, OSError) as e:
            raise FileParsingError(
                f"Failed to read input file '{self.config.input_file}': {e}",
                str(self.config.input_file),
            )

    def _log_summary(self, result: ExtractionResult):
        """Log extraction summary."""
        self.logger.info("")
        self.logger.info("=== Extraction Summary ===")
        self.logger.info(f"Files created:     {result.files_created}")
        self.logger.info(f"Files overwritten: {result.files_overwritten}")

        if result.files_failed > 0:
            self.logger.error(f"Files failed:      {result.files_failed}")
        else:
            self.logger.info(f"Files failed:      {result.files_failed}")

        self.logger.info(f"Total processed:   {result.total_files}")
        self.logger.info(f"Success rate:      {result.success_rate:.1f}%")
        self.logger.info(f"Time taken:        {result.execution_time:.2f} seconds")
        self.logger.info("")

        if result.files_failed == 0 and result.total_files > 0:
            self.logger.info("✓ All files extracted successfully!")
        elif result.files_failed > 0:
            self.logger.error(
                f"✗ Extraction completed with {result.files_failed} error(s). "
                f"Check the logs above for details."
            )


# Alias for backward compatibility with tests
S1FExtractor = FileSplitter
