# m1f Setup Guide

This guide walks you through setting up m1f on your system.

## Prerequisites

- Python 3.10 or higher
- Git
- pip

## 1. Clone the Repository

```bash
git clone https://github.com/franz-agency/m1f.git
cd m1f
```

## 2. Create Virtual Environment

### Linux/macOS

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Windows

#### PowerShell

```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# If you get an execution policy error, run:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Install dependencies
pip install -r requirements.txt
```

#### Command Prompt (cmd)

```cmd
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

## 3. Generate m1f Bundle Files

### Linux/macOS

```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Run the update script
./scripts/update_m1f_files.sh
```

### Windows

Since the update script is a bash script, you have a few options:

#### Option A: Use Git Bash

```bash
# In Git Bash
./scripts/update_m1f_files.sh
```

#### Option B: Run Python commands directly

```powershell
# In PowerShell with activated venv
# Create .m1f directory
New-Item -ItemType Directory -Force -Path .m1f

# Generate bundles
python tools/m1f.py -s docs -o .m1f/m1f-documentation.txt --include-extensions .md .txt -f
python tools/m1f.py -s tools -o .m1f/m1f-programs.txt --include-extensions .py -f
python tools/m1f.py -s tests -o .m1f/m1f-tests.txt --include-extensions .py --excludes "*/source/*" "*/extracted/*" "*/output/*" -f
python tools/m1f.py -s . -o .m1f/m1f-allinone.txt --include-extensions .py .md .txt .yml .yaml .json --excludes "*/node_modules/*" "*/.venv/*" "*/.git/*" "*/.m1f/*" -f
```

## 4. Set Up Global Access

### Linux/macOS

Run the setup script to create shell aliases:

```bash
./scripts/setup_m1f_aliases.sh

# Reload your shell configuration
source ~/.bashrc  # or ~/.zshrc for zsh
```

Now you can use `m1f`, `s1f`, `html2md` commands from anywhere.

### Windows

For Windows, we recommend creating batch files or PowerShell functions:

#### Option A: Add to PATH (Recommended)

1. Create a `bin` directory in the m1f project:

```powershell
New-Item -ItemType Directory -Force -Path bin
```

2. Create batch files for each tool:

**bin/m1f.bat:**

```batch
@echo off
cd /d "C:\path\to\m1f"
call .venv\Scripts\activate.bat
python tools\m1f.py %*
```

**bin/s1f.bat:**

```batch
@echo off
cd /d "C:\path\to\m1f"
call .venv\Scripts\activate.bat
python tools\s1f.py %*
```

**bin/html2md.bat:**

```batch
@echo off
cd /d "C:\path\to\m1f"
call .venv\Scripts\activate.bat
python tools\html2md.py %*
```

3. Add the `bin` directory to your PATH:
   - Press Win + X, select "System"
   - Click "Advanced system settings"
   - Click "Environment Variables"
   - Under "User variables", select "Path" and click "Edit"
   - Click "New" and add: `C:\path\to\m1f\bin`
   - Click "OK" to save

#### Option B: PowerShell Profile

Add functions to your PowerShell profile:

```powershell
# Open your profile
notepad $PROFILE

# Add these functions (adjust path as needed):
function m1f {
    $m1fPath = "C:\path\to\m1f"
    Push-Location $m1fPath
    & "$m1fPath\.venv\Scripts\python.exe" "$m1fPath\tools\m1f.py" $args
    Pop-Location
}

function s1f {
    $m1fPath = "C:\path\to\m1f"
    Push-Location $m1fPath
    & "$m1fPath\.venv\Scripts\python.exe" "$m1fPath\tools\s1f.py" $args
    Pop-Location
}

function html2md {
    $m1fPath = "C:\path\to\m1f"
    Push-Location $m1fPath
    & "$m1fPath\.venv\Scripts\python.exe" "$m1fPath\tools\html2md.py" $args
    Pop-Location
}

# Save and reload profile
. $PROFILE
```

## 5. Using m1f in Other Projects

### Linux/macOS - Creating Symlinks

```bash
cd /path/to/your/project
mkdir -p .m1f
ln -s /path/to/m1f/.m1f .m1f/m1f

# Now you can access m1f bundles:
cat .m1f/m1f/m1f-documentation.txt
```

### Windows - Symlinks

Windows supports symlinks, but they require administrator privileges or
Developer Mode:

#### With Developer Mode enabled (Windows 10/11):

```powershell
cd C:\path\to\your\project
New-Item -ItemType Directory -Force -Path .m1f
New-Item -ItemType SymbolicLink -Path ".m1f\m1f" -Target "C:\path\to\m1f\.m1f"
```

#### Without Developer Mode (using Junction):

```powershell
cd C:\path\to\your\project
New-Item -ItemType Directory -Force -Path .m1f
cmd /c mklink /J ".m1f\m1f" "C:\path\to\m1f\.m1f"
```

#### Alternative: Copy Instead of Symlink

If symlinks are problematic, you can simply copy the files:

```powershell
cd C:\path\to\your\project
New-Item -ItemType Directory -Force -Path .m1f\m1f
Copy-Item -Path "C:\path\to\m1f\.m1f\*" -Destination ".m1f\m1f\" -Recurse
```

## Verification

Test your installation:

```bash
# Linux/macOS
m1f --version
m1f --help

# Windows (if using batch files or PowerShell functions)
m1f --version
m1f --help
```

## Troubleshooting

### Virtual Environment Not Activating (Windows)

If you get an error about execution policies in PowerShell:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Command Not Found (Linux/macOS)

Make sure you've:

1. Run the setup script: `./scripts/setup_m1f_aliases.sh`
2. Reloaded your shell: `source ~/.bashrc` or `source ~/.zshrc`

### Path Issues (Windows)

If batch files aren't found:

1. Verify the bin directory is in your PATH
2. Open a new Command Prompt or PowerShell window
3. Try using the full path: `C:\path\to\m1f\bin\m1f.bat`

### Symlink Permission Errors (Windows)

If you can't create symlinks:

1. Enable Developer Mode in Windows Settings
2. Or run PowerShell as Administrator
3. Or use the Junction alternative (mklink /J)
4. Or simply copy the files instead

## Next Steps

- Read the [M1F Development Workflow](docs/04_m1f_development_workflow.md) guide
- Check out example presets in the `presets/` directory
- Run `m1f --help` to see all available options
