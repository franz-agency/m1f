# Version Management

This project uses centralized version management to ensure consistency across all components.

## Structure

- **Single Source of Truth**: `tools/_version.py`
- **Automatic Syncing**: Scripts to keep all files in sync
- **Dynamic Imports**: All modules import from the central version file

## Files That Use Version

1. **Python Modules**:
   - `tools/__init__.py` - imports from `_version.py`
   - `tools/m1f/__init__.py` - imports from `../_version.py`
   - `tools/s1f/__init__.py` - imports from `../_version.py`
   - `tools/html2md/__init__.py` - imports from `../_version.py`
   - `tools/webscraper/__init__.py` - imports from `../_version.py`

2. **Setup Files**:
   - `tools/setup.py` - reads version dynamically from `_version.py`

3. **NPM Package**:
   - `package.json` - synced using `sync_version.py`

4. **Legacy Script**:
   - `tools/m1f.py` - imports with fallback for standalone usage

## Updating Version

### Manual Update

1. Edit `tools/_version.py` and change the version
2. Run `python scripts/sync_version.py` to sync with package.json

### Using Bump Script

```bash
# Bump patch version (3.1.0 → 3.1.1)
python scripts/bump_version.py patch

# Bump minor version (3.1.0 → 3.2.0)
python scripts/bump_version.py minor

# Bump major version (3.1.0 → 4.0.0)
python scripts/bump_version.py major

# Set specific version
python scripts/bump_version.py 3.2.0-beta1
```

The bump script will:
1. Update `tools/_version.py`
2. Automatically sync `package.json`
3. Display next steps for committing and tagging

## Benefits

1. **Single Update Point**: Change version in one place only
2. **Consistency**: All components always have the same version
3. **Automation**: Scripts handle syncing and validation
4. **Future-Proof**: Easy to add new files that need version info

## Adding New Components

When adding a new tool or module that needs version info:

1. Import from the parent package:
   ```python
   from .._version import __version__, __version_info__
   ```

2. No need to update sync scripts - they work automatically

## Version Format

- Follows semantic versioning: `MAJOR.MINOR.PATCH`
- Pre-release versions supported: `3.2.0-beta1`
- `__version__`: String format (e.g., "3.1.0")
- `__version_info__`: Tuple format (e.g., (3, 1, 0))