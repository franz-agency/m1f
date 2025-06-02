# m1f Development Workflow

This document describes the recommended workflow for developing with m1f and
using it in other projects.

## Overview

The m1f project provides a self-contained development environment with:

- Pre-generated m1f bundles of its own source code
- Shell aliases for convenient access from anywhere
- Symlink system for using m1f documentation in other projects

## Prerequisites

For initial setup instructions, see the [SETUP.md](../../SETUP.md) guide.

## Using m1f in Other Projects

### Method 1: Using Aliases (Recommended)

From any directory, you can use m1f directly:

```bash
cd /path/to/your/project
m1f -s . -o combined.txt
```

### Method 2: Using m1f Bundles in Your Project

1. Navigate to your project:

   ```bash
   cd /path/to/your/project
   ```

2. Create m1f symlink:

   ```bash
   m1f-link
   ```

3. Access m1f documentation and source:

   ```bash
   # View m1f documentation
   cat .m1f/m1f/m1f-documentation.txt

   # View m1f source code
   cat .m1f/m1f/m1f-programs.txt
   ```

## Development Workflow

### When Developing m1f

1. Always work in the development environment:

   ```bash
   cd /path/to/m1f
   source .venv/bin/activate
   ```

2. Test changes directly:

   ```bash
   python tools/m1f.py -s test_dir -o output.txt
   ```

3. Run tests:

   ```bash
   pytest tests/
   ```

4. Update bundle files after significant changes:
   ```bash
   m1f-update
   ```

### When Using m1f in Projects

1. Use the global aliases:

   ```bash
   m1f -s src -o bundle.txt --preset documentation
   ```

2. Or create project-specific configuration:

   ```bash
   # Create .m1f directory in your project
   mkdir .m1f

   # Create m1f preset
   cat > .m1f/project.m1f-presets.yml << 'EOF'
   presets:
     my-bundle:
       source_directory: "."
       include_extensions: [".py", ".md", ".txt"]
       excludes: ["*/node_modules/*", "*/__pycache__/*"]
   EOF

   # Use preset
   m1f --preset .m1f/project.m1f-presets.yml --preset-group my-bundle -o bundle.txt
   ```

## Directory Structure

```
m1f/
├── .m1f/                      # Pre-generated m1f bundles
│   ├── m1f-documentation.txt
│   ├── m1f-programs.txt
│   ├── m1f-tests.txt
│   ├── m1f-allinone.txt
│   └── README.md
├── scripts/
│   ├── update_m1f_files.sh    # Update bundle files
│   └── setup_m1f_aliases.sh   # Setup shell aliases
└── tools/                     # m1f source code
    ├── m1f.py
    ├── s1f.py
    └── html2md.py

your-project/
└── .m1f/
    └── m1f -> /path/to/m1f/.m1f/  # Symlink to m1f bundles
```

## Best Practices

1. **Keep Bundles Updated**: Run `m1f-update` after significant changes to m1f
2. **Use Aliases**: The shell aliases handle virtual environment activation
   automatically
3. **Project Organization**: Keep project-specific m1f configurations in `.m1f/`
   directory
4. **Version Control**: The `.m1f/` directory is already in `.gitignore`

## Troubleshooting

### Aliases Not Working

If aliases don't work after setup:

1. Make sure you've reloaded your shell configuration
2. Check that the aliases were added to your shell config file
3. Verify the m1f project path is correct in the aliases

### Virtual Environment Issues

The aliases automatically activate the virtual environment. If you encounter
issues:

1. Ensure the virtual environment exists at `/path/to/m1f/.venv`
2. Check that all dependencies are installed

### Symlink Issues

If `m1f-link` fails:

1. Ensure you have write permissions in the current directory
2. Check that the m1f project path is accessible
3. Remove any existing `.m1f/m1f` symlink and try again

## Advanced Usage

### Custom Bundle Generation

Create custom bundles for specific use cases:

```bash
# Bundle only specific file types
m1f -s /path/to/project -o api-docs.txt \
    --include-extensions .py .yaml \
    --excludes "*/tests/*" \
    --separator-style Markdown

# Create compressed archive
m1f -s . -o project.txt --create-archive --archive-type tar.gz
```

### Integration with CI/CD

Add m1f to your CI pipeline:

```yaml
# Example GitHub Actions
- name: Generate Documentation Bundle
  run: |
    python tools/m1f.py -s docs -o docs-bundle.txt

- name: Upload Bundle
  uses: actions/upload-artifact@v2
  with:
    name: documentation
    path: docs-bundle.txt
```
