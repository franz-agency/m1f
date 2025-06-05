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
from .presets import PresetManager


class OutputWriter:
    """Handles writing the combined output file."""

    def __init__(self, config: Config, logger_manager: LoggerManager):
        self.config = config
        self.logger = logger_manager.get_logger(__name__)

        # Initialize preset manager first to get global settings
        self.preset_manager = None
        self.global_settings = None
        if not config.preset.disable_presets and config.preset.preset_files:
            try:
                from .presets import load_presets

                self.preset_manager = load_presets(config.preset.preset_files)
                self.global_settings = self.preset_manager.get_global_settings()
                self.logger.debug(
                    f"Loaded {len(self.preset_manager.groups)} preset groups"
                )
            except Exception as e:
                self.logger.warning(f"Failed to load presets: {e}")

        # Apply global settings to config if available
        config = self._apply_global_settings(config)

        self.encoding_handler = EncodingHandler(config, logger_manager)
        self.separator_generator = SeparatorGenerator(config, logger_manager)
        self._processed_checksums: Set[str] = set()
        self._content_dedupe: bool = True  # Enable content deduplication by default
        self._checksum_lock = asyncio.Lock()  # Lock for thread-safe checksum operations

    def _apply_global_settings(self, config: Config) -> Config:
        """Apply global preset settings to config if not already set."""
        if not self.global_settings:
            return config

        from dataclasses import replace
        from .config import (
            SeparatorStyle,
            LineEnding,
            EncodingConfig,
            OutputConfig,
            FilterConfig,
            SecurityConfig,
            SecurityCheckMode,
        )

        # Create updated components
        encoding_config = config.encoding
        output_config = config.output
        filter_config = config.filter
        security_config = config.security

        # Apply encoding settings
        if not config.encoding.target_charset and self.global_settings.encoding:
            encoding_config = replace(
                config.encoding, target_charset=self.global_settings.encoding
            )
            self.logger.debug(
                f"Applied global encoding: {self.global_settings.encoding}"
            )

        if self.global_settings.abort_on_encoding_error is not None:
            encoding_config = replace(
                encoding_config,
                abort_on_error=self.global_settings.abort_on_encoding_error,
            )
            self.logger.debug(
                f"Applied global abort_on_encoding_error: {self.global_settings.abort_on_encoding_error}"
            )

        # Apply separator style if global setting exists
        if self.global_settings.separator_style:
            try:
                global_style = SeparatorStyle(self.global_settings.separator_style)
                output_config = replace(output_config, separator_style=global_style)
                self.logger.debug(
                    f"Applied global separator style: {self.global_settings.separator_style}"
                )
            except ValueError:
                self.logger.warning(
                    f"Invalid global separator style: {self.global_settings.separator_style}"
                )

        # Apply line ending if global setting exists
        if self.global_settings.line_ending:
            try:
                global_ending = LineEnding.from_str(self.global_settings.line_ending)
                output_config = replace(output_config, line_ending=global_ending)
                self.logger.debug(
                    f"Applied global line ending: {self.global_settings.line_ending}"
                )
            except ValueError:
                self.logger.warning(
                    f"Invalid global line ending: {self.global_settings.line_ending}"
                )

        # Apply filter settings
        if self.global_settings.remove_scraped_metadata is not None:
            filter_config = replace(
                filter_config,
                remove_scraped_metadata=self.global_settings.remove_scraped_metadata,
            )
            self.logger.debug(
                f"Applied global remove_scraped_metadata: {self.global_settings.remove_scraped_metadata}"
            )

        # Apply security settings
        if self.global_settings.security_check and not config.security.security_check:
            try:
                security_mode = SecurityCheckMode(self.global_settings.security_check)
                security_config = replace(security_config, security_check=security_mode)
                self.logger.debug(
                    f"Applied global security_check: {self.global_settings.security_check}"
                )
            except ValueError:
                self.logger.warning(
                    f"Invalid global security_check mode: {self.global_settings.security_check}"
                )

        # Return updated config
        return replace(
            config,
            encoding=encoding_config,
            output=output_config,
            filter=filter_config,
            security=security_config,
        )

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

        # Use parallel processing if enabled and have multiple files
        if self.config.output.parallel and len(all_files) > 1:
            return await self._write_combined_file_parallel(output_path, all_files)
        else:
            return await self._write_combined_file_sequential(output_path, all_files)

    async def _write_combined_file_sequential(
        self, output_path: Path, all_files: List[Tuple[Path, str]]
    ) -> int:
        """Write all files sequentially (original implementation)."""
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

    async def _write_combined_file_parallel(
        self, output_path: Path, all_files: List[Tuple[Path, str]]
    ) -> int:
        """Write all files using parallel processing for reading."""
        self.logger.info("Using parallel processing for file reading...")

        try:
            # Process files in batches to avoid too many concurrent operations
            batch_size = 10  # Process 10 files concurrently

            # First, read and process all files in parallel
            processed_files = []

            for batch_start in range(0, len(all_files), batch_size):
                batch_end = min(batch_start + batch_size, len(all_files))
                batch = all_files[batch_start:batch_end]

                # Create tasks for parallel processing
                tasks = []
                for i, (file_path, rel_path) in enumerate(batch, batch_start + 1):
                    # Skip if output file itself
                    if file_path.resolve() == output_path.resolve():
                        self.logger.warning(f"Skipping output file itself: {file_path}")
                        continue

                    task = self._process_single_file_parallel(
                        file_path, rel_path, i, len(all_files)
                    )
                    tasks.append(task)

                # Process batch concurrently
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                # Collect successful results
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        # Log error but continue
                        file_path, rel_path = batch[j]
                        self.logger.error(f"Failed to process {file_path}: {result}")
                    elif result is not None:
                        processed_files.append((batch[j], result))

            # Now write all processed files sequentially to maintain order
            output_encoding = self.config.encoding.target_charset or "utf-8"

            with open(
                output_path,
                "w",
                encoding=output_encoding,
                newline=self.config.output.line_ending.value,
            ) as outfile:
                files_written = 0

                for i, ((file_path, rel_path), processed_data) in enumerate(
                    processed_files
                ):
                    if processed_data:
                        # Write the pre-processed content
                        separator, content, separator_style = processed_data

                        # Write separator
                        outfile.write(separator)

                        # Add blank line for some styles (between separator and content)
                        if separator_style in [
                            SeparatorStyle.STANDARD,
                            SeparatorStyle.DETAILED,
                            SeparatorStyle.MARKDOWN,
                        ]:
                            outfile.write(self.config.output.line_ending.value)

                        # Write content
                        outfile.write(content)

                        # Ensure newline at end if needed
                        if content and not content.endswith(("\n", "\r")):
                            outfile.write(self.config.output.line_ending.value)

                        # Write closing separator for Markdown
                        if separator_style == SeparatorStyle.MARKDOWN:
                            outfile.write("```")
                            outfile.write(self.config.output.line_ending.value)

                        # Add inter-file spacing if not last file
                        if i < len(processed_files) - 1:
                            outfile.write(self.config.output.line_ending.value)

                        files_written += 1

            return files_written

        except IOError as e:
            raise PermissionError(f"Cannot write to output file: {e}")

    async def _process_single_file_parallel(
        self, file_path: Path, rel_path: str, file_num: int, total_files: int
    ) -> Optional[Tuple[str, str]]:
        """Process a single file for parallel writing, returning separator and content."""
        try:
            # Log progress
            if self.config.logging.verbose:
                self.logger.debug(
                    f"Processing file ({file_num}/{total_files}): {file_path.name}"
                )

            # Read file with encoding handling
            content, encoding_info = await self.encoding_handler.read_file(file_path)

            # Apply preset processing if available
            preset = None
            if self.preset_manager:
                preset = self.preset_manager.get_preset_for_file(
                    file_path, self.config.preset.preset_group
                )
                if preset:
                    self.logger.debug(f"Applying preset to {file_path}")
                    content = self.preset_manager.process_content(
                        content, preset, file_path
                    )

            # Remove scraped metadata if requested
            # Check file-specific override first
            remove_metadata = self.config.filter.remove_scraped_metadata
            if (
                preset
                and hasattr(preset, "remove_scraped_metadata")
                and preset.remove_scraped_metadata is not None
            ):
                remove_metadata = preset.remove_scraped_metadata

            if remove_metadata:
                content = self._remove_scraped_metadata(content)

            # Check for content deduplication
            # Skip deduplication for symlinks when include_symlinks is enabled
            skip_dedupe = self.config.filter.include_symlinks and file_path.is_symlink()

            if (
                self._content_dedupe
                and not rel_path.startswith(("intro:", "include:"))
                and not skip_dedupe
            ):
                content_checksum = calculate_checksum(content)

                async with self._checksum_lock:
                    if content_checksum in self._processed_checksums:
                        self.logger.debug(f"Skipping duplicate content: {file_path}")
                        return None

                    self._processed_checksums.add(content_checksum)

            # Generate separator
            # Check if preset overrides separator style
            separator_style = self.config.output.separator_style
            if self.preset_manager and preset and preset.separator_style:
                try:
                    separator_style = SeparatorStyle(preset.separator_style)
                except ValueError:
                    self.logger.warning(
                        f"Invalid separator style in preset: {preset.separator_style}"
                    )

            # Temporarily override separator style if needed
            original_style = self.separator_generator.config.output.separator_style
            if separator_style != original_style:
                # Create a temporary config with the new style
                from dataclasses import replace

                temp_output = replace(
                    self.separator_generator.config.output,
                    separator_style=separator_style,
                )
                temp_config = replace(
                    self.separator_generator.config, output=temp_output
                )
                self.separator_generator.config = temp_config

            separator = await self.separator_generator.generate_separator(
                file_path=file_path,
                rel_path=rel_path,
                encoding_info=encoding_info,
                file_content=content,
            )

            # Restore original config if changed
            if separator_style != original_style:
                self.separator_generator.config = self.config

            return (separator, content, separator_style)

        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")
            raise

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

            # Apply preset processing if available
            preset = None
            if self.preset_manager:
                preset = self.preset_manager.get_preset_for_file(
                    file_path, self.config.preset.preset_group
                )
                if preset:
                    self.logger.debug(f"Applying preset to {file_path}")
                    content = self.preset_manager.process_content(
                        content, preset, file_path
                    )

            # Remove scraped metadata if requested
            # Check file-specific override first
            remove_metadata = self.config.filter.remove_scraped_metadata
            if (
                preset
                and hasattr(preset, "remove_scraped_metadata")
                and preset.remove_scraped_metadata is not None
            ):
                remove_metadata = preset.remove_scraped_metadata

            if remove_metadata:
                content = self._remove_scraped_metadata(content)

            # Check for content deduplication
            # Skip deduplication for symlinks when include_symlinks is enabled
            skip_dedupe = self.config.filter.include_symlinks and file_path.is_symlink()

            if (
                self._content_dedupe
                and not rel_path.startswith(("intro:", "include:"))
                and not skip_dedupe
            ):
                content_checksum = calculate_checksum(content)

                async with self._checksum_lock:
                    if content_checksum in self._processed_checksums:
                        self.logger.debug(f"Skipping duplicate content: {file_path}")
                        return False

                    self._processed_checksums.add(content_checksum)

            # Generate separator
            # Check if preset overrides separator style
            separator_style = self.config.output.separator_style
            if self.preset_manager and preset and preset.separator_style:
                try:
                    separator_style = SeparatorStyle(preset.separator_style)
                except ValueError:
                    self.logger.warning(
                        f"Invalid separator style in preset: {preset.separator_style}"
                    )

            # Temporarily override separator style if needed
            original_style = self.separator_generator.config.output.separator_style
            if separator_style != original_style:
                # Create a temporary config with the new style
                from dataclasses import replace

                temp_output = replace(
                    self.separator_generator.config.output,
                    separator_style=separator_style,
                )
                temp_config = replace(
                    self.separator_generator.config, output=temp_output
                )
                self.separator_generator.config = temp_config

            separator = await self.separator_generator.generate_separator(
                file_path=file_path,
                rel_path=rel_path,
                encoding_info=encoding_info,
                file_content=content,
            )

            # Restore original config if changed
            if separator_style != original_style:
                self.separator_generator.config = self.config

            # Write separator
            if separator:
                outfile.write(separator)

                # For Markdown, ensure separator ends with newline before adding blank line
                if self.config.output.separator_style == SeparatorStyle.MARKDOWN:
                    if not separator.endswith(("\n", "\r\n", "\r")):
                        outfile.write(self.config.output.line_ending.value)

                # Add blank line for some styles
                if self.config.output.separator_style in [
                    SeparatorStyle.STANDARD,
                    SeparatorStyle.DETAILED,
                    SeparatorStyle.MARKDOWN,
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
