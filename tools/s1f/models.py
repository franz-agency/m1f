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

"""Data models for s1f."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


@dataclass
class FileMetadata:
    """Metadata for an extracted file."""

    path: str
    checksum_sha256: Optional[str] = None
    size_bytes: Optional[int] = None
    modified: Optional[datetime] = None
    encoding: Optional[str] = None
    line_endings: Optional[str] = None
    type: Optional[str] = None
    had_encoding_errors: bool = False


@dataclass
class ExtractedFile:
    """Represents a file extracted from the combined file."""

    metadata: FileMetadata
    content: str

    @property
    def path(self) -> str:
        """Convenience property for accessing the file path."""
        return self.metadata.path


@dataclass
class ExtractionResult:
    """Result of the extraction process."""

    files_created: int = 0
    files_overwritten: int = 0
    files_failed: int = 0
    execution_time: float = 0.0

    @property
    def total_files(self) -> int:
        """Total number of files processed."""
        return self.files_created + self.files_overwritten + self.files_failed

    @property
    def success_rate(self) -> float:
        """Percentage of successfully processed files."""
        if self.total_files == 0:
            return 0.0
        return (self.files_created + self.files_overwritten) / self.total_files * 100

    @property
    def extracted_count(self) -> int:
        """Total number of successfully extracted files."""
        return self.files_created + self.files_overwritten

    @property
    def success(self) -> bool:
        """Whether the extraction was successful."""
        return self.files_failed == 0 and self.extracted_count > 0


@dataclass
class SeparatorMatch:
    """Represents a matched separator in the content."""

    separator_type: str
    start_index: int
    end_index: int
    metadata: Dict[str, Any]
    header_length: int = 0
    uuid: Optional[str] = None
