# AI Context File Generator

## Overview

This directory contains tasks for creating selective file bundles that serve as
context for AI interactions. Using the `makeonefile.py` tool, you can combine
selected important files from your project into a single file that can be loaded
into an AI's context window.

## When to Use This Tool

**Do NOT use this tool if:**

- You only have a few files to work with (just reference them directly)
- You want to include your entire project (this will overwhelm the AI with
  irrelevant information)

**DO use this tool when:**

- You have a large project (hundreds or thousands of files)
- You need to provide context from ~50 key files that are most relevant to your
  current task
- You want to give the AI a focused understanding of specific parts of your
  codebase

## Purpose

When working with AI assistants (like those in Windsurf, Cursor, VS Code, or
other AI-enabled editors), providing selective but sufficient context is
essential. This tool helps you to:

1. Select and combine only the most important files into a single document
2. Include metadata that helps AI systems understand file relationships
3. Create machine-readable formats optimized for Large Language Models
4. Efficiently manage context limitations by focusing on what matters

## Tasks in makeonefile.json

The `makeonefile.json` file defines two VS Code tasks:

### 1. AI Context: Create Combined File

This task combines files from your project with common exclusions:

- **Source**: Project directory with extensive filtering
- **Output**: `.gen/ai_context.m1f.txt`
- **Excludes**: Non-relevant directories (`node_modules`, `.git`, `.venv`, etc.)
- **Format**: Machine-readable format with clear file separators
- **Optimization**: Uses `--minimal-output` to generate only the combined file without extra logs or lists
- **Best for**: Initial exploration when you're unsure which files are important

### 2. AI Context: Create From Input List (Recommended)

This task combines only the specific files you select:

- **Source**: Files explicitly listed in `tasks/ai_context_files.txt`
- **Output**: `.gen/ai_context_custom.m1f.txt`
- **Format**: Same machine-readable format
- **Efficiency**: Uses `--minimal-output --quiet` for silent operation with no auxiliary files
- **Best for**: Focused work when you know which ~20-50 files are most relevant

## Practical Usage Guide

### Step 1: Identify Key Files

Start by identifying the most important files for your current task:

- **Core files**: Main entry points, key modules, and configuration files
- **Relevant to your task**: Files you're actively working on or need to
  understand
- **Context providers**: Files that explain project structure or domain concepts
- **Aim for 20-50 files**: This provides enough context without overwhelming the
  AI

### Step 2: Create Your Custom File List

The recommended approach is to create a task-specific file list in
`ai_context_files.txt`:

```
# Core modules for authentication feature
${workspaceFolder}/auth/user.py
${workspaceFolder}/auth/permissions.py
${workspaceFolder}/auth/tokens.py

# Configuration
${workspaceFolder}/config/settings.py

# Related utilities
${workspaceFolder}/utils/crypto.py
```

### Step 3: Generate the Context File

1. Open Windsurf/VS Code Command Palette (`Ctrl+Shift+P`)
2. Type "Tasks: Run Task" and press Enter
3. Select "AI Context: Create From Input List" (recommended)
4. The task will run and create the output file in the `.gen` directory

### Step 4: Use with AI

1. Open the generated `.m1f.txt` file in your editor
2. In your AI-enabled editor (Windsurf, Cursor, VS Code):
   - Include this file in the AI's context using the editor's method
   - In Windsurf: Type `@filename` in chat or use the "Add to Context" option

## Best Practices for Effective AI Context

1. **Be selective**: Choose only the most important 20-50 files for your current
   task
2. **Include structure files**: Add README.md, configuration files, and key
   interfaces
3. **Group related files**: When customizing your list, organize files by
   related functionality
4. **Refresh context files**: Create new context files for different tasks
   rather than using one for everything
5. **Comment your file lists**: Add comments in `ai_context_files.txt` to
   explain why files are included

## Customizing the Process

You can customize the tasks by editing `makeonefile.json` for your specific
needs:

- Modify output file locations and naming conventions
- Adjust file exclusion patterns for your project structure
- Add task-specific configurations for different project components

## Additional Options

Advanced options available in the `makeonefile.py` script:

- `--include-dot-files`: Include configuration files like `.gitignore` when
  needed
- `--add-timestamp`: Track different versions of context files with timestamps
- `--create-archive`: Create a reference archive of all included files
- `--separator-style`: Choose format for file separators (MachineReadable
  recommended)

For a complete list of options, run:

```
python tools/makeonefile.py --help
```

## Machine-Readable Format

The default separator style "MachineReadable" optimizes the combined file for AI
understanding:

```
# ===============================================================================
# FILE: auth/user.py
# ===============================================================================
# METADATA: {"modified": "2023-01-01 12:00:00", "type": ".py", "size_bytes": 1234}
# -------------------------------------------------------------------------------

[file content]

# ===============================================================================
# END FILE
# ===============================================================================
```

This format ensures the AI can clearly identify file boundaries and understand
metadata about each file, making it more effective in processing your selected
files.

## Author

Franz und Franz - https://franz.agency

## Example: WordPress Theme Development

This example shows how to use the AI context generator for WordPress theme and plugin development.

### Setup: Create a Directory for AI Context Files

1. First, create a dedicated directory for your AI context files in your project root:

```bash
mkdir -p .ai-context
```

2. Add this directory to your `.gitignore` file to avoid committing potentially large context files:

```bash
# Add to .gitignore
.ai-context/
```

### WordPress Structured Include/Exclude Files

For WordPress development, we've created specialized include and exclude files:

- `tasks/wp_theme_includes.txt`: Common WordPress theme files and patterns
- `tasks/wp_plugin_includes.txt`: Common WordPress plugin files and patterns
- `tasks/wp_excludes.txt`: WordPress-specific paths and files to exclude

These files contain well-structured paths with common WordPress conventions and can be easily customized for your specific project.

### Creating WordPress Theme and Plugin Contexts

Let's say you're developing both a custom theme "mytheme" and a plugin "myplugin" for a WordPress project:

#### Theme Context

Use this task to generate a context file with just your theme files:

```json
{
    "label": "WordPress: Generate Theme Context",
    "type": "shell",
    "command": "python",
    "args": [
        "${workspaceFolder}/tools/makeonefile.py",
        "--source-directory",
        "${workspaceFolder}/wp-content/themes/mytheme",
        "--exclude-paths-file",
        "${workspaceFolder}/tasks/wp_excludes.txt",
        "--output-file",
        "${workspaceFolder}/.ai-context/mytheme.m1f.txt",
        "--separator-style",
        "MachineReadable",
        "--force",
        "--minimal-output",
        "--quiet"
    ]
}
```

#### Plugin Context

Use this task to generate a context file with just your plugin files:

```json
{
    "label": "WordPress: Generate Plugin Context",
    "type": "shell",
    "command": "python",
    "args": [
        "${workspaceFolder}/tools/makeonefile.py",
        "--source-directory",
        "${workspaceFolder}/wp-content/plugins/myplugin",
        "--exclude-paths-file",
        "${workspaceFolder}/tasks/wp_excludes.txt",
        "--output-file",
        "${workspaceFolder}/.ai-context/myplugin.m1f.txt",
        "--separator-style",
        "MachineReadable",
        "--force",
        "--minimal-output",
        "--quiet"
    ]
}
```

#### Combined Theme and Plugin Context

This task combines both your theme and plugin files for a complete project context:

```json
{
    "label": "WordPress: Generate Both Theme and Plugin Context",
    "type": "shell",
    "command": "python",
    "args": [
        "${workspaceFolder}/tools/makeonefile.py",
        "--input-file",
        "${workspaceFolder}/tasks/wp_theme_includes.txt",
        "${workspaceFolder}/tasks/wp_plugin_includes.txt",
        "--exclude-paths-file",
        "${workspaceFolder}/tasks/wp_excludes.txt",
        "--output-file",
        "${workspaceFolder}/.ai-context/wordpress_project.m1f.txt",
        "--separator-style",
        "MachineReadable",
        "--force",
        "--minimal-output",
        "--quiet"
    ]
}
```

### Running the Tasks

1. Open VS Code Command Palette (`Ctrl+Shift+P`)
2. Type "Tasks: Run Task" and press Enter
3. Select one of the WordPress tasks:
   - "WordPress: Generate Theme Context" - for theme-only work
   - "WordPress: Generate Plugin Context" - for plugin-only work
   - "WordPress: Generate Both Theme and Plugin Context" - for the complete project

### Keeping the Context Updated

To ensure your AI context stays up-to-date with your WordPress development:

1. **Automatic Updates**: Configure VS Code to run the task on file save:

   ```json
   "runOptions": {
       "runOn": "folderOpen"
   }
   ```

2. **Update on Demand**: Run the appropriate task after making significant changes.

3. **Feature-Specific Work**: Create specialized include files for different parts of your project:
   - Templates and theme structure
   - Plugin admin dashboard functionality
   - WooCommerce integration features
   - Custom post types and taxonomies

### Using with AI Assistants

When getting AI help with your WordPress development:

1. Load the appropriate context file depending on what you're working on
2. Ask specific questions about your code, theme structure, or plugin functionality
3. Generate hooks, filters, and template implementations based on WordPress standards
4. Troubleshoot theme/plugin conflicts or integration issues

This approach ensures your AI assistant understands your WordPress project structure while maintaining clean, organized context files.
