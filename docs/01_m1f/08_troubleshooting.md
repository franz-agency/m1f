# Troubleshooting Guide

This guide covers common issues and error messages you might encounter when
using m1f.

## Common Issues

### Module Import Error

**Problem**: Running `python -m tools.m1f` results in:

```
ModuleNotFoundError: No module named 'm1f'
```

**Solution**: Use the direct script invocation instead:

```bash
python tools/m1f.py [options]
```

Or set up the alias as described in the
[Development Workflow](./04_m1f_development_workflow.md).

### Permission Denied

**Problem**: Error when trying to write output file:

```
PermissionError: [Errno 13] Permission denied: '/path/to/output.txt'
```

**Solutions**:

1. Check write permissions in the output directory
2. Use a different output location
3. Run with appropriate permissions (avoid using sudo unless necessary)

### File Not Found

**Problem**: Source directory or input file not found.

**Solutions**:

1. Verify the path exists: `ls -la /path/to/source`
2. Use absolute paths to avoid confusion
3. Check for typos in the path

### Encoding Errors

**Problem**: `UnicodeDecodeError` when processing files.

**Solutions**:

1. Use `--convert-to-charset utf-8` to force UTF-8 encoding
2. Skip problematic files with proper exclusion patterns
3. Use `--abort-on-encoding-error` to identify problematic files

Example:

```bash
python tools/m1f.py -s . -o output.txt --convert-to-charset utf-8
```

### Memory Issues with Large Projects

**Problem**: Memory usage is too high or process is killed.

**Solutions**:

1. Use `--max-file-size` to limit individual file sizes
2. Process specific directories instead of entire project
3. Use `--include-extensions` to limit file types
4. Enable minimal output mode: `--minimal-output`

Example:

```bash
python tools/m1f.py -s . -o output.txt --max-file-size 1MB --include-extensions .py .md
```

### Symlink Cycles

**Problem**: Infinite loop when following symlinks.

**Solutions**:

1. Don't use `--include-symlinks` unless necessary
2. Exclude directories with circular symlinks
3. m1f has built-in cycle detection, but it's better to avoid the issue

### Security Check Failures

**Problem**: Files contain sensitive information.

**Solutions**:

1. Review the detected secrets
2. Use `--security-check skip` to skip files with secrets
3. Use `--security-check warn` to include but get warnings
4. Add sensitive files to exclusions

Example:

```bash
python tools/m1f.py -s . -o output.txt --security-check warn --excludes ".env" "config/secrets.yml"
```

## Error Messages

### "Output file already exists"

**Meaning**: The specified output file exists and would be overwritten.

**Solution**: Use `-f` or `--force` to overwrite, or choose a different output
filename.

### "No files found to process"

**Meaning**: No files matched the inclusion criteria.

**Solutions**:

1. Check your source directory contains files
2. Verify extension filters aren't too restrictive
3. Check exclusion patterns aren't excluding everything
4. Use `--verbose` to see what's being processed

### "File size exceeds maximum allowed"

**Meaning**: A file is larger than the specified `--max-file-size`.

**Solution**: The file is automatically skipped. Adjust `--max-file-size` if
needed.

### "Failed to create archive"

**Meaning**: Archive creation failed (disk space, permissions, etc.).

**Solutions**:

1. Check available disk space
2. Verify write permissions
3. Try a different archive format
4. Skip archive creation and create output file only

### "Preset file not found"

**Meaning**: The specified preset configuration file doesn't exist.

**Solutions**:

1. Check the preset file path
2. Use absolute paths for preset files
3. Verify preset file exists: `ls -la presets/`

## Performance Optimization

### Slow Processing

**Solutions**:

1. Use `--include-extensions` to limit file types
2. Exclude large directories like `node_modules`
3. Use `--max-file-size` to skip large files
4. Enable minimal output: `--minimal-output`
5. Disable security checks if not needed

### High Memory Usage

**Solutions**:

1. Process smaller directory trees
2. Use file size limits
3. Exclude binary files
4. Process in batches using input file lists

## Debug Mode

For detailed debugging information:

```bash
python tools/m1f.py -s . -o output.txt --verbose
```

This will show:

- Files being processed
- Files being skipped and why
- Processing times
- Detailed error messages

## Getting Help

1. Check the [CLI Reference](./07_cli_reference.md) for parameter details
2. Review [examples in the main documentation](./01_m1f.md#common-use-cases)
3. Check the [preset documentation](./02_m1f_presets.md) for configuration
   issues
4. Report issues at the project repository

## Exit Codes

Understanding exit codes can help in scripting:

- `0`: Success
- `1`: General error
- `2`: Invalid arguments
- `3`: File not found
- `4`: Permission denied
- `5`: Security check failed

Use in scripts:

```bash
if python tools/m1f.py -s . -o output.txt; then
    echo "Success"
else
    echo "Failed with exit code: $?"
fi
```
