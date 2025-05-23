import sys
import logging
import shutil
from pathlib import Path

import pytest

pytest.importorskip("detect_secrets")

# Reuse helper from main test suite
from .test_m1f import run_m1f, SOURCE_DIR, OUTPUT_DIR, _create_test_file

# Import the security scan function directly for isolated testing
from tools.m1f import _scan_files_for_sensitive_info


def test_security_detection():
    """Test that security scanning correctly identifies files with/without sensitive information."""
    # Create a test directory with clean and sensitive files
    test_dir = SOURCE_DIR / "security_detection_test"
    test_dir.mkdir(exist_ok=True)

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
    output_file = OUTPUT_DIR / "security_skip.txt"
    run_m1f(
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
    assert output_file.exists(), "Output file missing when skipping"
    with open(output_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "SECRET_KEY" not in content


def test_security_check_warn():
    output_file = OUTPUT_DIR / "security_warn.txt"
    run_m1f(
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
    assert output_file.exists(), "Output file missing when warning"
    with open(output_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "SECRET_KEY" in content
    log_file = output_file.with_suffix(".log")
    if log_file.exists():
        with open(log_file, "r", encoding="utf-8") as log:
            log_content = log.read()
            assert "SECURITY WARNING" in log_content
