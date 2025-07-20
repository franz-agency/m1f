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
Encoding handler module for character encoding detection and conversion.
"""

from __future__ import annotations

import asyncio
import gc
import sys
from pathlib import Path
from typing import Tuple, Optional
from dataclasses import dataclass

from .config import Config
from .constants import UTF8_PREFERRED_EXTENSIONS
from .exceptions import EncodingError
from .logging import LoggerManager

# Try to import chardet for encoding detection
try:
    import chardet

    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False


@dataclass
class EncodingInfo:
    """Information about file encoding."""

    original_encoding: str
    target_encoding: Optional[str] = None
    had_errors: bool = False


class EncodingHandler:
    """Handles character encoding detection and conversion."""

    def __init__(self, config: Config, logger_manager: LoggerManager):
        self.config = config
        self.logger = logger_manager.get_logger(__name__)

        if self.config.encoding.target_charset and not CHARDET_AVAILABLE:
            self.logger.warning(
                "chardet library not available. Encoding detection will be limited."
            )

    async def read_file(self, file_path: Path) -> Tuple[str, EncodingInfo]:
        """Read a file with encoding detection and optional conversion."""
        # Detect encoding
        detected_encoding = await self._detect_encoding(file_path)

        # Determine target encoding
        target_encoding = self.config.encoding.target_charset or detected_encoding

        # Read and convert file
        content, had_errors = await self._read_and_convert(
            file_path, detected_encoding, target_encoding
        )

        # Create encoding info
        encoding_info = EncodingInfo(
            original_encoding=detected_encoding,
            target_encoding=(
                target_encoding if target_encoding != detected_encoding else None
            ),
            had_errors=had_errors,
        )

        return content, encoding_info

    async def _detect_encoding(self, file_path: Path) -> str:
        """Detect the encoding of a file."""
        # Default to utf-8 if chardet is not available
        if not CHARDET_AVAILABLE:
            self.logger.debug(f"chardet not available, using UTF-8 for {file_path}")
            return "utf-8"

        try:
            # Read file in binary mode with explicit handle cleanup
            raw_data = None
            with open(file_path, "rb") as f:
                raw_data = f.read(65536)  # Read up to 64KB
            # Explicitly ensure file handle is released
            f = None

            if not raw_data:
                return "utf-8"

            # Check for BOM (Byte Order Mark)
            if raw_data.startswith(b"\xff\xfe"):
                return "utf-16-le"
            elif raw_data.startswith(b"\xfe\xff"):
                return "utf-16-be"
            elif raw_data.startswith(b"\xef\xbb\xbf"):
                return "utf-8-sig"

            # Special handling for files with encoding hints in name
            file_name_lower = file_path.name.lower()
            if "latin1" in file_name_lower or "latin-1" in file_name_lower:
                return "latin-1"
            elif "utf16" in file_name_lower or "utf-16" in file_name_lower:
                # Check for UTF-16 pattern
                if self._looks_like_utf16(raw_data):
                    return "utf-16-le"

            # Try to decode as UTF-8 first (most common encoding)
            try:
                raw_data.decode("utf-8", errors="strict")
                self.logger.debug(f"Successfully decoded {file_path} as UTF-8")
                return "utf-8"
            except UnicodeDecodeError:
                # UTF-8 decoding failed, use chardet
                pass

            # Use chardet for detection
            result = chardet.detect(raw_data)

            # If chardet returns None or empty encoding, default to utf-8
            if not result or not result.get("encoding"):
                self.logger.debug(
                    f"chardet returned no encoding for {file_path}, using UTF-8"
                )
                return "utf-8"

            encoding = result["encoding"]
            confidence = result["confidence"]

            self.logger.debug(
                f"chardet detected {encoding} with confidence {confidence:.2f} for {file_path}"
            )

            # Low confidence threshold
            if confidence < 0.7:
                self.logger.debug(
                    f"Low confidence encoding detection for {file_path}: "
                    f"{encoding} ({confidence:.2f}), defaulting to UTF-8"
                )
                return "utf-8"

            # Map some common encoding names
            encoding_map = {
                "iso-8859-8": "windows-1255",  # Hebrew
                "ascii": "utf-8",  # Treat ASCII as UTF-8
            }

            # Special handling for Windows-1252 detection
            if encoding.lower() == "windows-1252":
                # Check if file extension suggests documentation files that should be UTF-8
                if (
                    self.config.encoding.prefer_utf8_for_text_files
                    and file_path.suffix.lower() in UTF8_PREFERRED_EXTENSIONS
                ):
                    # For documentation files, prefer UTF-8 over Windows-1252
                    # unless we have very high confidence
                    if confidence < 0.95:
                        self.logger.debug(
                            f"Preferring UTF-8 over {encoding} for documentation file {file_path}"
                        )
                        return "utf-8"

                # For other files, only use Windows-1252 if we have high confidence
                # and the file really can't be decoded as UTF-8
                if confidence < 0.9:
                    return "utf-8"

            return encoding_map.get(encoding.lower(), encoding.lower())

        except Exception as e:
            self.logger.warning(f"Error detecting encoding for {file_path}: {e}")
            return "utf-8"
        finally:
            # Force garbage collection on Windows to ensure file handles are released
            if sys.platform.startswith("win"):
                gc.collect()

    def _looks_like_utf16(self, data: bytes) -> bool:
        """Check if data looks like UTF-16 encoded text."""
        # Check if every other byte is zero (common in UTF-16-LE for ASCII text)
        if len(data) < 100:
            return False

        zero_count = 0
        for i in range(1, min(100, len(data)), 2):
            if data[i] == 0:
                zero_count += 1

        return zero_count > 40  # More than 40% of checked bytes are zero

    async def _read_and_convert(
        self, file_path: Path, source_encoding: str, target_encoding: str
    ) -> Tuple[str, bool]:
        """Read a file and convert to target encoding."""
        had_errors = False

        try:
            # Read file with source encoding and explicit handle cleanup
            content = None
            try:
                with open(file_path, "r", encoding=source_encoding) as f:
                    content = f.read()
            except UnicodeDecodeError as e:
                # If initial read fails, try with error handling
                self.logger.debug(
                    f"Initial read failed for {file_path} with {source_encoding}, "
                    f"retrying with error replacement"
                )
                with open(
                    file_path, "r", encoding=source_encoding, errors="replace"
                ) as f:
                    content = f.read()
                had_errors = True

            # Explicitly ensure file handle is released
            f = None

            # If no conversion needed, return as is
            if source_encoding.lower() == target_encoding.lower():
                return content, had_errors

            # Try to encode to target encoding
            try:
                # Encode and decode to ensure it's valid in target encoding
                encoded = content.encode(target_encoding, errors="strict")
                decoded = encoded.decode(target_encoding)

                if self.config.logging.verbose:
                    self.logger.debug(
                        f"Converted {file_path} from {source_encoding} to {target_encoding}"
                    )

                return decoded, had_errors

            except UnicodeEncodeError as e:
                if self.config.encoding.abort_on_error:
                    raise EncodingError(
                        f"Cannot convert {file_path} from {source_encoding} "
                        f"to {target_encoding}: {e}"
                    )

                # Fall back to replacement
                encoded = content.encode(target_encoding, errors="replace")
                decoded = encoded.decode(target_encoding)

                self.logger.warning(
                    f"Character conversion errors in {file_path} "
                    f"(from {source_encoding} to {target_encoding})"
                )

                return decoded, True

        except UnicodeDecodeError as e:
            # This shouldn't happen since we handle it above, but just in case
            if self.config.encoding.abort_on_error:
                raise EncodingError(
                    f"Cannot decode {file_path} with encoding {source_encoding}: {e}"
                )

            # Last resort: read as binary and decode with replacement
            try:
                binary_data = None
                with open(file_path, "rb") as f:
                    binary_data = f.read()
                # Explicitly ensure file handle is released
                f = None

                # Try UTF-8 first, then fallback to latin-1
                for fallback_encoding in ["utf-8", "latin-1"]:
                    try:
                        content = binary_data.decode(
                            fallback_encoding, errors="replace"
                        )
                        self.logger.warning(
                            f"Failed to decode {file_path} with {source_encoding}, "
                            f"using {fallback_encoding} fallback"
                        )
                        break
                    except Exception:
                        continue
                else:
                    # Ultimate fallback - decode as latin-1 which accepts all bytes
                    content = binary_data.decode("latin-1", errors="replace")
                    self.logger.error(
                        f"Failed to decode {file_path} properly, using latin-1 fallback"
                    )

                return content, True

            except Exception as e2:
                # Final fallback
                error_content = (
                    f"[ERROR: Unable to read file {file_path}. Reason: {e2}]"
                )
                return error_content, True

        except Exception as e:
            # Handle other errors (file not found, permissions, etc.)
            if self.config.encoding.abort_on_error:
                raise EncodingError(f"Error reading {file_path}: {e}")

            # Return error message as content
            error_content = f"[ERROR: Unable to read file {file_path}. Reason: {e}]"
            return error_content, True
        finally:
            # Force garbage collection on Windows to ensure file handles are released
            if sys.platform.startswith("win"):
                gc.collect()
