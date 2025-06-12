# Auto-Bundle Guide

The m1f auto-bundle feature allows you to automatically generate predefined
bundles of files based on configuration. This is especially useful for
maintaining consistent documentation bundles, creating project snapshots, and
managing multiple projects on a server.

## Configuration File

Auto-bundle looks for a `.m1f.config.yml` file in your project. The tool
searches from the current directory upward to the root, allowing flexible
project organization.

### Basic Configuration Structure

```yaml
# .m1f.config.yml

# Global settings that apply to all bundles
global:
  global_excludes:
    - "**/*.pyc"
    - "**/*.log"
    - "**/tmp/**"

# Bundle definitions
bundles:
  docs:
    description: "Project documentation"
    output: "m1f/docs/manual.txt"
    sources:
      - path: "docs"
        include_extensions: [".md", ".txt"]

  code:
    description: "Source code bundle"
    output: "m1f/src/code.txt"
    sources:
      - path: "src"
        include_extensions: [".py", ".js", ".ts"]
```

## Command Usage

### Create All Bundles

```bash
m1f auto-bundle
# Or use the convenient alias:
m1f-update
```

### Create Specific Bundle

```bash
m1f auto-bundle docs
# Or use the convenient alias:
m1f-update docs
```

### List Available Bundles

```bash
m1f auto-bundle --list
```

### Create Bundles by Group

```bash
m1f auto-bundle --group documentation
# Or use the convenient alias:
m1f-update --group documentation
```

**Note**: The `m1f-update` command is a convenient alias for `m1f auto-bundle` that provides a simpler way to regenerate bundles.

## Bundle Groups

You can organize bundles into groups for easier management:

```yaml
bundles:
  user-docs:
    description: "User documentation"
    group: "documentation"
    output: "m1f/docs/user.txt"
    sources:
      - path: "docs/user"

  api-docs:
    description: "API documentation"
    group: "documentation"
    output: "m1f/docs/api.txt"
    sources:
      - path: "docs/api"

  frontend-code:
    description: "Frontend source code"
    group: "source"
    output: "m1f/src/frontend.txt"
    sources:
      - path: "frontend"
```

Then create all documentation bundles:

```bash
m1f auto-bundle --group documentation
```

## Server-Wide Usage

### Managing Multiple Projects

For server environments with multiple projects, you can create a management
script:

```bash
#!/bin/bash
# update-all-bundles.sh

# Find all projects with .m1f.config.yml
for config in $(find /home/projects -name ".m1f.config.yml" -type f); do
    project_dir=$(dirname "$config")
    echo "Updating bundles in: $project_dir"

    cd "$project_dir"
    m1f-update --quiet
done
```

### Project-Specific Bundles

Create project-specific configurations by using groups:

```yaml
# Project A - .m1f.config.yml
bundles:
  all:
    description: "Complete project bundle"
    group: "project-a"
    output: "m1f/project-a-complete.txt"
    sources:
      - path: "."
```

Then update only specific projects:

```bash
cd /path/to/project-a
m1f-update --group project-a
```

### Automated Bundle Updates

Set up a cron job for automatic updates:

```bash
# Update all project bundles daily at 2 AM
0 2 * * * /usr/local/bin/update-all-bundles.sh
```

### Centralized Bundle Storage

Configure bundles to output to a central location:

```yaml
bundles:
  project-bundle:
    description: "Project bundle for central storage"
    output: "/var/m1f-bundles/myproject/latest.txt"
    sources:
      - path: "."
```

## Advanced Features

### Conditional Bundles

Enable bundles only when specific files exist:

```yaml
bundles:
  python-docs:
    description: "Python documentation"
    enabled_if_exists: "setup.py"
    output: "m1f/python-docs.txt"
    sources:
      - path: "."
        include_extensions: [".py"]
```

### Multiple Source Configurations

Combine files from different locations with different settings:

```yaml
bundles:
  complete:
    description: "Complete project documentation"
    output: "m1f/complete.txt"
    sources:
      - path: "docs"
        include_extensions: [".md"]
      - path: "src"
        include_extensions: [".py"]
        excludes: ["**/test_*.py"]
      - path: "."
        include_files: ["README.md", "CHANGELOG.md"]
```

### Using Presets

Apply presets for advanced file processing:

```yaml
bundles:
  web-bundle:
    description: "Web project bundle"
    output: "m1f/web.txt"
    preset: "presets/web-project.m1f-presets.yml"
    preset_group: "production"
    sources:
      - path: "."
```

## Automatic Bundle Generation with Git Hooks

m1f provides a Git pre-commit hook that automatically runs auto-bundle before
each commit. This ensures your bundles are always in sync with your source code.

### Installing the Git Hook

```bash
# Run from your project root (where .m1f.config.yml is located)
bash /path/to/m1f/scripts/install-git-hooks.sh
```

The hook will:

- Run `m1f-update` before each commit
- Add generated bundles to the commit automatically
- Block commits if bundle generation fails

For detailed setup instructions, see the
[Git Hooks Setup Guide](../05_development/56_git_hooks_setup.md).

## Best Practices

1. **Organize with Groups**: Use groups to categorize bundles logically
2. **Version Control**: Include `.m1f.config.yml` in version control
3. **Include m1f/ Directory**: Keep generated bundles in version control for AI
   tool access
4. **Use Descriptive Names**: Make bundle names self-explanatory
5. **Regular Updates**: Use Git hooks or schedule automatic updates for
   frequently changing projects
6. **Review Bundle Changes**: Check generated bundle diffs before committing

## Troubleshooting

### Config Not Found

If you see "No .m1f.config.yml configuration found!", the tool couldn't find a
config file searching from the current directory up to the root. Create a
`.m1f.config.yml` in your project root.

### Bundle Not Created

Check the verbose output:

```bash
m1f-update --verbose
```

Common issues:

- Incorrect file paths
- Missing source directories
- Invalid YAML syntax
- Disabled bundles

### Group Not Found

If using `--group` and no bundles are found:

1. Check that bundles have the `group` field
2. Verify the group name matches exactly
3. Use `--list` to see available groups

## Examples

### Documentation Site Bundle

```yaml
bundles:
  docs-site:
    description: "Documentation site content"
    group: "documentation"
    output: "m1f/docs-site.txt"
    sources:
      - path: "content"
        include_extensions: [".md", ".mdx"]
      - path: "src/components"
        include_extensions: [".jsx", ".tsx"]
    excludes:
      - "**/node_modules/**"
      - "**/.next/**"
```

### Multi-Language Project

```yaml
bundles:
  python-code:
    description: "Python backend code"
    group: "backend"
    output: "m1f/backend/python.txt"
    sources:
      - path: "backend"
        include_extensions: [".py"]

  javascript-code:
    description: "JavaScript frontend code"
    group: "frontend"
    output: "m1f/frontend/javascript.txt"
    sources:
      - path: "frontend"
        include_extensions: [".js", ".jsx", ".ts", ".tsx"]

  all-code:
    description: "All source code"
    output: "m1f/all-code.txt"
    sources:
      - path: "."
        include_extensions: [".py", ".js", ".jsx", ".ts", ".tsx"]
```

### WordPress Plugin Bundle

```yaml
bundles:
  wp-plugin:
    description: "WordPress plugin files"
    group: "wordpress"
    output: "m1f/wp-plugin.txt"
    preset: "presets/wordpress.m1f-presets.yml"
    sources:
      - path: "."
        include_extensions: [".php", ".js", ".css"]
    excludes:
      - "**/vendor/**"
      - "**/node_modules/**"
```
