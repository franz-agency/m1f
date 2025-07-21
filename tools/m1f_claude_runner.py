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
from typing import Tuple, Optional, IO
import signal


class M1FClaudeRunner:
    """Handles Claude CLI execution with streaming output and robust timeout handling."""

    def __init__(self, claude_binary: Optional[str] = None):
        self.claude_binary = claude_binary or self._find_claude_binary()
        self.process = None

    def _find_claude_binary(self) -> str:
        """Find Claude binary in system."""
        # Check default command first
        try:
            subprocess.run(
                ["claude", "--version"], capture_output=True, check=True, timeout=5
            )
            return "claude"
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ):
            pass

        # Check known locations
        claude_paths = [
            Path.home() / ".claude" / "local" / "node_modules" / ".bin" / "claude",
            Path("/usr/local/bin/claude"),
            Path("/usr/bin/claude"),
            Path.home() / ".npm-global" / "bin" / "claude",
        ]

        # Add npm global bin if available
        try:
            npm_prefix = subprocess.run(
                ["npm", "config", "get", "prefix"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if npm_prefix.returncode == 0:
                npm_bin = Path(npm_prefix.stdout.strip()) / "bin" / "claude"
                claude_paths.append(npm_bin)
        except:
            pass

        for path in claude_paths:
            if path.exists() and path.is_file():
                return str(path)

        raise FileNotFoundError("Claude binary not found. Please install Claude CLI.")

    def run_claude_streaming(
        self,
        prompt: str,
        working_dir: str,
        allowed_tools: str = "Read,Write,Edit,MultiEdit,Glob,Grep",
        add_dir: Optional[str] = None,
        timeout: int = 600,  # 10 minutes default
        show_output: bool = True,
        output_handler: Optional[callable] = None,
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
            self.claude_binary,
            "--print",  # Use print mode for non-interactive output
            "--allowedTools",
            allowed_tools,
        ]

        if add_dir:
            cmd.extend(["--add-dir", add_dir])

        # Use conservative timeout (at least 60 seconds)
        actual_timeout = max(60, timeout)

        # Collect all output
        stdout_lines = []
        stderr_lines = []

        # Signal handler for graceful interruption
        def handle_interrupt(signum, frame):
            if self.process:
                print("\n🛑 Interrupting Claude... Press Ctrl-C again to force quit.")
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
                        # Show progress with elapsed time
                        if len(line) > 150:
                            print(f"[{elapsed:5.1f}s] {line[:147]}...")
                        else:
                            print(f"[{elapsed:5.1f}s] {line}")

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
                            print(f"\n⏰ Claude timed out after {actual_timeout}s")
                        self.process.kill()
                        return (
                            -1,
                            "\n".join(stdout_lines),
                            f"Process timed out after {actual_timeout}s",
                        )

                    # Check inactivity timeout (60 seconds)
                    if current_time - last_output_time > 60:
                        if show_output:
                            print(
                                f"\n⏰ Claude inactive for 60s (total time: {elapsed:.1f}s)"
                            )
                        self.process.kill()
                        return (
                            -1,
                            "\n".join(stdout_lines),
                            "Process inactive for 60 seconds",
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
                print(f"\n✅ Claude completed in {total_time:.1f}s")

            return self.process.returncode, stdout, stderr

        except KeyboardInterrupt:
            if show_output:
                print("\n❌ Operation cancelled by user")
            return -1, "\n".join(stdout_lines), "Cancelled by user"
        except Exception as e:
            if show_output:
                print(f"\n❌ Error running Claude: {e}")
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
