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

"""Tests for file validation functionality."""

import pytest
from tools.scrape_tool.file_validator import FileValidator


class TestFileValidator:
    """Test file validation functionality."""
    
    def test_validate_jpeg(self):
        """Test JPEG file validation."""
        # Valid JPEG header and footer
        valid_jpeg = b'\xFF\xD8\xFF\xE0' + b'\x00' * 100 + b'\xFF\xD9'
        result = FileValidator.validate_file(valid_jpeg, '.jpg')
        
        assert result['valid'] == True
        assert result['format_match'] == True
        assert 'JPEG' in result['detected_type']
        
        # Invalid JPEG (wrong magic number)
        invalid_jpeg = b'NOT_A_JPEG' + b'\x00' * 100
        result = FileValidator.validate_file(invalid_jpeg, '.jpg')
        
        assert result['valid'] == False
        assert result['format_match'] == False
        assert result['error'] is not None
    
    def test_validate_png(self):
        """Test PNG file validation."""
        # Valid PNG header with IEND chunk
        valid_png = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100 + b'\x00\x00\x00\x00IEND\xAE\x42\x60\x82'
        result = FileValidator.validate_file(valid_png, '.png')
        
        assert result['valid'] == True
        assert result['format_match'] == True
        assert 'PNG' in result['detected_type']
        
        # PNG without IEND chunk (truncated)
        truncated_png = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        result = FileValidator.validate_file(truncated_png, '.png')
        
        assert result['valid'] == True  # Still valid PNG header
        assert result['format_match'] == True
        assert len(result['warnings']) > 0  # Should warn about missing IEND
        assert 'truncated' in result['warnings'][0].lower()
    
    def test_validate_gif(self):
        """Test GIF file validation."""
        # Valid GIF87a
        valid_gif87 = b'GIF87a' + b'\x00' * 100 + b'\x00;'
        result = FileValidator.validate_file(valid_gif87, '.gif')
        
        assert result['valid'] == True
        assert result['format_match'] == True
        assert 'GIF87a' in result['detected_type']
        
        # Valid GIF89a
        valid_gif89 = b'GIF89a' + b'\x00' * 100 + b';'
        result = FileValidator.validate_file(valid_gif89, '.gif')
        
        assert result['valid'] == True
        assert result['format_match'] == True
        assert 'GIF89a' in result['detected_type']
    
    def test_validate_pdf(self):
        """Test PDF file validation."""
        # Valid PDF
        valid_pdf = b'%PDF-1.4' + b'\x00' * 100 + b'endobj' + b'\x00' * 50 + b'%%EOF'
        result = FileValidator.validate_file(valid_pdf, '.pdf')
        
        assert result['valid'] == True
        assert result['format_match'] == True
        assert 'PDF' in result['detected_type']
        
        # PDF without EOF marker
        truncated_pdf = b'%PDF-1.4' + b'\x00' * 100 + b'endobj'
        result = FileValidator.validate_file(truncated_pdf, '.pdf')
        
        assert result['valid'] == True  # Still valid PDF header
        assert len(result['warnings']) > 0
        assert '%%EOF' in result['warnings'][0]
    
    def test_validate_text_files(self):
        """Test text file validation."""
        # Valid JSON
        valid_json = b'{"key": "value", "number": 123}'
        result = FileValidator.validate_file(valid_json, '.json')
        
        assert result['valid'] == True
        assert result['format_match'] == True
        assert 'JSON' in result['detected_type']
        
        # Invalid JSON
        invalid_json = b'{"key": "value", invalid}'
        result = FileValidator.validate_file(invalid_json, '.json')
        
        assert result['valid'] == False
        assert 'Invalid JSON' in result['warnings'][0]
        
        # Valid CSS
        valid_css = b'body { margin: 0; padding: 0; } /* comment */'
        result = FileValidator.validate_file(valid_css, '.css')
        
        assert result['valid'] == True
        assert 'CSS' in result['detected_type']
        
        # Valid JavaScript
        valid_js = b'function test() { return true; }'
        result = FileValidator.validate_file(valid_js, '.js')
        
        assert result['valid'] == True
        assert 'JavaScript' in result['detected_type']
        
        # Valid CSV
        valid_csv = b'header1,header2,header3\nvalue1,value2,value3'
        result = FileValidator.validate_file(valid_csv, '.csv')
        
        assert result['valid'] == True
        assert 'CSV' in result['detected_type']
    
    def test_validate_zip(self):
        """Test ZIP file validation."""
        # Valid ZIP
        valid_zip = b'PK\x03\x04' + b'\x00' * 100 + b'PK\x05\x06' + b'\x00' * 18
        result = FileValidator.validate_file(valid_zip, '.zip')
        
        assert result['valid'] == True
        assert result['format_match'] == True
        assert 'ZIP' in result['detected_type']
    
    def test_validate_webp(self):
        """Test WebP file validation."""
        # Valid WebP (RIFF....WEBP format)
        valid_webp = b'RIFF\x00\x00\x00\x00WEBP' + b'\x00' * 100
        result = FileValidator.validate_file(valid_webp, '.webp')
        
        assert result['valid'] == True
        assert result['format_match'] == True
        assert 'WebP' in result['detected_type']
    
    def test_empty_file(self):
        """Test empty file validation."""
        empty = b''
        result = FileValidator.validate_file(empty, '.jpg')
        
        assert result['valid'] == False
        assert result['error'] == 'Empty file'
    
    def test_unknown_file_type(self):
        """Test unknown file type."""
        content = b'Some random content'
        result = FileValidator.validate_file(content, '.xyz')
        
        assert result['valid'] == True  # Unknown types are assumed valid
        assert 'Unknown file type' in result['warnings'][0]
    
    def test_file_type_mismatch(self):
        """Test when file extension doesn't match content."""
        # JPEG content with PNG extension
        jpeg_content = b'\xFF\xD8\xFF\xE0' + b'\x00' * 100
        result = FileValidator.validate_file(jpeg_content, '.png')
        
        assert result['valid'] == False
        assert result['format_match'] == False
        assert 'does not match content' in result['error']
        assert 'JPEG' in result['detected_type']
    
    def test_content_type_validation(self):
        """Test Content-Type header validation."""
        # Correct content type (with proper JPEG ending)
        jpeg_content = b'\xFF\xD8\xFF\xE0' + b'\x00' * 100 + b'\xFF\xD9'
        result = FileValidator.validate_file(jpeg_content, '.jpg', 'image/jpeg')
        
        assert result['valid'] == True
        assert len(result['warnings']) == 0
        
        # Wrong content type
        result = FileValidator.validate_file(jpeg_content, '.jpg', 'image/png')
        
        assert result['valid'] == True  # Still valid JPEG
        assert len(result['warnings']) > 0
        assert 'Content-Type mismatch' in result['warnings'][0]
    
    def test_small_file_warning(self):
        """Test warning for suspiciously small files."""
        # Very small "image"
        small_jpeg = b'\xFF\xD8\xFF\xE0\xFF\xD9'  # Minimal JPEG
        result = FileValidator.validate_file(small_jpeg, '.jpg')
        
        assert result['valid'] == True
        assert result['format_match'] == True
        assert len(result['warnings']) > 0
        assert 'small' in result['warnings'][0].lower()
    
    def test_font_validation(self):
        """Test font file validation."""
        # WOFF font
        woff = b'wOFF' + b'\x00' * 100
        result = FileValidator.validate_file(woff, '.woff')
        
        assert result['valid'] == True
        assert result['format_match'] == True
        assert 'WOFF' in result['detected_type']
        
        # WOFF2 font
        woff2 = b'wOF2' + b'\x00' * 100
        result = FileValidator.validate_file(woff2, '.woff2')
        
        assert result['valid'] == True
        assert result['format_match'] == True
        assert 'WOFF2' in result['detected_type']
    
    def test_svg_validation(self):
        """Test SVG file validation."""
        # SVG with <svg> tag
        svg1 = b'<svg xmlns="http://www.w3.org/2000/svg"></svg>'
        result = FileValidator.validate_file(svg1, '.svg')
        
        assert result['valid'] == True
        assert result['format_match'] == True
        assert 'SVG' in result['detected_type'] or 'XML' in result['detected_type']
        
        # SVG with XML declaration
        svg2 = b'<?xml version="1.0"?><svg></svg>'
        result = FileValidator.validate_file(svg2, '.svg')
        
        assert result['valid'] == True
        assert result['format_match'] == True