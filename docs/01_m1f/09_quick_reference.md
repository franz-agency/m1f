# m1f Quick Reference

## Most Common Commands

### Basic File Combination

```bash
# Combine all files in current directory
python tools/m1f.py -s . -o output.txt

# Combine specific directory
python tools/m1f.py -s ./src -o bundle.txt

# Force overwrite existing output
python tools/m1f.py -s . -o output.txt -f
```

### File Type Filtering

```bash
# Only Python files
python tools/m1f.py -s . -o code.txt --include-extensions .py

# Multiple file types
python tools/m1f.py -s . -o docs.txt --include-extensions .md .txt .rst

# Exclude certain types
python tools/m1f.py -s . -o output.txt --exclude-extensions .pyc .log
```

### Directory and Pattern Exclusions

```bash
# Exclude specific directories
python tools/m1f.py -s . -o output.txt --excludes "tests/" "docs/"

# Exclude patterns
python tools/m1f.py -s . -o output.txt --excludes "*.test.js" "*/tmp/*"

# Use gitignore file
python tools/m1f.py -s . -o output.txt --exclude-paths-file .gitignore
```

### Output Formatting

```bash
# Markdown format
python tools/m1f.py -s . -o output.md --separator-style Markdown

# Machine-readable JSON metadata
python tools/m1f.py -s . -o output.txt --separator-style MachineReadable

# No separators
python tools/m1f.py -s . -o output.txt --separator-style None
```

### Size Management

```bash
# Skip large files
python tools/m1f.py -s . -o output.txt --max-file-size 100KB

# Include only small text files
python tools/m1f.py -s . -o small.txt --max-file-size 50KB --include-extensions .txt .md
```

### Archive Creation

```bash
# Create zip backup
python tools/m1f.py -s . -o output.txt --create-archive

# Create tar.gz backup
python tools/m1f.py -s . -o output.txt --create-archive --archive-type tar.gz
```

### Using Presets

```bash
# Use single preset
python tools/m1f.py -s . -o output.txt --preset wordpress.m1f-presets.yml

# Use preset group
python tools/m1f.py -s . -o output.txt --preset web.yml --preset-group frontend

# Multiple presets (merged in order)
python tools/m1f.py -s . -o output.txt --preset base.yml project.yml
```

## Common Patterns

### Documentation Bundle

```bash
python tools/m1f.py -s ./docs -o documentation.txt \
    --include-extensions .md .rst .txt \
    --separator-style Markdown
```

### Source Code Bundle

```bash
python tools/m1f.py -s ./src -o source-code.txt \
    --include-extensions .py .js .ts .jsx .tsx \
    --excludes "*.test.*" "*.spec.*" \
    --max-file-size 500KB
```

### WordPress Theme/Plugin

```bash
python tools/m1f.py -s ./wp-content/themes/mytheme -o theme.txt \
    --include-extensions .php .js .css \
    --excludes "node_modules/" "vendor/" \
    --preset presets/wordpress.m1f-presets.yml
```

### Clean Documentation Export

```bash
python tools/m1f.py -s ./scraped_docs -o clean-docs.txt \
    --include-extensions .md \
    --remove-scraped-metadata \
    --separator-style Markdown
```

### CI/CD Integration

```bash
# Create timestamped output
python tools/m1f.py -s . -o build.txt -t

# Minimal output for automation
python tools/m1f.py -s . -o output.txt --minimal-output --quiet

# With security check
python tools/m1f.py -s . -o output.txt --security-check abort
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
python tools/m1f.py -s . -o output.txt && echo "Success!"
```

## Aliases Setup

Add to your shell profile:

```bash
alias m1f='python /path/to/m1f/tools/m1f.py'
alias m1f-docs='m1f -s . -o docs.txt --include-extensions .md .txt'
alias m1f-code='m1f -s . -o code.txt --include-extensions .py .js'
```

## Need Help?

- Full options: `python tools/m1f.py --help`
- [Complete CLI Reference](./07_cli_reference.md)
- [Troubleshooting Guide](./08_troubleshooting.md)
- [Preset Documentation](./02_m1f_presets.md)
