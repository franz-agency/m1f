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

"""Manage the HTML2MD test server."""

import subprocess
import sys
import os
import signal
import time
import platform
from pathlib import Path

# Platform-specific PID file location
if platform.system() == "Windows":
    import tempfile
    PID_FILE = Path(tempfile.gettempdir()) / "html2md_test_server.pid"
else:
    PID_FILE = Path("/tmp/html2md_test_server.pid")

# Optional psutil import for better process management
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    psutil = None
    HAS_PSUTIL = False


def start_server():
    """Start the test server."""
    if PID_FILE.exists():
        print("Server already running or PID file exists.")
        print(f"Check PID file: {PID_FILE}")
        return

    server_path = Path(__file__).parent / "server.py"
    
    # Platform-specific process creation
    if platform.system() == "Windows":
        process = subprocess.Popen(
            [sys.executable, str(server_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        process = subprocess.Popen(
            [sys.executable, str(server_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid,  # Create new process group
        )

    # Save PID
    PID_FILE.write_text(str(process.pid))
    print(f"Server started with PID: {process.pid}")
    print("Server running at: http://localhost:8080")


def stop_server():
    """Stop the test server gracefully."""
    if not PID_FILE.exists():
        print("No server PID file found.")
        return

    try:
        pid = int(PID_FILE.read_text())
        
        # Use psutil for better process management if available
        if HAS_PSUTIL:
            try:
                process = psutil.Process(pid)
                
                # Terminate child processes first
                children = process.children(recursive=True)
                for child in children:
                    try:
                        child.terminate()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # Wait for children to terminate
                psutil.wait_procs(children, timeout=3)
                
                # Terminate the main process
                process.terminate()
                print(f"Sent terminate signal to PID {pid}")
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=5)
                    print("Server stopped gracefully.")
                except psutil.TimeoutExpired:
                    print("Server still running, forcing termination...")
                    process.kill()
                    process.wait(timeout=2)
                    print("Server forcefully terminated.")
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                print("Process not found or access denied.")
        else:
            # Fallback to OS signals
            if platform.system() == "Windows":
                # Windows doesn't have SIGTERM, use taskkill
                import subprocess
                try:
                    subprocess.run(["taskkill", "/F", "/PID", str(pid)], 
                                 check=True, capture_output=True)
                    print(f"Terminated process {pid}")
                except subprocess.CalledProcessError as e:
                    print(f"Failed to terminate process: {e}")
            else:
                # Unix-like systems
                try:
                    # Send SIGTERM for graceful shutdown
                    os.kill(pid, signal.SIGTERM)
                    print(f"Sent SIGTERM to PID {pid}")

                    # Wait a bit
                    time.sleep(1)

                    # Check if still running
                    try:
                        os.kill(pid, 0)  # Check if process exists
                        print("Server still running, sending SIGKILL...")
                        os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        print("Server stopped gracefully.")
                except ProcessLookupError:
                    print("Process not found.")

        # Clean up PID file
        PID_FILE.unlink()

    except (ValueError, ProcessLookupError) as e:
        print(f"Error stopping server: {e}")
        if PID_FILE.exists():
            PID_FILE.unlink()


def status_server():
    """Check server status."""
    if not PID_FILE.exists():
        print("Server not running (no PID file)")
        return

    try:
        pid = int(PID_FILE.read_text())
        
        # Use psutil for better process information if available
        if HAS_PSUTIL:
            try:
                process = psutil.Process(pid)
                if process.is_running() and process.name() in ['python', 'python.exe']:
                    print(f"Server running with PID: {pid}")
                    print(f"Process name: {process.name()}")
                    print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB")
                    print(f"CPU percent: {process.cpu_percent():.1f}%")
                else:
                    print("Server not running (stale PID file)")
                    PID_FILE.unlink()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                print("Server not running (stale PID file)")
                PID_FILE.unlink()
        else:
            # Fallback to basic process check
            if platform.system() == "Windows":
                import subprocess
                try:
                    result = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], 
                                          capture_output=True, text=True)
                    if str(pid) in result.stdout:
                        print(f"Server running with PID: {pid}")
                    else:
                        print("Server not running (stale PID file)")
                        PID_FILE.unlink()
                except subprocess.CalledProcessError:
                    print("Server not running (stale PID file)")
                    PID_FILE.unlink()
            else:
                try:
                    os.kill(pid, 0)  # Check if process exists
                    print(f"Server running with PID: {pid}")
                except ProcessLookupError:
                    print("Server not running (stale PID file)")
                    PID_FILE.unlink()
                    
    except ValueError:
        print("Invalid PID file")
        PID_FILE.unlink()


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["start", "stop", "status"]:
        print("Usage: python manage_server.py [start|stop|status]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "start":
        start_server()
    elif command == "stop":
        stop_server()
    elif command == "status":
        status_server()
