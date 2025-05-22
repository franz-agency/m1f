"""
Archive creator module for creating backup archives of processed files.
"""

from __future__ import annotations

import asyncio
import tarfile
import zipfile
from pathlib import Path
from typing import List, Tuple, Optional

from .config import Config, ArchiveType
from .exceptions import ArchiveError
from .logging import LoggerManager


class ArchiveCreator:
    """Handles creation of backup archives."""

    def __init__(self, config: Config, logger_manager: LoggerManager):
        self.config = config
        self.logger = logger_manager.get_logger(__name__)

    async def create_archive(
        self, output_path: Path, files_to_process: List[Tuple[Path, str]]
    ) -> Optional[Path]:
        """Create an archive of all processed files."""
        if not self.config.archive.create_archive:
            return None

        if not files_to_process:
            self.logger.info("No files to archive")
            return None

        # Determine archive path
        base_name = output_path.stem
        archive_suffix = (
            ".zip" if self.config.archive.archive_type == ArchiveType.ZIP else ".tar.gz"
        )
        archive_path = output_path.with_name(f"{base_name}_backup{archive_suffix}")

        self.logger.info(
            f"Creating {self.config.archive.archive_type.value} archive at: {archive_path}"
        )

        try:
            if self.config.archive.archive_type == ArchiveType.ZIP:
                await self._create_zip_archive(archive_path, files_to_process)
            else:
                await self._create_tar_archive(archive_path, files_to_process)

            self.logger.info(
                f"Successfully created archive with {len(files_to_process)} file(s)"
            )

            return archive_path

        except Exception as e:
            raise ArchiveError(f"Failed to create archive: {e}")

    async def _create_zip_archive(
        self, archive_path: Path, files: List[Tuple[Path, str]]
    ) -> None:
        """Create a ZIP archive."""

        def _write_zip():
            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for file_path, rel_path in files:
                    if self.config.logging.verbose:
                        self.logger.debug(f"Adding to zip: {file_path} as {rel_path}")

                    # Skip if file doesn't exist
                    if not file_path.exists():
                        self.logger.warning(f"File not found, skipping: {file_path}")
                        continue

                    # Add file to archive
                    try:
                        zf.write(file_path, arcname=rel_path)
                    except Exception as e:
                        self.logger.error(f"Error adding {file_path} to zip: {e}")
                        if self.config.encoding.abort_on_error:
                            raise

        # Run in thread pool to avoid blocking
        await asyncio.to_thread(_write_zip)

    async def _create_tar_archive(
        self, archive_path: Path, files: List[Tuple[Path, str]]
    ) -> None:
        """Create a TAR.GZ archive."""

        def _write_tar():
            with tarfile.open(archive_path, "w:gz") as tf:
                for file_path, rel_path in files:
                    if self.config.logging.verbose:
                        self.logger.debug(
                            f"Adding to tar.gz: {file_path} as {rel_path}"
                        )

                    # Skip if file doesn't exist
                    if not file_path.exists():
                        self.logger.warning(f"File not found, skipping: {file_path}")
                        continue

                    # Add file to archive
                    try:
                        tf.add(file_path, arcname=rel_path)
                    except Exception as e:
                        self.logger.error(f"Error adding {file_path} to tar.gz: {e}")
                        if self.config.encoding.abort_on_error:
                            raise

        # Run in thread pool to avoid blocking
        await asyncio.to_thread(_write_tar)
