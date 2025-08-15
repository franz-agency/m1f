#!/usr/bin/env python3
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

"""File validation for downloaded assets using magic numbers and basic checks."""

import logging
from typing import Optional, Dict, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class FileValidator:
    """Validates downloaded files by checking magic numbers and basic structure."""
    
    # Magic numbers (file signatures) for common file types
    # Format: file_extension -> (offset, bytes_to_match, description)
    MAGIC_NUMBERS = {
        # Images
        '.jpg': [(0, b'\xFF\xD8\xFF', 'JPEG image')],
        '.jpeg': [(0, b'\xFF\xD8\xFF', 'JPEG image')],
        '.png': [(0, b'\x89PNG\r\n\x1a\n', 'PNG image')],
        '.gif': [
            (0, b'GIF87a', 'GIF87a image'),
            (0, b'GIF89a', 'GIF89a image')
        ],
        '.webp': [(8, b'WEBP', 'WebP image')],  # RIFF....WEBP
        '.ico': [
            (0, b'\x00\x00\x01\x00', 'ICO icon'),
            (0, b'\x00\x00\x02\x00', 'CUR cursor')
        ],
        '.svg': [(0, b'<svg', 'SVG image'), (0, b'<?xml', 'SVG/XML image')],
        '.bmp': [(0, b'BM', 'BMP image')],
        
        # Documents
        '.pdf': [(0, b'%PDF-', 'PDF document')],
        '.doc': [(0, b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1', 'MS Office document')],
        '.docx': [(0, b'PK\x03\x04', 'Office Open XML')],  # Actually a ZIP
        '.xls': [(0, b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1', 'MS Office document')],
        '.xlsx': [(0, b'PK\x03\x04', 'Office Open XML')],
        '.ppt': [(0, b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1', 'MS Office document')],
        '.pptx': [(0, b'PK\x03\x04', 'Office Open XML')],
        
        # Archives
        '.zip': [(0, b'PK\x03\x04', 'ZIP archive'), (0, b'PK\x05\x06', 'Empty ZIP')],
        '.gz': [(0, b'\x1f\x8b', 'GZIP archive')],
        '.tar': [(257, b'ustar', 'TAR archive')],
        '.rar': [
            (0, b'Rar!\x1A\x07\x00', 'RAR v1.5+'),
            (0, b'Rar!\x1A\x07\x01\x00', 'RAR v5+')
        ],
        '.7z': [(0, b'7z\xBC\xAF\x27\x1C', '7-Zip archive')],
        
        # Fonts
        '.ttf': [
            (0, b'\x00\x01\x00\x00', 'TrueType font'),
            (0, b'true', 'TrueType font'),
            (0, b'OTTO', 'OpenType font')
        ],
        '.otf': [(0, b'OTTO', 'OpenType font')],
        '.woff': [(0, b'wOFF', 'WOFF font')],
        '.woff2': [(0, b'wOF2', 'WOFF2 font')],
        '.eot': [(0, b'\x00\x00\x00\x00', 'EOT font')],  # Less reliable
        
        # Media
        '.mp4': [(4, b'ftyp', 'MP4 video')],
        '.webm': [(0, b'\x1A\x45\xDF\xA3', 'WebM video')],
        '.mp3': [
            (0, b'ID3', 'MP3 with ID3'),
            (0, b'\xFF\xFB', 'MP3 audio'),
            (0, b'\xFF\xF3', 'MP3 audio'),
            (0, b'\xFF\xF2', 'MP3 audio')
        ],
        '.wav': [(0, b'RIFF', 'WAV audio'), (8, b'WAVE', 'WAV audio')],
        '.ogg': [(0, b'OggS', 'OGG media')],
        
        # Text/Code (these don't have magic numbers, need content check)
        '.html': None,
        '.htm': None,
        '.css': None,
        '.js': None,
        '.json': None,
        '.xml': None,
        '.txt': None,
        '.md': None,
        '.csv': None,
    }
    
    @classmethod
    def validate_file(cls, content: bytes, file_extension: str, 
                      content_type: Optional[str] = None) -> Dict[str, any]:
        """Validate file content against expected format.
        
        Args:
            content: Binary content of the file
            file_extension: File extension (with dot, e.g., '.jpg')
            content_type: Optional HTTP Content-Type header
            
        Returns:
            Dictionary with validation results:
            - valid: Boolean indicating if file is valid
            - format_match: Boolean if magic number matches
            - detected_type: Detected file type
            - warnings: List of warning messages
            - error: Error message if validation failed
        """
        result = {
            'valid': False,
            'format_match': False,
            'detected_type': None,
            'warnings': [],
            'error': None,
            'file_size': len(content),
        }
        
        # Check minimum size
        if len(content) == 0:
            result['error'] = 'Empty file'
            return result
        
        # Normalize extension
        ext = file_extension.lower() if file_extension else ''
        if not ext.startswith('.'):
            ext = '.' + ext
        
        # Check if we have magic numbers for this type
        if ext not in cls.MAGIC_NUMBERS:
            result['warnings'].append(f'Unknown file type: {ext}')
            result['valid'] = True  # Assume valid if we don't know the type
            return result
        
        magic_specs = cls.MAGIC_NUMBERS[ext]
        
        # Text files don't have magic numbers
        if magic_specs is None:
            return cls._validate_text_file(content, ext, result)
        
        # Check magic numbers
        for offset, expected_bytes, description in magic_specs:
            if cls._check_magic_number(content, offset, expected_bytes):
                result['format_match'] = True
                result['detected_type'] = description
                result['valid'] = True
                break
        
        if not result['format_match']:
            # Try to detect actual type
            actual_type = cls._detect_file_type(content)
            if actual_type:
                result['error'] = f'File extension {ext} does not match content (detected: {actual_type})'
                result['detected_type'] = actual_type
            else:
                result['error'] = f'Invalid {ext} file: magic number mismatch'
        
        # Additional validation for specific types
        if result['valid']:
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                cls._validate_image_structure(content, ext, result)
            elif ext == '.pdf':
                cls._validate_pdf_structure(content, result)
            elif ext in ['.zip', '.gz', '.tar', '.rar', '.7z']:
                cls._validate_archive_structure(content, ext, result)
        
        # Check content type mismatch
        if content_type and result['valid']:
            cls._check_content_type_match(ext, content_type, result)
        
        return result
    
    @staticmethod
    def _check_magic_number(content: bytes, offset: int, expected: bytes) -> bool:
        """Check if content matches expected bytes at offset."""
        if len(content) < offset + len(expected):
            return False
        return content[offset:offset + len(expected)] == expected
    
    @classmethod
    def _detect_file_type(cls, content: bytes) -> Optional[str]:
        """Try to detect actual file type from content."""
        # Check against all known magic numbers
        for ext, magic_specs in cls.MAGIC_NUMBERS.items():
            if magic_specs is None:
                continue
            for offset, expected_bytes, description in magic_specs:
                if cls._check_magic_number(content, offset, expected_bytes):
                    return f'{description} ({ext})'
        return None
    
    @classmethod
    def _validate_text_file(cls, content: bytes, ext: str, result: Dict) -> Dict:
        """Validate text-based files."""
        try:
            # Try to decode as UTF-8
            text = content.decode('utf-8')
            result['valid'] = True
            result['format_match'] = True
            
            # Specific checks for different text types
            if ext == '.json':
                import json
                try:
                    json.loads(text)
                    result['detected_type'] = 'JSON document'
                except json.JSONDecodeError as e:
                    result['warnings'].append(f'Invalid JSON: {str(e)[:100]}')
                    result['valid'] = False
                    
            elif ext in ['.html', '.htm']:
                result['detected_type'] = 'HTML document'
                cls._validate_html_content(text, result)
                
            elif ext == '.xml' or ext == '.svg':
                if not text.strip().startswith('<'):
                    result['warnings'].append('XML/SVG should start with <')
                result['detected_type'] = 'XML document'
                
            elif ext == '.css':
                # Basic CSS check - look for common patterns
                css_patterns = ['{', '}', ':', ';', '/*', '*/']
                if not any(p in text for p in css_patterns):
                    result['warnings'].append('File does not appear to contain CSS')
                result['detected_type'] = 'CSS stylesheet'
                
            elif ext == '.js':
                # Basic JavaScript check
                js_keywords = ['function', 'var', 'let', 'const', 'return', 
                              'if', 'for', 'while', '=>', '=', '(', ')']
                if not any(kw in text for kw in js_keywords):
                    result['warnings'].append('File does not appear to contain JavaScript')
                result['detected_type'] = 'JavaScript code'
                
            elif ext == '.csv':
                # Check for comma/tab/semicolon separators
                if ',' not in text and '\t' not in text and ';' not in text:
                    result['warnings'].append('CSV file has no visible delimiters')
                result['detected_type'] = 'CSV data'
                
            else:
                result['detected_type'] = 'Plain text'
                
        except UnicodeDecodeError:
            result['error'] = f'Invalid {ext} file: not valid UTF-8 text'
            result['valid'] = False
            
        return result
    
    @classmethod
    def _validate_html_content(cls, text: str, result: Dict):
        """Validate HTML content and check for inline binaries."""
        import re
        
        # Check basic HTML structure
        text_lower = text.lower()
        
        # Check for HTML tags
        if '<html' not in text_lower and '<!doctype' not in text_lower:
            # May be a fragment, still valid
            if not re.search(r'<[^>]+>', text):
                result['warnings'].append('No HTML tags found')
                result['valid'] = False
                return
        
        # Check for common HTML elements
        html_elements = ['<head', '<body', '<div', '<p', '<a', '<img', '<script', '<style']
        if not any(elem in text_lower for elem in html_elements):
            result['warnings'].append('Missing common HTML elements')
        
        # Check for balanced tags (basic check)
        open_tags = len(re.findall(r'<[^/][^>]*>', text))
        close_tags = len(re.findall(r'</[^>]+>', text))
        if open_tags > 0 and abs(open_tags - close_tags) > open_tags * 0.3:  # Allow 30% imbalance
            result['warnings'].append(f'Potentially unbalanced HTML tags (open: {open_tags}, close: {close_tags})')
        
        # Detect inline binaries (data: URLs)
        inline_binaries = []
        
        # Find data URLs in various contexts
        data_url_pattern = r'data:([^;,]+)(;[^,]*)?,([^"\'\s>]+)'
        data_urls = re.findall(data_url_pattern, text)
        
        for mime_type, encoding, data in data_urls:
            # Check the MIME type
            if mime_type:
                inline_binaries.append({
                    'mime_type': mime_type,
                    'encoding': encoding.strip(';') if encoding else None,
                    'size': len(data)
                })
        
        if inline_binaries:
            result['inline_binaries'] = inline_binaries
            result['warnings'].append(f'Found {len(inline_binaries)} inline binary data URLs')
            
            # Check for suspicious inline binaries
            suspicious_types = ['application/x-', 'application/octet-stream']
            for binary in inline_binaries:
                if any(susp in binary['mime_type'] for susp in suspicious_types):
                    result['warnings'].append(f'Suspicious inline binary type: {binary["mime_type"]}')
        
        # Check for external scripts/resources
        external_resources = []
        
        # Find external scripts
        script_srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', text, re.IGNORECASE)
        for src in script_srcs:
            if src.startswith(('http://', 'https://', '//')):
                external_resources.append(('script', src))
        
        # Find external stylesheets
        link_hrefs = re.findall(r'<link[^>]+href=["\']([^"\']+)["\']', text, re.IGNORECASE)
        for href in link_hrefs:
            if href.startswith(('http://', 'https://', '//')):
                external_resources.append(('stylesheet', href))
        
        # Find external images
        img_srcs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', text, re.IGNORECASE)
        for src in img_srcs:
            if not src.startswith('data:') and src.startswith(('http://', 'https://', '//')):
                external_resources.append(('image', src))
        
        if external_resources:
            result['external_resources'] = external_resources
            result['warnings'].append(f'Found {len(external_resources)} external resources')
        
        # Check for potentially malicious patterns
        malicious_patterns = [
            (r'<script[^>]*>.*?eval\s*\(', 'Potential eval() in script'),
            (r'javascript:\s*eval\s*\(', 'eval() in javascript: URL'),
            (r'on\w+\s*=\s*["\'].*?eval\s*\(', 'eval() in event handler'),
            (r'<iframe[^>]+src=["\']javascript:', 'JavaScript URL in iframe'),
            (r'<object[^>]+data=["\']javascript:', 'JavaScript URL in object'),
        ]
        
        for pattern, description in malicious_patterns:
            if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
                result['warnings'].append(f'Security warning: {description}')
        
        # Try to parse with BeautifulSoup for more thorough validation
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(text, 'html.parser')
            
            # Check if parsing resulted in meaningful content
            if not soup.find_all():
                result['warnings'].append('HTML parsing resulted in no elements')
            
            # Count various elements
            result['html_stats'] = {
                'total_tags': len(soup.find_all()),
                'images': len(soup.find_all('img')),
                'scripts': len(soup.find_all('script')),
                'styles': len(soup.find_all('style')),
                'links': len(soup.find_all('a')),
                'forms': len(soup.find_all('form')),
            }
            
        except Exception as e:
            result['warnings'].append(f'BeautifulSoup parsing error: {str(e)[:100]}')
    
    @staticmethod
    def _validate_image_structure(content: bytes, ext: str, result: Dict):
        """Additional validation for image files using Pillow if available."""
        # Check minimum reasonable size for images
        if len(content) < 100:
            result['warnings'].append('Suspiciously small image file')
        
        # Try to use Pillow for proper validation
        try:
            from PIL import Image
            import io
            
            # Try to open and verify the image
            try:
                img = Image.open(io.BytesIO(content))
                img.verify()  # Verify image integrity
                
                # Get image info
                result['image_info'] = {
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size if hasattr(img, 'size') else None,
                }
                
                # Check if format matches extension
                expected_formats = {
                    '.jpg': ['JPEG'],
                    '.jpeg': ['JPEG'],
                    '.png': ['PNG'],
                    '.gif': ['GIF'],
                    '.webp': ['WEBP'],
                    '.bmp': ['BMP'],
                    '.ico': ['ICO'],
                }
                
                if ext in expected_formats:
                    if img.format not in expected_formats[ext]:
                        result['warnings'].append(
                            f'Image format mismatch: {img.format} saved as {ext}'
                        )
                
            except Exception as e:
                result['warnings'].append(f'Pillow validation failed: {str(e)[:100]}')
                result['valid'] = False
                
        except ImportError:
            # Pillow not available, fall back to basic checks
            # JPEG specific
            if ext in ['.jpg', '.jpeg']:
                # Check for JPEG end marker
                if not content.endswith(b'\xFF\xD9'):
                    result['warnings'].append('JPEG file may be truncated (missing end marker)')
            
            # PNG specific
            elif ext == '.png':
                # Check for PNG end chunk
                if not content.endswith(b'\x00\x00\x00\x00IEND\xAE\x42\x60\x82'):
                    result['warnings'].append('PNG file may be truncated (missing IEND chunk)')
            
            # GIF specific
            elif ext == '.gif':
                # Check for GIF trailer
                if not content.endswith(b'\x00;') and not content.endswith(b';'):
                    result['warnings'].append('GIF file may be truncated (missing trailer)')
    
    @staticmethod
    def _validate_pdf_structure(content: bytes, result: Dict):
        """Additional validation for PDF files using PyPDF2 if available."""
        # Try to use PyPDF2 for proper validation
        try:
            import PyPDF2
            import io
            
            try:
                pdf_file = io.BytesIO(content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                # Get PDF info
                result['pdf_info'] = {
                    'num_pages': len(pdf_reader.pages),
                    'is_encrypted': pdf_reader.is_encrypted,
                }
                
                # Try to access metadata
                if pdf_reader.metadata:
                    metadata = {}
                    if pdf_reader.metadata.title:
                        metadata['title'] = str(pdf_reader.metadata.title)
                    if pdf_reader.metadata.author:
                        metadata['author'] = str(pdf_reader.metadata.author)
                    if metadata:
                        result['pdf_info']['metadata'] = metadata
                
            except Exception as e:
                result['warnings'].append(f'PyPDF2 validation failed: {str(e)[:100]}')
                # Don't mark as invalid - might be encrypted or have other issues
                
        except ImportError:
            # PyPDF2 not available, fall back to basic checks
            # Check for PDF end marker
            if b'%%EOF' not in content[-1024:]:  # Check last 1KB
                result['warnings'].append('PDF file may be truncated (missing %%EOF)')
            
            # Check for basic PDF structure
            if b'endobj' not in content:
                result['warnings'].append('PDF file appears corrupted (no objects found)')
    
    @staticmethod
    def _validate_archive_structure(content: bytes, ext: str, result: Dict):
        """Additional validation for archive files."""
        # Check minimum reasonable size
        if len(content) < 22:  # Minimum ZIP size
            result['warnings'].append('Archive file too small to be valid')
        
        # ZIP specific
        if ext == '.zip':
            # Check for central directory end signature
            if b'PK\x05\x06' not in content[-65536:]:  # Check last 64KB
                result['warnings'].append('ZIP file may be corrupted (missing end record)')
    
    @staticmethod
    def _check_content_type_match(ext: str, content_type: str, result: Dict):
        """Check if file extension matches Content-Type header."""
        content_type = content_type.lower().split(';')[0].strip()
        
        expected_types = {
            '.jpg': ['image/jpeg', 'image/jpg'],
            '.jpeg': ['image/jpeg', 'image/jpg'],
            '.png': ['image/png'],
            '.gif': ['image/gif'],
            '.webp': ['image/webp'],
            '.svg': ['image/svg+xml', 'text/xml', 'application/xml'],
            '.pdf': ['application/pdf'],
            '.css': ['text/css'],
            '.js': ['application/javascript', 'text/javascript', 'application/x-javascript'],
            '.json': ['application/json', 'text/json'],
            '.xml': ['application/xml', 'text/xml'],
            '.txt': ['text/plain'],
            '.html': ['text/html', 'application/xhtml+xml'],
            '.htm': ['text/html', 'application/xhtml+xml'],
            '.zip': ['application/zip', 'application/x-zip-compressed'],
            '.gz': ['application/gzip', 'application/x-gzip'],
        }
        
        if ext in expected_types:
            if content_type not in expected_types[ext]:
                result['warnings'].append(
                    f'Content-Type mismatch: got {content_type}, expected {expected_types[ext][0]}'
                )