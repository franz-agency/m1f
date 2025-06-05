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

import sys
import logging
import shutil
from pathlib import Path

import pytest

pytest.importorskip("detect_secrets")

# Import helpers from conftest
from pathlib import Path
import subprocess
import tempfile

# Define test directories - use project's tmp directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
SOURCE_DIR = PROJECT_ROOT / "tmp" / "m1f_test_source"
OUTPUT_DIR = PROJECT_ROOT / "tmp" / "m1f_test_output"

def _create_test_file(path: Path, content: str) -> None:
    """Create a test file with given content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')

def run_m1f(args):
    """Run m1f with given arguments."""
    cmd = [sys.executable, "-m", "tools.m1f"] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result

# Import the security scan function directly for isolated testing
import asyncio
from tools.m1f.security_scanner import SecurityScanner
from tools.m1f.config import Config, SecurityConfig, SecurityCheckMode
from tools.m1f.logging import LoggerManager

def _scan_files_for_sensitive_info(files):
    """Helper function to scan files for sensitive info."""
    # Create a minimal config with security enabled
    security_config = SecurityConfig(
        security_check=SecurityCheckMode.WARN
    )
    
    # Need to import other config classes
    from tools.m1f.config import OutputConfig, FilterConfig, EncodingConfig, ArchiveConfig, LoggingConfig, PresetConfig
    
    # Create a minimal config
    config = Config(
        source_directory=None,
        input_file=None,
        input_include_files=[],
        output=OutputConfig(output_file=Path("dummy.txt")),
        filter=FilterConfig(),
        encoding=EncodingConfig(),
        security=security_config,
        archive=ArchiveConfig(),
        logging=LoggingConfig(),
        preset=PresetConfig()
    )
    
    # Create logger manager
    logging_config = LoggingConfig(verbose=False, quiet=True)
    logger_manager = LoggerManager(config=logging_config)
    
    # Create scanner and run async scan
    scanner = SecurityScanner(config, logger_manager)
    return asyncio.run(scanner.scan_files(files))


def test_security_detection():
    """Test that security scanning correctly identifies files with/without sensitive information."""
    # Ensure base directories exist
    try:
        SOURCE_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as e:
        pytest.skip(f"Cannot create test directories in {PROJECT_ROOT}/tmp: {e}")
    
    # Create a test directory with clean and sensitive files
    test_dir = SOURCE_DIR / "security_detection_test"
    test_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Create a file with no sensitive information
        clean_file = test_dir / "clean_file.txt"
        _create_test_file(clean_file, "This is a clean file with no secrets.")

        # Create a file with a password
        password_file = test_dir / "password_file.txt"
        _create_test_file(password_file, "password = 'supersecret123'")

        # Create a file with an API key
        api_key_file = test_dir / "api_key_file.txt"
        _create_test_file(api_key_file, "api_key: abcdef123456")

        # Create files to process tuples (abs_path, rel_path)
        clean_tuple = (clean_file, "clean_file.txt")
        password_tuple = (password_file, "password_file.txt")
        api_key_tuple = (api_key_file, "api_key_file.txt")

        # Test 1: Scan the clean file only
        clean_findings = _scan_files_for_sensitive_info([clean_tuple])
        assert len(clean_findings) == 0, "Clean file should have no findings"

        # Test 2: Scan the password file only
        password_findings = _scan_files_for_sensitive_info([password_tuple])
        assert len(password_findings) > 0, "Password file should have findings"
        assert (
            password_findings[0]["path"] == "password_file.txt"
        ), "Finding should reference correct file"

        # Test 3: Scan the API key file only
        api_key_findings = _scan_files_for_sensitive_info([api_key_tuple])
        assert len(api_key_findings) > 0, "API key file should have findings"
        assert (
            api_key_findings[0]["path"] == "api_key_file.txt"
        ), "Finding should reference correct file"

        # Test 4: Scan all files together
        all_findings = _scan_files_for_sensitive_info(
            [clean_tuple, password_tuple, api_key_tuple]
        )

        # The API key file triggers both "Secret Keyword" and "Hex High Entropy String" detections
        assert (
            len(all_findings) == 3
        ), "Should have 3 findings (password + api_key with 2 detections)"

        # Verify the specific findings contain expected information
        password_findings_count = 0
        api_key_findings_count = 0

        for finding in all_findings:
            if finding["path"] == "password_file.txt":
                password_findings_count += 1
                assert (
                    finding["type"] == "Secret Keyword"
                ), "Password should be detected as Secret Keyword"
            elif finding["path"] == "api_key_file.txt":
                api_key_findings_count += 1
                assert finding["type"] in [
                    "Secret Keyword",
                    "Hex High Entropy String",
                ], "API key should be detected as either Secret Keyword or Hex High Entropy String"

        assert (
            password_findings_count == 1
        ), "Should have exactly 1 finding for password file"
        assert (
            api_key_findings_count == 2
        ), "Should have exactly 2 findings for API key file (both Secret Keyword and Hex High Entropy String)"

    finally:
        # Clean up
        shutil.rmtree(test_dir)


def test_security_check_skip():
    # Ensure source directory exists and has a file with sensitive content
    try:
        SOURCE_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as e:
        pytest.skip(f"Cannot create test directories in {PROJECT_ROOT}/tmp: {e}")
    
    # Create a test file with SECRET_KEY
    test_file = SOURCE_DIR / "test_with_secret.py"
    _create_test_file(test_file, 'SECRET_KEY = "super_secret_123"')
    
    try:
        output_file = OUTPUT_DIR / "security_skip.txt"
        result = run_m1f(
            [
                "--source-directory",
                str(SOURCE_DIR),
                "--output-file",
                str(output_file),
                "--include-dot-paths",
                "--security-check",
                "skip",
                "--force",
            ]
        )
        # With skip mode, the output should be created regardless of security findings
        assert output_file.exists(), f"Output file missing when skipping. stderr: {result.stderr}"
        
        # Clean up
        if output_file.exists():
            output_file.unlink()
    finally:
        # Clean up test file
        if test_file.exists():
            test_file.unlink()


def test_security_check_warn():
    # Ensure source directory exists and has a file with sensitive content
    try:
        SOURCE_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as e:
        pytest.skip(f"Cannot create test directories in {PROJECT_ROOT}/tmp: {e}")
    
    # Create a test file with SECRET_KEY
    test_file = SOURCE_DIR / "test_with_secret.py"
    _create_test_file(test_file, 'SECRET_KEY = "super_secret_123"')
    
    try:
        output_file = OUTPUT_DIR / "security_warn.txt"
        result = run_m1f(
            [
                "--source-directory",
                str(SOURCE_DIR),
                "--output-file",
                str(output_file),
                "--include-dot-paths",
                "--security-check",
                "warn",
                "--force",
            ]
        )
        assert output_file.exists(), f"Output file missing when warning. stderr: {result.stderr}"
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "SECRET_KEY" in content
        
        # Clean up
        if output_file.exists():
            output_file.unlink()
    finally:
        # Clean up test file
        if test_file.exists():
            test_file.unlink()
