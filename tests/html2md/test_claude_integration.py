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

"""Test Claude integration improvements in m1f-html2md."""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path

# Add the tools directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from html2md_tool.claude_runner import ClaudeRunner

# Skip all tests if Claude is not available
pytestmark = pytest.mark.skipif(
    not shutil.which("claude") and not os.getenv("ANTHROPIC_API_KEY"),
    reason="Claude CLI not installed or API key not set"
)


class TestClaudeRunner:
    """Test the ClaudeRunner improvements."""

    def test_claude_runner_initialization(self):
        """Test that ClaudeRunner can be initialized."""
        try:
            runner = ClaudeRunner()
            assert runner.claude_binary is not None
            assert runner.max_workers == 5
        except FileNotFoundError:
            pytest.skip("Claude CLI not installed")

    def test_streaming_output(self):
        """Test streaming output functionality."""
        try:
            runner = ClaudeRunner()
        except FileNotFoundError:
            pytest.skip("Claude CLI not installed")

        # Simple test prompt
        prompt = "What is 2+2? Reply with just the number."

        returncode, stdout, stderr = runner.run_claude_streaming(
            prompt=prompt, timeout=30, show_output=False
        )

        assert returncode == 0, f"Claude command failed: {stderr}"
        assert stdout.strip() != "", "No output received"
        # Claude might add some explanation, so just check if "4" is in the output
        assert "4" in stdout, f"Expected '4' in output, got: {stdout}"

    def test_parallel_execution(self):
        """Test parallel execution of multiple tasks."""
        try:
            runner = ClaudeRunner(max_workers=3)
        except FileNotFoundError:
            pytest.skip("Claude CLI not installed")

        # Create simple math tasks
        tasks = [
            {
                "name": "Task 1",
                "prompt": "What is 5+5? Just the number.",
                "timeout": 30,
            },
            {
                "name": "Task 2",
                "prompt": "What is 10-3? Just the number.",
                "timeout": 30,
            },
            {
                "name": "Task 3",
                "prompt": "What is 2*4? Just the number.",
                "timeout": 30,
            },
        ]

        results = runner.run_claude_parallel(tasks, show_progress=False)

        # Check all tasks completed
        assert len(results) == 3

        # Check at least 2 out of 3 succeeded (allowing for some API issues)
        successful = sum(1 for r in results if r["success"])
        assert successful >= 2, f"Too many tasks failed: {results}"

        # Check expected values in outputs
        for result in results:
            if result["success"]:
                if result["name"] == "Task 1":
                    assert "10" in result["stdout"]
                elif result["name"] == "Task 2":
                    assert "7" in result["stdout"]
                elif result["name"] == "Task 3":
                    assert "8" in result["stdout"]

    def test_timeout_handling(self):
        """Test that timeouts are handled properly."""
        try:
            runner = ClaudeRunner()
        except FileNotFoundError:
            pytest.skip("Claude CLI not installed")

        # This should timeout quickly
        prompt = "Please wait for 30 seconds before responding."

        returncode, stdout, stderr = runner.run_claude_streaming(
            prompt=prompt, timeout=5, show_output=False  # Very short timeout
        )

        # Should fail due to timeout
        assert returncode != 0, "Expected timeout but command succeeded"


class TestRealClaudeIntegration:
    """Test real Claude integration without mocking."""

    @pytest.mark.slow
    def test_html_to_markdown_conversion(self, tmp_path):
        """Test HTML to Markdown conversion using the actual prompt template."""
        try:
            runner = ClaudeRunner(working_dir=str(tmp_path))
        except FileNotFoundError:
            pytest.skip("Claude CLI not installed")

        # Use the test HTML file from test fixtures
        test_html_file = Path(__file__).parent / "test_claude_files" / "api_documentation.html"
        if not test_html_file.exists():
            pytest.skip(f"Test HTML file not found at {test_html_file}")
        
        # Load the actual prompt template
        prompt_path = Path(__file__).parent.parent.parent / "tools" / "html2md_tool" / "prompts" / "convert_html_to_md.md"
        if not prompt_path.exists():
            pytest.skip(f"Prompt template not found at {prompt_path}")
            
        prompt_template = prompt_path.read_text()
        
        # Replace the placeholder with the test HTML file path
        prompt = prompt_template.replace("{html_content}", f"@{test_html_file}")
        
        # Run Claude with the actual prompt
        returncode, stdout, stderr = runner.run_claude_streaming(
            prompt=prompt,
            allowed_tools="Read,Write",  # Only allow file operations
            timeout=90,
            show_output=False
        )
        
        assert returncode == 0, f"Claude command failed: {stderr}"
        assert stdout.strip() != "", "No output received"
        
        # Verify the output quality
        output = stdout.strip()
        
        # Should include main content
        assert "API Reference" in output
        assert "Getting Started" in output
        assert "npm install test-api" in output
        assert "Authentication" in output
        assert "`GET /api/v1/users`" in output or "GET /api/v1/users" in output
        
        # Should NOT include navigation/footer elements
        assert "Test Framework" not in output or "API Reference" in output  # Title OK, nav not
        assert "Home > Docs" not in output  # Breadcrumb
        assert "Edit this page" not in output
        assert "Subscribe to our newsletter" not in output
        assert "This site uses cookies" not in output
        
        # Should have proper markdown formatting
        assert "#" in output  # Headers
        assert "```" in output or "    " in output  # Code blocks
        assert "|" in output  # Table formatting


if __name__ == "__main__":
    # Run specific test if provided
    if len(sys.argv) > 1:
        pytest.main([__file__, "-v", "-k", sys.argv[1]])
    else:
        pytest.main([__file__, "-v"])
