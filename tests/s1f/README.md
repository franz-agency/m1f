# s1f (Split One File) Test Suite

This directory contains tests for the `s1f.py` utility (the s1f tool). The test
suite verifies that files combined with m1f (`m1f.py`) using different separator
styles can be correctly extracted back to their original form.

## Directory Structure

- `source/`: Contains example files created during test setup (not used
  directly)
- `output/`: Contains combined files created with different separator styles
- `extracted/`: Target directory for extracted files during tests

## Test Setup

Before running tests, combined test files need to be created using the m1f tool
(`m1f.py`). These files serve as input for the s1f tests. Run the following
commands from the project root to create the necessary test files:

```bash
# Create combined files with different separator styles
m1f --source-directory tests/m1f/source --output-file tests/s1f/output/standard.txt --separator-style Standard --force
m1f --source-directory tests/m1f/source --output-file tests/s1f/output/detailed.txt --separator-style Detailed --force
m1f --source-directory tests/m1f/source --output-file tests/s1f/output/markdown.txt --separator-style Markdown --force
m1f --source-directory tests/m1f/source --output-file tests/s1f/output/machinereadable.txt --separator-style MachineReadable --force
```

## Running Tests

To run all tests:

```bash
# Activate the virtual environment first
.venv/Scripts/activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Run tests from the project root
python tests/s1f/run_tests.py
```

Or, you can use pytest directly:

```bash
pytest tests/s1f/test_s1f.py -xvs
```

## Test Cases

The test suite includes the following test cases:

1. **Separator Style Tests**:
   - Tests extraction with Standard separator style
   - Tests extraction with Detailed separator style
   - Tests extraction with Markdown separator style
   - Tests extraction with MachineReadable separator style (optimized for AI
     processing)

2. **Feature Tests**:
   - Tests force overwrite of existing files
   - Tests setting file timestamps to original or current time

3. **Integration Tests**:
   - Tests command-line execution
   - Tests compatibility with LLM workflow patterns

## AI and LLM Integration

The s1f tool is designed to work seamlessly with files generated by m1f for LLM
context:

- **Preserves Structure**: Maintains the exact directory structure for reference
- **Integrity Verification**: Validates that files have not been altered during
  AI processing
- **Metadata Handling**: Correctly processes machine-readable metadata added for
  AI interpretation

## Recent Improvements

The following improvements have been made to the s1f utility (`s1f.py`):

- **Improved Path Extraction**: Fixed issues with path extraction in the
  Standard separator style. All separator styles now correctly extract and
  preserve the original file paths.
- **Consistent Behavior**: Ensured consistent behavior across all separator
  styles (Standard, Detailed, Markdown, and MachineReadable).
- **LLM Optimizations**: Enhanced support for AI-specific workflows and formats.
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

## Maintainer Information

- Author: Franz und Franz
- Homepage: https://franz.agency
- Project: https://m1f.dev
- License: See project LICENSE file

## Dependencies

- Python 3.9+
- pytest
- Access to the original source files in `tests/m1f/source/`
