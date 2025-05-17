# AI Context File Generator

## Overview

This directory contains tasks for creating selective file bundles that serve as
context for AI interactions. Using the `m1f.py` tool, you can combine
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

## Tasks in m1f.json

The `m1f.json` file defines two VS Code tasks:

### 1. AI Context: Create Combined File

This task combines files from your project with common exclusions:

- **Source**: Project directory with extensive filtering
- **Output**: `.gen/ai_context.m1f.txt`
- **Excludes**: Non-relevant directories (`node_modules`, `.git`, `.venv`, etc.)
- **Format**: Machine-readable format with clear file separators
- **Optimization**: Uses `--minimal-output` to generate only the combined file
  without extra logs or lists
- **Best for**: Initial exploration when you're unsure which files are important

### 2. AI Context: Create From Input List (Recommended)

This task combines only the specific files you select:

- **Source**: Files explicitly listed in `tasks/ai_context_files.txt`
- **Output**: `.gen/ai_context_custom.m1f.txt`
- **Format**: Same machine-readable format
- **Efficiency**: Uses `--minimal-output --quiet` for silent operation with no
  auxiliary files
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

You can customize the tasks by editing `m1f.json` for your specific
needs:

- Modify output file locations and naming conventions
- Adjust file exclusion patterns for your project structure
- Add task-specific configurations for different project components

## Additional Options

Consider these advanced options from `m1f.py` for specific needs:

- `--include-dot-files`: Useful for including WordPress-specific configuration
  files like `.htaccess` or other dotfiles if they are relevant to your context.
- `--separator-style`: While `MachineReadable` is generally recommended for AI
  context files, you can explore other styles if needed.
- `--skip-output-file`: Executes all operations (logs, additional files, etc.)
  but skips writing the final .m1f.txt output file. Useful when you're only
  interested in generating the file and directory listings or logs, but not the
  combined content file itself.

For a complete list of all available options and their detailed descriptions,
run:

```
python tools/m1f.py --help
```

## Machine-Readable Format

The default separator style "MachineReadable" optimizes the combined file for AI
understanding:

```
--- PYMK1F_BEGIN_FILE_METADATA_BLOCK_f84a9c25-b8cf-4e6a-a39d-842d7fe3b6e1 ---
METADATA_JSON:
{
    "original_filepath": "relative/path.ext",
    "original_filename": "path.ext",
    "timestamp_utc_iso": "2023-01-01T12:00:00Z",
    "type": ".ext",
    "size_bytes": 1234,
    "checksum_sha256": "abc123..."
}
--- PYMK1F_END_FILE_METADATA_BLOCK_f84a9c25-b8cf-4e6a-a39d-842d7fe3b6e1 ---
--- PYMK1F_BEGIN_FILE_CONTENT_BLOCK_f84a9c25-b8cf-4e6a-a39d-842d7fe3b6e1 ---

[file content]

--- PYMK1F_END_FILE_CONTENT_BLOCK_f84a9c25-b8cf-4e6a-a39d-842d7fe3b6e1 ---
```

This format ensures the AI can clearly identify file boundaries and understand
metadata about each file, making it more effective in processing your selected
files. The JSON metadata includes the original filepath, filename, timestamp in
ISO format, file type, size in bytes, and SHA256 checksum for data integrity
verification. It's particularly suitable for automated processing and splitting
back into individual files.

## Author

Franz und Franz - https://franz.agency

## Use Case: WordPress Theme/Plugin Context File

When developing WordPress themes or plugins, you often need to provide an AI
assistant with the context of your specific theme/plugin files. Here's how you
can create a single context file for this purpose using `m1f.py`:

### 1. Strategically Select WordPress Files

To create an effective AI context for WordPress development, carefully select
files that represent the functionality or problem area you're focusing on.
Consider these categories:

- **Core Theme Files**:

  - `style.css` (for theme identity and metadata)
  - `functions.php` (critical for theme logic, hooks, and filters)
  - `index.php`, `header.php`, `footer.php`, `sidebar.php` (main template
    structure)
  - Specific template files relevant to your task: `single.php`, `page.php`,
    `archive.php`, `category.php`, `tag.php`, `search.php`, `404.php`,
    `front-page.php`, `home.php`.
  - Template parts (e.g., files in `template-parts/` directory like
    `content-page.php`).
  - Customizer settings and controls if relevant (`inc/customizer.php`).
  - Key JavaScript (e.g., `assets/js/custom.js`) and CSS files.

- **Core Plugin Files**:

  - The main plugin file (e.g., `your-plugin-name/your-plugin-name.php`) which
    includes the plugin header.
  - Files containing main classes, action/filter hooks, shortcodes, and admin
    panel logic.
  - AJAX handlers, REST API endpoint definitions.
  - Files related to Custom Post Types (CPTs) or taxonomies defined by the
    plugin.
  - Key JavaScript and CSS files specific to the plugin's functionality.

- **Feature-Specific Files**: If you are working on a particular feature (e.g.,
  WooCommerce integration, a custom contact form, a specific admin page):

  - Include all files directly related to that feature from both your theme and
    any relevant plugins.
  - For example, for WooCommerce: relevant template overrides in
    `your-theme/woocommerce/`, custom functions related to WooCommerce in
    `functions.php` or a plugin.

- **Problem-Specific Files**: If debugging, include files involved in the error
  stack trace or areas where the bug is suspected.

- **Important Note on Parent/Child Themes**:
  - If using a child theme, include relevant files from _both_ the child theme
    and parent theme that interact or are being overridden.

### 2. Structure Your Input File List (`my_wp_context_files.txt`)

Create a plain text file (e.g., `my_wp_context_files.txt`) listing the absolute
or relative paths to your selected files. Organize and comment this list for
clarity, especially if you plan to reuse or modify it.

**Example `my_wp_context_files.txt` for a theme feature and a related plugin:**

```plaintext
# Paths should be relative to your project root, or absolute.
# For VS Code tasks, ${workspaceFolder} can be used.

# =====================================
# My Custom Theme: "AwesomeTheme"
# Working on: Homepage Slider Feature
# =====================================

# Core Theme Files
wp-content/themes/AwesomeTheme/style.css
wp-content/themes/AwesomeTheme/functions.php
wp-content/themes/AwesomeTheme/header.php
wp-content/themes/AwesomeTheme/footer.php
wp-content/themes/AwesomeTheme/front-page.php

# Homepage Slider Specifics
wp-content/themes/AwesomeTheme/template-parts/homepage-slider.php
wp-content/themes/AwesomeTheme/includes/slider-customizer-settings.php
wp-content/themes/AwesomeTheme/assets/js/homepage-slider.js
wp-content/themes/AwesomeTheme/assets/css/homepage-slider.css

# =====================================
# Related Plugin: "UtilityPlugin"
# Used by: Homepage Slider for data
# =====================================
wp-content/plugins/UtilityPlugin/utility-plugin.php
wp-content/plugins/UtilityPlugin/includes/class-data-provider.php
wp-content/plugins/UtilityPlugin/includes/cpt-slides.php

# =====================================
# General WordPress Context (Optional)
# =====================================
# Consider adding if debugging core interactions, but be selective:
# wp-includes/post.php
# wp-includes/query.php
```

**Tips for your list:**

- Use comments (`#`) to organize sections or explain choices.
- Start with a small, focused set of files and expand if the AI needs more
  context.
- Paths are typically relative to where you run the `m1f.py` script, or
  from the `${workspaceFolder}` if using VS Code tasks.

### 3. Generate the Combined Context File

Run `m1f.py` from your terminal, pointing to your input file list and
specifying an output file. It's recommended to use the `MachineReadable`
separator style.

```bash
python tools/m1f.py \
  --input-file my_wp_context_files.txt \
  --output-file .gen/wordpress_context.m1f.txt \
  --separator-style MachineReadable \
  --force \
  --minimal-output
```

**Explanation of options:**

- `--input-file my_wp_context_files.txt`: Specifies the list of files to
  include.
- `--output-file .gen/wordpress_context.m1f.txt`: Defines where the combined
  file will be saved. Using a `.gen` or `.ai-context` subfolder is good
  practice.
- `--separator-style MachineReadable`: Ensures the output is easily parsable by
  AI tools.
- `--force`: Overwrites the output file if it already exists.
- `--minimal-output`: Prevents the script from generating auxiliary files like
  file lists or logs, keeping your project clean.

You can also generate only the auxiliary files (file list and directory list)
without creating the combined file:

```bash
python tools/m1f.py \
  --input-file my_wp_context_files.txt \
  --output-file .gen/wordpress_auxiliary_only.m1f.txt \
  --skip-output-file \
  --verbose
```

This will create `wordpress_auxiliary_only_filelist.txt` and
`wordpress_auxiliary_only_dirlist.txt` files but won't generate the combined
content file.

### 4. Using the Context File with Your AI Assistant

Once `wordpress_context.m1f.txt` is generated:

1.  Open the file in your AI-enabled editor (e.g., Cursor, VS Code with AI
    extensions).
2.  Use your editor's features to add this file to the AI's context. For
    example, in Cursor, you can type `@wordpress_context.m1f.txt` in the chat or
    use the "Add to Context" option.
3.  Now, when you ask the AI questions or request code related to your WordPress
    theme/plugin, it will have the specific context of your selected files.

### Example: Creating a VS Code Task

You can automate this process by creating a VS Code task in your
`.vscode/tasks.json` file:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "WordPress: Generate AI Context from List",
      "type": "shell",
      "command": "python",
      "args": [
        "${workspaceFolder}/tools/m1f.py",
        "--input-file",
        "${workspaceFolder}/my_wp_context_files.txt",
        "--output-file",
        "${workspaceFolder}/.gen/wordpress_context.m1f.txt",
        "--separator-style",
        "MachineReadable",
        "--force",
        "--minimal-output",
        "--quiet"
      ],
      "problemMatcher": [],
      "group": {
        "kind": "build",
        "isDefault": true
      },
      "detail": "Combines specified WordPress theme/plugin files into a single context file for AI."
    },
    {
      "label": "WordPress: Generate File Lists Only",
      "type": "shell",
      "command": "python",
      "args": [
        "${workspaceFolder}/tools/m1f.py",
        "--input-file",
        "${workspaceFolder}/my_wp_context_files.txt",
        "--output-file",
        "${workspaceFolder}/.gen/wordpress_auxiliary.m1f.txt",
        "--skip-output-file",
        "--verbose"
      ],
      "problemMatcher": [],
      "group": "build",
      "detail": "Generates file and directory lists without creating the combined file."
    }
  ]
}
```

With this task, you can simply run "WordPress: Generate AI Context from List"
from the VS Code Command Palette to update your context file. Remember to
maintain your `my_wp_context_files.txt` list as your project evolves.

This approach helps you provide targeted and relevant information to your AI
assistant, leading to more accurate and helpful responses for your WordPress
development tasks.
