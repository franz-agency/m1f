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

# Add colorama imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from tools.shared.colors import info, error, warning, success

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
        warning("Server already running or PID file exists.")
        warning(f"Check PID file: {PID_FILE}")
        return

    server_path = Path(__file__).parent / "server.py"

    # Platform-specific process creation
    if platform.system() == "Windows":
        process = subprocess.Popen(
            [sys.executable, str(server_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
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
    success(f"Server started with PID: {process.pid}")
    port = os.environ.get("HTML2MD_SERVER_PORT", "8090")
    info(f"Server running at: http://localhost:{port}")


def stop_server():
    """Stop the test server gracefully."""
    if not PID_FILE.exists():
        warning("No server PID file found.")
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
                info(f"Sent terminate signal to PID {pid}")

                # Wait for graceful shutdown
                try:
                    process.wait(timeout=5)
                    success("Server stopped gracefully.")
                except psutil.TimeoutExpired:
                    warning("Server still running, forcing termination...")
                    process.kill()
                    process.wait(timeout=2)
                    warning("Server forcefully terminated.")

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                error("Process not found or access denied.")
        else:
            # Fallback to OS signals
            if platform.system() == "Windows":
                # Windows doesn't have SIGTERM, use taskkill
                import subprocess

                try:
                    subprocess.run(
                        ["taskkill", "/F", "/PID", str(pid)],
                        check=True,
                        capture_output=True,
                    )
                    success(f"Terminated process {pid}")
                except subprocess.CalledProcessError as e:
                    error(f"Failed to terminate process: {e}")
            else:
                # Unix-like systems
                try:
                    # Send SIGTERM for graceful shutdown
                    os.kill(pid, signal.SIGTERM)
                    info(f"Sent SIGTERM to PID {pid}")

                    # Wait a bit
                    time.sleep(1)

                    # Check if still running
                    try:
                        os.kill(pid, 0)  # Check if process exists
                        warning("Server still running, sending SIGKILL...")
                        os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        success("Server stopped gracefully.")
                except ProcessLookupError:
                    error("Process not found.")

        # Clean up PID file
        PID_FILE.unlink()

    except (ValueError, ProcessLookupError) as e:
        error(f"Error stopping server: {e}")
        if PID_FILE.exists():
            PID_FILE.unlink()


def status_server():
    """Check server status."""
    if not PID_FILE.exists():
        info("Server not running (no PID file)")
        return

    try:
        pid = int(PID_FILE.read_text())

        # Use psutil for better process information if available
        if HAS_PSUTIL:
            try:
                process = psutil.Process(pid)
                if process.is_running() and process.name() in [
                    sys.executable,
                    "python.exe",
                ]:
                    success(f"Server running with PID: {pid}")
                    info(f"Process name: {process.name()}")
                    info(
                        f"Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB"
                    )
                    info(f"CPU percent: {process.cpu_percent():.1f}%")
                else:
                    warning("Server not running (stale PID file)")
                    PID_FILE.unlink()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                warning("Server not running (stale PID file)")
                PID_FILE.unlink()
        else:
            # Fallback to basic process check
            if platform.system() == "Windows":
                import subprocess

                try:
                    result = subprocess.run(
                        ["tasklist", "/FI", f"PID eq {pid}"],
                        capture_output=True,
                        text=True,
                    )
                    if str(pid) in result.stdout:
                        success(f"Server running with PID: {pid}")
                    else:
                        warning("Server not running (stale PID file)")
                        PID_FILE.unlink()
                except subprocess.CalledProcessError:
                    warning("Server not running (stale PID file)")
                    PID_FILE.unlink()
            else:
                try:
                    os.kill(pid, 0)  # Check if process exists
                    success(f"Server running with PID: {pid}")
                except ProcessLookupError:
                    warning("Server not running (stale PID file)")
                    PID_FILE.unlink()

    except ValueError:
        error("Invalid PID file")
        PID_FILE.unlink()


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["start", "stop", "status"]:
        error("Usage: python manage_server.py [start|stop|status]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "start":
        start_server()
    elif command == "stop":
        stop_server()
    elif command == "status":
        status_server()
