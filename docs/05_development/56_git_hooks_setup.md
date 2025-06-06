# m1f Git Hooks Setup Guide

This guide explains how to set up Git hooks for automatic m1f bundle generation
in your projects.

## Overview

The m1f Git pre-commit hook automatically runs `m1f auto-bundle` before each
commit, ensuring that your bundled files are always up-to-date with your source
code.

## Features

- **Automatic bundle generation** - Bundles are regenerated on every commit
- **Fail-safe commits** - Commits are blocked if bundle generation fails
- **Auto-staging** - Generated bundles in the `m1f/` directory are automatically
  added to commits
- **Conditional execution** - Only runs if `.m1f.config.yml` exists in your
  project

## Installation

### Method 1: Using the Installation Script (Recommended)

1. Navigate to your project root (where `.m1f.config.yml` is located)
2. Run the installation script:

```bash
# Download and run the installation script
curl -sSL https://raw.githubusercontent.com/franzundfranz/m1f/main/scripts/install-git-hooks.sh | bash

# Or if you have the m1f repository cloned
bash /path/to/m1f/scripts/install-git-hooks.sh
```

The script will:

- Check if you're in a Git repository
- Install the pre-commit hook
- Backup any existing pre-commit hook
- Make the hook executable

### Method 2: Manual Installation

1. Create the pre-commit hook file:

```bash
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# m1f Auto-Bundle Git Pre-Commit Hook

if [ -f ".m1f.config.yml" ]; then
    if ! command -v m1f &> /dev/null; then
        echo "Error: m1f command not found!"
        echo "Please install m1f: pip install m1f"
        exit 1
    fi

    echo "Running m1f auto-bundle..."
    if m1f auto-bundle; then
        echo "Auto-bundle completed successfully."
        [ -d "m1f" ] && git add m1f/*
    else
        echo "Auto-bundle failed. Please fix the issues before committing."
        exit 1
    fi
fi
exit 0
EOF
```

2. Make it executable:

```bash
chmod +x .git/hooks/pre-commit
```

## How It Works

When you run `git commit`, the pre-commit hook:

1. Checks if `.m1f.config.yml` exists in your repository
2. Verifies that the `m1f` command is available
3. If both conditions are met, runs `m1f auto-bundle`
4. If bundle generation succeeds:
   - Adds all files in the `m1f/` directory to the commit
   - Allows the commit to proceed
5. If bundle generation fails:
   - Displays the error message
   - Blocks the commit
   - You must fix the issues before committing

## Usage

Once installed, the hook works automatically:

```bash
# Normal commit - bundles are generated automatically
git add your-files.py
git commit -m "feat: add new feature"

# Skip the hook if needed
git commit --no-verify -m "wip: quick save"
```

## Troubleshooting

### Hook not running

1. Check if the hook is executable:

   ```bash
   ls -la .git/hooks/pre-commit
   ```

2. Make it executable if needed:
   ```bash
   chmod +x .git/hooks/pre-commit
   ```

### Bundle generation fails

1. Run auto-bundle manually to see the error:

   ```bash
   m1f auto-bundle
   ```

2. Fix any issues in your `.m1f.config.yml`

3. Try committing again

### m1f command not found

If you get "m1f command not found", ensure m1f is installed:

```bash
pip install m1f
# or for development
pip install -e /path/to/m1f
```

### Disable the hook temporarily

Use the `--no-verify` flag:

```bash
git commit --no-verify -m "your message"
```

### Remove the hook

To uninstall the pre-commit hook:

```bash
rm .git/hooks/pre-commit
```

## Best Practices

1. **Include m1f/ in version control** - This ensures bundled files are
   available to all team members and AI tools

2. **Review bundle changes** - Check the generated bundles in your diffs before
   committing

3. **Keep bundles focused** - Configure smaller, specific bundles rather than
   one large bundle

4. **Use bundle groups** - Organize related bundles into groups for better
   management

## Example Workflow

1. Set up your project with m1f:

   ```bash
   m1f-link  # Create documentation symlink
   ```

2. Create `.m1f.config.yml`:

   ```yaml
   bundles:
     project-docs:
       description: "Project documentation"
       output: "m1f/docs.txt"
       sources:
         - path: "docs"
           include_extensions: [".md"]
   ```

3. Install the Git hook:

   ```bash
   bash /path/to/m1f/scripts/install-git-hooks.sh
   ```

4. Work normally - bundles update automatically:
   ```bash
   echo "# New Feature" > docs/feature.md
   git add docs/feature.md
   git commit -m "docs: add feature documentation"
   # Bundle is regenerated and included in the commit
   ```

## Integration with CI/CD

The pre-commit hook ensures local development stays in sync. For CI/CD
pipelines, you can also run auto-bundle as a build step:

```yaml
# GitHub Actions example
- name: Install m1f
  run: pip install m1f

- name: Generate m1f bundles
  run: m1f auto-bundle
```

```bash
# GitLab CI example
before_script:
  - pip install m1f

bundle:
  script:
    - m1f auto-bundle
```

## See Also

- [Auto-Bundle Guide](../01_m1f/06_auto_bundle_guide.md) - Complete auto-bundle
  documentation
- [m1f Configuration](../01_m1f/02_m1f_presets.md) - Preset system documentation
- [Quick Reference](../01_m1f/09_quick_reference.md) - Common m1f commands
