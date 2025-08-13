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
import json
import os
import threading
from pathlib import Path
from typing import Tuple, Optional, IO, Callable, Dict, Any
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

    def run_claude_streaming_json(
        self,
        prompt: str,
        working_dir: str,
        allowed_tools: str = "Agent,Edit,Glob,Grep,LS,MultiEdit,Read,TodoRead,TodoWrite,WebFetch,WebSearch,Write,Task",
        add_dir: Optional[str] = None,
        timeout: int = 600,
        show_progress: bool = True,
        permission_mode: str = "default",
        append_system_prompt: Optional[str] = None,
        mcp_config: Optional[str] = None,
        disallowed_tools: Optional[str] = None,
        cwd: Optional[str] = None,
    ) -> Tuple[int, str, str]:
        """
        Run Claude with stream-json output format and real-time progress display.

        Returns: (returncode, stdout, stderr)
        """
        # Use working directory if provided
        work_dir = cwd or working_dir

        # Build command with stream-json format
        cmd = [
            self.get_binary(),
            "-p",
            "--output-format",
            "stream-json",
            "--allowedTools",
            allowed_tools,
            "--verbose",  # Required for stream-json with -p
        ]

        if add_dir:
            cmd.extend(["--add-dir", add_dir])

        if permission_mode and permission_mode != "default":
            cmd.extend(["--permission-mode", permission_mode])

        if append_system_prompt:
            cmd.extend(["--append-system-prompt", append_system_prompt])

        if mcp_config:
            cmd.extend(["--mcp-config", mcp_config])

        if disallowed_tools:
            cmd.extend(["--disallowedTools", disallowed_tools])

        # Set environment for unbuffered output
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        if show_progress:
            try:
                from .shared.colors import Colors
            except ImportError:
                # Fallback for when running as script
                from tools.shared.colors import Colors

            info(
                f"{Colors.BLUE}🤖 Starting Claude with real-time streaming...{Colors.RESET}"
            )

        # Collect all output
        stdout_lines = []
        stderr_lines = []

        try:
            # Start the process
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=work_dir,
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True,
                env=env,
            )

            # Send the prompt and close stdin
            process.stdin.write(prompt)
            process.stdin.close()

            # Create thread to read stderr
            def read_stderr():
                while True:
                    err_line = process.stderr.readline()
                    if not err_line:
                        break
                    stderr_lines.append(err_line.strip())
                    if show_progress and err_line.strip():
                        warning(f"⚠️  {err_line.strip()}")

            stderr_thread = threading.Thread(target=read_stderr)
            stderr_thread.start()

            # Track timing
            start_time = time.time()

            if show_progress:
                info("🔄 Processing with Claude (streaming output)...")

            # Read stdout line by line and parse JSON in real-time
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break

                if line:
                    line = line.strip()
                    stdout_lines.append(line)

                    # Parse and display progress in real-time
                    if line and show_progress:
                        try:
                            json_obj = json.loads(line)
                            self._display_claude_progress(json_obj, start_time)
                        except json.JSONDecodeError:
                            # Not a JSON line, might be other output
                            if line and not line.startswith("Running command:"):
                                try:
                                    from .shared.colors import Colors
                                except ImportError:
                                    from tools.shared.colors import Colors

                                info(
                                    f"{Colors.DIM}Raw: {line[:100]}{'...' if len(line) > 100 else ''}{Colors.RESET}"
                                )

                # Check timeout
                if time.time() - start_time > timeout:
                    process.kill()
                    if show_progress:
                        warning(f"⏰ Claude timed out after {timeout}s")
                    return -1, "\n".join(stdout_lines), "Process timed out"

            # Wait for process to complete
            process.wait()

            # Wait for stderr thread to finish
            stderr_thread.join()

            # Join all output
            stdout = "\n".join(stdout_lines)
            stderr = "\n".join(stderr_lines)

            if show_progress:
                total_time = time.time() - start_time
                if process.returncode == 0:
                    success(f"✅ Claude processing complete ({total_time:.1f}s)")
                else:
                    error(f"❌ Claude failed with code {process.returncode}")
                    if stderr:
                        try:
                            from .shared.colors import Colors
                        except ImportError:
                            from tools.shared.colors import Colors

                        error(f"{Colors.DIM}Error: {stderr[:200]}...{Colors.RESET}")

            return process.returncode, stdout, stderr

        except Exception as e:
            if show_progress:
                error(f"Error during Claude JSON streaming: {e}")
            return -1, "\n".join(stdout_lines), str(e)

    def _display_claude_progress(self, json_obj: Dict[str, Any], start_time: float):
        """Display friendly progress messages based on Claude's JSON output."""
        try:
            from .shared.colors import Colors
        except ImportError:
            from tools.shared.colors import Colors

        msg_type = json_obj.get("type", "unknown")
        elapsed = time.time() - start_time

        if msg_type == "system" and json_obj.get("subtype") == "init":
            info("🚀 Starting conversation with Claude")
        elif msg_type == "assistant":
            # Handle assistant messages
            message = json_obj.get("message", {})
            if isinstance(message, dict):
                content_parts = message.get("content", [])
                if isinstance(content_parts, list):
                    for part in content_parts:
                        if isinstance(part, dict):
                            if part.get("type") == "text":
                                text = part.get("text", "")
                                # Extract meaningful actions from assistant messages
                                if "Task tool" in text or "Task(" in text:
                                    info(
                                        f"[{elapsed:.0f}s] 🚀 Claude is launching a subagent..."
                                    )
                                elif "Edit tool" in text or "Edit(" in text:
                                    info(
                                        f"[{elapsed:.0f}s] ✏️  Claude is editing files..."
                                    )
                                elif "Read tool" in text or "Read(" in text:
                                    info(
                                        f"[{elapsed:.0f}s] 📖 Claude is reading files..."
                                    )
                                elif (
                                    "Grep tool" in text
                                    or "Grep(" in text
                                    or "search" in text.lower()
                                ):
                                    info(
                                        f"[{elapsed:.0f}s] 🔎 Claude is searching for content..."
                                    )
                                elif "TodoWrite" in text or "todo" in text.lower():
                                    info(
                                        f"[{elapsed:.0f}s] 📝 Claude is managing tasks..."
                                    )
                                elif "Write tool" in text or "Write(" in text:
                                    info(
                                        f"[{elapsed:.0f}s] 💾 Claude is writing files..."
                                    )
                                elif "Glob tool" in text or "Glob(" in text:
                                    info(
                                        f"[{elapsed:.0f}s] 📂 Claude is finding files..."
                                    )
                                elif "LS tool" in text or "LS(" in text:
                                    info(
                                        f"[{elapsed:.0f}s] 📁 Claude is listing directories..."
                                    )
                                elif (
                                    "analyzing" in text.lower()
                                    or "thinking" in text.lower()
                                ):
                                    info(f"[{elapsed:.0f}s] 💭 Claude is analyzing...")
                                elif (
                                    "creating" in text.lower()
                                    or "generating" in text.lower()
                                ):
                                    info(
                                        f"[{elapsed:.0f}s] 🛠️  Claude is creating bundles..."
                                    )
                            elif part.get("type") == "tool_use":
                                # Handle inline tool calls in assistant messages
                                tool_name = part.get("name", "unknown")
                                if tool_name == "Task":
                                    info(
                                        f"[{elapsed:.0f}s] 🚀 Delegating to subagent..."
                                    )
                                elif tool_name == "TodoWrite":
                                    info(f"[{elapsed:.0f}s] 📝 Updating task list...")
                                elif tool_name in ["Edit", "MultiEdit"]:
                                    info(f"[{elapsed:.0f}s] ✏️  Editing files...")
                                elif tool_name == "Write":
                                    info(f"[{elapsed:.0f}s] 💾 Writing new file...")
                                elif tool_name == "Read":
                                    info(f"[{elapsed:.0f}s] 📖 Reading file...")
                                elif tool_name in ["Grep", "Glob", "LS"]:
                                    info(f"[{elapsed:.0f}s] 🔍 Searching project...")
        elif msg_type == "human":
            # Human input
            info(f"[{elapsed:.0f}s] 👤 User input provided")
        elif msg_type == "tool_response":
            # Tool response received
            tool_name = json_obj.get("tool_name", "unknown")
            if tool_name == "Task":
                info(f"[{elapsed:.0f}s] ✅ Subagent completed task")
            else:
                info(f"[{elapsed:.0f}s] ✅ Tool completed: {tool_name}")
