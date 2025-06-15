# m1f Default Excludes Guide

This guide explains the files and directories that m1f excludes by default,
helping you write minimal and efficient `.m1f.config.yml` configurations.

## 🚨 CRITICAL: Correct Bundle Format

**ALWAYS use the `sources:` array format, NOT `source_directory:`!**

```yaml
# ✅ CORRECT FORMAT:
bundles:
  - name: my-bundle
    sources:
      - "./src"
    output_file: "m1f/my-bundle.txt"
    separator_style: Standard  # Or omit - Standard is default

# ❌ WRONG FORMAT (will cause errors):
bundles:
  my-bundle:
    source_directory: "./src"  # This format causes "ERROR: At least one of -s/--source-directory..."
    output_file: "m1f/my-bundle.txt"
    separator_style: Detailed  # Don't use for AI bundles!
```

**ALWAYS test with `m1f-update` immediately after creating/editing
.m1f.config.yml!**

## Understanding Default Excludes

**IMPORTANT**: m1f automatically excludes many common directories and files. You
DON'T need to repeat these in your configuration - only add project-specific
exclusions!

## Default Excluded Directories

The following directories are ALWAYS excluded unless you explicitly use
`--no-default-excludes`:

```yaml
# These are excluded automatically - no need to add them to your config!
- vendor/ # Composer dependencies (PHP)
- node_modules/ # NPM dependencies (JavaScript)
- build/ # Common build output directory
- dist/ # Distribution/compiled files
- cache/ # Cache directories
- .git/ # Git repository data
- .svn/ # Subversion data
- .hg/ # Mercurial data
- __pycache__/ # Python bytecode cache
- .pytest_cache/ # Pytest cache
- .mypy_cache/ # MyPy type checker cache
- .tox/ # Tox testing cache
- .coverage/ # Coverage.py data
- .eggs/ # Python eggs
- htmlcov/ # HTML coverage reports
- .idea/ # IntelliJ IDEA settings
- .vscode/ # Visual Studio Code settings
```

## Default Excluded Files

These specific files are also excluded automatically:

```yaml
# These files are excluded by default:
- LICENSE # License files (usually not needed in bundles)
- package-lock.json # NPM lock file
- composer.lock # Composer lock file
- poetry.lock # Poetry lock file
- Pipfile.lock # Pipenv lock file
- yarn.lock # Yarn lock file
```

## Writing Minimal Configurations

### ❌ BAD - Overly Verbose Configuration

```yaml
# DON'T DO THIS - repeating default excludes unnecessarily!
global:
  global_excludes:
    - "**/node_modules/**" # Already excluded by default!
    - "**/vendor/**" # Already excluded by default!
    - "**/__pycache__/**" # Already excluded by default!
    - "**/build/**" # Already excluded by default!
    - "**/dist/**" # Already excluded by default!
    - "**/.git/**" # Already excluded by default!
    - "**/cache/**" # Already excluded by default!
    - "**/.vscode/**" # Already excluded by default!
    - "**/*.pyc" # Project-specific - OK
    - "**/logs/**" # Project-specific - OK
```

### ✅ GOOD - Minimal Configuration

```yaml
# Only add project-specific exclusions!
global:
  global_excludes:
    - "**/*.pyc" # Python bytecode
    - "**/logs/**" # Your project's log files
    - "**/tmp/**" # Your temporary directories
    - "/m1f/**" # Output directory
    - "**/secrets/**" # Sensitive data
```

## Common Patterns by Project Type

### Python Projects

```yaml
# Only add what's NOT in default excludes
global:
  global_excludes:
    - "**/*.pyc" # Bytecode files
    - "**/*.pyo" # Optimized bytecode
    - "**/*.pyd" # Python DLL files
    - "**/venv/**" # Virtual environments
    - "**/.venv/**" # Alternative venv naming
    - "**/env/**" # Another venv naming
```

### Node.js Projects

```yaml
# node_modules is already excluded!
global:
  global_excludes:
    - "**/.next/**" # Next.js build cache
    - "**/.nuxt/**" # Nuxt.js build cache
    - "**/coverage/**" # Test coverage reports
    - "**/*.log" # Log files
```

### WordPress Projects

```yaml
# Only WordPress-specific excludes needed
global:
  global_excludes:
    - "**/wp-content/uploads/**" # User uploads
    - "**/wp-content/cache/**" # Cache plugins
    - "**/wp-content/backup/**" # Backup files
    - "wp-admin/**" # Core files
    - "wp-includes/**" # Core files
```

## Using .gitignore as Exclude File

Instead of manually listing excludes, use your existing .gitignore:

```yaml
global:
  global_settings:
    # This automatically uses your .gitignore patterns!
    exclude_paths_file: ".gitignore"
```

Or use multiple exclude files:

```yaml
global:
  global_settings:
    exclude_paths_file:
      - ".gitignore" # Version control ignores
      - ".m1fignore" # m1f-specific ignores
```

## Checking What's Excluded

To see all excluded paths (including defaults), use verbose mode:

```bash
m1f -s . -o test.txt --verbose
```

This will show:

- Default excluded directories
- Patterns from your config
- Files matched by your exclude patterns

## Disabling Default Excludes

If you need to include normally excluded directories:

```bash
# Include everything, even node_modules, .git, etc.
m1f -s . -o complete.txt --no-default-excludes
```

⚠️ **WARNING**: This can create HUGE bundles and include sensitive data!

## Best Practices

1. **Start Simple**: Begin with no excludes and add only as needed
2. **Use .gitignore**: Leverage existing ignore patterns
3. **Test First**: Run with `--verbose` to see what's excluded
4. **Document Why**: Add comments explaining non-obvious excludes

```yaml
global:
  global_excludes:
    # Project-specific build artifacts
    - "**/generated/**" # Auto-generated code
    - "**/reports/**" # Test/coverage reports

    # Large data files
    - "**/*.sqlite" # Database files
    - "**/*.csv" # Data exports

    # Sensitive information
    - "**/.env*" # Environment files
    - "**/secrets/**" # API keys, certs
```

## Quick Reference

### Already Excluded (Don't Repeat)

- `node_modules/`, `vendor/`, `build/`, `dist/`
- `.git/`, `.svn/`, `.hg/`
- `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`
- `.idea/`, `.vscode/`
- Lock files: `*.lock`, `package-lock.json`

### Commonly Added (Project-Specific)

- Virtual envs: `venv/`, `.venv/`, `env/`
- Logs: `*.log`, `logs/`
- Temp files: `tmp/`, `temp/`, `*.tmp`
- Database: `*.sqlite`, `*.db`
- Environment: `.env`, `.env.*`
- Output: `/m1f/` (your bundle directory)

## Summary

Keep your `.m1f.config.yml` files clean and minimal by:

1. NOT repeating default excludes
2. Only adding project-specific patterns
3. Using `.gitignore` when possible
4. Documenting non-obvious exclusions

This makes your configurations easier to read, maintain, and share with others!
