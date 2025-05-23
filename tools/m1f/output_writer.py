"""
Output writer module for writing combined files with separators.
"""

from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path
from typing import List, Tuple, Set, Optional
import re

from .config import Config, SeparatorStyle
from .constants import READ_BUFFER_SIZE
from .encoding_handler import EncodingHandler
from .exceptions import PermissionError, EncodingError
from .logging import LoggerManager
from .separator_generator import SeparatorGenerator
from .utils import calculate_checksum


class OutputWriter:
    """Handles writing the combined output file."""

    def __init__(self, config: Config, logger_manager: LoggerManager):
        self.config = config
        self.logger = logger_manager.get_logger(__name__)
        self.encoding_handler = EncodingHandler(config, logger_manager)
        self.separator_generator = SeparatorGenerator(config, logger_manager)
        self._processed_checksums: Set[str] = set()
        self._content_dedupe: bool = True  # Enable content deduplication by default

    def _remove_scraped_metadata(self, content: str) -> str:
        """Remove scraped metadata from the end of markdown content."""
        if not self.config.filter.remove_scraped_metadata:
            return content

        # Pattern to match scraped metadata at the end of the file
        # Looks for a horizontal rule followed by scraped metadata
        pattern = (
            r"\n\n---\n\n"
            r"\*Scraped from:.*?\*\n\n"
            r"\*Scraped at:.*?\*\n\n"
            r"\*Source URL:.*?\*\s*$"
        )

        # Remove the metadata if found
        cleaned_content = re.sub(pattern, "", content, flags=re.DOTALL)

        if cleaned_content != content:
            self.logger.debug("Removed scraped metadata from file content")

        return cleaned_content

    async def write_combined_file(
        self, output_path: Path, files_to_process: List[Tuple[Path, str]]
    ) -> int:
        """Write all files to the combined output file."""
        total_files = len(files_to_process)
        self.logger.info(f"Processing {total_files} file(s) for inclusion...")

        # Prepare include files if any
        include_files = await self._prepare_include_files()

        # Combine include files with regular files
        all_files = include_files + files_to_process

        try:
            # Open output file
            output_encoding = self.config.encoding.target_charset or "utf-8"

            with open(
                output_path,
                "w",
                encoding=output_encoding,
                newline=self.config.output.line_ending.value,
            ) as outfile:

                files_written = 0

                for i, (file_path, rel_path) in enumerate(all_files, 1):
                    # Skip if output file itself
                    if file_path.resolve() == output_path.resolve():
                        self.logger.warning(f"Skipping output file itself: {file_path}")
                        continue

                    # Process and write file
                    if await self._write_single_file(
                        outfile, file_path, rel_path, i, len(all_files)
                    ):
                        files_written += 1

                return files_written

        except IOError as e:
            raise PermissionError(f"Cannot write to output file: {e}")

    async def _prepare_include_files(self) -> List[Tuple[Path, str]]:
        """Prepare include files from configuration."""
        include_files = []

        if not self.config.input_include_files:
            return include_files

        for i, include_path in enumerate(self.config.input_include_files):
            if not include_path.exists():
                self.logger.warning(f"Include file not found: {include_path}")
                continue

            # Use special prefix for include files
            if i == 0:
                rel_path = f"intro:{include_path.name}"
            else:
                rel_path = f"include:{include_path.name}"

            include_files.append((include_path, rel_path))

        return include_files

    async def _write_single_file(
        self, outfile, file_path: Path, rel_path: str, file_num: int, total_files: int
    ) -> bool:
        """Write a single file to the output."""
        try:
            # Log progress
            if self.config.logging.verbose:
                self.logger.debug(
                    f"Processing file ({file_num}/{total_files}): {file_path.name}"
                )

            # Read file with encoding handling
            content, encoding_info = await self.encoding_handler.read_file(file_path)

            # Remove scraped metadata if requested
            content = self._remove_scraped_metadata(content)

            # Check for content deduplication
            if self._content_dedupe and not rel_path.startswith(("intro:", "include:")):
                content_checksum = calculate_checksum(content)

                if content_checksum in self._processed_checksums:
                    self.logger.debug(f"Skipping duplicate content: {file_path}")
                    return False

                self._processed_checksums.add(content_checksum)

            # Generate separator
            separator = await self.separator_generator.generate_separator(
                file_path=file_path,
                rel_path=rel_path,
                encoding_info=encoding_info,
                file_content=content,
            )

            # Write separator
            if separator:
                outfile.write(separator)

                # Add blank line for some styles
                if self.config.output.separator_style in [
                    SeparatorStyle.STANDARD,
                    SeparatorStyle.DETAILED,
                ]:
                    outfile.write(self.config.output.line_ending.value)

            # Write content
            outfile.write(content)

            # Ensure newline at end if needed
            if (
                content
                and not content.endswith(("\n", "\r"))
                and self.config.output.separator_style
                != SeparatorStyle.MACHINE_READABLE
            ):
                outfile.write(self.config.output.line_ending.value)

            # Write closing separator
            closing = await self.separator_generator.generate_closing_separator()
            if closing:
                outfile.write(closing)
                outfile.write(self.config.output.line_ending.value)

            # Add inter-file spacing
            if (
                file_num < total_files
                and self.config.output.separator_style != SeparatorStyle.NONE
            ):
                outfile.write(self.config.output.line_ending.value)

            return True

        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")

            if self.config.encoding.abort_on_error:
                raise EncodingError(f"Failed to process {file_path}: {e}")

            # Write error placeholder
            error_msg = f"[ERROR: Unable to read file '{file_path}'. Reason: {e}]"
            outfile.write(error_msg)
            outfile.write(self.config.output.line_ending.value)

            return True
