#!/usr/bin/env python3
"""
Test runner for m1f.py tests

This script runs the test suite for the m1f.py tool and provides a
convenient way to execute all tests or specific test categories.

Usage:
    python run_tests.py [--all] [--basic] [--archive] [--styles] [--cli]
"""

import argparse
import sys
import pytest
from pathlib import Path


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run tests for m1f.py")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument(
        "--basic", action="store_true", help="Run basic functionality tests"
    )
    parser.add_argument(
        "--archive", action="store_true", help="Run archive creation tests"
    )
    parser.add_argument(
        "--styles", action="store_true", help="Run separator style tests"
    )
    parser.add_argument(
        "--cli", action="store_true", help="Run command line interface tests"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    return parser.parse_args()


def main():
    """Main function"""
    args = parse_args()

    # If no specific tests are selected, run all tests
    if not (args.basic or args.archive or args.styles or args.cli):
        args.all = True

    # Build pytest arguments
    pytest_args = ["-xvs"] if args.verbose else ["-xs"]

    if args.all:
        # Run all tests
        pytest_args.append(str(Path(__file__).parent / "test_m1f.py"))
    else:
        # Build test selection expression
        test_expr = []

        if args.basic:
            test_expr.extend(
                [
                    "test_basic_execution",
                    "test_include_dot_files",
                    "test_exclude_paths_file",
                    "test_additional_excludes",
                    "test_line_ending_option",
                    "test_timestamp_in_filename",
                ]
            )

        if args.archive:
            test_expr.extend(["test_create_archive_zip", "test_create_archive_tar"])

        if args.styles:
            test_expr.extend(["test_separator_styles"])

        if args.cli:
            test_expr.extend(["test_command_line_execution"])

        # Build expression for pytest
        if test_expr:
            test_selection = " or ".join(
                f"test_m1f.TestM1F.{test}" for test in test_expr
            )
            pytest_args.extend(
                [
                    "-k",
                    test_selection,
                    str(Path(__file__).parent / "test_m1f.py"),
                ]
            )

    # Run the tests
    return pytest.main(pytest_args)


if __name__ == "__main__":
    sys.exit(main())
