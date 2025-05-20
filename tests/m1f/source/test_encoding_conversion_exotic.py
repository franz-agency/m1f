import os
import sys
from pathlib import Path
import pytest

# Add the tools directory to path to import the m1f module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))
import m1f


def test_exotic_encoding_conversion():
    """Verify m1f detects & converts exotic encoded files to UTF-16-LE."""
    test_dir = Path(__file__).parent / "exotic_encodings"
    output_dir = Path(__file__).parent / "output"
    output_file = output_dir / "test_encoding_utf16le.txt"

    output_dir.mkdir(exist_ok=True)

    encoding_map = {
        "shiftjis.txt": "shift_jis",
        "big5.txt": "big5",
        "koi8r.txt": "koi8_r",
        "iso8859-8.txt": "iso8859_8",
        "euckr.txt": "euc_kr",
        "windows1256.txt": "cp1256",
    }

    args = [
        "--source-directory",
        str(test_dir),
        "--output-file",
        str(output_file),
        "--separator-style",
        "MachineReadable",
        "--convert-to-charset",
        "utf-16-le",
        "--force",
        "--include-extensions",
        ".txt",
        "--exclude-extensions",
        ".utf8",
        "--minimal-output",
    ]

    old_argv = sys.argv
    sys.argv = ["m1f.py"] + args
    old_exit = sys.exit
    sys.exit = lambda *_args, **_kw: None  # Prevent SystemExit
    try:
        m1f.main()
        assert output_file.exists() and output_file.stat().st_size > 0

        with open(output_file, "r", encoding="utf-16-le") as f:
            content = f.read()

        for filename in encoding_map:
            assert filename in content, f"{filename} missing in output"
        for enc in encoding_map.values():
            assert f'"encoding": "{enc}"' in content, f"Encoding {enc} not found"
    finally:
        sys.argv = old_argv
        sys.exit = old_exit
        try:
            output_file.unlink()
        except Exception:
            pass 