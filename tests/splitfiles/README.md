# Splitfiles Test Suite

This directory contains tests for the `splitfiles.py` utility. The test suite
verifies that files combined with `makeonefile.py` using different separator
styles can be correctly extracted back to their original form.

## Directory Structure

- `source/`: Contains example files created during test setup (not used
  directly)
- `output/`: Contains combined files created with different separator styles
- `extracted/`: Target directory for extracted files during tests

## Test Setup

Before running tests, combined test files need to be created using
`makeonefile.py`. These files serve as input for the `splitfiles.py` tests. Run
the following commands from the project root to create the necessary test files:

```bash
# Create combined files with different separator styles
python tools/makeonefile.py --source-directory tests/makeonefile/source --output-file tests/splitfiles/output/standard.txt --separator-style Standard --force
python tools/makeonefile.py --source-directory tests/makeonefile/source --output-file tests/splitfiles/output/detailed.txt --separator-style Detailed --force
python tools/makeonefile.py --source-directory tests/makeonefile/source --output-file tests/splitfiles/output/markdown.txt --separator-style Markdown --force
python tools/makeonefile.py --source-directory tests/makeonefile/source --output-file tests/splitfiles/output/machinereadable.txt --separator-style MachineReadable --force
```

## Running Tests

To run all tests:

```bash
# Activate the virtual environment first
.venv/Scripts/activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Run tests from the project root
python tests/splitfiles/run_tests.py
```

Or, you can use pytest directly:

```bash
pytest tests/splitfiles/test_splitfiles.py -xvs
```

## Test Cases

The test suite includes the following test cases:

1. **Separator Style Tests**:

   - Tests extraction with Standard separator style
   - Tests extraction with Detailed separator style
   - Tests extraction with Markdown separator style
   - Tests extraction with MachineReadable separator style

2. **Feature Tests**:

   - Tests force overwrite of existing files
   - Tests setting file timestamps to current time

3. **Integration Tests**:
   - Tests command-line execution

## Recent Improvements

The following improvements have been made to the `splitfiles.py` utility:

- **Improved Path Extraction**: Fixed issues with path extraction in the
  Standard separator style. All separator styles now correctly extract and
  preserve the original file paths.
- **Consistent Behavior**: Ensured consistent behavior across all separator
  styles (Standard, Detailed, Markdown, and MachineReadable).
- **Documentation Updates**: Updated documentation to reflect these
  improvements.

These changes ensure that the directory structure is properly reconstructed
regardless of which separator style was used when creating the combined file.

## Verification Process

The tests verify that:

1. Files are successfully extracted to the destination directory
2. The directory structure is preserved
3. File content matches the original files (verified using SHA-256 checksums)
4. Command-line options work as expected

## Dependencies

- Python 3.7+
- pytest
- Access to the original source files in `tests/makeonefile/source/`
