# M1F Test Suite

Comprehensive test suite for the m1f (Make One File) tool with 23 test files and ~180 test methods, covering all aspects of functionality, security, and performance.

## 📁 Test Structure

```
tests/m1f/
├── README.md                             # This file
├── conftest.py                           # m1f-specific test fixtures
│
├── Core Functionality Tests
│   ├── test_m1f_basic.py                # Basic operations and CLI options
│   ├── test_m1f_advanced.py             # Advanced features (archives, patterns)
│   ├── test_m1f_integration.py          # End-to-end integration tests
│   ├── test_m1f_edge_cases.py           # Edge cases and special scenarios
│   └── test_m1f.py                      # General functionality tests
│
├── Security & Safety Tests
│   ├── test_security_check.py           # Secret detection features
│   ├── test_path_traversal_security.py  # Path traversal vulnerability tests
│   └── test_content_deduplication.py    # File deduplication logic
│
├── Performance & Optimization Tests
│   ├── test_parallel_processing.py      # Async/parallel operations
│   ├── test_large_file.py              # Large file performance tests
│   └── test_cross_platform_paths.py    # Windows/Linux compatibility
│
├── Encoding & Character Tests
│   ├── test_m1f_encoding.py            # Character encoding handling
│   └── test_m1f_unicode.py             # Unicode handling tests
│
├── File System Tests
│   ├── test_symlinks.py                # Symbolic link handling
│   ├── test_symlinks_relative.py       # Relative symlink tests
│   ├── test_symlinks_deduplication.py  # Symlink deduplication
│   └── test_m1f_file_hash.py          # Filename mtime hash functionality
│
├── Preset System Tests (v3.2+ features)
│   ├── test_m1f_presets_basic.py       # Basic preset functionality
│   ├── test_m1f_presets_integration.py # Advanced preset scenarios
│   └── test_m1f_presets_v3_2.py       # v3.2 preset features
│
├── Advanced Filtering Tests
│   ├── test_multiple_exclude_include_files.py # Complex filtering
│   └── test_m1f_excludes.py            # Exclusion pattern tests
│
├── Test Data & Resources
│   ├── source/                         # Test data organized by scenario
│   │   ├── glob_*/                    # Pattern matching test cases
│   │   ├── exotic_encodings/          # Non-UTF8 encoding samples
│   │   ├── advanced_glob_test/        # Complex nested structures
│   │   ├── code/                      # Sample code files
│   │   ├── docs/                      # Sample documentation
│   │   └── config/                    # Sample configs
│   ├── exclude_paths.txt              # Sample exclusion file
│   └── input_paths.txt                # Sample input paths file
```

## 🧪 Test Categories

### 1. **Core Functionality** 
Tests fundamental m1f operations across multiple test files.

**Basic Operations** (`test_m1f_basic.py`):
- ✅ Basic file combination
- ✅ Separator styles (Standard, Detailed, Markdown, MachineReadable)
- ✅ Timestamp in filenames (`-t` flag)
- ✅ Line ending options (LF/CRLF)
- ✅ Dot file/directory inclusion
- ✅ Path exclusion from file
- ✅ Force overwrite (`-f`)
- ✅ Verbose/quiet modes

**Advanced Features** (`test_m1f_advanced.py`):
- 📦 Archive creation (ZIP, TAR.GZ)
- 🚫 Gitignore pattern support
- 📝 File extension filtering
- 🔍 Input paths with glob patterns
- 🔐 Filename mtime hash
- 🛠️ Disabling default excludes
- 🔢 Binary file inclusion

### 2. **Security & Safety**
Comprehensive security testing to prevent vulnerabilities.

**Secret Detection** (`test_security_check.py`):
- 🔍 Password and API key detection
- ⚙️ Security check modes (skip, warn, abort)
- 📝 Security warning logs
- ✅ Clean file verification

**Path Traversal** (`test_path_traversal_security.py`):
- 🛡️ Path traversal attack prevention
- 📁 Malicious path handling
- 🔒 Sandbox escape prevention
- ⚠️ Security boundary enforcement

**Content Deduplication** (`test_content_deduplication.py`):
- #️⃣ SHA256-based deduplication
- 🔄 Duplicate file detection
- 📊 Deduplication statistics
- 💾 Memory efficiency

### 3. **Performance & Scalability**

**Parallel Processing** (`test_parallel_processing.py`):
- ⚡ Async file operations
- 🔀 Concurrent processing
- 📈 Performance benchmarks
- 🎯 Resource optimization

**Large Files** (`test_large_file.py`):
- 📊 Various file sizes (0.5MB - 10MB)
- 💾 Memory efficiency
- ⚡ Processing speed
- ✅ Content integrity

**Cross-Platform** (`test_cross_platform_paths.py`):
- 🪟 Windows path handling
- 🐧 Linux/macOS compatibility
- 🔀 Path separator normalization
- 📁 Drive letter handling

### 4. **Encoding & Internationalization**

**Encoding Support** (`test_m1f_encoding.py`):
- 🔤 UTF-8, UTF-16, Latin-1
- 🌏 Exotic encodings:
  - Shift-JIS (Japanese)
  - GB2312 (Chinese)
  - EUC-KR (Korean)
  - KOI8-R (Russian)
  - ISO-8859-8 (Hebrew)
  - Windows-1256 (Arabic)
- ⚠️ Encoding error handling
- 💾 BOM handling

**Unicode** (`test_m1f_unicode.py`):
- 🌍 Unicode filename support
- 😀 Emoji in content
- 🎭 Special characters
- 📝 Unicode normalization

### 5. **File System Features**

**Symbolic Links** (3 test files):
- 🔗 Basic symlink handling (`test_symlinks.py`)
- 📍 Relative symlinks (`test_symlinks_relative.py`)
- 🔄 Symlink deduplication (`test_symlinks_deduplication.py`)
- 🚫 Circular reference detection
- 📝 Target resolution

**File Hash** (`test_m1f_file_hash.py`):
- #️⃣ Modification time hashing
- 🔒 Hash consistency
- 🔄 Change detection
- 📁 Directory handling

### 6. **Preset System** (v3.2+)

**Basic Presets** (`test_m1f_presets_basic.py`):
- 🎨 Global preset settings
- 📝 File-specific processors
- 🧹 Content cleaning

**Advanced Presets** (`test_m1f_presets_integration.py`):
- 🔗 Preset inheritance
- 🌍 Environment-based presets
- 🎯 Conditional presets
- 🔧 Complex workflows

**v3.2 Features** (`test_m1f_presets_v3_2.py`):
- 📁 Source/output configuration
- 📋 Input include files
- ⚙️ Runtime behavior settings
- 🔄 CLI argument overrides

### 7. **Advanced Filtering**

**Multiple Files** (`test_multiple_exclude_include_files.py`):
- 📋 Multiple exclude files
- ✅ Multiple include files
- 🔀 Combined exclude/include
- ⚠️ Error handling

**Exclusion Patterns** (`test_m1f_excludes.py`):
- 🎯 Glob pattern exclusions
- 📝 Regex exclusions
- 🔍 Gitignore integration
- 📁 Directory exclusions

## 🧪 Test Fixtures (conftest.py)

**Core Fixtures:**
- `m1f_source_dir` - Source directory for test files
- `m1f_output_dir` - Output directory with auto-cleanup
- `m1f_extracted_dir` - Extraction directory
- `run_m1f` - Direct function testing with mocked args
- `m1f_cli_runner` - Subprocess-based CLI testing
- `create_m1f_test_structure` - Standard test directory creation

**Utilities:**
- Cross-platform path handling
- Automatic cleanup on Windows
- Test file creation helpers
- Directory structure builders

## 🚀 Running Tests

### Run All M1F Tests
```bash
pytest tests/m1f/ -v
```

### Run Specific Categories
```bash
# By marker
pytest tests/m1f/ -m unit
pytest tests/m1f/ -m integration
pytest tests/m1f/ -m encoding
pytest tests/m1f/ -m "not slow"
pytest tests/m1f/ -m requires_git

# By test file pattern
pytest tests/m1f/test_*security*.py -v
pytest tests/m1f/test_*encoding*.py -v
pytest tests/m1f/test_*preset*.py -v
```

### Run Individual Tests
```bash
# Specific test file
pytest tests/m1f/test_m1f_basic.py -v

# Specific test method
pytest tests/m1f/test_m1f_encoding.py::TestM1FEncoding::test_exotic_encodings -v

# Tests matching pattern
pytest tests/m1f/ -k "test_encoding" -v
```

### Debug Options
```bash
# Stop on first failure
pytest tests/m1f/ -x

# Show print statements
pytest tests/m1f/ -s

# Drop into debugger
pytest tests/m1f/ --pdb

# Verbose with full diff
pytest tests/m1f/ -vv
```

## 📊 Coverage Analysis

```bash
# Run with coverage
pytest tests/m1f/ --cov=tools.m1f --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html
```

**Coverage Goals:**
- Core functionality: 100%
- Edge cases: >95%
- Error handling: >90%
- Platform-specific: >85%

## 🧪 Test Data Organization

### Pattern Testing (`source/glob_*`)
- Basic glob patterns
- Recursive patterns
- Multiple wildcards
- Directory-specific patterns

### Encoding Samples (`source/exotic_encodings/`)
- Text files in various encodings
- International content
- BOM variations
- Mixed encodings

### Complex Structures (`source/advanced_glob_test/`)
- Deep nesting (5+ levels)
- International filenames
- Mixed file types
- Large directory trees

### Real-World Examples
- Code files (Python, JavaScript, etc.)
- Documentation (Markdown, RST)
- Configuration (YAML, JSON, INI)
- Binary files (images, archives)

## 📝 Writing New Tests

### Test Template
```python
from __future__ import annotations

import pytest
from pathlib import Path
from ..conftest import M1FTestContext

class TestNewFeature:
    """Tests for new m1f feature."""
    
    @pytest.mark.unit
    async def test_feature_basic(self, run_m1f: M1FTestContext):
        """Test basic feature functionality."""
        # Arrange
        test_file = run_m1f.create_file("test.txt", "content")
        
        # Act
        result = await run_m1f.execute([
            str(test_file),
            "-o", str(run_m1f.output_dir / "output.txt")
        ])
        
        # Assert
        assert result.returncode == 0
        assert "expected output" in result.stdout
```

### Best Practices
1. **Use fixtures** - Don't create files manually
2. **Test isolation** - Each test should be independent
3. **Clear naming** - Test name should describe behavior
4. **Appropriate markers** - Use unit/integration/slow markers
5. **Cleanup** - Fixtures handle cleanup automatically
6. **Cross-platform** - Consider Windows/Linux differences

## 🔧 Troubleshooting

### Common Issues

**Windows-Specific:**
- File locking during cleanup
- Path length limitations
- Case-insensitive paths
- Line ending differences

**Encoding Issues:**
- System locale dependencies
- Missing codec support
- BOM handling differences

**Performance:**
- Slow tests not marked
- Resource cleanup delays
- Large test data files

### Solutions
```bash
# Skip slow tests
pytest -m "not slow"

# Run with specific encoding
PYTHONIOENCODING=utf-8 pytest

# Increase timeout
pytest --timeout=300

# Clean test artifacts
rm -rf tests/m1f/output_* tests/m1f/extracted_*
```

## 🛠️ Maintenance

- **Regular cleanup** - Remove obsolete test data
- **Performance monitoring** - Track test suite execution time
- **Coverage tracking** - Maintain high coverage
- **Dependency updates** - Keep test dependencies current
- **Documentation** - Update this README with new tests
