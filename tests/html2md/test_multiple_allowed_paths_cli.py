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
        """Test that --allowed-path works as an alias for --allowed-paths."""
        parser = create_parser()
        args = parser.parse_args([
            'https://example.com', 
            '-o', '/tmp/output',
            '--allowed-path', '/docs/'
        ])
        
        # --allowed-path is now an alias for --allowed-paths
        assert args.allowed_paths == ['/docs/']

    def test_multiple_allowed_paths_parsing(self):
        """Test that --allowed-paths accepts multiple paths."""
        parser = create_parser()
        args = parser.parse_args([
            'https://example.com', 
            '-o', '/tmp/output',
            '--allowed-paths', '/docs/', '/api/', '/guides/'
        ])
        
        assert args.allowed_paths == ['/docs/', '/api/', '/guides/']

    def test_empty_allowed_paths_parsing(self):
        """Test that --allowed-paths can be empty."""
        parser = create_parser()
        args = parser.parse_args([
            'https://example.com', 
            '-o', '/tmp/output',
            '--allowed-paths'
        ])
        
        assert args.allowed_paths == []

    def test_both_aliases_work_together(self):
        """Test that --allowed-path and --allowed-paths work together as aliases."""
        parser = create_parser()
        
        # Since they're aliases, the last one wins
        args = parser.parse_args([
            'https://example.com', 
            '-o', '/tmp/output',
            '--allowed-path', '/docs/',
            '--allowed-paths', '/api/', '/guides/'
        ])
        
        # The last argument (--allowed-paths) overrides the previous one
        assert args.allowed_paths == ['/api/', '/guides/']

    def test_neither_path_option(self):
        """Test that neither path option is fine."""
        parser = create_parser()
        args = parser.parse_args([
            'https://example.com', 
            '-o', '/tmp/output'
        ])
        
        # Only allowed_paths exists now (allowed_path is an alias)
        assert args.allowed_paths is None

    def test_help_text_includes_new_option(self):
        """Test that help text includes the --allowed-paths option."""
        parser = create_parser()
        help_text = parser.format_help()
        
        # Only --allowed-paths should be visible in help
        # --allowed-path is a hidden alias
        assert '--allowed-paths' in help_text
        assert 'restrict crawling to specified paths' in help_text.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])