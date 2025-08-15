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
Claude runner with reliable subprocess execution and streaming support.
"""

import subprocess
import sys
import os
import json
import threading
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Import safe file operations
from m1f.file_operations import safe_exists, safe_is_file

# Use unified colorama module
from shared.colors import (
    Colors,
    success,
    error,
    warning,
    info,
    header,
    COLORAMA_AVAILABLE,
)

# Import shared Claude utilities
from shared.claude_utils import (
    ClaudeBinaryFinder,
    ClaudeErrorHandler,
    ClaudeConfig,
    ClaudeRunner as BaseClaudeRunner,
)


class ClaudeRunner(BaseClaudeRunner):
    """Handles Claude CLI execution with reliable subprocess support."""

    def __init__(
        self,
        max_workers: int = 5,
        working_dir: Optional[str] = None,
        claude_binary: Optional[str] = None,
        config: Optional[ClaudeConfig] = None,
    ):
        super().__init__(config=config, binary_path=claude_binary)
        self.max_workers = max_workers
        self.working_dir = working_dir or str(Path.cwd())

    def run_claude_simple(
        self,
        prompt: str,
        allowed_tools: str = "Agent,Edit,Glob,Grep,LS,MultiEdit,Read,TodoRead,TodoWrite,WebFetch,WebSearch,Write",
        add_dir: Optional[str] = None,
        timeout: int = 300,
        show_output: bool = False,
    ) -> Tuple[int, str, str]:
        """
        Run Claude using simple subprocess approach with better timeout handling.

        Returns: (returncode, stdout, stderr)
        """
        cmd = [
            self.get_binary(),
            "--print",  # Use print mode for non-interactive output
            "--allowedTools",
            allowed_tools,
        ]

        # Add working directory to command if different from current
        if add_dir:
            cmd.extend(["--add-dir", add_dir])

        # Set environment to ensure unbuffered output
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        if show_output:
            info(f"{Colors.BLUE}🤖 Running Claude...{Colors.RESET}")
            info(f"{Colors.DIM}Command: {' '.join(cmd[:3])} ...{Colors.RESET}")
            info(f"{Colors.DIM}Working dir: {self.working_dir}{Colors.RESET}")

        try:
            # Use a more conservative timeout for complex tasks
            actual_timeout = max(60, timeout)  # At least 60 seconds

            # Run the process with timeout
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=actual_timeout,
                env=env,
                cwd=self.working_dir,
            )

            if show_output:
                if result.returncode == 0:
                    success("Claude processing complete")
                else:
                    error(f"Claude failed with code {result.returncode}")
                    if result.stderr:
                        error(
                            f"{Colors.DIM}Error: {result.stderr[:200]}...{Colors.RESET}"
                        )

            return result.returncode, result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            warning(f"⏰ Claude timed out after {actual_timeout}s")
            info(
                f"{Colors.BLUE}💡 Try increasing timeout or simplifying the task{Colors.RESET}"
            )
            return -1, "", f"Process timed out after {actual_timeout}s"
        except Exception as e:
            self.error_handler.handle_api_error(e, operation="Claude simple")
            return -1, "", str(e)

    def run_claude_streaming(
        self,
        prompt: str,
        allowed_tools: str = "Agent,Edit,Glob,Grep,LS,MultiEdit,Read,TodoRead,TodoWrite,WebFetch,WebSearch,Write",
        add_dir: Optional[str] = None,
        timeout: int = 300,
        show_output: bool = False,
        working_dir: Optional[str] = None,
    ) -> Tuple[int, str, str]:
        """
        Run Claude with real-time streaming output.

        Returns: (returncode, stdout, stderr)
        """
        # Use the working_dir parameter if provided, otherwise use instance default
        work_dir = working_dir if working_dir is not None else self.working_dir

        # Build command
        cmd = [self.get_binary(), "-p", "--allowedTools", allowed_tools]

        if add_dir:
            cmd.extend(["--add-dir", add_dir])

        # Only show initial message if show_output is enabled
        # Removed verbose output for cleaner interface

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
                bufsize=1,
                universal_newlines=True,
            )

            # Send the prompt and close stdin
            process.stdin.write(prompt)
            process.stdin.close()

            # Track timing
            start_time = time.time()
            last_output_time = start_time

            # Read stdout line by line
            while True:
                line = process.stdout.readline()
                if line == "" and process.poll() is not None:
                    break
                if line:
                    line = line.rstrip()
                    stdout_lines.append(line)

                    if show_output:
                        current_time = time.time()
                        elapsed = current_time - start_time
                        # Show Claude's actual output (no truncation, terminal will soft wrap)
                        info(f"[{elapsed:.1f}s] {line}")
                        last_output_time = current_time

                # Check timeout
                if time.time() - start_time > timeout:
                    process.kill()
                    if show_output:
                        warning(f"⏰ Claude timed out after {timeout}s")
                    return -1, "\n".join(stdout_lines), "Process timed out"

            # Get any remaining output
            try:
                remaining_stdout, stderr = process.communicate(timeout=5)
                if remaining_stdout:
                    stdout_lines.extend(remaining_stdout.splitlines())
                if stderr:
                    stderr_lines.extend(stderr.splitlines())
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            except ValueError:
                # Ignore "I/O operation on closed file" errors
                stderr = ""

            # Join all output
            stdout = "\n".join(stdout_lines)
            stderr = "\n".join(stderr_lines)

            if show_output:
                total_time = time.time() - start_time
                if process.returncode == 0:
                    success("Claude processing complete")
                else:
                    error(f"Claude failed with code {process.returncode}")
                    if stderr:
                        error(f"{Colors.DIM}Error: {stderr[:200]}...{Colors.RESET}")

            return process.returncode, stdout, stderr

        except Exception as e:
            if show_output:
                self.error_handler.handle_api_error(e, operation="Claude streaming")
            return -1, "\n".join(stdout_lines), str(e)

    def run_claude_streaming_json(
        self,
        prompt: str,
        allowed_tools: str = "Agent,Edit,Glob,Grep,LS,MultiEdit,Read,TodoRead,TodoWrite,WebFetch,WebSearch,Write,Task",
        add_dir: Optional[str] = None,
        timeout: int = 600,
        working_dir: Optional[str] = None,
        show_progress: bool = True,
    ) -> Tuple[int, str, str]:
        """
        Run Claude with stream-json output format and real-time progress display.

        Returns: (returncode, stdout, stderr)
        """
        # Use working directory if provided
        work_dir = working_dir or self.working_dir

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

        # Set environment for unbuffered output
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        if show_progress:
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
                        error(f"{Colors.DIM}Error: {stderr[:200]}...{Colors.RESET}")

            return process.returncode, stdout, stderr

        except Exception as e:
            if show_progress:
                self.error_handler.handle_api_error(
                    e, operation="Claude JSON streaming"
                )
            return -1, "\n".join(stdout_lines), str(e)

    def _display_claude_progress(self, json_obj: Dict[str, Any], start_time: float):
        """Display friendly progress messages based on Claude's JSON output."""
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
                                        f"[{elapsed:.0f}s] 🔍 Claude is launching a subagent..."
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
                                elif "TodoWrite" in text:
                                    info(
                                        f"[{elapsed:.0f}s] 📝 Claude is managing tasks..."
                                    )
                                elif "Write tool" in text or "Write(" in text:
                                    info(
                                        f"[{elapsed:.0f}s] 💾 Claude is writing files..."
                                    )
                                elif len(text) > 50:  # Significant text output
                                    info(f"[{elapsed:.0f}s] 💭 Claude is analyzing...")
                            elif part.get("type") == "tool_use":
                                # Handle inline tool calls in assistant messages
                                tool_name = part.get("name", "unknown")
                                tool_input = part.get("input", {})

                                if tool_name == "Edit":
                                    file_path = tool_input.get("file_path", "")
                                    file_name = (
                                        os.path.basename(file_path)
                                        if file_path
                                        else "file"
                                    )
                                    info(f"[{elapsed:.0f}s] ✏️  Editing: {file_name}")
                                elif tool_name == "MultiEdit":
                                    file_path = tool_input.get("file_path", "")
                                    edits_count = len(tool_input.get("edits", []))
                                    file_name = (
                                        os.path.basename(file_path)
                                        if file_path
                                        else "file"
                                    )
                                    info(
                                        f"[{elapsed:.0f}s] ✏️  Making {edits_count} edits to: {file_name}"
                                    )
                                elif tool_name == "Read":
                                    file_path = tool_input.get("file_path", "")
                                    file_name = (
                                        os.path.basename(file_path)
                                        if file_path
                                        else "file"
                                    )
                                    info(f"[{elapsed:.0f}s] 📖 Reading: {file_name}")
                                elif tool_name == "Task":
                                    desc = tool_input.get("description", "")
                                    agent_type = tool_input.get(
                                        "subagent_type", "general"
                                    )
                                    info(
                                        f"[{elapsed:.0f}s] 🤖 Launching {agent_type} subagent: {desc[:50]}{'...' if len(desc) > 50 else ''}"
                                    )
                                elif tool_name == "Grep":
                                    pattern = tool_input.get("pattern", "")
                                    path = tool_input.get("path", ".")
                                    info(
                                        f"[{elapsed:.0f}s] 🔎 Searching for '{pattern[:30]}{'...' if len(pattern) > 30 else ''}' in {os.path.basename(path)}"
                                    )
                                elif tool_name == "TodoWrite":
                                    todos = tool_input.get("todos", [])
                                    info(
                                        f"[{elapsed:.0f}s] 📝 Managing {len(todos)} tasks"
                                    )
                                elif tool_name == "Write":
                                    file_path = tool_input.get("file_path", "")
                                    file_name = (
                                        os.path.basename(file_path)
                                        if file_path
                                        else "file"
                                    )
                                    info(f"[{elapsed:.0f}s] 💾 Writing: {file_name}")
                                elif tool_name == "Glob":
                                    pattern = tool_input.get("pattern", "")
                                    info(
                                        f"[{elapsed:.0f}s] 📁 Finding files: {pattern}"
                                    )
                                elif tool_name == "LS":
                                    path = tool_input.get("path", "")
                                    info(
                                        f"[{elapsed:.0f}s] 📂 Listing: {os.path.basename(path) if path else 'directory'}"
                                    )
                                else:
                                    info(f"[{elapsed:.0f}s] 🔧 Using tool: {tool_name}")
        elif msg_type == "result":
            if json_obj.get("subtype") == "success":
                success(f"[{elapsed:.0f}s] ✅ Task completed successfully")
            else:
                warning(f"[{elapsed:.0f}s] ❌ Task failed")
        elif msg_type == "user":
            # Skip displaying user messages (the prompt) unless it's a tool result
            parent_id = json_obj.get("parent_tool_use_id")
            if parent_id:
                info(f"[{elapsed:.0f}s]   ↳ Tool result received")

    def run_claude_parallel(
        self, tasks: List[Dict[str, Any]], show_progress: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Run multiple Claude tasks in parallel using SDK.

        Args:
            tasks: List of task dictionaries with keys:
                - prompt: The prompt to send
                - name: Task name for display
                - allowed_tools: Tools to allow (optional)
                - add_dir: Directory to add (optional)
                - timeout: Timeout in seconds (optional)

        Returns:
            List of results with keys:
                - name: Task name
                - success: Boolean
                - returncode: Process return code
                - stdout: Standard output
                - stderr: Standard error
                - error: Error message if failed
        """
        results = []
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {}
            for task in tasks:
                future = executor.submit(
                    self.run_claude_streaming,
                    prompt=task["prompt"],
                    allowed_tools=task.get(
                        "allowed_tools",
                        "Agent,Edit,Glob,Grep,LS,MultiEdit,Read,TodoRead,TodoWrite,WebFetch,WebSearch,Write",
                    ),
                    add_dir=task.get("add_dir"),
                    timeout=task.get("timeout", 300),
                    show_output=show_progress,  # Show output if progress enabled
                    working_dir=task.get("working_dir"),
                )
                future_to_task[future] = task

            # Process completed tasks
            completed = 0
            total = len(tasks)

            for future in as_completed(future_to_task):
                task = future_to_task[future]
                completed += 1

                if show_progress:
                    elapsed_time = (
                        time.time() - start_time if "start_time" in locals() else 0
                    )
                    info(
                        f"{Colors.BLUE}📊 Progress: {completed}/{total} tasks completed [{elapsed_time:.0f}s elapsed]{Colors.RESET}"
                    )

                try:
                    returncode, stdout, stderr = future.result()

                    result = {
                        "name": task["name"],
                        "success": returncode == 0,
                        "returncode": returncode,
                        "stdout": stdout,
                        "stderr": stderr,
                        "error": None,
                    }

                    if returncode == 0:
                        success(f"Completed: {task['name']}")
                    else:
                        error(f"Failed: {task['name']}")

                except Exception as e:
                    error(f"Exception in {task['name']}: {e}")
                    result = {
                        "name": task["name"],
                        "success": False,
                        "returncode": -1,
                        "stdout": "",
                        "stderr": "",
                        "error": str(e),
                    }

                results.append(result)

        return results
