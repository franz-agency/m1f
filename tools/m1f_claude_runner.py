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
Claude runner with streaming output and timeout handling for m1f-claude.
Based on improvements from html2md tool.
"""

import subprocess
import time
import sys
from pathlib import Path
from typing import Tuple, Optional, IO, Callable
import signal

# Use unified colorama module
try:
    from .shared.colors import success, error, warning, info
except ImportError:
    # Try direct import if running as script
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from tools.shared.colors import success, error, warning, info

# Import shared Claude utilities
try:
    from .shared.claude_utils import (
        ClaudeBinaryFinder,
        ClaudeErrorHandler,
        ClaudeRunner,
        ClaudeConfig,
    )
except ImportError:
    from tools.shared.claude_utils import (
        ClaudeBinaryFinder,
        ClaudeErrorHandler,
        ClaudeRunner,
        ClaudeConfig,
    )

# Import safe file operations
try:
    from .m1f.file_operations import (
        safe_exists,
        safe_is_file,
    )
except ImportError:
    from tools.m1f.file_operations import (
        safe_exists,
        safe_is_file,
    )


class M1FClaudeRunner(ClaudeRunner):
    """Handles Claude CLI execution with streaming output and robust timeout handling."""

    def __init__(
        self, claude_binary: Optional[str] = None, config: Optional[ClaudeConfig] = None
    ):
        super().__init__(config=config, binary_path=claude_binary)
        self.process = None

    def run_claude_streaming(
        self,
        prompt: str,
        working_dir: str,
        allowed_tools: str = "Read,Write,Edit,MultiEdit,Glob,Grep",
        add_dir: Optional[str] = None,
        timeout: int = 600,  # 10 minutes default
        show_output: bool = True,
        output_handler: Optional[callable] = None,
        permission_mode: str = "default",
        append_system_prompt: Optional[str] = None,
        mcp_config: Optional[str] = None,
        disallowed_tools: Optional[str] = None,
        output_format: str = "text",
        cwd: Optional[str] = None,
    ) -> Tuple[int, str, str]:
        """
        Run Claude with real-time streaming output and improved timeout handling.

        Args:
            prompt: The prompt to send to Claude
            working_dir: Working directory for the command
            allowed_tools: Comma-separated list of allowed tools
            add_dir: Directory to add to Claude's context
            timeout: Maximum time in seconds (default 600s = 10 minutes)
            show_output: Whether to print output to console
            output_handler: Optional callback for each output line

        Returns:
            (returncode, stdout, stderr)
        """
        # Build command - use --print mode and stdin for prompt
        cmd = [
            self.get_binary(),
            "--print",  # Use print mode for non-interactive output
            "--allowedTools",
            allowed_tools,
        ]

        if add_dir:
            cmd.extend(["--add-dir", add_dir])

        # Add new optional parameters
        if permission_mode != "default":
            cmd.extend(["--permission-mode", permission_mode])
        if append_system_prompt:
            cmd.extend(["--append-system-prompt", append_system_prompt])
        if mcp_config:
            cmd.extend(["--mcp-config", mcp_config])
        if disallowed_tools:
            cmd.extend(["--disallowedTools", disallowed_tools])
        if output_format != "text":
            cmd.extend(["--output-format", output_format])
        if cwd:
            cmd.extend(["--cwd", cwd])

        # Use conservative timeout (at least 60 seconds)
        actual_timeout = max(60, timeout)

        # Collect all output
        stdout_lines = []
        stderr_lines = []

        # Signal handler for graceful interruption
        def handle_interrupt(signum, frame):
            if self.process:
                warning("\n🛑 Interrupting Claude... Press Ctrl-C again to force quit.")
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            raise KeyboardInterrupt()

        old_handler = signal.signal(signal.SIGINT, handle_interrupt)

        try:
            # Start the process
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=working_dir,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            # Send the prompt and close stdin
            self.process.stdin.write(prompt)
            self.process.stdin.close()

            # Track timing
            start_time = time.time()
            last_output_time = start_time

            # Progress indicators
            spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
            spinner_idx = 0

            # Read output line by line
            while True:
                line = self.process.stdout.readline()
                if line == "" and self.process.poll() is not None:
                    break

                if line:
                    line = line.rstrip()
                    stdout_lines.append(line)
                    current_time = time.time()
                    elapsed = current_time - start_time

                    if show_output:
                        # Show progress with elapsed time (no truncation, terminal will soft wrap)
                        info(f"[{elapsed:5.1f}s] {line}")

                    if output_handler:
                        output_handler(line, elapsed)

                    last_output_time = current_time
                else:
                    # No output, check for timeout
                    current_time = time.time()
                    elapsed = current_time - start_time

                    # Check absolute timeout
                    if elapsed > actual_timeout:
                        if show_output:
                            warning(f"\n⏰ Claude timed out after {actual_timeout}s")
                        self.process.kill()
                        return (
                            -1,
                            "\n".join(stdout_lines),
                            f"Process timed out after {actual_timeout}s",
                        )

                    # Check inactivity timeout (120 seconds)
                    if current_time - last_output_time > 120:
                        if show_output:
                            warning(
                                f"\n⏰ Claude inactive for 120s (total time: {elapsed:.1f}s)"
                            )
                        self.process.kill()
                        return (
                            -1,
                            "\n".join(stdout_lines),
                            "Process inactive for 120 seconds",
                        )

                    # Show spinner to indicate we're still waiting
                    if show_output and int(elapsed) % 5 == 0:
                        sys.stdout.write(
                            f"\r⏳ Waiting for Claude... {spinner_chars[spinner_idx]} [{elapsed:.0f}s]"
                        )
                        sys.stdout.flush()
                        spinner_idx = (spinner_idx + 1) % len(spinner_chars)

                    time.sleep(0.1)  # Small delay to prevent busy waiting

            # Get any remaining output
            try:
                remaining_stdout, stderr = self.process.communicate(timeout=5)
                if remaining_stdout:
                    stdout_lines.extend(remaining_stdout.splitlines())
                if stderr:
                    stderr_lines.extend(stderr.splitlines())
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            except ValueError:
                # Ignore "I/O operation on closed file" errors
                stderr = ""

            # Join all output
            stdout = "\n".join(stdout_lines)
            stderr = "\n".join(stderr_lines)

            if show_output:
                total_time = time.time() - start_time
                success(f"\n✅ Claude completed in {total_time:.1f}s")

            return self.process.returncode, stdout, stderr

        except KeyboardInterrupt:
            if show_output:
                warning("\n❌ Operation cancelled by user")
            return -1, "\n".join(stdout_lines), "Cancelled by user"
        except Exception as e:
            if show_output:
                self.error_handler.handle_api_error(e, operation="Claude streaming")
            return -1, "\n".join(stdout_lines), str(e)
        finally:
            # Restore signal handler
            signal.signal(signal.SIGINT, old_handler)
            # Ensure process is cleaned up
            if self.process and self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            self.process = None
