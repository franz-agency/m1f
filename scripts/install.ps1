# Complete installation script for m1f tools
# This script handles the entire setup process after git clone

param(
    [switch]$Help
)

# Script requires administrator privileges for some operations
$ErrorActionPreference = "Stop"

# Show help if requested
if ($Help) {
    Write-Host @"
m1f Installation Script (PowerShell)
====================================

USAGE:
    .\install.ps1 [OPTIONS]

DESCRIPTION:
    This script installs the m1f (Make One File) toolkit and all its dependencies.
    It performs a complete setup including:
    - Creating a Python virtual environment
    - Installing all required dependencies
    - Setting up PowerShell functions
    - Creating batch files for Command Prompt

OPTIONS:
    -Help          Show this help message and exit

REQUIREMENTS:
    - Windows operating system
    - Python 3.10 or higher
    - pip package manager
    - PowerShell 5.0 or higher

EXAMPLES:
    # Basic installation
    .\scripts\install.ps1

    # Show help
    .\scripts\install.ps1 -Help

WHAT IT DOES:
    1. Creates a Python virtual environment in .venv\
    2. Installs all dependencies from requirements.txt
    3. Tests the m1f installation
    4. Adds m1f functions to your PowerShell profile
    5. Creates batch files for Command Prompt usage

AFTER INSTALLATION:
    - Restart PowerShell or run: . `$PROFILE
    - For Command Prompt: Add the batch directory to PATH
    - Test with 'm1f --help'

TO UNINSTALL:
    Run: .\scripts\uninstall.ps1

For more information, visit: https://github.com/denoland/m1f
"@
    exit 0
}

# Colors for output
$colors = @{
    Green = "Green"
    Yellow = "Yellow"
    Blue = "Cyan"
    Red = "Red"
}

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Get script and project paths
$scriptPath = $PSScriptRoot
$projectRoot = Split-Path $scriptPath -Parent
$venvBinDir = Join-Path $projectRoot ".venv\Scripts"
$oldBinDir = Join-Path $projectRoot "bin"

Write-ColorOutput "m1f Installation" -Color $colors.Blue
Write-ColorOutput "================" -Color $colors.Blue
Write-Host

# Check if this is an upgrade from an old installation
if ((Test-Path ".venv") -and (Test-Path "bin") -and (Test-Path "bin\m1f")) {
    Write-ColorOutput "📦 Upgrade detected: Migrating to Python entry points system" -Color $colors.Yellow
    Write-Host
}

# Check execution policy
$executionPolicy = Get-ExecutionPolicy -Scope CurrentUser
if ($executionPolicy -eq "Restricted") {
    Write-ColorOutput "PowerShell execution policy is restricted." -Color $colors.Yellow
    Write-ColorOutput "Updating execution policy for current user..." -Color $colors.Yellow
    try {
        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
        Write-ColorOutput "✓ Execution policy updated" -Color $colors.Green
    } catch {
        Write-ColorOutput "Error: Could not update execution policy. Please run as administrator or run:" -Color $colors.Red
        Write-ColorOutput "  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -Color $colors.Blue
        Write-ColorOutput "Run '.\install.ps1 -Help' for more information." -Color $colors.Yellow
        exit 1
    }
}

# Check if running in virtual environment already
if ($env:VIRTUAL_ENV) {
    Write-ColorOutput "Warning: Script is running inside a virtual environment." -Color $colors.Yellow
    Write-ColorOutput "It's recommended to run the installer outside of any virtual environment." -Color $colors.Yellow
    Write-Host
}

# Check Python version
Write-ColorOutput "Checking Python version..." -Color $colors.Green
$pythonCmd = $null

# Try to find Python
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py -3"
} else {
    Write-ColorOutput "Error: Python is not installed. Please install Python 3.10 or higher." -Color $colors.Red
    Write-ColorOutput "Download from: https://www.python.org/downloads/" -Color $colors.Yellow
    Write-ColorOutput "Run '.\install.ps1 -Help' for more information." -Color $colors.Yellow
    exit 1
}

# Check Python version is 3.10+
try {
    $versionOutput = & $pythonCmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    $versionParts = $versionOutput -split '\.'
    $major = [int]$versionParts[0]
    $minor = [int]$versionParts[1]
    
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
        Write-ColorOutput "Error: Python 3.10 or higher is required. Found Python $versionOutput" -Color $colors.Red
        Write-ColorOutput "Run '.\install.ps1 -Help' for more information." -Color $colors.Yellow
        exit 1
    }
    
    Write-ColorOutput "✓ Python $versionOutput found" -Color $colors.Green
} catch {
    Write-ColorOutput "Error: Could not determine Python version" -Color $colors.Red
    Write-ColorOutput "Run '.\install.ps1 -Help' for more information." -Color $colors.Yellow
    exit 1
}

Write-Host

# Step 1: Create virtual environment
Write-ColorOutput "Step 1: Creating virtual environment..." -Color $colors.Green
Set-Location $projectRoot

if (Test-Path ".venv") {
    Write-ColorOutput "Virtual environment already exists." -Color $colors.Yellow
} else {
    & $pythonCmd -m venv .venv
    Write-ColorOutput "✓ Virtual environment created" -Color $colors.Green
}

# Step 2: Activate virtual environment and install dependencies
Write-Host
Write-ColorOutput "Step 2: Installing dependencies..." -Color $colors.Green

# Activate virtual environment
$venvActivate = Join-Path $projectRoot ".venv\Scripts\Activate.ps1"
& $venvActivate

# Upgrade pip first
python -m pip install --upgrade pip --quiet

# Install requirements
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt --quiet
    Write-ColorOutput "✓ Dependencies installed" -Color $colors.Green
} else {
    Write-ColorOutput "Error: requirements.txt not found" -Color $colors.Red
    Write-ColorOutput "Run '.\install.ps1 -Help' for more information." -Color $colors.Yellow
    exit 1
}

# Install m1f package in editable mode (creates all entry points)
Write-ColorOutput "Installing m1f package with all tools..." -Color $colors.Green
pip install -e tools\ --quiet
Write-ColorOutput "✓ m1f package installed with all entry points" -Color $colors.Green

# Step 3: Test m1f installation
Write-Host
Write-ColorOutput "Step 3: Testing m1f installation..." -Color $colors.Green
try {
    $null = & python -m tools.m1f --version 2>&1
    Write-ColorOutput "✓ m1f is working correctly" -Color $colors.Green
    
    # Create symlink for main documentation if needed
    $m1fDocPath = Join-Path $projectRoot "m1f\m1f\87_m1f_only_docs.txt"
    $m1fLinkPath = Join-Path $projectRoot "m1f\m1f.txt"
    if ((Test-Path $m1fDocPath) -and !(Test-Path $m1fLinkPath)) {
        New-Item -ItemType SymbolicLink -Path $m1fLinkPath -Target "m1f\87_m1f_only_docs.txt" -Force | Out-Null
        Write-ColorOutput "✓ Created m1f.txt symlink to main documentation" -Color $colors.Green
    }
} catch {
    Write-ColorOutput "Warning: Could not verify m1f installation" -Color $colors.Yellow
    Write-ColorOutput "You can test it manually with 'm1f --help'" -Color $colors.Yellow
}

# Step 4: Setup PowerShell functions
Write-Host
Write-ColorOutput "Step 4: Setting up PowerShell functions..." -Color $colors.Green

# Check if profile exists
if (!(Test-Path $PROFILE)) {
    Write-ColorOutput "Creating PowerShell profile..." -Color $colors.Yellow
    New-Item -ItemType File -Path $PROFILE -Force | Out-Null
}

# Check if functions already exist
$profileContent = Get-Content $PROFILE -Raw -ErrorAction SilentlyContinue
if ($profileContent -match "# m1f tools functions") {
    # Check if we need to update from old bin path to new venv path
    if ($profileContent -match [regex]::Escape($oldBinDir)) {
        Write-ColorOutput "🔄 Updating PowerShell profile from old paths to new entry points..." -Color $colors.Yellow
        $profileContent = $profileContent -replace [regex]::Escape($oldBinDir), $venvBinDir
        Set-Content $PROFILE $profileContent
        Write-ColorOutput "✓ Updated PowerShell profile to use Python entry points" -Color $colors.Green
    } else {
        Write-ColorOutput "m1f functions already exist in profile" -Color $colors.Yellow
    }
} else {
    # Add functions to profile
    $functionsContent = @"

# m1f tools functions (added by m1f setup script)
# Add m1f entry points to PATH
`$env:PATH = "$venvBinDir;`$env:PATH"

# Dot-source the m1f aliases file if it exists (for backward compatibility)
if (Test-Path "$projectRoot\scripts\m1f_aliases.ps1") {
    . "$projectRoot\scripts\m1f_aliases.ps1"
}

"@
    Add-Content $PROFILE $functionsContent
    Write-ColorOutput "✓ PowerShell functions added to profile" -Color $colors.Green
}

# Step 5: Create batch files for Command Prompt (optional)
Write-Host
Write-ColorOutput "Step 5: Creating batch files for Command Prompt..." -Color $colors.Green

# Create batch directory if it doesn't exist
$batchDir = Join-Path $projectRoot "batch"
if (!(Test-Path $batchDir)) {
    New-Item -ItemType Directory -Path $batchDir | Out-Null
}

# Create batch files (now using Python entry points)
$commands = @{
    "m1f.bat" = "m1f"
    "s1f.bat" = "s1f"
    "m1f-s1f.bat" = "m1f-s1f"  # Alias for backward compatibility
    "m1f-html2md.bat" = "m1f-html2md"
    "m1f-scrape.bat" = "m1f-scrape"
    "m1f-research.bat" = "m1f-research"
    "m1f-token-counter.bat" = "m1f-token-counter"
    "m1f-update.bat" = "m1f-update"
    "m1f-init.bat" = "m1f-init"
    "m1f-claude.bat" = "m1f-claude"
    "m1f-help.bat" = '@echo off
echo m1f Tools - Available Commands:
echo   m1f               - Main m1f tool for combining files
echo   m1f-s1f           - Split combined files back to original structure
echo   m1f-html2md       - Convert HTML to Markdown
echo   m1f-scrape        - Download websites for offline viewing
echo   m1f-research      - AI-powered research and content analysis
echo   m1f-token-counter - Count tokens in files
echo   m1f-update        - Update m1f bundle files
echo   m1f-init          - Initialize m1f for your project
echo   m1f-claude        - Advanced setup with topic-specific bundles
echo   m1f-link          - Link m1f documentation for AI tools
echo   m1f-help          - Show this help message
echo.
echo For detailed help on each tool, use: ^<tool^> --help'
    "m1f-link.bat" = '@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "M1F_DOCS=%PROJECT_ROOT%\m1f\m1f-docs.txt"
if not exist "m1f" mkdir "m1f"
if exist "m1f\m1f-docs.txt" (
    echo m1f documentation already linked at m1f\m1f-docs.txt
) else (
    mklink "m1f\m1f-docs.txt" "%M1F_DOCS%"
    echo.
    echo You can now reference m1f documentation in AI tools:
    echo   @m1f\m1f-docs.txt
    echo.
    echo Example usage with Claude Code:
    echo   "Please read @m1f\m1f-docs.txt and help me set up m1f for this project"
)'
}

foreach ($file in $commands.Keys) {
    $content = $commands[$file]
    if ($content -notmatch '^@echo') {
        $content = "@echo off`r`n"
        $content += "cd /d `"%~dp0..`"`r`n"
        $content += "call .venv\Scripts\activate.bat`r`n"
        $content += "$($commands[$file]) %*"
    }
    $filePath = Join-Path $batchDir $file
    Set-Content -Path $filePath -Value $content -Encoding ASCII
}

Write-ColorOutput "✓ Batch files created in $batchDir" -Color $colors.Green

# Installation complete
Write-Host
Write-ColorOutput "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -Color $colors.Green
Write-ColorOutput "✨ Installation complete!" -Color $colors.Green
Write-ColorOutput "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -Color $colors.Green
Write-Host

Write-ColorOutput "Available commands in PowerShell:" -Color $colors.Yellow
Write-Host "  • m1f               - Main m1f tool for combining files"
Write-Host "  • m1f-s1f           - Split combined files back to original structure"
Write-Host "  • m1f-html2md       - Convert HTML to Markdown"
Write-Host "  • m1f-scrape        - Download websites for offline viewing"
Write-Host "  • m1f-research      - AI-powered research and content analysis"
Write-Host "  • m1f-token-counter - Count tokens in files"
Write-Host "  • m1f-update        - Regenerate m1f bundles"
Write-Host "  • m1f-init          - Initialize m1f for your project"
Write-Host "  • m1f-claude        - Advanced setup with topic-specific bundles"
Write-Host "  • m1f-link          - Link m1f documentation for AI tools"
Write-Host "  • m1f-help          - Show available commands"
Write-Host

Write-ColorOutput "For Command Prompt:" -Color $colors.Yellow
Write-ColorOutput "  Add $batchDir to your PATH environment variable" -Color $colors.Blue
Write-Host

Write-ColorOutput "Next step:" -Color $colors.Yellow
Write-ColorOutput "  Restart PowerShell or run: . `"`$PROFILE`"" -Color $colors.Blue
Write-Host

Write-ColorOutput "Test installation:" -Color $colors.Yellow
Write-ColorOutput "  m1f --help" -Color $colors.Blue
Write-Host

Write-ColorOutput "To uninstall:" -Color $colors.Yellow
Write-ColorOutput "  .\scripts\uninstall.ps1" -Color $colors.Blue