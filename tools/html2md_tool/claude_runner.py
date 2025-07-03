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
from rich.console import Console

console = Console()


class ClaudeRunner:
    """Handles Claude CLI execution with reliable subprocess support."""

    def __init__(self, max_workers: int = 5, working_dir: Optional[str] = None, claude_binary: Optional[str] = None):
        self.max_workers = max_workers
        self.working_dir = working_dir or str(Path.cwd())
        self.claude_binary = claude_binary or self._find_claude_binary()

    def _find_claude_binary(self) -> str:
        """Find Claude binary in system."""
        # Try default command first
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
            Path.home() / ".claude" / "local" / "claude",
            Path("/usr/local/bin/claude"),
            Path("/usr/bin/claude"),
        ]

        for path in claude_paths:
            if path.exists() and path.is_file():
                return str(path)

        raise FileNotFoundError("Claude binary not found. Please install Claude CLI.")

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
            self.claude_binary,
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
            console.print("🤖 Running Claude...", style="blue")
            console.print(f"Command: {' '.join(cmd[:3])} ...", style="dim")
            console.print(f"Working dir: {self.working_dir}", style="dim")

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
                    console.print("✅ Claude processing complete", style="green")
                else:
                    console.print(f"❌ Claude failed with code {result.returncode}", style="red")
                    if result.stderr:
                        console.print(f"Error: {result.stderr[:200]}...", style="red dim")

            return result.returncode, result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            console.print(f"⏰ Claude timed out after {actual_timeout}s", style="yellow")
            console.print("💡 Try increasing timeout or simplifying the task", style="blue")
            return -1, "", f"Process timed out after {actual_timeout}s"
        except Exception as e:
            console.print(f"❌ Error running Claude: {e}", style="red")
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
        Run Claude with improved subprocess handling.
        
        Returns: (returncode, stdout, stderr)
        """
        # Use the working_dir parameter if provided, otherwise use instance default
        work_dir = working_dir if working_dir is not None else self.working_dir
        
        # Temporarily update the working directory for this call
        original_work_dir = self.working_dir
        self.working_dir = work_dir
        
        try:
            return self.run_claude_simple(
                prompt=prompt,
                allowed_tools=allowed_tools,
                add_dir=add_dir,
                timeout=timeout,
                show_output=show_output,
            )
        finally:
            # Restore original working directory
            self.working_dir = original_work_dir

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

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {}
            for task in tasks:
                future = executor.submit(
                    self.run_claude_streaming,
                    prompt=task["prompt"],
                    allowed_tools=task.get("allowed_tools", "Agent,Edit,Glob,Grep,LS,MultiEdit,Read,TodoRead,TodoWrite,WebFetch,WebSearch,Write"),
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
                    console.print(
                        f"📊 Progress: {completed}/{total} tasks completed",
                        style="blue",
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
                        console.print(f"✅ Completed: {task['name']}", style="green")
                    else:
                        console.print(f"❌ Failed: {task['name']}", style="red")

                except Exception as e:
                    console.print(f"❌ Exception in {task['name']}: {e}", style="red")
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
