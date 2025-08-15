# m1f Git Hooks Setup Guide

This guide explains how to set up Git hooks for automatic m1f bundle generation
and code formatting in your projects.

## Overview

m1f provides two types of Git pre-commit hooks:

1. **Internal Hook** - For m1f project development

   - Formats Python files with Black
   - Formats Markdown files with Prettier
   - Runs m1f auto-bundle

2. **External Hook** - For projects using m1f
   - Runs m1f auto-bundle when `.m1f.config.yml` exists

Both hooks support Linux, macOS, and Windows platforms.

## Features

- **Automatic bundle generation** - Bundles are regenerated on every commit
- **Code formatting** (internal hook only) - Python and Markdown files are
  auto-formatted
- **Cross-platform support** - Works on Linux, macOS, and Windows
- **Fail-safe commits** - Commits are blocked if bundle generation fails
- **Auto-staging** - Modified files are automatically staged
- **Smart detection** - Automatically detects project type and suggests
  appropriate hook

## Installation

### Prerequisites

You must have m1f installed locally before setting up Git hooks:

```bash
# Clone m1f repository
git clone https://github.com/franz-agency/m1f.git
cd m1f

# Install m1f using the installation script
# Linux/macOS:
./scripts/install.sh

# Windows PowerShell:
.\scripts\install.ps1
```

### Quick Installation

#### Linux/macOS

```bash
# Run from your project directory (not the m1f directory)
bash /path/to/m1f/scripts/install-git-hooks.sh
```

#### Windows (PowerShell)

```powershell
# Run from your project directory (not the m1f directory)
& C:\path\to\m1f\scripts\install-git-hooks.ps1
```

### Installation Process

The installer will:

1. **Detect your project type**:

   - If in the m1f project: Offers both internal and external hooks
   - If in another project: Installs external hook

2. **Choose the appropriate hook**:

   - Internal: For m1f contributors (includes formatters)
   - External: For m1f users (auto-bundle only)

3. **Install platform-specific version**:
   - Linux/macOS: Bash script
   - Windows: PowerShell script with Git wrapper

### Manual Installation

If you prefer manual installation:

#### External Hook (for projects using m1f)

```bash
# Create the hook file
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# m1f Git Pre-Commit Hook (External Projects)

if [ ! -f ".m1f.config.yml" ]; then
    echo "No .m1f.config.yml found. Skipping m1f auto-bundle."
    exit 0
fi

if command -v m1f-update &> /dev/null; then
    echo "Running m1f auto-bundle..."
    if m1f-update --quiet; then
        echo "✓ Auto-bundle completed"
        find . -path "*/m1f/*.txt" -type f | while read -r file; do
            git add "$file"
        done
    else
        echo "✗ Auto-bundle failed"
        exit 1
    fi
fi
exit 0
EOF

# Make it executable
chmod +x .git/hooks/pre-commit
```

## How It Works

### External Hook Workflow

1. Checks if `.m1f.config.yml` exists
2. Verifies m1f is available in PATH
3. Runs `m1f-update` to generate bundles
4. Automatically stages generated bundle files
5. Allows commit to proceed

### Internal Hook Workflow (m1f project only)

1. Formats staged Python files with Black
2. Formats staged Markdown files with Prettier
3. Runs m1f auto-bundle
4. Re-stages all modified files
5. Shows warning about modified files

## Usage Examples

### Normal Usage

```bash
# Make changes to your code
vim src/feature.py

# Stage changes
git add src/feature.py

# Commit - bundles are generated automatically
git commit -m "feat: add new feature"
```

### Skip Hook When Needed

```bash
# Skip all pre-commit hooks
git commit --no-verify -m "wip: quick save"
```

### Check What the Hook Does

```bash
# See hook output without committing
git add .
git commit --dry-run
```

## Platform-Specific Notes

### Windows

On Windows, the installer creates:

- `.git/hooks/pre-commit` - Bash wrapper for Git
- `.git/hooks/pre-commit.ps1` - PowerShell script with actual logic

Both files are needed for proper operation.

### Linux/macOS

The hook is a standard bash script that works with Git's hook system.

## Troubleshooting

### Hook Not Running

1. **Check if hook exists**:

   ```bash
   ls -la .git/hooks/pre-commit*
   ```

2. **Check if executable** (Linux/macOS):

   ```bash
   chmod +x .git/hooks/pre-commit
   ```

3. **Check Git version**:
   ```bash
   git --version  # Should be 2.9+
   ```

### m1f Command Not Found

m1f must be installed using the official installation scripts:

```bash
# Clone m1f if you haven't already
git clone https://github.com/franz-agency/m1f.git
cd m1f

# Install using the appropriate script
# Linux/macOS:
./scripts/install.sh

# Windows PowerShell:
.\scripts\install.ps1
```

The installation script will:

- Create a Python virtual environment
- Install all dependencies
- Add m1f to your PATH
- Set up command aliases

After installation, restart your terminal or reload your shell configuration:

```bash
# Linux/macOS
source ~/.bashrc  # or ~/.zshrc for zsh

# Windows PowerShell
. $PROFILE
```

### Bundle Generation Fails

1. **Run manually to see errors**:

   ```bash
   m1f-update
   ```

2. **Check config syntax**:

   ```bash
   # Validate YAML syntax
   python -c "import yaml; yaml.safe_load(open('.m1f.config.yml'))"
   ```

3. **Check file permissions**:
   ```bash
   # Ensure m1f can write to output directory
   ls -la m1f/
   ```

### Formatter Issues (Internal Hook)

**Black not found**:

```bash
pip install black
```

**Prettier not found**:

```bash
npm install -g prettier
```

## Uninstallation

### Linux/macOS

```bash
rm .git/hooks/pre-commit
```

### Windows

```powershell
Remove-Item .git\hooks\pre-commit
Remove-Item .git\hooks\pre-commit.ps1
```

## Best Practices

1. **Commit bundle files** - Include `m1f/` directory in version control
2. **Review changes** - Check bundle diffs before committing
3. **Keep bundles small** - Use focused bundles for better performance
4. **Use descriptive names** - Name bundles clearly (e.g., `api-docs`,
   `frontend-code`)
5. **Document dependencies** - Note formatter requirements in your README

## Configuration Examples

### Basic Project Setup

```yaml
# .m1f.config.yml
bundles:
  docs:
    description: "Project documentation"
    output: "m1f/docs.txt"
    sources:
      - path: "docs"
        include_extensions: [".md", ".rst"]

  code:
    description: "Source code"
    output: "m1f/code.txt"
    sources:
      - path: "src"
        include_extensions: [".py", ".js"]
```

### Advanced Setup with Groups

```yaml
# .m1f.config.yml
bundles:
  api-docs:
    description: "API documentation"
    group: "documentation"
    output: "m1f/api-docs.txt"
    sources:
      - path: "docs/api"

  api-code:
    description: "API implementation"
    group: "backend"
    output: "m1f/api-code.txt"
    sources:
      - path: "src/api"
```

## Integration with Development Tools

### VS Code

Add to `.vscode/settings.json`:

```json
{
  "git.enableCommitSigning": true,
  "files.exclude": {
    "m1f/**/*.txt": false
  }
}
```

### Pre-commit Framework

If using [pre-commit](https://pre-commit.com/):

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: m1f-bundle
        name: m1f auto-bundle
        entry: m1f-update
        language: system
        pass_filenames: false
        always_run: true
```

## CI/CD Integration

While the Git hook handles local development, you should also run m1f in CI/CD:

### GitHub Actions

```yaml
- name: Setup Python
  uses: actions/setup-python@v4
  with:
    python-version: "3.10"

- name: Clone and install m1f
  run: |
    git clone https://github.com/franz-agency/m1f.git
    cd m1f
    source ./scripts/install.sh
    cd ..

- name: Generate bundles
  run: |
    source m1f/.venv/bin/activate
    m1f-update

- name: Check for changes
  run: |
    git diff --exit-code || (echo "Bundles out of sync!" && exit 1)
```

### GitLab CI

```yaml
bundle-check:
  stage: test
  before_script:
    - git clone https://github.com/franz-agency/m1f.git
    - cd m1f && source ./scripts/install.sh && cd ..
  script:
    - source m1f/.venv/bin/activate
    - m1f-update
    - git diff --exit-code
```

## See Also

- [Auto-Bundle Guide](../01_m1f/20_auto_bundle_guide.md) - Complete auto-bundle
  documentation
- [Configuration Reference](../01_m1f/10_m1f_presets.md) - Detailed
  configuration options
- [Quick Reference](../01_m1f/99_quick_reference.md) - Common m1f commands
