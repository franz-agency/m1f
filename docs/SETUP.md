# m1f Setup Guide

## Prerequisites

You only need:

- **Python 3.10+** (check with `python --version` or `python3 --version`)
- **Git** (to clone the repository)

That's all! The installer handles everything else.

## Installation

### Linux/macOS

```bash
git clone https://github.com/franz-agency/m1f.git
cd m1f
source ./scripts/install.sh
```

**Important**: Use `source` (not just `./scripts/install.sh`) to activate
commands immediately.

### Windows

```powershell
git clone https://github.com/franz-agency/m1f.git
cd m1f
.\scripts\install.ps1
```

Then either:

- Restart PowerShell (recommended), or
- Reload profile: `. $PROFILE`

## What the Installer Does

The installation script automatically:

- ✅ Checks Python version (3.10+ required)
- ✅ Creates virtual environment
- ✅ Installs all dependencies
- ✅ Adds commands to your PATH
- ✅ Creates global command shortcuts
- ✅ Sets up symlinks

## Test Your Installation

```bash
m1f-help
m1f --help
```

## Available Commands

After installation, these commands are available globally:

- `m1f` - Main tool for combining files
- `m1f-s1f` - Split combined files back to original structure
- `m1f-html2md` - Convert HTML to Markdown
- `m1f-scrape` - Download websites for offline viewing
- `m1f-token-counter` - Count tokens in files
- `m1f-update` - Regenerate all m1f bundles
- `m1f-init` - Initialize m1f for your project (replaces m1f-link)
- `m1f-claude` - A wrapper for Claude AI and send infos about m1f. So claude now
  knows how to work with m1f
- `m1f-help` - Show help for all commands

## Uninstall

### Linux/macOS

```bash
cd /path/to/m1f
./scripts/uninstall.sh
```

### Windows

```powershell
cd C:\path\to\m1f
.\scripts\uninstall.ps1
```

---

## Manual Installation (Advanced)

If you prefer to install manually or the automatic installation fails:

### 1. Prerequisites

- Python 3.10 or higher
- Git
- pip

### 2. Clone and Setup Virtual Environment

```bash
git clone https://github.com/franz-agency/m1f.git
cd m1f

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Windows cmd:
.venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

### 3. Generate Initial Bundles

```bash
m1f-update
```

### 4. Add to PATH

#### Linux/macOS

Add to your shell configuration file (`~/.bashrc` or `~/.zshrc`):

```bash
export PATH="/path/to/m1f/bin:$PATH"  # m1f tools
```

Then reload:

```bash
source ~/.bashrc  # or ~/.zshrc
```

#### Windows

**Option A: PowerShell Functions**

The install script already configures PowerShell functions. To reload them:

```powershell
. $PROFILE
```

**Option B: Add to System PATH**

1. Create batch files in a directory (e.g., `C:\m1f\batch\`)
2. Add that directory to your system PATH:
   - Win + X → System → Advanced system settings
   - Environment Variables → Path → Edit → New
   - Add your batch directory path

Example batch file (`m1f.bat`):

```batch
@echo off
cd /d "C:\path\to\m1f"
call .venv\Scripts\activate.bat
m1f %*
```

Create similar batch files for:

- `m1f-s1f.bat` → `m1f-s1f %*`
- `m1f-html2md.bat` → `m1f-html2md %*`
- `m1f-scrape.bat` → `m1f-scrape %*`
- `m1f-token-counter.bat` → `m1f-token-counter %*`

## Using m1f in Other Projects

### Quick Setup for AI-Assisted Development

When starting a new project with m1f, use the `m1f-init` command for quick
setup:

```bash
cd /your/project
m1f-init
```

This command:

- Creates `m1f/m1f.txt` - a symlink to the complete m1f documentation
- Analyzes your project structure
- Generates initial bundles with auxiliary files:
  - `m1f/<project>_complete.txt` - Full project bundle
  - `m1f/<project>_complete_filelist.txt` - List of all included files
  - `m1f/<project>_complete_dirlist.txt` - List of all directories
  - `m1f/<project>_docs.txt` - Documentation bundle
  - `m1f/<project>_docs_filelist.txt` - List of documentation files
  - `m1f/<project>_docs_dirlist.txt` - Documentation directories
- Creates a basic `.m1f.config.yml`
- Shows platform-specific next steps

#### Working with Generated File Lists

The file lists created by `m1f-init` can be edited to customize future bundles:

```bash
# Edit the complete file list to remove unwanted files
vi m1f/<project>_complete_filelist.txt

# Use the edited list to create a custom bundle
m1f -i m1f/<project>_complete_filelist.txt -o m1f/custom_bundle.txt

# Create a bundle from specific directories (edit dirlist first)
m1f -s . -i m1f/selected_dirs.txt -o m1f/specific_areas.txt
```

For advanced setup with topic-specific bundles (Linux/macOS only):

```bash
m1f-claude --setup
```

#### Example AI Prompts:

```bash
# Ask Claude Code to create a configuration
"Please read @m1f/m1f.txt and create a .m1f.config.yml
for my Python web project"

# Get help with specific use cases
"Based on @m1f/m1f.txt, how do I exclude all test
files but include fixture data?"

# Troubleshoot issues
"I'm getting this error: [error message]. Can you check
@m1f/m1f.txt to help me fix it?"
```

The AI will understand:

- All m1f commands and parameters
- How to create `.m1f.config.yml` files
- Preset system and file processing options
- Best practices for different project types

## Troubleshooting

### Python Version Error

Install Python 3.10+ from [python.org](https://python.org)

### PowerShell Execution Policy (Windows)

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Command Not Found

- Linux/macOS: Make sure you've run `source ~/.bashrc` (or `~/.zshrc`)
- Windows: Restart PowerShell or Command Prompt

### Permission Errors

- Linux/macOS: Make sure scripts are executable: `chmod +x scripts/*.sh`
- Windows: Run PowerShell as Administrator if needed

## Next Steps

- Read the
  [M1F Development Workflow](docs/01_m1f/04_m1f_development_workflow.md)
- Check out example presets in `presets/`
- Run `m1f --help` to explore options
