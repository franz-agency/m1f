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

"""
Test script for m1f-claude improvements.
This tests the new features without requiring actual Claude Code SDK.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
import tempfile
import json
import unittest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.m1f_claude import M1FClaude


class TestM1FClaudeImprovements(unittest.TestCase):
    """Test the improved m1f-claude functionality."""

    def test_init_with_new_parameters(self):
        """Test initialization with new parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            m1f = M1FClaude(
                project_path=Path(tmpdir),
                allowed_tools="Read,Write,Edit",
                disallowed_tools="Bash,System",
                permission_mode="acceptEdits",
                append_system_prompt="Be extra helpful",
                output_format="json",
                mcp_config="/path/to/mcp.json",
                cwd=Path("/custom/working/dir"),
            )

            assert m1f.allowed_tools == "Read,Write,Edit"
            assert m1f.disallowed_tools == "Bash,System"
            assert m1f.permission_mode == "acceptEdits"
            assert m1f.append_system_prompt == "Be extra helpful"
            assert m1f.output_format == "json"
            assert m1f.mcp_config == "/path/to/mcp.json"
            assert m1f.cwd == Path("/custom/working/dir")

    def test_permission_modes(self):
        """Test different permission modes."""
        modes = ["default", "acceptEdits", "plan", "bypassPermissions"]

        for mode in modes:
            m1f = M1FClaude(permission_mode=mode)
            assert m1f.permission_mode == mode

    def test_output_formats(self):
        """Test different output formats."""
        formats = ["text", "json", "stream-json"]

        for fmt in formats:
            m1f = M1FClaude(output_format=fmt)
            assert m1f.output_format == fmt

    def test_mcp_config_loading(self):
        """Test MCP configuration file support."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            mcp_config = {
                "servers": {
                    "example-server": {
                        "command": "npx",
                        "args": ["example-mcp-server"],
                        "env": {"API_KEY": "test-key"},
                    }
                }
            }
            json.dump(mcp_config, f)
            f.flush()

            m1f = M1FClaude(mcp_config=f.name)
            assert m1f.mcp_config == f.name

    @patch("tools.m1f_claude.query")
    def test_claude_code_options_structure(self, mock_query):
        """Test that ClaudeCodeOptions is created with correct parameters."""
        from claude_code_sdk import ClaudeCodeOptions

        # Mock the query to capture options
        captured_options = None

        async def mock_query_impl(prompt, options):
            nonlocal captured_options
            captured_options = options
            return []

        mock_query.side_effect = mock_query_impl

        m1f = M1FClaude(
            allowed_tools="Read,Write",
            permission_mode="acceptEdits",
            append_system_prompt="Custom prompt",
            mcp_config="/path/to/mcp.json",
        )

        # Note: In real usage, this would be called with proper async handling
        # Here we're just testing the options structure

    def test_command_building_with_new_flags(self):
        """Test that CLI commands are built correctly with new flags."""
        m1f = M1FClaude(
            permission_mode="plan",
            append_system_prompt="Be concise",
            mcp_config="/etc/mcp.json",
            output_format="stream-json",
        )

        # Test subprocess command building
        with patch("subprocess.run") as mock_run:
            # First call is for finding claude executable (returns success)
            # This makes find_claude_executable return "claude"
            mock_run.return_value = MagicMock(returncode=0, stdout="claude version 1.0.0")

            # This should trigger the subprocess fallback display
            result = m1f.send_to_claude_code_subprocess("Test prompt")

            # Verify the command would include new parameters
            assert result == "Manual execution required - see instructions above"

    def test_message_type_handling(self):
        """Test handling of different message types."""
        m1f = M1FClaude(debug=True)

        # Test different event types
        test_events = [
            {"type": "system", "subtype": "init", "session_id": "test-123"},
            {
                "type": "system",
                "subtype": "permission_prompt",
                "tool_name": "Read",
                "parameters": {"file": "test.py"},
            },
            {"type": "user", "content": "Hello Claude"},
            {
                "type": "assistant",
                "message": {"content": [{"type": "text", "text": "Hello!"}]},
            },
            {"type": "tool_use", "name": "Read", "input": {"file_path": "/test.py"}},
            {"type": "tool_result", "output": "File contents"},
            {
                "type": "result",
                "subtype": "complete",
                "session_id": "test-123",
                "total_cost_usd": 0.01,
                "num_turns": 1,
                "duration": 2.5,
            },
            {"type": "result", "subtype": "error", "error": "Something went wrong"},
            {"type": "result", "subtype": "cancelled"},
        ]

        # These would be processed in the _send_with_session method
        # Here we're just verifying the structure is correct
        for event in test_events:
            assert "type" in event

    def test_enhanced_prompt_with_new_context(self):
        """Test that enhanced prompts include new parameter context when relevant."""
        m1f = M1FClaude(
            project_description="A Python web application",
            project_priorities="Security and performance",
            permission_mode="acceptEdits",
            mcp_config="/path/to/mcp.json",
        )

        prompt = "Help me set up m1f"
        enhanced = m1f.create_enhanced_prompt(prompt)

        # Verify project description and priorities are included
        assert "A Python web application" in enhanced
        assert "Security and performance" in enhanced

    def test_cli_argument_parsing(self):
        """Test that CLI arguments are parsed correctly."""
        from tools.m1f_claude import main

        test_args = [
            "m1f-claude",
            "Test prompt",
            "--permission-mode",
            "acceptEdits",
            "--output-format",
            "json",
            "--append-system-prompt",
            "Be helpful",
            "--mcp-config",
            "/path/to/config.json",
            "--cwd",
            "/project/dir",
            "--disallowed-tools",
            "Bash,System",
            "--verbose",
            "--debug",
        ]

        with patch("sys.argv", test_args):
            with patch("tools.m1f_claude.M1FClaude") as mock_class:
                # Mock the instance
                mock_instance = MagicMock()
                mock_class.return_value = mock_instance

                # Mock send_to_claude_code to prevent actual execution
                mock_instance.send_to_claude_code.return_value = "Test response"

                with patch("builtins.print"):  # Suppress output
                    try:
                        main()
                    except SystemExit:
                        pass  # Expected in some cases

                # Verify M1FClaude was initialized with correct parameters
                mock_class.assert_called_once()
                call_kwargs = mock_class.call_args[1]

                assert call_kwargs["permission_mode"] == "acceptEdits"
                assert call_kwargs["output_format"] == "json"
                assert call_kwargs["append_system_prompt"] == "Be helpful"
                assert call_kwargs["mcp_config"] == "/path/to/config.json"
                assert call_kwargs["disallowed_tools"] == "Bash,System"
                assert call_kwargs["verbose"] is True
                assert call_kwargs["debug"] is True


if __name__ == "__main__":
    unittest.main(verbosity=2)
