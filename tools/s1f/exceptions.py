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

"""Custom exceptions for s1f."""

from typing import Optional


class S1FError(Exception):
    """Base exception for all s1f errors."""

    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code


class FileParsingError(S1FError):
    """Raised when file parsing fails."""

    def __init__(self, message: str, file_path: Optional[str] = None):
        super().__init__(message, exit_code=2)
        self.file_path = file_path


class FileWriteError(S1FError):
    """Raised when file writing fails."""

    def __init__(self, message: str, file_path: Optional[str] = None):
        super().__init__(message, exit_code=3)
        self.file_path = file_path


class ConfigurationError(S1FError):
    """Raised when configuration is invalid."""

    def __init__(self, message: str):
        super().__init__(message, exit_code=4)


class ChecksumMismatchError(S1FError):
    """Raised when checksum verification fails."""

    def __init__(self, file_path: str, expected: str, actual: str):
        message = (
            f"Checksum mismatch for {file_path}: expected {expected}, got {actual}"
        )
        super().__init__(message, exit_code=5)
        self.file_path = file_path
        self.expected_checksum = expected
        self.actual_checksum = actual
