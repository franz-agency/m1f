# m1f Test Suite

Comprehensive test suite for the m1f (Make One File) tool, organized by
functionality and test scenarios.

## 📁 Test Structure

```
tests/m1f/
├── README.md                          # This file
├── conftest.py                        # m1f-specific test fixtures
├── run_tests.py                       # Test runner utility
├── check_failures.py                  # Test failure analysis utility
│
├── Core Functionality Tests
│   ├── test_m1f_basic.py             # Basic operations and CLI options
│   ├── test_m1f_advanced.py          # Advanced features (archives, patterns)
│   ├── test_m1f_integration.py       # End-to-end integration tests
│   └── test_m1f_edge_cases.py        # Edge cases and special scenarios
│
├── Specialized Feature Tests
│   ├── test_m1f_encoding.py          # Character encoding handling
│   ├── test_m1f_file_hash.py         # Filename mtime hash functionality
│   ├── test_security_check.py        # Security scanning features
│   ├── test_symlinks.py              # Symbolic link handling
│   └── test_large_file.py            # Large file performance tests
│
├── Preset System Tests
│   ├── test_m1f_presets_basic.py     # Basic preset functionality
│   ├── test_m1f_presets_integration.py # Advanced preset scenarios
│   └── test_m1f_presets_v3_2.py     # v3.2 preset features
│
├── File Filtering Tests
│   └── test_multiple_exclude_include_files.py # Complex filtering scenarios
│
├── Test Fixtures
│   ├── source/                        # Test data organized by scenario
│   ├── exclude_paths.txt             # Sample exclusion file
│   └── input_paths.txt               # Sample input paths file
│
└── Utilities
    ├── run_tests.py                  # Category-based test runner
    └── check_failures.py             # Failure analysis tool
```

## 🧪 Test Categories

### 1. **Core Functionality** (`test_m1f_basic.py`)

Tests fundamental m1f operations and command-line options.

- ✅ Basic file combination
- ✅ Separator styles (Standard, Detailed, Markdown, MachineReadable)
- ✅ Timestamp in filenames (`-t` flag)
- ✅ Line ending options (LF/CRLF)
- ✅ Dot file/directory inclusion (`--include-dot-paths`)
- ✅ Path exclusion from file (`--exclude-paths-file`)
- ✅ Force overwrite (`-f`)
- ✅ Verbose/quiet modes
- ✅ Help and version display

### 2. **Advanced Features** (`test_m1f_advanced.py`)

Tests complex features and workflows.

- 📦 Archive creation (ZIP, TAR.GZ)
- 🚫 Gitignore pattern support
- 📝 File extension filtering (include/exclude)
- 🔍 Input paths with glob patterns
- 🔐 Filename mtime hash for change detection
- 🛠️ Disabling default excludes
- 📏 File size limits (`--max-file-size`)
- 🔢 Binary file inclusion

### 3. **Integration Tests** (`test_m1f_integration.py`)

End-to-end testing of complete workflows.

- 🔗 Command-line execution via subprocess
- 📋 Complex input paths file scenarios
- 🎯 Multiple glob pattern combinations
- 🔀 Gitignore + explicit excludes
- ⚡ Performance with many files
- 🏗️ Archive creation with filters

### 4. **Edge Cases** (`test_m1f_edge_cases.py`)

Tests unusual scenarios and boundary conditions.

- 🌍 Unicode character handling
- 🎭 Fake separator patterns in content
- 📁 Empty files and directories
- 🔗 Symbolic links (without `--include-symlinks`)
- 🎨 Special characters in filenames
- 🏗️ Deeply nested directories
- 🔄 Complex gitignore with negations
- ⚡ Concurrent file modifications

### 5. **Encoding Tests** (`test_m1f_encoding.py`)

Comprehensive character encoding support.

- 🔤 Encoding conversion to UTF-8
- 🎯 Target encoding options
- ⚠️ Encoding error handling
- 📊 MachineReadable format metadata
- 💾 BOM (Byte Order Mark) handling
- 🌏 Exotic encodings:
  - Shift-JIS (Japanese)
  - GB2312 (Chinese)
  - EUC-KR (Korean)
  - KOI8-R (Russian)
  - ISO-8859-8 (Hebrew)
  - Windows-1256 (Arabic)

### 6. **File Hash Feature** (`test_m1f_file_hash.py`)

Tests the filename mtime hash functionality.

- #️⃣ Hash generation from modification times
- 🔒 Hash consistency for unchanged files
- 🔄 Hash updates on file changes
- ➕ Hash changes with file additions/removals
- 📝 Hash changes on renames
- 🕐 Combining hash with timestamp
- 📁 Empty directory handling

### 7. **Preset System** (`test_m1f_presets_*.py`)

Tests the flexible preset configuration system.

**Basic Presets:**

- 🎨 Global preset settings
- 📝 File-specific processors
- 🧹 Content cleaning (strip_tags, remove_empty_lines)

**Advanced Presets:**

- 🔗 Preset inheritance and merging
- 🌍 Environment-based presets
- 🎯 Conditional presets
- 🔧 Complex workflows
- ⚠️ Error handling

**v3.2 Features:**

- 📁 Source/output configuration via preset
- 📋 Input include files via preset
- ⚙️ Runtime behavior settings
- 🔄 CLI argument overrides
- 🔤 Encoding settings via preset

### 8. **Security Scanning** (`test_security_check.py`)

Tests for sensitive information detection.

- 🔍 Password and API key detection
- ✅ Clean file verification
- ⚙️ Security check modes (skip, warn, abort)
- 📝 Security warning logs

### 9. **Performance Tests** (`test_large_file.py`)

Tests handling of large files.

- 📊 Various file sizes (0.5MB - 10MB)
- 🔤 Encoding with large files
- ⚡ Performance baselines
- 💾 Memory efficiency
- ✅ Content integrity

### 10. **Symbolic Links** (`test_symlinks.py`)

Tests symbolic link handling.

- 🔄 Symlink cycle detection
- 🔗 Symlink inclusion flag
- 🚫 Circular reference handling
- 📝 File deduplication

### 11. **File Filtering** (`test_multiple_exclude_include_files.py`)

Tests complex filtering scenarios.

- 📋 Multiple exclude files
- ✅ Multiple include files
- 🔀 Combined exclude/include
- 🎯 Input file bypass
- ⚠️ Non-existent file handling

## 🧪 Test Data Structure

The `source/` directory contains carefully organized test fixtures:

### Pattern Testing

- `glob_*` directories: Various glob pattern scenarios
- `file_extensions_test/`: Extension filtering tests
- `special_chars/`: Filename edge cases

### Encoding Testing

- `exotic_encodings/`: Files in various character encodings
- International filenames (German, Spanish, Russian, Chinese)

### Structure Testing

- `advanced_glob_test/`: Complex directory hierarchies
- Deep nesting scenarios
- Mixed file types

### Content Testing

- `code/`: Programming language files
- `docs/`: Documentation files
- `config/`: Configuration files

## 🚀 Running Tests

### Run All Tests

```bash
pytest tests/m1f/ -v
```

### Run Specific Test Categories

```bash
# Using pytest markers
pytest tests/m1f/ -m unit
pytest tests/m1f/ -m integration
pytest tests/m1f/ -m encoding
pytest tests/m1f/ -m "not slow"

# Using the test runner utility
python tests/m1f/run_tests.py --all
python tests/m1f/run_tests.py --basic --advanced
python tests/m1f/run_tests.py --encoding --presets
```

### Run Individual Test Files

```bash
pytest tests/m1f/test_m1f_basic.py -v
pytest tests/m1f/test_m1f_encoding.py::TestM1FEncoding::test_encoding_conversion -v
```

### Analyze Test Failures

```bash
python tests/m1f/check_failures.py
```

## 📊 Coverage Goals

- **Core Functionality**: 100% coverage of basic m1f operations
- **Edge Cases**: Comprehensive handling of unusual scenarios
- **Encoding**: Support for all major character encodings
- **Performance**: Baseline tests for large file handling
- **Security**: Detection of common sensitive patterns
- **Presets**: Full preset system functionality
- **Integration**: Real-world workflow scenarios

## 🛠️ Test Utilities

### `run_tests.py`

Convenient test runner with category selection:

- `--all`: Run all tests
- `--basic`: Basic functionality tests
- `--advanced`: Advanced feature tests
- `--encoding`: Encoding-related tests
- `--presets`: Preset system tests
- `--verbose`: Verbose output

### `check_failures.py`

Analyzes test failures and provides summaries:

- Groups failures by type
- Suggests potential fixes
- Identifies flaky tests

## 📝 Writing New Tests

When adding new tests:

1. **Choose the right file**: Add to existing test files when possible
2. **Use appropriate markers**: `@pytest.mark.unit`, `@pytest.mark.integration`,
   etc.
3. **Follow naming conventions**: `test_<feature>_<scenario>`
4. **Add test data**: Place fixtures in appropriate `source/` subdirectories
5. **Document complex tests**: Add docstrings explaining the test purpose
6. **Consider performance**: Mark slow tests with `@pytest.mark.slow`

## 🔧 Maintenance

- **Test data**: Keep test fixtures minimal but representative
- **Performance**: Monitor test suite execution time
- **Dependencies**: Update test dependencies regularly
- **Coverage**: Maintain high test coverage (aim for >90%)
