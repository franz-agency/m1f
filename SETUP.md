# m1f Setup Guide

## Prerequisites

You only need:
- **Python 3.10+** (check with `python --version` or `python3 --version`)
- **Git** (to clone the repository)

That's all! The installer handles everything else.

## Installation (3 Commands!)

### Linux/macOS

```bash
git clone https://github.com/franz-agency/m1f.git
cd m1f
source ./scripts/install.sh
```

**Important**: Use `source` (not just `./scripts/install.sh`) to activate commands immediately!

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
- ✅ Generates initial m1f bundles
- ✅ Adds commands to your PATH
- ✅ Creates global command shortcuts
- ✅ Sets up symlinks (optional)

## Test Your Installation

```bash
m1f --help
m1f-update
```

## Available Commands

After installation, these commands are available globally:

- `m1f` - Main tool for combining files
- `m1f-s1f` - Split combined files back to original structure  
- `m1f-html2md` - Convert HTML to Markdown
- `m1f-scrape` - Download websites for offline viewing
- `m1f-token-counter` - Count tokens in files
- `m1f-update` - Regenerate all m1f bundles
- `m1f-link` - Create symlink to m1f bundles in current project
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
.\scripts\setup_m1f_aliases.ps1 -Remove
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
python -m tools.m1f auto-bundle
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

Run the setup script:
```powershell
.\scripts\setup_m1f_aliases.ps1
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
python -m tools.m1f %*
```

Create similar batch files for:
- `m1f-s1f.bat` → `python -m tools.s1f %*`
- `m1f-html2md.bat` → `python -m tools.html2md %*`
- `m1f-scrape.bat` → `python -m tools.webscraper %*`
- `m1f-token-counter.bat` → `python tools\token_counter.py %*`

## Using m1f in Other Projects

Create a symlink to access m1f bundles in your project:

```bash
cd /your/project
m1f-link
# Now access bundles at .m1f/m1f/
```

Or manually:

### Linux/macOS
```bash
mkdir -p .m1f
ln -s /path/to/m1f/.m1f .m1f/m1f
```

### Windows (with Developer Mode)
```powershell
New-Item -ItemType Directory -Force -Path .m1f
New-Item -ItemType SymbolicLink -Path ".m1f\m1f" -Target "C:\path\to\m1f\.m1f"
```

### Windows (without Developer Mode - Junction)
```powershell
New-Item -ItemType Directory -Force -Path .m1f
cmd /c mklink /J ".m1f\m1f" "C:\path\to\m1f\.m1f"
```

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

- Read the [M1F Development Workflow](docs/01_m1f/04_m1f_development_workflow.md)
- Check out example presets in `presets/`
- Run `m1f --help` to explore options