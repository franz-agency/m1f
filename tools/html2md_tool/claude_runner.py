"""
Claude runner with improved timeout handling and parallel processing support.
"""
import asyncio
import subprocess
import sys
import os
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import queue
import time
import signal
from rich.console import Console

console = Console()


class ClaudeRunner:
    """Handles Claude CLI execution with improved timeout and streaming support."""
    
    def __init__(self, claude_binary: Optional[str] = None, max_workers: int = 5):
        self.claude_binary = claude_binary or self._find_claude_binary()
        self.max_workers = max_workers
        
    def _find_claude_binary(self) -> str:
        """Find Claude binary in system."""
        # Try default command first
        try:
            subprocess.run(["claude", "--version"], capture_output=True, check=True, timeout=5)
            return "claude"
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
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
    
    def _stream_output(self, process: subprocess.Popen, output_queue: queue.Queue, stream_name: str):
        """Stream output from a subprocess in real-time."""
        stream = getattr(process, stream_name)
        for line in iter(stream.readline, ''):
            if line:
                output_queue.put((stream_name, line))
        stream.close()
    
    def run_claude_streaming(
        self, 
        prompt: str, 
        allowed_tools: str = "Read,Glob,Grep,Write",
        add_dir: Optional[str] = None,
        timeout: int = 300,
        show_output: bool = False
    ) -> Tuple[int, str, str]:
        """
        Run Claude with streaming output and improved timeout handling.
        
        Returns: (returncode, stdout, stderr)
        """
        cmd = [
            self.claude_binary,
            "--print",  # Use print mode for non-interactive output
            "--allowedTools", allowed_tools,
        ]
        
        if add_dir:
            cmd.extend(["--add-dir", add_dir])
        
        # Set environment to ensure unbuffered output
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        
        stdout_lines = []
        stderr_lines = []
        output_queue = queue.Queue()
        
        try:
            # Start the process
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                env=env
            )
            
            # Create threads to read stdout and stderr
            stdout_thread = threading.Thread(
                target=self._stream_output,
                args=(process, output_queue, 'stdout')
            )
            stderr_thread = threading.Thread(
                target=self._stream_output,
                args=(process, output_queue, 'stderr')
            )
            
            stdout_thread.daemon = True
            stderr_thread.daemon = True
            stdout_thread.start()
            stderr_thread.start()
            
            # Send input and close stdin
            process.stdin.write(prompt)
            process.stdin.close()
            
            # Monitor output with timeout
            start_time = time.time()
            last_output_time = start_time
            
            while True:
                elapsed = time.time() - start_time
                time_since_last_output = time.time() - last_output_time
                
                # Check if process has completed
                if process.poll() is not None:
                    # Give threads a moment to finish reading
                    stdout_thread.join(timeout=1)
                    stderr_thread.join(timeout=1)
                    break
                
                # Check for absolute timeout
                if elapsed > timeout:
                    console.print(f"⏰ Absolute timeout reached ({timeout}s)", style="yellow")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    break
                
                # Check for completion signals in output
                output_so_far = ''.join(stdout_lines)
                if any(signal in output_so_far for signal in [
                    "ANALYSIS_COMPLETE_OK",
                    "FILE_SELECTION_COMPLETE_OK", 
                    "SYNTHESIS_COMPLETE_OK"
                ]):
                    console.print("✅ Completion signal detected", style="green dim")
                    # Give process a moment to finish cleanly
                    time.sleep(1)
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    break
                
                # Check for output timeout (no output for 60 seconds)
                if time_since_last_output > 60:
                    console.print("⏰ No output for 60 seconds, assuming completion", style="yellow")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    break
                
                # Read from queue with timeout
                try:
                    stream_name, line = output_queue.get(timeout=0.1)
                    last_output_time = time.time()
                    
                    if stream_name == 'stdout':
                        stdout_lines.append(line)
                        if show_output:
                            console.print(f"📝 {line.rstrip()}", style="dim")
                    else:
                        stderr_lines.append(line)
                        if show_output:
                            console.print(f"⚠️  {line.rstrip()}", style="yellow dim")
                            
                except queue.Empty:
                    continue
            
            # Drain any remaining output
            while not output_queue.empty():
                try:
                    stream_name, line = output_queue.get_nowait()
                    if stream_name == 'stdout':
                        stdout_lines.append(line)
                    else:
                        stderr_lines.append(line)
                except queue.Empty:
                    break
            
            returncode = process.returncode
            stdout = ''.join(stdout_lines)
            stderr = ''.join(stderr_lines)
            
            return returncode, stdout, stderr
            
        except Exception as e:
            console.print(f"❌ Error running Claude: {e}", style="red")
            return -1, "", str(e)
    
    def run_claude_parallel(
        self,
        tasks: List[Dict[str, Any]],
        show_progress: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Run multiple Claude tasks in parallel.
        
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
                    prompt=task['prompt'],
                    allowed_tools=task.get('allowed_tools', 'Read,Glob,Grep,Write'),
                    add_dir=task.get('add_dir'),
                    timeout=task.get('timeout', 300),
                    show_output=False  # Don't show output in parallel mode
                )
                future_to_task[future] = task
            
            # Process completed tasks
            completed = 0
            total = len(tasks)
            
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                completed += 1
                
                if show_progress:
                    console.print(f"📊 Progress: {completed}/{total} tasks completed", style="blue")
                
                try:
                    returncode, stdout, stderr = future.result()
                    
                    result = {
                        'name': task['name'],
                        'success': returncode == 0,
                        'returncode': returncode,
                        'stdout': stdout,
                        'stderr': stderr,
                        'error': None
                    }
                    
                    if returncode == 0:
                        console.print(f"✅ Completed: {task['name']}", style="green")
                    else:
                        console.print(f"❌ Failed: {task['name']}", style="red")
                        
                except Exception as e:
                    console.print(f"❌ Exception in {task['name']}: {e}", style="red")
                    result = {
                        'name': task['name'],
                        'success': False,
                        'returncode': -1,
                        'stdout': '',
                        'stderr': '',
                        'error': str(e)
                    }
                
                results.append(result)
        
        return results
    
    async def run_claude_async(
        self,
        prompt: str,
        allowed_tools: str = "Read,Glob,Grep,Write",
        add_dir: Optional[str] = None,
        timeout: int = 300
    ) -> Tuple[int, str, str]:
        """
        Async version using asyncio for better integration.
        """
        cmd = [
            self.claude_binary,
            "--print",
            "--allowedTools", allowed_tools,
        ]
        
        if add_dir:
            cmd.extend(["--add-dir", add_dir])
        
        # Create subprocess
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            # Send input and get output with timeout
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(prompt.encode()),
                timeout=timeout
            )
            
            return proc.returncode, stdout.decode(), stderr.decode()
            
        except asyncio.TimeoutError:
            console.print(f"⏰ Async timeout reached ({timeout}s)", style="yellow")
            proc.kill()
            await proc.wait()
            return -1, "", "Process timed out"