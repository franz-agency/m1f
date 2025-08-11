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
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Import safe file operations
from ..m1f.file_operations import safe_exists, safe_is_file

# Use unified colorama module
from ..shared.colors import (
    Colors,
    success,
    error,
    warning,
    info,
    header,
    COLORAMA_AVAILABLE,
)

# Import shared Claude utilities
from ..shared.claude_utils import (
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
