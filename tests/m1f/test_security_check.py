import sys
import logging
from pathlib import Path

import pytest

pytest.importorskip("detect_secrets")

# Reuse helper from main test suite
from tests.m1f.test_m1f import run_m1f, SOURCE_DIR, OUTPUT_DIR

def test_security_check_abort():
    output_file = OUTPUT_DIR / "security_abort.txt"
    with pytest.raises(SystemExit):
        run_m1f([
            "--source-directory",
            str(SOURCE_DIR),
            "--output-file",
            str(output_file),
            "--include-dot-paths",
            "--security-check",
            "abort",
            "--force",
        ])
    assert not output_file.exists(), "Output file should not be created when aborting"


def test_security_check_skip():
    output_file = OUTPUT_DIR / "security_skip.txt"
    run_m1f([
        "--source-directory",
        str(SOURCE_DIR),
        "--output-file",
        str(output_file),
        "--include-dot-paths",
        "--security-check",
        "skip",
        "--force",
    ])
    assert output_file.exists(), "Output file missing when skipping"
    with open(output_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "SECRET_KEY" not in content


def test_security_check_warn():
    output_file = OUTPUT_DIR / "security_warn.txt"
    run_m1f([
        "--source-directory",
        str(SOURCE_DIR),
        "--output-file",
        str(output_file),
        "--include-dot-paths",
        "--security-check",
        "warn",
        "--force",
    ])
    assert output_file.exists(), "Output file missing when warning"
    with open(output_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "SECRET_KEY" in content
    log_file = output_file.with_suffix(".log")
    if log_file.exists():
        with open(log_file, "r", encoding="utf-8") as log:
            log_content = log.read()
            assert "SECURITY WARNING" in log_content
