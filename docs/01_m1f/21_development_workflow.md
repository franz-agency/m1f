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

### Method 2: Quick Project Setup with m1f-init

When starting a new project with m1f, use `m1f-init` for quick setup:

```bash
cd /path/to/your/project
m1f-init
```

#### What m1f-init does:

1. **Links m1f documentation** (creates `m1f/m1f.txt`)

   - Makes m1f docs available to AI tools
   - Creates symlink on Linux/macOS, copies on Windows

2. **Analyzes your project**

   - Detects project type and languages
   - Creates file and directory listings

3. **Generates initial bundles with auxiliary files**

   - `m1f/<project>_complete.txt` - Full project bundle
   - `m1f/<project>_complete_filelist.txt` - List of all included files
   - `m1f/<project>_complete_dirlist.txt` - List of all directories
   - `m1f/<project>_docs.txt` - Documentation only bundle
   - `m1f/<project>_docs_filelist.txt` - List of documentation files
   - `m1f/<project>_docs_dirlist.txt` - Documentation directories

4. **Creates basic configuration**
   - Generates `.m1f.config.yml` if not present
   - Sets up sensible defaults

#### Using with AI Tools:

After running `m1f-init`, reference the documentation in your AI tool:

```bash
# For Claude Code, Cursor, or similar AI assistants:
@m1f/m1f.txt

# Example prompts:
"Please read @m1f/m1f.txt and help me create custom bundles
for my Python web application"

"Based on @m1f/m1f.txt, how can I exclude test files
while keeping fixture data?"

"Using @m1f/m1f.txt as reference, help me optimize
my .m1f.config.yml for a React project"
```

#### Advanced Setup (Linux/macOS only):

For topic-specific bundles and Claude-assisted configuration:

```bash
m1f-claude --advanced-setup
```

#### Working with File Lists:

The generated file lists are valuable for customizing bundles:

```bash
# View what files are included
cat m1f/*_filelist.txt | wc -l  # Count total files

# Edit file lists to customize bundles
vi m1f/myproject_complete_filelist.txt
# Remove lines for files you don't want
# Add paths for files you do want

# Create a custom bundle from edited list
m1f -i m1f/myproject_complete_filelist.txt -o m1f/custom.txt

# Combine multiple file lists
cat m1f/*_docs_filelist.txt m1f/api_filelist.txt | sort -u > m1f/combined_list.txt
m1f -i m1f/combined_list.txt -o m1f/docs_and_api.txt
```

This single documentation file contains:

- Complete m1f usage guide and all parameters
- Examples and best practices
- Preset system documentation
- Auto-bundle configuration guide
- All tool documentation (m1f, s1f, html2md, webscraper)

The AI can then:

- Understand all m1f parameters and options
- Help create custom `.m1f.config.yml` configurations
- Suggest appropriate presets for your project type
- Generate complex m1f commands with correct syntax
- Troubleshoot issues based on error messages

## Development Workflow

### When Developing m1f

1. Always work in the development environment:

   ```bash
   cd /path/to/m1f
   source .venv/bin/activate
   ```

2. Test changes directly:

   ```bash
   python -m tools.m1f -s test_dir -o output.txt
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
│   ├── m1f/                   # Tool bundles
│   └── m1f-doc/
│       └── 99_m1fdocs.txt    # Complete documentation
├── bin/                       # Executable commands
│   ├── m1f
│   ├── m1f-s1f
│   ├── m1f-html2md
│   ├── scrape_tool
│   └── ...
├── scripts/
│   ├── install.sh            # Installation script
│   └── watch_and_bundle.sh   # File watcher for auto-bundling
└── tools/                    # m1f source code
    ├── m1f/
    ├── s1f/
    └── html2md/

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
    python -m tools.m1f -s docs -o docs-bundle.txt

- name: Upload Bundle
  uses: actions/upload-artifact@v2
  with:
    name: documentation
    path: docs-bundle.txt
```
