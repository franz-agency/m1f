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
        message = f"Checksum mismatch for {file_path}: expected {expected}, got {actual}"
        super().__init__(message, exit_code=5)
        self.file_path = file_path
        self.expected_checksum = expected
        self.actual_checksum = actual 