# m1f (Make One File) Tests

This directory contains comprehensive tests for the `makeonefile.py` script
(the m1f tool) located in the `tools` directory.

## Test Structure

The test suite consists of:

1. **Test Files**:

   - `test_makeonefile.py`: The main test file containing all test cases
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
python -m pytest tests/makeonefile/test_makeonefile.py -v
```

### Run using the run_tests.py utility

```bash
# Run all tests
python tests/makeonefile/run_tests.py --all

# Run specific test categories
python tests/makeonefile/run_tests.py --basic --archive
python tests/makeonefile/run_tests.py --styles
python tests/makeonefile/run_tests.py --cli

# Run with verbose output
python tests/makeonefile/run_tests.py --all --verbose
```

## Test Coverage

The tests cover all major functionality of the m1f tool (`makeonefile.py`):

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
