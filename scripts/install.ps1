# Complete installation script for m1f tools
# This script handles the entire setup process after git clone

# Script requires administrator privileges for some operations
$ErrorActionPreference = "Stop"

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
$binDir = Join-Path $projectRoot "bin"

Write-ColorOutput "m1f Installation" -Color $colors.Blue
Write-ColorOutput "================" -Color $colors.Blue
Write-Host

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
        exit 1
    }
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
        exit 1
    }
    
    Write-ColorOutput "✓ Python $versionOutput found" -Color $colors.Green
} catch {
    Write-ColorOutput "Error: Could not determine Python version" -Color $colors.Red
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
    exit 1
}

# Step 3: Generate initial m1f bundles
Write-Host
Write-ColorOutput "Step 3: Generating initial m1f bundles..." -Color $colors.Green
python -m tools.m1f auto-bundle --quiet
Write-ColorOutput "✓ Initial bundles generated" -Color $colors.Green

# Step 4: Setup PowerShell functions
Write-Host
Write-ColorOutput "Step 4: Setting up PowerShell functions..." -Color $colors.Green

# Run the PowerShell setup script
$setupScript = Join-Path $scriptPath "setup_m1f_aliases.ps1"
& $setupScript

Write-ColorOutput "✓ PowerShell functions configured" -Color $colors.Green

# Step 5: Create batch files for Command Prompt (optional)
Write-Host
Write-ColorOutput "Step 5: Creating batch files for Command Prompt..." -Color $colors.Green

# Create batch directory if it doesn't exist
$batchDir = Join-Path $projectRoot "batch"
if (!(Test-Path $batchDir)) {
    New-Item -ItemType Directory -Path $batchDir | Out-Null
}

# Create batch files
$commands = @{
    "m1f.bat" = "python -m tools.m1f"
    "m1f-s1f.bat" = "python -m tools.s1f"
    "m1f-html2md.bat" = "python -m tools.html2md"
    "m1f-scrape.bat" = "python -m tools.webscraper"
    "m1f-token-counter.bat" = "python tools\token_counter.py"
    "m1f-update.bat" = "python -m tools.m1f auto-bundle"
    "m1f-help.bat" = '@echo off
echo m1f Tools - Available Commands:
echo   m1f               - Main m1f tool for combining files
echo   m1f-s1f           - Split combined files back to original structure
echo   m1f-html2md       - Convert HTML to Markdown
echo   m1f-scrape        - Download websites for offline viewing
echo   m1f-token-counter - Count tokens in files
echo   m1f-update        - Update m1f bundle files
echo   m1f-link          - Create symlink to m1f bundles in current project
echo   m1f-help          - Show this help message
echo.
echo For detailed help on each tool, use: ^<tool^> --help'
    "m1f-link.bat" = '@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
if not exist ".m1f" mkdir ".m1f"
if exist ".m1f\m1f" (
    echo m1f link already exists in .m1f\m1f
) else (
    mklink /J ".m1f\m1f" "%PROJECT_ROOT%\.m1f"
    echo Created junction: .m1f\m1f -^> %PROJECT_ROOT%\.m1f
    echo You can now access m1f bundles at .m1f\m1f\
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
Write-Host "  • m1f-token-counter - Count tokens in files"
Write-Host "  • m1f-update        - Regenerate m1f bundles"
Write-Host "  • m1f-link          - Create symlinks to m1f bundles"
Write-Host "  • m1f-help          - Show available commands"
Write-Host

Write-ColorOutput "For Command Prompt:" -Color $colors.Yellow
Write-ColorOutput "  Add $batchDir to your PATH environment variable" -Color $colors.Blue
Write-Host

Write-ColorOutput "Next step:" -Color $colors.Yellow
Write-ColorOutput "  Restart PowerShell or run: . `$PROFILE" -Color $colors.Blue
Write-Host

Write-ColorOutput "Test installation:" -Color $colors.Yellow
Write-ColorOutput "  m1f --help" -Color $colors.Blue
Write-Host

Write-ColorOutput "To uninstall:" -Color $colors.Yellow
Write-ColorOutput "  .\scripts\setup_m1f_aliases.ps1 -Remove" -Color $colors.Blue