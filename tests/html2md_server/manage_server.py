#!/usr/bin/env python3
"""Manage the HTML2MD test server."""

import subprocess
import sys
import os
import signal
import time
from pathlib import Path

PID_FILE = Path("/tmp/html2md_test_server.pid")


def start_server():
    """Start the test server."""
    if PID_FILE.exists():
        print("Server already running or PID file exists.")
        print(f"Check PID file: {PID_FILE}")
        return
    
    server_path = Path(__file__).parent / "server.py"
    process = subprocess.Popen(
        [sys.executable, str(server_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        preexec_fn=os.setsid  # Create new process group
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
        os.kill(pid, 0)  # Check if process exists
        print(f"Server running with PID: {pid}")
    except (ValueError, ProcessLookupError):
        print("Server not running (stale PID file)")
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