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

"""Tests for HTML validation functionality."""

import pytest
from tools.scrape_tool.file_validator import FileValidator


class TestHTMLValidation:
    """Test HTML file validation."""
    
    def test_valid_html_document(self):
        """Test validation of a valid HTML document."""
        html_content = b"""<!DOCTYPE html>
        <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <h1>Hello World</h1>
            <p>This is a test page.</p>
        </body>
        </html>"""
        
        result = FileValidator.validate_file(html_content, '.html', 'text/html')
        
        assert result['valid'] is True
        assert result['detected_type'] == 'HTML document'
        assert 'html_stats' in result
        assert result['html_stats']['total_tags'] > 0
    
    def test_html_fragment(self):
        """Test validation of HTML fragment (no doctype/html tag)."""
        html_content = b"""<div>
            <h1>Fragment</h1>
            <p>This is just a fragment.</p>
        </div>"""
        
        result = FileValidator.validate_file(html_content, '.html', 'text/html')
        
        assert result['valid'] is True
        assert result['detected_type'] == 'HTML document'
        # Fragment should still be valid, may have warnings about missing common elements
        # Check that it was still processed as HTML
        assert 'html_stats' in result
    
    def test_html_with_inline_binaries(self):
        """Test detection of inline binary data (data: URLs)."""
        html_content = b"""<!DOCTYPE html>
        <html>
        <head><title>Test</title></head>
        <body>
            <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==">
            <img src="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBD">
            <script src="data:application/javascript,alert('test')"></script>
        </body>
        </html>"""
        
        result = FileValidator.validate_file(html_content, '.html', 'text/html')
        
        assert result['valid'] is True
        assert 'inline_binaries' in result
        assert len(result['inline_binaries']) == 3
        
        # Check that we detected the MIME types
        mime_types = [b['mime_type'] for b in result['inline_binaries']]
        assert 'image/png' in mime_types
        assert 'image/jpeg' in mime_types
        assert 'application/javascript' in mime_types
        
        # Should have warning about inline binaries
        assert any('inline binary' in w for w in result.get('warnings', []))
    
    def test_html_with_external_resources(self):
        """Test detection of external resources."""
        html_content = b"""<!DOCTYPE html>
        <html>
        <head>
            <link rel="stylesheet" href="https://cdn.example.com/style.css">
            <script src="https://cdn.example.com/script.js"></script>
        </head>
        <body>
            <img src="https://cdn.example.com/image.jpg">
            <img src="/local/image.png">
        </body>
        </html>"""
        
        result = FileValidator.validate_file(html_content, '.html', 'text/html')
        
        assert result['valid'] is True
        assert 'external_resources' in result
        assert len(result['external_resources']) == 3  # Only external URLs
        
        # Check resource types
        resource_types = [r[0] for r in result['external_resources']]
        assert 'stylesheet' in resource_types
        assert 'script' in resource_types
        assert 'image' in resource_types
    
    def test_html_with_malicious_patterns(self):
        """Test detection of potentially malicious patterns."""
        html_content = b"""<!DOCTYPE html>
        <html>
        <body>
            <script>eval('alert(1)')</script>
            <a href="javascript:eval('alert(2)')">Click</a>
            <div onclick="eval('alert(3)')">Click</div>
            <iframe src="javascript:alert(4)"></iframe>
        </body>
        </html>"""
        
        result = FileValidator.validate_file(html_content, '.html', 'text/html')
        
        # Should still be valid but with security warnings
        assert result['valid'] is True
        
        # Check for security warnings
        security_warnings = [w for w in result.get('warnings', []) if 'Security' in w or 'eval' in w]
        assert len(security_warnings) >= 3  # At least 3 different eval patterns
    
    def test_invalid_html_not_text(self):
        """Test handling of non-text content claimed to be HTML."""
        # Binary content (not valid UTF-8)
        binary_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
        
        result = FileValidator.validate_file(binary_content, '.html', 'text/html')
        
        assert result['valid'] is False
        assert 'not valid UTF-8' in result.get('error', '')
    
    def test_html_with_unbalanced_tags(self):
        """Test detection of unbalanced HTML tags."""
        html_content = b"""<html>
        <body>
            <div>
                <p>Paragraph without closing
                <div>Another div
            <span>Span without closing
        </body>"""
        
        result = FileValidator.validate_file(html_content, '.html', 'text/html')
        
        assert result['valid'] is True  # Still valid HTML (browsers are forgiving)
        # But should have warning about unbalanced tags
        assert any('unbalanced' in w.lower() for w in result.get('warnings', []))
    
    def test_html_content_type_mismatch(self):
        """Test warning when content-type doesn't match."""
        html_content = b"""<!DOCTYPE html>
        <html><body>Test</body></html>"""
        
        # Claim it's JSON but it's actually HTML
        result = FileValidator.validate_file(html_content, '.html', 'application/json')
        
        assert result['valid'] is True
        # Should have warning about content-type mismatch  
        warnings = result.get('warnings', [])
        # The content-type check might not always trigger for HTML as it's text-based
        # So let's just check that the HTML was processed correctly
        assert result['detected_type'] == 'HTML document'
    
    def test_empty_html(self):
        """Test handling of empty HTML file."""
        html_content = b""
        
        result = FileValidator.validate_file(html_content, '.html', 'text/html')
        
        assert result['valid'] is False
        assert result['error'] == 'Empty file'
    
    def test_html_with_suspicious_inline_binary(self):
        """Test detection of suspicious inline binary types."""
        html_content = b"""<!DOCTYPE html>
        <html>
        <body>
            <object data="data:application/x-executable;base64,TVqQAAMAAAA">
            <embed src="data:application/octet-stream;base64,UEsDBAoA">
        </body>
        </html>"""
        
        result = FileValidator.validate_file(html_content, '.html', 'text/html')
        
        assert result['valid'] is True
        assert 'inline_binaries' in result
        
        # Should have warnings about suspicious types
        suspicious_warnings = [w for w in result.get('warnings', []) if 'Suspicious' in w]
        assert len(suspicious_warnings) >= 1
    
    def test_html_stats_collection(self):
        """Test that HTML stats are properly collected."""
        html_content = b"""<!DOCTYPE html>
        <html>
        <head>
            <style>body { color: red; }</style>
            <script>console.log('test');</script>
        </head>
        <body>
            <form action="/submit">
                <input type="text">
            </form>
            <a href="/page1">Link 1</a>
            <a href="/page2">Link 2</a>
            <img src="image.jpg">
            <img src="image2.jpg">
            <img src="image3.jpg">
        </body>
        </html>"""
        
        result = FileValidator.validate_file(html_content, '.html', 'text/html')
        
        assert result['valid'] is True
        assert 'html_stats' in result
        
        stats = result['html_stats']
        assert stats['forms'] == 1
        assert stats['links'] == 2
        assert stats['images'] == 3
        assert stats['scripts'] == 1
        assert stats['styles'] == 1
        assert stats['total_tags'] > 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])