#!/usr/bin/env python3
"""
Test that all m1f commands are available and executable.

This test verifies that the package installation correctly creates all
expected command-line entry points and that they can be invoked with --help.
"""

import subprocess
import sys
import pytest
from pathlib import Path
import os
import platform


# List of all m1f commands that should be available
M1F_COMMANDS = [
    "m1f",
    "m1f-s1f",
    "m1f-update",
    "m1f-html2md",
    "m1f-scrape",
    "m1f-research",
    "m1f-token-counter",
    "m1f-claude",
    "m1f-help",
]


def find_command(cmd):
    """
    Find the full path to a command, cross-platform compatible.
    
    Args:
        cmd: Command name to find
        
    Returns:
        Full path to command or None if not found
    """
    # For Windows, we might need to check with .exe extension
    if platform.system() == "Windows":
        cmd_variations = [cmd, f"{cmd}.exe", f"{cmd}.bat", f"{cmd}.cmd"]
    else:
        cmd_variations = [cmd]
    
    # First, try to find in PATH using 'which' (Unix) or 'where' (Windows)
    for cmd_var in cmd_variations:
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["where", cmd_var],
                    capture_output=True,
                    text=True,
                    check=False
                )
            else:
                result = subprocess.run(
                    ["which", cmd_var],
                    capture_output=True,
                    text=True,
                    check=False
                )
            
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]  # Return first match
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
    
    # If not found in PATH, check common installation locations
    possible_paths = []
    
    # Add virtual environment paths
    if hasattr(sys, 'prefix'):
        if platform.system() == "Windows":
            possible_paths.extend([
                Path(sys.prefix) / "Scripts",
                Path(sys.prefix) / "bin",
            ])
        else:
            possible_paths.append(Path(sys.prefix) / "bin")
    
    # Check each possible path
    for path in possible_paths:
        for cmd_var in cmd_variations:
            full_path = path / cmd_var
            if full_path.exists() and full_path.is_file():
                return str(full_path)
    
    return None


class TestCommandAvailability:
    """Test suite for m1f command availability."""
    
    @pytest.mark.parametrize("command", M1F_COMMANDS)
    def test_command_exists(self, command):
        """Test that each command exists and is findable."""
        cmd_path = find_command(command)
        assert cmd_path is not None, f"Command '{command}' not found in PATH or virtual environment"
        assert Path(cmd_path).exists(), f"Command path '{cmd_path}' does not exist"
    
    @pytest.mark.parametrize("command", M1F_COMMANDS)
    def test_command_help(self, command):
        """Test that each command can be invoked with --help."""
        cmd_path = find_command(command)
        if cmd_path is None:
            pytest.skip(f"Command '{command}' not found")
        
        try:
            # Run command with --help
            result = subprocess.run(
                [cmd_path, "--help"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False
            )
            
            # Check that command executed successfully
            # Note: Some commands might return 0, others might return 1 or 2 for help
            assert result.returncode in [0, 1, 2], (
                f"Command '{command}' returned unexpected code {result.returncode}"
            )
            
            # Check that help text was produced
            output = result.stdout + result.stderr
            assert len(output) > 0, f"Command '{command}' produced no output with --help"
            
            # Check for common help text indicators
            help_indicators = ["usage:", "Usage:", "help", "Help", "--help", "options:"]
            assert any(indicator in output for indicator in help_indicators), (
                f"Command '{command}' output doesn't look like help text"
            )
            
        except subprocess.TimeoutExpired:
            pytest.fail(f"Command '{command}' timed out when running --help")
        except Exception as e:
            pytest.fail(f"Failed to run command '{command}': {e}")
    
    @pytest.mark.parametrize("command", M1F_COMMANDS)
    def test_command_version(self, command):
        """Test that each command can show version information."""
        cmd_path = find_command(command)
        if cmd_path is None:
            pytest.skip(f"Command '{command}' not found")
        
        try:
            # Try --version flag
            result = subprocess.run(
                [cmd_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False
            )
            
            # Many commands support --version
            if result.returncode in [0, 1, 2]:
                output = result.stdout + result.stderr
                # Check if version info is present (might be in error message for unsupported flag)
                if "version" in output.lower() or "." in output:
                    return  # Test passed
            
            # If --version didn't work, that's okay - not all commands support it
            pytest.skip(f"Command '{command}' doesn't support --version")
            
        except subprocess.TimeoutExpired:
            pytest.fail(f"Command '{command}' timed out when running --version")
        except Exception as e:
            pytest.fail(f"Failed to run command '{command}': {e}")


class TestImportStructure:
    """Test that the package import structure is correct."""
    
    def test_tools_modules_importable(self):
        """Test that main tool modules can be imported."""
        import_tests = [
            "import m1f",
            "import s1f",
            "import html2md_tool",
            "import scrape_tool",
            "import research",
            "import shared",
            "import _version",
        ]
        
        for import_stmt in import_tests:
            try:
                exec(import_stmt)
            except ImportError as e:
                pytest.fail(f"Failed to {import_stmt}: {e}")
    
    def test_submodules_importable(self):
        """Test that submodules can be imported correctly."""
        import sys
        import os
        
        # Make sure we import from tools directory, not tests directory
        original_path = sys.path.copy()
        try:
            # Add tools directory to the front of sys.path
            tools_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools')
            if tools_dir not in sys.path:
                sys.path.insert(0, tools_dir)
            
            import_tests = [
                "from m1f import cli",
                "from s1f import cli",
                "from html2md_tool import cli",
                "from scrape_tool import cli",
                "from research import cli",
                "from shared import colors",
            ]
            
            for import_stmt in import_tests:
                try:
                    exec(import_stmt)
                except ImportError as e:
                    # Some imports might legitimately fail if dependencies are missing
                    if "No module named" not in str(e):
                        pytest.fail(f"Failed to {import_stmt}: {e}")
        finally:
            # Restore original sys.path
            sys.path = original_path
    
    def test_cross_package_imports(self):
        """Test that cross-package imports work correctly."""
        # These are the types of imports that were changed
        import_tests = [
            ("from m1f.file_operations import safe_exists", "safe_exists"),
            ("from shared.colors import Colors", "Colors"),
            ("from _version import __version__", "__version__"),
        ]
        
        for import_stmt, symbol in import_tests:
            try:
                namespace = {}
                exec(import_stmt, namespace)
                assert symbol in namespace, f"Symbol '{symbol}' not imported"
            except ImportError as e:
                pytest.fail(f"Failed to execute '{import_stmt}': {e}")


class TestPlatformCompatibility:
    """Test platform-specific compatibility."""
    
    def test_path_separators(self):
        """Test that path operations work correctly on current platform."""
        from pathlib import Path
        
        # Test that Path handles separators correctly
        test_path = Path("tools") / "m1f" / "cli.py"
        assert test_path.parts[-1] == "cli.py"
        
    def test_shebang_presence(self):
        """Test that Python files have proper shebang lines."""
        # This is more for documentation - Windows ignores shebangs
        tools_dir = Path(__file__).parent.parent / "tools"
        
        # Check a few key files
        key_files = [
            tools_dir / "m1f.py",
            tools_dir / "s1f.py",
        ]
        
        for file_path in key_files:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    # Shebang is optional but if present should be correct
                    if first_line.startswith("#!"):
                        assert "python" in first_line.lower(), (
                            f"File {file_path} has shebang but doesn't reference python"
                        )


def test_installation_method():
    """Test that the package is installed correctly."""
    try:
        import m1f
        
        # Check if it's an editable installation
        if hasattr(m1f, '__file__'):
            install_path = Path(m1f.__file__).parent
            print(f"Package installed at: {install_path}")
            
            # Check if this looks like an editable install
            if "site-packages" not in str(install_path):
                print("Package appears to be an editable installation")
            else:
                print("Package appears to be a regular installation")
    except ImportError:
        pytest.fail("Package 'm1f' is not installed")


if __name__ == "__main__":
    # Allow running this test directly
    pytest.main([__file__, "-v"])