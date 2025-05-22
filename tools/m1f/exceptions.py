"""
Custom exception classes for m1f.
"""

from typing import Optional


class M1FError(Exception):
    """Base exception for all m1f errors."""
    
    exit_code: int = 1
    
    def __init__(self, message: str, exit_code: Optional[int] = None):
        super().__init__(message)
        if exit_code is not None:
            self.exit_code = exit_code


class FileNotFoundError(M1FError):
    """Raised when a required file is not found."""
    
    exit_code = 2


class PermissionError(M1FError):
    """Raised when there's a permission issue."""
    
    exit_code = 3


class EncodingError(M1FError):
    """Raised when there's an encoding/decoding issue."""
    
    exit_code = 4


class ConfigurationError(M1FError):
    """Raised when there's a configuration issue."""
    
    exit_code = 5


class ValidationError(M1FError):
    """Raised when validation fails."""
    
    exit_code = 6


class SecurityError(M1FError):
    """Raised when sensitive information is detected."""
    
    exit_code = 7


class ArchiveError(M1FError):
    """Raised when archive creation fails."""
    
    exit_code = 8 