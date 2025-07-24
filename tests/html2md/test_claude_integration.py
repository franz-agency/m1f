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

import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the tools directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from html2md_tool.claude_runner import ClaudeRunner


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


class TestCLIIntegration:
    """Test the CLI integration with improved Claude handling."""

    def test_analyze_with_claude(self, tmp_path):
        """Test the analyze command with Claude improvements."""
        # Create test HTML files
        html_dir = tmp_path / "html"
        html_dir.mkdir()

        for i in range(3):
            html_file = html_dir / f"test{i}.html"
            html_file.write_text(
                f"""
            <html>
            <head><title>Test {i}</title></head>
            <body>
                <main>
                    <h1>Test Document {i}</h1>
                    <p>This is test content {i}.</p>
                </main>
            </body>
            </html>
            """
            )

        # Mock the ClaudeRunner to avoid actual API calls
        with patch("html2md_tool.cli_claude.ClaudeRunner") as mock_runner_class:
            mock_runner = MagicMock()
            mock_runner_class.return_value = mock_runner

            # Mock file selection
            mock_runner.run_claude_streaming.return_value = (
                0,
                "test0.html\ntest1.html\ntest2.html",
                "",
            )

            # Mock parallel analysis
            mock_runner.run_claude_parallel.return_value = [
                {
                    "name": "Analysis 1: test0.html",
                    "success": True,
                    "stdout": "Analysis 1",
                    "stderr": "",
                },
                {
                    "name": "Analysis 2: test1.html",
                    "success": True,
                    "stdout": "Analysis 2",
                    "stderr": "",
                },
                {
                    "name": "Analysis 3: test2.html",
                    "success": True,
                    "stdout": "Analysis 3",
                    "stderr": "",
                },
            ]

            # Import after patching
            from html2md_tool.cli_claude import handle_claude_analysis_improved

            # Run analysis with mocked input
            with patch("builtins.input", return_value="Test project"):
                html_files = list(html_dir.glob("*.html"))
                handle_claude_analysis_improved(
                    html_files, num_files_to_analyze=3, parallel_workers=3
                )

            # Verify Claude was called correctly
            assert mock_runner.run_claude_streaming.call_count >= 1
            assert mock_runner.run_claude_parallel.call_count == 1

            # Verify parallel tasks were created
            parallel_call = mock_runner.run_claude_parallel.call_args[0][0]
            assert len(parallel_call) == 3
            assert all("prompt" in task for task in parallel_call)


if __name__ == "__main__":
    # Run specific test if provided
    if len(sys.argv) > 1:
        pytest.main([__file__, "-v", "-k", sys.argv[1]])
    else:
        pytest.main([__file__, "-v"])
