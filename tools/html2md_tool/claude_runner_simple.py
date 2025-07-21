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
Simplified Claude runner for debugging.
"""

import subprocess
import os
from pathlib import Path
from typing import Tuple, Optional
from rich.console import Console

console = Console()


class ClaudeRunnerSimple:
    """Simplified Claude runner without streaming."""

    def __init__(self, claude_binary: Optional[str] = None):
        self.claude_binary = claude_binary or self._find_claude_binary()

    def _find_claude_binary(self) -> str:
        """Find Claude binary in system."""
        # Check known locations
        claude_paths = [
            Path.home() / ".claude" / "local" / "claude",
            Path("/usr/local/bin/claude"),
            Path("/usr/bin/claude"),
        ]

        for path in claude_paths:
            if path.exists() and path.is_file():
                return str(path)

        # Try default command
        try:
            subprocess.run(
                ["claude", "--version"], capture_output=True, check=True, timeout=5
            )
            return "claude"
        except:
            pass

        raise FileNotFoundError("Claude CLI not found")

    def run_claude(
        self,
        prompt: str,
        allowed_tools: str = "Read,Glob,Grep,Write",
        add_dir: Optional[str] = None,
        timeout: int = 300,
        working_dir: Optional[str] = None,
    ) -> Tuple[int, str, str]:
        """Run Claude with simple subprocess."""

        cmd = [
            self.claude_binary,
            "--print",
            "--allowedTools",
            allowed_tools,
        ]

        if add_dir:
            cmd.extend(["--add-dir", add_dir])

        # Add prompt as command argument
        cmd.extend(["--", prompt])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=working_dir,
            )

            return result.returncode, result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return -1, "", str(e)
