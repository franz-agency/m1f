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

"""Test script for Claude improvements in m1f-html2md."""

import sys
import tempfile
from pathlib import Path

# Add the tools directory to the path
sys.path.insert(0, str(Path(__file__).parent / "tools"))

from html2md_tool.claude_runner import ClaudeRunner

# Use unified colorama module
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))
    from shared.colors import Colors, success, error, warning, info, header, COLORAMA_AVAILABLE
except ImportError:
    # Fallback to no colors
    COLORAMA_AVAILABLE = False
    class Colors:
        GREEN = ""
        RED = ""
        YELLOW = ""
        BLUE = ""
        CYAN = ""
        BOLD = ""
        DIM = ""
        RESET = ""
    
    def success(msg): print(f"✅ {msg}")
    def error(msg): print(f"❌ {msg}", file=sys.stderr)
    def warning(msg): print(f"⚠️  {msg}")
    def info(msg): print(msg)
    def header(title, subtitle=None):
        print(f"\n{title}")
        if subtitle:
            print(subtitle)


def test_streaming_output():
    """Test streaming output with timeout handling."""
    header(f"{Colors.BOLD}Testing streaming output with improved timeout handling...{Colors.RESET}")

    try:
        runner = ClaudeRunner()
        success("Claude runner initialized successfully")
    except FileNotFoundError as e:
        error(str(e))
        return False

    # Test 1: Simple prompt with streaming
    info(f"\n{Colors.BLUE}Test 1: Simple prompt with streaming{Colors.RESET}")
    prompt = "What is 2+2? Just give me the number, nothing else."

    returncode, stdout, stderr = runner.run_claude_streaming(
        prompt=prompt, timeout=30, show_output=True
    )

    if returncode == 0:
        success(f"Test 1 passed. Output: {stdout.strip()}")
    else:
        error(f"Test 1 failed. Error: {stderr}")
        assert False, f"Test failed: {stderr}"


def test_parallel_execution():
    """Test parallel execution of multiple tasks."""
    header(f"{Colors.BOLD}Testing parallel execution...{Colors.RESET}")

    try:
        runner = ClaudeRunner(max_workers=3)
    except FileNotFoundError as e:
        error(str(e))
        return False

    # Create test tasks
    tasks = [
        {
            "name": "Math calculation 1",
            "prompt": "What is 10 + 20? Just give me the number.",
            "timeout": 30,
        },
        {
            "name": "Math calculation 2",
            "prompt": "What is 100 - 50? Just give me the number.",
            "timeout": 30,
        },
        {
            "name": "Math calculation 3",
            "prompt": "What is 5 * 8? Just give me the number.",
            "timeout": 30,
        },
    ]

    info(f"\n{Colors.BLUE}Running {len(tasks)} tasks in parallel...{Colors.RESET}")
    results = runner.run_claude_parallel(tasks, show_progress=True)

    # Check results
    all_success = all(r["success"] for r in results)

    if all_success:
        success("All parallel tasks completed successfully!")
        for result in results:
            info(f"  - {result['name']}: {result['stdout'].strip()}")
    else:
        error("Some tasks failed:")
        for result in results:
            if not result["success"]:
                error(f"  - {result['name']}: {result.get('error') or result.get('stderr')}")
        assert False, "Some parallel tasks failed"


def test_timeout_handling():
    """Test timeout handling with a long-running task."""
    header(f"{Colors.BOLD}Testing timeout handling...{Colors.RESET}")

    try:
        runner = ClaudeRunner()
    except FileNotFoundError as e:
        error(str(e))
        return False

    # This prompt should timeout if Claude takes too long
    prompt = """Please count from 1 to 1000 very slowly, 
    pausing for a second between each number. 
    Show each number on a new line."""

    info(f"\n{Colors.BLUE}Testing with 10-second timeout (should timeout)...{Colors.RESET}")

    returncode, stdout, stderr = runner.run_claude_streaming(
        prompt=prompt, timeout=10, show_output=True  # Very short timeout
    )

    if returncode != 0:
        success("Timeout handling worked correctly")
    else:
        warning("Task completed before timeout")


def main():
    """Run all tests."""
    header(f"{Colors.BOLD}Claude Runner Improvement Tests{Colors.RESET}")
    info("=" * 50)

    tests = [
        ("Streaming Output", test_streaming_output),
        ("Parallel Execution", test_parallel_execution),
        ("Timeout Handling", test_timeout_handling),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        info(f"\n{Colors.YELLOW}Running: {test_name}{Colors.RESET}")
        try:
            if test_func():
                passed += 1
                success(f"{test_name} passed")
            else:
                failed += 1
                error(f"{test_name} failed")
        except Exception as e:
            failed += 1
            error(f"{test_name} failed with exception: {e}")

    info("\n" + "=" * 50)
    header(f"{Colors.BOLD}Test Summary:{Colors.RESET}")
    info(f"{Colors.GREEN}  Passed: {passed}{Colors.RESET}")
    if failed > 0:
        info(f"{Colors.RED}  Failed: {failed}{Colors.RESET}")
    info(f"  Total: {len(tests)}")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
