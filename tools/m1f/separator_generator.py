"""
Separator generator module for creating file separators in various styles.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .config import Config, SeparatorStyle
from .constants import MACHINE_READABLE_BOUNDARY_PREFIX
from .encoding_handler import EncodingInfo
from .logging import LoggerManager
from .utils import format_file_size, calculate_checksum


class SeparatorGenerator:
    """Generates file separators in various styles."""
    
    def __init__(self, config: Config, logger_manager: LoggerManager):
        self.config = config
        self.logger = logger_manager.get_logger(__name__)
        self._current_uuid: Optional[str] = None
    
    async def generate_separator(
        self,
        file_path: Path,
        rel_path: str,
        encoding_info: EncodingInfo,
        file_content: str
    ) -> str:
        """Generate a file separator based on the configured style."""
        style = self.config.output.separator_style
        linesep = self.config.output.line_ending.value
        
        if style == SeparatorStyle.NONE:
            return ""
        
        # Gather file metadata
        metadata = self._gather_metadata(file_path, rel_path, encoding_info)
        
        # Calculate checksum if needed
        checksum = ""
        if style in [
            SeparatorStyle.STANDARD, 
            SeparatorStyle.DETAILED, 
            SeparatorStyle.MARKDOWN, 
            SeparatorStyle.MACHINE_READABLE
        ]:
            checksum = calculate_checksum(file_content)
        
        # Generate separator based on style
        if style == SeparatorStyle.STANDARD:
            return self._generate_standard(metadata, checksum)
        elif style == SeparatorStyle.DETAILED:
            return self._generate_detailed(metadata, checksum, linesep)
        elif style == SeparatorStyle.MARKDOWN:
            return self._generate_markdown(file_path, metadata, checksum, linesep)
        elif style == SeparatorStyle.MACHINE_READABLE:
            return self._generate_machine_readable(metadata, checksum, linesep)
        else:
            return f"--- {rel_path} ---"
    
    async def generate_closing_separator(self) -> Optional[str]:
        """Generate a closing separator if needed."""
        style = self.config.output.separator_style
        
        if style == SeparatorStyle.NONE:
            return ""
        elif style == SeparatorStyle.MARKDOWN:
            return "```"
        elif style == SeparatorStyle.MACHINE_READABLE and self._current_uuid:
            return f"--- {MACHINE_READABLE_BOUNDARY_PREFIX}_END_FILE_CONTENT_BLOCK_{self._current_uuid} ---"
        
        return None
    
    def _gather_metadata(
        self, 
        file_path: Path, 
        rel_path: str, 
        encoding_info: EncodingInfo
    ) -> dict:
        """Gather metadata about the file."""
        try:
            stat_info = file_path.stat()
            mod_time = datetime.fromtimestamp(stat_info.st_mtime)
            
            return {
                'relative_path': rel_path,
                'mod_date_str': mod_time.strftime("%Y-%m-%d %H:%M:%S"),
                'file_size_bytes': stat_info.st_size,
                'file_size_hr': format_file_size(stat_info.st_size),
                'file_ext': file_path.suffix.lower() if file_path.suffix else "[no extension]",
                'display_encoding': encoding_info.original_encoding,
                'encoding': encoding_info.target_encoding or encoding_info.original_encoding,
                'original_encoding': encoding_info.original_encoding,
                'had_encoding_errors': encoding_info.had_errors,
                'stat_info': stat_info
            }
        except Exception as e:
            self.logger.warning(f"Could not get metadata for {file_path}: {e}")
            return {
                'relative_path': rel_path,
                'mod_date_str': "[unknown]",
                'file_size_bytes': 0,
                'file_size_hr': "[unknown]",
                'file_ext': file_path.suffix.lower() if file_path.suffix else "[no extension]",
                'display_encoding': encoding_info.original_encoding,
                'encoding': encoding_info.target_encoding or encoding_info.original_encoding,
                'original_encoding': encoding_info.original_encoding,
                'had_encoding_errors': encoding_info.had_errors,
                'stat_info': None
            }
    
    def _generate_standard(self, metadata: dict, checksum: str) -> str:
        """Generate Standard style separator."""
        if checksum:
            return f"======= {metadata['relative_path']} | CHECKSUM_SHA256: {checksum} ======"
        return f"======= {metadata['relative_path']} ======"
    
    def _generate_detailed(self, metadata: dict, checksum: str, linesep: str) -> str:
        """Generate Detailed style separator."""
        separator_lines = [
            "=" * 88,
            f"== FILE: {metadata['relative_path']}",
            f"== DATE: {metadata['mod_date_str']} | SIZE: {metadata['file_size_hr']} | TYPE: {metadata['file_ext']}"
        ]
        
        # Add encoding information if available
        if metadata['display_encoding']:
            encoding_status = f"ENCODING: {metadata['display_encoding']}"
            if metadata['encoding'] and metadata['original_encoding'] and metadata['encoding'] != metadata['original_encoding']:
                encoding_status += f" (converted to {metadata['encoding']})"
            if metadata['had_encoding_errors']:
                encoding_status += " (with conversion errors)"
            separator_lines.append(f"== {encoding_status}")
        
        if checksum:
            separator_lines.append(f"== CHECKSUM_SHA256: {checksum}")
        
        separator_lines.append("=" * 88)
        return linesep.join(separator_lines)
    
    def _generate_markdown(
        self, 
        file_path: Path, 
        metadata: dict, 
        checksum: str, 
        linesep: str
    ) -> str:
        """Generate Markdown style separator."""
        # Determine language hint for syntax highlighting
        md_lang_hint = file_path.suffix[1:] if file_path.suffix and len(file_path.suffix) > 1 else ""
        
        metadata_line = f"**Date Modified:** {metadata['mod_date_str']} | **Size:** {metadata['file_size_hr']} | **Type:** {metadata['file_ext']}"
        
        # Add encoding information if available
        if metadata['display_encoding']:
            encoding_status = f"**Encoding:** {metadata['display_encoding']}"
            if metadata['encoding'] and metadata['original_encoding'] and metadata['encoding'] != metadata['original_encoding']:
                encoding_status += f" (converted to {metadata['encoding']})"
            if metadata['had_encoding_errors']:
                encoding_status += " (with conversion errors)"
            metadata_line += f" | {encoding_status}"
        
        if checksum:
            metadata_line += f" | **Checksum (SHA256):** {checksum}"
        
        separator_lines = [
            f"## {metadata['relative_path']}",
            metadata_line,
            "",  # Empty line before code block
            f"```{md_lang_hint}"
        ]
        return linesep.join(separator_lines)
    
    def _generate_machine_readable(self, metadata: dict, checksum: str, linesep: str) -> str:
        """Generate MachineReadable style separator."""
        # Generate new UUID for this file
        self._current_uuid = str(uuid.uuid4())
        
        # Create metadata for the file
        meta = {
            "original_filepath": str(metadata['relative_path']),
            "original_filename": Path(metadata['relative_path']).name,
            "timestamp_utc_iso": datetime.fromtimestamp(
                metadata['stat_info'].st_mtime if metadata['stat_info'] else 0, 
                tz=timezone.utc
            ).isoformat().replace("+00:00", "Z"),
            "type": metadata['file_ext'],
            "size_bytes": metadata['file_size_bytes'],
            "checksum_sha256": checksum if checksum else ""
        }
        
        # Add encoding information
        if metadata['original_encoding']:
            meta["encoding"] = self._normalize_encoding_name(metadata['original_encoding'])
            
            if metadata['encoding'] != metadata['original_encoding']:
                meta["target_encoding"] = self._normalize_encoding_name(metadata['encoding'])
        
        if metadata['had_encoding_errors']:
            meta["had_encoding_errors"] = True
        
        json_meta = json.dumps(meta, indent=4)
        
        separator_lines = [
            f"--- {MACHINE_READABLE_BOUNDARY_PREFIX}_BEGIN_FILE_METADATA_BLOCK_{self._current_uuid} ---",
            "METADATA_JSON:",
            json_meta,
            f"--- {MACHINE_READABLE_BOUNDARY_PREFIX}_END_FILE_METADATA_BLOCK_{self._current_uuid} ---",
            f"--- {MACHINE_READABLE_BOUNDARY_PREFIX}_BEGIN_FILE_CONTENT_BLOCK_{self._current_uuid} ---",
            ""
        ]
        return linesep.join(separator_lines)
    
    def _normalize_encoding_name(self, encoding_name: str) -> str:
        """Normalize encoding names to canonical forms."""
        if not encoding_name:
            return encoding_name
        
        enc_lower = encoding_name.lower()
        
        # Map common encoding name variants
        encoding_map = {
            'utf_8': 'utf-8',
            'utf8': 'utf-8',
            'utf-8': 'utf-8',
            'utf_16': 'utf-16',
            'utf16': 'utf-16',
            'utf-16': 'utf-16',
            'utf_16_le': 'utf-16-le',
            'utf16le': 'utf-16-le',
            'utf-16-le': 'utf-16-le',
            'utf_16_be': 'utf-16-be',
            'utf16be': 'utf-16-be',
            'utf-16-be': 'utf-16-be',
            'latin_1': 'latin-1',
            'latin1': 'latin-1',
            'latin-1': 'latin-1',
            'iso_8859_1': 'latin-1',
            'iso-8859-1': 'latin-1',
            'cp1252': 'windows-1252',
            'windows_1252': 'windows-1252',
            'windows-1252': 'windows-1252',
        }
        
        return encoding_map.get(enc_lower, encoding_name) 