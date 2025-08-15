# Uninstall script for m1f tools on Windows
# This removes m1f from your system and cleans up all components

param(
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# Show help if requested
if ($Help) {
    Write-Host @"
m1f Uninstallation Script (PowerShell)
======================================

USAGE:
    .\uninstall.ps1 [OPTIONS]

DESCRIPTION:
    This script safely removes the m1f (Make One File) toolkit from your Windows system.
    It cleans up all components installed by the install.ps1 script.

OPTIONS:
    -Help          Show this help message and exit

WHAT IT REMOVES:
    - PowerShell functions added to your profile
    - Command Prompt batch files directory
    - Python virtual environment (optional)
    - Generated m1f bundles (optional)

INTERACTIVE MODE:
    The script will ask for confirmation before:
    - Proceeding with uninstallation
    - Removing generated m1f bundles
    - Removing the Python virtual environment

SAFETY FEATURES:
    - Prompts for confirmation before destructive actions
    - Provides manual cleanup instructions if automatic removal fails
    - Checks for PATH entries that may need manual removal

EXAMPLES:
    # Run the uninstaller
    .\scripts\uninstall.ps1

    # Show help
    .\scripts\uninstall.ps1 -Help

AFTER UNINSTALLATION:
    - Reload PowerShell or open a new session
    - Manually remove batch directory from PATH if needed

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
$binDir = Join-Path $projectRoot "bin"
$batchDir = Join-Path $projectRoot "batch"
$venvDir = Join-Path $projectRoot ".venv"

Write-ColorOutput "m1f Uninstallation" -Color $colors.Blue
Write-ColorOutput "==================" -Color $colors.Blue
Write-Host

# Track what we'll remove
$componentsToRemove = @()

# Check for virtual environment
if (Test-Path $venvDir) {
    $componentsToRemove += "Python virtual environment (.venv)"
}

# Check for batch directory
if (Test-Path $batchDir) {
    $componentsToRemove += "Command Prompt batch files ($batchDir)"
}

# Check if PowerShell functions are installed
$profileContent = ""
if (Test-Path $PROFILE) {
    $profileContent = Get-Content $PROFILE -Raw
    if ($profileContent -match "# m1f tools functions") {
        $componentsToRemove += "PowerShell functions in profile"
    }
}

# Check for generated bundles
$bundleFiles = @()
if (Test-Path "m1f") {
    $bundleFiles = Get-ChildItem -Path "m1f" -Filter "*.txt" | Where-Object { $_.Name -notlike "*config*" }
    if ($bundleFiles.Count -gt 0) {
        $componentsToRemove += "Generated m1f bundles ($($bundleFiles.Count) files)"
    }
}

# Show what will be removed
if ($componentsToRemove.Count -eq 0) {
    Write-ColorOutput "No m1f installation found." -Color $colors.Yellow
    Write-ColorOutput "Run '.\uninstall.ps1 -Help' for more information." -Color $colors.Yellow
    exit 0
}

Write-Host "The following components will be removed:"
Write-Host
foreach ($component in $componentsToRemove) {
    Write-Host "  • $component"
}
Write-Host

# Ask for confirmation
Write-ColorOutput "Do you want to continue with uninstallation? (y/N) " -Color $colors.Yellow -NoNewline
$response = Read-Host
if ($response -notmatch '^[Yy]$') {
    Write-Host "Uninstallation cancelled."
    exit 0
}

Write-Host

# Remove PowerShell functions
if ($profileContent -match "# m1f tools functions") {
    Write-ColorOutput "Removing m1f functions from PowerShell profile..." -Color $colors.Green
    try {
        # Remove the m1f source line and empty lines after it
        $newContent = $profileContent -replace "(?m)^# m1f tools functions.*\r?\n(.*m1f_aliases\.ps1.*\r?\n)?(\r?\n)*", ""
        Set-Content $PROFILE $newContent
        Write-ColorOutput "✓ PowerShell functions removed" -Color $colors.Green
    } catch {
        Write-ColorOutput "Warning: Could not remove PowerShell functions automatically" -Color $colors.Yellow
        Write-ColorOutput "Please manually edit: $PROFILE" -Color $colors.Yellow
    }
}

# Remove batch directory
if (Test-Path $batchDir) {
    Write-ColorOutput "Removing Command Prompt batch files..." -Color $colors.Green
    Remove-Item -Path $batchDir -Recurse -Force
    Write-ColorOutput "✓ Batch files removed" -Color $colors.Green
}

# Ask about generated bundles
if ($bundleFiles.Count -gt 0) {
    Write-Host
    Write-ColorOutput "Do you want to remove generated m1f bundles? (y/N) " -Color $colors.Yellow -NoNewline
    $bundleResponse = Read-Host
    if ($bundleResponse -match '^[Yy]$') {
        Write-ColorOutput "Removing generated bundles..." -Color $colors.Green
        foreach ($file in $bundleFiles) {
            Remove-Item -Path $file.FullName -Force
        }
        Write-ColorOutput "✓ Bundles removed" -Color $colors.Green
    } else {
        Write-ColorOutput "Keeping generated bundles" -Color $colors.Yellow
    }
}

# Remove virtual environment (ask first as it's destructive)
if (Test-Path $venvDir) {
    Write-Host
    Write-ColorOutput "Do you want to remove the Python virtual environment? (y/N) " -Color $colors.Yellow -NoNewline
    $venvResponse = Read-Host
    if ($venvResponse -match '^[Yy]$') {
        Write-ColorOutput "Removing virtual environment..." -Color $colors.Green
        try {
            # Deactivate if active
            if ($env:VIRTUAL_ENV -eq $venvDir) {
                deactivate 2>$null
            }
            Remove-Item -Path $venvDir -Recurse -Force
            Write-ColorOutput "✓ Virtual environment removed" -Color $colors.Green
        } catch {
            Write-ColorOutput "Warning: Could not remove virtual environment completely" -Color $colors.Yellow
            Write-ColorOutput "You may need to manually delete: $venvDir" -Color $colors.Yellow
        }
    } else {
        Write-ColorOutput "Keeping virtual environment" -Color $colors.Yellow
    }
}

Write-Host
Write-ColorOutput "✓ Uninstallation complete!" -Color $colors.Green
Write-Host

if ($profileContent -match "# m1f tools functions") {
    Write-ColorOutput "Please reload your PowerShell profile or start a new PowerShell session for changes to take effect." -Color $colors.Yellow
}

# Check if PATH still contains batch directory
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -like "*$batchDir*") {
    Write-Host
    Write-ColorOutput "Note: $batchDir may still be in your PATH environment variable." -Color $colors.Yellow
    Write-ColorOutput "To remove it manually:" -Color $colors.Yellow
    Write-ColorOutput "  1. Open System Properties > Environment Variables" -Color $colors.Blue
    Write-ColorOutput "  2. Edit the Path variable and remove: $batchDir" -Color $colors.Blue
}