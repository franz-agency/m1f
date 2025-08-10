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

"""Test CLI argument parsing for multiple allowed paths."""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch

from tools.scrape_tool.cli import create_parser


class TestMultipleAllowedPathsCLI:
    """Test CLI parsing for multiple allowed paths feature."""

    def test_single_allowed_path_parsing(self):
        """Test that single --allowed-path still works."""
        parser = create_parser()
        args = parser.parse_args([
            'https://example.com', 
            '-o', '/tmp/output',
            '--allowed-path', '/docs/'
        ])
        
        assert args.allowed_path == '/docs/'
        assert args.allowed_paths is None

    def test_multiple_allowed_paths_parsing(self):
        """Test that --allowed-paths accepts multiple paths."""
        parser = create_parser()
        args = parser.parse_args([
            'https://example.com', 
            '-o', '/tmp/output',
            '--allowed-paths', '/docs/', '/api/', '/guides/'
        ])
        
        assert args.allowed_path is None
        assert args.allowed_paths == ['/docs/', '/api/', '/guides/']

    def test_empty_allowed_paths_parsing(self):
        """Test that --allowed-paths can be empty."""
        parser = create_parser()
        args = parser.parse_args([
            'https://example.com', 
            '-o', '/tmp/output',
            '--allowed-paths'
        ])
        
        assert args.allowed_path is None
        assert args.allowed_paths == []

    def test_mutual_exclusivity_error(self):
        """Test that --allowed-path and --allowed-paths cannot be used together."""
        parser = create_parser()
        
        with pytest.raises(SystemExit):
            args = parser.parse_args([
                'https://example.com', 
                '-o', '/tmp/output',
                '--allowed-path', '/docs/',
                '--allowed-paths', '/api/', '/guides/'
            ])

    def test_neither_path_option(self):
        """Test that neither path option is fine."""
        parser = create_parser()
        args = parser.parse_args([
            'https://example.com', 
            '-o', '/tmp/output'
        ])
        
        assert args.allowed_path is None
        assert args.allowed_paths is None

    def test_help_text_includes_new_option(self):
        """Test that help text includes the new --allowed-paths option."""
        parser = create_parser()
        help_text = parser.format_help()
        
        assert '--allowed-path' in help_text
        assert '--allowed-paths' in help_text
        assert 'multiple paths' in help_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])