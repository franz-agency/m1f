"""Character encoding detection and handling utilities."""

import logging
from pathlib import Path
from typing import Optional, Tuple

try:
    import chardet
    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False

logger = logging.getLogger(__name__)


def detect_encoding(file_path: Path, sample_size: int = 65536) -> str:
    """Detect the character encoding of a file.
    
    Args:
        file_path: Path to the file
        sample_size: Number of bytes to sample for detection
        
    Returns:
        Detected encoding name (e.g., 'utf-8', 'iso-8859-1')
    """
    # Check for BOM markers first
    with open(file_path, "rb") as f:
        bom = f.read(4)
    
    if not bom:
        return "utf-8"
    
    # Check common BOMs
    if bom.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    elif bom.startswith(b"\xff\xfe\x00\x00"):
        return "utf-32-le"
    elif bom.startswith(b"\x00\x00\xfe\xff"):
        return "utf-32-be"
    elif bom.startswith(b"\xff\xfe"):
        return "utf-16-le"
    elif bom.startswith(b"\xfe\xff"):
        return "utf-16-be"
    
    # Use chardet if available
    if CHARDET_AVAILABLE:
        try:
            with open(file_path, "rb") as f:
                sample = f.read(sample_size)
            
            result = chardet.detect(sample)
            
            if result["confidence"] >= 0.7:
                encoding = normalize_encoding(result["encoding"])
                logger.debug(
                    f"Detected encoding for {file_path}: {encoding} "
                    f"(confidence: {result['confidence']:.2f})"
                )
                return encoding
        except Exception as e:
            logger.warning(f"Error during encoding detection: {e}")
    
    # Default to UTF-8
    logger.debug(f"Using default UTF-8 encoding for {file_path}")
    return "utf-8"


def normalize_encoding(encoding: Optional[str]) -> str:
    """Normalize encoding name to Python codec name.
    
    Args:
        encoding: Raw encoding name
        
    Returns:
        Normalized encoding name
    """
    if not encoding:
        return "utf-8"
    
    # Convert to lowercase and remove hyphens/underscores
    normalized = encoding.lower().replace("-", "").replace("_", "")
    
    # Map common aliases
    encoding_map = {
        "utf8": "utf-8",
        "utf16": "utf-16",
        "utf32": "utf-32",
        "latin1": "iso-8859-1",
        "latin2": "iso-8859-2",
        "cp1252": "windows-1252",
        "win1252": "windows-1252",
        "ascii": "ascii",
        "usascii": "ascii",
        "iso88591": "iso-8859-1",
        "iso88592": "iso-8859-2",
        "iso885915": "iso-8859-15",
        "gb2312": "gb2312",
        "gbk": "gbk",
        "gb18030": "gb18030",
        "big5": "big5",
        "shiftjis": "shift-jis",
        "eucjp": "euc-jp",
        "euckr": "euc-kr",
    }
    
    return encoding_map.get(normalized, encoding)


def read_with_encoding(
    file_path: Path,
    encoding: Optional[str] = None,
    fallback_encoding: str = "utf-8",
    errors: str = "replace"
) -> Tuple[str, str]:
    """Read a file with specified or detected encoding.
    
    Args:
        file_path: Path to the file
        encoding: Explicit encoding to use (if None, will detect)
        fallback_encoding: Encoding to use if detection fails
        errors: How to handle encoding errors
        
    Returns:
        Tuple of (file content, used encoding)
    """
    if encoding is None:
        encoding = detect_encoding(file_path)
    
    try:
        with open(file_path, "r", encoding=encoding, errors="strict") as f:
            content = f.read()
        return content, encoding
    except UnicodeDecodeError:
        logger.warning(
            f"Failed to decode {file_path} with {encoding}, "
            f"falling back to {fallback_encoding} with {errors} error handling"
        )
        with open(file_path, "r", encoding=fallback_encoding, errors=errors) as f:
            content = f.read()
        return content, fallback_encoding


def convert_encoding(
    content: str,
    target_encoding: str = "utf-8",
    errors: str = "replace"
) -> bytes:
    """Convert string content to target encoding.
    
    Args:
        content: String content to convert
        target_encoding: Target encoding
        errors: How to handle encoding errors
        
    Returns:
        Encoded bytes
    """
    return content.encode(target_encoding, errors=errors) 