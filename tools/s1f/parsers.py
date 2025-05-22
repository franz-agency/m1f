"""Parsers for different separator formats."""

import json
import re
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Pattern
from datetime import datetime
import logging

from .models import ExtractedFile, FileMetadata, SeparatorMatch
from .utils import convert_to_posix_path, parse_iso_timestamp
from .exceptions import FileParsingError


class SeparatorParser(ABC):
    """Abstract base class for separator parsers."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of this parser."""
        pass
    
    @property
    @abstractmethod
    def pattern(self) -> Pattern:
        """Get the regex pattern for this separator type."""
        pass
    
    @abstractmethod
    def parse_match(self, match: re.Match, content: str, index: int) -> Optional[SeparatorMatch]:
        """Parse a regex match into a SeparatorMatch object."""
        pass
    
    @abstractmethod
    def extract_content(self, content: str, current_match: SeparatorMatch, 
                        next_match: Optional[SeparatorMatch]) -> str:
        """Extract file content between separators."""
        pass


class PYMK1FParser(SeparatorParser):
    """Parser for PYMK1F format with UUID-based separators."""
    
    PATTERN = re.compile(
        r"--- PYMK1F_BEGIN_FILE_METADATA_BLOCK_([a-f0-9-]+) ---\r?\n"
        r"METADATA_JSON:\r?\n"
        r"(\{(?:.|\s)*?\})\r?\n"
        r"--- PYMK1F_END_FILE_METADATA_BLOCK_\1 ---\r?\n"
        r"--- PYMK1F_BEGIN_FILE_CONTENT_BLOCK_\1 ---\r?\n",
        re.MULTILINE | re.DOTALL,
    )
    
    END_MARKER_PATTERN = "--- PYMK1F_END_FILE_CONTENT_BLOCK_{uuid} ---"
    
    @property
    def name(self) -> str:
        return "PYMK1F"
    
    @property
    def pattern(self) -> Pattern:
        return self.PATTERN
    
    def parse_match(self, match: re.Match, content: str, index: int) -> Optional[SeparatorMatch]:
        """Parse a PYMK1F format match."""
        try:
            uuid = match.group(1)
            json_str = match.group(2)
            meta = json.loads(json_str)
            
            # Extract path from metadata
            path = meta.get("original_filepath", "").strip()
            path = convert_to_posix_path(path)
            
            if not path:
                self.logger.warning(
                    f"PYMK1F block at offset {match.start()} has missing or empty path"
                )
                return None
            
            # Parse timestamp if available
            timestamp = None
            if "timestamp_utc_iso" in meta:
                try:
                    timestamp = parse_iso_timestamp(meta["timestamp_utc_iso"])
                except ValueError as e:
                    self.logger.warning(f"Failed to parse timestamp: {e}")
            
            # Extract encoding info
            encoding = meta.get("encoding")
            had_errors = meta.get("had_encoding_errors", False)
            if had_errors and encoding:
                encoding += " (with conversion errors)"
            
            return SeparatorMatch(
                separator_type=self.name,
                start_index=match.start(),
                end_index=match.end(),
                metadata={
                    "path": path,
                    "checksum_sha256": meta.get("checksum_sha256"),
                    "size_bytes": meta.get("size_bytes"),
                    "modified": timestamp,
                    "encoding": encoding,
                    "line_endings": meta.get("line_endings", ""),
                    "type": meta.get("type"),
                },
                header_length=len(match.group(0)),
                uuid=uuid,
            )
            
        except json.JSONDecodeError as e:
            self.logger.warning(
                f"PYMK1F block at offset {match.start()} has invalid JSON: {e}"
            )
            return None
        except Exception as e:
            self.logger.warning(
                f"Error parsing PYMK1F block at offset {match.start()}: {e}"
            )
            return None
    
    def extract_content(self, content: str, current_match: SeparatorMatch,
                        next_match: Optional[SeparatorMatch]) -> str:
        """Extract content for PYMK1F format."""
        content_start = current_match.end_index
        
        # Find the end marker with matching UUID
        if current_match.uuid:
            end_marker = self.END_MARKER_PATTERN.format(uuid=current_match.uuid)
            end_pos = content.find(end_marker, content_start)
            
            if end_pos != -1:
                file_content = content[content_start:end_pos]
            else:
                self.logger.warning(
                    f"PYMK1F file '{current_match.metadata['path']}' missing end marker"
                )
                # Fallback to next separator or EOF
                if next_match:
                    file_content = content[content_start:next_match.start_index]
                else:
                    file_content = content[content_start:]
        else:
            # No UUID available
            if next_match:
                file_content = content[content_start:next_match.start_index]
            else:
                file_content = content[content_start:]
        
        # Apply pragmatic fix for trailing \r if needed
        if (current_match.metadata.get("size_bytes") is not None and 
            current_match.metadata.get("checksum_sha256") is not None):
            file_content = self._apply_trailing_cr_fix(file_content, current_match.metadata)
        
        return file_content
    
    def _apply_trailing_cr_fix(self, content: str, metadata: Dict[str, Any]) -> str:
        """Apply pragmatic fix for trailing \r character."""
        try:
            current_bytes = content.encode("utf-8")
            current_size = len(current_bytes)
            original_size = metadata["size_bytes"]
            
            if current_size == original_size + 1 and content.endswith("\r"):
                # Verify if removing \r would match the original checksum
                import hashlib
                fixed_bytes = content[:-1].encode("utf-8")
                fixed_checksum = hashlib.sha256(fixed_bytes).hexdigest()
                
                if (fixed_checksum == metadata["checksum_sha256"] and 
                    len(fixed_bytes) == original_size):
                    self.logger.info(
                        f"Applied trailing \\r fix for '{metadata['path']}'"
                    )
                    return content[:-1]
                    
        except Exception as e:
            self.logger.warning(f"Error during trailing \\r fix attempt: {e}")
        
        return content


class MachineReadableParser(SeparatorParser):
    """Parser for legacy MachineReadable format."""
    
    PATTERN = re.compile(
        r"# PYM1F-BOUNDARY-99C5F740A78D4ABC82E3F9882D5A281E\r?\n"
        r"# FILE: (.*?)\r?\n"
        r"# PYM1F-BOUNDARY-99C5F740A78D4ABC82E3F9882D5A281E\r?\n"
        r"# METADATA: (\{.*?\})\r?\n"
        r"# PYM1F-BOUNDARY-99C5F740A78D4ABC82E3F9882D5A281E\r?\n",
        re.MULTILINE,
    )
    
    END_MARKER_PATTERN = re.compile(
        r"# PYM1F-BOUNDARY-99C5F740A78D4ABC82E3F9882D5A281E\r?\n"
        r"# END FILE\r?\n"
        r"# PYM1F-BOUNDARY-99C5F740A78D4ABC82E3F9882D5A281E",
        re.MULTILINE,
    )
    
    @property
    def name(self) -> str:
        return "MachineReadable"
    
    @property
    def pattern(self) -> Pattern:
        return self.PATTERN
    
    def parse_match(self, match: re.Match, content: str, index: int) -> Optional[SeparatorMatch]:
        """Parse a MachineReadable format match."""
        try:
            path = match.group(1).strip()
            path = convert_to_posix_path(path)
            
            if not path:
                self.logger.warning(
                    f"MachineReadable block at offset {match.start()} has empty path"
                )
                return None
            
            # Parse metadata JSON
            json_str = match.group(2)
            meta = json.loads(json_str)
            
            # Parse timestamp if available
            timestamp = None
            if "modified" in meta:
                try:
                    timestamp = parse_iso_timestamp(meta["modified"])
                except ValueError as e:
                    self.logger.warning(f"Failed to parse timestamp: {e}")
            
            # Calculate header length including potential blank line
            header_len = len(match.group(0))
            next_pos = match.end()
            if next_pos < len(content) and content[next_pos:next_pos + 2] in ["\r\n", "\n"]:
                header_len += 2 if content[next_pos:next_pos + 2] == "\r\n" else 1
            
            return SeparatorMatch(
                separator_type=self.name,
                start_index=match.start(),
                end_index=match.end(),
                metadata={
                    "path": path,
                    "checksum_sha256": meta.get("checksum_sha256"),
                    "size_bytes": meta.get("size_bytes"),
                    "modified": timestamp,
                    "encoding": meta.get("encoding"),
                    "line_endings": meta.get("line_endings", ""),
                    "type": meta.get("type"),
                },
                header_length=header_len,
            )
            
        except json.JSONDecodeError as e:
            self.logger.warning(
                f"MachineReadable block at offset {match.start()} has invalid JSON: {e}"
            )
            return None
        except Exception as e:
            self.logger.warning(
                f"Error parsing MachineReadable block at offset {match.start()}: {e}"
            )
            return None
    
    def extract_content(self, content: str, current_match: SeparatorMatch,
                        next_match: Optional[SeparatorMatch]) -> str:
        """Extract content for MachineReadable format."""
        content_start = current_match.end_index
        
        # Find the end marker
        end_search = self.END_MARKER_PATTERN.search(content, content_start)
        
        if end_search:
            end_pos = end_search.start()
            # Check for newline before marker
            if end_pos > 1 and content[end_pos - 2:end_pos] == "\r\n":
                end_pos -= 2
            elif end_pos > 0 and content[end_pos - 1] == "\n":
                end_pos -= 1
        else:
            self.logger.warning(
                f"MachineReadable file '{current_match.metadata['path']}' missing end marker"
            )
            # Fallback to next separator or EOF
            if next_match:
                end_pos = next_match.start_index
            else:
                end_pos = len(content)
        
        return content[content_start:end_pos]


class MarkdownParser(SeparatorParser):
    """Parser for Markdown format."""
    
    PATTERN = re.compile(
        r"^(## (.*?)$\r?\n"
        r"(?:\*\*Date Modified:\*\* .*? \| \*\*Size:\*\* .*? \| \*\*Type:\*\* .*?"
        r"(?:\s\|\s\*\*Encoding:\*\*\s(.*?)(?:\s\(with conversion errors\))?)?"
        r"(?:\s\|\s\*\*Checksum \(SHA256\):\*\*\s([0-9a-fA-F]{64}))?)$\r?\n\r?\n"
        r"```(?:.*?)$\r?\n)",
        re.MULTILINE,
    )
    
    @property
    def name(self) -> str:
        return "Markdown"
    
    @property
    def pattern(self) -> Pattern:
        return self.PATTERN
    
    def parse_match(self, match: re.Match, content: str, index: int) -> Optional[SeparatorMatch]:
        """Parse a Markdown format match."""
        path = match.group(2).strip()
        path = convert_to_posix_path(path)
        
        if not path:
            return None
        
        encoding = None
        if match.group(3):
            encoding = match.group(3)
        
        return SeparatorMatch(
            separator_type=self.name,
            start_index=match.start(),
            end_index=match.end(),
            metadata={
                "path": path,
                "checksum_sha256": match.group(4) if match.group(4) else None,
                "encoding": encoding,
            },
            header_length=len(match.group(1)),
        )
    
    def extract_content(self, content: str, current_match: SeparatorMatch,
                        next_match: Optional[SeparatorMatch]) -> str:
        """Extract content for Markdown format."""
        content_start = current_match.end_index
        
        if next_match:
            raw_content = content[content_start:next_match.start_index]
        else:
            raw_content = content[content_start:]
        
        # Strip inter-file newline if not last file
        if next_match:
            if raw_content.endswith("\r\n"):
                raw_content = raw_content[:-2]
            elif raw_content.endswith("\n"):
                raw_content = raw_content[:-1]
        
        # Strip closing marker
        if raw_content.endswith("```\r\n"):
            return raw_content[:-5]
        elif raw_content.endswith("```\n"):
            return raw_content[:-4]
        else:
            self.logger.warning(
                f"Markdown file '{current_match.metadata['path']}' missing closing marker"
            )
            return raw_content


class DetailedParser(SeparatorParser):
    """Parser for Detailed format."""
    
    PATTERN = re.compile(
        r"^(========================================================================================$\r?\n"
        r"== FILE: (.*?)$\r?\n"
        r"== DATE: .*? \| SIZE: .*? \| TYPE: .*?$\r?\n"
        r"(?:== ENCODING: (.*?)(?:\s\(with conversion errors\))?$\r?\n)?"
        r"(?:== CHECKSUM_SHA256: ([0-9a-fA-F]{64})$\r?\n)?"
        r"========================================================================================$\r?\n?)",
        re.MULTILINE,
    )
    
    @property
    def name(self) -> str:
        return "Detailed"
    
    @property
    def pattern(self) -> Pattern:
        return self.PATTERN
    
    def parse_match(self, match: re.Match, content: str, index: int) -> Optional[SeparatorMatch]:
        """Parse a Detailed format match."""
        path = match.group(2).strip()
        path = convert_to_posix_path(path)
        
        if not path:
            return None
        
        return SeparatorMatch(
            separator_type=self.name,
            start_index=match.start(),
            end_index=match.end(),
            metadata={
                "path": path,
                "checksum_sha256": match.group(4) if match.group(4) else None,
                "encoding": match.group(3) if match.group(3) else None,
            },
            header_length=len(match.group(1)),
        )
    
    def extract_content(self, content: str, current_match: SeparatorMatch,
                        next_match: Optional[SeparatorMatch]) -> str:
        """Extract content for Detailed format."""
        return self._extract_standard_format_content(content, current_match, next_match)
    
    def _extract_standard_format_content(self, content: str, current_match: SeparatorMatch,
                                         next_match: Optional[SeparatorMatch]) -> str:
        """Extract content for Standard/Detailed formats."""
        content_start = current_match.end_index
        
        if next_match:
            raw_content = content[content_start:next_match.start_index]
        else:
            raw_content = content[content_start:]
        
        # Strip leading blank line
        if raw_content.startswith("\r\n"):
            raw_content = raw_content[2:]
        elif raw_content.startswith("\n"):
            raw_content = raw_content[1:]
        
        # Strip trailing inter-file newline if not last file
        if next_match:
            if raw_content.endswith("\r\n"):
                raw_content = raw_content[:-2]
            elif raw_content.endswith("\n"):
                raw_content = raw_content[:-1]
        
        return raw_content


class StandardParser(DetailedParser):
    """Parser for Standard format."""
    
    PATTERN = re.compile(
        r"======= (.*?)(?:\s*\|\s*CHECKSUM_SHA256:\s*([0-9a-fA-F]{64}))?\s*======",
        re.MULTILINE,
    )
    
    @property
    def name(self) -> str:
        return "Standard"
    
    @property
    def pattern(self) -> Pattern:
        return self.PATTERN
    
    def parse_match(self, match: re.Match, content: str, index: int) -> Optional[SeparatorMatch]:
        """Parse a Standard format match."""
        path = match.group(1).strip()
        path = convert_to_posix_path(path)
        
        if not path:
            return None
        
        return SeparatorMatch(
            separator_type=self.name,
            start_index=match.start(),
            end_index=match.end(),
            metadata={
                "path": path,
                "checksum_sha256": match.group(2) if match.group(2) else None,
                "encoding": None,
            },
            header_length=0,  # Standard format doesn't have multi-line headers
        )


class CombinedFileParser:
    """Main parser that coordinates all separator parsers."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.parsers = [
            PYMK1FParser(logger),
            MachineReadableParser(logger),
            MarkdownParser(logger),
            DetailedParser(logger),
            StandardParser(logger),
        ]
    
    def parse(self, content: str) -> List[ExtractedFile]:
        """Parse the combined file content and extract individual files."""
        # Find all matches from all parsers
        matches: List[SeparatorMatch] = []
        
        for parser in self.parsers:
            for match in parser.pattern.finditer(content):
                separator_match = parser.parse_match(match, content, len(matches))
                if separator_match:
                    matches.append(separator_match)
        
        # Sort by position in file
        matches.sort(key=lambda m: m.start_index)
        
        if not matches:
            self.logger.warning("No recognizable file separators found")
            return []
        
        # Extract files
        extracted_files: List[ExtractedFile] = []
        
        for i, current_match in enumerate(matches):
            # Find the appropriate parser
            parser = next(p for p in self.parsers if p.name == current_match.separator_type)
            
            # Get next match if available
            next_match = matches[i + 1] if i + 1 < len(matches) else None
            
            # Extract content
            file_content = parser.extract_content(content, current_match, next_match)
            
            # Create metadata
            metadata = FileMetadata(
                path=current_match.metadata["path"],
                checksum_sha256=current_match.metadata.get("checksum_sha256"),
                size_bytes=current_match.metadata.get("size_bytes"),
                modified=current_match.metadata.get("modified"),
                encoding=current_match.metadata.get("encoding"),
                line_endings=current_match.metadata.get("line_endings"),
                type=current_match.metadata.get("type"),
            )
            
            # Create extracted file
            extracted_file = ExtractedFile(metadata=metadata, content=file_content)
            extracted_files.append(extracted_file)
            
            self.logger.debug(
                f"Identified file: '{metadata.path}', type: {current_match.separator_type}, "
                f"content length: {len(file_content)}"
            )
        
        return extracted_files 