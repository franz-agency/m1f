#!/usr/bin/env pwsh
# Setup script for m1f aliases in PowerShell
# This script creates convenient aliases and functions to use m1f from anywhere

param(
    [switch]$Force,
    [switch]$Remove
)

# Colors for output
$Blue = "`e[34m"
$Green = "`e[32m"
$Yellow = "`e[33m"
$Red = "`e[31m"
$Reset = "`e[0m"

# Get the script directory and project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "${Blue}m1f PowerShell Setup${Reset}"
Write-Host "${Blue}=====================${Reset}"
Write-Host ""

# Check if we're removing
if ($Remove) {
    Write-Host "${Yellow}Removing m1f functions from PowerShell profile...${Reset}"
    
    if (!(Test-Path $PROFILE)) {
        Write-Host "${Red}No PowerShell profile found at: $PROFILE${Reset}"
        exit 1
    }
    
    $profileContent = Get-Content $PROFILE -Raw
    $startMarker = "# m1f tools functions (added by m1f setup script)"
    
    if ($profileContent -match "$startMarker") {
        # Remove the m1f source line and empty lines after it
        $newContent = $profileContent -replace "(?m)^$startMarker.*\r?\n(.*m1f_aliases\.ps1.*\r?\n)?(\r?\n)*", ""
        Set-Content $PROFILE $newContent
        Write-Host "${Green}✓ m1f functions removed from profile${Reset}"
        Write-Host ""
        Write-Host "Please reload your PowerShell profile:"
        Write-Host "  ${Blue}. `$PROFILE${Reset}"
    } else {
        Write-Host "${Yellow}No m1f functions found in profile${Reset}"
    }
    exit 0
}

# Explain what this script does
Write-Host "This script will add the following functions to your PowerShell profile:"
Write-Host ""
Write-Host "  • m1f          - Main m1f tool for combining files"
Write-Host "  • s1f          - Split combined files back to original structure"
Write-Host "  • html2md      - Convert HTML to Markdown"
Write-Host "  • webscraper   - Download websites for offline viewing"
Write-Host "  • token-counter - Count tokens in files"
Write-Host "  • m1f-update   - Regenerate m1f bundles"
Write-Host "  • m1f-link     - Create symlinks to m1f bundles"
Write-Host "  • m1f-help     - Show available commands"
Write-Host ""
Write-Host "These functions will be added to your PowerShell profile."
Write-Host ""

# Create PowerShell functions content
$FunctionsContent = @"

# m1f tools functions (added by m1f setup script)
# Dot-source the m1f aliases file
if (Test-Path "$ProjectRoot\scripts\m1f_aliases.ps1") {
    . "$ProjectRoot\scripts\m1f_aliases.ps1"
} else {
    Write-Warning "m1f aliases file not found at: $ProjectRoot\scripts\m1f_aliases.ps1 (check your PowerShell profile at: `$PROFILE)"
}

"@

# Check if profile exists
if (!(Test-Path $PROFILE)) {
    Write-Host "${Yellow}PowerShell profile not found. Creating profile...${Reset}"
    New-Item -ItemType File -Path $PROFILE -Force | Out-Null
}

# Check if functions already exist
$profileContent = Get-Content $PROFILE -Raw -ErrorAction SilentlyContinue
if ($profileContent -match "# m1f tools functions") {
    if (!$Force) {
        Write-Host "${Yellow}m1f functions already exist in profile${Reset}"
        Write-Host ""
        Write-Host "Options:"
        Write-Host "1. Run with -Force to overwrite existing functions"
        Write-Host "2. Run with -Remove to remove existing functions"
        Write-Host ""
        Write-Host "${Yellow}To remove the functions manually:${Reset}"
        Write-Host "1. Open `$PROFILE in your editor"
        Write-Host "2. Find the line '# m1f tools functions (added by m1f setup script)'"
        Write-Host "3. Delete that line and the dot-source line below it"
        Write-Host "4. Save the file and reload your PowerShell"
        exit 1
    } else {
        Write-Host "${Yellow}Removing existing m1f functions...${Reset}"
        $profileContent = $profileContent -replace "(?m)^# m1f tools functions.*\r?\n(.*m1f_aliases\.ps1.*\r?\n)?(\r?\n)*", ""
        Set-Content $PROFILE $profileContent
    }
}

# Show what will be modified
Write-Host "${Yellow}PowerShell profile:${Reset} $PROFILE"
Write-Host "${Yellow}Project root:${Reset} $ProjectRoot"
Write-Host ""

# Ask for confirmation if not forced
if (!$Force) {
    $response = Read-Host "Do you want to continue? (y/N)"
    if ($response -notmatch '^[Yy]$') {
        Write-Host "Setup cancelled."
        exit 0
    }
}

# Add functions to profile
Write-Host ""
Write-Host "${Green}Adding m1f functions to PowerShell profile...${Reset}"
Add-Content $PROFILE $FunctionsContent

# Create standalone scripts directory
$scriptsDir = "$env:LOCALAPPDATA\m1f\bin"
if (!(Test-Path $scriptsDir)) {
    New-Item -ItemType Directory -Force -Path $scriptsDir | Out-Null
}

# Create standalone batch file
$standaloneBatch = @"
@echo off
cd /d "$ProjectRoot"
call "$ProjectRoot\.venv\Scripts\activate.bat"
m1f %*
"@
Set-Content "$scriptsDir\m1f.bat" $standaloneBatch

Write-Host "${Green}✓ Setup complete!${Reset}"
Write-Host ""
Write-Host "${Yellow}Next steps:${Reset}"
Write-Host "1. Reload your PowerShell profile:"
Write-Host "   ${Blue}. `$PROFILE${Reset}"
Write-Host ""
Write-Host "2. Test the installation:"
Write-Host "   ${Blue}m1f --help${Reset}"
Write-Host ""
Write-Host "3. In any project, create m1f symlink:"
Write-Host "   ${Blue}m1f-link${Reset}"
Write-Host ""
Write-Host "4. View all available commands:"
Write-Host "   ${Blue}m1f-help${Reset}"
Write-Host ""
Write-Host "${Green}Standalone batch file also created at: $scriptsDir\m1f.bat${Reset}"
Write-Host ""
Write-Host "${Yellow}To remove the functions later:${Reset}"
Write-Host "1. Run: ${Blue}.\scripts\setup_m1f_aliases.ps1 -Remove${Reset}"
Write-Host "2. Or manually edit `$PROFILE and remove the m1f section"
Write-Host "3. Optionally remove: $scriptsDir"