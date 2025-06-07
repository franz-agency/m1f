# m1f Quick Reference

## Most Common Commands

### Basic File Combination

```bash
# Combine all files in current directory
m1f -s . -o output.txt

# Combine specific directory
m1f -s ./src -o bundle.txt

# Force overwrite existing output
m1f -s . -o output.txt -f
```

### Using Presets (v3.2.0+)

```bash
# Use a preset file (can define ALL parameters)
m1f --preset production.yml -o output.txt

# Preset can even define source and output
m1f --preset full-config.yml

# Override preset values with CLI
m1f --preset prod.yml -o custom-output.txt -v
```

### File Type Filtering

```bash
# Only Python files
m1f -s . -o code.txt --include-extensions .py

# Multiple file types
m1f -s . -o docs.txt --include-extensions .md .txt .rst

# Exclude certain types
m1f -s . -o output.txt --exclude-extensions .pyc .log
```

### Directory and Pattern Exclusions

```bash
# Exclude specific directories
m1f -s . -o output.txt --excludes "tests/" "docs/"

# Exclude patterns
m1f -s . -o output.txt --excludes "*.test.js" "*/tmp/*"

# Use gitignore file
m1f -s . -o output.txt --exclude-paths-file .gitignore
```

### Output Formatting

```bash
# Markdown format
m1f -s . -o output.md --separator-style Markdown

# Machine-readable JSON metadata
m1f -s . -o output.txt --separator-style MachineReadable

# No separators
m1f -s . -o output.txt --separator-style None
```

### Size Management

```bash
# Skip large files
m1f -s . -o output.txt --max-file-size 100KB

# Include only small text files
m1f -s . -o small.txt --max-file-size 50KB --include-extensions .txt .md
```

### Archive Creation

```bash
# Create zip backup
m1f -s . -o output.txt --create-archive

# Create tar.gz backup
m1f -s . -o output.txt --create-archive --archive-type tar.gz
```

### Using Presets

```bash
# Use single preset
m1f -s . -o output.txt --preset wordpress.m1f-presets.yml

# Use preset group
m1f -s . -o output.txt --preset web.yml --preset-group frontend

# Multiple presets (merged in order)
m1f -s . -o output.txt --preset base.yml project.yml
```

## Common Patterns

### Documentation Bundle

```bash
m1f -s ./docs -o documentation.txt \
    --include-extensions .md .rst .txt \
    --separator-style Markdown
```

### Source Code Bundle

```bash
m1f -s ./src -o source-code.txt \
    --include-extensions .py .js .ts .jsx .tsx \
    --excludes "*.test.*" "*.spec.*" \
    --max-file-size 500KB
```

### WordPress Theme/Plugin

```bash
m1f -s ./wp-content/themes/mytheme -o theme.txt \
    --include-extensions .php .js .css \
    --excludes "node_modules/" "vendor/" \
    --preset presets/wordpress.m1f-presets.yml
```

### Clean Documentation Export

```bash
m1f -s ./scraped_docs -o clean-docs.txt \
    --include-extensions .md \
    --remove-scraped-metadata \
    --separator-style Markdown
```

### Multiple Exclude/Include Files

```bash
# Multiple exclude files (merged)
m1f -s . -o output.txt \
    --exclude-paths-file .gitignore .dockerignore custom-excludes.txt

# Whitelist mode with include files
m1f -s . -o api-bundle.txt \
    --include-paths-file api-files.txt core-files.txt \
    --exclude-paths-file .gitignore
```

### Working with File Lists (-i)

```bash
# Single input file
m1f -s . -i files.txt -o output.txt

# Merge multiple file lists (Bash)
m1f -s . -i <(cat critical.txt important.txt nice-to-have.txt) -o output.txt

# Combine with filters (input files bypass filters)
m1f -s . -i must-include.txt -o output.txt \
    --exclude-paths-file .gitignore
```

### CI/CD Integration

```bash
# Create timestamped output
m1f -s . -o build.txt -t

# Minimal output for automation
m1f -s . -o output.txt --minimal-output --quiet

# With security check
m1f -s . -o output.txt --security-check abort
```

## Quick Option Reference

| Short | Long                 | Purpose                   |
| ----- | -------------------- | ------------------------- |
| `-s`  | `--source-directory` | Source directory          |
| `-i`  | `--input-file`       | File list input           |
| `-o`  | `--output-file`      | Output file (required)    |
| `-f`  | `--force`            | Overwrite existing        |
| `-t`  | `--add-timestamp`    | Add timestamp to filename |
| `-v`  | `--verbose`          | Detailed output           |
| `-q`  | `--quiet`            | Suppress output           |

## Separator Styles

- **Standard**: Simple filename separator
- **Detailed**: Full metadata (default)
- **Markdown**: Markdown formatting
- **MachineReadable**: JSON metadata
- **None**: No separators

## Size Units

- `B`: Bytes
- `KB`: Kilobytes (1024 bytes)
- `MB`: Megabytes
- `GB`: Gigabytes

Example: `--max-file-size 1.5MB`

## Exit on Success

```bash
m1f -s . -o output.txt && echo "Success!"
```

## Aliases Setup

Add to your shell profile:

```bash
alias m1f='python /path/to/m1f/tools/m1f.py'
alias m1f-docs='m1f -s . -o docs.txt --include-extensions .md .txt'
alias m1f-code='m1f -s . -o code.txt --include-extensions .py .js'
```

## Need Help?

- Full options: `m1f --help`
- [Complete CLI Reference](./02_cli_reference.md)
- [Troubleshooting Guide](./03_troubleshooting.md)
- [Preset Documentation](./10_m1f_presets.md)
