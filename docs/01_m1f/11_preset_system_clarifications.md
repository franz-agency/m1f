# Preset System Clarifications and Notes

This document clarifies important aspects of the m1f preset system that may not
be immediately obvious from the main documentation.

## Command Invocation

Both module and direct script invocation are supported:

```bash
# Module invocation (recommended):
python -m tools.m1f -s . -o out.txt --preset my-preset.yml

# Direct script invocation (alternative):
python tools/m1f.py -s . -o out.txt --preset my-preset.yml
```

## Pattern Matching Limitations

### Exclude Patterns

Exclude patterns with `!` prefix (e.g., `!*.min.js`) are **not currently
supported** in the `patterns` field of presets. To exclude files, use one of
these approaches:

1. **Global Settings Approach** (Recommended):

   ```yaml
   globals:
     global_settings:
       exclude_patterns: ["*.min.js", "*.map", "dist/**/*"]
   ```

2. **CLI Arguments**:
   ```bash
   python tools/m1f.py -s . -o out.txt --exclude-patterns "*.min.js" "*.map"
   ```

## Settings Hierarchy

Understanding where settings can be applied is crucial:

### 1. Global Settings Level

Available in `globals.global_settings`:

- `include_patterns` / `exclude_patterns`
- `include_extensions` / `exclude_extensions`
- `security_check`
- `max_file_size`
- All other general m1f settings

### 2. Preset Level

Available in individual presets:

- `patterns` (for matching files)
- `extensions` (for matching files)
- `actions` (processing actions)
- `strip_tags` / `preserve_tags` (for strip_tags action)
- `separator_style`
- `include_metadata`
- `max_lines`
- `custom_processor` / `processor_args`
- Override settings: `security_check`, `max_file_size`, etc.

### 3. Extension-Specific Global Settings

Available in `globals.global_settings.extensions.{extension}`:

- All preset-level settings can be applied per extension globally

## Built-in vs Example Processors

### Currently Implemented Custom Processors:

- `truncate` - Limits file content by lines or characters
- `redact_secrets` - Removes sensitive information using regex patterns
- `extract_functions` - Extracts Python function definitions

### Example/Future Processors (Not Implemented):

- `extract_code_cells` - Would extract code cells from Jupyter notebooks
- Any other custom processors mentioned in examples

To implement a custom processor, you would need to add it to the
`tools/m1f/presets.py` file.

## Common Misconceptions

### 1. Exclude Patterns in Presets

**Incorrect**:

```yaml
presets:
  my_preset:
    exclude_patterns: ["*.min.js"] # This doesn't work here
```

**Correct**:

```yaml
globals:
  global_settings:
    exclude_patterns: ["*.min.js"] # Works here
```

### 2. Action vs Setting

Some features are actions (in the `actions` list), while others are settings:

**Actions** (go in `actions` list):

- `minify`
- `strip_tags`
- `strip_comments`
- `compress_whitespace`
- `remove_empty_lines`
- `custom`

**Settings** (separate fields):

- `strip_tags: ["script", "style"]` (which tags to strip)
- `preserve_tags: ["pre", "code"]` (which tags to keep)
- `max_lines: 100` (truncation setting)
- `separator_style: "Markdown"` (output format)

### 3. Pattern Base Path

When using `base_path` at the group level, it affects all patterns in that
group:

```yaml
my_group:
  base_path: "src"
  presets:
    components:
      patterns: ["components/*.js"] # Actually matches: src/components/*.js
```

## Best Practices

1. **Test with Verbose Mode**: Always test new presets with `--verbose` to see
   which files match which presets.

2. **Use Priority Wisely**: Higher priority groups are checked first. Use this
   to create override rules.

3. **Combine Multiple Files**: Layer preset files for maximum flexibility:

   ```bash
   python tools/m1f.py -s . -o out.txt \
     --preset company-defaults.yml \
     --preset project-specific.yml \
     --preset local-overrides.yml
   ```

4. **Document Your Presets**: Always add descriptions to explain the purpose of
   each preset group.

## Debugging Tips

### Check What's Applied

```bash
python tools/m1f.py -s . -o out.txt --preset my.yml --verbose 2>&1 | grep "Applying preset"
```

### Validate YAML

```bash
python -c "import yaml; yaml.safe_load(open('my-preset.yml'))"
```

### Test Small First

Create a test directory with a few files to verify preset behavior before
running on large codebases.

## Version Information

This documentation is accurate as of m1f version 3.2.0.
