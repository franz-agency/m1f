# m1f (Make One File) Tests

This directory contains comprehensive tests for the `m1f.py` script (the m1f
tool) located in the `tools` directory.

## Test Structure

The test suite consists of:

1. **Test Files**:

   - `test_m1f.py`: The main test file containing all test cases
   - `run_tests.py`: A utility script to run tests selectively

2. **Test Directories**:

   - `source/`: Contains test files with various formats and edge cases
   - `output/`: Contains generated output files (this directory is git-ignored)

3. **Utility Files**:
   - `exclude_paths.txt`: Sample file for testing path exclusion
   - `input_paths.txt`: Sample file for testing input paths functionality

## Running Tests

You can run the tests in several ways:

### Run all tests

```bash
python -m pytest tests/m1f/test_m1f.py -v
```

### Run using the run_tests.py utility

```bash
# Run all tests
python tests/m1f/run_tests.py --all

# Run specific test categories
python tests/m1f/run_tests.py --basic --archive
python tests/m1f/run_tests.py --styles
python tests/m1f/run_tests.py --cli

# Run with verbose output
python tests/m1f/run_tests.py --all --verbose
```

## Test Coverage

The tests cover all major functionality of the m1f tool (`m1f.py`):

1. **Basic functionality**:

   - Combining files from source directory
   - File separators
   - Excluding directories

2. **File selection**:

   - Including/excluding dot files
   - Excluding paths from file
   - Additional directory exclusions

3. **Output options**:

   - Different separator styles
   - Line ending options
   - Timestamp in filename

4. **Archive creation**:

   - ZIP archive
   - TAR.GZ archive

5. **Edge cases**:

   - Unicode character handling
   - HTML with complex syntax
   - Large files
   - Files with fake separators

6. **LLM-specific features**:
   - Machine-readable formatting for AI processing
   - Token estimation for context planning
   - Command line interface options for integration with AI workflows

## Maintainer Information

- Author: Franz und Franz
- Homepage: https://franz.agency
- Project: https://m1f.dev
- License: See project LICENSE file
