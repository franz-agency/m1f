# Test Suite Documentation

This directory contains the modernized test suite for the m1f and s1f tools, using Python 3.10+ features and modern testing practices.

## Test Structure

```
tests/
├── conftest.py              # Global fixtures and test configuration
├── base_test.py             # Base test classes with common utilities
├── pytest.ini               # Test-specific pytest configuration
├── m1f/                     # m1f-specific tests
│   ├── conftest.py          # m1f-specific fixtures
│   ├── test_m1f_basic.py    # Basic functionality tests
│   ├── test_m1f_advanced.py # Advanced features tests
│   ├── test_m1f_encoding.py # Encoding-related tests
│   ├── test_m1f_edge_cases.py # Edge cases and special scenarios
│   ├── test_m1f_file_hash.py # Filename mtime hash functionality
│   ├── test_m1f_integration.py # Integration and CLI tests
│   └── ...                  # Other test files and resources
└── s1f/                     # s1f-specific tests
    ├── conftest.py          # s1f-specific fixtures
    ├── test_s1f_basic.py    # Basic functionality tests
    ├── test_s1f_encoding.py # Encoding-related tests
    ├── test_s1f_async.py    # Async functionality tests
    └── ...                  # Other test files and resources
```

## Key Features

### Modern Python 3.10+ Features

- **Type Hints**: All functions and fixtures use modern type hints with the union operator (`|`)
- **Structural Pattern Matching**: Where applicable (Python 3.10+)
- **Better Type Annotations**: Using `from __future__ import annotations`
- **Modern pathlib Usage**: Consistent use of `Path` objects

### Test Organization

- **Modular Test Files**: Tests are split into focused modules by functionality
- **Base Test Classes**: Common functionality is abstracted into base classes
- **Fixture Hierarchy**: Global, tool-specific, and test-specific fixtures
- **Clear Test Markers**: Tests are marked with categories (unit, integration, slow, encoding)

### Key Fixtures

#### Global Fixtures (conftest.py)

- `temp_dir`: Creates a temporary directory for test files
- `isolated_filesystem`: Provides an isolated filesystem environment
- `create_test_file`: Factory for creating test files
- `create_test_directory_structure`: Creates complex directory structures
- `capture_logs`: Captures and examines log output
- `cleanup_logging`: Automatically cleans up logging handlers

#### M1F-Specific Fixtures (m1f/conftest.py)

- `run_m1f`: Runs m1f with specified arguments
- `m1f_cli_runner`: Runs m1f as a subprocess
- `create_m1f_test_structure`: Creates m1f-specific test structures

#### S1F-Specific Fixtures (s1f/conftest.py)

- `run_s1f`: Runs s1f with specified arguments
- `s1f_cli_runner`: Runs s1f as a subprocess
- `create_combined_file`: Creates combined files in different formats
- `create_m1f_output`: Uses m1f to create realistic test files

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test Categories
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run encoding-related tests
pytest -m encoding

# Skip slow tests
pytest -m "not slow"
```

### Run Tests for Specific Tools
```bash
# Run only m1f tests
pytest tests/m1f/

# Run only s1f tests
pytest tests/s1f/
```

### Run Specific Test Files
```bash
# Run basic m1f tests
pytest tests/m1f/test_m1f_basic.py

# Run encoding tests for both tools
pytest tests/m1f/test_m1f_encoding.py tests/s1f/test_s1f_encoding.py
```

### Run with Coverage
```bash
# Install pytest-cov if not already installed
pip install pytest-cov

# Run with coverage report
pytest --cov=tools --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
- Fast, isolated tests of individual components
- No external dependencies
- Mock external interactions

### Integration Tests (`@pytest.mark.integration`)
- Test interaction between multiple components
- May create real files and directories
- Test end-to-end workflows

### Slow Tests (`@pytest.mark.slow`)
- Tests that take significant time (e.g., large file handling)
- Skipped in quick test runs

### Encoding Tests (`@pytest.mark.encoding`)
- Tests related to character encoding
- May require specific system encodings

## Writing New Tests

### Test Class Structure
```python
from __future__ import annotations

import pytest
from ..base_test import BaseM1FTest  # or BaseS1FTest

class TestFeatureName(BaseM1FTest):
    """Description of what these tests cover."""
    
    @pytest.mark.unit
    def test_specific_behavior(self, fixture1, fixture2):
        """Test description."""
        # Arrange
        ...
        
        # Act
        ...
        
        # Assert
        ...
```

### Using Fixtures
```python
def test_with_temp_files(self, create_test_file, temp_dir):
    """Example using fixture to create test files."""
    # Create a test file
    test_file = create_test_file("test.txt", "content")
    
    # Use temp_dir for output
    output_file = temp_dir / "output.txt"
```

### Parametrized Tests
```python
@pytest.mark.parametrize("input,expected", [
    ("value1", "result1"),
    ("value2", "result2"),
])
def test_multiple_cases(self, input, expected):
    """Test with multiple input/output pairs."""
    assert process(input) == expected
```

## Best Practices

1. **Use Type Hints**: All test functions and fixtures should have type hints
2. **Clear Test Names**: Test names should describe what is being tested
3. **Docstrings**: Each test should have a docstring explaining its purpose
4. **Arrange-Act-Assert**: Follow the AAA pattern for test structure
5. **Use Fixtures**: Leverage fixtures for common setup and teardown
6. **Mark Tests**: Use appropriate markers for test categorization
7. **Isolated Tests**: Each test should be independent and not rely on others

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the tools directory is in the Python path
2. **Fixture Not Found**: Check that conftest.py files are properly placed
3. **Encoding Errors**: Some encoding tests may fail on systems without specific encodings
4. **Permission Errors**: Ensure proper cleanup of temporary files

### Debug Options
```bash
# Run with verbose output
pytest -vv

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Drop into debugger on failure
pytest --pdb
``` 