#!/usr/bin/env pwsh
# Install m1f Git Hooks (PowerShell version)
# This script installs the m1f git hooks into your project

param(
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# Show help if requested
if ($Help) {
    Write-Host @"
m1f Git Hook Installer (PowerShell)
===================================

USAGE:
    .\install-git-hooks.ps1 [OPTIONS]

DESCRIPTION:
    This script installs m1f git hooks into your project's .git/hooks directory.
    The hooks automatically run m1f bundling operations before commits.

OPTIONS:
    -Help          Show this help message and exit

HOOK TYPES:
    Internal Hook (m1f project development):
        - Formats Python files with Black
        - Formats Markdown files with Prettier
        - Runs m1f auto-bundle

    External Hook (projects using m1f):
        - Runs m1f auto-bundle only (if .m1f.config.yml exists)

REQUIREMENTS:
    - Git repository
    - m1f installed and in PATH
    - For internal hook: Black (pip install black) and Prettier (npm install -g prettier)

EXAMPLES:
    # Install hook interactively
    .\scripts\install-git-hooks.ps1

    # Show help
    .\scripts\install-git-hooks.ps1 -Help

BYPASS HOOK:
    To commit without running the hook:
    git commit --no-verify

UNINSTALL:
    Remove-Item .\.git\hooks\pre-commit
    Remove-Item .\.git\hooks\pre-commit.ps1

For more information, visit: https://github.com/denoland/m1f
"@
    exit 0
}

# Colors for output
$colors = @{
    Red = "Red"
    Green = "Green"
    Yellow = "Yellow"
    Blue = "Cyan"
}

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Check if we're in a git repository
try {
    $gitDir = git rev-parse --git-dir 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw
    }
} catch {
    Write-ColorOutput "Error: Not in a git repository!" -Color $colors.Red
    Write-ColorOutput "Please run this script from the root of your git project." -Color $colors.Red
    Write-ColorOutput "Run '.\install-git-hooks.ps1 -Help' for more information." -Color $colors.Yellow
    exit 1
}

# Detect if we're in the m1f project itself
$isM1fProject = $false
if ((Test-Path "tools\m1f.py") -and (Test-Path ".m1f.config.yml") -and (Test-Path "scripts\hooks")) {
    $isM1fProject = $true
}

# Script location
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$hooksDir = Join-Path $scriptDir "hooks"

# Check if running from URL (not implemented for PowerShell)
$useRemote = $false
if (-not (Test-Path $hooksDir)) {
    Write-ColorOutput "Error: Hooks directory not found. Please run from the m1f repository." -Color $colors.Red
    Write-ColorOutput "Run '.\install-git-hooks.ps1 -Help' for more information." -Color $colors.Yellow
    exit 1
}

Write-ColorOutput "m1f Git Hook Installer" -Color $colors.Blue
Write-ColorOutput "======================" -Color $colors.Blue
Write-Host

# Function to install hook
function Install-Hook {
    param(
        [string]$HookType
    )
    
    $targetFile = Join-Path $gitDir "hooks\pre-commit"
    $targetPsFile = Join-Path $gitDir "hooks\pre-commit.ps1"
    
    # Create bash wrapper for Git
    $wrapperContent = @'
#!/bin/sh
# Git hook wrapper for PowerShell on Windows
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(dirname "$0")/pre-commit.ps1"
exit $?
'@
    
    # Write the bash wrapper
    $wrapperContent | Out-File -FilePath $targetFile -Encoding ASCII -NoNewline
    
    # Copy the PowerShell hook
    $sourceFile = Join-Path $hooksDir "pre-commit-$HookType.ps1"
    if (-not (Test-Path $sourceFile)) {
        Write-ColorOutput "Error: Hook file not found: $sourceFile" -Color $colors.Red
        Write-ColorOutput "Run '.\install-git-hooks.ps1 -Help' for more information." -Color $colors.Yellow
        exit 1
    }
    
    Copy-Item -Path $sourceFile -Destination $targetPsFile -Force
    
    Write-ColorOutput "✓ Installed $HookType pre-commit hook" -Color $colors.Green
}

# Show hook options
Write-Host "Available hooks:"
Write-Host

if ($isM1fProject) {
    Write-Host "  1) Internal - For m1f project development"
    Write-Host "     • Formats Python files with Black"
    Write-Host "     • Formats Markdown files with Prettier"
    Write-Host "     • Runs m1f auto-bundle"
    Write-Host
    Write-Host "  2) External - For projects using m1f"
    Write-Host "     • Runs m1f auto-bundle only"
    Write-Host
    
    $choice = Read-Host "Which hook would you like to install? [1/2] (default: 1)"
    
    switch ($choice) {
        "2" { $hookType = "external" }
        default { $hookType = "internal" }
    }
} else {
    Write-Host "  • External - For projects using m1f"
    Write-Host "    Runs m1f auto-bundle when .m1f.config.yml exists"
    Write-Host
    $hookType = "external"
}

# Check for existing hook
$existingHook = Join-Path $gitDir "hooks\pre-commit"
$existingPsHook = Join-Path $gitDir "hooks\pre-commit.ps1"

if ((Test-Path $existingHook) -or (Test-Path $existingPsHook)) {
    Write-ColorOutput "Warning: A pre-commit hook already exists." -Color $colors.Yellow
    $response = Read-Host "Do you want to replace it? [y/N]"
    if ($response -notmatch '^[Yy]$') {
        Write-Host "Installation cancelled."
        exit 0
    }
}

# Install the hook
Install-Hook -HookType $hookType

Write-Host
Write-ColorOutput "✓ Git hook installation complete!" -Color $colors.Green
Write-Host

# Show usage instructions based on hook type
if ($hookType -eq "internal") {
    Write-Host "The internal hook will:"
    Write-Host "  - Format Python files with Black (if installed)"
    Write-Host "  - Format Markdown files with Prettier (if installed)"
    Write-Host "  - Run m1f auto-bundle"
    Write-Host
    Write-Host "Requirements:"
    Write-Host "  - Black: pip install black"
    Write-Host "  - Prettier: npm install -g prettier"
    Write-Host "  - m1f: Already available in this project"
} else {
    Write-Host "The external hook will:"
    Write-Host "  - Run m1f auto-bundle if .m1f.config.yml exists"
    Write-Host
    Write-Host "Requirements:"
    Write-Host "  - m1f installed and available in PATH"
    Write-Host "  - .m1f.config.yml in your project root"
}

Write-Host
Write-Host "To disable the hook temporarily, use:"
Write-Host "  git commit --no-verify"
Write-Host
Write-Host "To uninstall, remove the hook files:"
Write-Host "  Remove-Item '$gitDir\hooks\pre-commit'"
Write-Host "  Remove-Item '$gitDir\hooks\pre-commit.ps1'"