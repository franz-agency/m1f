# m1f Auto-Generated Bundles

This directory contains auto-generated bundle files created by the m1f tool's auto-bundle feature.

## About These Files

- All files in this directory are automatically generated based on the `.m1f.config.yml` configuration
- They are regenerated during the git pre-commit hook to ensure they stay up-to-date
- These files are included in version control by default to support Claude Code and other AI tools that cannot access dot-directories

## Configuration

The bundles in this directory are configured in the `.m1f.config.yml` file in the project root.

## Usage with AI Tools

These bundles can be referenced directly in AI tools like Claude Code:
```
@m1f/bundle-name.txt
```

## Adding to .gitignore (Optional)

If you prefer not to track these auto-generated files in your repository, you can add this directory to your `.gitignore`:
```
m1f/
```

However, note that this will make the bundles unavailable to AI tools that cannot access files outside of version control.

## Regenerating Bundles

To manually regenerate all bundles:
```bash
m1f auto-bundle
# or
python -m tools.m1f auto-bundle
```

To regenerate a specific bundle:
```bash
m1f auto-bundle <bundle-name>
# or
python -m tools.m1f auto-bundle <bundle-name>
```

To list all available bundles:
```bash
m1f auto-bundle --list
# or
python -m tools.m1f auto-bundle --list
```

To regenerate bundles by group:
```bash
m1f auto-bundle --group <group-name>
# or
python -m tools.m1f auto-bundle --group <group-name>
```